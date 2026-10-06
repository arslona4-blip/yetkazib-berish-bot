"""product_vision.normalize_draft unit checks (no API key)."""

from __future__ import annotations

import unittest
from unittest.mock import patch


class NormalizeDraftTests(unittest.TestCase):
    def test_price_and_unit(self) -> None:
        from bot.product_vision import normalize_draft

        with patch("bot.product_vision.get_categories", return_value=[]):
            d = normalize_draft(
                {
                    "name": "Coca-Cola",
                    "brand": "Coca-Cola",
                    "price": "12 000",
                    "category_hint": "ichimlik",
                    "unit": "l",
                    "description": "Gazli ichimlik",
                    "barcode": "4601234567890",
                }
            )
        self.assertEqual(d["name"], "Coca-Cola")
        self.assertEqual(d["price"], 12000)
        self.assertIn("l", (d["description"] or "").lower())
        self.assertEqual(d["barcode"], "4601234567890")

    def test_category_match(self) -> None:
        from bot.product_vision import normalize_draft

        cats = [
            {"id": 3, "name": "Ichimliklar"},
            {"id": 5, "name": "Non mahsulotlari"},
        ]
        with patch("bot.product_vision.get_categories", return_value=cats):
            d = normalize_draft(
                {
                    "name": "Pepsi 1L",
                    "price": None,
                    "category_hint": "ichimlik",
                    "unit": "l",
                    "description": "",
                }
            )
        self.assertEqual(d["category_id"], 3)


if __name__ == "__main__":
    unittest.main()
