from __future__ import annotations

import json
import logging
import math
import re
import urllib.error
import urllib.request
from datetime import datetime
from typing import Any

from ai_sotuvchi.config import (
    DELIVERY_FEE,
    MIN_ORDER_AMOUNT,
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

_STOP = {
    "kerak",
    "kerakli",
    "bormi",
    "bor",
    "yoq",
    "yo‘q",
    "yuboring",
    "bering",
    "iltimos",
    "menga",
    "bizga",
    "va",
    "ham",
    "uchun",
    "dan",
    "ga",
    "ni",
    "ning",
    "x",
    "ta",
    "dona",
    "kg",
    "l",
    "lt",
    "litr",
    "gr",
    "g",
}


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
    tokens = [t for t in re.split(r"\W+", text) if len(t) >= 3 and t not in _STOP]
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


def _norm(s: str) -> str:
    return (
        (s or "")
        .lower()
        .replace("‘", "'")
        .replace("’", "'")
        .replace("ё", "e")
        .replace(",", ".")
    )


def _pack_size_from_name(name: str) -> tuple[float | None, str | None]:
    m = re.search(r"(\d+(?:\.\d+)?)\s*(kg|l|lt|litr|gr|g)\b", _norm(name))
    if not m:
        return None, None
    return float(m.group(1)), m.group(2)


def _score_product(query: str, product: Any, want_size: float | None, want_unit: str | None) -> int:
    name = _norm(str(product["name"]))
    q = _norm(query)
    score = 0
    if q and q in name:
        score += 50
    for tok in re.split(r"\W+", q):
        if len(tok) >= 3 and tok in name:
            score += 10
    if want_size is not None and want_unit:
        psize, punit = _pack_size_from_name(name)
        if psize is not None and punit:
            # unit family
            uq = want_unit
            up = punit
            if uq in {"l", "lt", "litr"}:
                uq = "l"
            if up in {"l", "lt", "litr"}:
                up = "l"
            if uq in {"gr", "g"}:
                uq = "g"
            if up in {"gr", "g"}:
                up = "g"
            if uq == up:
                score += 20
                if abs(psize - want_size) < 0.01:
                    score += 40
                elif psize <= want_size + 0.01:
                    score += 10
    return score


def _best_product(query: str, want_size: float | None = None, want_unit: str | None = None):
    q = query.strip()
    if len(q) < 2:
        return None
    candidates = db.search_products(q, limit=8)
    if not candidates and len(q) >= 4:
        candidates = find_products(q, limit=8)
    if not candidates:
        return None
    ranked = sorted(
        candidates,
        key=lambda p: _score_product(q, p, want_size, want_unit),
        reverse=True,
    )
    best = ranked[0]
    if _score_product(q, best, want_size, want_unit) <= 0:
        return None
    return best


def _parse_segment(seg: str) -> dict[str, Any] | None:
    raw = _norm(seg).strip()
    if len(raw) < 2:
        return None
    raw = re.sub(r"\b(kerak|bormi|bering|iltimos|menga)\b", " ", raw)
    raw = re.sub(r"\s+", " ", raw).strip()

    qty = 1
    want_size = None
    want_unit = None

    # x2 / ×2
    m = re.search(r"[x×*]\s*(\d+)\b", raw)
    if m:
        qty = max(1, int(m.group(1)))
        raw = (raw[: m.start()] + " " + raw[m.end() :]).strip()

    # 2 ta / 2 dona
    m = re.search(r"\b(\d+)\s*(?:ta|dona)\b", raw)
    if m:
        qty = max(1, int(m.group(1)))
        raw = (raw[: m.start()] + " " + raw[m.end() :]).strip()

    # 2kg / 1.5 l / 0.5 kg
    m = re.search(r"(\d+(?:\.\d+)?)\s*(kg|l|lt|litr|gr|g)\b", raw)
    if m:
        want_size = float(m.group(1))
        want_unit = m.group(2)
        raw = (raw[: m.start()] + " " + raw[m.end() :]).strip()

    # leading qty still there?
    m = re.match(r"^(\d+)\s+(.+)$", raw)
    if m and want_size is None:
        qty = max(1, int(m.group(1)))
        raw = m.group(2).strip()

    # cleanup
    raw = re.sub(r"[x×*]", " ", raw)
    tokens = [t for t in re.split(r"\W+", raw) if t and t not in _STOP]
    query = " ".join(tokens).strip()
    if len(query) < 2:
        return None
    return {
        "query": query,
        "qty": qty,
        "want_size": want_size,
        "want_unit": want_unit,
    }


def parse_order_segments(user_text: str) -> list[dict[str, Any]]:
    text = (user_text or "").strip()
    if not text:
        return []
    # 0,5 kg kabi o‘nlik vergulni nuqtaga
    text = re.sub(r"(\d),(\d)", r"\1.\2", text)
    # split by comma / semicolon / newline / " va "
    parts = re.split(r"[,;\n]|[\s]+va[\s]+", text, flags=re.IGNORECASE)
    out = []
    for part in parts:
        parsed = _parse_segment(part)
        if parsed:
            out.append(parsed)
    if not out:
        parsed = _parse_segment(text)
        if parsed:
            out.append(parsed)
    return out


def try_multi_add(user_id: int, user_text: str) -> tuple[str, list[Any]] | None:
    """Bir nechta mahsulotli so‘rovni savatga yig‘adi."""
    text = _norm(user_text)
    # savolga o‘xshasa (faqat «bormi?») — multi-add qilmaymiz
    if text.endswith("?") and not any(
        w in text for w in ("kerak", "bering", "yuboring", "olaman", "zakaz")
    ):
        # lekin ro‘yxat bo‘lsa ham qo‘shish mumkin
        if "," not in user_text and " va " not in text:
            return None

    segments = parse_order_segments(user_text)
    if len(segments) < 1:
        return None

    # faqat bitta oddiy qidiruv so‘zi bo‘lsa — multi emas
    if len(segments) == 1 and segments[0]["want_size"] is None and segments[0]["qty"] == 1:
        # «2 ta sut» ni try_quick_add ushlaydi; «guruch» ni local topadi
        if not any(w in text for w in ("kerak", "bering", "yuboring", "olaman", "zakaz", ",")):
            return None

    added_lines: list[str] = []
    missing: list[str] = []
    notes: list[str] = []
    products: list[Any] = []

    for seg in segments:
        product = _best_product(seg["query"], seg["want_size"], seg["want_unit"])
        if not product:
            missing.append(seg["query"])
            continue

        qty = int(seg["qty"] or 1)
        want_size = seg["want_size"]
        want_unit = seg["want_unit"]
        psize, punit = _pack_size_from_name(str(product["name"]))

        if want_size is not None and psize:
            # bir xil o‘lchov oilasi
            wu = want_unit or ""
            pu = punit or ""
            if wu in {"l", "lt", "litr"}:
                wu = "l"
            if pu in {"l", "lt", "litr"}:
                pu = "l"
            if wu in {"gr", "g"}:
                wu = "g"
            if pu in {"gr", "g"}:
                pu = "g"
            if wu == pu and psize > 0:
                packs = max(1, int(math.ceil(want_size / psize - 1e-9)))
                qty = packs * max(1, int(seg["qty"] or 1))
                if abs(packs * psize - want_size) > 0.05:
                    notes.append(
                        f"{product['name']}: so‘ralgan {want_size}{want_unit}, "
                        f"paket {psize}{punit} → {qty} dona"
                    )

        db.cart_add(user_id, int(product["id"]), qty)
        line_total = int(product["price"]) * qty
        added_lines.append(
            f"• {product['name']} × {qty} — {money(line_total)}"
        )
        products.append(product)

    if not added_lines:
        return None

    from ai_sotuvchi.config import DELIVERY_FEE

    subtotal = db.cart_total(user_id)
    lines = ["✅ Savatga qo‘shildi:", *added_lines, "————————————"]
    if notes:
        lines.extend([f"ℹ️ {n}" for n in notes])
    if missing:
        lines.append("Topilmadi: " + ", ".join(missing))
    lines.append(f"Mahsulotlar: {money(subtotal)}")
    lines.append(f"Yetkazish: {money(DELIVERY_FEE)}")
    lines.append(f"<b>Jami: {money(subtotal + DELIVERY_FEE)}</b>")
    lines.append("\nDavom etish: <b>Buyurtma berish</b>")
    return "\n".join(lines), products


def try_quick_add(user_id: int, user_text: str) -> str | None:
    """«2 ta sut» / «sut qo‘sh» kabi buyruqlarni ushlaydi."""
    text = (user_text or "").strip().lower()
    has_add_verb = bool(
        re.search(r"(qo['‘’`]?sh|savatga|qoshib\s*qo)", text)
    )
    m_qty = re.match(r"^(\d+)\s*(?:ta|dona)?\s+(.+)$", text)
    if not has_add_verb and not m_qty:
        return None
    # ko‘p mahsulotli bo‘lsa multi ishlaydi
    if "," in text or " va " in text:
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
    product = _best_product(query)
    if not product:
        return None
    db.cart_add(user_id, int(product["id"]), max(1, qty))
    return (
        f"✅ {product['name']} ×{max(1, qty)} savatga qo‘shildi.\n"
        f"Savat: {money(db.cart_total(user_id))}"
    )


def _faq_reply(user_text: str) -> str | None:
    text = _norm(user_text)
    if any(w in text for w in ("salom", "assalom", "hello", "hi", "hayrli")):
        return (
            f"Assalomu alaykum! {SHOP_NAME} xizmatidaman.\n"
            f"⏰ {SHOP_HOURS} · 📞 {SHOP_PHONE}\n\n"
            "Nima kerak? Masalan:\n"
            "<i>guruch 2kg, cola 1.5l x 2, shakar 0.5kg</i>"
        )
    if any(w in text for w in ("rahmat", "tashakkur", "spasibo")):
        return "Arzimaydi! Yana kerak bo‘lsa yozing."
    if any(w in text for w in ("katalog", "mahsulotlar", "nima bor", "royxat", "ro‘yxat")):
        return "<b>Katalog</b>\n\n" + catalog_text()
    if any(
        w in text
        for w in (
            "telefon",
            "aloqa",
            "manzil",
            "qayerda",
            "soat",
            "ish vaqti",
            "ochiqmi",
        )
    ):
        return (
            f"<b>{SHOP_NAME}</b>\n"
            f"📞 {SHOP_PHONE}\n"
            f"⏰ {SHOP_HOURS}\n"
            f"💳 Minimal: {money(MIN_ORDER_AMOUNT)}\n"
            f"🚚 Yetkazish: {money(DELIVERY_FEE)}"
        )
    if any(w in text for w in ("yetkaz", "dostavka", "delivery", "yetkazib")):
        return (
            f"Yetkazib beramiz.\n"
            f"🚚 Narxi: <b>{money(DELIVERY_FEE)}</b>\n"
            f"Minimal buyurtma: <b>{money(MIN_ORDER_AMOUNT)}</b>\n"
            "Manzilni buyurtmada yozasiz."
        )
    if any(w in text for w in ("to‘lov", "tolov", "pul", "naqd", "karta", "qanday to")):
        return (
            "To‘lov: buyurtma yetkazilganda (odatda naqd).\n"
            "Batafsil: admin tasdiqlagach xabar beriladi."
        )
    if any(w in text for w in ("minimal", "eng kam", "kamida")):
        return f"Minimal buyurtma: <b>{money(MIN_ORDER_AMOUNT)}</b> (mahsulotlar)."
    if any(w in text for w in ("savat", "cart")):
        return "Savatni ko‘rish: pastdagi <b>Savat</b> tugmasi."
    if any(w in text for w in ("buyurtma qanday", "qanday buyurtma", "qanday zakaz")):
        return (
            "1) Mahsulotlarni yozing yoki Katalogdan qo‘shing\n"
            "2) <b>Savat</b>ni tekshiring\n"
            "3) <b>Buyurtma berish</b> — telefon, manzil, ism"
        )
    if "soat nechi" in text or text in {"vaqt", "time"}:
        now = datetime.now().strftime("%H:%M")
        return f"Hozir taxminan {now}. Do‘kon: {SHOP_HOURS}."
    # oddiy hisob
    m = re.fullmatch(r"\s*(\d+)\s*([+\-*/])\s*(\d+)\s*", text)
    if m:
        a, op, b = int(m.group(1)), m.group(2), int(m.group(3))
        try:
            if op == "+":
                r = a + b
            elif op == "-":
                r = a - b
            elif op == "*":
                r = a * b
            else:
                r = a / b if b else "∞"
            return f"Javob: <b>{r}</b>"
        except Exception:
            pass
    return None


def _general_reply(user_text: str) -> str:
    """Har qanday savolga do‘stona javob (katalogsiz ham)."""
    text = (user_text or "").strip()
    return (
        f"Tushundim: «{text[:120]}»\n\n"
        f"Men {SHOP_NAME} AI sotuvchisiman — asosan mahsulot, narx va buyurtma bo‘yicha yordam beraman.\n"
        f"📞 {SHOP_PHONE} · ⏰ {SHOP_HOURS}\n\n"
        "Agar buyurtma bo‘lsa, shunday yozing:\n"
        "<i>guruch 2kg, cola 1.5l x 2, shakar 0.5kg</i>\n\n"
        "Boshqa savolingiz bo‘lsa — yozing, imkon qadar javob beraman."
    )


def _local_reply(user_text: str) -> tuple[str, list[Any]]:
    faq = _faq_reply(user_text)
    if faq:
        return faq, []

    found = find_products(user_text)
    if found:
        lines = ["Topdim:"]
        for p in found[:6]:
            lines.append(f"• {p['name']} — {money(int(p['price']))} (#{p['id']})")
        lines.append("\nSavatga qo‘shish: tugmani bosing yoki miqdor bilan yozing.")
        return "\n".join(lines), found[:6]

    return _general_reply(user_text), []


def _apply_ai_adds(user_id: int, reply: str) -> str:
    """AI javobidagi ADD:#id:qty qatorlarini savatga qo‘llaydi."""
    adds = re.findall(r"ADD:#(\d+):(\d+)", reply)
    if not adds:
        return reply
    lines = []
    for pid_s, qty_s in adds:
        pid, qty = int(pid_s), int(qty_s)
        product = db.get_product(pid)
        if not product or not product["is_active"] or qty <= 0:
            continue
        db.cart_add(user_id, pid, qty)
        lines.append(f"• {product['name']} × {qty}")
    clean = re.sub(r"\n?ADD:#\d+:\d+", "", reply).strip()
    if lines:
        subtotal = db.cart_total(user_id)
        clean += (
            "\n\n✅ Savatga qo‘shildi:\n"
            + "\n".join(lines)
            + f"\nJami mahsulot: {money(subtotal)}"
        )
    return clean


def _openai_reply(user_id: int, user_text: str) -> str | None:
    if not OPENAI_API_KEY:
        return None

    history = db.get_memory(user_id)
    system = (
        f"Sen «{SHOP_NAME}» do‘konining professional o‘zbek AI yordamchisisan.\n"
        f"Telefon: {SHOP_PHONE}. Ish vaqti: {SHOP_HOURS}. "
        f"Minimal: {MIN_ORDER_AMOUNT}. Yetkazish: {DELIVERY_FEE}.\n"
        "Har qanday savolga odobli va foydali javob ber (do‘kon, hayot, umumiy).\n"
        "Do‘kon savollarida katalogdan foydalan. Yo‘q mahsulotni o‘ylab topma.\n"
        "Agar mijoz bir nechta mahsulot so‘rasa (masalan: guruch 2kg, cola 1.5l x2), "
        "mos mahsulotlarni tanla va HAR BIR uchun alohida qator yoz:\n"
        "ADD:#ID:QTY\n"
        "Masalan: ADD:#1:2\n"
        "Keyin odamga tushunarli xulosa yoz.\n\n"
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
        "max_tokens": 700,
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
        reply = _apply_ai_adds(user_id, reply)
        history.append({"role": "user", "content": user_text})
        history.append({"role": "assistant", "content": reply})
        db.save_memory(user_id, history)
        return reply
    except (urllib.error.URLError, urllib.error.HTTPError, KeyError, IndexError, TimeoutError) as exc:
        logger.warning("OpenAI xato: %s", exc)
        return None


def reply_to_user(user_id: int, user_text: str) -> tuple[str, list[Any]]:
    multi = try_multi_add(user_id, user_text)
    if multi:
        return multi

    quick = try_quick_add(user_id, user_text)
    if quick:
        return quick, []

    ai = _openai_reply(user_id, user_text)
    if ai:
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
