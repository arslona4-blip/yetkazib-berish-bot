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


def catalog_text(limit: int = 40, category: str | None = None) -> str:
    if category:
        products = db.list_products_by_category(category)[:limit]
    else:
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


def find_products(user_text: str, limit: int = 6) -> list[Any]:
    text = (user_text or "").strip().lower()
    tokens = [t for t in re.split(r"\W+", text) if len(t) >= 3]
    found: list[Any] = []
    seen: set[int] = set()
    for token in tokens or [text]:
        for p in db.search_products(token, limit=5):
            pid = int(p["id"])
            if pid not in seen:
                seen.add(pid)
                found.append(p)
            if len(found) >= limit:
                return found
    return found


def try_quick_add(user_id: int, user_text: str) -> str | None:
    """«2 ta sut» / «sut qo‘sh» kabi buyruqlarni ushlaydi."""
    text = (user_text or "").strip().lower()
    has_add_verb = bool(
        re.search(r"(qo['‘’`]?sh|savatga|qoshib\s*qo)", text)
    )
    m_qty = re.match(r"^(\d+)\s*(?:ta|dona)?\s+(.+)$", text)
    if not has_add_verb and not m_qty:
        return None
    if m_qty:
        qty = int(m_qty.group(1))
        query = m_qty.group(2).strip()
        query = re.sub(r"\s*(qo['‘’`]?sh|ol|ber)\s*$", "", query).strip()
    else:
        qty = 1
        query = re.sub(r"\s*(qo['‘’`]?sh|savatga)\s*$", "", text).strip()
        m2 = re.match(r"^(\d+)\s*(?:ta|dona)?\s+(.+)$", query)
        if m2:
            qty = int(m2.group(1))
            query = m2.group(2).strip()
    if len(query) < 2:
        return None
    found = db.search_products(query, limit=3)
    if not found:
        return None
    best = found[0]
    for p in found:
        if query in str(p["name"]).lower():
            best = p
            break
    if len(found) > 1 and query not in str(best["name"]).lower():
        names = ", ".join(p["name"] for p in found)
        return f"Bir nechta topildi: {names}. Aniqroq yozing."
    db.cart_add(user_id, int(best["id"]), max(1, qty))
    return (
        f"✅ {best['name']} ×{max(1, qty)} savatga qo‘shildi.\n"
        f"Savat: {money(db.cart_total(user_id))}"
    )


def _local_reply(user_text: str) -> tuple[str, list[Any]]:
    text = (user_text or "").strip().lower()
    if not text:
        return (
            "Savolingizni yozing: masalan «guruch bormi?» yoki «narxlar».",
            [],
        )

    if any(w in text for w in ("salom", "assalom", "hello", "hi")):
        return (
            f"Assalomu alaykum! Men {SHOP_NAME} AI sotuvchisiman.\n"
            f"⏰ {SHOP_HOURS} · 📞 {SHOP_PHONE}\n\n"
            "Nima kerakligini yozing yoki «katalog» deb yozing.",
            [],
        )

    if any(w in text for w in ("katalog", "mahsulot", "ro‘yxat", "royxat", "nima bor")):
        return "📦 Katalog:\n\n" + catalog_text(), []

    if any(w in text for w in ("telefon", "aloqa", "manzil", "soat", "ish vaqti")):
        return f"📞 {SHOP_PHONE}\n⏰ {SHOP_HOURS}\n🏪 {SHOP_NAME}", []

    found = find_products(text)
    if found:
        lines = ["Topdim:"]
        for p in found[:6]:
            lines.append(f"• {p['name']} — {money(int(p['price']))} (#{p['id']})")
        lines.append("\nPastdagi tugmadan savatga qo‘shing.")
        return "\n".join(lines), found[:6]

    return (
        "Aniq topa olmadim. «katalog» deb yozing yoki mahsulot nomini yozing "
        "(masalan: sut, non, cola).",
        [],
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
        "Buyurtma uchun savatga qo‘shishni taklif qil. "
        "Mahsulot topilsa ID raqamini (#123) ko‘rsat.\n\n"
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


def reply_to_user(user_id: int, user_text: str) -> tuple[str, list[Any]]:
    quick = try_quick_add(user_id, user_text)
    if quick:
        return quick, []

    ai = _openai_reply(user_id, user_text)
    if ai:
        # AI javobidan ID larni olib tugma qilish
        ids = [int(x) for x in re.findall(r"#(\d+)", ai)]
        products = []
        for pid in ids[:6]:
            p = db.get_product(pid)
            if p and p["is_active"]:
                products.append(p)
        if not products:
            products = find_products(user_text)
        return ai, products

    return _local_reply(user_text)
