from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR / "vositachi" / ".env", override=True)

DATA_DIR = Path(os.getenv("DATA_DIR", str(BASE_DIR / "data")))
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Alohida token — Baraka BOT_TOKEN bilan aralashmasin
BOT_TOKEN = os.getenv("VOSITACHI_BOT_TOKEN", "").strip()
ADMIN_IDS = {
    int(x.strip())
    for x in os.getenv("VOSITACHI_ADMIN_IDS", os.getenv("ADMIN_IDS", "")).split(",")
    if x.strip().isdigit()
}

DATABASE_PATH = os.getenv(
    "VOSITACHI_DB", str(DATA_DIR / "vositachi.db")
)

BOT_NAME = os.getenv("VOSITACHI_BOT_NAME", "Vositachi")
