"""AI Sotuvchi matching va savat testlari."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path


class MatchingTests(unittest.TestCase):
    def test_fuzzy_pechene(self):
        from ai_sotuvchi.matching import query_matches_name

        score = query_matches_name("Yubileniy PECHENE", "Yubileyniy Pechene 1kg")
        self.assertGreater(score, 0)

    def test_parse_somlik(self):
        from ai_sotuvchi.matching import parse_segment

        seg = parse_segment("guruch 5000 so‘mlik")
        self.assertIsNotNone(seg)
        self.assertEqual(seg["query"], "guruch")
        self.assertEqual(seg["want_money"], 5000)

        seg2 = parse_segment("shakar 10 minglik")
        self.assertEqual(seg2["want_money"], 10000)
        self.assertEqual(seg2["query"], "shakar")

    def test_grams_and_price(self):
        from ai_sotuvchi.matching import grams_for_money, price_from_kg

        self.assertEqual(price_from_kg(18000, 250), 4500)
        self.assertEqual(price_from_kg(18000, 500), 9000)
        self.assertEqual(grams_for_money(18000, 5000), 278)

    def test_should_list_variants(self):
        from ai_sotuvchi.matching import should_list_variants

        products = [{"id": 1, "name": "Guruch 1kg", "price": 18000}]
        self.assertTrue(
            should_list_variants({"qty": 1, "want_size": None}, products)
        )
        self.assertFalse(
            should_list_variants(
                {"qty": 1, "want_size": 2, "want_unit": "kg"}, products
            )
        )
        self.assertFalse(
            should_list_variants({"qty": 1, "want_money": 5000}, products)
        )

    def test_format_variants_includes_somlik(self):
        from ai_sotuvchi.matching import format_variants

        products = [
            {"id": 1, "name": "Guruch 250g", "price": 4500},
            {"id": 2, "name": "Guruch 500g", "price": 9000},
            {"id": 3, "name": "Guruch 1kg", "price": 18000},
        ]
        text = format_variants("guruch", products)
        self.assertIn("250 gramm", text)
        self.assertIn("So‘mlik", text)
        self.assertIn("5 000 so‘mlik", text)

    def test_packs_needed_unit_convert(self):
        from ai_sotuvchi.matching import packs_needed

        self.assertEqual(packs_needed(2, "kg", "Guruch 1kg"), 2)
        self.assertEqual(packs_needed(250, "g", "Guruch 250g"), 1)
        self.assertEqual(packs_needed(1, "kg", "Guruch 250g"), 4)


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self._tmp.close()
        from ai_sotuvchi import config

        self._old = config.DATABASE_PATH
        config.DATABASE_PATH = self._tmp.name
        from ai_sotuvchi import database as db

        db.init_db()
        self.db = db

    def tearDown(self):
        from ai_sotuvchi import config

        config.DATABASE_PATH = self._old
        try:
            os.unlink(self._tmp.name)
        except OSError:
            pass

    def test_weight_packs_from_1kg(self):
        products = {str(p["name"]): int(p["price"]) for p in self.db.list_products()}
        self.assertIn("Guruch 1kg", products)
        self.assertIn("Guruch 250g", products)
        self.assertIn("Guruch 500g", products)
        self.assertEqual(products["Guruch 250g"], 4500)
        self.assertEqual(products["Guruch 500g"], 9000)

    def test_cola_variants(self):
        names = {str(p["name"]).lower() for p in self.db.list_products()}
        self.assertTrue(any("0.5" in n and "cola" in n for n in names))
        self.assertTrue(any("1.5" in n and "cola" in n for n in names))

    def test_somlik_cart(self):
        guruch = next(
            p
            for p in self.db.list_products()
            if str(p["name"]) == "Guruch 1kg"
        )
        self.db.cart_add_by_money(
            1,
            int(guruch["id"]),
            amount=5000,
            grams=278,
            label="Guruch ~278 g (5 000 so‘mlik)",
        )
        items = self.db.get_cart(1)
        self.assertEqual(len(items), 1)
        self.assertTrue(items[0]["is_custom"])
        self.assertEqual(items[0]["line_total"], 5000)
        self.assertEqual(items[0]["grams"], 278)

    def test_customer_profile(self):
        self.assertIsNone(self.db.get_customer(7))
        self.db.upsert_customer(
            7, name="Ali", phone="+998901112233", address="Toshkent, Chilonzor"
        )
        c = self.db.get_customer(7)
        self.assertEqual(c["name"], "Ali")
        self.assertIn("Chilonzor", c["address"])

    def test_find_variants_fuzzy(self):
        from ai_sotuvchi.ai import find_variants

        pid = self.db.add_product(
            "Yubileyniy Pechene 1kg", 20000, category="Oziq-ovqat"
        )
        self.assertGreater(pid, 0)
        found = find_variants("Yubileniy PECHENE")
        names = [str(p["name"]).lower() for p in found]
        self.assertTrue(any("pechene" in n or "yubileyniy" in n for n in names))

    def test_reply_lists_guruch_packs(self):
        from ai_sotuvchi.ai import reply_to_user

        text, products = reply_to_user(99, "guruch")
        self.assertIn("Qadoq", text)
        self.assertIn("So‘mlik", text)
        self.assertGreaterEqual(len(products), 3)

    def test_reply_somlik_adds_cart(self):
        from ai_sotuvchi.ai import reply_to_user

        text, _ = reply_to_user(55, "guruch 5000 so‘mlik")
        self.assertIn("qo‘shildi", text.lower())
        items = self.db.get_cart(55)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["price"], 5000)


if __name__ == "__main__":
    unittest.main()
