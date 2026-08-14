import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
# Avval repo ildizi, keyin ai_sotuvchi/.env
load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR / "ai_sotuvchi" / ".env", override=True)

DATA_DIR = Path(os.getenv("DATA_DIR", str(BASE_DIR / "data")))
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Faqat alohida token — Baraka BOT_TOKEN bilan aralashmasin
BOT_TOKEN = os.getenv("AI_SOTUVCHI_BOT_TOKEN", "").strip()
ADMIN_IDS = {
    int(x.strip())
    for x in os.getenv(
        "AI_SOTUVCHI_ADMIN_IDS", os.getenv("ADMIN_IDS", "")
    ).split(",")
    if x.strip().isdigit()
}

DATABASE_PATH = os.getenv(
    "AI_SOTUVCHI_DB", str(DATA_DIR / "ai_sotuvchi.db")
)

SHOP_NAME = os.getenv("AI_SOTUVCHI_SHOP_NAME", "AI Sotuvchi")
SHOP_PHONE = os.getenv("AI_SOTUVCHI_SHOP_PHONE", "+998 99 819 34 37")
SHOP_HOURS = os.getenv("AI_SOTUVCHI_SHOP_HOURS", "09:00 - 21:00")
MIN_ORDER_AMOUNT = int(os.getenv("AI_SOTUVCHI_MIN_ORDER", "10000"))
DELIVERY_FEE = int(os.getenv("AI_SOTUVCHI_DELIVERY_FEE", "10000"))
PRODUCT_CATEGORIES = tuple(
    c.strip()
    for c in os.getenv(
        "AI_SOTUVCHI_CATEGORIES",
        "Oziq-ovqat,Ichimliklar,Uy-ro‘zg‘or,Umumiy",
    ).split(",")
    if c.strip()
)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_BASE_URL = os.getenv(
    "OPENAI_BASE_URL", "https://api.openai.com/v1"
).rstrip("/")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def is_admin(user_id: int | None) -> bool:
    return bool(user_id) and int(user_id) in ADMIN_IDS


def money(amount: int) -> str:
    return f"{int(amount):,}".replace(",", " ") + " so‘m"
