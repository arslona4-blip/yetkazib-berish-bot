"""Kamera orqali mahsulot — oddiy unit testlar (API kalitsiz)."""

from __future__ import annotations

import unittest
from types import SimpleNamespace

from bot.product_vision import (
    AI_KEY_REQUIRED_MSG,
    VisionKeyMissing,
    _normalize_draft,
    match_category_id,
    parse_product_photo,
)


class ProductVisionTests(unittest.TestCase):
    def test_match_category(self) -> None:
        cats = [
            SimpleNamespace(**{"name": "Ichimliklar", "id": 1}),
            SimpleNamespace(**{"name": "Oziq-ovqat", "id": 2}),
        ]
        # Row-like access
        class Row(dict):
            def __getitem__(self, key):  # noqa: ANN001
                return dict.__getitem__(self, key)

        rows = [Row(id=1, name="Ichimliklar"), Row(id=2, name="Oziq-ovqat")]
        self.assertEqual(match_category_id("ichimlik", rows), 1)
        self.assertEqual(match_category_id("guruch / oziq", rows), 2)
        self.assertIsNone(match_category_id("", rows))

    def test_normalize_draft_price_and_brand(self) -> None:
        draft = _normalize_draft(
            {
                "name": "Cola 1L",
                "brand": "Coca-Cola",
                "price": "12 000 so'm",
                "description": "Gazli ichimlik",
                "category_hint": "Ichimliklar",
                "unit": "l",
            },
            categories=[],
        )
        self.assertIn("Coca-Cola", draft["name"])
        self.assertEqual(draft["price"], 12000)
        self.assertIn("l", draft["description"].casefold())

    def test_no_api_key_message(self) -> None:
        from bot import product_vision as pv

        old = pv.OPENAI_API_KEY
        try:
            pv.OPENAI_API_KEY = ""
            with self.assertRaises(VisionKeyMissing) as ctx:
                parse_product_photo(b"fake")
            self.assertEqual(str(ctx.exception), AI_KEY_REQUIRED_MSG)
        finally:
            pv.OPENAI_API_KEY = old


if __name__ == "__main__":
    unittest.main()
