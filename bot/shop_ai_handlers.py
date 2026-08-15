"""Yetkazib berish boti — matn orqali AI savdo."""

from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from bot.config import ADMIN_IDS, COURIER_IDS
from bot.database import add_money_to_cart, get_cart_totals, get_product
from bot.keyboards import main_menu_keyboard, shop_ai_results_keyboard
from bot.shop_ai import (
    _money_label,
    expand_kg_packs,
    format_variants,
    grams_for_money,
    kg_family_for_product,
    money,
    reply_to_user,
)


def _menu(user_id: int):
    return main_menu_keyboard(
        is_admin=user_id in ADMIN_IDS,
        is_courier=user_id in COURIER_IDS,
    )


async def shop_ai_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    text = (update.message.text or "").strip()
    if not text:
        return
    uid = update.effective_user.id
    answer, products = reply_to_user(uid, text)
    kb = shop_ai_results_keyboard(products) if products else None
    await update.message.reply_text(
        answer,
        parse_mode="HTML",
        reply_markup=kb or _menu(uid),
    )
    if kb:
        await update.message.reply_text("Menyu:", reply_markup=_menu(uid))


async def shop_ai_money_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    query = update.callback_query
    parts = (query.data or "").split(":")
    if len(parts) < 3:
        await query.answer()
        return
    pid = int(parts[1])
    amount = int(parts[2])
    product = get_product(pid)
    if not product or amount < 500:
        await query.answer("Topilmadi", show_alert=True)
        return
    price_kg = int(product["price"])
    grams = grams_for_money(price_kg, amount)
    label = _money_label(str(product["name"]), grams, amount)
    uid = query.from_user.id
    add_money_to_cart(uid, pid, amount=amount, grams=grams, label=label)
    count, total = get_cart_totals(uid)
    await query.answer("Savatga qo‘shildi")
    await query.message.reply_text(
        f"✅ <b>{label}</b> savatchaga qo‘shildi.\n"
        f"Savat: {count} ta · {money(total)}",
        parse_mode="HTML",
        reply_markup=_menu(uid),
    )


async def shop_ai_pack_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """ai_p:{kg_product_id}:{grams} — 250g/500g virtual qadoq."""
    query = update.callback_query
    parts = (query.data or "").split(":")
    if len(parts) < 3:
        await query.answer()
        return
    pid = int(parts[1])
    grams = int(parts[2])
    product = get_product(pid)
    if not product or grams < 1:
        await query.answer("Topilmadi", show_alert=True)
        return
    price_kg = int(product["price"])
    amount = max(100, int(round(price_kg * grams / 1000.0)))
    label = _money_label(str(product["name"]), grams, amount)
    uid = query.from_user.id
    add_money_to_cart(uid, pid, amount=amount, grams=grams, label=label)
    count, total = get_cart_totals(uid)
    await query.answer("Savatga qo‘shildi")
    await query.message.reply_text(
        f"✅ <b>{label}</b> savatchaga qo‘shildi.\n"
        f"Savat: {count} ta · {money(total)}",
        parse_mode="HTML",
        reply_markup=_menu(uid),
    )


async def show_kg_product_options(update: Update, product) -> bool:
    """Kg mahsulot bo‘lsa barcha hajmlarni chiqaradi. True = ko‘rsatildi."""
    query = update.callback_query
    _query, family = kg_family_for_product(product)
    packs = expand_kg_packs(family)
    if not packs:
        return False
    await query.answer()
    title = _query or str(product["name"])
    text = format_variants(title, family)
    kb = shop_ai_results_keyboard(family)
    uid = query.from_user.id
    await query.message.reply_text(
        text,
        parse_mode="HTML",
        reply_markup=kb,
    )
    await query.message.reply_text("Menyu:", reply_markup=_menu(uid))
    return True
