"""Admin: matndan bir nechta mahsulotni AI / parser orqali ajratish."""

from __future__ import annotations

import base64
import io
import json
import logging
import re
import urllib.error
import urllib.request
from typing import Any

from bot.config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL

logger = logging.getLogger(__name__)

_PRICE_RE = re.compile(
    r"(?P<name>.+?)\s*[-–—:=]?\s*(?P<price>\d[\d\s.,]*)\s*(?:so['ʻ’`]?m|sum|som)?\s*$",
    re.I,
)
_PRICE_TRAIL_RE = re.compile(
    r"^(?P<name>.+?)\s+(?P<price>\d{3,}(?:[\s.,]\d{3})*)\s*(?:so['ʻ’`]?m|sum|som)?\s*$",
    re.I,
)


def _clean_price(raw: str) -> int | None:
    digits = re.sub(r"[^\d]", "", str(raw or ""))
    if not digits:
        return None
    try:
        value = int(digits)
    except ValueError:
        return None
    if value < 100 or value > 50_000_000:
        return None
    return value


def parse_price_phrase(text: str) -> int | None:
    """«Narhi 3.000 ming», «narxi 15000», «15 ming so'm»."""
    raw = (text or "").strip()
    if not raw:
        return None
    # 15 ming / 3 ming so'm
    m = re.search(
        r"(\d+(?:[.,]\d+)?)\s*ming(?:\s*(?:so['ʻ’`]?m|sum|som))?",
        raw,
        flags=re.I,
    )
    if m:
        num = m.group(1).replace(",", ".")
        # «3.000 ming» — nuqta minglik ajratuvchi (3000), qayta *1000 qilinmasin
        if re.fullmatch(r"\d{1,3}[.,]\d{3}", m.group(1)):
            return _clean_price(m.group(1))
        try:
            base = float(num)
        except ValueError:
            base = None
        if base is not None:
            # «15 ming» → 15000; lekin «3000 ming» g‘alati — agar base>=100 bo‘lsa *1000
            if base < 1000:
                return _clean_price(str(int(round(base * 1000))))
            return _clean_price(str(int(round(base))))

    m = re.search(
        r"(?:narx[iı]?|narh[iı]?|цена|price)\s*[:\-]?\s*(\d[\d\s.,]*)",
        raw,
        flags=re.I,
    )
    if m:
        return _clean_price(m.group(1))

    m = re.search(r"(\d{1,3}(?:[.,\s]\d{3})+|\d{3,})\s*(?:so['ʻ’`]?m|sum|som)?", raw)
    if m:
        return _clean_price(m.group(1))
    return None


def _strip_trailing_price(name: str) -> str:
    """«Sun'iy bezak gul 70000» → «Sun'iy bezak gul»."""
    text = (name or "").strip()
    text = re.sub(
        r"\s*(?:narx[iı]?|narh[iı]?|цена|price)\s*[:\-]?\s*\d[\d\s.,]*\s*"
        r"(?:ming)?\s*(?:so['ʻ’`]?m|sum|som)?\s*$",
        "",
        text,
        flags=re.I,
    )
    text = re.sub(
        r"\s+\d{1,3}(?:[.,\s]\d{3})+\s*(?:so['ʻ’`]?m|sum|som)?\s*$",
        "",
        text,
        flags=re.I,
    )
    text = re.sub(
        r"\s+\d{3,8}\s*(?:so['ʻ’`]?m|sum|som)?\s*$",
        "",
        text,
        flags=re.I,
    )
    text = re.sub(
        r"\s+\d+(?:[.,]\d+)?\s*ming(?:\s*(?:so['ʻ’`]?m|sum|som))?\s*$",
        "",
        text,
        flags=re.I,
    )
    return text.strip(" -–—:|")


def parse_caption_product(
    caption: str, categories: list[Any], *, default_category_id: int | None = None
) -> dict[str, Any] | None:
    """Rasm caption: «Daftar 36 varoqli\\nNarhi 3.000 ming» yoki «Sun'iy gul 70000»."""
    text = (caption or "").strip()
    if not text:
        return None
    price = parse_price_phrase(text)
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    name_lines: list[str] = []
    for ln in lines:
        # Faqat narx qatori (masalan «Narhi 3000») — nom emas
        if re.match(
            r"^(?:narx[iı]?|narh[iı]?|цена|price)\b", ln, flags=re.I
        ) and parse_price_phrase(ln):
            continue
        if re.match(
            r"^\d[\d\s.,]*\s*(?:ming)?\s*(?:so['ʻ’`]?m|sum|som)?\s*$",
            ln,
            flags=re.I,
        ):
            continue
        if re.match(r"^(?:toifa|category)\s*:", ln, flags=re.I):
            continue
        name_lines.append(ln)
    name = _strip_trailing_price(" ".join(name_lines).strip())
    if not name:
        # Narx qatoridan tashqari birinchi qator
        name = lines[0] if lines else ""
        name = _strip_trailing_price(
            re.sub(
                r"(?:narx[iı]?|narh[iı]?|цена|price)\s*[:\-]?\s*\d[\d\s.,]*.*$",
                "",
                name,
                flags=re.I,
            ).strip()
        )
    if price is None:
        # Butun matndan oxirgi urinish
        local = parse_products_local(text, categories, default_category_id=default_category_id)
        if local:
            return local[0]
        return None
    if not name or len(name) < 2:
        name = "Mahsulot"
    # Toifa hint
    cat_id = default_category_id
    for ln in lines:
        cm = re.match(r"^(?:toifa|category)\s*[:\-]\s*(.+)$", ln, flags=re.I)
        if cm:
            cat_id = match_category_id(cm.group(1), categories) or cat_id
    from bot.product_ad_image import guess_category_keywords

    if cat_id is None:
        cat_id = guess_category_keywords(name, categories)
    return {
        "name": name[:120],
        "price": price,
        "category_id": cat_id,
        "description": "",
    }


def _image_to_data_url(photo_bytes: bytes, max_side: int = 1280) -> str:
    """Vision API uchun JPEG data URL (hajmni qisqartirish)."""
    try:
        from PIL import Image

        img = Image.open(io.BytesIO(photo_bytes)).convert("RGB")
        w, h = img.size
        scale = min(1.0, max_side / max(w, h))
        if scale < 1.0:
            img = img.resize(
                (max(1, int(w * scale)), max(1, int(h * scale))),
                Image.Resampling.LANCZOS,
            )
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85, optimize=True)
        raw = buf.getvalue()
    except Exception:
        raw = photo_bytes
    b64 = base64.b64encode(raw).decode("ascii")
    return f"data:image/jpeg;base64,{b64}"


def extract_product_from_image(
    photo_bytes: bytes,
    categories: list[Any],
    *,
    caption_hint: str = "",
    default_category_id: int | None = None,
) -> dict[str, Any] | None:
    """Rasmdagi yozuv / mahsulotdan nom+narx+toifa (OpenAI Vision)."""
    if not OPENAI_API_KEY or not photo_bytes:
        return None

    # Avval caption bo‘lsa — tezkor yo‘l
    if (caption_hint or "").strip():
        quick = parse_caption_product(
            caption_hint, categories, default_category_id=default_category_id
        )
        if quick and quick.get("price") and quick.get("name"):
            return quick

    cat_lines = []
    for c in categories:
        emoji = (c["emoji"] if "emoji" in c.keys() else "") or ""
        cat_lines.append(f"- id={c['id']}: {emoji} {c['name']}".strip())
    cats_block = "\n".join(cat_lines) if cat_lines else "(toifa yo‘q)"
    hint = (caption_hint or "").strip()
    system = (
        "Sen do‘kon katalogi uchun mahsulot aniqlovchisan. "
        "Rasmda (yoki izohda) yozilgan mahsulot nomi va narxni o‘qi. "
        "Narx odatda so‘mda (masalan 70000, 3.000, 15 ming).\n"
        'Javob faqat JSON: {"name":"...","price":70000,"category_id":1,"description":""}\n'
        "price — butun son (so‘m). Agar narx ko‘rinmasa — null.\n"
        "name — qisqa uzbekcha nom (rasmdagi yozuv yoki mahsulot tavsifi).\n"
        "category_id — pastdagi ro‘yxatdan eng mos; bilmasa null.\n"
        "REDMI/vaqt belgisi/watermark — e’tiborsiz.\n\n"
        f"TOIFALAR:\n{cats_block}\n"
        f"DEFAULT_CATEGORY_ID: {default_category_id}\n"
        f"IZOH_HINT: {hint or '(yo‘q)'}"
    )
    user_content: list[dict[str, Any]] = [
        {
            "type": "text",
            "text": "Rasmdan mahsulot nomi va narxini ajrat. JSON qaytar.",
        },
        {
            "type": "image_url",
            "image_url": {"url": _image_to_data_url(photo_bytes)},
        },
    ]
    if hint:
        user_content.insert(
            0, {"type": "text", "text": f"Telegram izohi: {hint}"}
        )

    payload = {
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_content},
        ],
        "temperature": 0.1,
        "max_tokens": 400,
        "response_format": {"type": "json_object"},
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
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        content = data["choices"][0]["message"]["content"].strip()
        parsed = json.loads(content)
        if not isinstance(parsed, dict):
            return None
        name = _strip_trailing_price(str(parsed.get("name") or "").strip())
        price = _clean_price(str(parsed.get("price") or ""))
        if price is None and hint:
            price = parse_price_phrase(hint)
        if not name and hint:
            cap = parse_caption_product(
                hint, categories, default_category_id=default_category_id
            )
            if cap:
                name = str(cap.get("name") or "")
                price = price or cap.get("price")
        if not name or price is None:
            return None
        cid = parsed.get("category_id")
        try:
            category_id = (
                int(cid) if cid not in (None, "", "null") else default_category_id
            )
        except (TypeError, ValueError):
            category_id = default_category_id
        if category_id is not None:
            known = {int(c["id"]) for c in categories}
            if category_id not in known:
                category_id = default_category_id
        from bot.product_ad_image import guess_category_keywords

        if category_id is None:
            category_id = guess_category_keywords(name, categories)
        return {
            "name": name[:120],
            "price": int(price),
            "category_id": category_id,
            "description": str(parsed.get("description") or "")[:300],
        }
    except (
        urllib.error.URLError,
        urllib.error.HTTPError,
        KeyError,
        IndexError,
        TimeoutError,
        json.JSONDecodeError,
        TypeError,
        ValueError,
    ) as exc:
        logger.warning("AI image product parse xato: %s", exc)
        return None


def _norm_cat(name: str) -> str:
    return re.sub(r"\s+", " ", (name or "").strip().lower())


def match_category_id(label: str, categories: list[Any]) -> int | None:
    want = _norm_cat(label)
    if not want:
        return None
    for c in categories:
        name = _norm_cat(str(c["name"]))
        emoji = str(c["emoji"] if "emoji" in c.keys() else "") or ""
        full = _norm_cat(f"{emoji} {c['name']}")
        if want == name or want == full or want in name or name in want:
            return int(c["id"])
    return None


def _parse_line(line: str) -> dict[str, Any] | None:
    text = (line or "").strip()
    if not text or text.startswith("#"):
        return None
    # "Toifa:" yoki "Toifa - Ichimliklar"
    cat_m = re.match(
        r"^(?:toifa|category|cat)\s*[:\-–—]\s*(.+)$", text, flags=re.I
    )
    if cat_m:
        return {"_category_hint": cat_m.group(1).strip()}

    for pattern in (_PRICE_RE, _PRICE_TRAIL_RE):
        m = pattern.match(text)
        if not m:
            continue
        name = re.sub(r"\s+", " ", m.group("name")).strip(" -–—:=.")
        price = _clean_price(m.group("price"))
        if name and price and len(name) >= 2:
            return {"name": name, "price": price, "description": ""}
    return None


def parse_products_local(
    text: str, categories: list[Any], *, default_category_id: int | None = None
) -> list[dict[str, Any]]:
    """Qatorma-qator: «Guruch 1kg 18000» yoki «Shakar 1kg - 14000»."""
    items: list[dict[str, Any]] = []
    current_cat = default_category_id
    for raw in (text or "").splitlines():
        line = raw.strip()
        if not line:
            continue
        # Bo‘lim sarlavhasi: "Ichimliklar:" yoki "[Ichimliklar]"
        section = re.match(r"^\[(.+)\]\s*$", line) or re.match(
            r"^([^:]{2,40}):\s*$", line
        )
        if section and not re.search(r"\d{3,}", line):
            cid = match_category_id(section.group(1), categories)
            if cid:
                current_cat = cid
            continue
        parsed = _parse_line(line)
        if not parsed:
            continue
        if "_category_hint" in parsed:
            cid = match_category_id(str(parsed["_category_hint"]), categories)
            if cid:
                current_cat = cid
            continue
        parsed["category_id"] = current_cat
        items.append(parsed)
    return items[:50]


def parse_products_openai(
    text: str, categories: list[Any], *, default_category_id: int | None = None
) -> list[dict[str, Any]] | None:
    if not OPENAI_API_KEY or not (text or "").strip():
        return None
    cat_lines = []
    for c in categories:
        emoji = (c["emoji"] if "emoji" in c.keys() else "") or ""
        cat_lines.append(f"- id={c['id']}: {emoji} {c['name']}".strip())
    cats_block = "\n".join(cat_lines) if cat_lines else "(toifa yo‘q)"
    system = (
        "Sen do‘kon admini uchun mahsulot parserisan. "
        "Berilgan matndan mahsulotlar ro‘yxatini JSON qilib chiqar.\n"
        'Format: {"items":[{"name":"...","price":18000,"category_id":1,"description":""}]}\n'
        "price — butun so‘m (raqam). name — qisqa mahsulot nomi (hajm bilan, masalan Guruch 1kg).\n"
        "category_id — pastdagi ro‘yxatdan; mos kelmasa null.\n"
        "Faqat JSON qaytar, boshqa matn yo‘q.\n\n"
        f"TOIFALAR:\n{cats_block}\n"
        f"DEFAULT_CATEGORY_ID: {default_category_id}"
    )
    payload = {
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": text.strip()},
        ],
        "temperature": 0.1,
        "max_tokens": 1200,
        "response_format": {"type": "json_object"},
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
        with urllib.request.urlopen(req, timeout=45) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        content = data["choices"][0]["message"]["content"].strip()
        parsed = json.loads(content)
        raw_items = parsed.get("items") if isinstance(parsed, dict) else parsed
        if not isinstance(raw_items, list):
            return None
        out: list[dict[str, Any]] = []
        for row in raw_items[:50]:
            if not isinstance(row, dict):
                continue
            name = str(row.get("name") or "").strip()
            price = _clean_price(str(row.get("price") or ""))
            if not name or price is None:
                continue
            cid = row.get("category_id")
            try:
                category_id = int(cid) if cid not in (None, "", "null") else default_category_id
            except (TypeError, ValueError):
                category_id = default_category_id
            if category_id is not None:
                known = {int(c["id"]) for c in categories}
                if category_id not in known:
                    category_id = default_category_id
            out.append(
                {
                    "name": name[:120],
                    "price": price,
                    "category_id": category_id,
                    "description": str(row.get("description") or "")[:300],
                }
            )
        return out
    except (
        urllib.error.URLError,
        urllib.error.HTTPError,
        KeyError,
        IndexError,
        TimeoutError,
        json.JSONDecodeError,
        TypeError,
        ValueError,
    ) as exc:
        logger.warning("AI product parse xato: %s", exc)
        return None


def parse_product_drafts(
    text: str, categories: list[Any], *, default_category_id: int | None = None
) -> tuple[list[dict[str, Any]], str]:
    """Qaytaradi: (items, manba: 'ai'|'local')."""
    ai_items = parse_products_openai(
        text, categories, default_category_id=default_category_id
    )
    if ai_items:
        return ai_items, "ai"
    local = parse_products_local(
        text, categories, default_category_id=default_category_id
    )
    return local, "local"


def format_draft_preview(items: list[dict[str, Any]], categories: list[Any]) -> str:
    by_id = {int(c["id"]): c for c in categories}
    lines = ["🤖 <b>AI agent — tasdiqlash</b>", ""]
    for i, item in enumerate(items, 1):
        cid = item.get("category_id")
        cat = by_id.get(int(cid)) if cid is not None else None
        if cat:
            emoji = (cat["emoji"] if "emoji" in cat.keys() else "") or "📦"
            cat_label = f"{emoji} {cat['name']}".strip()
        else:
            cat_label = "—"
        price = f"{int(item['price']):,}".replace(",", " ")
        lines.append(
            f"{i}. <b>{item['name']}</b> — {price} so‘m\n"
            f"   🗂 {cat_label}"
        )
    lines.append("")
    lines.append(f"Jami: <b>{len(items)}</b> ta mahsulot")
    lines.append("Tasdiqlasangiz katalogga qo‘shiladi.")
    return "\n".join(lines)
