from __future__ import annotations

import json
import logging
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
from ai_sotuvchi.matching import (
    format_variants,
    grams_for_money,
    kg_money_options,
    not_found_text,
    pack_grams_from_name,
    pack_size_from_name,
    packs_needed,
    parse_order_segments,
    pick_family,
    query_matches_name,
    query_tokens,
    score_product,
    should_list_variants,
    to_base_unit,
)

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
    text = (user_text or "").strip()
    tokens = query_tokens(text)
    scored: list[tuple[int, Any]] = []
    seen: set[int] = set()

    for token in tokens or [text]:
        for p in db.search_products(token, limit=12):
            pid = int(p["id"])
            if pid in seen:
                continue
            seen.add(pid)
            scored.append((query_matches_name(text, str(p["name"])) or 10, p))

    if len(scored) < limit:
        for p in db.list_products(active_only=True):
            pid = int(p["id"])
            if pid in seen:
                continue
            score = query_matches_name(text, str(p["name"]))
            if score <= 0:
                for tok in tokens:
                    if query_matches_name(tok, str(p["name"])) > 0:
                        score = 30
                        break
            if score > 0:
                seen.add(pid)
                scored.append((score, p))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [p for s, p in scored[:limit] if s > 0]


def find_variants(query: str, limit: int = 20) -> list[Any]:
    tokens = query_tokens(query)
    if not tokens:
        return []

    all_products = db.list_products(active_only=True)
    scored: list[tuple[int, Any]] = []
    for p in all_products:
        score = query_matches_name(query, str(p["name"]))
        if score <= 0:
            name = str(p["name"])
            for tok in tokens:
                if query_matches_name(tok, name) > 0:
                    score += 25
        name_n = str(p["name"]).lower()
        if "cola" in tokens or "coca" in tokens:
            if "cola" in name_n or "coca" in name_n:
                score += 25
        if score > 0:
            scored.append((score, p))

    if not scored:
        for p in find_products(query, limit=20):
            scored.append((query_matches_name(query, str(p["name"])) or 20, p))

    return pick_family(scored, limit=limit)


def _best_product(
    query: str, want_size: float | None = None, want_unit: str | None = None
):
    variants = find_variants(query, limit=20)
    if not variants:
        return None
    ranked = sorted(
        variants,
        key=lambda p: score_product(query, str(p["name"]), want_size, want_unit),
        reverse=True,
    )
    best = ranked[0]
    if score_product(query, str(best["name"]), want_size, want_unit) <= 0:
        return None
    return best


def _somlik_label(product_name: str, amount: int, grams: int) -> str:
    base = re.sub(
        r"\s*\d+(?:\.\d+)?\s*(kg|g|gr|l|ml)\b",
        "",
        str(product_name),
        flags=re.IGNORECASE,
    ).strip() or str(product_name)
    return f"{base} ~{grams} g ({money(amount)}lik)"


def _add_somlik(user_id: int, product: Any, amount: int) -> str | None:
    price_kg = int(product["price"])
    grams = grams_for_money(price_kg, amount)
    if grams <= 0:
        return None
    label = _somlik_label(str(product["name"]), amount, grams)
    db.cart_add_by_money(
        user_id,
        int(product["id"]),
        amount=amount,
        grams=grams,
        label=label,
    )
    return f"• {label} — {money(amount)}"


def try_multi_add(user_id: int, user_text: str) -> tuple[str, list[Any]] | None:
    """Bir nechta mahsulotli so‘rovni savatga yig‘adi.

    Hajmsiz so‘rovda (masalan «cola») — barcha variantlarni ko‘rsatadi.
    «guruch 5000 so‘mlik» — gramm hisoblab savatga qo‘shadi.
    """
    text = (user_text or "").strip().lower()
    if text.endswith("?") and not any(
        w in text for w in ("kerak", "bering", "yuboring", "olaman", "zakaz")
    ):
        if "," not in user_text and " va " not in text:
            return None

    segments = parse_order_segments(user_text)
    if len(segments) < 1:
        return None

    if len(segments) == 1:
        variants = find_variants(segments[0]["query"])
        if should_list_variants(segments[0], variants):
            return format_variants(segments[0]["query"], variants), variants

    added_lines: list[str] = []
    missing: list[str] = []
    notes: list[str] = []
    products: list[Any] = []
    choose_blocks: list[tuple[str, list[Any]]] = []

    for seg in segments:
        variants = find_variants(seg["query"])
        want_size = seg["want_size"]
        want_unit = seg["want_unit"]
        want_money = seg.get("want_money")
        qty = int(seg["qty"] or 1)

        if want_money:
            kg = None
            for p in variants:
                if pack_grams_from_name(str(p["name"])) == 1000:
                    kg = p
                    break
            kg = kg or _best_product(seg["query"])
            if not kg:
                missing.append(seg["query"])
                continue
            line = _add_somlik(user_id, kg, int(want_money) * max(1, qty))
            if line:
                added_lines.append(line)
                products.append(kg)
            else:
                missing.append(seg["query"])
            continue

        if should_list_variants(seg, variants):
            choose_blocks.append((seg["query"], variants))
            continue

        product = _best_product(seg["query"], want_size, want_unit)
        if not product:
            missing.append(seg["query"])
            continue

        if want_size is not None and want_unit:
            packs = packs_needed(want_size, want_unit, str(product["name"]))
            if packs:
                qty = packs * max(1, int(seg["qty"] or 1))
                psize, punit = pack_size_from_name(str(product["name"]))
                if psize and punit:
                    want = to_base_unit(want_size, want_unit)
                    have = to_base_unit(psize, punit)
                    if want and have and abs(packs * have[0] - want[0]) > 5:
                        notes.append(
                            f"{product['name']}: so‘ralgan {want_size}{want_unit} "
                            f"→ {qty} dona"
                        )

        db.cart_add(user_id, int(product["id"]), qty)
        line_total = int(product["price"]) * qty
        added_lines.append(
            f"• {product['name']} × {qty} — {money(line_total)}"
        )
        products.append(product)

    if not added_lines and choose_blocks:
        q, vars_ = choose_blocks[0]
        if len(choose_blocks) == 1:
            return format_variants(q, vars_), vars_
        lines = ["Bir nechta mahsulotda hajm tanlang:"]
        all_p: list[Any] = []
        for q2, vars2 in choose_blocks:
            lines.append("")
            lines.append(format_variants(q2, vars2))
            all_p.extend(vars2)
        return "\n".join(lines), all_p

    if not added_lines:
        return None

    subtotal = db.cart_total(user_id)
    lines = ["✅ Savatga qo‘shildi:", *added_lines, "————————————"]
    if notes:
        lines.extend([f"ℹ️ {n}" for n in notes])
    if missing:
        lines.append("Topilmadi: " + ", ".join(missing))
    if choose_blocks:
        lines.append("")
        for q2, vars2 in choose_blocks:
            lines.append(format_variants(q2, vars2))
            products.extend(vars2)
    lines.append(f"Mahsulotlar: {money(subtotal)}")
    lines.append(f"Yetkazish: {money(DELIVERY_FEE)}")
    lines.append(f"<b>Jami: {money(subtotal + DELIVERY_FEE)}</b>")
    lines.append("\nYana nima kerak? Yoki <b>Buyurtma berish</b>.")
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
    segments = parse_order_segments(query)
    if segments and segments[0].get("want_money"):
        return None
    if segments and should_list_variants(segments[0], find_variants(segments[0]["query"])):
        return None
    product = _best_product(query)
    if not product:
        return None
    db.cart_add(user_id, int(product["id"]), max(1, qty))
    return (
        f"✅ {product['name']} ×{max(1, qty)} savatga qo‘shildi.\n"
        f"Savat: {money(db.cart_total(user_id))}\n"
        "Yana nima kerak?"
    )


def _faq_reply(user_text: str) -> str | None:
    text = (user_text or "").strip().lower()
    text = (
        text.replace("‘", "'")
        .replace("’", "'")
        .replace("ё", "e")
        .replace(",", ".")
    )
    if any(w in text for w in ("salom", "assalom", "hello", "hi", "hayrli")):
        return (
            f"Assalomu alaykum! {SHOP_NAME} xizmatidaman.\n"
            f"⏰ {SHOP_HOURS} · 📞 {SHOP_PHONE}\n\n"
            "Nima kerak? Masalan:\n"
            "<i>guruch 2kg, cola 1.5l x 2, shakar 5000 so‘mlik</i>"
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
    q = (user_text or "").strip()
    if len(q) >= 2:
        return not_found_text(q)
    return (
        f"Men {SHOP_NAME} AI sotuvchisiman — mahsulot, narx va buyurtma.\n"
        f"📞 {SHOP_PHONE} · ⏰ {SHOP_HOURS}\n\n"
        "Masalan: <i>guruch, cola, shakar 5000 so‘mlik</i>"
    )


def _local_reply(user_text: str) -> tuple[str, list[Any]]:
    faq = _faq_reply(user_text)
    if faq:
        return faq, []

    segments = parse_order_segments(user_text)
    if len(segments) == 1:
        variants = find_variants(segments[0]["query"])
        if should_list_variants(segments[0], variants):
            return format_variants(segments[0]["query"], variants), variants

    found = find_products(user_text)
    if found:
        q = segments[0]["query"] if segments else user_text
        variants = find_variants(q)
        if variants and should_list_variants(
            segments[0] if segments else {"qty": 1, "want_size": None},
            variants,
        ):
            return format_variants(q, variants), variants
        lines = ["Topdim:"]
        for p in found[:6]:
            lines.append(f"• {p['name']} — {money(int(p['price']))} (#{p['id']})")
        lines.append("\nSavatga qo‘shish: tugmani bosing yoki miqdor bilan yozing.")
        return "\n".join(lines), found[:6]

    return _general_reply(user_text), []


def _apply_ai_adds(user_id: int, reply: str) -> str:
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
        f"Sen «{SHOP_NAME}» do‘konining professional o‘zbek AI sotuvchisisan.\n"
        f"Telefon: {SHOP_PHONE}. Ish vaqti: {SHOP_HOURS}. "
        f"Minimal: {MIN_ORDER_AMOUNT}. Yetkazish: {DELIVERY_FEE}.\n"
        "Sotuvchi kabi yoz: qisqa, aniq, mahsulotni taklif qil, savatga chorla.\n"
        "Yo‘q mahsulotni o‘ylab topma. Topilmasa shunday de: katalogda yo‘q.\n"
        "Hajmsiz so‘rovda (cola, sut, guruch) ADD qilma — variantlarni (#ID) ko‘rsat.\n"
        "Kg mahsulotda qadoq (250g/500g/1kg) va so‘mlik (5000/10000) ni ayt.\n"
        "Bir nechta mahsulot so‘ralsa HAR BIR uchun: ADD:#ID:QTY\n\n"
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
    segments = parse_order_segments(user_text)
    if len(segments) == 1 and "," not in user_text:
        seg = segments[0]
        variants = find_variants(seg["query"])
        if should_list_variants(seg, variants):
            return format_variants(seg["query"], variants), variants

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
            products = find_variants(user_text) or find_products(user_text)
        return ai, products

    return _local_reply(user_text)


# handlers / keyboards uchun
__all__ = [
    "catalog_text",
    "find_products",
    "find_variants",
    "format_variants",
    "kg_money_options",
    "reply_to_user",
]
