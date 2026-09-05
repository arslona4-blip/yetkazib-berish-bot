import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_IDS = {
    int(admin_id.strip())
    for admin_id in os.getenv("ADMIN_IDS", "").split(",")
    if admin_id.strip().isdigit()
}
COURIER_IDS = {
    int(cid.strip())
    for cid in os.getenv("COURIER_IDS", "").split(",")
    if cid.strip().isdigit()
}
# Bo'sh bo'lsa — adminlar ham kuryer panelidan foydalana oladi
if not COURIER_IDS:
    COURIER_IDS = set(ADMIN_IDS)
PAYMENT_PROVIDER_TOKEN = os.getenv("PAYMENT_PROVIDER_TOKEN", "").strip()
DATABASE_PATH = os.getenv("DATABASE_PATH", str(DATA_DIR / "bot.db"))

ORDER_STATUS_LABELS = {
    "new": "🆕 Yangi",
    "accepted": "✅ Qabul qilindi",
    "in_delivery": "🚚 Yo'lda",
    "delivered": "📦 Yetkazildi",
    "cancelled": "❌ Bekor qilindi",
}

PAYMENT_STATUS_LABELS = {
    "pending": "⏳ Kutilmoqda",
    "cash": "💵 Naqd",
    "card_waiting": "💳 Karta (tekshirilmoqda)",
    "paid": "✅ To'langan",
    "debt": "📒 Qarz (eski)",  # yangi qarz yo‘q; eski yozuvlar uchun
    "rejected": "❌ Rad etildi",
}

DELIVERY_FEE_THRESHOLD = int(os.getenv("DELIVERY_FEE_THRESHOLD", "50000"))
DELIVERY_FEE_LOW = int(os.getenv("DELIVERY_FEE_LOW", "5000"))
DELIVERY_FEE_HIGH = int(
    os.getenv("DELIVERY_FEE_HIGH") or os.getenv("DELIVERY_PRICE", "10000")
)
# Eski kod / Railway DELIVERY_PRICE — yuqori stavka
DELIVERY_PRICE = DELIVERY_FEE_HIGH
# Minimal buyurtma — 10 000 so'm (Railway MIN_ORDER_AMOUNT env e'tiborga olinmaydi)
MIN_ORDER_AMOUNT = 10000
BONUS_PERCENT = int(os.getenv("BONUS_PERCENT", "2"))
BONUS_RATE = int(os.getenv("BONUS_RATE", "100"))  # 100 so'm = 1 ball

# 100 000+ buyurtmaga bepul 1L ichimlik
GIFT_DRINK_THRESHOLD = int(os.getenv("GIFT_DRINK_THRESHOLD", "100000"))
GIFT_DRINK_OPTIONS = (
    "🥤 Coca-Cola 1L",
    "🔵 Pepsi 1L",
    "🧡 Fanta 1L",
)


def _som(amount: int) -> str:
    return f"{int(amount):,}".replace(",", " ")


def delivery_rates_html() -> str:
    """Mijozga ko‘rinadigan yetkazish tariflari."""
    thr = _som(DELIVERY_FEE_THRESHOLD)
    low = _som(DELIVERY_FEE_LOW)
    high = _som(DELIVERY_FEE_HIGH)
    return (
        f"🚚 <b>Yetkazish narxi</b>\n"
        f"• {thr} so‘mgacha — <b>{low} so‘m</b>\n"
        f"• {thr} so‘mdan yuqori — <b>{high} so‘m</b>"
    )


def delivery_rates_plain() -> str:
    thr = _som(DELIVERY_FEE_THRESHOLD)
    low = _som(DELIVERY_FEE_LOW)
    high = _som(DELIVERY_FEE_HIGH)
    return (
        f"🚚 Yetkazish narxi\n"
        f"• {thr} so‘mgacha — {low} so‘m\n"
        f"• {thr} so‘mdan yuqori — {high} so‘m"
    )


def gift_drink_promo_html() -> str:
    """E’tiborni tortadigan bepul ichimlik aksiyasi."""
    thr = _som(GIFT_DRINK_THRESHOLD)
    return (
        f"🎁 <b>SUPER AKSIYA!</b>\n"
        f"━━━━━━━━━━━━━━\n"
        f"🛒 Buyurtma <b>{thr} so‘m</b> va undan yuqori bo‘lsa —\n"
        f"<b>BEPUL 1 litr ichimlik</b> tanlaysiz:\n\n"
        f"🥤 <b>Coca-Cola</b> 1L\n"
        f"🔵 <b>Pepsi</b> 1L\n"
        f"🧡 <b>Fanta</b> 1L\n"
        f"━━━━━━━━━━━━━━\n"
        f"✨ Tanlov — o‘zingizniki!"
    )


def gift_drink_promo_plain() -> str:
    thr = _som(GIFT_DRINK_THRESHOLD)
    return (
        f"🎁 SUPER AKSIYA!\n"
        f"Buyurtma {thr} so‘m+ bo‘lsa — BEPUL 1L ichimlik:\n"
        f"🥤 Coca-Cola · 🔵 Pepsi · 🧡 Fanta"
    )


def gift_drink_progress_html(subtotal: int) -> str:
    """Savat summasi bo‘yicha aksiya holati."""
    amount = max(0, int(subtotal or 0))
    thr = GIFT_DRINK_THRESHOLD
    if amount >= thr:
        return (
            f"🎉 <b>Tabriklaymiz!</b> Sovg‘angiz tayyor!\n"
            f"Tanlang: 🥤 Coca-Cola · 🔵 Pepsi · 🧡 Fanta (1L)"
        )
    left = thr - amount
    return (
        f"🎁 Yana <b>{_som(left)} so‘m</b> qo‘shsangiz —\n"
        f"BEPUL 🥤 Coca-Cola / 🔵 Pepsi / 🧡 Fanta 1L!"
    )


SHOP_NAME = os.getenv("SHOP_NAME", "Do'kon")
SHOP_ADDRESS = os.getenv("SHOP_ADDRESS", "Toshkent sh.")
SHOP_PHONE = os.getenv("SHOP_PHONE", "+998 90 123 45 67")
SHOP_TELEGRAM = os.getenv("SHOP_TELEGRAM", "@support")
SHOP_HOURS = os.getenv("SHOP_HOURS", "09:00 - 22:00")
BOT_USERNAME = os.getenv("BOT_USERNAME", "yetkazib_berish_xizmat_bot").lstrip("@")


def _mahalla_bot_cta() -> tuple[str, str]:
    """Mahalla reklama CTA: (html, plain)."""
    shop_link = (os.getenv("SHOP_BOT_LINK") or "").strip()
    env_user = (os.getenv("BOT_USERNAME") or "").strip().lstrip("@")
    if shop_link:
        return (
            f'🛒 <a href="{shop_link}">Bot orqali buyurtma bering</a>',
            f"🛒 Buyurtma: {shop_link}",
        )
    if env_user:
        link = f"https://t.me/{env_user}"
        return (
            f"🛒 Bot: <b>@{env_user}</b>\n🔗 {link}",
            f"🛒 Bot: @{env_user}\n🔗 {link}",
        )
    if BOT_USERNAME:
        link = f"https://t.me/{BOT_USERNAME}"
        return (
            f"🛒 Bot: <b>@{BOT_USERNAME}</b>\n🔗 {link}",
            f"🛒 Bot: @{BOT_USERNAME}\n🔗 {link}",
        )
    return (
        "🛒 Bot orqali buyurtma bering",
        "🛒 Bot orqali buyurtma bering",
    )


def mahalla_promo_html() -> str:
    """Mahalla guruhlariga forward qilish uchun qisqa HTML caption."""
    thr = _som(GIFT_DRINK_THRESHOLD)
    cta_html, _ = _mahalla_bot_cta()
    return (
        f"📣 <b>{SHOP_NAME}</b> — mahallangizga yetkazamiz!\n"
        f"━━━━━━━━━━━━━━\n"
        f"{delivery_rates_html()}\n\n"
        f"🎁 <b>{thr} so‘m+</b> → <b>BEPUL 1L</b> ichimlik\n"
        f"🥤 Coca-Cola · 🔵 Pepsi · 🧡 Fanta\n"
        f"━━━━━━━━━━━━━━\n"
        f"{cta_html}"
    )


def mahalla_promo_plain() -> str:
    """Nusxa olish uchun oddiy matn."""
    thr = _som(GIFT_DRINK_THRESHOLD)
    _, cta_plain = _mahalla_bot_cta()
    return (
        f"📣 {SHOP_NAME} — mahallangizga yetkazamiz!\n"
        f"{delivery_rates_plain()}\n"
        f"🎁 {thr} so‘m+ → BEPUL 1L ichimlik (Cola/Pepsi/Fanta)\n"
        f"{cta_plain}"
    )


REFERRAL_BONUS = int(os.getenv("REFERRAL_BONUS", "1000"))
WEBAPP_PORT = int(os.getenv("PORT") or os.getenv("WEBAPP_PORT", "8088"))
# Cloudflare tunnel / Railway HTTPS URL, masalan https://xxxx.up.railway.app
MINIAPP_URL = os.getenv("MINIAPP_URL", "").rstrip("/")

CARD_NUMBER = os.getenv("CARD_NUMBER", "").strip()
CARD_HOLDER = os.getenv("CARD_HOLDER", SHOP_NAME).strip()
PAYME_LINK = os.getenv("PAYME_LINK", "").strip()
CLICK_LINK = os.getenv("CLICK_LINK", "").strip()

LOW_STOCK_THRESHOLD = int(os.getenv("LOW_STOCK_THRESHOLD", "5"))
DAILY_REPORT_HOUR = int(os.getenv("DAILY_REPORT_HOUR", "21"))
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "").rstrip("/")
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "telegram")
WEBHOOK_PORT = int(os.getenv("WEBHOOK_LISTEN_PORT", "0") or "0")
DATABASE_URL = os.getenv("DATABASE_URL", "")  # reserved; SQLite primary
DEFAULT_LANG = os.getenv("DEFAULT_LANG", "uz")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_BASE_URL = os.getenv(
    "OPENAI_BASE_URL", "https://api.openai.com/v1"
).rstrip("/")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Admin PWA brauzer kirishi (kodsiz). Railway’da o‘zgartirish mumkin.
ADMIN_APP_PIN = os.getenv("ADMIN_APP_PIN", "7788").strip()

# /start da chiqadigan rasm / GIF (bo‘sh bo‘lsa — faqat matn)
_WELCOME_DEFAULT = BASE_DIR / "bot" / "assets" / "welcome.jpg"
WELCOME_PHOTO_PATH = Path(
    os.getenv("WELCOME_PHOTO_PATH", str(_WELCOME_DEFAULT))
).expanduser()
_WELCOME_GIF_DEFAULT = BASE_DIR / "bot" / "assets" / "welcome.gif"
WELCOME_ANIMATION_PATH = Path(
    os.getenv("WELCOME_ANIMATION_PATH", str(_WELCOME_GIF_DEFAULT))
).expanduser()

# Buyurtma qabulida o‘zbekcha ovoz (edge-tts, Madina)
_VOICE_CONFIRM_RAW = os.getenv("VOICE_CONFIRM", "1").strip().lower()
VOICE_CONFIRM_ENABLED = _VOICE_CONFIRM_RAW not in {"0", "false", "no", "off"}
VOICE_CONFIRM_VOICE = os.getenv(
    "VOICE_CONFIRM_VOICE", "uz-UZ-MadinaNeural"
).strip() or "uz-UZ-MadinaNeural"
# Ovoz matni. Placeholderlar: {shop} {order} {total}
# {order}/{total} — o‘zbekcha so‘z (yetmish uch, qirq to‘qqiz ming)
VOICE_CONFIRM_SCRIPT = os.getenv(
    "VOICE_CONFIRM_SCRIPT",
    "Assalomu alaykum! Baraka Market yetkazib berish xizmatiga xush kelibsiz. "
    "Buyurtmangiz qabul qilindi. "
    "Buyurtma raqami: {order}. "
    "Jami: {total} so‘m. "
    "Buyurtmangiz uchun rahmat. "
    "Baraka Market yetkazib berish xodimlari sizdan mamnun.",
).strip()

# /start da xush kelibsiz ovozi (mijozlar uchun)
_VOICE_WELCOME_RAW = os.getenv("VOICE_WELCOME", "1").strip().lower()
VOICE_WELCOME_ENABLED = _VOICE_WELCOME_RAW not in {"0", "false", "no", "off"}
VOICE_WELCOME_SCRIPT = os.getenv(
    "VOICE_WELCOME_SCRIPT",
    "Assalomu alaykum! Baraka Market yetkazib berish xizmatiga xush kelibsiz.",
).strip()

# Eski konstanta — endi bot.timeutil.get_delivery_slots() ishlatiladi
DELIVERY_SLOTS = []


def online_payment_enabled() -> bool:
    return bool(PAYMENT_PROVIDER_TOKEN) and not PAYMENT_PROVIDER_TOKEN.startswith("your_")


def card_payment_enabled() -> bool:
    return bool(CARD_NUMBER) and "XXXX" not in CARD_NUMBER


def payment_link_with_amount(base_url: str, amount: int, order_id: int) -> str:
    """Payme/Click linkiga amount va order_id qo'shadi."""
    if not base_url:
        return ""
    sep = "&" if "?" in base_url else "?"
    return f"{base_url}{sep}amount={int(amount)}&order_id={int(order_id)}"
