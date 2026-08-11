"""Professional ombor moduli — kirim, chiqim, inventar, harakatlar."""

from __future__ import annotations

from enum import IntEnum

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from bot.config import ADMIN_IDS, LOW_STOCK_THRESHOLD
from bot.database import (
    adjust_product_stock,
    get_inventory_categories,
    get_inventory_products,
    get_product_by_id,
    get_stock_movements,
    get_warehouse_summary,
    set_product_stock,
)
from bot.keyboards import (
    cancel_keyboard,
    main_menu_keyboard,
)
from bot.timeutil import format_dt, format_now_html

STOCK_REASON_LABELS = {
    "sale": "🛒 Sotuv",
    "in": "📥 Kirim",
    "out": "📤 Chiqim",
    "inventory": "📋 Inventar",
    "adjust": "✏️ Tuzatish",
}


class WhState(IntEnum):
    QTY = 1
    NOTE = 2


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def menu_kb(user_id: int):
    return main_menu_keyboard(is_admin(user_id), is_admin(user_id))


def warehouse_home_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("📥 Kirim", callback_data="wh:in"),
                InlineKeyboardButton("📤 Chiqim", callback_data="wh:out"),
            ],
            [
                InlineKeyboardButton("📋 Inventar", callback_data="wh:inv"),
                InlineKeyboardButton("📜 Harakatlar", callback_data="wh:moves"),
            ],
            [
                InlineKeyboardButton("📊 Hisobot", callback_data="wh:report"),
                InlineKeyboardButton("⚠️ Kam qoldiq", callback_data="admin:stock_low"),
            ],
            [
                InlineKeyboardButton(
                    "📁 Toifalar spiska", callback_data="admin:stock_cats"
                )
            ],
            [
                InlineKeyboardButton(
                    "📋 Hammasi (toifa bo‘yicha)", callback_data="admin:stock_all"
                )
            ],
            [InlineKeyboardButton("⬅️ Admin panel", callback_data="admin:menu")],
        ]
    )


def warehouse_pick_categories_keyboard(
    categories: list[dict], mode: str
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for cat in categories:
        label = f"📁 {cat['category_name']} — {cat['product_count']} ta"
        if len(label) > 64:
            label = label[:61] + "..."
        rows.append(
            [
                InlineKeyboardButton(
                    label,
                    callback_data=f"wh:{mode}_cat:{cat['category_id']}",
                )
            ]
        )
    rows.append([InlineKeyboardButton("⬅️ Ombor", callback_data="admin:stock")])
    return InlineKeyboardMarkup(rows)


def warehouse_pick_products_keyboard(products, mode: str) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for p in products[:40]:
        stock = int(p["stock"] if "stock" in p.keys() else 0)
        mark = "⚠️" if stock <= LOW_STOCK_THRESHOLD else "✅"
        label = f"{mark} {p['name']} — {stock}"
        if len(label) > 64:
            label = label[:61] + "..."
        rows.append(
            [
                InlineKeyboardButton(
                    label,
                    callback_data=f"wh:{mode}_p:{p['id']}",
                )
            ]
        )
    rows.append([InlineKeyboardButton("⬅️ Toifalar", callback_data=f"wh:{mode}")])
    return InlineKeyboardMarkup(rows)


async def show_warehouse_home(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    query = update.callback_query
    if query:
        await query.answer()
    user = query.from_user if query else update.effective_user
    if not is_admin(user.id):
        return
    s = get_warehouse_summary()
    text = (
        f"📦 <b>Professional Ombor</b>\n"
        f"{format_now_html()}\n\n"
        f"🛍 Mahsulot: <b>{s['products']}</b> ta\n"
        f"📦 Jami qoldiq: <b>{s['units']:,}</b> dona\n"
        f"⚠️ Kam qoldiq: <b>{s['low_stock']}</b> (≤ {LOW_STOCK_THRESHOLD})\n"
        f"🚫 Nol qoldiq: <b>{s['zero_stock']}</b>\n\n"
        f"<b>Bugun:</b>\n"
        f"📥 Kirim: <b>{s['today_in']:,}</b> · "
        f"📤 Chiqim: <b>{s['today_out']:,}</b>\n"
        f"📜 Harakat: <b>{s['today_moves']}</b> ta"
    )
    markup = warehouse_home_keyboard()
    if query:
        await query.edit_message_text(text, reply_markup=markup, parse_mode="HTML")
    else:
        await update.message.reply_text(text, reply_markup=markup, parse_mode="HTML")


async def warehouse_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int | None:
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        await query.edit_message_text("Ruxsat yo'q.")
        return ConversationHandler.END

    data = query.data or ""
    parts = data.split(":")
    action = parts[1] if len(parts) > 1 else ""

    if action == "home":
        await show_warehouse_home(update, context)
        return ConversationHandler.END

    if action in {"in", "out", "inv"}:
        cats = get_inventory_categories(low_only=False)
        titles = {
            "in": "📥 Kirim — toifa tanlang",
            "out": "📤 Chiqim — toifa tanlang",
            "inv": "📋 Inventar — toifa tanlang",
        }
        await query.edit_message_text(
            titles[action],
            reply_markup=warehouse_pick_categories_keyboard(cats, action),
        )
        return ConversationHandler.END

    if action.endswith("_cat") and len(parts) > 2:
        mode = action.replace("_cat", "")
        cat_id = int(parts[2])
        products = get_inventory_products(category_id=cat_id, limit=80)
        labels = {"in": "📥 Kirim", "out": "📤 Chiqim", "inv": "📋 Inventar"}
        await query.edit_message_text(
            f"{labels.get(mode, 'Ombor')} — mahsulot tanlang",
            reply_markup=warehouse_pick_products_keyboard(products, mode),
        )
        return ConversationHandler.END

    if action.endswith("_p") and len(parts) > 2:
        mode = action.replace("_p", "")
        product_id = int(parts[2])
        product = get_product_by_id(product_id)
        if not product:
            await query.edit_message_text("Mahsulot topilmadi.")
            return ConversationHandler.END
        stock = int(product["stock"] or 0)
        context.user_data["wh"] = {
            "mode": mode,
            "product_id": product_id,
            "name": product["name"],
            "stock": stock,
        }
        prompts = {
            "in": f"📥 <b>{product['name']}</b>\nHozirgi: {stock} dona\n\nKirim miqdorini yozing:",
            "out": f"📤 <b>{product['name']}</b>\nHozirgi: {stock} dona\n\nChiqim miqdorini yozing:",
            "inv": f"📋 <b>{product['name']}</b>\nHozirgi: {stock} dona\n\nHaqiqiy sanagani yozing:",
        }
        await query.message.reply_text(
            prompts[mode],
            reply_markup=cancel_keyboard(),
            parse_mode="HTML",
        )
        return WhState.QTY

    if action == "moves":
        moves = get_stock_movements(limit=20)
        if not moves:
            text = "📜 Harakatlar\n\nHali yozuv yo‘q."
        else:
            lines = [f"📜 <b>Ombor harakatlari</b>\n{format_now_html()}\n"]
            for m in moves:
                reason = STOCK_REASON_LABELS.get(m["reason"], m["reason"])
                delta = int(m["delta"])
                sign = f"+{delta}" if delta > 0 else str(delta)
                when = format_dt(m["created_at"]) if m["created_at"] else "—"
                note = f" · {m['note']}" if m["note"] else ""
                lines.append(
                    f"• {reason} <b>{m['product_name']}</b> {sign} "
                    f"→ {m['stock_after']} ({when}){note}"
                )
            text = "\n".join(lines)
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("⬅️ Ombor", callback_data="admin:stock")]]
            ),
            parse_mode="HTML",
        )
        return ConversationHandler.END

    if action == "report":
        s = get_warehouse_summary()
        moves_in = get_stock_movements(limit=5, reason="in")
        moves_out = get_stock_movements(limit=5, reason="out")
        text = (
            f"📊 <b>Ombor hisoboti</b>\n"
            f"{format_now_html()}\n\n"
            f"Mahsulot: {s['products']} · Qoldiq: {s['units']:,} dona\n"
            f"Kam: {s['low_stock']} · Nol: {s['zero_stock']}\n"
            f"Bugun kirim/chiqim: {s['today_in']:,} / {s['today_out']:,}\n\n"
            f"<b>Oxirgi kirimlar:</b>\n"
        )
        if moves_in:
            for m in moves_in:
                text += f"• {m['product_name']} +{m['delta']}\n"
        else:
            text += "• yo‘q\n"
        text += "\n<b>Oxirgi chiqimlar:</b>\n"
        if moves_out:
            for m in moves_out:
                text += f"• {m['product_name']} {m['delta']}\n"
        else:
            text += "• yo‘q\n"
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("⬅️ Ombor", callback_data="admin:stock")]]
            ),
            parse_mode="HTML",
        )
        return ConversationHandler.END

    await show_warehouse_home(update, context)
    return ConversationHandler.END


async def warehouse_qty(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    text = (update.message.text or "").strip()
    if text == "❌ Bekor qilish":
        context.user_data.pop("wh", None)
        await update.message.reply_text(
            "Bekor qilindi.", reply_markup=menu_kb(update.effective_user.id)
        )
        return ConversationHandler.END
    if not text.isdigit():
        await update.message.reply_text("Musbat butun son yozing.")
        return WhState.QTY
    qty = int(text)
    if qty < 0:
        await update.message.reply_text("0 yoki undan katta son yozing.")
        return WhState.QTY
    wh = context.user_data.get("wh") or {}
    if not wh.get("product_id"):
        await update.message.reply_text(
            "Sessiya tugadi. Omboradan qayta boshlang.",
            reply_markup=menu_kb(update.effective_user.id),
        )
        return ConversationHandler.END
    context.user_data["wh"]["qty"] = qty
    await update.message.reply_text(
        "Izoh yozing (ixtiyoriy) yoki — deb yuboring:",
        reply_markup=cancel_keyboard(),
    )
    return WhState.NOTE


async def warehouse_note(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    text = (update.message.text or "").strip()
    if text == "❌ Bekor qilish":
        context.user_data.pop("wh", None)
        await update.message.reply_text(
            "Bekor qilindi.", reply_markup=menu_kb(update.effective_user.id)
        )
        return ConversationHandler.END
    note = "" if text in {"—", "-", "yo'q", "yoq"} else text
    wh = context.user_data.get("wh") or {}
    mode = wh.get("mode")
    product_id = int(wh.get("product_id") or 0)
    qty = int(wh.get("qty") or 0)
    name = wh.get("name") or f"#{product_id}"
    admin_id = update.effective_user.id
    try:
        if mode == "in":
            stock = adjust_product_stock(
                product_id, qty, reason="in", note=note, admin_id=admin_id
            )
            msg = f"✅ Kirim: <b>{name}</b> +{qty}\nYangi qoldiq: <b>{stock}</b>"
        elif mode == "out":
            stock = adjust_product_stock(
                product_id, -qty, reason="out", note=note, admin_id=admin_id
            )
            msg = f"✅ Chiqim: <b>{name}</b> −{qty}\nYangi qoldiq: <b>{stock}</b>"
        elif mode == "inv":
            stock = set_product_stock(
                product_id,
                qty,
                reason="inventory",
                note=note,
                admin_id=admin_id,
            )
            msg = (
                f"✅ Inventar: <b>{name}</b>\n"
                f"Sanagan: {qty} · Saqlandi: <b>{stock}</b>"
            )
        else:
            raise ValueError("Noma'lum amal")
    except ValueError as exc:
        await update.message.reply_text(
            str(exc), reply_markup=menu_kb(update.effective_user.id)
        )
        context.user_data.pop("wh", None)
        return ConversationHandler.END

    context.user_data.pop("wh", None)
    await update.message.reply_text(
        msg,
        reply_markup=menu_kb(update.effective_user.id),
        parse_mode="HTML",
    )
    await update.message.reply_text(
        "📦 Ombor menyusi:",
        reply_markup=warehouse_home_keyboard(),
    )
    return ConversationHandler.END


def build_warehouse_conversations() -> list[ConversationHandler]:
    return [
        ConversationHandler(
            entry_points=[
                CallbackQueryHandler(
                    warehouse_callback,
                    pattern=r"^wh:(in_p|out_p|inv_p):\d+$",
                )
            ],
            states={
                WhState.QTY: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, warehouse_qty)
                ],
                WhState.NOTE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, warehouse_note)
                ],
            },
            fallbacks=[
                MessageHandler(filters.Regex("^❌ Bekor qilish$"), warehouse_qty),
            ],
            allow_reentry=True,
        )
    ]
