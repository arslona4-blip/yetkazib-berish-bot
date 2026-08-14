import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# Alohida bot token (Baraka Market BOT_TOKEN dan farq qiladi)
BOT_TOKEN = os.getenv("AI_SOTUVCHI_BOT_TOKEN") or os.getenv("BOT_TOKEN", "")
ADMIN_IDS = {
    int(x.strip())
    for x in os.getenv("AI_SOTUVCHI_ADMIN_IDS", os.getenv("ADMIN_IDS", "")).split(",")
    if x.strip().isdigit()
}

DATABASE_PATH = os.getenv(
    "AI_SOTUVCHI_DB", str(DATA_DIR / "ai_sotuvchi.db")
)

SHOP_NAME = os.getenv("AI_SOTUVCHI_SHOP_NAME", "AI Sotuvchi Demo Do‘kon")
SHOP_PHONE = os.getenv("AI_SOTUVCHI_SHOP_PHONE", "+998 99 000 00 00")
SHOP_HOURS = os.getenv("AI_SOTUVCHI_SHOP_HOURS", "09:00 - 21:00")
MIN_ORDER_AMOUNT = int(os.getenv("AI_SOTUVCHI_MIN_ORDER", "10000"))

# OpenAI-compatible API (bo‘sh bo‘lsa — mahalliy qidiruv ishlaydi)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_BASE_URL = os.getenv(
    "OPENAI_BASE_URL", "https://api.openai.com/v1"
).rstrip("/")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def is_admin(user_id: int | None) -> bool:
    return bool(user_id) and int(user_id) in ADMIN_IDS


def money(amount: int) -> str:
    return f"{int(amount):,}".replace(",", " ") + " so‘m"
