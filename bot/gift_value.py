"""100 000+ aksiya: sovg‘a limi = Coca-Cola 1L narxi + tanlov."""

from __future__ import annotations

import re
from typing import Any

from bot.config import GIFT_VALUE_FALLBACK

# Mijozga doim ko‘rinadigan asosiy ichimliklar
GIFT_DRINK_CHOICES: tuple[dict[str, str], ...] = (
    {"key": "cola", "label": "Coca-Cola 1L"},
    {"key": "pepsi", "label": "Pepsi 1L"},
    {"key": "fanta", "label": "Fanta 1L"},
)


def _norm_name(name: str) -> str:
    return (
        (name or "")
        .lower()
        .replace("‘", "'")
        .replace("’", "'")
        .replace("-", " ")
    )


def _ml_from_name(name: str) -> int | None:
    n = _norm_name(name).replace(",", ".")
    m = re.search(r"(\d+(?:\.\d+)?)\s*l\b", n)
    if m:
        return int(round(float(m.group(1)) * 1000))
    m = re.search(r"(\d+)\s*ml\b", n)
    if m:
        return int(m.group(1))
    return None


def _is_coca_cola(name: str) -> bool:
    n = _norm_name(name)
    if "pepsi" in n or "fanta" in n or "sprite" in n:
        return False
    return "coca" in n or re.search(r"\bcola\b", n) or re.search(r"\bkola\b", n)


def _is_pepsi(name: str) -> bool:
    return "pepsi" in _norm_name(name)


def _is_fanta(name: str) -> bool:
    return "fanta" in _norm_name(name)


def _match_drink(key: str, name: str) -> bool:
    if key == "cola":
        return _is_coca_cola(name)
    if key == "pepsi":
        return _is_pepsi(name)
    if key == "fanta":
        return _is_fanta(name)
    return False


def _pick_drink_1l(products: list[Any], key: str) -> Any | None:
    hits: list[tuple[int, int, Any]] = []
    for p in products:
        if not _match_drink(key, str(p["name"])):
            continue
        ml = _ml_from_name(str(p["name"]))
        if not ml:
            continue
        dist = abs(ml - 1000)
        hits.append((dist, ml, p))
    if not hits:
        return None
    hits.sort(key=lambda x: (x[0], abs(x[1] - 1000)))
    return hits[0][2]


def pick_cola_1l_product(products: list[Any] | None = None) -> Any | None:
    """Katalogdan Coca-Cola 1L (yoki eng yaqin litr)."""
    if products is None:
        from bot.database import get_products

        products = list(get_products())
    return _pick_drink_1l(products, "cola")


def get_gift_value_limit() -> int:
    """Sovg‘a limi (so‘m) = Coca-Cola 1L narxi; topilmasa fallback."""
    try:
        p = pick_cola_1l_product()
        if p is not None:
            price = int(p["price"] or 0)
            if price > 0:
                return price
    except Exception:
        pass
    return max(1000, int(GIFT_VALUE_FALLBACK))


def get_gift_value_info() -> dict[str, Any]:
    """amount + reference product name for messages."""
    amount = get_gift_value_limit()
    ref = "Coca-Cola 1L"
    try:
        p = pick_cola_1l_product()
        if p is not None:
            ref = str(p["name"])
            amount = int(p["price"] or amount)
    except Exception:
        pass
    return {"amount": amount, "ref_name": ref}


def list_gift_options(*, alt_limit: int = 24) -> dict[str, Any]:
    """Mini App / bot uchun sovg‘a tanlovlari."""
    from bot.database import get_products

    products = list(get_products())
    limit = get_gift_value_limit()
    drinks: list[dict[str, Any]] = []
    drink_ids: set[int] = set()
    for choice in GIFT_DRINK_CHOICES:
        hit = _pick_drink_1l(products, choice["key"])
        item: dict[str, Any] = {
            "key": choice["key"],
            "label": choice["label"],
            "product_id": None,
            "price": limit,
        }
        if hit is not None:
            pid = int(hit["id"])
            drink_ids.add(pid)
            item["product_id"] = pid
            item["label"] = str(hit["name"])
            item["price"] = int(hit["price"] or limit)
        drinks.append(item)

    alts: list[dict[str, Any]] = []
    for p in products:
        pid = int(p["id"])
        if pid in drink_ids:
            continue
        price = int(p["price"] or 0)
        if price <= 0 or price > limit:
            continue
        alts.append(
            {
                "product_id": pid,
                "label": str(p["name"]),
                "price": price,
            }
        )
    alts.sort(key=lambda x: (x["label"].lower(), x["price"]))
    alts = alts[: max(0, int(alt_limit))]
    return {
        "threshold": None,  # caller fills from config if needed
        "limit": limit,
        "drinks": drinks,
        "alts": alts,
    }


def resolve_gift_choice(
    *,
    gift_key: str = "",
    gift_choice: str = "",
    gift_product_id: int | None = None,
) -> str:
    """Buyurtmaga yoziladigan sovg‘a matni. Bo‘sh bo‘lsa — ValueError."""
    key = (gift_key or "").strip().lower()
    text = (gift_choice or "").strip()
    options = list_gift_options()
    limit = int(options["limit"])

    if gift_product_id:
        for d in options["drinks"]:
            if d.get("product_id") == int(gift_product_id):
                return str(d["label"])
        for a in options["alts"]:
            if int(a["product_id"]) == int(gift_product_id):
                return str(a["label"])
        from bot.database import get_product

        p = get_product(int(gift_product_id))
        if not p:
            raise ValueError("Sovg‘a mahsuloti topilmadi")
        price = int(p["price"] or 0)
        if price > limit:
            raise ValueError(
                f"Sovg‘a limidan oshib ketdi (maks {limit:,} so‘m)".replace(",", " ")
            )
        return str(p["name"])

    if key in {"cola", "pepsi", "fanta"}:
        for d in options["drinks"]:
            if d["key"] == key:
                return str(d["label"])
        for c in GIFT_DRINK_CHOICES:
            if c["key"] == key:
                return c["label"]

    if text:
        # Oldindan belgilangan ichimlik yorliqlari
        low = _norm_name(text)
        for c in GIFT_DRINK_CHOICES:
            if _norm_name(c["label"]) == low or c["key"] in low:
                return c["label"]
        for d in options["drinks"]:
            if _norm_name(d["label"]) == low:
                return str(d["label"])
        for a in options["alts"]:
            if _norm_name(a["label"]) == low:
                return str(a["label"])
        # Erkin matn (masalan «Sprite 1L» yoki katalogdagi nom)
        if len(text) > 80:
            raise ValueError("Sovg‘a nomi juda uzun")
        return text

    raise ValueError("Sovg‘ani tanlang: Coca-Cola / Pepsi / Fanta yoki shu narxdagi mahsulot")
