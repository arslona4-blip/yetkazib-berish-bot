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

MAX_IMAGE_BYTES = 8 * 1024 * 1024  # 8 MB

_VISION_SYSTEM = (
    "Sen Baraka Market (O‘zbekiston do‘koni) uchun mahsulot katalog yordamchisisan.\n"
    "Rasmda ko‘rinadigan mahsulot yorlig‘i / qadoqdan ma’lumotni o‘qi.\n"
    "Faqat JSON qaytar (boshqa matn yo‘q). Maydonlar:\n"
    "{\n"
    '  "name": "mahsulot nomi o‘zbekcha yoki yorliqdagi til",\n'
    '  "brand": "brend yoki bo‘sh",\n'
    '  "price": null yoki butun so‘m (faqat yorliqda aniq narx bo‘lsa),\n'
    '  "category_hint": "toifa ishorasi: ichimlik, sut, non, meva, go‘sht, ...",\n'
    '  "unit": "dona|kg|l|gr|ml|paket|...",\n'
    '  "description": "1 qisqa o‘zbekcha jumla",\n'
    '  "barcode": "raqamlar yoki bo‘sh"\n'
    "}\n"
    "Narxni o‘ylab topma. Ko‘rinmasa price=null. Nomni to‘ldirishga harakat qil."
)


class VisionNotConfigured(RuntimeError):
    """OPENAI_API_KEY yo‘q."""


class VisionError(RuntimeError):
    """Vision API chaqiruvida xato."""


def vision_configured() -> bool:
    return bool(OPENAI_API_KEY)


def _vision_model() -> str:
    return (OPENAI_VISION_MODEL or OPENAI_MODEL or "gpt-4o-mini").strip()


def _guess_mime(data: bytes, declared: str | None = None) -> str:
    if declared and declared.startswith("image/"):
        return declared.split(";")[0].strip()
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return "image/jpeg"


def _extract_json_object(text: str) -> dict[str, Any]:
    raw = (text or "").strip()
    if not raw:
        raise VisionError("AI bo‘sh javob qaytardi")
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.I)
        raw = re.sub(r"\s*```$", "", raw)
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{[\s\S]*\}", raw)
    if not match:
        raise VisionError("AI JSON qaytarmadi")
    data = json.loads(match.group(0))
    if not isinstance(data, dict):
        raise VisionError("AI JSON obyekt emas")
    return data


def _norm_price(value: Any) -> int | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        n = int(round(float(value)))
        return n if n >= 0 else None
    s = str(value).strip().lower().replace(" ", "").replace(",", "")
    s = s.replace("so'm", "").replace("so‘m", "").replace("sum", "")
    s = re.sub(r"[^\d.]", "", s)
    if not s:
        return None
    try:
        n = int(round(float(s)))
    except ValueError:
        return None
    return n if n >= 0 else None


def _match_category_id(hint: str) -> int | None:
    h = (hint or "").strip().lower()
    if not h:
        return None
    cats = get_categories(active_only=True)
    if not cats:
        return None
    # Exact / contains on category name
    for c in cats:
        name = str(c["name"] or "").strip().lower()
        if not name:
            continue
        if h == name or h in name or name in h:
            return int(c["id"])
    # Token overlap
    tokens = [t for t in re.split(r"[\s,/|+]+", h) if len(t) >= 3]
    best_id = None
    best_score = 0
    for c in cats:
        name = str(c["name"] or "").strip().lower()
        score = sum(1 for t in tokens if t in name)
        if score > best_score:
            best_score = score
            best_id = int(c["id"])
    return best_id if best_score else None


def normalize_draft(raw: dict[str, Any]) -> dict[str, Any]:
    name = str(raw.get("name") or "").strip()
    brand = str(raw.get("brand") or "").strip()
    if brand and brand.lower() not in name.lower() and name:
        # Prefer brand + name when brand missing from title
        pass
    unit = str(raw.get("unit") or "").strip().lower() or None
    description = str(raw.get("description") or "").strip()
    if unit and unit not in description.lower():
        description = (f"{description} · {unit}".strip(" ·") if description else unit)
    barcode = str(raw.get("barcode") or "").strip()
    barcode = re.sub(r"\D", "", barcode) or None
    category_hint = str(raw.get("category_hint") or "").strip() or None
    price = _norm_price(raw.get("price"))
    category_id = _match_category_id(category_hint or "")
    if not name and brand:
        name = brand
    return {
        "name": name,
        "brand": brand or None,
        "price": price,
        "category_hint": category_hint,
        "category_id": category_id,
        "unit": unit,
        "description": description or None,
        "barcode": barcode,
    }


def extract_product_from_image(
    image_bytes: bytes,
    *,
    mime: str | None = None,
) -> dict[str, Any]:
    if not OPENAI_API_KEY:
        raise VisionNotConfigured(
            "OPENAI_API_KEY sozlanmagan. Vision uchun kalit kerak "
            "(Railway/env → OPENAI_API_KEY)."
        )
    if not image_bytes:
        raise VisionError("Rasm bo‘sh")
    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise VisionError("Rasm juda katta (max 8 MB)")

    mime_type = _guess_mime(image_bytes, mime)
    b64 = base64.b64encode(image_bytes).decode("ascii")
    data_url = f"data:{mime_type};base64,{b64}"
    model = _vision_model()
    payload = {
        "model": model,
        "temperature": 0.2,
        "max_tokens": 500,
        "messages": [
            {"role": "system", "content": _VISION_SYSTEM},
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Shu mahsulot rasmidan katalog maydonlarini JSON qilib ber.",
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
            data = json.loads(resp.read().decode("utf-8"))
        content = data["choices"][0]["message"]["content"]
        if isinstance(content, list):
            parts = []
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text":
                    parts.append(str(part.get("text") or ""))
                elif isinstance(part, str):
                    parts.append(part)
            content = "\n".join(parts)
        draft = normalize_draft(_extract_json_object(str(content)))
        draft["source"] = "openai"
        draft["model"] = model
        return draft
    except VisionError:
        raise
    except urllib.error.HTTPError as exc:
        body = ""
        try:
            body = exc.read().decode("utf-8", errors="ignore")[:400]
        except Exception:
            pass
        logger.warning("Vision HTTP %s: %s", exc.code, body)
        raise VisionError(
            f"Vision API xato (HTTP {exc.code}). Kalit/modelni tekshiring."
        ) from exc
    except (urllib.error.URLError, TimeoutError, KeyError, IndexError, json.JSONDecodeError) as exc:
        logger.warning("Vision xato: %s", exc)
        raise VisionError("Vision API bilan bog‘lanib bo‘lmadi. Keyinroq urinib ko‘ring.") from exc
