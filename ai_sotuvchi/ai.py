from __future__ import annotations

import json
import logging
import re
import urllib.error
import urllib.request
from typing import Any

from ai_sotuvchi.config import (
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    OPENAI_MODEL,
    SHOP_HOURS,
    SHOP_NAME,
    SHOP_PHONE,
    money,
)
from ai_sotuvchi import database as db

logger = logging.getLogger(__name__)


def catalog_text(limit: int = 40) -> str:
    products = db.list_products()[:limit]
    if not products:
        return "Hozircha mahsulot yo‘q."
    lines = []
    for p in products:
        lines.append(
            f"#{p['id']} {p['name']} — {money(int(p['price']))}"
            f" ({p['category']})"
            + (f" · {p['description']}" if p["description"] else "")
        )
    return "\n".join(lines)


def _local_reply(user_text: str) -> str:
    text = (user_text or "").strip().lower()
    if not text:
        return "Savolingizni yozing: masalan «guruch bormi?» yoki «narxlar»."

    if any(w in text for w in ("salom", "assalom", "hello", "hi")):
        return (
            f"Assalomu alaykum! Men {SHOP_NAME} AI sotuvchisiman.\n"
            f"⏰ {SHOP_HOURS} · 📞 {SHOP_PHONE}\n\n"
            "Nima kerakligini yozing yoki «katalog» deb yozing."
        )

    if any(w in text for w in ("katalog", "mahsulot", "ro‘yxat", "royxat", "nima bor")):
        return "📦 Katalog:\n\n" + catalog_text()

    if any(w in text for w in ("telefon", "aloqa", "manzil", "soat", "ish vaqti")):
        return f"📞 {SHOP_PHONE}\n⏰ {SHOP_HOURS}\n🏪 {SHOP_NAME}"

    # Oddiy qidiruv: so‘zlarni mahsulot nomidan izlash
    tokens = [t for t in re.split(r"\W+", text) if len(t) >= 3]
    found: list[Any] = []
    seen: set[int] = set()
    for token in tokens or [text]:
        for p in db.search_products(token, limit=5):
            pid = int(p["id"])
            if pid not in seen:
                seen.add(pid)
                found.append(p)

    if found:
        lines = ["Topdim:"]
        for p in found[:6]:
            lines.append(f"• {p['name']} — {money(int(p['price']))} (#{p['id']})")
        lines.append("\nSavatga qo‘shish: «+1» yoki tugmadan «Savat».")
        return "\n".join(lines)

    return (
        "Aniq topa olmadim. «katalog» deb yozing yoki mahsulot nomini yozing "
        "(masalan: sut, non, cola)."
    )


def _openai_reply(user_id: int, user_text: str) -> str | None:
    if not OPENAI_API_KEY:
        return None

    history = db.get_memory(user_id)
    system = (
        f"Sen «{SHOP_NAME}» do‘konining o‘zbek tilidagi AI sotuvchisisan. "
        f"Telefon: {SHOP_PHONE}. Ish vaqti: {SHOP_HOURS}. "
        "Qisqa, do‘stona javob ber. Faqat berilgan katalogdan foydalan. "
        "Yo‘q mahsulotni o‘ylab topma. Narxlarni so‘mda ayt. "
        "Buyurtma uchun savatga qo‘shishni taklif qil.\n\n"
        f"KATALOG:\n{catalog_text()}"
    )
    messages = [{"role": "system", "content": system}]
    for m in history[-8:]:
        if m.get("role") in {"user", "assistant"} and m.get("content"):
            messages.append({"role": m["role"], "content": m["content"]})
    messages.append({"role": "user", "content": user_text})

    payload = {
        "model": OPENAI_MODEL,
        "messages": messages,
        "temperature": 0.4,
        "max_tokens": 500,
    }
    req = urllib.request.Request(
        f"{OPENAI_BASE_URL}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=40) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        reply = data["choices"][0]["message"]["content"].strip()
        history.append({"role": "user", "content": user_text})
        history.append({"role": "assistant", "content": reply})
        db.save_memory(user_id, history)
        return reply
    except (urllib.error.URLError, urllib.error.HTTPError, KeyError, IndexError, TimeoutError) as exc:
        logger.warning("OpenAI xato: %s", exc)
        return None


def reply_to_user(user_id: int, user_text: str) -> str:
    ai = _openai_reply(user_id, user_text)
    if ai:
        return ai
    return _local_reply(user_text)
