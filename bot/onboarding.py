"""Mijoz uchun qisqa qo‘llanma — do‘kon, savat, buyurtma."""

from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from bot.config import MINIAPP_URL, delivery_rates_html, gift_drink_promo_html
from bot.database import set_onboarding_done
from bot.keyboards import shop_inline_button


_STEPS: list[dict[str, str]] = [
    {
        "title": "1️⃣ Mahsulot tanlash",
        "body": (
            "Pastdagi <b>🛒 Do'kon</b> tugmasini bosing — "
            "rasmli katalog ochiladi.\n\n"
            "Yoki <b>🛍 Katalog</b> orqali bot ichida tanlang.\n\n"
            "Yoqqan mahsulotni bosing — u savatchaga tushadi ✅"
        ),
    },
    {
        "title": "2️⃣ Savatchani tekshirish",
        "body": (
            "<b>🛒 Savatcha</b> ni oching.\n\n"
            "• Miqdorni oshiring / kamaytiring\n"
            "• Keraksizini olib tashlang\n"
            "• Jami summani ko‘ring\n\n"
            f"{delivery_rates_html()}"
        ),
    },
    {
        "title": "3️⃣ Buyurtma berish",
        "body": (
            "Savatdan <b>Buyurtma berish</b> ni bosing.\n\n"
            "1️⃣ Telefon raqamingiz\n"
            "2️⃣ Yetkazish manzili (yoki lokatsiya)\n"
            "3️⃣ Qulay vaqt\n"
            "4️⃣ To‘lov usuli\n\n"
            "Tasdiqlang — buyurtma qabul qilinadi 🚚"
        ),
    },
    {
        "title": "4️⃣ Tezroq: chatga yozing",
        "body": (
            "Katalog ochmasdan ham buyurtma berishingiz mumkin:\n\n"
            "💬 <i>guruch 2kg</i>\n"
            "💬 <i>cola 1.5l x 2</i>\n"
            "🍽 <i>osh uchun</i> — retsept to‘plami\n"
            "📦 <i>buyurtmam qayerda?</i>\n\n"
            "⋯ Ko‘proq → <b>🤖 AI sotuvchi</b>"
        ),
    },
    {
        "title": "5️⃣ Buyurtmani kuzatish",
        "body": (
            "<b>📋 Mening buyurtmalarim</b> — holatni kuzating:\n"
            "yangi → tayyorlanmoqda → yo‘lda → yetkazildi.\n\n"
            f"{gift_drink_promo_html()}\n\n"
            "Tayyor! Endi birinchi buyurtmangizni bering 👇"
        ),
    },
]


def _progress(step: int) -> str:
    total = len(_STEPS)
    dots = "".join("●" if i <= step else "○" for i in range(total))
    return f"{dots}  {step + 1}/{total}"


def _keyboard(step: int) -> InlineKeyboardMarkup:
    total = len(_STEPS)
    rows: list[list[InlineKeyboardButton]] = []
    nav: list[InlineKeyboardButton] = []
    if step > 0:
        nav.append(
            InlineKeyboardButton("⬅️ Orqaga", callback_data=f"onboard:{step - 1}")
        )
    if step < total - 1:
        nav.append(
            InlineKeyboardButton("Keyingi ➡️", callback_data=f"onboard:{step + 1}")
        )
    else:
        nav.append(
            InlineKeyboardButton("✅ Tushundim", callback_data="onboard:done")
        )
    rows.append(nav)

    if step < total - 1:
        rows.append(
            [InlineKeyboardButton("O‘tkazib yuborish", callback_data="onboard:skip")]
        )
    else:
        shop = shop_inline_button("🛒 Do'konni ochish")
        finish_row: list[InlineKeyboardButton] = []
        if shop:
            finish_row.append(shop)
        else:
            finish_row.append(
                InlineKeyboardButton("🛍 Katalog", callback_data="catalog:list")
            )
        rows.append(finish_row)

    return InlineKeyboardMarkup(rows)


def step_text(step: int) -> str:
    step = max(0, min(step, len(_STEPS) - 1))
    meta = _STEPS[step]
    return (
        f"📚 <b>Qisqa qo‘llanma</b>\n"
        f"{_progress(step)}\n\n"
        f"<b>{meta['title']}</b>\n\n"
        f"{meta['body']}"
    )


async def send_onboarding(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    *,
    step: int = 0,
    edit: bool = False,
) -> None:
    text = step_text(step)
    markup = _keyboard(step)
    query = update.callback_query
    if edit and query and query.message:
        try:
            await query.edit_message_text(
                text, parse_mode="HTML", reply_markup=markup
            )
            return
        except Exception:
            pass
    target = update.effective_message
    if target:
        await target.reply_text(text, parse_mode="HTML", reply_markup=markup)


async def onboarding_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    query = update.callback_query
    if not query:
        return
    data = (query.data or "").strip()
    uid = query.from_user.id if query.from_user else 0
    await query.answer()

    if data in {"onboard:done", "onboard:skip"}:
        set_onboarding_done(uid, True)
        shop = shop_inline_button("🛒 Do'konni ochish")
        rows: list[list[InlineKeyboardButton]] = []
        if shop:
            rows.append([shop])
        else:
            rows.append(
                [InlineKeyboardButton("🛍 Katalog", callback_data="catalog:list")]
            )
        rows.append(
            [InlineKeyboardButton("🛒 Savatcha", callback_data="cart:view")]
        )
        tip = (
            "✅ <b>Qo‘llanma tugadi!</b>\n\n"
            "Endi mahsulot tanlab, buyurtma berishingiz mumkin.\n"
        )
        if MINIAPP_URL:
            tip += "Eng qulay yo‘l — <b>🛒 Do'kon</b> 👇"
        else:
            tip += "<b>🛍 Katalog</b> dan boshlang 👇"
        try:
            await query.edit_message_text(
                tip, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(rows)
            )
        except Exception:
            if update.effective_message:
                await update.effective_message.reply_text(
                    tip, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(rows)
                )
        return

    if data.startswith("onboard:"):
        raw = data.split(":", 1)[1]
        if raw.isdigit():
            await send_onboarding(update, context, step=int(raw), edit=True)


async def start_onboarding_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Menyu / yordamdan qo‘llanmani qayta ochish."""
    await send_onboarding(update, context, step=0, edit=False)
