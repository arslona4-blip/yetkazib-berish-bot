"""Demo: mock vision → create_product (kalitsiz)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock


class CameraIntakeTests(unittest.TestCase):
    def test_mock_extract_and_save(self) -> None:
        from bot.product_vision import (
            MockVisionProvider,
            build_description,
            match_category_id,
        )

        draft = MockVisionProvider().extract_from_image(b"fake-jpeg-bytes")
        self.assertEqual(draft.provider, "mock")
        self.assertTrue(draft.display_name())
        self.assertIsNotNone(draft.price)
        self.assertIn("Birlik", build_description(draft))

        class Cat:
            def __getitem__(self, key: str):
                return {"id": 3, "name": "Oziq-ovqat"}[key]

        self.assertEqual(match_category_id("oziq", [Cat()]), 3)

    def test_create_product_with_temp_db(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "test.db")
            with mock.patch("bot.config.DATABASE_PATH", db_path), mock.patch(
                "bot.database.DATABASE_PATH", db_path
            ):
                from bot import database as db

                db.init_db()
                cats = db.get_categories(active_only=False)
                cat_id = int(cats[0]["id"]) if cats else db.create_category("Test")
                from bot.product_vision import MockVisionProvider, build_description

                draft = MockVisionProvider().extract_from_image(b"x" * 200)
                pid = db.create_product(
                    name=draft.display_name(),
                    price=int(draft.price or 0),
                    description=build_description(draft),
                    category_id=cat_id,
                    stock=10,
                )
                product = db.get_product_by_id(pid)
                self.assertIsNotNone(product)
                self.assertEqual(product["name"], draft.display_name())


if __name__ == "__main__":
    unittest.main()
