"""Mahsulot rasmidan AI orqali draft maydonlar (OpenAI-compatible vision)."""

from __future__ import annotations

import base64
import json
import logging
import re
import urllib.error
import urllib.request
from typing import Any

from bot.config import (
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    OPENAI_MODEL,
    OPENAI_VISION_MODEL,
)
from bot.database import get_categories

logger = logging.getLogger(__name__)

AI_KEY_REQUIRED_MSG = "AI kalit kerak"


class VisionKeyMissing(RuntimeError):
    """OPENAI_API_KEY o‘rnatilmagan."""


class VisionParseError(RuntimeError):
    """Vision API yoki JSON parse xatosi."""


def _vision_model() -> str:
    return (OPENAI_VISION_MODEL or OPENAI_MODEL or "gpt-4o-mini").strip()


def match_category_id(
    hint: str | None, categories: list[Any] | None = None
) -> int | None:
    """AI toifa ishorasini mavjud toifalarga moslashtirish."""
    text = (hint or "").strip().casefold()
    if not text:
        return None
    cats = categories if categories is not None else get_categories(active_only=True)
    if not cats:
        return None

    def _norm(s: str) -> str:
        return (
            (s or "")
            .casefold()
            .replace("‘", "'")
            .replace("’", "'")
            .replace("ё", "e")
        )

    # Exact / contains
    for cat in cats:
        name = _norm(str(cat["name"] or ""))
        if not name:
            continue
        if text == name or text in name or name in text:
            return int(cat["id"])

    # Token overlap
    hint_toks = {t for t in re.split(r"\W+", text) if len(t) >= 3}
    best_id = None
    best_score = 0
    for cat in cats:
        name = _norm(str(cat["name"] or ""))
        toks = {t for t in re.split(r"\W+", name) if len(t) >= 3}
        score = len(hint_toks & toks)
        if score > best_score:
            best_score = score
            best_id = int(cat["id"])
    return best_id if best_score > 0 else None


def _extract_json_object(raw: str) -> dict[str, Any]:
    text = (raw or "").strip()
    if not text:
        raise VisionParseError("Bo‘sh AI javobi")
    # ```json ... ```
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL | re.I)
    if fence:
        text = fence.group(1)
    else:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            text = text[start : end + 1]
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise VisionParseError(f"JSON o‘qilmadi: {exc}") from exc
    if not isinstance(data, dict):
        raise VisionParseError("JSON obyekt emas")
    return data


def _normalize_draft(data: dict[str, Any], categories: list[Any] | None = None) -> dict[str, Any]:
    name = str(data.get("name") or "").strip()[:120]
    brand = str(data.get("brand") or "").strip()[:60]
    if brand and name and brand.casefold() not in name.casefold():
        name = f"{brand} {name}".strip()[:120]

    description = str(data.get("description") or "").strip()[:300]
    unit = str(data.get("unit") or "").strip()[:20]
    category_hint = str(
        data.get("category_hint") or data.get("category") or ""
    ).strip()[:80]

    price: int | None = None
    raw_price = data.get("price")
    if raw_price is not None and str(raw_price).strip() not in {"", "null", "None"}:
        digits = re.sub(r"[^\d]", "", str(raw_price))
        if digits:
            value = int(digits)
            if value > 0:
                price = value

    if unit and description and unit.casefold() not in description.casefold():
        description = f"{description} ({unit})".strip()
    elif unit and not description:
        description = unit

    category_id = match_category_id(category_hint, categories)
    return {
        "name": name,
        "brand": brand,
        "description": description,
        "price": price,
        "category_hint": category_hint,
        "category_id": category_id,
        "unit": unit,
        "confidence": float(data.get("confidence") or 0) or None,
    }


def parse_product_photo(
    image_bytes: bytes,
    *,
    mime_type: str = "image/jpeg",
    categories: list[Any] | None = None,
) -> dict[str, Any]:
    """Rasm → draft maydonlar. Kalit yo‘q bo‘lsa VisionKeyMissing."""
    if not OPENAI_API_KEY:
        raise VisionKeyMissing(AI_KEY_REQUIRED_MSG)
    if not image_bytes:
        raise VisionParseError("Rasm bo‘sh")

    cats = categories if categories is not None else get_categories(active_only=True)
    cat_names = [str(c["name"]) for c in cats if c["name"]]
    cat_list = ", ".join(cat_names[:40]) if cat_names else "Umumiy"

    b64 = base64.b64encode(image_bytes).decode("ascii")
    data_url = f"data:{mime_type};base64,{b64}"

    system = (
        "Sen O‘zbekiston do‘koni (Baraka Market) uchun mahsulot kartochkasi yordamchisisan. "
        "Rasmda ko‘rinadigan mahsulotni o‘qi. Faqat JSON qaytar, boshqa matn yo‘q.\n"
        "Maydonlar:\n"
        '- "name": qisqa mahsulot nomi (o‘zbekcha yoki yorliqdagi brend+nom)\n'
        '- "brand": brend (yo‘q bo‘lsa "")\n'
        '- "description": 1 qisqa jumla\n'
        '- "price": yorliqda aniq so‘m narxi bo‘lsa butun son, aks holda null\n'
        '- "category_hint": quyidagi toifalardan eng mosiga yaqin so‘z\n'
        f"  Mavjud toifalar: {cat_list}\n"
        '- "unit": kg/l/dona/ml/g yoki ""\n'
        '- "confidence": 0..1\n'
        "Narxni taxmin qilma — faqat yorliqda aniq ko‘rinsa."
    )

    payload = {
        "model": _vision_model(),
        "temperature": 0.2,
        "max_tokens": 500,
        "messages": [
            {"role": "system", "content": system},
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Bu mahsulot rasmidan JSON draft yasang.",
                    },
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            },
        ],
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
            body = json.loads(resp.read().decode("utf-8"))
        raw = body["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")[:200]
        logger.warning("Vision HTTP %s: %s", exc.code, detail)
        raise VisionParseError(f"AI xato ({exc.code})") from exc
    except (urllib.error.URLError, TimeoutError, KeyError, IndexError, TypeError) as exc:
        logger.warning("Vision xato: %s", exc)
        raise VisionParseError("AI javob bermadi") from exc

    draft = _normalize_draft(_extract_json_object(str(raw)), cats)
    if not draft["name"]:
        raise VisionParseError("Nom aniqlanmadi — boshqa rasm yuboring")
    return draft
