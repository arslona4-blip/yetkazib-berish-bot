from __future__ import annotations

import json
import logging
import re

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from ai_sotuvchi.ai import catalog_text, reply_to_user
from ai_sotuvchi.config import (
    ADMIN_IDS,
    MIN_ORDER_AMOUNT,
    is_admin,
    money,
)
from ai_sotuvchi import database as db
from ai_sotuvchi.keyboards import (
    admin_order_keyboard,
    admin_product_keyboard,
    cancel_keyboard,
    cart_keyboard,
    catalog_keyboard,
    categories_keyboard,
    main_keyboard,
    search_results_keyboard,
    skip_keyboard,
)
from ai_sotuvchi.texts import (
    admin_home,
    cart_text,
    order_receipt,
    shop_card,
    status_line,
    welcome_text,
)

logger = logging.getLogger(__name__)

WAIT_PHONE, WAIT_ADDRESS, WAIT_NAME = range(3)
WAIT_PROD_NAME, WAIT_PROD_PRICE, WAIT_PROD_PHOTO = range(10, 13)
WAIT_ADMIN_PRICE = 20


def _cart_message(uid: int) -> tuple[str, object]:
    items = db.get_cart(uid)
    total = sum(i["line_total"] for i in items)
    text = cart_text(items, total)
    return text, cart_keyboard(items) if items else None


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
    lines = ["<b>Mening buyurtmalarim</b>", "————————————"]
    for o in orders:
        lines.append(
            f"#{o['id']} · {money(int(o['total']))} · {status_line(o['status'])}"
        )
    await update.message.reply_text(
        "\n".join(lines),
        parse_mode="HTML",
        reply_markup=main_keyboard(is_admin(update.effective_user.id)),
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
    if action == "order":
        return await start_order(update, context)

    # Admin narx kiritish
    if context.user_data.get("await_price_for"):
        return await admin_price_input(update, context)

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
        _, sign, pid_s = data.split(":")
        pid = int(pid_s)
        db.cart_delta(uid, pid, 1 if sign == "+" else -1)
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

    if data == "cart:order":
        await context.bot.send_message(
            uid,
            "Buyurtmani yakunlash uchun <b>Buyurtma berish</b> tugmasini bosing.",
            parse_mode="HTML",
            reply_markup=main_keyboard(is_admin(uid)),
        )
        return

    if data.startswith("ap:") and is_admin(uid):
        parts = data.split(":")
        action, pid = parts[1], int(parts[2])
        product = db.get_product(pid)
        if not product:
            await query.answer("Topilmadi", show_alert=True)
            return
        if action == "toggle":
            new_active = not bool(product["is_active"])
            db.set_product_active(pid, new_active)
            await query.answer("Yoqildi" if new_active else "Yashirildi")
            await query.edit_message_reply_markup(
                reply_markup=admin_product_keyboard(pid, new_active)
            )
            return
        if action == "price":
            context.user_data["await_price_for"] = pid
            await context.bot.send_message(
                uid,
                f"<b>{product['name']}</b> uchun yangi narxni yozing:",
                parse_mode="HTML",
                reply_markup=cancel_keyboard(),
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
            receipt = order_receipt(
                oid,
                customer=order["customer_name"],
                phone=order["phone"],
                address=order["address"],
                items=items,
                total=int(order["total"]),
                status=status,
            )
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


async def admin_price_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = (update.message.text or "").strip()
    uid = update.effective_user.id
    if text in {"Bekor qilish", "Bekor", "❌ Bekor", "/cancel"}:
        context.user_data.pop("await_price_for", None)
        await update.message.reply_text(
            "Bekor qilindi.",
            reply_markup=main_keyboard(is_admin(uid)),
        )
        return ConversationHandler.END
    pid = int(context.user_data.get("await_price_for") or 0)
    digits = re.sub(r"\D", "", text)
    if not digits or not pid:
        await update.message.reply_text("Raqam yozing, masalan: 15000")
        return WAIT_ADMIN_PRICE
    price = int(digits)
    db.set_product_price(pid, price)
    context.user_data.pop("await_price_for", None)
    product = db.get_product(pid)
    name = product["name"] if product else f"#{pid}"
    await update.message.reply_text(
        f"Narx yangilandi: <b>{name}</b> — {money(price)}",
        parse_mode="HTML",
        reply_markup=main_keyboard(True),
    )
    return ConversationHandler.END


async def start_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    uid = update.effective_user.id
    items = db.get_cart(uid)
    total = sum(i["line_total"] for i in items)
    if not items:
        await update.message.reply_text(
            "Avval savatga mahsulot qo‘shing.",
            reply_markup=main_keyboard(is_admin(uid)),
        )
        return ConversationHandler.END
    if total < MIN_ORDER_AMOUNT:
        await update.message.reply_text(
            f"Minimal buyurtma: {money(MIN_ORDER_AMOUNT)}\n"
            f"Hozirgi savat: {money(total)}",
            reply_markup=main_keyboard(is_admin(uid)),
        )
        return ConversationHandler.END
    context.user_data["order"] = {}
    await update.message.reply_text(
        "Telefon raqamingizni yozing:\n<i>+998 90 123 45 67</i>",
        parse_mode="HTML",
        reply_markup=cancel_keyboard(),
    )
    return WAIT_PHONE


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
    uid = update.effective_user.id
    order_data = context.user_data.get("order") or {}
    items = db.get_cart(uid)
    total = sum(i["line_total"] for i in items)
    order_id = db.create_order(
        uid,
        customer_name=name,
        phone=order_data.get("phone", ""),
        address=order_data.get("address", ""),
    )
    context.user_data.pop("order", None)

    receipt = order_receipt(
        order_id,
        customer=name,
        phone=order_data.get("phone", ""),
        address=order_data.get("address", ""),
        items=items,
        total=total,
        status="new",
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
    # Oxirgi mahsulotlar
    products = db.list_products(active_only=False)[:8]
    for p in products:
        active = bool(p["is_active"])
        mark = "" if active else " (yashirin)"
        await update.message.reply_text(
            f"<b>{p['name']}</b>{mark}\n{money(int(p['price']))} · #{p['id']}",
            parse_mode="HTML",
            reply_markup=admin_product_keyboard(int(p["id"]), active),
        )


async def start_add_product(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Faqat admin.")
        return ConversationHandler.END
    context.user_data["new_product"] = {}
    await update.message.reply_text(
        "<b>Yangi mahsulot</b>\n\n1/3 — Nomini yozing\n<i>Masalan: Sut 1L</i>",
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
        "2/3 — Narxini yozing (so‘m)\n<i>Masalan: 12000</i>",
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
        "3/3 — Rasm yuboring (ixtiyoriy)\nyoki <b>O‘tkazib yuborish</b>",
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

    pid = db.add_product(name, price, category="Umumiy", image_file_id=image_id)
    context.user_data.pop("new_product", None)
    caption = f"✅ Qo‘shildi\n<b>{name}</b>\n{money(price)} · #{pid}"
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
        receipt = order_receipt(
            int(o["id"]),
            customer=o["customer_name"],
            phone=o["phone"],
            address=o["address"],
            items=items,
            total=int(o["total"]),
            status=o["status"],
        )
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
