"""Telegram: kamera/foto orqali mahsulot kiritish (admin)."""

from __future__ import annotations

import logging
from enum import IntEnum

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from bot.category_emoji import category_label
from bot.config import ADMIN_IDS, OPENAI_API_KEY
from bot.database import (
    create_product,
    get_categories,
    get_category,
    set_product_image,
)
from bot.keyboards import cancel_keyboard, category_pick_keyboard, main_menu_keyboard
from bot.product_vision import (
    AI_KEY_REQUIRED_MSG,
    VisionKeyMissing,
    VisionParseError,
    parse_product_photo,
)

logger = logging.getLogger(__name__)


class CameraProductState(IntEnum):
    WAIT_PHOTO = 1
    CONFIRM = 2
    EDIT_NAME = 3
    EDIT_PRICE = 4
    EDIT_DESC = 5
    PICK_CATEGORY = 6


def _is_admin(user_id: int | None) -> bool:
    return bool(user_id) and int(user_id) in ADMIN_IDS


def _menu_kb(user_id: int):
    return main_menu_keyboard(True, True)


def _draft(context: ContextTypes.DEFAULT_TYPE) -> dict:
    return context.user_data.setdefault("camera_product", {})


def _clear(context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.pop("camera_product", None)
    context.user_data.pop("awaiting_admin", None)


def _format_draft(data: dict) -> str:
    price = data.get("price")
    price_s = f"{int(price):,} so‘m".replace(",", " ") if price else "— (kiriting)"
    cat_id = data.get("category_id")
    cat = get_category(int(cat_id)) if cat_id else None
    cat_s = category_label(cat) if cat else (data.get("category_hint") or "—")
    desc = data.get("description") or "—"
    return (
        "📷 <b>AI draft</b> — tekshiring\n\n"
        f"🏷 <b>{data.get('name') or '—'}</b>\n"
        f"💰 {price_s}\n"
        f"📁 {cat_s}\n"
        f"📝 {desc}\n\n"
        "To‘g‘ri bo‘lsa <b>✅ Saqlash</b>. "
        "Xato bo‘lsa maydonni tahrirlang."
    )


def _confirm_keyboard(data: dict) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton("✅ Saqlash", callback_data="cam_prod:save"),
            InlineKeyboardButton("❌ Bekor", callback_data="cam_prod:cancel"),
        ],
        [
            InlineKeyboardButton("✏️ Nom", callback_data="cam_prod:edit_name"),
            InlineKeyboardButton("💰 Narx", callback_data="cam_prod:edit_price"),
        ],
        [
            InlineKeyboardButton("📁 Toifa", callback_data="cam_prod:edit_cat"),
            InlineKeyboardButton("📄 Izoh", callback_data="cam_prod:edit_desc"),
        ],
    ]
    if data.get("price") is None:
        rows.insert(
            1,
            [
                InlineKeyboardButton(
                    "⚠️ Avval narx kiriting", callback_data="cam_prod:edit_price"
                )
            ],
        )
    return InlineKeyboardMarkup(rows)


async def start_camera_product(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Callback: admin_prod:camera yoki /foto_mahsulot."""
    user = update.effective_user
    if not user or not _is_admin(user.id):
        if update.callback_query:
            await update.callback_query.answer("Faqat admin.", show_alert=True)
        elif update.message:
            await update.message.reply_text("Faqat adminlar uchun.")
        return ConversationHandler.END

    if not OPENAI_API_KEY:
        msg = (
            f"❌ <b>{AI_KEY_REQUIRED_MSG}</b>\n\n"
            "Railway / .env da <code>OPENAI_API_KEY</code> qo‘ying "
            "(vision model: <code>OPENAI_VISION_MODEL</code> yoki "
            "<code>OPENAI_MODEL</code>)."
        )
        if update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.message.reply_text(msg, parse_mode="HTML")
        else:
            await update.message.reply_text(msg, parse_mode="HTML")
        return ConversationHandler.END

    _clear(context)
    context.user_data["awaiting_admin"] = "camera_photo"
    text = (
        "📷 <b>Foto bilan mahsulot</b>\n\n"
        "Mahsulot rasmini yuboring (kamera yoki galereya).\n"
        "AI nom, toifa, izoh va (yorliqda bo‘lsa) narxni o‘qiydi — "
        "siz tasdiqlaysiz."
    )
    if update.callback_query:
        await update.callback_query.answer()
        try:
            await update.callback_query.edit_message_text(text, parse_mode="HTML")
        except Exception:
            pass
        await update.callback_query.message.reply_text(
            "Rasmni yuboring 👇",
            reply_markup=cancel_keyboard(),
        )
    else:
        await update.message.reply_text(
            text,
            parse_mode="HTML",
            reply_markup=cancel_keyboard(),
        )
    return CameraProductState.WAIT_PHOTO


async def receive_camera_photo(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    from bot.keyboards import is_main_menu_text

    text = (update.message.text or "").strip() if update.message else ""
    if text == "❌ Bekor qilish" or "bekor" in text.casefold():
        return await cancel_camera_product(update, context)
    if is_main_menu_text(text):
        _clear(context)
        from bot.handlers import dispatch_main_menu

        await dispatch_main_menu(update, context)
        return ConversationHandler.END

    file_id = None
    mime = "image/jpeg"
    if update.message.photo:
        file_id = update.message.photo[-1].file_id
    elif update.message.document and (
        update.message.document.mime_type or ""
    ).startswith("image/"):
        file_id = update.message.document.file_id
        mime = update.message.document.mime_type or mime

    if not file_id:
        await update.message.reply_text(
            "Iltimos, rasm yuboring (kamera yoki galereya)."
        )
        return CameraProductState.WAIT_PHOTO

    if not OPENAI_API_KEY:
        await update.message.reply_text(
            f"❌ <b>{AI_KEY_REQUIRED_MSG}</b>",
            parse_mode="HTML",
            reply_markup=_menu_kb(update.effective_user.id),
        )
        _clear(context)
        return ConversationHandler.END

    status = await update.message.reply_text("⏳ AI o‘qimoqda…")
    try:
        tg_file = await context.bot.get_file(file_id)
        image_bytes = bytes(await tg_file.download_as_bytearray())
        draft = parse_product_photo(image_bytes, mime_type=mime)
    except VisionKeyMissing:
        await status.edit_text(f"❌ <b>{AI_KEY_REQUIRED_MSG}</b>", parse_mode="HTML")
        _clear(context)
        return ConversationHandler.END
    except VisionParseError as exc:
        await status.edit_text(
            f"❌ {exc}\nBoshqa rasm yuboring yoki «❌ Bekor qilish».",
        )
        return CameraProductState.WAIT_PHOTO
    except Exception as exc:
        logger.exception("camera product photo failed")
        await status.edit_text(f"❌ Xato: {exc}")
        return CameraProductState.WAIT_PHOTO

    data = _draft(context)
    data.update(draft)
    data["image_file_id"] = file_id
    context.user_data["awaiting_admin"] = "camera_confirm"

    await status.edit_text(
        _format_draft(data),
        parse_mode="HTML",
        reply_markup=_confirm_keyboard(data),
    )
    return CameraProductState.CONFIRM


async def camera_confirm_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    await query.answer()
    action = (query.data or "").split(":")[-1]
    data = _draft(context)

    if action == "cancel":
        _clear(context)
        await query.edit_message_text("❌ Bekor qilindi.")
        await query.message.reply_text(
            "Admin menyuga qayting.",
            reply_markup=_menu_kb(query.from_user.id),
        )
        return ConversationHandler.END

    if action == "edit_name":
        context.user_data["awaiting_admin"] = "camera_edit_name"
        await query.message.reply_text(
            f"Yangi nom yozing:\nHozirgi: <b>{data.get('name') or '—'}</b>",
            parse_mode="HTML",
            reply_markup=cancel_keyboard(),
        )
        return CameraProductState.EDIT_NAME

    if action == "edit_price":
        context.user_data["awaiting_admin"] = "camera_edit_price"
        cur = data.get("price")
        cur_s = f"{int(cur):,}".replace(",", " ") if cur else "—"
        await query.message.reply_text(
            f"Narxni so‘mda yozing (masalan <code>15000</code>).\nHozirgi: {cur_s}",
            parse_mode="HTML",
            reply_markup=cancel_keyboard(),
        )
        return CameraProductState.EDIT_PRICE

    if action == "edit_desc":
        context.user_data["awaiting_admin"] = "camera_edit_desc"
        await query.message.reply_text(
            f"Izoh yozing:\nHozirgi: {data.get('description') or '—'}",
            reply_markup=cancel_keyboard(),
        )
        return CameraProductState.EDIT_DESC

    if action == "edit_cat":
        cats = get_categories(active_only=True)
        if not cats:
            await query.answer("Avval toifa yarating.", show_alert=True)
            return CameraProductState.CONFIRM
        context.user_data["awaiting_admin"] = "camera_edit_cat"
        await query.message.reply_text(
            "Toifani tanlang:",
            reply_markup=category_pick_keyboard(cats, prefix="cam_prod:setcat"),
        )
        return CameraProductState.PICK_CATEGORY

    if action == "save":
        return await _save_camera_product(update, context)

    return CameraProductState.CONFIRM


async def camera_set_category(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    await query.answer()
    parts = (query.data or "").split(":")
    try:
        category_id = int(parts[-1])
    except (ValueError, IndexError):
        await query.answer("Toifa noto‘g‘ri", show_alert=True)
        return CameraProductState.PICK_CATEGORY

    data = _draft(context)
    data["category_id"] = category_id
    cat = get_category(category_id)
    if cat:
        data["category_hint"] = str(cat["name"] or "")
    context.user_data["awaiting_admin"] = "camera_confirm"
    await query.edit_message_text(
        _format_draft(data),
        parse_mode="HTML",
        reply_markup=_confirm_keyboard(data),
    )
    return CameraProductState.CONFIRM


async def edit_camera_name(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    text = (update.message.text or "").strip()
    if text == "❌ Bekor qilish":
        return await _back_to_confirm(update, context)
    if len(text) < 2:
        await update.message.reply_text("Nom juda qisqa. Qayta yozing:")
        return CameraProductState.EDIT_NAME
    data = _draft(context)
    data["name"] = text[:120]
    return await _back_to_confirm(update, context)


async def edit_camera_price(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    text = (update.message.text or "").strip()
    if text == "❌ Bekor qilish":
        return await _back_to_confirm(update, context)
    from bot.handlers import parse_price_sum

    price = parse_price_sum(text)
    if price is None:
        await update.message.reply_text(
            "Narxni yozing. Masalan: <code>12000</code>",
            parse_mode="HTML",
        )
        return CameraProductState.EDIT_PRICE
    data = _draft(context)
    data["price"] = price
    return await _back_to_confirm(update, context)


async def edit_camera_desc(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    text = (update.message.text or "").strip()
    if text == "❌ Bekor qilish":
        return await _back_to_confirm(update, context)
    data = _draft(context)
    data["description"] = "" if text in {"-", "skip"} else text[:300]
    return await _back_to_confirm(update, context)


async def _back_to_confirm(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    data = _draft(context)
    context.user_data["awaiting_admin"] = "camera_confirm"
    await update.message.reply_text(
        _format_draft(data),
        parse_mode="HTML",
        reply_markup=_confirm_keyboard(data),
    )
    return CameraProductState.CONFIRM


async def _save_camera_product(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    data = _draft(context)
    name = (data.get("name") or "").strip()
    price = data.get("price")
    if not name:
        await query.answer("Nom kerak", show_alert=True)
        return CameraProductState.CONFIRM
    if price is None:
        await query.answer("Narxni kiriting (AI topa olmagan)", show_alert=True)
        return CameraProductState.CONFIRM

    categories = get_categories(active_only=True)
    category_id = data.get("category_id")
    if not category_id and categories:
        await query.answer("Toifa tanlang", show_alert=True)
        return CameraProductState.CONFIRM
    if not categories:
        await query.answer("Avval toifa yarating", show_alert=True)
        return ConversationHandler.END

    try:
        product_id = create_product(
            name=name,
            price=int(price),
            description=str(data.get("description") or ""),
            category_id=int(category_id) if category_id else None,
            barcode=None,
            stock=100,
        )
    except Exception as exc:
        await query.answer(str(exc)[:180], show_alert=True)
        return CameraProductState.CONFIRM

    image_id = data.get("image_file_id")
    if image_id:
        try:
            set_product_image(product_id, str(image_id))
            from bot.webapp import cache_product_photo, photo_cache_path

            cache = photo_cache_path(int(product_id))
            if cache.is_file():
                cache.unlink(missing_ok=True)
            await cache_product_photo(int(product_id), str(image_id))
        except Exception:
            logger.exception("camera product image save failed")

    cat = get_category(int(category_id)) if category_id else None
    _clear(context)
    await query.edit_message_text(
        f"✅ Bazaga qo‘shildi!\n"
        f"#{product_id} <b>{name}</b>\n"
        f"💰 {int(price):,} so‘m\n"
        f"📁 {category_label(cat) if cat else '—'}",
        parse_mode="HTML",
    )
    await query.message.reply_text(
        "Yana qo‘shish: Admin → Mahsulotlar → 📷 Foto bilan qo‘shish",
        reply_markup=_menu_kb(query.from_user.id),
    )
    return ConversationHandler.END


async def cancel_camera_product(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    _clear(context)
    uid = update.effective_user.id if update.effective_user else 0
    msg = update.effective_message
    if msg:
        await msg.reply_text(
            "❌ Bekor qilindi.",
            reply_markup=_menu_kb(uid),
        )
    return ConversationHandler.END


def build_camera_product_conversation() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                start_camera_product, pattern=r"^admin_prod:camera$"
            ),
            CommandHandler("foto_mahsulot", start_camera_product),
        ],
        name="camera_product",
        states={
            CameraProductState.WAIT_PHOTO: [
                MessageHandler(
                    filters.PHOTO | filters.Document.IMAGE | filters.TEXT,
                    receive_camera_photo,
                )
            ],
            CameraProductState.CONFIRM: [
                CallbackQueryHandler(
                    camera_confirm_callback,
                    pattern=r"^cam_prod:(save|cancel|edit_name|edit_price|edit_desc|edit_cat)$",
                ),
            ],
            CameraProductState.EDIT_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, edit_camera_name)
            ],
            CameraProductState.EDIT_PRICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, edit_camera_price)
            ],
            CameraProductState.EDIT_DESC: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, edit_camera_desc)
            ],
            CameraProductState.PICK_CATEGORY: [
                CallbackQueryHandler(
                    camera_set_category, pattern=r"^cam_prod:setcat:\d+$"
                ),
                CallbackQueryHandler(
                    camera_confirm_callback,
                    pattern=r"^cam_prod:(save|cancel|edit_name|edit_price|edit_desc|edit_cat)$",
                ),
            ],
        },
        fallbacks=[
            MessageHandler(filters.Regex("^❌ Bekor qilish$"), cancel_camera_product),
            CommandHandler("cancel", cancel_camera_product),
        ],
        allow_reentry=True,
    )
