"""Til, reyting, tavsiyalar, takroriy buyurtma, zonalar."""

from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from bot.config import ADMIN_IDS
from bot.database import (
    create_recurring_order,
    deactivate_recurring,
    get_order,
    get_recommended_products,
    list_delivery_zones,
    list_user_recurring,
    save_order_review,
    upsert_zone,
)
from bot.i18n import get_user_lang, set_user_lang, t
from bot.keyboards import (
    catalog_keyboard,
    language_keyboard,
    main_menu_keyboard,
    recurring_interval_keyboard,
    zones_admin_keyboard,
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


async def admin_zones_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    query = update.callback_query
    await query.answer()
    if not _is_admin(query.from_user.id):
        await query.edit_message_text("Ruxsat yo'q.")
        return
    zones = list_delivery_zones(active_only=False)
    lines = ["🗺 Yetkazish zonalari:\n"]
    if not zones:
        lines.append("Hali zona yo'q.")
    else:
        for z in zones:
            active = "✅" if z["is_active"] else "⏸"
            kw = z["keywords"] or "—"
            lines.append(
                f"{active} #{z['id']} {z['name']}: {z['price']:,} so'm\n"
                f"   Kalit: {kw}"
            )
    await query.edit_message_text(
        "\n".join(lines),
        reply_markup=zones_admin_keyboard(),
    )


async def start_add_zone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if not _is_admin(query.from_user.id):
        return ConversationHandler.END
    await query.message.reply_text(
        "Yangi zona: `Nom | kalit1,kalit2 | narx`\n"
        "Masalan: `Chilonzor | chilonzor,chilanzar | 15000`",
        parse_mode="Markdown",
    )
    context.user_data["awaiting_zone"] = True
    return 1


async def do_add_zone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = (update.message.text or "").strip()
    if text == "❌ Bekor qilish":
        context.user_data.pop("awaiting_zone", None)
        await update.message.reply_text(
            "Bekor qilindi.",
            reply_markup=main_menu_keyboard(_is_admin(update.effective_user.id)),
        )
        return ConversationHandler.END
    parts = [p.strip() for p in text.split("|")]
    if len(parts) < 3 or not parts[2].replace(" ", "").isdigit():
        await update.message.reply_text(
            "Format: `Nom | kalitlar | narx`", parse_mode="Markdown"
        )
        return 1
    name, keywords, price_s = parts[0], parts[1], parts[2]
    price = int("".join(ch for ch in price_s if ch.isdigit()))
    zone_id = upsert_zone(name=name, keywords=keywords, price=price)
    context.user_data.pop("awaiting_zone", None)
    await update.message.reply_text(
        f"✅ Zona #{zone_id} saqlandi: {name} — {price:,} so'm",
        reply_markup=main_menu_keyboard(_is_admin(update.effective_user.id)),
    )
    return ConversationHandler.END
