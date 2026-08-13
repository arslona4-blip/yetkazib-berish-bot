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
    "debt": "📒 Qarzga",
    "rejected": "❌ Rad etildi",
}

DELIVERY_PRICE = int(os.getenv("DELIVERY_PRICE", "10000"))
MIN_ORDER_AMOUNT = int(os.getenv("MIN_ORDER_AMOUNT", "30000"))
BONUS_PERCENT = int(os.getenv("BONUS_PERCENT", "2"))
BONUS_RATE = int(os.getenv("BONUS_RATE", "100"))  # 100 so'm = 1 ball

SHOP_NAME = os.getenv("SHOP_NAME", "Do'kon")
SHOP_ADDRESS = os.getenv("SHOP_ADDRESS", "Toshkent sh.")
SHOP_PHONE = os.getenv("SHOP_PHONE", "+998 90 123 45 67")
SHOP_TELEGRAM = os.getenv("SHOP_TELEGRAM", "@support")
SHOP_HOURS = os.getenv("SHOP_HOURS", "09:00 - 22:00")
BOT_USERNAME = os.getenv("BOT_USERNAME", "yetkazib_berish_xizmat_bot").lstrip("@")
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

# Admin PWA brauzer kirishi (kodsiz). Railway’da o‘zgartirish mumkin.
ADMIN_APP_PIN = os.getenv("ADMIN_APP_PIN", "7788").strip()

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
