"""Mahsulot qidiruv: fuzzy, qadoq hajmlari, so‘mlik.

Telegram va DB ga bog‘lanmagan — test qilish oson.
"""

from __future__ import annotations

import math
import re
from typing import Any

_STOP = {
    "kerak",
    "kerakli",
    "bormi",
    "bor",
    "yoq",
    "yo‘q",
    "yo'q",
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
    "gramm",
    "somlik",
    "so'mlik",
    "minglik",
    "ming",
}

_ALIASES = {
    "cola": "cola",
    "kola": "cola",
    "coca": "cola",
    "kokakola": "cola",
    "fanta": "fanta",
    "pepsi": "pepsi",
}

KG_MONEY_OPTIONS = (5000, 10000)
WEIGHT_PACK_GRAMS = (250, 500, 1000)


def money(amount: int) -> str:
    return f"{int(amount):,}".replace(",", " ") + " so‘m"


def norm(s: str) -> str:
    return (
        (s or "")
        .lower()
        .replace("‘", "'")
        .replace("’", "'")
        .replace("ʻ", "'")
        .replace("ё", "e")
        .replace(",", ".")
        .replace("gramm", "g")
        .replace("грамм", "g")
    )


def fold_token(s: str) -> str:
    """Yozuv farqlari: pechene≈pecnene, yubileniy≈yubileyni."""
    t = norm(s)
    for a, b in (
        ("ch", "c"),
        ("sh", "s"),
        ("zh", "j"),
        ("kh", "x"),
        ("'", ""),
        ("`", ""),
    ):
        t = t.replace(a, b)
    t = re.sub(r"[^a-z0-9]+", "", t)
    t = re.sub(r"(iy|yi|yy)$", "i", t)
    return t


def edit_distance(a: str, b: str) -> int:
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


def tokens_fuzzy_match(query_tok: str, name_tok: str) -> bool:
    q = fold_token(query_tok)
    n = fold_token(name_tok)
    if len(q) < 3 or len(n) < 3:
        return q == n and len(q) >= 2
    if q in n or n in q:
        return True
    limit = 1 if min(len(q), len(n)) <= 5 else 2
    return edit_distance(q, n) <= limit


def pack_size_from_name(name: str) -> tuple[float | None, str | None]:
    n = norm(name)
    m = re.search(r"(\d+(?:\.\d+)?)\s*(kg|l|lt|litr|gr|g|ml)\b", n)
    if not m:
        return None, None
    size = float(m.group(1))
    unit = m.group(2)
    if unit == "gr":
        unit = "g"
    if unit in {"lt", "litr"}:
        unit = "l"
    return size, unit


def to_base_unit(size: float, unit: str) -> tuple[float, str] | None:
    u = (unit or "").lower()
    if u in {"g", "gr"}:
        return size, "g"
    if u == "kg":
        return size * 1000.0, "g"
    if u == "ml":
        return size, "ml"
    if u in {"l", "lt", "litr"}:
        return size * 1000.0, "ml"
    return None


def pack_grams_from_name(name: str) -> int | None:
    size, unit = pack_size_from_name(name)
    if size is None or not unit:
        return None
    base = to_base_unit(size, unit)
    if not base or base[1] != "g":
        return None
    return int(round(base[0]))


def base_name(name: str) -> str:
    """«Coca-Cola 1.5L» → «coca cola»; «Guruch 250g» → «guruch»."""
    n = norm(name)
    n = re.sub(r"\d+(?:\.\d+)?\s*(kg|l|lt|litr|gr|g|ml|dona|ta)\b", " ", n)
    n = re.sub(r"[-_/]+", " ", n)
    n = re.sub(r"\s+", " ", n).strip()
    return n


def query_tokens(query: str) -> list[str]:
    q = norm(query)
    parts = [t for t in re.split(r"\W+", q) if t]
    mapped = [_ALIASES.get(t, t) for t in parts]
    return [t for t in mapped if len(t) >= 2 and t not in _STOP]


def query_matches_name(query: str, name: str) -> int:
    """Moslik balli (0 = yo‘q)."""
    q = norm(query)
    n = norm(name)
    if not q:
        return 0
    if q in n:
        return 100
    q_toks = query_tokens(q)
    n_toks = [t for t in re.split(r"\W+", n) if len(t) >= 2]
    if not q_toks:
        return 0
    matched = 0
    for qt in q_toks:
        if any(tokens_fuzzy_match(qt, nt) for nt in n_toks):
            matched += 1
        elif any(fold_token(qt) in fold_token(nt) or fold_token(nt) in fold_token(qt) for nt in n_toks):
            matched += 1
    if matched == 0:
        qb = fold_token(re.sub(r"\d+(?:\.\d+)?\s*(kg|g|l|ml)\b", "", q))
        nb = fold_token(base_name(name))
        if qb and nb and (qb in nb or nb in qb or edit_distance(qb, nb) <= 2):
            return 40
        return 0
    return int(50 + 50 * (matched / len(q_toks)))


def price_from_kg(price_1kg: int, grams: int) -> int:
    return max(0, int(round(int(price_1kg) * int(grams) / 1000.0)))


def grams_for_money(price_1kg: int, amount: int) -> int:
    if int(price_1kg) <= 0:
        return 0
    return max(1, int(round(int(amount) * 1000.0 / int(price_1kg))))


def human_pack_label(name: str) -> str:
    size, unit = pack_size_from_name(name)
    if size is None or not unit:
        return str(name)
    if abs(size - int(size)) < 0.001:
        size_s = str(int(size))
    else:
        size_s = str(size).rstrip("0").rstrip(".")
    if unit == "g":
        return f"{size_s} gramm"
    if unit == "kg":
        return f"{size_s} kg"
    if unit == "ml":
        return f"{size_s} ml"
    if unit == "l":
        return f"{size_s} litr"
    return str(name)


def size_sort_value(name: str) -> tuple[int, float]:
    size, unit = pack_size_from_name(name)
    if size is None or not unit:
        return (9, 999999.0)
    base = to_base_unit(size, unit)
    if not base:
        return (9, size)
    kind, val = base
    return (0 if kind == "ml" else 1, val)


def score_product(
    query: str,
    product_name: str,
    want_size: float | None = None,
    want_unit: str | None = None,
) -> int:
    score = query_matches_name(query, product_name)
    if want_size is not None and want_unit:
        psize, punit = pack_size_from_name(product_name)
        if psize is not None and punit:
            want = to_base_unit(want_size, want_unit)
            have = to_base_unit(psize, punit)
            if want and have and want[1] == have[1]:
                score += 20
                if abs(have[0] - want[0]) < 0.5:
                    score += 50
                elif have[0] <= want[0] + 0.5:
                    score += 10
    return score


def parse_money_amount(text: str) -> int | None:
    """«5000 so‘mlik», «10 minglik», «5 ming so‘m»."""
    raw = norm(text)
    m = re.search(r"(\d+(?:\.\d+)?)\s*ming(?:lik)?(?:\s*so['`]?m(?:lik)?)?", raw)
    if m:
        return int(round(float(m.group(1)) * 1000))
    m = re.search(r"(\d+)\s*so['`]?m(?:lik)?", raw)
    if m:
        return int(m.group(1))
    m = re.search(r"(\d+)\s*sum(?:lik)?", raw)
    if m:
        return int(m.group(1))
    return None


def parse_segment(seg: str) -> dict[str, Any] | None:
    raw = norm(seg).strip()
    if len(raw) < 2:
        return None
    raw = re.sub(r"\b(kerak|bormi|bering|iltimos|menga)\b", " ", raw)
    raw = re.sub(r"\s+", " ", raw).strip()

    qty = 1
    want_size = None
    want_unit = None
    want_money = parse_money_amount(raw)
    if want_money:
        raw = re.sub(
            r"(\d+(?:\.\d+)?)\s*ming(?:lik)?(?:\s*so['`]?m(?:lik)?)?",
            " ",
            raw,
        )
        raw = re.sub(r"(\d+)\s*so['`]?m(?:lik)?", " ", raw)
        raw = re.sub(r"(\d+)\s*sum(?:lik)?", " ", raw)
        raw = re.sub(r"\s+", " ", raw).strip()

    m = re.search(r"[x×*]\s*(\d+)\b", raw)
    if m:
        qty = max(1, int(m.group(1)))
        raw = (raw[: m.start()] + " " + raw[m.end() :]).strip()

    m = re.search(r"\b(\d+)\s*(?:ta|dona)\b", raw)
    if m:
        qty = max(1, int(m.group(1)))
        raw = (raw[: m.start()] + " " + raw[m.end() :]).strip()

    m = re.search(r"(\d+(?:\.\d+)?)\s*(kg|l|lt|litr|gr|g|ml)\b", raw)
    if m:
        want_size = float(m.group(1))
        want_unit = m.group(2)
        raw = (raw[: m.start()] + " " + raw[m.end() :]).strip()

    m = re.match(r"^(\d+)\s+(.+)$", raw)
    if m and want_size is None and want_money is None:
        qty = max(1, int(m.group(1)))
        raw = m.group(2).strip()

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


def parse_order_segments(user_text: str) -> list[dict[str, Any]]:
    text = (user_text or "").strip()
    if not text:
        return []
    text = re.sub(r"(\d),(\d)", r"\1.\2", text)
    parts = re.split(r"[,;\n]|[\s]+va[\s]+", text, flags=re.IGNORECASE)
    out = []
    for part in parts:
        parsed = parse_segment(part)
        if parsed:
            out.append(parsed)
    if not out:
        parsed = parse_segment(text)
        if parsed:
            out.append(parsed)
    return out


def find_1kg_product(products: list[Any]) -> Any | None:
    for p in products:
        if pack_grams_from_name(str(p["name"])) == 1000:
            return p
    return None


def kg_money_options(products: list[Any]) -> list[dict[str, Any]]:
    kg = find_1kg_product(products)
    if not kg:
        return []
    price_kg = int(kg["price"])
    out: list[dict[str, Any]] = []
    for amount in KG_MONEY_OPTIONS:
        grams = grams_for_money(price_kg, amount)
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


def packs_needed(want_size: float, want_unit: str, product_name: str) -> int | None:
    psize, punit = pack_size_from_name(product_name)
    if psize is None or not punit:
        return None
    want = to_base_unit(want_size, want_unit)
    have = to_base_unit(psize, punit)
    if not want or not have or want[1] != have[1] or have[0] <= 0:
        return None
    return max(1, int(math.ceil(want[0] / have[0] - 1e-9)))


def should_list_variants(seg: dict[str, Any], variants: list[Any]) -> bool:
    if not variants:
        return False
    if seg.get("want_size") is not None:
        return False
    if seg.get("want_money"):
        return False
    if int(seg.get("qty") or 1) > 1 and len(variants) == 1:
        return False
    return True


def format_variants(query: str, products: list[Any]) -> str:
    title = query.strip().title() if query else "Mahsulot"
    money_opts = kg_money_options(products)
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
        label = human_pack_label(str(p["name"]))
        show = label if label != str(p["name"]) else str(p["name"])
        lines.append(f"• <b>{show}</b> — {money(int(p['price']))}")
    if money_opts:
        lines.append("")
        lines.append("<b>So‘mlik:</b>")
        for opt in money_opts:
            lines.append(f"• <b>{opt['label']}</b> — {opt['detail']}")
    lines.append("\nKeraklisini tugmadan tanlang.")
    return "\n".join(lines)


def not_found_text(query: str) -> str:
    q = (query or "").strip() or "bu mahsulot"
    return (
        f"Katalogda «<b>{q}</b>» topilmadi.\n"
        "Nomini boshqacha yozing yoki <b>Katalog</b>dan tanlang."
    )


def pick_family(scored: list[tuple[int, Any]], limit: int = 20) -> list[Any]:
    if not scored:
        return []
    scored = sorted(scored, key=lambda x: x[0], reverse=True)
    if scored[0][0] <= 0:
        return []
    top = scored[0][1]
    top_base = base_name(str(top["name"]))
    top_tokens = [t for t in re.split(r"\W+", top_base) if t and t not in _STOP]
    family: list[Any] = []
    seen: set[int] = set()
    for score, p in scored:
        if score <= 0:
            continue
        pid = int(p["id"])
        if pid in seen:
            continue
        p_base = base_name(str(p["name"]))
        p_tokens = [t for t in re.split(r"\W+", p_base) if t and t not in _STOP]
        shared = any(
            tokens_fuzzy_match(tt, pt) for tt in top_tokens for pt in p_tokens
        )
        if shared or (
            top_base
            and (
                top_base in p_base
                or p_base in top_base
                or edit_distance(fold_token(top_base), fold_token(p_base)) <= 2
            )
        ):
            seen.add(pid)
            family.append(p)
    if not family:
        family = [p for s, p in scored[:limit] if s > 0]
    family.sort(key=lambda p: (*size_sort_value(str(p["name"])), norm(str(p["name"]))))
    return family[:limit]
