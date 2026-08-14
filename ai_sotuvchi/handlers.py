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
    SHOP_HOURS,
    SHOP_NAME,
    SHOP_PHONE,
    is_admin,
    money,
)
from ai_sotuvchi import database as db
from ai_sotuvchi.keyboards import (
    STATUS_LABELS,
    admin_order_keyboard,
    cart_keyboard,
    catalog_keyboard,
    categories_keyboard,
    main_keyboard,
    search_results_keyboard,
)

logger = logging.getLogger(__name__)

WAIT_PHONE, WAIT_ADDRESS, WAIT_NAME = range(3)


def _cart_message(uid: int) -> tuple[str, object]:
    items = db.get_cart(uid)
    if not items:
        return "🛒 Savat bo‘sh. Katalogdan qo‘shing.", None
    lines = ["🛒 <b>Savat</b>:"]
    for it in items:
        lines.append(
            f"• {it['name']} × {it['quantity']} = {money(it['line_total'])}"
        )
    total = sum(i["line_total"] for i in items)
    lines.append(f"\nJami: <b>{money(total)}</b>")
    if total < MIN_ORDER_AMOUNT:
        lines.append(f"Minimal: {money(MIN_ORDER_AMOUNT)}")
    return "\n".join(lines), cart_keyboard(items)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    db.init_db()
    text = (
        f"🤖 <b>{SHOP_NAME}</b>\n"
        "Men AI sotuvchiman — yozing, maslahat beraman, savatga qo‘shaman.\n\n"
        f"⏰ {SHOP_HOURS}\n📞 {SHOP_PHONE}\n"
        f"Minimal buyurtma: {money(MIN_ORDER_AMOUNT)}\n\n"
        "Masalan: <i>guruch bormi?</i> · <i>2 ta sut qo‘sh</i> · <i>katalog</i>"
    )
    await update.message.reply_text(
        text,
        parse_mode="HTML",
        reply_markup=main_keyboard(is_admin(user.id if user else None)),
    )


async def shop_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        f"🏪 <b>{SHOP_NAME}</b>\n⏰ {SHOP_HOURS}\n📞 {SHOP_PHONE}\n"
        f"Minimal: {money(MIN_ORDER_AMOUNT)}",
        parse_mode="HTML",
        reply_markup=main_keyboard(is_admin(update.effective_user.id)),
    )


async def show_catalog(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    cats = db.list_categories()
    if not cats:
        await update.message.reply_text("Katalog bo‘sh.")
        return
    await update.message.reply_text(
        "📦 Kategoriyani tanlang:",
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
        await update.message.reply_text("Hali buyurtma yo‘q.")
        return
    lines = ["📋 <b>Mening buyurtmalarim</b>:"]
    for o in orders:
        st = STATUS_LABELS.get(o["status"], o["status"])
        lines.append(f"#{o['id']} · {money(int(o['total']))} · {st}")
    await update.message.reply_text("\n".join(lines), parse_mode="HTML")


async def ai_hint(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data["ai_mode"] = True
    await update.message.reply_text(
        "💬 AI rejim yoqildi. Savolingizni yozing.\n"
        "Masalan: <i>cola bormi?</i> yoki <i>2 ta non qo‘sh</i>",
        parse_mode="HTML",
    )


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int | None:
    text = (update.message.text or "").strip()
    user = update.effective_user
    uid = user.id

    if text in {"📦 Katalog", "Katalog"}:
        await show_catalog(update, context)
        return ConversationHandler.END
    if text in {"🛒 Savat", "Savat"}:
        await show_cart(update, context)
        return ConversationHandler.END
    if text in {"ℹ️ Do‘kon", "Do‘kon"}:
        await shop_info(update, context)
        return ConversationHandler.END
    if text in {"💬 AI suhbat", "AI suhbat"}:
        await ai_hint(update, context)
        return ConversationHandler.END
    if text in {"📋 Mening buyurtmalarim", "Mening buyurtmalarim"}:
        await show_my_orders(update, context)
        return ConversationHandler.END
    if text in {"🛠 Admin", "Admin"} and is_admin(uid):
        await admin_panel(update, context)
        return ConversationHandler.END
    if text in {"✅ Buyurtma", "Buyurtma"}:
        return await start_order(update, context)

    m = re.match(r"^\+(\d+)$", text)
    if m:
        pid = int(m.group(1))
        product = db.get_product(pid)
        if not product or not product["is_active"]:
            await update.message.reply_text("Mahsulot topilmadi.")
            return ConversationHandler.END
        db.cart_add(uid, pid, 1)
        await update.message.reply_text(
            f"✅ {product['name']} savatga qo‘shildi.",
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
            "📦 Kategoriyani tanlang:",
            reply_markup=categories_keyboard(cats),
        )
        return

    if data.startswith("cat:"):
        key = data[4:]
        if key == "all":
            products = db.list_products()
            title = "📦 Barcha mahsulotlar"
        else:
            products = db.list_products_by_category(key)
            title = f"📦 {key}"
        if not products:
            await query.edit_message_text("Bu kategoriyada mahsulot yo‘q.")
            return
        body = title + "\n\n" + catalog_text(
            25, None if key == "all" else key
        )
        await query.edit_message_text(
            body[:3500],
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
        await query.answer(f"{product['name']} qo‘shildi")
        await context.bot.send_message(
            uid,
            f"✅ {product['name']} savatga qo‘shildi.\nJami: {money(db.cart_total(uid))}",
            reply_markup=main_keyboard(is_admin(uid)),
        )
        return

    if data.startswith("qty:"):
        _, sign, pid_s = data.split(":")
        pid = int(pid_s)
        delta = 1 if sign == "+" else -1
        db.cart_delta(uid, pid, delta)
        text, kb = _cart_message(uid)
        if kb is None:
            await query.edit_message_text(text)
        else:
            await query.edit_message_text(
                text, parse_mode="HTML", reply_markup=kb
            )
        return

    if data == "cart:clear":
        db.cart_clear(uid)
        await query.edit_message_text("🗑 Savat tozalandi.")
        return

    if data == "cart:order":
        await context.bot.send_message(
            uid,
            "Buyurtmani yakunlash uchun pastdagi «✅ Buyurtma» tugmasini bosing.",
            reply_markup=main_keyboard(is_admin(uid)),
        )
        return

    if data.startswith("ord:"):
        if not is_admin(uid):
            await query.answer("Faqat admin", show_alert=True)
            return
        parts = data.split(":")
        action, oid = parts[1], int(parts[2])
        status_map = {"ok": "accepted", "no": "cancelled", "done": "delivered"}
        status = status_map.get(action)
        if not status:
            return
        db.set_order_status(oid, status)
        label = STATUS_LABELS.get(status, status)
        await query.edit_message_text(f"Buyurtma #{oid}: {label}")
        order = db.get_order(oid)
        if order:
            try:
                await context.bot.send_message(
                    int(order["user_id"]),
                    f"Buyurtma #{oid} holati: {label}",
                )
            except Exception:
                logger.exception("Mijozga status yuborilmadi")
        return


async def start_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    uid = update.effective_user.id
    items = db.get_cart(uid)
    total = sum(i["line_total"] for i in items)
    if not items:
        await update.message.reply_text("Avval savatga mahsulot qo‘shing.")
        return ConversationHandler.END
    if total < MIN_ORDER_AMOUNT:
        await update.message.reply_text(
            f"Minimal buyurtma {money(MIN_ORDER_AMOUNT)}. Hozir: {money(total)}"
        )
        return ConversationHandler.END
    context.user_data["order"] = {}
    await update.message.reply_text("📞 Telefon raqamingizni yozing:")
    return WAIT_PHONE


async def order_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    phone = (update.message.text or "").strip()
    digits = re.sub(r"\D", "", phone)
    if len(digits) < 9:
        await update.message.reply_text("Telefon noto‘g‘ri. Qayta yozing:")
        return WAIT_PHONE
    context.user_data.setdefault("order", {})["phone"] = phone
    await update.message.reply_text("📍 Yetkazish manzilini yozing:")
    return WAIT_ADDRESS


async def order_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    address = (update.message.text or "").strip()
    if len(address) < 5:
        await update.message.reply_text("Manzil qisqa. To‘liqroq yozing:")
        return WAIT_ADDRESS
    context.user_data.setdefault("order", {})["address"] = address
    await update.message.reply_text("👤 Ismingiz:")
    return WAIT_NAME


async def order_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    name = (update.message.text or "").strip()
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

    lines = [f"✅ Buyurtma #{order_id} qabul qilindi!", f"Jami: {money(total)}"]
    for it in items:
        lines.append(f"• {it['name']} × {it['quantity']}")
    await update.message.reply_text(
        "\n".join(lines),
        reply_markup=main_keyboard(is_admin(uid)),
    )

    admin_text = (
        f"🆕 <b>Yangi buyurtma #{order_id}</b>\n"
        f"👤 {name}\n📞 {order_data.get('phone')}\n📍 {order_data.get('address')}\n"
        f"💰 {money(total)}\n"
        + "\n".join(f"• {it['name']} × {it['quantity']}" for it in items)
    )
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                admin_id,
                admin_text,
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
    text = (
        "🛠 <b>Admin</b>\n"
        f"Mahsulotlar: {st['products']}\n"
        f"Buyurtmalar: {st['orders']} (yangi: {st['new']})\n"
        f"Qabul: {st['accepted']} · Yetkazilgan: {st['delivered']}\n"
        f"Tushum: {money(st['revenue'])}\n\n"
        "<code>/add Nom | 12000 | Kategoriya</code>\n"
        "<code>/off 3</code> — mahsulotni o‘chirish\n"
        "<code>/on 3</code> — qayta yoqish\n"
        "/orders — yangi · /stats — statistika"
    )
    await update.message.reply_text(text, parse_mode="HTML")


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
        st = STATUS_LABELS.get(o["status"], o["status"])
        body = (
            f"#{o['id']} · {money(int(o['total']))} · {st}\n"
            f"{o['customer_name']} · {o['phone']}\n{o['address']}\n"
            + "\n".join(
                f"• {it.get('name')} × {it.get('quantity')}" for it in items
            )
        )
        await update.message.reply_text(
            body,
            reply_markup=admin_order_keyboard(int(o["id"]), o["status"]),
        )


async def admin_stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.effective_user.id):
        return
    st = db.admin_stats()
    await update.message.reply_text(
        "📊 Statistika\n"
        f"Mahsulotlar: {st['products']}\n"
        f"Buyurtmalar: {st['orders']}\n"
        f"Yangi: {st['new']} · Qabul: {st['accepted']} · Yetkazilgan: {st['delivered']}\n"
        f"Tushum: {money(st['revenue'])}"
    )


async def admin_add_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.effective_user.id):
        return
    raw = " ".join(context.args) if context.args else ""
    if "|" not in raw:
        await update.message.reply_text(
            "Format: /add Nom | narx | kategoriya\nMasalan: /add Sut 1L | 12000 | Ichimliklar"
        )
        return
    parts = [p.strip() for p in raw.split("|")]
    name = parts[0]
    try:
        price = int(re.sub(r"\D", "", parts[1] or "0") or "0")
    except ValueError:
        price = 0
    category = parts[2] if len(parts) > 2 else "Umumiy"
    if not name or price <= 0:
        await update.message.reply_text("Nom va narx majburiy.")
        return
    pid = db.add_product(name, price, category=category)
    await update.message.reply_text(f"✅ Qo‘shildi #{pid}: {name} — {money(price)}")


async def admin_off_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.effective_user.id):
        return
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Format: /off 3")
        return
    pid = int(context.args[0])
    if db.set_product_active(pid, False):
        await update.message.reply_text(f"⏸ #{pid} o‘chirildi (katalogdan yashirin).")
    else:
        await update.message.reply_text("Mahsulot topilmadi.")


async def admin_on_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.effective_user.id):
        return
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Format: /on 3")
        return
    pid = int(context.args[0])
    if db.set_product_active(pid, True):
        await update.message.reply_text(f"▶️ #{pid} qayta yoqildi.")
    else:
        await update.message.reply_text("Mahsulot topilmadi.")
