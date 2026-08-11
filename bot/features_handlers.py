"""Til, reyting, tavsiyalar, takroriy buyurtma."""

from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from bot.config import ADMIN_IDS
from bot.database import (
    create_recurring_order,
    deactivate_recurring,
    get_order,
    get_recommended_products,
    list_user_recurring,
    save_order_review,
)
from bot.i18n import get_user_lang, set_user_lang, t
from bot.keyboards import (
    catalog_keyboard,
    language_keyboard,
    recurring_interval_keyboard,
)


def _is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def _cart_qty(user_id: int) -> dict[int, int]:
    from bot.database import get_cart

    qty: dict[int, int] = {}
    for item in get_cart(user_id):
        qty[item["product_id"]] = qty.get(item["product_id"], 0) + item["quantity"]
    return qty


async def ask_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    uid = update.effective_user.id
    lang = get_user_lang(uid)
    await update.message.reply_text(
        t("choose_lang", lang),
        reply_markup=language_keyboard(),
    )


async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    lang = query.data.split(":", 1)[1]
    set_user_lang(query.from_user.id, lang)
    await query.edit_message_text(t("lang_set", lang))


async def rating_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    parts = query.data.split(":")
    if len(parts) != 3:
        await query.answer()
        return
    order_id = int(parts[1])
    rating = int(parts[2])
    order = get_order(order_id)
    if not order or order["user_id"] != query.from_user.id:
        await query.answer("Ruxsat yo'q", show_alert=True)
        return
    if order["status"] != "delivered":
        await query.answer("Faqat yetkazilgan buyurtma", show_alert=True)
        return
    ok = save_order_review(order_id, query.from_user.id, rating)
    lang = get_user_lang(query.from_user.id)
    if not ok:
        await query.answer("Allaqachon baholangan", show_alert=True)
        return
    await query.answer()
    await query.edit_message_text(
        f"{t('rating_thanks', lang)}\nBuyurtma #{order_id}: {'⭐' * rating}"
    )
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                admin_id,
                f"⭐ Baholash #{order_id}: {'⭐' * rating} ({rating}/5)\n"
                f"Mijoz: {query.from_user.full_name}",
            )
        except Exception:
            pass


async def show_recommendations(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    uid = update.effective_user.id
    lang = get_user_lang(uid)
    products = get_recommended_products(uid, limit=8)
    if not products:
        await update.message.reply_text(t("no_recommendations", lang))
        return
    await update.message.reply_text(t("recommend_title", lang))
    await update.message.reply_text(
        "Tanlang:",
        reply_markup=catalog_keyboard(products, cart_qty=_cart_qty(uid)),
    )


async def show_recurring_list(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    uid = update.effective_user.id
    lang = get_user_lang(uid)
    rows = list_user_recurring(uid)
    if not rows:
        await update.message.reply_text(t("no_recurring", lang))
        return
    lines = ["🔁 Faol takroriy buyurtmalar:"]
    for r in rows:
        lines.append(
            f"• #{r['id']} — buyurtma #{r['source_order_id']}, "
            f"har {r['interval_days']} kun\n"
            f"  Keyingi: {str(r['next_run'])[:16]}"
        )
    lines.append("\nO'chirish: /stop_recur ID")
    await update.message.reply_text("\n".join(lines))


async def stop_recur_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    args = context.args or []
    if not args or not str(args[0]).isdigit():
        await update.message.reply_text("Foydalanish: /stop_recur 12")
        return
    rid = int(args[0])
    ok = deactivate_recurring(rid, update.effective_user.id)
    await update.message.reply_text("✅ O'chirildi" if ok else "Topilmadi")


async def recur_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "recur_cancel":
        await query.edit_message_text("Bekor qilindi.")
        return

    if data.startswith("recur:") and not data.startswith("recur_set:"):
        order_id = int(data.split(":")[1])
        order = get_order(order_id)
        if not order or order["user_id"] != query.from_user.id:
            await query.edit_message_text("Buyurtma topilmadi.")
            return
        await query.edit_message_text(
            f"🔁 Buyurtma #{order_id} ni qancha vaqtda takrorlaymiz?",
            reply_markup=recurring_interval_keyboard(order_id),
        )
        return

    if data.startswith("recur_set:"):
        _, order_id_s, days_s = data.split(":")
        order_id = int(order_id_s)
        days = int(days_s)
        order = get_order(order_id)
        if not order or order["user_id"] != query.from_user.id:
            await query.edit_message_text("Buyurtma topilmadi.")
            return
        create_recurring_order(
            user_id=query.from_user.id,
            source_order_id=order_id,
            interval_days=days,
        )
        lang = get_user_lang(query.from_user.id)
        await query.edit_message_text(t("recurring_saved", lang, days=days))
