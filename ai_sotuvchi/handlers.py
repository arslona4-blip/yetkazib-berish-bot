from __future__ import annotations

import json
import logging
import re

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from ai_sotuvchi.ai import catalog_text, reply_to_user
from ai_sotuvchi.config import (
    ADMIN_IDS,
    DELIVERY_FEE,
    MIN_ORDER_AMOUNT,
    PRODUCT_CATEGORIES,
    is_admin,
    money,
)
from ai_sotuvchi import database as db
from ai_sotuvchi.keyboards import (
    admin_edit_category_keyboard,
    admin_order_keyboard,
    admin_product_edit_keyboard,
    admin_product_keyboard,
    admin_products_manage_keyboard,
    cancel_keyboard,
    cart_keyboard,
    catalog_keyboard,
    categories_keyboard,
    main_keyboard,
    my_order_keyboard,
    search_results_keyboard,
    skip_keyboard,
)
from ai_sotuvchi.texts import (
    admin_home,
    admin_product_card,
    cart_text,
    order_receipt,
    shop_card,
    status_line,
    welcome_text,
)

logger = logging.getLogger(__name__)

WAIT_PHONE, WAIT_ADDRESS, WAIT_NAME, WAIT_NOTE = range(4)
WAIT_PROD_NAME, WAIT_PROD_PRICE, WAIT_PROD_PHOTO, WAIT_PROD_CAT = range(10, 14)
WAIT_ADMIN_PRICE = 20
WAIT_BROADCAST = 30


def _category_reply_keyboard():
    from telegram import ReplyKeyboardMarkup

    rows: list[list[str]] = []
    row: list[str] = []
    for cat in PRODUCT_CATEGORIES:
        row.append(cat)
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append(["Bekor qilish"])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)


def _cart_message(uid: int) -> tuple[str, object]:
    items = db.get_cart(uid)
    total = sum(i["line_total"] for i in items)
    text = cart_text(items, total)
    return text, cart_keyboard(items) if items else None


def _receipt_from_order(order, items: list | None = None, status: str | None = None) -> str:
    if items is None:
        try:
            items = json.loads(order["items_json"] or "[]")
        except json.JSONDecodeError:
            items = []
    keys = order.keys()
    delivery = int(order["delivery_fee"] or 0) if "delivery_fee" in keys else 0
    if "subtotal" in keys and order["subtotal"]:
        subtotal = int(order["subtotal"])
    else:
        subtotal = int(order["total"]) - delivery
    return order_receipt(
        int(order["id"]),
        customer=order["customer_name"],
        phone=order["phone"],
        address=order["address"],
        items=items or [],
        total=int(order["total"]),
        status=status or order["status"],
        note=order["note"] or "",
        subtotal=subtotal,
        delivery_fee=delivery,
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    db.init_db()
    await update.message.reply_text(
        welcome_text(user.first_name if user else None),
        parse_mode="HTML",
        reply_markup=main_keyboard(is_admin(user.id if user else None)),
    )


async def shop_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        shop_card(),
        parse_mode="HTML",
        reply_markup=main_keyboard(is_admin(update.effective_user.id)),
    )


async def show_catalog(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    cats = db.list_categories()
    if not cats:
        await update.message.reply_text(
            "Katalog hozircha bo‘sh.",
            reply_markup=main_keyboard(is_admin(update.effective_user.id)),
        )
        return
    await update.message.reply_text(
        "<b>Katalog</b>\nKategoriyani tanlang:",
        parse_mode="HTML",
        reply_markup=categories_keyboard(cats),
    )


async def show_cart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text, kb = _cart_message(update.effective_user.id)
    await update.message.reply_text(
        text,
        parse_mode="HTML",
        reply_markup=kb or main_keyboard(is_admin(update.effective_user.id)),
    )


async def show_my_orders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    orders = db.list_orders_by_user(update.effective_user.id, limit=8)
    if not orders:
        await update.message.reply_text(
            "Hali buyurtma yo‘q.",
            reply_markup=main_keyboard(is_admin(update.effective_user.id)),
        )
        return
    await update.message.reply_text(
        "<b>Mening buyurtmalarim</b>",
        parse_mode="HTML",
        reply_markup=main_keyboard(is_admin(update.effective_user.id)),
    )
    for o in orders:
        try:
            items = json.loads(o["items_json"] or "[]")
        except json.JSONDecodeError:
            items = []
        delivery = int(o["delivery_fee"] or 0) if "delivery_fee" in o.keys() else 0
        subtotal = int(o["subtotal"] or 0) if "subtotal" in o.keys() else int(o["total"]) - delivery
        receipt = order_receipt(
            int(o["id"]),
            customer=o["customer_name"],
            phone=o["phone"],
            address=o["address"],
            items=items,
            total=int(o["total"]),
            status=o["status"],
            note=o["note"] or "",
            subtotal=subtotal,
            delivery_fee=delivery,
        )
        await update.message.reply_text(
            receipt,
            parse_mode="HTML",
            reply_markup=my_order_keyboard(int(o["id"])),
        )


async def ai_hint(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Savolingizni yozing.\n"
        "Masalan: <i>cola bormi?</i> yoki <i>2 ta non</i>",
        parse_mode="HTML",
        reply_markup=main_keyboard(is_admin(update.effective_user.id)),
    )


def _is_menu(text: str) -> str | None:
    mapping = {
        "Katalog": "catalog",
        "📦 Katalog": "catalog",
        "Savat": "cart",
        "🛒 Savat": "cart",
        "Buyurtma berish": "order",
        "✅ Buyurtma": "order",
        "Buyurtma": "order",
        "Mening buyurtmalarim": "myorders",
        "📋 Mening buyurtmalarim": "myorders",
        "Do‘kon haqida": "info",
        "ℹ️ Do‘kon": "info",
        "Do‘kon": "info",
        "💬 AI suhbat": "ai",
        "AI suhbat": "ai",
        "Admin": "admin",
        "🛠 Admin": "admin",
        "➕ Mahsulot": "add",
        "Mahsulot": "add",
        "📢 Xabar": "broadcast",
        "Xabar": "broadcast",
    }
    return mapping.get(text)


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int | None:
    text = (update.message.text or "").strip()
    uid = update.effective_user.id
    action = _is_menu(text)

    if action == "catalog":
        await show_catalog(update, context)
        return ConversationHandler.END
    if action == "cart":
        await show_cart(update, context)
        return ConversationHandler.END
    if action == "info":
        await shop_info(update, context)
        return ConversationHandler.END
    if action == "ai":
        await ai_hint(update, context)
        return ConversationHandler.END
    if action == "myorders":
        await show_my_orders(update, context)
        return ConversationHandler.END
    if action == "admin" and is_admin(uid):
        await admin_panel(update, context)
        return ConversationHandler.END
    if action == "add" and is_admin(uid):
        return await start_add_product(update, context)
    if action == "broadcast" and is_admin(uid):
        return await start_broadcast(update, context)
    if action == "order":
        return await start_order(update, context)

    # Admin tahrirlash (nom/narx/izoh/rasm)
    if context.user_data.get("edit_product") or context.user_data.get("await_price_for"):
        return await admin_edit_input(update, context)

    m = re.match(r"^\+(\d+)$", text)
    if m:
        pid = int(m.group(1))
        product = db.get_product(pid)
        if not product or not product["is_active"]:
            await update.message.reply_text("Mahsulot topilmadi.")
            return ConversationHandler.END
        db.cart_add(uid, pid, 1)
        await update.message.reply_text(
            f"Savatga qo‘shildi: <b>{product['name']}</b>\n"
            f"Jami: {money(db.cart_total(uid))}",
            parse_mode="HTML",
            reply_markup=main_keyboard(is_admin(uid)),
        )
        return ConversationHandler.END

    answer, products = reply_to_user(uid, text)
    kb = search_results_keyboard(products) if products else None
    await update.message.reply_text(
        answer,
        parse_mode="HTML",
        reply_markup=kb or main_keyboard(is_admin(uid)),
    )
    if kb:
        await update.message.reply_text(
            "Menyu:",
            reply_markup=main_keyboard(is_admin(uid)),
        )
    return ConversationHandler.END


async def callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data or ""
    uid = query.from_user.id

    if data == "noop":
        return

    if data == "cat:menu":
        cats = db.list_categories()
        await query.edit_message_text(
            "<b>Katalog</b>\nKategoriyani tanlang:",
            parse_mode="HTML",
            reply_markup=categories_keyboard(cats),
        )
        return

    if data.startswith("cat:"):
        key = data[4:]
        if key == "all":
            products = db.list_products()
            title = "Barcha mahsulotlar"
            body = catalog_text(25)
        else:
            products = db.list_products_by_category(key)
            title = key
            body = catalog_text(25, key)
        if not products:
            await query.edit_message_text("Bu bo‘limda mahsulot yo‘q.")
            return
        await query.edit_message_text(
            f"<b>{title}</b>\n\n{body}"[:3500],
            parse_mode="HTML",
            reply_markup=catalog_keyboard(products),
        )
        return

    if data.startswith("add:"):
        pid = int(data.split(":")[1])
        product = db.get_product(pid)
        if not product:
            await query.answer("Topilmadi", show_alert=True)
            return
        db.cart_add(uid, pid, 1)
        await query.answer("Savatga qo‘shildi")
        caption = (
            f"<b>{product['name']}</b> savatga qo‘shildi.\n"
            f"Jami: {money(db.cart_total(uid))}"
        )
        image_id = None
        try:
            image_id = product["image_file_id"]
        except (KeyError, IndexError):
            image_id = None
        if image_id:
            await context.bot.send_photo(
                uid,
                photo=image_id,
                caption=caption,
                parse_mode="HTML",
                reply_markup=main_keyboard(is_admin(uid)),
            )
        else:
            await context.bot.send_message(
                uid,
                caption,
                parse_mode="HTML",
                reply_markup=main_keyboard(is_admin(uid)),
            )
        return

    if data.startswith("qty:"):
        _, sign, cid_s = data.split(":")
        cid = int(cid_s)
        db.cart_delta(uid, cid, 1 if sign == "+" else -1)
        text, kb = _cart_message(uid)
        if kb is None:
            await query.edit_message_text(text, parse_mode="HTML")
        else:
            await query.edit_message_text(text, parse_mode="HTML", reply_markup=kb)
        return

    if data == "cart:clear":
        db.cart_clear(uid)
        await query.edit_message_text("Savat tozalandi.")
        return

    # cart:order — ConversationHandler entry orqali (bu yerda spam xabar yo‘q)

    if data.startswith("reorder:"):
        oid = int(data.split(":")[1])
        added = db.fill_cart_from_order(uid, oid)
        if added <= 0:
            await query.answer("Mahsulotlar topilmadi", show_alert=True)
            return
        await query.answer("Savatga yuklandi")
        text, kb = _cart_message(uid)
        await context.bot.send_message(
            uid,
            f"Buyurtma #{oid} savatga qayta yuklandi.\n\n{text}",
            parse_mode="HTML",
            reply_markup=kb or main_keyboard(is_admin(uid)),
        )
        return

    if data.startswith("ap:") and is_admin(uid):
        parts = data.split(":")
        action = parts[1] if len(parts) > 1 else ""
        if action == "list":
            await _send_admin_products(update, context, edit=True)
            return
        if len(parts) < 3:
            return
        pid = int(parts[2])
        product = db.get_product(pid)
        if not product and action != "list":
            await query.answer("Topilmadi", show_alert=True)
            return

        if action == "edit":
            await query.edit_message_text(
                admin_product_card(product) + "\n\n<i>Nimani o‘zgartiramiz?</i>",
                parse_mode="HTML",
                reply_markup=admin_product_edit_keyboard(
                    pid, bool(product["is_active"])
                ),
            )
            return

        if action == "toggle":
            new_active = not bool(product["is_active"])
            db.set_product_active(pid, new_active)
            product = db.get_product(pid)
            await query.answer("Yoqildi" if new_active else "Yashirildi")
            await query.edit_message_text(
                admin_product_card(product),
                parse_mode="HTML",
                reply_markup=admin_product_edit_keyboard(pid, new_active),
            )
            return

        if action == "price":
            context.user_data.pop("await_price_for", None)
            context.user_data["edit_product"] = {"id": pid, "field": "price"}
            await context.bot.send_message(
                uid,
                f"<b>{product['name']}</b>\nYangi narxni yozing (so‘m):\n"
                f"<i>Hozirgi: {money(int(product['price']))}</i>",
                parse_mode="HTML",
                reply_markup=cancel_keyboard(),
            )
            return

        if action == "name":
            context.user_data["edit_product"] = {"id": pid, "field": "name"}
            await context.bot.send_message(
                uid,
                f"Yangi nomni yozing:\n<i>Hozirgi: {product['name']}</i>",
                parse_mode="HTML",
                reply_markup=cancel_keyboard(),
            )
            return

        if action == "desc":
            context.user_data["edit_product"] = {"id": pid, "field": "desc"}
            await context.bot.send_message(
                uid,
                f"Yangi izohni yozing:\n"
                f"<i>Hozirgi: {product['description'] or '—'}</i>",
                parse_mode="HTML",
                reply_markup=cancel_keyboard(),
            )
            return

        if action == "photo":
            context.user_data["edit_product"] = {"id": pid, "field": "photo"}
            await context.bot.send_message(
                uid,
                f"<b>{product['name']}</b>\nYangi rasm yuboring:",
                parse_mode="HTML",
                reply_markup=cancel_keyboard(),
            )
            return

        if action == "cat":
            await query.edit_message_text(
                f"<b>{product['name']}</b>\nToifani tanlang:",
                parse_mode="HTML",
                reply_markup=admin_edit_category_keyboard(pid, PRODUCT_CATEGORIES),
            )
            return

        if action == "setcat":
            # ap:setcat:{pid}:{category}
            cat = parts[3] if len(parts) > 3 else ""
            if not cat:
                await query.answer("Toifa yo‘q", show_alert=True)
                return
            db.set_product_category(pid, cat)
            product = db.get_product(pid)
            await query.answer(f"Toifa: {cat}")
            await query.edit_message_text(
                admin_product_card(product),
                parse_mode="HTML",
                reply_markup=admin_product_edit_keyboard(
                    pid, bool(product["is_active"])
                ),
            )
            return

    if data.startswith("ord:"):
        if not is_admin(uid):
            await query.answer("Faqat admin", show_alert=True)
            return
        parts = data.split(":")
        action, oid = parts[1], int(parts[2])
        status_map = {
            "ok": "accepted",
            "no": "cancelled",
            "go": "delivering",
            "done": "delivered",
        }
        status = status_map.get(action)
        if not status:
            return
        db.set_order_status(oid, status)
        order = db.get_order(oid)
        try:
            items = json.loads(order["items_json"] or "[]") if order else []
        except json.JSONDecodeError:
            items = []
        if order:
            receipt = _receipt_from_order(order, items, status=status)
            await query.edit_message_text(
                receipt,
                parse_mode="HTML",
                reply_markup=admin_order_keyboard(oid, status),
            )
            try:
                await context.bot.send_message(
                    int(order["user_id"]),
                    f"Buyurtma #{oid} holati yangilandi:\n{status_line(status)}",
                    parse_mode="HTML",
                )
            except Exception:
                logger.exception("Mijozga status yuborilmadi")
        return


async def admin_edit_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Nom / narx / izoh / rasm tahrirlash."""
    uid = update.effective_user.id
    text = (update.message.text or "").strip() if update.message.text else ""

    # Eski await_price_for → edit_product ga ko‘chirish
    if context.user_data.get("await_price_for") and not context.user_data.get(
        "edit_product"
    ):
        context.user_data["edit_product"] = {
            "id": int(context.user_data.pop("await_price_for")),
            "field": "price",
        }

    edit = context.user_data.get("edit_product") or {}
    pid = int(edit.get("id") or 0)
    field = str(edit.get("field") or "")

    if text in {"Bekor qilish", "Bekor", "❌ Bekor", "/cancel"}:
        context.user_data.pop("edit_product", None)
        context.user_data.pop("await_price_for", None)
        await update.message.reply_text(
            "Bekor qilindi.",
            reply_markup=main_keyboard(is_admin(uid)),
        )
        return ConversationHandler.END

    if not pid or not field:
        context.user_data.pop("edit_product", None)
        await update.message.reply_text(
            "Tahrirlash sessiyasi tugadi.",
            reply_markup=main_keyboard(is_admin(uid)),
        )
        return ConversationHandler.END

    product = db.get_product(pid)
    if not product:
        context.user_data.pop("edit_product", None)
        await update.message.reply_text(
            "Mahsulot topilmadi.",
            reply_markup=main_keyboard(is_admin(uid)),
        )
        return ConversationHandler.END

    if field == "price":
        digits = re.sub(r"\D", "", text)
        if not digits:
            await update.message.reply_text("Raqam yozing, masalan: 15000")
            return WAIT_ADMIN_PRICE
        price = int(digits)
        db.set_product_price(pid, price)
        msg = f"Narx yangilandi: <b>{product['name']}</b> — {money(price)}"
    elif field == "name":
        if len(text) < 2:
            await update.message.reply_text("Nom kamida 2 belgi bo‘lsin:")
            return WAIT_ADMIN_PRICE
        db.set_product_name(pid, text)
        msg = f"Nom yangilandi: <b>{text}</b>"
    elif field == "desc":
        db.set_product_description(pid, text)
        msg = f"Izoh yangilandi: <b>{product['name']}</b>"
    elif field == "photo":
        if not update.message.photo:
            await update.message.reply_text("Rasm yuboring (foto).")
            return WAIT_ADMIN_PRICE
        file_id = update.message.photo[-1].file_id
        db.set_product_image(pid, file_id)
        msg = f"Rasm yangilandi: <b>{product['name']}</b>"
    else:
        context.user_data.pop("edit_product", None)
        await update.message.reply_text(
            "Noma’lum maydon.",
            reply_markup=main_keyboard(is_admin(uid)),
        )
        return ConversationHandler.END

    context.user_data.pop("edit_product", None)
    product = db.get_product(pid)
    await update.message.reply_text(
        msg + "\n\n" + admin_product_card(product),
        parse_mode="HTML",
        reply_markup=admin_product_edit_keyboard(pid, bool(product["is_active"])),
    )
    await update.message.reply_text(
        "Asosiy menyu.",
        reply_markup=main_keyboard(True),
    )
    return ConversationHandler.END


# orqaga moslik
async def admin_price_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await admin_edit_input(update, context)


async def on_admin_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Tahrirlashda rasm qabul qilish."""
    edit = context.user_data.get("edit_product") or {}
    if not edit or edit.get("field") != "photo":
        return
    if not is_admin(update.effective_user.id):
        return
    await admin_edit_input(update, context)


async def _send_admin_products(
    update: Update, context: ContextTypes.DEFAULT_TYPE, *, edit: bool = False
) -> None:
    """Admin mahsulotlar spiskasi (toifa + alifbo) — tugmadan tahrirlash."""
    products = db.list_products(active_only=False)
    products = sorted(
        products,
        key=lambda p: (
            str(p["category"] or "Umumiy").casefold(),
            str(p["name"] or "").casefold(),
            int(p["id"]),
        ),
    )
    kb = admin_products_manage_keyboard(products)
    if not products:
        text = "Mahsulot yo‘q. ➕ Mahsulot bilan qo‘shing."
    else:
        text = (
            f"<b>Mahsulotlar</b> · {len(products)} ta\n"
            "Toifa + alifbo tartibida.\n"
            "✏️ Tahrirlash: mahsulotni bosing."
        )
    if edit and update.callback_query:
        try:
            await update.callback_query.edit_message_text(
                text, parse_mode="HTML", reply_markup=kb
            )
        except Exception:
            await context.bot.send_message(
                update.effective_user.id,
                text,
                parse_mode="HTML",
                reply_markup=kb,
            )
        return
    if update.message:
        await update.message.reply_text(
            text, parse_mode="HTML", reply_markup=kb
        )


async def _begin_checkout(context: ContextTypes.DEFAULT_TYPE, uid: int, reply) -> int:
    """Buyurtma suhbatini boshlash (message yoki callback)."""
    items = db.get_cart(uid)
    total = sum(i["line_total"] for i in items)
    if not items:
        await reply(
            "Avval savatga mahsulot qo‘shing.",
            reply_markup=main_keyboard(is_admin(uid)),
        )
        return ConversationHandler.END
    if total < MIN_ORDER_AMOUNT:
        await reply(
            f"Minimal buyurtma: {money(MIN_ORDER_AMOUNT)}\n"
            f"Hozirgi savat: {money(total)}",
            reply_markup=main_keyboard(is_admin(uid)),
        )
        return ConversationHandler.END
    context.user_data["order"] = {}
    await reply(
        "Telefon raqamingizni yozing:\n<i>+998 90 123 45 67</i>",
        parse_mode="HTML",
        reply_markup=cancel_keyboard(),
    )
    return WAIT_PHONE


async def start_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    uid = update.effective_user.id

    async def reply(text: str, **kwargs):
        await update.message.reply_text(text, **kwargs)

    return await _begin_checkout(context, uid, reply)


async def start_order_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Savatdagi inline «Buyurtma berish» — to‘g‘ridan checkout."""
    query = update.callback_query
    if query:
        await query.answer()
    uid = update.effective_user.id

    async def reply(text: str, **kwargs):
        await context.bot.send_message(uid, text, **kwargs)

    return await _begin_checkout(context, uid, reply)


async def order_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    phone = (update.message.text or "").strip()
    if phone in {"Bekor qilish", "Bekor", "/cancel"}:
        return await cancel_order_flow(update, context)
    digits = re.sub(r"\D", "", phone)
    if len(digits) < 9:
        await update.message.reply_text("Telefon noto‘g‘ri. Qayta yozing:")
        return WAIT_PHONE
    context.user_data.setdefault("order", {})["phone"] = phone
    await update.message.reply_text(
        "Yetkazish manzilini yozing:",
        reply_markup=cancel_keyboard(),
    )
    return WAIT_ADDRESS


async def order_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    address = (update.message.text or "").strip()
    if address in {"Bekor qilish", "Bekor", "/cancel"}:
        return await cancel_order_flow(update, context)
    if len(address) < 5:
        await update.message.reply_text("Manzilni to‘liqroq yozing:")
        return WAIT_ADDRESS
    context.user_data.setdefault("order", {})["address"] = address
    await update.message.reply_text(
        "Ismingizni yozing:",
        reply_markup=cancel_keyboard(),
    )
    return WAIT_NAME


async def order_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    name = (update.message.text or "").strip()
    if name in {"Bekor qilish", "Bekor", "/cancel"}:
        return await cancel_order_flow(update, context)
    if len(name) < 2:
        await update.message.reply_text("Ism yozing:")
        return WAIT_NAME
    context.user_data.setdefault("order", {})["name"] = name
    await update.message.reply_text(
        "Izoh yozing (ixtiyoriy)\nyoki <b>O‘tkazib yuborish</b>",
        parse_mode="HTML",
        reply_markup=skip_keyboard(),
    )
    return WAIT_NOTE


async def order_note(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = (update.message.text or "").strip()
    if text in {"Bekor qilish", "Bekor", "/cancel"}:
        return await cancel_order_flow(update, context)
    note = ""
    if text not in {"O‘tkazib yuborish", "Otkazib yuborish", "Skip"}:
        note = text
    context.user_data.setdefault("order", {})["note"] = note
    return await _finalize_order(update, context)


async def _finalize_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    uid = update.effective_user.id
    order_data = context.user_data.get("order") or {}
    items = db.get_cart(uid)
    if not items:
        await update.message.reply_text(
            "Savat bo‘sh.",
            reply_markup=main_keyboard(is_admin(uid)),
        )
        return ConversationHandler.END
    subtotal = sum(i["line_total"] for i in items)
    name = str(order_data.get("name") or "")
    order_id = db.create_order(
        uid,
        customer_name=name,
        phone=order_data.get("phone", ""),
        address=order_data.get("address", ""),
        note=order_data.get("note", ""),
        delivery_fee=DELIVERY_FEE,
    )
    context.user_data.pop("order", None)
    total = subtotal + DELIVERY_FEE
    receipt = order_receipt(
        order_id,
        customer=name,
        phone=order_data.get("phone", ""),
        address=order_data.get("address", ""),
        items=items,
        total=total,
        status="new",
        note=order_data.get("note", ""),
        subtotal=subtotal,
        delivery_fee=DELIVERY_FEE,
    )
    await update.message.reply_text(
        "✅ Buyurtma qabul qilindi.\n\n" + receipt,
        parse_mode="HTML",
        reply_markup=main_keyboard(is_admin(uid)),
    )
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                admin_id,
                "🆕 Yangi buyurtma\n\n" + receipt,
                parse_mode="HTML",
                reply_markup=admin_order_keyboard(order_id, "new"),
            )
        except Exception:
            logger.exception("Adminga yuborilmadi: %s", admin_id)
    return ConversationHandler.END


async def cancel_order_flow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("order", None)
    await update.message.reply_text(
        "Bekor qilindi.",
        reply_markup=main_keyboard(is_admin(update.effective_user.id)),
    )
    return ConversationHandler.END


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Faqat admin.")
        return
    st = db.admin_stats()
    await update.message.reply_text(
        admin_home(st),
        parse_mode="HTML",
        reply_markup=main_keyboard(True),
    )
    await _send_admin_products(update, context, edit=False)


async def start_add_product(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Faqat admin.")
        return ConversationHandler.END
    context.user_data["new_product"] = {}
    await update.message.reply_text(
        "<b>Yangi mahsulot</b>\n\n1/4 — Nomini yozing\n<i>Masalan: Sut 1L</i>",
        parse_mode="HTML",
        reply_markup=cancel_keyboard(),
    )
    return WAIT_PROD_NAME


async def add_product_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = (update.message.text or "").strip()
    if text in {"Bekor qilish", "Bekor", "❌ Bekor", "/cancel"}:
        return await cancel_add_product(update, context)
    if len(text) < 2:
        await update.message.reply_text("Nomni yozing:")
        return WAIT_PROD_NAME
    context.user_data.setdefault("new_product", {})["name"] = text
    await update.message.reply_text(
        "2/4 — Narxini yozing (so‘m)\n<i>Masalan: 12000</i>",
        parse_mode="HTML",
        reply_markup=cancel_keyboard(),
    )
    return WAIT_PROD_PRICE


async def add_product_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = (update.message.text or "").strip()
    if text in {"Bekor qilish", "Bekor", "❌ Bekor", "/cancel"}:
        return await cancel_add_product(update, context)
    digits = re.sub(r"\D", "", text)
    if not digits:
        await update.message.reply_text("Faqat raqam: 12000")
        return WAIT_PROD_PRICE
    price = int(digits)
    if price <= 0:
        await update.message.reply_text("Narx 0 dan katta bo‘lsin:")
        return WAIT_PROD_PRICE
    context.user_data.setdefault("new_product", {})["price"] = price
    await update.message.reply_text(
        "3/4 — Rasm yuboring (ixtiyoriy)\nyoki <b>O‘tkazib yuborish</b>",
        parse_mode="HTML",
        reply_markup=skip_keyboard(),
    )
    return WAIT_PROD_PHOTO


async def add_product_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    data = context.user_data.get("new_product") or {}
    name = str(data.get("name") or "").strip()
    price = int(data.get("price") or 0)
    if not name or price <= 0:
        await update.message.reply_text(
            "Ma’lumot yo‘qaldi. Qaytadan boshlang.",
            reply_markup=main_keyboard(True),
        )
        return ConversationHandler.END

    text = (update.message.text or "").strip() if update.message.text else ""
    if text in {"Bekor qilish", "Bekor", "/cancel"}:
        return await cancel_add_product(update, context)

    image_id = None
    if update.message.photo:
        image_id = update.message.photo[-1].file_id
    elif text not in {"O‘tkazib yuborish", "Otkazib yuborish", "Skip"}:
        await update.message.reply_text(
            "Rasm yuboring yoki «O‘tkazib yuborish» ni bosing."
        )
        return WAIT_PROD_PHOTO

    context.user_data.setdefault("new_product", {})["image_file_id"] = image_id
    await update.message.reply_text(
        "4/4 — Kategoriyani tanlang:",
        reply_markup=_category_reply_keyboard(),
    )
    return WAIT_PROD_CAT


async def add_product_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = (update.message.text or "").strip()
    if text in {"Bekor qilish", "Bekor", "/cancel"}:
        return await cancel_add_product(update, context)
    category = text if text in PRODUCT_CATEGORIES else (text or "Umumiy")
    if len(category) < 2:
        await update.message.reply_text("Kategoriyani tanlang yoki yozing:")
        return WAIT_PROD_CAT

    data = context.user_data.get("new_product") or {}
    name = str(data.get("name") or "").strip()
    price = int(data.get("price") or 0)
    image_id = data.get("image_file_id")
    if not name or price <= 0:
        await update.message.reply_text(
            "Ma’lumot yo‘qaldi. Qaytadan boshlang.",
            reply_markup=main_keyboard(True),
        )
        return ConversationHandler.END

    pid = db.add_product(
        name, price, category=category, image_file_id=image_id
    )
    context.user_data.pop("new_product", None)
    caption = (
        f"✅ Qo‘shildi\n<b>{name}</b>\n"
        f"{money(price)} · {category} · #{pid}"
    )
    if image_id:
        await update.message.reply_photo(
            photo=image_id,
            caption=caption,
            parse_mode="HTML",
            reply_markup=main_keyboard(True),
        )
    else:
        await update.message.reply_text(
            caption,
            parse_mode="HTML",
            reply_markup=main_keyboard(True),
        )
    return ConversationHandler.END


async def cancel_add_product(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("new_product", None)
    await update.message.reply_text(
        "Bekor qilindi.",
        reply_markup=main_keyboard(is_admin(update.effective_user.id)),
    )
    return ConversationHandler.END


async def start_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Faqat admin.")
        return ConversationHandler.END
    customers = db.list_customer_ids()
    await update.message.reply_text(
        f"Mijozlarga xabar ({len(customers)} ta).\n"
        "Xabar matnini yozing:",
        reply_markup=cancel_keyboard(),
    )
    return WAIT_BROADCAST


async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    text = (update.message.text or "").strip()
    if text in {"Bekor qilish", "Bekor", "/cancel"}:
        await update.message.reply_text(
            "Bekor qilindi.",
            reply_markup=main_keyboard(True),
        )
        return ConversationHandler.END
    if len(text) < 2:
        await update.message.reply_text("Xabar yozing:")
        return WAIT_BROADCAST
    customers = db.list_customer_ids()
    ok = 0
    fail = 0
    for cid in customers:
        try:
            await context.bot.send_message(cid, f"📢 {text}")
            ok += 1
        except Exception:
            fail += 1
    await update.message.reply_text(
        f"Yuborildi: {ok}\nYetkmadi: {fail}",
        reply_markup=main_keyboard(True),
    )
    return ConversationHandler.END


async def admin_orders_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.effective_user.id):
        return
    status = "new"
    if context.args:
        raw = context.args[0].strip().lower()
        mapping = {
            "all": None,
            "hammasi": None,
            "new": "new",
            "yangi": "new",
            "accepted": "accepted",
            "qabul": "accepted",
            "delivering": "delivering",
            "yo‘lda": "delivering",
            "yolda": "delivering",
            "delivered": "delivered",
            "yetkazilgan": "delivered",
        }
        status = mapping.get(raw, "new")
    orders = (
        db.list_new_orders(15)
        if status == "new"
        else db.list_orders(status=status, limit=15)
    )
    if not orders:
        await update.message.reply_text("Buyurtma yo‘q.")
        return
    for o in orders:
        try:
            items = json.loads(o["items_json"] or "[]")
        except json.JSONDecodeError:
            items = []
        receipt = _receipt_from_order(o, items)
        await update.message.reply_text(
            receipt,
            parse_mode="HTML",
            reply_markup=admin_order_keyboard(int(o["id"]), o["status"]),
        )


async def admin_stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.effective_user.id):
        return
    st = db.admin_stats()
    await update.message.reply_text(admin_home(st), parse_mode="HTML")


async def admin_add_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Eski nom — endi oddiy suhbat."""
    return await start_add_product(update, context)


async def admin_off_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.effective_user.id):
        return
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Format: /off 3")
        return
    pid = int(context.args[0])
    if db.set_product_active(pid, False):
        await update.message.reply_text(f"#{pid} yashirildi.")
    else:
        await update.message.reply_text("Topilmadi.")


async def admin_on_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.effective_user.id):
        return
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Format: /on 3")
        return
    pid = int(context.args[0])
    if db.set_product_active(pid, True):
        await update.message.reply_text(f"#{pid} yoqildi.")
    else:
        await update.message.reply_text("Topilmadi.")
