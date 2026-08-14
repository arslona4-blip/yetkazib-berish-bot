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
    admin_order_keyboard,
    cart_keyboard,
    catalog_keyboard,
    main_keyboard,
)

logger = logging.getLogger(__name__)

WAIT_PHONE, WAIT_ADDRESS, WAIT_NAME = range(3)
ADMIN_WAIT_PRODUCT = 10


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    db.init_db()
    text = (
        f"🤖 <b>{SHOP_NAME}</b>\n"
        "Men AI sotuvchiman — yozing, maslahat beraman, savatga qo‘shaman.\n\n"
        f"⏰ {SHOP_HOURS}\n📞 {SHOP_PHONE}\n"
        f"Minimal buyurtma: {money(MIN_ORDER_AMOUNT)}\n\n"
        "Masalan: <i>guruch bormi?</i> yoki <i>katalog</i>"
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
    products = db.list_products()
    if not products:
        await update.message.reply_text("Katalog bo‘sh.")
        return
    await update.message.reply_text(
        "📦 Katalog — qo‘shish uchun bosing:\n\n" + catalog_text(25),
        reply_markup=catalog_keyboard(products),
    )


async def show_cart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    items = db.get_cart(update.effective_user.id)
    if not items:
        await update.message.reply_text("🛒 Savat bo‘sh. Katalogdan qo‘shing.")
        return
    lines = ["🛒 <b>Savat</b>:"]
    for it in items:
        lines.append(
            f"• {it['name']} × {it['quantity']} = {money(it['line_total'])}"
        )
    total = sum(i["line_total"] for i in items)
    lines.append(f"\nJami: <b>{money(total)}</b>")
    if total < MIN_ORDER_AMOUNT:
        lines.append(f"Minimal: {money(MIN_ORDER_AMOUNT)}")
    await update.message.reply_text(
        "\n".join(lines),
        parse_mode="HTML",
        reply_markup=cart_keyboard(),
    )


async def ai_hint(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data["ai_mode"] = True
    await update.message.reply_text(
        "💬 AI rejim yoqildi. Savolingizni yozing.\n"
        "Chiqish: «📦 Katalog» yoki boshqa menyu tugmasi."
    )


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int | None:
    """Oddiy matn / AI suhbat / buyurtma bosqichlari."""
    text = (update.message.text or "").strip()
    user = update.effective_user
    uid = user.id

    # Menyu tugmalari
    if text in {"📦 Katalog", "Katalog"}:
        context.user_data["ai_mode"] = True
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
    if text in {"🛠 Admin", "Admin"} and is_admin(uid):
        await admin_panel(update, context)
        return ConversationHandler.END
    if text in {"✅ Buyurtma", "Buyurtma"}:
        return await start_order(update, context)

    # +id yoki +nom orqali tezkor qo‘shish
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

    # AI / mahalliy javob
    context.user_data["ai_mode"] = True
    answer = reply_to_user(uid, text)
    await update.message.reply_text(
        answer,
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

    if data.startswith("add:"):
        pid = int(data.split(":")[1])
        product = db.get_product(pid)
        if not product:
            await query.edit_message_text("Mahsulot topilmadi.")
            return
        db.cart_add(uid, pid, 1)
        await query.answer(f"{product['name']} qo‘shildi", show_alert=False)
        await context.bot.send_message(
            uid,
            f"✅ {product['name']} savatga qo‘shildi.\nJami: {money(db.cart_total(uid))}",
            reply_markup=main_keyboard(is_admin(uid)),
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

    if data.startswith("ord:ok:") or data.startswith("ord:no:"):
        if not is_admin(uid):
            await query.answer("Faqat admin", show_alert=True)
            return
        parts = data.split(":")
        action, oid = parts[1], int(parts[2])
        status = "accepted" if action == "ok" else "cancelled"
        db.set_order_status(oid, status)
        order = db.get_order(oid)
        await query.edit_message_text(
            f"Buyurtma #{oid}: {'✅ qabul' if status == 'accepted' else '❌ bekor'}"
        )
        if order:
            try:
                await context.bot.send_message(
                    int(order["user_id"]),
                    f"Buyurtma #{oid} holati: "
                    f"{'qabul qilindi ✅' if status == 'accepted' else 'bekor qilindi ❌'}",
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
                reply_markup=admin_order_keyboard(order_id),
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
    orders = db.list_new_orders(10)
    products = db.list_products(active_only=False)
    text = (
        "🛠 <b>Admin</b>\n"
        f"Mahsulotlar: {len(products)}\n"
        f"Yangi buyurtmalar: {len(orders)}\n\n"
        "Yangi mahsulot: <code>/add Guruch 1kg | 18000 | Oziq-ovqat</code>\n"
        "Buyurtmalar: /orders"
    )
    await update.message.reply_text(text, parse_mode="HTML")


async def admin_orders_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.effective_user.id):
        return
    orders = db.list_new_orders(15)
    if not orders:
        await update.message.reply_text("Yangi buyurtma yo‘q.")
        return
    for o in orders:
        try:
            items = json.loads(o["items_json"] or "[]")
        except json.JSONDecodeError:
            items = []
        body = (
            f"#{o['id']} · {money(int(o['total']))}\n"
            f"{o['customer_name']} · {o['phone']}\n{o['address']}\n"
            + "\n".join(
                f"• {it.get('name')} × {it.get('quantity')}" for it in items
            )
        )
        await update.message.reply_text(
            body, reply_markup=admin_order_keyboard(int(o["id"]))
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
