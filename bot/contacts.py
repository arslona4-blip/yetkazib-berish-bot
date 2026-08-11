"""Admin: kontaktlar (qarz o'chirilgan)."""

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

from bot.config import ADMIN_IDS
from bot.database import create_contact, get_contact, list_contacts
from bot.keyboards import cancel_keyboard, main_menu_keyboard
from bot.timeutil import format_now_html


class ContactState(IntEnum):
    NAME = 1
    PHONE = 2
    NOTE = 3


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def menu_kb(user_id: int):
    return main_menu_keyboard(is_admin(user_id), is_admin(user_id))


def contacts_home_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("👥 Ro'yxat", callback_data="contact:list")],
            [
                InlineKeyboardButton(
                    "➕ Yangi kontakt", callback_data="contact:add"
                )
            ],
            [InlineKeyboardButton("⬅️ Admin", callback_data="admin:menu")],
        ]
    )


def contact_list_keyboard(contacts: list[dict]) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for c in contacts[:25]:
        rows.append(
            [
                InlineKeyboardButton(
                    str(c["name"]),
                    callback_data=f"contact:view:{c['id']}",
                )
            ]
        )
    rows.append(
        [InlineKeyboardButton("➕ Yangi", callback_data="contact:add")]
    )
    rows.append([InlineKeyboardButton("⬅️ Orqaga", callback_data="contact:home")])
    return InlineKeyboardMarkup(rows)


def contact_card_keyboard(_contact_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("⬅️ Ro'yxat", callback_data="contact:list")],
        ]
    )


def _format_contact_card(contact) -> str:
    phone = contact["phone"] or "—"
    note = contact["note"] or "—"
    return (
        f"👤 <b>{contact['name']}</b>\n"
        f"📞 {phone}\n"
        f"📝 {note}\n"
        f"{format_now_html()}"
    )


async def contacts_home(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query:
        await query.answer()
    if not is_admin((query.from_user if query else update.effective_user).id):
        return
    contacts = list_contacts(debtors_only=False)
    text = (
        f"👥 <b>Kontaktlar</b>\n"
        f"{format_now_html()}\n\n"
        f"Jami: <b>{len(contacts)}</b> ta"
    )
    markup = contacts_home_keyboard()
    if query:
        await query.edit_message_text(text, reply_markup=markup, parse_mode="HTML")
    else:
        await update.message.reply_text(text, reply_markup=markup, parse_mode="HTML")


async def contact_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int | None:
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        await query.edit_message_text("Ruxsat yo'q.")
        return ConversationHandler.END

    parts = (query.data or "").split(":")
    action = parts[1] if len(parts) > 1 else ""

    if action == "home":
        await contacts_home(update, context)
        return ConversationHandler.END

    if action in {"list", "debtors"}:
        contacts = list_contacts(debtors_only=False)
        if not contacts:
            text = "👥 Kontaktlar\n\nHali yo'q."
        else:
            lines = [f"<b>👥 Kontaktlar</b> ({len(contacts)})\n"]
            for c in contacts[:20]:
                phone = c.get("phone") or ""
                lines.append(f"• {c['name']}" + (f" — {phone}" if phone else ""))
            text = "\n".join(lines)
        await query.edit_message_text(
            text,
            reply_markup=contact_list_keyboard(contacts),
            parse_mode="HTML",
        )
        return ConversationHandler.END

    if action == "add":
        context.user_data["contact_draft"] = {}
        await query.edit_message_text("➕ Yangi kontakt")
        await query.message.reply_text(
            "Ismni yozing:", reply_markup=cancel_keyboard()
        )
        return ContactState.NAME

    if action == "view" and len(parts) > 2:
        cid = int(parts[2])
        contact = get_contact(cid)
        if not contact:
            await query.edit_message_text("Kontakt topilmadi.")
            return ConversationHandler.END
        await query.edit_message_text(
            _format_contact_card(contact),
            reply_markup=contact_card_keyboard(cid),
            parse_mode="HTML",
        )
        return ConversationHandler.END

    if action in {"debt", "pay", "hist"}:
        await query.answer("Qarz funksiyasi o‘chirilgan.", show_alert=True)
        await contacts_home(update, context)
        return ConversationHandler.END

    await contacts_home(update, context)
    return ConversationHandler.END


async def contact_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = (update.message.text or "").strip()
    if text == "❌ Bekor qilish":
        await update.message.reply_text(
            "Bekor qilindi.", reply_markup=menu_kb(update.effective_user.id)
        )
        return ConversationHandler.END
    context.user_data.setdefault("contact_draft", {})["name"] = text
    await update.message.reply_text(
        "Telefon (yoki — deb yozing):", reply_markup=cancel_keyboard()
    )
    return ContactState.PHONE


async def contact_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = (update.message.text or "").strip()
    if text == "❌ Bekor qilish":
        await update.message.reply_text(
            "Bekor qilindi.", reply_markup=menu_kb(update.effective_user.id)
        )
        return ConversationHandler.END
    phone = "" if text in {"—", "-", "yo'q", "yoq"} else text
    context.user_data.setdefault("contact_draft", {})["phone"] = phone
    await update.message.reply_text(
        "Izoh (ixtiyoriy, yoki —):", reply_markup=cancel_keyboard()
    )
    return ContactState.NOTE


async def contact_note(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = (update.message.text or "").strip()
    if text == "❌ Bekor qilish":
        await update.message.reply_text(
            "Bekor qilindi.", reply_markup=menu_kb(update.effective_user.id)
        )
        return ConversationHandler.END
    note = "" if text in {"—", "-", "yo'q", "yoq"} else text
    draft = context.user_data.get("contact_draft") or {}
    name = (draft.get("name") or "").strip()
    if not name:
        await update.message.reply_text(
            "Ism topilmadi. Qaytadan boshlang.",
            reply_markup=menu_kb(update.effective_user.id),
        )
        return ConversationHandler.END
    cid = create_contact(
        name,
        phone=draft.get("phone") or None,
        note=note,
        telegram_user_id=None,
    )
    context.user_data.pop("contact_draft", None)
    contact = get_contact(cid)
    await update.message.reply_text(
        f"✅ Kontakt saqlandi\n\n{_format_contact_card(contact)}",
        reply_markup=menu_kb(update.effective_user.id),
        parse_mode="HTML",
    )
    return ConversationHandler.END


def build_contact_conversations() -> list[ConversationHandler]:
    return [
        ConversationHandler(
            entry_points=[
                CallbackQueryHandler(contact_callback, pattern=r"^contact:add$"),
            ],
            states={
                ContactState.NAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, contact_name)
                ],
                ContactState.PHONE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, contact_phone)
                ],
                ContactState.NOTE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, contact_note)
                ],
            },
            fallbacks=[
                MessageHandler(filters.Regex("^❌ Bekor qilish$"), contact_name),
            ],
            allow_reentry=True,
        )
    ]
