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
    "bitta",
    "bittasini",
    "kg",
    "l",
    "lt",
    "litr",
    "gr",
    "g",
}

# Qisqa nom → qidiruv kaliti
_ALIASES = {
    "cola": "cola",
    "kola": "cola",
    "coca": "cola",
    "fanta": "fanta",
    "pepsi": "pepsi",
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


def _norm(s: str) -> str:
    return (
        (s or "")
        .lower()
        .replace("‘", "'")
        .replace("’", "'")
        .replace("ё", "e")
        .replace(",", ".")
    )


_LOOKALIKE_ZERO = str.maketrans({
    "o": "0",
    "о": "0",  # kirill o
    "О": "0",
    "O": "0",
})


def _fix_lookalike_digits(s: str) -> str:
    """20OOO / 20ооо → 20000; 20 000 / 20.000 → 20000.

    Faqat raqam+O tokenlari o‘zgaradi — cola, somlik, guruch tegilmaydi.
    """

    def _token(m: re.Match[str]) -> str:
        return m.group(0).translate(_LOOKALIKE_ZERO)

    s = re.sub(r"(?i)\b[\dOОoо]+\b", _token, s)
    # minglik ajratgich: 20 000 yoki 20.000
    s = re.sub(r"(\d)[\s.](\d{3})(?=\D|$)", r"\1\2", s)
    s = re.sub(r"(\d)[\s.](\d{3})(?=\D|$)", r"\1\2", s)
    return s


def _fold_token(s: str) -> str:
    """Yozuv farqlari uchun yumshoq shakl: pechene≈pecnene, yubileniy≈yubileyni."""
    t = _norm(s)
    # lotin/kirill chalkashligi
    for a, b in (
        ("ch", "c"),
        ("sh", "s"),
        ("zh", "j"),
        ("kh", "x"),
        ("ʻ", ""),
        ("'", ""),
        ("`", ""),
    ):
        t = t.replace(a, b)
    t = re.sub(r"[^a-z0-9]+", "", t)
    # oxiridagi yumshoq unlilar (iy/yi/i)
    t = re.sub(r"(iy|yi|yy)$", "i", t)
    return t


def _edit_distance(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    if abs(len(a) - len(b)) > 3:
        return 99
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            ins = cur[j - 1] + 1
            delete = prev[j] + 1
            sub = prev[j - 1] + (0 if ca == cb else 1)
            cur.append(min(ins, delete, sub))
        prev = cur
    return prev[-1]


def _tokens_fuzzy_match(query_tok: str, name_tok: str) -> bool:
    q = _fold_token(query_tok)
    n = _fold_token(name_tok)
    if len(q) < 3 or len(n) < 3:
        return q == n and len(q) >= 2
    if q in n or n in q:
        return True
    # qisqa tokenlar — 1 xato; uzun — 2 xato
    limit = 1 if min(len(q), len(n)) <= 5 else 2
    return _edit_distance(q, n) <= limit


def _query_matches_name(query: str, name: str) -> int:
    """Moslik balli (0 = yo‘q)."""
    q = _norm(query)
    n = _norm(name)
    if not q:
        return 0
    if q in n:
        return 100
    q_toks = [t for t in re.split(r"\W+", q) if len(t) >= 2 and t not in _STOP]
    n_toks = [t for t in re.split(r"\W+", n) if len(t) >= 2]
    if not q_toks:
        return 0
    matched = 0
    for qt in q_toks:
        if any(_tokens_fuzzy_match(qt, nt) for nt in n_toks):
            matched += 1
        elif any(_fold_token(qt) in _fold_token(nt) or _fold_token(nt) in _fold_token(qt) for nt in n_toks):
            matched += 1
    if matched == 0:
        # butun so‘rov vs butun nom (hajmsiz)
        qb = _fold_token(re.sub(r"\d+(?:\.\d+)?\s*(kg|g|l|ml)\b", "", q))
        nb = _fold_token(_base_name(name) if "(" not in name else name)
        if qb and nb and (qb in nb or nb in qb or _edit_distance(qb, nb) <= 2):
            return 40
        return 0
    # barcha muhim tokenlar topilsa — yuqori ball
    ratio = matched / len(q_toks)
    return int(50 + 50 * ratio)


def find_products(user_text: str, limit: int = 6) -> list[Any]:
    text = (user_text or "").strip()
    tokens = [
        t
        for t in re.split(r"\W+", _norm(text))
        if len(t) >= 3 and t not in _STOP
    ]
    scored: list[tuple[int, Any]] = []
    seen: set[int] = set()

    # 1) LIKE qidiruv
    for token in tokens or [_norm(text)]:
        for p in db.search_products(token, limit=12):
            pid = int(p["id"])
            if pid in seen:
                continue
            seen.add(pid)
            scored.append((_query_matches_name(text, str(p["name"])) or 10, p))

    # 2) Fuzzy — butun katalog (kichik do‘kon)
    if len(scored) < limit:
        for p in db.list_products(active_only=True):
            pid = int(p["id"])
            if pid in seen:
                continue
            score = _query_matches_name(text, str(p["name"]))
            if score <= 0:
                # tokenlar bo‘yicha ham
                for tok in tokens:
                    if _query_matches_name(tok, str(p["name"])) > 0:
                        score = 30
                        break
            if score > 0:
                seen.add(pid)
                scored.append((score, p))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [p for s, p in scored[:limit] if s > 0]


def _pack_size_from_name(name: str) -> tuple[float | None, str | None]:
    n = _norm(name)
    n = n.replace("gramm", "g").replace("грамм", "g")
    m = re.search(r"(\d+(?:\.\d+)?)\s*(kg|l|lt|litr|gr|g|ml)\b", n)
    if not m:
        return None, None
    size = float(m.group(1))
    unit = m.group(2)
    if unit == "gr":
        unit = "g"
    return size, unit


def _size_sort_value(name: str) -> tuple[int, float]:
    """Og‘irlik/hajm bo‘yicha tartib: 250g, 500g, 1kg."""
    size, unit = _pack_size_from_name(name)
    if size is None or not unit:
        return (9, 999999.0)
    if unit in {"g", "gr"}:
        return (1, size)  # gramm
    if unit == "kg":
        return (1, size * 1000.0)
    if unit == "ml":
        return (0, size)
    if unit in {"l", "lt", "litr"}:
        return (0, size * 1000.0)
    return (9, size)


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


def _base_name(name: str) -> str:
    """«Coca-Cola 1.5L» → «coca cola»; «Guruch 250g» → «guruch»."""
    n = _norm(name)
    n = n.replace("gramm", "g").replace("грамм", "g")
    n = re.sub(r"\d+(?:\.\d+)?\s*(kg|l|lt|litr|gr|g|ml|dona|ta)\b", " ", n)
    n = re.sub(r"[-_/]+", " ", n)
    n = re.sub(r"\s+", " ", n).strip()
    return n


def _query_tokens(query: str) -> list[str]:
    q = _norm(query)
    for tok in list(re.split(r"\W+", q)):
        if tok in _ALIASES:
            q = _ALIASES[tok]
            break
    return [t for t in re.split(r"\W+", q) if len(t) >= 2 and t not in _STOP]


def _best_product(query: str, want_size: float | None = None, want_unit: str | None = None):
    variants = find_variants(query, limit=20)
    if not variants:
        return None
    ranked = sorted(
        variants,
        key=lambda p: _score_product(query, p, want_size, want_unit),
        reverse=True,
    )
    best = ranked[0]
    if _score_product(query, best, want_size, want_unit) <= 0:
        return None
    return best


def find_variants(query: str, limit: int = 20) -> list[Any]:
    """Har qanday mahsulot oilasi: hajmsiz so‘rovda barcha variantlar.

    Masalan: cola → 0.5L/1.5L/2L; sut → Sut 1L, Sut 0.5L (bor bo‘lsa).
    """
    tokens = _query_tokens(query)
    if not tokens:
        return []

    all_products = db.list_products(active_only=True)
    scored: list[tuple[int, Any]] = []
    for p in all_products:
        score = _query_matches_name(query, str(p["name"]))
        if score <= 0:
            # alohida tokenlar
            name = str(p["name"])
            for tok in tokens:
                if _query_matches_name(tok, name) > 0:
                    score += 25
        # alias: cola ↔ coca
        name_n = _norm(str(p["name"]))
        if "cola" in tokens or "coca" in tokens:
            if "cola" in name_n or "coca" in name_n:
                score += 25
        if score > 0:
            scored.append((score, p))

    if not scored:
        # fallback LIKE + fuzzy find_products
        for p in find_products(query, limit=20):
            scored.append((_query_matches_name(query, str(p["name"])) or 20, p))

    scored.sort(key=lambda x: x[0], reverse=True)
    if not scored or scored[0][0] <= 0:
        return []

    top = scored[0][1]
    top_base = _base_name(str(top["name"]))
    top_tokens = [
        t for t in re.split(r"\W+", top_base) if t and t not in _STOP
    ]

    family: list[Any] = []
    seen: set[int] = set()
    for score, p in scored:
        if score <= 0:
            continue
        pid = int(p["id"])
        if pid in seen:
            continue
        p_base = _base_name(str(p["name"]))
        p_tokens = [
            t for t in re.split(r"\W+", p_base) if t and t not in _STOP
        ]
        # bir oila: fuzzy umumiy token yoki base o‘xshash
        shared = False
        for tt in top_tokens:
            for pt in p_tokens:
                if _tokens_fuzzy_match(tt, pt):
                    shared = True
                    break
            if shared:
                break
        if shared or (
            top_base
            and (
                top_base in p_base
                or p_base in top_base
                or _edit_distance(_fold_token(top_base), _fold_token(p_base)) <= 2
            )
        ):
            seen.add(pid)
            family.append(p)

    if not family:
        for score, p in scored[:limit]:
            if score > 0:
                family.append(p)

    def sort_key(p: Any) -> tuple:
        fam, val = _size_sort_value(str(p["name"]))
        return (fam, val, _norm(str(p["name"])))

    family.sort(key=sort_key)
    return family[:limit]


def _human_pack_label(name: str) -> str:
    """«Guruch 250g» → «250 gramm»; «Guruch 1kg» → «1 kg»."""
    size, unit = _pack_size_from_name(name)
    if size is None or not unit:
        return str(name)
    if abs(size - int(size)) < 0.001:
        size_s = str(int(size))
    else:
        size_s = str(size).rstrip("0").rstrip(".")
    if unit in {"g", "gr"}:
        return f"{size_s} gramm"
    if unit == "kg":
        return f"{size_s} kg"
    if unit == "ml":
        return f"{size_s} ml"
    if unit in {"l", "lt", "litr"}:
        return f"{size_s} litr"
    return str(name)


# Kg mahsulot tanlanganda chiqadigan so‘mlik variantlar
KG_MONEY_OPTIONS = (5000, 10000)


def kg_money_options(products: list[Any]) -> list[dict[str, Any]]:
    """1kg bor bo‘lsa — 5000 / 10000 so‘mlik variantlar."""
    kg = _find_1kg_product(products)
    if not kg:
        return []
    price_kg = int(kg["price"])
    out: list[dict[str, Any]] = []
    for amount in KG_MONEY_OPTIONS:
        grams = db.grams_for_money(price_kg, amount)
        out.append(
            {
                "product_id": int(kg["id"]),
                "amount": amount,
                "grams": grams,
                "label": f"{money(amount)}lik",
                "detail": f"~{grams} g",
            }
        )
    return out


def format_variants(query: str, products: list[Any]) -> str:
    title = query.strip().title() if query else "Mahsulot"
    money_opts = kg_money_options(products)

    # Bitta oddiy (kg emas) mahsulot
    if len(products) == 1 and not money_opts:
        p = products[0]
        return (
            f"Topdim: <b>{p['name']}</b> — {money(int(p['price']))}\n"
            "Savatga qo‘shish: pastdagi tugma."
        )

    lines = [
        f"<b>{title}</b> — barcha variantlar:",
        "————————————",
        "<b>Qadoq:</b>",
    ]
    for p in products:
        label = _human_pack_label(str(p["name"]))
        show = label if label != str(p["name"]) else str(p["name"])
        lines.append(f"• <b>{show}</b> — {money(int(p['price']))}")

    if money_opts:
        lines.append("")
        lines.append("<b>So‘mlik:</b>")
        for opt in money_opts:
            lines.append(
                f"• <b>{opt['label']}</b> — {opt['detail']}"
            )

    lines.append("\nKeraklisini tugmadan tanlang.")
    return "\n".join(lines)


def _should_list_variants(seg: dict[str, Any], variants: list[Any]) -> bool:
    """Hajm aytilmagan bo‘lsa — barcha mahsulotlar uchun variantlarni ko‘rsat."""
    if not variants:
        return False
    if seg.get("want_money") is not None:
        return False
    if seg.get("want_size") is not None:
        return False
    # Aniq miqdor (2 ta) va faqat 1 variant → to‘g‘ridan qo‘shish mumkin
    if int(seg.get("qty") or 1) > 1 and len(variants) == 1:
        return False
    # 1+ variant: har doim ro‘yxat (cola, sut, guruch, …)
    return True


def _extract_money_amount(raw: str) -> tuple[int | None, str]:
    """«5000 so'mlik» / «10 ming» / «10000lik» → summa va qolgan matn."""
    # 10 ming so'mlik
    m = re.search(
        r"(\d+(?:\.\d+)?)\s*ming(?:\s*(?:so['ʻ’`]?m|sum|som))?(?:lik|liq)?",
        raw,
    )
    if m:
        amount = int(round(float(m.group(1)) * 1000))
        rest = (raw[: m.start()] + " " + raw[m.end() :]).strip()
        return amount, re.sub(r"\s+", " ", rest)
    # 5000 so'm / 5000 so'mlik
    m = re.search(
        r"(\d+)\s*(?:so['ʻ’`]?m|sum|som)(?:lik|liq)?",
        raw,
    )
    if m:
        amount = int(m.group(1))
        rest = (raw[: m.start()] + " " + raw[m.end() :]).strip()
        return amount, re.sub(r"\s+", " ", rest)
    # 5000lik / 10000liq
    m = re.search(r"\b(\d{3,})\s*(?:lik|liq)\b", raw)
    if m:
        amount = int(m.group(1))
        rest = (raw[: m.start()] + " " + raw[m.end() :]).strip()
        return amount, re.sub(r"\s+", " ", rest)
    return None, raw


def _parse_segment(seg: str) -> dict[str, Any] | None:
    raw = _fix_lookalike_digits(_norm(seg)).strip()
    if len(raw) < 2:
        return None
    raw = re.sub(r"\b(kerak|bormi|bering|iltimos|menga)\b", " ", raw)
    raw = re.sub(r"\s+", " ", raw).strip()

    qty = 1
    want_size = None
    want_unit = None
    want_money = None

    # so‘mlik (kg mahsulotlar uchun) — hajmdan oldin
    want_money, raw = _extract_money_amount(raw)

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

    # 2kg / 1.5 l / 0.5 kg / 250g / 250 gramm
    raw = raw.replace("gramm", "g").replace("грамм", "g")
    m = re.search(r"(\d+(?:\.\d+)?)\s*(kg|l|lt|litr|gr|g|ml)\b", raw)
    if m:
        want_size = float(m.group(1))
        want_unit = m.group(2)
        raw = (raw[: m.start()] + " " + raw[m.end() :]).strip()
        # aniq hajm bo‘lsa so‘mlikni e’tiborsiz qoldiramiz
        want_money = None

    # leading qty still there?
    m = re.match(r"^(\d+)\s+(.+)$", raw)
    if m and want_size is None and want_money is None:
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
        "want_money": want_money,
    }


def _find_1kg_product(variants: list[Any]):
    for p in variants:
        size, unit = _pack_size_from_name(str(p["name"]))
        if not size or not unit:
            continue
        if unit == "kg" and abs(size - 1.0) < 0.01:
            return p
        if unit in {"g", "gr"} and abs(size - 1000.0) < 0.01:
            return p
    return None


def _money_label(base_name: str, grams: int, amount: int) -> str:
    stem = re.sub(
        r"\d+(?:\.\d+)?\s*(kg|g|gr|gramm)\b",
        "",
        _norm(base_name),
        flags=re.I,
    ).strip()
    stem = re.sub(r"\s+", " ", stem).strip() or "mahsulot"
    title = stem[:1].upper() + stem[1:]
    if grams >= 1000:
        w = f"{grams / 1000:.2f}".rstrip("0").rstrip(".") + " kg"
    else:
        w = f"{grams} g"
    return f"{title} ~{w} ({money(amount)}lik)"


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
    """Bir nechta mahsulotli so‘rovni savatga yig‘adi.

    Hajmsiz so‘rovda (masalan «cola») — barcha variantlarni ko‘rsatadi, avto-qo‘shmaydi.
    """
    text = _norm(user_text)
    if text.endswith("?") and not any(
        w in text for w in ("kerak", "bering", "yuboring", "olaman", "zakaz")
    ):
        if "," not in user_text and " va " not in text:
            return None

    segments = parse_order_segments(user_text)
    if len(segments) < 1:
        return None

    # Bitta so‘rov, hajmsiz → variantlar (barcha mahsulotlar)
    if len(segments) == 1:
        variants = find_variants(segments[0]["query"])
        if _should_list_variants(segments[0], variants):
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

        # So‘mlik: kg mahsulotdan proporsional og‘irlik
        if want_money is not None:
            amount = int(want_money)
            if amount < 500:
                missing.append(f"{seg['query']} (min 500 so‘m)")
                continue
            kg_product = _find_1kg_product(variants)
            if not kg_product:
                missing.append(f"{seg['query']} (kg yo‘q)")
                continue
            price_kg = int(kg_product["price"])
            grams = db.grams_for_money(price_kg, amount)
            label = _money_label(str(kg_product["name"]), grams, amount)
            for _ in range(max(1, qty)):
                db.cart_add_by_money(
                    user_id,
                    int(kg_product["id"]),
                    amount=amount,
                    grams=grams,
                    label=label,
                )
            line_total = amount * max(1, qty)
            added_lines.append(f"• {label} × {max(1, qty)} — {money(line_total)}")
            products.append(kg_product)
            continue

        if _should_list_variants(seg, variants):
            choose_blocks.append((seg["query"], variants))
            continue

        product = _best_product(seg["query"], want_size, want_unit)
        if not product:
            missing.append(seg["query"])
            continue

        psize, punit = _pack_size_from_name(str(product["name"]))
        if want_size is not None and psize:
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

    # Faqat tanlash kerak bo‘lgan holat
    if not added_lines and choose_blocks:
        q, vars_ = choose_blocks[0]
        # bir nechta oila bo‘lsa birlashtiramiz
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
    # Mahsulotga o‘xshash so‘rov — aniqroq javob
    if len(text) >= 3 and not text.endswith("?"):
        return (
            f"«<b>{text[:80]}</b>» katalogda topilmadi.\n\n"
            "Nomini tekshiring yoki <b>Katalog</b>dan qarang.\n"
            "Admin bo‘lsangiz — <b>➕ Mahsulot</b> bilan qo‘shing.\n\n"
            f"📞 {SHOP_PHONE} · ⏰ {SHOP_HOURS}"
        )
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

    segments = parse_order_segments(user_text)
    if len(segments) == 1:
        variants = find_variants(segments[0]["query"])
        if _should_list_variants(segments[0], variants):
            return format_variants(segments[0]["query"], variants), variants

    found = find_products(user_text)
    if found:
        q = segments[0]["query"] if segments else user_text
        variants = find_variants(q)
        if variants and _should_list_variants(
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
        "Agar mijoz hajmsiz yozsa (masalan «cola», «sut», «guruch») — ADD qilma; "
        "katalogdagi SHU mahsulotning barcha hajm/tur variantlarini (#ID bilan) ko‘rsat "
        "va tanlashni so‘ra. Bu QOIDА barcha mahsulotlarga tegishli.\n"
        "Agar mijoz so‘mlik so‘rasa (masalan «guruch 5000 so‘mlik», «shakar 10 minglik») — "
        "1kg narxidan gramm hisobla va tushuntir; ADD qilma (tizim o‘zi qo‘shadi).\n"
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
    # So‘mlik / aniq hajm — avval multi; faqat hajmsiz → variantlar
    segments = parse_order_segments(user_text)
    if len(segments) == 1 and "," not in user_text:
        seg0 = segments[0]
        if seg0.get("want_money") is None and seg0.get("want_size") is None:
            variants = find_variants(seg0["query"])
            if _should_list_variants(seg0, variants):
                return format_variants(seg0["query"], variants), variants

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
