"""100 000+ aksiya: sovg‘a limi = Coca-Cola 1L narxi."""

from __future__ import annotations

import re
from typing import Any

from bot.config import GIFT_VALUE_FALLBACK


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


def pick_cola_1l_product(products: list[Any] | None = None) -> Any | None:
    """Katalogdan Coca-Cola 1L (yoki eng yaqin litr)."""
    if products is None:
        from bot.database import get_products

        products = list(get_products())
    cokes: list[tuple[int, int, Any]] = []
    for p in products:
        if not _is_coca_cola(str(p["name"])):
            continue
        ml = _ml_from_name(str(p["name"]))
        if not ml:
            continue
        # 1L ga yaqinlik (0 = ideal)
        dist = abs(ml - 1000)
        cokes.append((dist, ml, p))
    if not cokes:
        return None
    cokes.sort(key=lambda x: (x[0], abs(x[1] - 1000)))
    return cokes[0][2]


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
