"""Telegram: foto → AI → tasdiq → Baraka products DB."""

from __future__ import annotations

import logging
from enum import IntEnum
from io import BytesIO

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from bot.config import ADMIN_IDS
from bot.database import (
    create_product,
    get_categories,
    get_category,
    get_product_by_id,
    set_product_image,
)
from bot.category_emoji import category_label
from bot.keyboards import cancel_keyboard, main_menu_keyboard
from bot.product_vision import (
    ProductDraft,
    build_description,
    extract_product_fields,
    match_category_id,
)

logger = logging.getLogger(__name__)


class CameraIntakeState(IntEnum):
    PHOTO = 1
    REVIEW = 2
    EDIT_NAME = 3
    EDIT_PRICE = 4


def _is_admin(user_id: int | None) -> bool:
    return bool(user_id and user_id in ADMIN_IDS)


def _menu(user_id: int):
    return main_menu_keyboard(is_admin=True)


def _draft_from_user_data(context: ContextTypes.DEFAULT_TYPE) -> ProductDraft:
    raw = context.user_data.get("camera_draft") or {}
    return ProductDraft(
        name=str(raw.get("name") or ""),
        brand=str(raw.get("brand") or ""),
        price=raw.get("price"),
        category_hint=str(raw.get("category_hint") or ""),
        unit=str(raw.get("unit") or ""),
        description=str(raw.get("description") or ""),
        confidence=float(raw.get("confidence") or 0),
        provider=str(raw.get("provider") or "mock"),
        raw_notes=str(raw.get("raw_notes") or ""),
    )


def _store_draft(context: ContextTypes.DEFAULT_TYPE, draft: ProductDraft) -> None:
    context.user_data["camera_draft"] = draft.to_dict()


def _format_draft_html(context: ContextTypes.DEFAULT_TYPE) -> str:
    draft = _draft_from_user_data(context)
    cat_id = context.user_data.get("camera_category_id")
    cat = get_category(int(cat_id)) if cat_id else None
    price = draft.price
    price_s = f"{int(price):,} so‘m".replace(",", " ") if price is not None else "— (yozing)"
    conf = int(round(float(draft.confidence or 0) * 100))
    mode = "🤖 AI" if draft.provider == "openai" else "🧪 Demo"
    return (
        f"📷 <b>Foto mahsulot</b> ({mode}, ishonch ~{conf}%)\n\n"
        f"🏷 <b>Nom:</b> {draft.display_name() or '—'}\n"
        f"💰 <b>Narx:</b> {price_s}\n"
        f"🗂 <b>Toifa:</b> {category_label(cat) if cat else (draft.category_hint or '—')}\n"
        f"📐 <b>Birlik:</b> {draft.unit or '—'}\n"
        f"📝 <b>Izoh:</b> {draft.description or '—'}\n\n"
        "Tekshiring. Noto‘g‘ri bo‘lsa tahrirlang, keyin saqlang."
    )


def _review_keyboard(context: ContextTypes.DEFAULT_TYPE) -> InlineKeyboardMarkup:
    cats = get_categories(active_only=True)[:8]
    rows: list[list[InlineKeyboardButton]] = [
        [
            InlineKeyboardButton("✅ Bazaga yozish", callback_data="cam:save"),
            InlineKeyboardButton("❌ Bekor", callback_data="cam:cancel"),
        ],
        [
            InlineKeyboardButton("✏️ Nom", callback_data="cam:edit_name"),
            InlineKeyboardButton("💰 Narx", callback_data="cam:edit_price"),
        ],
    ]
    cat_row: list[InlineKeyboardButton] = []
    for cat in cats:
        cat_row.append(
            InlineKeyboardButton(
                category_label(cat)[:28],
                callback_data=f"cam:cat:{int(cat['id'])}",
            )
        )
        if len(cat_row) == 2:
            rows.append(cat_row)
            cat_row = []
    if cat_row:
        rows.append(cat_row)
    return InlineKeyboardMarkup(rows)


async def start_camera_intake(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    user = update.effective_user
    if not user or not _is_admin(user.id):
        msg = update.effective_message
        if msg:
            await msg.reply_text("Faqat adminlar uchun.")
        return ConversationHandler.END

    context.user_data.pop("camera_draft", None)
    context.user_data.pop("camera_category_id", None)
    context.user_data.pop("camera_file_id", None)
    context.user_data["awaiting_admin"] = "camera_photo"

    text = (
        "📷 <b>Foto bilan mahsulot</b>\n\n"
        "Mahsulot yorlig‘i yoki qadoq rasmini yuboring.\n"
        "AI (yoki demo) maydonlarni to‘ldiradi — saqlashdan oldin tekshirasiz."
    )
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, parse_mode="HTML")
        await update.callback_query.message.reply_text(
            "Rasmni yuboring 👇",
            reply_markup=cancel_keyboard(),
        )
    elif update.message:
        await update.message.reply_text(
            text,
            parse_mode="HTML",
            reply_markup=cancel_keyboard(),
        )
    return CameraIntakeState.PHOTO


async def camera_photo_received(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    from bot.keyboards import is_main_menu_text

    msg = update.message
    if not msg:
        return CameraIntakeState.PHOTO

    text = (msg.text or "").strip()
    if text == "❌ Bekor qilish" or text.lower() in {"/cancel", "bekor"}:
        return await camera_cancel(update, context)
    if is_main_menu_text(text):
        context.user_data.pop("awaiting_admin", None)
        from bot.handlers import dispatch_main_menu

        await dispatch_main_menu(update, context)
        return ConversationHandler.END

    file_id = None
    mime = "image/jpeg"
    if msg.photo:
        file_id = msg.photo[-1].file_id
    elif msg.document and (msg.document.mime_type or "").startswith("image/"):
        file_id = msg.document.file_id
        mime = msg.document.mime_type or mime

    if not file_id:
        await msg.reply_text("Iltimos, rasm yuboring (galereya yoki fayl).")
        return CameraIntakeState.PHOTO

    status = await msg.reply_text("⏳ Rasm o‘qilmoqda…")
    try:
        tg_file = await context.bot.get_file(file_id)
        buf = BytesIO()
        await tg_file.download_to_memory(buf)
        image_bytes = buf.getvalue()
        draft = extract_product_fields(image_bytes, mime_type=mime)
    except Exception as exc:
        logger.exception("Camera intake download/parse failed")
        await status.edit_text(f"❌ Rasm o‘qilmadi: {exc}")
        return CameraIntakeState.PHOTO

    _store_draft(context, draft)
    context.user_data["camera_file_id"] = file_id
    cats = get_categories(active_only=True)
    matched = match_category_id(draft.category_hint, cats)
    if matched:
        context.user_data["camera_category_id"] = matched
    else:
        context.user_data.pop("camera_category_id", None)

    context.user_data["awaiting_admin"] = "camera_review"
    await status.edit_text(
        _format_draft_html(context),
        parse_mode="HTML",
        reply_markup=_review_keyboard(context),
    )
    return CameraIntakeState.REVIEW


async def camera_review_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    if not query or not query.from_user or not _is_admin(query.from_user.id):
        if query:
            await query.answer("Faqat admin.", show_alert=True)
        return ConversationHandler.END

    await query.answer()
    data = query.data or ""
    parts = data.split(":")
    action = parts[1] if len(parts) > 1 else ""

    if action == "cancel":
        context.user_data.pop("camera_draft", None)
        context.user_data.pop("camera_category_id", None)
        context.user_data.pop("camera_file_id", None)
        context.user_data.pop("awaiting_admin", None)
        await query.edit_message_text("❌ Bekor qilindi.")
        await query.message.reply_text(
            "Admin menyu.",
            reply_markup=_menu(query.from_user.id),
        )
        return ConversationHandler.END

    if action == "edit_name":
        context.user_data["awaiting_admin"] = "camera_edit_name"
        await query.message.reply_text(
            "Yangi nomni yozing:",
            reply_markup=cancel_keyboard(),
        )
        return CameraIntakeState.EDIT_NAME

    if action == "edit_price":
        context.user_data["awaiting_admin"] = "camera_edit_price"
        await query.message.reply_text(
            "Narxni so‘mda yozing (faqat raqam):",
            reply_markup=cancel_keyboard(),
        )
        return CameraIntakeState.EDIT_PRICE

    if action == "cat" and len(parts) > 2:
        try:
            cat_id = int(parts[2])
        except ValueError:
            return CameraIntakeState.REVIEW
        context.user_data["camera_category_id"] = cat_id
        await query.edit_message_text(
            _format_draft_html(context),
            parse_mode="HTML",
            reply_markup=_review_keyboard(context),
        )
        return CameraIntakeState.REVIEW

    if action == "save":
        return await _save_camera_product(update, context)

    return CameraIntakeState.REVIEW


async def camera_edit_name(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    text = (update.message.text or "").strip() if update.message else ""
    if text == "❌ Bekor qilish":
        await update.message.reply_text(
            _format_draft_html(context),
            parse_mode="HTML",
            reply_markup=_review_keyboard(context),
        )
        return CameraIntakeState.REVIEW
    if len(text) < 2:
        await update.message.reply_text("Nom juda qisqa. Qayta yozing:")
        return CameraIntakeState.EDIT_NAME
    draft = _draft_from_user_data(context)
    draft.name = text
    draft.brand = ""
    _store_draft(context, draft)
    context.user_data["awaiting_admin"] = "camera_review"
    await update.message.reply_text(
        _format_draft_html(context),
        parse_mode="HTML",
        reply_markup=_review_keyboard(context),
    )
    return CameraIntakeState.REVIEW


async def camera_edit_price(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    text = (update.message.text or "").strip() if update.message else ""
    if text == "❌ Bekor qilish":
        await update.message.reply_text(
            _format_draft_html(context),
            parse_mode="HTML",
            reply_markup=_review_keyboard(context),
        )
        return CameraIntakeState.REVIEW
    digits = "".join(ch for ch in text if ch.isdigit())
    if not digits:
        await update.message.reply_text("Faqat raqam yozing (so‘m):")
        return CameraIntakeState.EDIT_PRICE
    draft = _draft_from_user_data(context)
    draft.price = int(digits)
    _store_draft(context, draft)
    context.user_data["awaiting_admin"] = "camera_review"
    await update.message.reply_text(
        _format_draft_html(context),
        parse_mode="HTML",
        reply_markup=_review_keyboard(context),
    )
    return CameraIntakeState.REVIEW


async def _save_camera_product(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    msg = query.message if query else update.effective_message
    user = update.effective_user
    draft = _draft_from_user_data(context)
    name = draft.display_name().strip()
    if not name:
        if query:
            await query.answer("Nom bo‘sh — tahrirlang.", show_alert=True)
        return CameraIntakeState.REVIEW
    price = draft.price
    if price is None:
        if query:
            await query.answer("Narx kerak — 💰 tugmasini bosing.", show_alert=True)
        return CameraIntakeState.REVIEW

    cat_id = context.user_data.get("camera_category_id")
    if not cat_id:
        cats = get_categories(active_only=True)
        if cats:
            if query:
                await query.answer("Toifa tanlang (pastdagi tugmalar).", show_alert=True)
            return CameraIntakeState.REVIEW

    description = build_description(draft)
    try:
        product_id = create_product(
            name=name,
            price=int(price),
            description=description,
            category_id=int(cat_id) if cat_id else None,
            barcode=None,
            stock=100,
        )
        file_id = context.user_data.get("camera_file_id")
        if file_id:
            set_product_image(product_id, str(file_id))
            try:
                from bot.webapp import cache_product_photo, photo_cache_path

                cache = photo_cache_path(int(product_id))
                if cache.is_file():
                    cache.unlink(missing_ok=True)
                await cache_product_photo(int(product_id), str(file_id))
            except Exception:
                pass
    except Exception as exc:
        logger.exception("Camera save failed")
        if query:
            await query.answer(str(exc)[:180], show_alert=True)
        return CameraIntakeState.REVIEW

    context.user_data.pop("camera_draft", None)
    context.user_data.pop("camera_category_id", None)
    context.user_data.pop("camera_file_id", None)
    context.user_data.pop("awaiting_admin", None)

    product = get_product_by_id(product_id)
    cat = get_category(int(product["category_id"])) if product and product["category_id"] else None
    text = (
        f"✅ Saqlandi!\n"
        f"#{product_id} <b>{name}</b>\n"
        f"💰 {int(price):,} so‘m\n"
        f"🗂 {category_label(cat) if cat else '—'}"
    ).replace(",", " ")
    if query:
        await query.edit_message_text(text, parse_mode="HTML")
        await query.message.reply_text(
            "Yana qo‘shish: /foto_mahsulot",
            reply_markup=_menu(user.id) if user else None,
        )
    elif msg:
        await msg.reply_text(text, parse_mode="HTML", reply_markup=_menu(user.id) if user else None)
    return ConversationHandler.END


async def camera_cancel(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    context.user_data.pop("camera_draft", None)
    context.user_data.pop("camera_category_id", None)
    context.user_data.pop("camera_file_id", None)
    context.user_data.pop("awaiting_admin", None)
    msg = update.effective_message
    user = update.effective_user
    if msg:
        await msg.reply_text(
            "❌ Bekor qilindi.",
            reply_markup=_menu(user.id) if user else None,
        )
    return ConversationHandler.END


def build_camera_intake_conversation() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CommandHandler("foto_mahsulot", start_camera_intake),
            CommandHandler("camera_product", start_camera_intake),
            CallbackQueryHandler(start_camera_intake, pattern=r"^admin_prod:camera$"),
        ],
        name="camera_product_intake",
        states={
            CameraIntakeState.PHOTO: [
                MessageHandler(
                    (filters.PHOTO | filters.Document.IMAGE | filters.TEXT)
                    & ~filters.COMMAND,
                    camera_photo_received,
                ),
            ],
            CameraIntakeState.REVIEW: [
                CallbackQueryHandler(camera_review_callback, pattern=r"^cam:"),
            ],
            CameraIntakeState.EDIT_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, camera_edit_name),
            ],
            CameraIntakeState.EDIT_PRICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, camera_edit_price),
            ],
        },
        fallbacks=[
            MessageHandler(filters.Regex("^❌ Bekor qilish$"), camera_cancel),
            CommandHandler("cancel", camera_cancel),
            CallbackQueryHandler(camera_review_callback, pattern=r"^cam:cancel$"),
        ],
        allow_reentry=True,
    )
