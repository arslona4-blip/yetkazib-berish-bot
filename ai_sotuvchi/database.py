from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Iterator

from ai_sotuvchi.config import DATABASE_PATH


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price INTEGER NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                category TEXT NOT NULL DEFAULT 'Umumiy',
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                customer_name TEXT NOT NULL DEFAULT '',
                phone TEXT NOT NULL DEFAULT '',
                address TEXT NOT NULL DEFAULT '',
                items_json TEXT NOT NULL DEFAULT '[]',
                total INTEGER NOT NULL DEFAULT 0,
                note TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'new',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS cart (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 1,
                custom_price INTEGER,
                custom_label TEXT NOT NULL DEFAULT '',
                grams INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS chat_memory (
                user_id INTEGER PRIMARY KEY,
                history_json TEXT NOT NULL DEFAULT '[]',
                updated_at TEXT NOT NULL
            );
            """
        )
        # Rasm ustuni (professional katalog)
        cols = {r[1] for r in conn.execute("PRAGMA table_info(products)").fetchall()}
        if "image_file_id" not in cols:
            conn.execute(
                "ALTER TABLE products ADD COLUMN image_file_id TEXT"
            )
        order_cols = {r[1] for r in conn.execute("PRAGMA table_info(orders)").fetchall()}
        if "delivery_fee" not in order_cols:
            conn.execute(
                "ALTER TABLE orders ADD COLUMN delivery_fee INTEGER NOT NULL DEFAULT 0"
            )
        if "subtotal" not in order_cols:
            conn.execute(
                "ALTER TABLE orders ADD COLUMN subtotal INTEGER NOT NULL DEFAULT 0"
            )
        _migrate_cart_table(conn)
        count = conn.execute("SELECT COUNT(*) AS c FROM products").fetchone()["c"]
        if count == 0:
            seed = [
                ("Guruch 1kg", 18000, "Oq guruch, yumshoq", "Oziq-ovqat"),
                ("Sut 0.5L", 7000, "Pastörizatsiya qilingan", "Ichimliklar"),
                ("Sut 1L", 12000, "Pastörizatsiya qilingan", "Ichimliklar"),
                ("Non", 4000, "Yangi non", "Oziq-ovqat"),
                ("Coca Cola 0.5L", 8000, "Gazli ichimlik", "Ichimliklar"),
                ("Coca-Cola 1.5L", 14000, "Gazli ichimlik", "Ichimliklar"),
                ("Coca Cola 2L", 18000, "Gazli ichimlik", "Ichimliklar"),
                ("Yog‘ 1L", 22000, "O‘simlik yog‘i", "Oziq-ovqat"),
                ("Shakar 1kg", 15000, "Oq shakar", "Oziq-ovqat"),
                ("Sovun", 8000, "Hojatxona sovuni", "Uy-ro‘zg‘or"),
                ("Nam salfetka", 10000, "120 donalik", "Uy-ro‘zg‘or"),
            ]
            for name, price, desc, cat in seed:
                conn.execute(
                    """
                    INSERT INTO products (name, price, description, category, is_active, created_at)
                    VALUES (?, ?, ?, ?, 1, ?)
                    """,
                    (name, price, desc, cat, _now()),
                )
        # Mavjud DB ga ham hajm variantlarini qo‘shish (yo‘q bo‘lsa)
        _ensure_size_variants(conn)
        # Barcha kg li oilalar: 250g/500g narxi 1kg dan
        _sync_all_weight_pack_prices(conn)
        _fix_common_product_spellings(conn)


def _fix_common_product_spellings(conn: sqlite3.Connection) -> None:
    """Odatiy yozuv xatolarini tuzatish (pechene, yubileyniy, …)."""
    fixes = [
        ("YUBILEYNI PECNENE  1 kg", "Yubileyniy Pechene 1kg"),
        ("Yubileyni pecnene 250g", "Yubileyniy Pechene 250g"),
        ("Yubileyni pecnene 500g", "Yubileyniy Pechene 500g"),
        ("YUBILEYNI PECNENE 1 kg", "Yubileyniy Pechene 1kg"),
        ("Yubileyni pecnene 1kg", "Yubileyniy Pechene 1kg"),
    ]
    for old, new in fixes:
        conn.execute(
            "UPDATE products SET name = ? WHERE name = ?",
            (new, old),
        )
        # case-insensitive
        conn.execute(
            "UPDATE products SET name = ? WHERE lower(name) = lower(?) AND name != ?",
            (new, old, new),
        )


def _price_from_kg(price_1kg: int, grams: int) -> int:
    """1 kg narxidan gramm uchun proporsional narx (butun so‘m)."""
    return max(0, int(round(int(price_1kg) * grams / 1000.0)))


def _normalize_product_key(name: str) -> str:
    return (
        (name or "")
        .casefold()
        .replace("‘", "'")
        .replace("’", "'")
        .replace(" ", "")
        .replace("-", "")
        .replace("_", "")
    )


def _weight_family_stem(name: str) -> str | None:
    """«Guruch 1kg» / «Shakar 500g» → «guruch» / «shakar». Litr/dona → None."""
    import re

    n = (name or "").casefold()
    if not re.search(r"\d+(?:[.,]\d+)?\s*(kg|g|gr|gramm)\b", n):
        return None
    base = re.sub(r"\d+(?:[.,]\d+)?\s*(kg|g|gr|gramm)\b", " ", n)
    base = re.sub(r"[-_/]+", " ", base)
    base = re.sub(r"\s+", " ", base).strip()
    return base or None


def _pack_grams_from_name(name: str) -> int | None:
    """«Guruch 250g» → 250; «Guruch 1kg» → 1000."""
    import re

    n = (name or "").casefold().replace("gramm", "g").replace("грамм", "g")
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*(kg|g|gr)\b", n)
    if not m:
        return None
    size = float(m.group(1).replace(",", "."))
    unit = m.group(2)
    if unit == "kg":
        return int(round(size * 1000))
    return int(round(size))


def _sync_weight_pack_prices(conn: sqlite3.Connection, *, stem: str) -> None:
    """Bitta oila: 1kg narxidan 250g/500g (va boshqa g) proporsional."""
    rows = conn.execute(
        "SELECT id, name, price FROM products WHERE is_active = 1 AND lower(name) LIKE ?",
        (f"%{stem}%",),
    ).fetchall()
    if not rows:
        return
    # Faqat shu stem oilasiga tegishli og‘irlik mahsulotlari
    family = []
    for r in rows:
        fam = _weight_family_stem(str(r["name"]))
        if fam == stem.casefold().strip():
            family.append(r)
    if not family:
        return
    kg_row = None
    for r in family:
        grams = _pack_grams_from_name(str(r["name"]))
        if grams == 1000:
            kg_row = r
            break
    if not kg_row:
        return
    price_1kg = int(kg_row["price"])
    for r in family:
        grams = _pack_grams_from_name(str(r["name"]))
        if not grams or grams == 1000:
            continue
        # Faqat 1kg dan kichik qadoqlar
        if grams >= 1000:
            continue
        new_price = _price_from_kg(price_1kg, grams)
        if int(r["price"]) != new_price:
            conn.execute(
                "UPDATE products SET price = ? WHERE id = ?",
                (new_price, int(r["id"])),
            )


def _sync_all_weight_pack_prices(conn: sqlite3.Connection) -> None:
    """Katalogdagi barcha *1kg oilalar uchun 250g/500g narxlarini sync."""
    rows = conn.execute(
        "SELECT id, name, price FROM products WHERE is_active = 1"
    ).fetchall()
    stems: set[str] = set()
    for r in rows:
        grams = _pack_grams_from_name(str(r["name"]))
        if grams != 1000:
            continue
        stem = _weight_family_stem(str(r["name"]))
        if stem:
            stems.add(stem)
    for stem in sorted(stems):
        _ensure_weight_packs_for_stem(conn, stem)
        _sync_weight_pack_prices(conn, stem=stem)


def _ensure_weight_packs_for_stem(conn: sqlite3.Connection, stem: str) -> None:
    """1kg bor bo‘lsa — 250g va 500g yo‘q bo‘lsa qo‘shadi (narx 1kg dan)."""
    rows = conn.execute(
        "SELECT id, name, price, description, category FROM products "
        "WHERE is_active = 1 AND lower(name) LIKE ?",
        (f"%{stem}%",),
    ).fetchall()
    kg_row = None
    existing_grams: set[int] = set()
    for r in rows:
        fam = _weight_family_stem(str(r["name"]))
        if fam != stem.casefold().strip():
            continue
        grams = _pack_grams_from_name(str(r["name"]))
        if grams is None:
            continue
        existing_grams.add(grams)
        if grams == 1000:
            kg_row = r
    if not kg_row:
        return
    price_1kg = int(kg_row["price"])
    cat = str(kg_row["category"] or "Oziq-ovqat")
    desc_base = str(kg_row["description"] or stem.title())
    display = stem[:1].upper() + stem[1:] if stem else "Mahsulot"
    # Title-case oddiy: guruch → Guruch
    for grams, label in ((250, "250g"), (500, "500g")):
        if grams in existing_grams:
            continue
        name = f"{display} {label}"
        conn.execute(
            """
            INSERT INTO products (name, price, description, category, is_active, created_at)
            VALUES (?, ?, ?, ?, 1, ?)
            """,
            (
                name,
                _price_from_kg(price_1kg, grams),
                f"{desc_base} — {grams} gramm",
                cat,
                _now(),
            ),
        )


def _ensure_size_variants(conn: sqlite3.Connection) -> None:
    """Guruch/shakar/sut/cola uchun barcha hajmlar bo‘lsin (250g, 500g, 1kg, …)."""
    # Og‘irlik: faqat 1kg seed; 250g/500g sync orqali 1kg dan hisoblanadi
    families = [
        (
            "guruch",
            [
                ("Guruch 1kg", 18000, "Oq guruch — 1 kilogram", "Oziq-ovqat"),
            ],
        ),
        (
            "shakar",
            [
                ("Shakar 1kg", 15000, "Oq shakar — 1 kilogram", "Oziq-ovqat"),
            ],
        ),
        (
            "sut",
            [
                ("Sut 0.5L", 7000, "Pastörizatsiya qilingan — 0.5 litr", "Ichimliklar"),
                ("Sut 1L", 12000, "Pastörizatsiya qilingan — 1 litr", "Ichimliklar"),
            ],
        ),
        (
            "cola",
            [
                ("Coca Cola 0.5L", 8000, "Gazli ichimlik — 0.5 litr", "Ichimliklar"),
                ("Coca-Cola 1.5L", 14000, "Gazli ichimlik — 1.5 litr", "Ichimliklar"),
                ("Coca Cola 2L", 18000, "Gazli ichimlik — 2 litr", "Ichimliklar"),
            ],
        ),
    ]
    for stem, variants in families:
        existing = {
            str(r["name"]).casefold()
            for r in conn.execute(
                "SELECT name FROM products WHERE is_active = 1 AND lower(name) LIKE ?",
                (f"%{stem}%",),
            ).fetchall()
        }
        for name, price, desc, cat in variants:
            if name.casefold() in existing:
                continue
            conn.execute(
                """
                INSERT INTO products (name, price, description, category, is_active, created_at)
                VALUES (?, ?, ?, ?, 1, ?)
                """,
                (name, price, desc, cat, _now()),
            )


def _migrate_cart_table(conn: sqlite3.Connection) -> None:
    """Savat: id PK + so‘mlik (custom) qatorlar uchun ustunlar."""
    cols = {r[1] for r in conn.execute("PRAGMA table_info(cart)").fetchall()}
    if "id" in cols and "custom_price" in cols:
        return
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS cart_v2 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 1,
            custom_price INTEGER,
            custom_label TEXT NOT NULL DEFAULT '',
            grams INTEGER NOT NULL DEFAULT 0
        );
        """
    )
    if cols:
        # eski savatni ko‘chirish
        has_custom = "custom_price" in cols
        if has_custom:
            conn.execute(
                """
                INSERT INTO cart_v2 (user_id, product_id, quantity, custom_price, custom_label, grams)
                SELECT user_id, product_id, quantity,
                       custom_price, COALESCE(custom_label, ''), COALESCE(grams, 0)
                FROM cart
                """
            )
        else:
            conn.execute(
                """
                INSERT INTO cart_v2 (user_id, product_id, quantity, custom_price, custom_label, grams)
                SELECT user_id, product_id, quantity, NULL, '', 0 FROM cart
                """
            )
        conn.execute("DROP TABLE cart")
    conn.execute("ALTER TABLE cart_v2 RENAME TO cart")
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_cart_user ON cart(user_id)"
    )


def list_products(active_only: bool = True) -> list[sqlite3.Row]:
    with get_connection() as conn:
        if active_only:
            rows = conn.execute(
                """
                SELECT * FROM products WHERE is_active = 1
                ORDER BY category, name COLLATE NOCASE
                """
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM products ORDER BY id DESC"
            ).fetchall()
    return list(rows)


def get_product(product_id: int) -> sqlite3.Row | None:
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM products WHERE id = ?", (product_id,)
        ).fetchone()


def search_products(query: str, limit: int = 8) -> list[sqlite3.Row]:
    q = f"%{(query or '').strip()}%"
    if q == "%%":
        return list_products()[:limit]
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM products
            WHERE is_active = 1
              AND (
                name LIKE ? COLLATE NOCASE
                OR description LIKE ? COLLATE NOCASE
                OR category LIKE ? COLLATE NOCASE
              )
            ORDER BY name COLLATE NOCASE
            LIMIT ?
            """,
            (q, q, q, limit),
        ).fetchall()
    return list(rows)


def add_product(
    name: str,
    price: int,
    description: str = "",
    category: str = "Umumiy",
    image_file_id: str | None = None,
) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO products (
                name, price, description, category, is_active, created_at, image_file_id
            )
            VALUES (?, ?, ?, ?, 1, ?, ?)
            """,
            (
                name.strip(),
                int(price),
                description.strip(),
                category.strip() or "Umumiy",
                _now(),
                image_file_id,
            ),
        )
        pid = int(cur.lastrowid)
        # kg li mahsulot: 250g/500g yarating yoki narxini sync qiling
        stem = _weight_family_stem(name)
        if stem and _pack_grams_from_name(name) is not None:
            _ensure_weight_packs_for_stem(conn, stem)
            _sync_weight_pack_prices(conn, stem=stem)
        return pid


def set_product_image(product_id: int, file_id: str) -> bool:
    with get_connection() as conn:
        cur = conn.execute(
            "UPDATE products SET image_file_id = ? WHERE id = ?",
            (file_id, int(product_id)),
        )
        return cur.rowcount > 0


def set_product_price(product_id: int, price: int) -> bool:
    with get_connection() as conn:
        cur = conn.execute(
            "UPDATE products SET price = ? WHERE id = ?",
            (max(0, int(price)), int(product_id)),
        )
        ok = cur.rowcount > 0
        if ok:
            row = conn.execute(
                "SELECT name FROM products WHERE id = ?", (int(product_id),)
            ).fetchone()
            if row:
                stem = _weight_family_stem(str(row["name"]))
                grams = _pack_grams_from_name(str(row["name"]))
                # 1kg (yoki oiladagi istalgan og‘irlik) yangilansa — g qadoqlar sync
                if stem and grams is not None:
                    if grams == 1000:
                        _ensure_weight_packs_for_stem(conn, stem)
                    _sync_weight_pack_prices(conn, stem=stem)
        return ok


def set_product_active(product_id: int, active: bool) -> bool:
    with get_connection() as conn:
        cur = conn.execute(
            "UPDATE products SET is_active = ? WHERE id = ?",
            (1 if active else 0, int(product_id)),
        )
        return cur.rowcount > 0


def set_product_name(product_id: int, name: str) -> bool:
    name = (name or "").strip()
    if len(name) < 2:
        return False
    with get_connection() as conn:
        cur = conn.execute(
            "UPDATE products SET name = ? WHERE id = ?",
            (name, int(product_id)),
        )
        ok = cur.rowcount > 0
        if ok:
            stem = _weight_family_stem(name)
            if stem and _pack_grams_from_name(name) is not None:
                _ensure_weight_packs_for_stem(conn, stem)
                _sync_weight_pack_prices(conn, stem=stem)
        return ok


def set_product_category(product_id: int, category: str) -> bool:
    category = (category or "").strip() or "Umumiy"
    with get_connection() as conn:
        cur = conn.execute(
            "UPDATE products SET category = ? WHERE id = ?",
            (category, int(product_id)),
        )
        return cur.rowcount > 0


def set_product_description(product_id: int, description: str) -> bool:
    with get_connection() as conn:
        cur = conn.execute(
            "UPDATE products SET description = ? WHERE id = ?",
            ((description or "").strip(), int(product_id)),
        )
        return cur.rowcount > 0


def update_product(
    product_id: int,
    *,
    name: str | None = None,
    price: int | None = None,
    category: str | None = None,
    description: str | None = None,
    image_file_id: str | None = None,
    is_active: bool | None = None,
) -> bool:
    """Mahsulot maydonlarini yangilash. True = kamida bitta o‘zgarish."""
    product = get_product(product_id)
    if not product:
        return False
    changed = False
    if name is not None and name.strip() and name.strip() != product["name"]:
        changed = set_product_name(product_id, name) or changed
    if price is not None and int(price) != int(product["price"]):
        changed = set_product_price(product_id, int(price)) or changed
    if category is not None and category.strip() != str(product["category"] or ""):
        changed = set_product_category(product_id, category) or changed
    if description is not None and description != str(product["description"] or ""):
        changed = set_product_description(product_id, description) or changed
    if image_file_id is not None:
        changed = set_product_image(product_id, image_file_id) or changed
    if is_active is not None and bool(is_active) != bool(product["is_active"]):
        changed = set_product_active(product_id, bool(is_active)) or changed
    return changed


def list_categories() -> list[str]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT DISTINCT category FROM products
            WHERE is_active = 1
            ORDER BY category COLLATE NOCASE
            """
        ).fetchall()
    return [str(r["category"]) for r in rows if r["category"]]


def list_products_by_category(category: str) -> list[sqlite3.Row]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM products
            WHERE is_active = 1 AND category = ?
            ORDER BY name COLLATE NOCASE
            """,
            (category,),
        ).fetchall()
    return list(rows)


def cart_add(user_id: int, product_id: int, qty: int = 1) -> None:
    """Oddiy mahsulot (qadoq) — bir xil product_id qatoriga qo‘shiladi."""
    qty = max(1, int(qty))
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, quantity FROM cart
            WHERE user_id = ? AND product_id = ?
              AND custom_price IS NULL AND grams = 0
            """,
            (user_id, product_id),
        ).fetchone()
        if row:
            conn.execute(
                "UPDATE cart SET quantity = quantity + ? WHERE id = ?",
                (qty, int(row["id"])),
            )
        else:
            conn.execute(
                """
                INSERT INTO cart (user_id, product_id, quantity, custom_price, custom_label, grams)
                VALUES (?, ?, ?, NULL, '', 0)
                """,
                (user_id, product_id, qty),
            )


def cart_add_by_money(
    user_id: int,
    product_id: int,
    *,
    amount: int,
    grams: int,
    label: str,
) -> dict[str, Any]:
    """Kg mahsulotdan so‘mlik olish (masalan 5000 so‘mlik guruch)."""
    amount = max(100, int(amount))
    grams = max(1, int(grams))
    label = (label or "").strip() or f"#{product_id}"
    with get_connection() as conn:
        # Bir xil so‘mlik qator bo‘lsa — miqdorni oshirish emas, yangi qator
        # (har bir so‘rov alohida). Lekin bir xil amount+grams birlashtiramiz.
        row = conn.execute(
            """
            SELECT id, quantity FROM cart
            WHERE user_id = ? AND product_id = ?
              AND custom_price = ? AND grams = ?
            """,
            (user_id, product_id, amount, grams),
        ).fetchone()
        if row:
            conn.execute(
                "UPDATE cart SET quantity = quantity + 1 WHERE id = ?",
                (int(row["id"]),),
            )
            cid = int(row["id"])
            qty = int(row["quantity"]) + 1
        else:
            cur = conn.execute(
                """
                INSERT INTO cart (
                    user_id, product_id, quantity, custom_price, custom_label, grams
                ) VALUES (?, ?, 1, ?, ?, ?)
                """,
                (user_id, product_id, amount, label, grams),
            )
            cid = int(cur.lastrowid)
            qty = 1
    return {
        "cart_id": cid,
        "product_id": int(product_id),
        "name": label,
        "price": amount,
        "quantity": qty,
        "grams": grams,
        "line_total": amount * qty,
        "is_custom": True,
    }


def cart_set_qty(user_id: int, cart_id: int, qty: int) -> None:
    qty = int(qty)
    with get_connection() as conn:
        if qty <= 0:
            conn.execute(
                "DELETE FROM cart WHERE user_id = ? AND id = ?",
                (user_id, int(cart_id)),
            )
            return
        conn.execute(
            "UPDATE cart SET quantity = ? WHERE user_id = ? AND id = ?",
            (qty, user_id, int(cart_id)),
        )


def cart_delta(user_id: int, cart_id: int, delta: int) -> int:
    """Miqdorni o‘zgartiradi (cart qator id); 0 = o‘chirilgan."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT quantity FROM cart WHERE user_id = ? AND id = ?",
            (user_id, int(cart_id)),
        ).fetchone()
        if not row:
            return 0
        cur = int(row["quantity"]) + int(delta)
    cart_set_qty(user_id, int(cart_id), cur)
    return max(0, cur)


def cart_clear(user_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))


def get_cart(user_id: int) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT c.id AS cart_id, c.product_id, c.quantity, c.custom_price,
                   c.custom_label, c.grams, p.name, p.price
            FROM cart c
            JOIN products p ON p.id = c.product_id
            WHERE c.user_id = ? AND p.is_active = 1
            ORDER BY c.id
            """,
            (user_id,),
        ).fetchall()
    items = []
    for r in rows:
        custom = r["custom_price"]
        grams = int(r["grams"] or 0)
        if custom is not None:
            unit_price = int(custom)
            name = str(r["custom_label"] or r["name"])
            is_custom = True
        else:
            unit_price = int(r["price"])
            name = str(r["name"])
            is_custom = False
        qty = int(r["quantity"])
        items.append(
            {
                "cart_id": int(r["cart_id"]),
                "product_id": int(r["product_id"]),
                "name": name,
                "price": unit_price,
                "quantity": qty,
                "grams": grams,
                "line_total": unit_price * qty,
                "is_custom": is_custom,
            }
        )
    return items


def cart_total(user_id: int) -> int:
    return sum(i["line_total"] for i in get_cart(user_id))


def find_kg_product(stem_query: str):
    """Oila ichidan 1kg mahsulotni topadi."""
    rows = list_products(active_only=True)
    q = (stem_query or "").casefold().strip()
    best = None
    for p in rows:
        name = str(p["name"])
        grams = _pack_grams_from_name(name)
        if grams != 1000:
            continue
        stem = _weight_family_stem(name)
        if not stem:
            continue
        if q in stem or stem in q or q in name.casefold():
            best = p
            break
    if best:
        return best
    # find_variants orqali
    return None


def grams_for_money(price_1kg: int, amount: int) -> int:
    """1kg narxidan so‘m bo‘yicha gramm."""
    if price_1kg <= 0:
        return 0
    return max(1, int(round(int(amount) * 1000.0 / int(price_1kg))))


def create_order(
    user_id: int,
    *,
    customer_name: str,
    phone: str,
    address: str,
    note: str = "",
    delivery_fee: int = 0,
) -> int:
    import json

    items = get_cart(user_id)
    subtotal = sum(i["line_total"] for i in items)
    delivery = max(0, int(delivery_fee))
    total = subtotal + delivery
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO orders (
                user_id, customer_name, phone, address, items_json,
                total, note, status, created_at, delivery_fee, subtotal
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'new', ?, ?, ?)
            """,
            (
                user_id,
                customer_name.strip(),
                phone.strip(),
                address.strip(),
                json.dumps(items, ensure_ascii=False),
                total,
                note.strip(),
                _now(),
                delivery,
                subtotal,
            ),
        )
        order_id = int(cur.lastrowid)
    cart_clear(user_id)
    return order_id


def fill_cart_from_order(user_id: int, order_id: int) -> int:
    """Buyurtmadagi mahsulotlarni savatga qayta yuklaydi. Qo‘shilgan qatorlar soni."""
    import json

    order = get_order(order_id)
    if not order or int(order["user_id"]) != int(user_id):
        return 0
    try:
        items = json.loads(order["items_json"] or "[]")
    except json.JSONDecodeError:
        return 0
    cart_clear(user_id)
    added = 0
    for it in items:
        try:
            pid = int(it.get("product_id") or 0)
            qty = int(it.get("quantity") or 0)
        except (TypeError, ValueError):
            continue
        product = get_product(pid)
        if not product or not product["is_active"] or qty <= 0:
            continue
        if it.get("is_custom") or it.get("custom_price") is not None or it.get("grams"):
            amount = int(it.get("price") or it.get("custom_price") or 0)
            grams = int(it.get("grams") or 0)
            label = str(it.get("name") or product["name"])
            if amount > 0 and grams > 0:
                for _ in range(qty):
                    cart_add_by_money(
                        user_id, pid, amount=amount, grams=grams, label=label
                    )
                added += 1
                continue
        cart_add(user_id, pid, qty)
        added += 1
    return added


def list_customer_ids(limit: int = 500) -> list[int]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT DISTINCT user_id FROM orders
            ORDER BY user_id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [int(r["user_id"]) for r in rows]


def get_order(order_id: int) -> sqlite3.Row | None:
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM orders WHERE id = ?", (order_id,)
        ).fetchone()


def set_order_status(order_id: int, status: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE orders SET status = ? WHERE id = ?",
            (status, order_id),
        )


def list_new_orders(limit: int = 20) -> list[sqlite3.Row]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM orders
            WHERE status = 'new'
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return list(rows)


def list_orders_by_user(user_id: int, limit: int = 10) -> list[sqlite3.Row]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM orders
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
    return list(rows)


def list_orders(status: str | None = None, limit: int = 20) -> list[sqlite3.Row]:
    with get_connection() as conn:
        if status:
            rows = conn.execute(
                """
                SELECT * FROM orders WHERE status = ?
                ORDER BY id DESC LIMIT ?
                """,
                (status, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM orders ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
    return list(rows)


def admin_stats() -> dict[str, int]:
    with get_connection() as conn:
        products = conn.execute(
            "SELECT COUNT(*) AS c FROM products WHERE is_active = 1"
        ).fetchone()["c"]
        orders = conn.execute("SELECT COUNT(*) AS c FROM orders").fetchone()["c"]
        new = conn.execute(
            "SELECT COUNT(*) AS c FROM orders WHERE status = 'new'"
        ).fetchone()["c"]
        accepted = conn.execute(
            "SELECT COUNT(*) AS c FROM orders WHERE status = 'accepted'"
        ).fetchone()["c"]
        delivering = conn.execute(
            "SELECT COUNT(*) AS c FROM orders WHERE status = 'delivering'"
        ).fetchone()["c"]
        delivered = conn.execute(
            "SELECT COUNT(*) AS c FROM orders WHERE status = 'delivered'"
        ).fetchone()["c"]
        revenue = conn.execute(
            """
            SELECT COALESCE(SUM(total), 0) AS s FROM orders
            WHERE status IN ('accepted', 'delivering', 'delivered')
            """
        ).fetchone()["s"]
    return {
        "products": int(products or 0),
        "orders": int(orders or 0),
        "new": int(new or 0),
        "accepted": int(accepted or 0),
        "delivering": int(delivering or 0),
        "delivered": int(delivered or 0),
        "revenue": int(revenue or 0),
    }


def get_memory(user_id: int) -> list[dict[str, str]]:
    import json

    with get_connection() as conn:
        row = conn.execute(
            "SELECT history_json FROM chat_memory WHERE user_id = ?",
            (user_id,),
        ).fetchone()
    if not row:
        return []
    try:
        data = json.loads(row["history_json"] or "[]")
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def save_memory(user_id: int, history: list[dict[str, str]]) -> None:
    import json

    trimmed = history[-12:]
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO chat_memory (user_id, history_json, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                history_json = excluded.history_json,
                updated_at = excluded.updated_at
            """,
            (user_id, json.dumps(trimmed, ensure_ascii=False), _now()),
        )
