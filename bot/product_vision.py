"""Mahsulot rasmidan maydonlarni ajratish (OpenAI vision yoki demo/mock)."""

from __future__ import annotations

import base64
import json
import logging
import re
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from typing import Any, Protocol

from bot.config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_VISION_MODEL

logger = logging.getLogger(__name__)


@dataclass
class ProductDraft:
    name: str = ""
    brand: str = ""
    price: int | None = None
    category_hint: str = ""
    unit: str = ""
    description: str = ""
    confidence: float = 0.0
    provider: str = "mock"
    raw_notes: str = ""

    def display_name(self) -> str:
        name = (self.name or "").strip()
        brand = (self.brand or "").strip()
        if brand and brand.lower() not in name.lower():
            return f"{brand} {name}".strip()
        return name or brand

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["display_name"] = self.display_name()
        return data


class VisionProvider(Protocol):
    name: str

    def extract_from_image(
        self, image_bytes: bytes, mime_type: str = "image/jpeg"
    ) -> ProductDraft:
        ...


def _parse_price(value: Any) -> int | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        n = int(value)
        return n if n >= 0 else None
    text = str(value)
    digits = re.sub(r"[^\d]", "", text.replace(" ", "").replace(",", ""))
    if not digits:
        return None
    try:
        return max(0, int(digits))
    except ValueError:
        return None


def _coerce_draft(data: dict[str, Any], provider: str) -> ProductDraft:
    conf = data.get("confidence", 0.5)
    try:
        confidence = float(conf)
    except (TypeError, ValueError):
        confidence = 0.5
    return ProductDraft(
        name=str(data.get("name") or "").strip()[:120],
        brand=str(data.get("brand") or "").strip()[:80],
        price=_parse_price(data.get("price")),
        category_hint=str(data.get("category_hint") or data.get("category") or "").strip()[
            :80
        ],
        unit=str(data.get("unit") or "").strip()[:40],
        description=str(data.get("description") or "").strip()[:300],
        confidence=max(0.0, min(1.0, confidence)),
        provider=provider,
        raw_notes=str(data.get("raw_notes") or data.get("notes") or "").strip()[:300],
    )


def _extract_json_object(text: str) -> dict[str, Any]:
    text = (text or "").strip()
    if not text:
        return {}
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        return {}
    try:
        data = json.loads(match.group(0))
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


class MockVisionProvider:
    """Kalit yo‘q bo‘lganda pipeline ishlashi uchun demo maydonlar."""

    name = "mock"

    def extract_from_image(
        self, image_bytes: bytes, mime_type: str = "image/jpeg"
    ) -> ProductDraft:
        size_kb = max(1, len(image_bytes) // 1024)
        return ProductDraft(
            name="Demo mahsulot (yorliq)",
            brand="Baraka",
            price=15000,
            category_hint="Oziq-ovqat",
            unit="dona",
            description=(
                f"Demo rejim — haqiqiy OCR yo‘q. Rasm ~{size_kb} KB. "
                "Maydonlarni tekshirib saqlang."
            ),
            confidence=0.2,
            provider=self.name,
            raw_notes="OPENAI_API_KEY o‘rnatilmagan yoki mock majburiy.",
        )


class OpenAIVisionProvider:
    name = "openai"

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ) -> None:
        self.api_key = (api_key or OPENAI_API_KEY).strip()
        self.base_url = (base_url or OPENAI_BASE_URL).rstrip("/")
        self.model = (model or OPENAI_VISION_MODEL).strip() or "gpt-4o-mini"

    def extract_from_image(
        self, image_bytes: bytes, mime_type: str = "image/jpeg"
    ) -> ProductDraft:
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY yo‘q")
        mime = (mime_type or "image/jpeg").split(";")[0].strip() or "image/jpeg"
        b64 = base64.b64encode(image_bytes).decode("ascii")
        system = (
            "Siz Baraka Market do‘koni uchun mahsulot yorlig‘ini o‘qiydigan yordamchisiz. "
            "Faqat JSON qaytaring (markdown yo‘q). Maydonlar: "
            "name (string), brand (string), price (integer so‘m yoki null), "
            "category_hint (o‘zbekcha toifa ishorasi), unit (kg|l|dona|ml|g|...), "
            "description (qisqa o‘zbekcha), confidence (0..1). "
            "Narx yorliqda ko‘rinmasa null. O‘zbek/rus/lotin matnni to‘g‘ri o‘qing."
        )
        user_text = (
            "Shu rasm dagi mahsulot maydonlarini JSON qilib ajrating. "
            "Do‘kon katalogiga qo‘shish uchun."
        )
        payload = {
            "model": self.model,
            "temperature": 0.1,
            "max_tokens": 500,
            "messages": [
                {"role": "system", "content": system},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_text},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime};base64,{b64}",
                            },
                        },
                    ],
                },
            ],
        }
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        content = body["choices"][0]["message"]["content"]
        parsed = _extract_json_object(content)
        draft = _coerce_draft(parsed, provider=self.name)
        if not draft.name:
            draft.name = "Noma’lum mahsulot"
            draft.confidence = min(draft.confidence, 0.3)
        return draft


def get_vision_provider(force_mock: bool = False) -> VisionProvider:
    if force_mock or not OPENAI_API_KEY:
        return MockVisionProvider()
    return OpenAIVisionProvider()


def extract_product_fields(
    image_bytes: bytes,
    mime_type: str = "image/jpeg",
    *,
    force_mock: bool = False,
) -> ProductDraft:
    provider = get_vision_provider(force_mock=force_mock)
    try:
        return provider.extract_from_image(image_bytes, mime_type=mime_type)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError, KeyError, IndexError, RuntimeError) as exc:
        logger.warning("Vision provider %s failed: %s — mockga o‘tdi", provider.name, exc)
        mock = MockVisionProvider().extract_from_image(image_bytes, mime_type=mime_type)
        mock.raw_notes = f"AI xato, demo: {exc}"
        return mock


def match_category_id(hint: str, categories: list[Any]) -> int | None:
    """category_hint ni mavjud toifa nomiga yaqinlashtirish."""
    q = (hint or "").strip().lower()
    if not q or not categories:
        return None

    def _norm(s: str) -> str:
        return (
            s.lower()
            .replace("‘", "'")
            .replace("’", "'")
            .replace("ё", "e")
        )

    qn = _norm(q)
    best_id: int | None = None
    best_score = 0
    for cat in categories:
        name = _norm(str(cat["name"] or ""))
        if not name:
            continue
        score = 0
        if qn == name:
            score = 100
        elif qn in name or name in qn:
            score = 80
        else:
            tokens = [t for t in re.split(r"\s+", qn) if len(t) > 2]
            hits = sum(1 for t in tokens if t in name)
            score = hits * 25
        if score > best_score:
            best_score = score
            best_id = int(cat["id"])
    return best_id if best_score >= 25 else None


def build_description(draft: ProductDraft) -> str:
    parts: list[str] = []
    if draft.description:
        parts.append(draft.description)
    bits = []
    if draft.unit:
        bits.append(f"Birlik: {draft.unit}")
    if draft.brand and draft.brand.lower() not in (draft.name or "").lower():
        bits.append(f"Brend: {draft.brand}")
    if bits:
        parts.append(" · ".join(bits))
    return "\n".join(parts).strip()[:300]
