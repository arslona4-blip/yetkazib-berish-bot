import sqlite3
from contextlib import contextmanager
from datetime import timedelta
from typing import Any

from bot.config import DATABASE_PATH, DELIVERY_PRICE, ORDER_STATUS_LABELS, PAYMENT_STATUS_LABELS
from bot.timeutil import format_dt, money_html, now_tashkent


def _now_iso() -> str:
    return now_tashkent().isoformat()


DEFAULT_CATEGORIES = [
    ("Oziq-ovqat", "🛒"),
    ("Ichimliklar", "🥤"),
    ("Uy-ro'zg'or", "🏠"),
]

DEFAULT_PRODUCTS = [
    ("Non (1 dona)", 4000, "Yangilik non", "Oziq-ovqat"),
    ("Sut 1L", 12000, "Tabiiy sut", "Oziq-ovqat"),
    ("Tuxum (10 dona)", 18000, "Tovuq tuxumi", "Oziq-ovqat"),
    ("Guruch 1kg", 16000, "Oq guruch", "Oziq-ovqat"),
    ("Yog' 1L", 22000, "O'simlik yog'i", "Oziq-ovqat"),
    ("Shakar 1kg", 14000, "Oq shakar", "Oziq-ovqat"),
    ("Choy 100g", 25000, "Qora choy", "Oziq-ovqat"),
    ("Makaron 400g", 9000, "Spaghetti", "Oziq-ovqat"),
    ("Cola 1.5L", 13000, "Ichimlik", "Ichimliklar"),
    ("Suv 1.5L", 5000, "Ichiladigan suv", "Ichimliklar"),
]


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT NOT NULL,
                phone TEXT,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                pickup_address TEXT NOT NULL,
                delivery_address TEXT NOT NULL,
                latitude REAL,
                longitude REAL,
                description TEXT,
                phone TEXT NOT NULL,
                price INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'new',
                payment_status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            );

            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                is_active INTEGER NOT NULL DEFAULT 1,
                emoji TEXT NOT NULL DEFAULT '📦'
            );

            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price INTEGER NOT NULL,
                description TEXT,
                category_id INTEGER,
                is_active INTEGER NOT NULL DEFAULT 1,
                FOREIGN KEY (category_id) REFERENCES categories (id)
            );

            CREATE TABLE IF NOT EXISTS product_variants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                price INTEGER NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                FOREIGN KEY (product_id) REFERENCES products (id)
            );

            CREATE TABLE IF NOT EXISTS cart_items (
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                variant_id INTEGER NOT NULL DEFAULT 0,
                quantity INTEGER NOT NULL DEFAULT 1,
                PRIMARY KEY (user_id, product_id, variant_id),
                FOREIGN KEY (product_id) REFERENCES products (id)
            );

            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER,
                product_name TEXT NOT NULL,
                price INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders (id)
            );
            """
        )
        order_columns = {
            row[1] for row in conn.execute("PRAGMA table_info(orders)").fetchall()
        }
        if "latitude" not in order_columns:
            conn.execute("ALTER TABLE orders ADD COLUMN latitude REAL")
        if "longitude" not in order_columns:
            conn.execute("ALTER TABLE orders ADD COLUMN longitude REAL")

        product_columns = {
            row[1] for row in conn.execute("PRAGMA table_info(products)").fetchall()
        }
        if "category_id" not in product_columns:
            conn.execute("ALTER TABLE products ADD COLUMN category_id INTEGER")

        cart_columns = {
            row[1] for row in conn.execute("PRAGMA table_info(cart_items)").fetchall()
        }
        if cart_columns and "variant_id" not in cart_columns:
            conn.executescript(
                """
                CREATE TABLE cart_items_new (
                    user_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    variant_id INTEGER NOT NULL DEFAULT 0,
                    quantity INTEGER NOT NULL DEFAULT 1,
                    PRIMARY KEY (user_id, product_id, variant_id)
                );
                INSERT INTO cart_items_new (user_id, product_id, variant_id, quantity)
                SELECT user_id, product_id, 0, quantity FROM cart_items;
                DROP TABLE cart_items;
                ALTER TABLE cart_items_new RENAME TO cart_items;
                """
            )

        cat_count = conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
        if cat_count == 0:
            conn.executemany(
                "INSERT INTO categories (name, emoji) VALUES (?, ?)",
                list(DEFAULT_CATEGORIES),
            )

        product_count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        if product_count == 0:
            for name, price, description, category_name in DEFAULT_PRODUCTS:
                category_id = conn.execute(
                    "SELECT id FROM categories WHERE name = ?",
                    (category_name,),
                ).fetchone()[0]
                conn.execute(
                    """
                    INSERT INTO products (name, price, description, category_id)
                    VALUES (?, ?, ?, ?)
                    """,
                    (name, price, description, category_id),
                )
        else:
            default_cat = conn.execute(
                "SELECT id FROM categories ORDER BY id LIMIT 1"
            ).fetchone()
            if default_cat:
                conn.execute(
                    """
                    UPDATE products
                    SET category_id = ?
                    WHERE category_id IS NULL
                    """,
                    (default_cat[0],),
                )

        _migrate_features(conn)


def _migrate_features(conn: sqlite3.Connection) -> None:
    user_cols = {r[1] for r in conn.execute("PRAGMA table_info(users)").fetchall()}
    if "bonus_points" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN bonus_points INTEGER NOT NULL DEFAULT 0")

    product_cols = {r[1] for r in conn.execute("PRAGMA table_info(products)").fetchall()}
    if "stock" not in product_cols:
        conn.execute("ALTER TABLE products ADD COLUMN stock INTEGER NOT NULL DEFAULT 100")
    # Ombor UI olib tashlangach stock=0 mahsulotlar katalogdan yo'qolgan edi —
    # faol va 0 qoldiqli mahsulotlarga boshlang'ich 100 beramiz.
    conn.execute(
        """
        UPDATE products
        SET stock = 100
        WHERE is_active = 1 AND COALESCE(stock, 0) <= 0
        """
    )
    if "image_file_id" not in product_cols:
        conn.execute("ALTER TABLE products ADD COLUMN image_file_id TEXT")
    if "barcode" not in product_cols:
        conn.execute("ALTER TABLE products ADD COLUMN barcode TEXT")

    cat_cols = {r[1] for r in conn.execute("PRAGMA table_info(categories)").fetchall()}
    if "emoji" not in cat_cols:
        conn.execute(
            "ALTER TABLE categories ADD COLUMN emoji TEXT NOT NULL DEFAULT '📦'"
        )
        from bot.category_emoji import parse_category_name

        rows = conn.execute("SELECT id, name FROM categories").fetchall()
        for row in rows:
            emoji, clean = parse_category_name(row["name"])
            clean_name = clean or row["name"]
            # Nomni tozalash (emoji alohida ustunda)
            try:
                conn.execute(
                    "UPDATE categories SET emoji = ?, name = ? WHERE id = ?",
                    (emoji, clean_name, int(row["id"])),
                )
            except sqlite3.IntegrityError:
                conn.execute(
                    "UPDATE categories SET emoji = ? WHERE id = ?",
                    (emoji, int(row["id"])),
                )

    conn.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_products_barcode
        ON products(barcode)
        WHERE barcode IS NOT NULL AND barcode != ''
        """
    )

    variant_cols = {
        r[1] for r in conn.execute("PRAGMA table_info(product_variants)").fetchall()
    }
    if "stock" not in variant_cols:
        conn.execute(
            "ALTER TABLE product_variants ADD COLUMN stock INTEGER NOT NULL DEFAULT 100"
        )

    order_cols = {r[1] for r in conn.execute("PRAGMA table_info(orders)").fetchall()}
    for col, sql_type in [
        ("delivery_slot", "TEXT"),
        ("promo_code", "TEXT"),
        ("discount", "INTEGER NOT NULL DEFAULT 0"),
        ("bonus_spent", "INTEGER NOT NULL DEFAULT 0"),
        ("subtotal", "INTEGER NOT NULL DEFAULT 0"),
    ]:
        if col not in order_cols:
            conn.execute(f"ALTER TABLE orders ADD COLUMN {col} {sql_type}")

    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS favorites (
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            PRIMARY KEY (user_id, product_id)
        );

        CREATE TABLE IF NOT EXISTS promo_codes (
            code TEXT PRIMARY KEY,
            discount_percent INTEGER NOT NULL DEFAULT 0,
            discount_amount INTEGER NOT NULL DEFAULT 0,
            min_order INTEGER NOT NULL DEFAULT 0,
            is_active INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS referrals (
            referred_user_id INTEGER PRIMARY KEY,
            referrer_user_id INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            rewarded INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            note TEXT,
            telegram_user_id INTEGER,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS debt_ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contact_id INTEGER NOT NULL,
            kind TEXT NOT NULL,
            amount INTEGER NOT NULL,
            order_id INTEGER,
            note TEXT,
            created_by INTEGER,
            created_at TEXT NOT NULL,
            FOREIGN KEY (contact_id) REFERENCES contacts (id)
        );
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_contacts_phone ON contacts(phone)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_debt_contact ON debt_ledger(contact_id)"
    )
    promo_count = conn.execute("SELECT COUNT(*) FROM promo_codes").fetchone()[0]
    if promo_count == 0:
        conn.execute(
            """
            INSERT INTO promo_codes (code, discount_percent, discount_amount, min_order, is_active)
            VALUES ('BARAKA10', 10, 0, 30000, 1)
            """
        )

    user_cols = {r[1] for r in conn.execute("PRAGMA table_info(users)").fetchall()}
    if "language" not in user_cols:
        conn.execute(
            "ALTER TABLE users ADD COLUMN language TEXT NOT NULL DEFAULT 'uz'"
        )

    cart_cols = {r[1] for r in conn.execute("PRAGMA table_info(cart_items)").fetchall()}
    if "custom_name" not in cart_cols:
        conn.execute("ALTER TABLE cart_items ADD COLUMN custom_name TEXT")
    if "grams" not in cart_cols:
        conn.execute("ALTER TABLE cart_items ADD COLUMN grams INTEGER")

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS ai_memory (
            user_id INTEGER PRIMARY KEY,
            history_json TEXT NOT NULL DEFAULT '[]',
            updated_at TEXT NOT NULL
        )
        """
    )

    product_cols = {r[1] for r in conn.execute("PRAGMA table_info(products)").fetchall()}
    if "sale_price" not in product_cols:
        conn.execute("ALTER TABLE products ADD COLUMN sale_price INTEGER")
    if "sale_until" not in product_cols:
        conn.execute("ALTER TABLE products ADD COLUMN sale_until TEXT")

    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS order_reviews (
            order_id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            rating INTEGER NOT NULL,
            comment TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders (id)
        );

        CREATE TABLE IF NOT EXISTS delivery_zones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            keywords TEXT,
            price INTEGER NOT NULL,
            is_active INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS recurring_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            source_order_id INTEGER,
            interval_days INTEGER NOT NULL DEFAULT 7,
            next_run TEXT NOT NULL,
            phone TEXT,
            address TEXT,
            slot TEXT,
            note TEXT,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS shajara_shares (
            code TEXT PRIMARY KEY,
            payload TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS stock_movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            delta INTEGER NOT NULL,
            stock_after INTEGER NOT NULL,
            reason TEXT NOT NULL,
            note TEXT,
            order_id INTEGER,
            admin_id INTEGER,
            created_at TEXT NOT NULL,
            FOREIGN KEY (product_id) REFERENCES products (id)
        );

        CREATE TABLE IF NOT EXISTS admin_login_codes (
            admin_id INTEGER PRIMARY KEY,
            code TEXT NOT NULL,
            expires_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS admin_sessions (
            token TEXT PRIMARY KEY,
            admin_id INTEGER NOT NULL,
            expires_at TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_stock_movements_product "
        "ON stock_movements(product_id, created_at)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_stock_movements_created "
        "ON stock_movements(created_at)"
    )
    zone_count = conn.execute("SELECT COUNT(*) FROM delivery_zones").fetchone()[0]
    if zone_count == 0:
        conn.execute(
            """
            INSERT INTO delivery_zones (name, keywords, price, is_active)
            VALUES ('Standart', '', ?, 1)
            """,
            (DELIVERY_PRICE,),
        )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS push_subscriptions (
            endpoint TEXT PRIMARY KEY,
            admin_id INTEGER NOT NULL,
            p256dh TEXT NOT NULL,
            auth TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )


@contextmanager
def get_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def upsert_user(user_id: int, full_name: str, username: str | None = None) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO users (user_id, username, full_name, created_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                full_name = excluded.full_name
            """,
            (user_id, username, full_name, _now_iso()),
        )


def set_user_phone(user_id: int, phone: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE users SET phone = ? WHERE user_id = ?",
            (phone, user_id),
        )


def get_user(user_id: int) -> sqlite3.Row | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE user_id = ?",
            (user_id,),
        ).fetchone()
    return row


def get_categories(active_only: bool = True) -> list[sqlite3.Row]:
    with get_connection() as conn:
        if active_only:
            rows = conn.execute(
                "SELECT * FROM categories WHERE is_active = 1 ORDER BY id"
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM categories ORDER BY id").fetchall()
    return list(rows)


def get_category(category_id: int) -> sqlite3.Row | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM categories WHERE id = ?",
            (category_id,),
        ).fetchone()
    return row


def create_category(name: str, emoji: str | None = None) -> int:
    from bot.category_emoji import parse_category_name

    parsed_emoji, clean_name = parse_category_name(name)
    icon = (emoji or "").strip() or parsed_emoji
    if not clean_name:
        raise ValueError("Toifa nomi kerak")
    with get_connection() as conn:
        existing = conn.execute(
            "SELECT id FROM categories WHERE name = ?",
            (clean_name,),
        ).fetchone()
        if existing:
            conn.execute(
                "UPDATE categories SET is_active = 1, emoji = ? WHERE id = ?",
                (icon, existing["id"]),
            )
            return int(existing["id"])
        cursor = conn.execute(
            "INSERT INTO categories (name, is_active, emoji) VALUES (?, 1, ?)",
            (clean_name, icon),
        )
        return int(cursor.lastrowid)


def update_category(category_id: int, name: str, emoji: str | None = None) -> None:
    """Toifa nomini (va ixtiyoriy emoji) yangilash."""
    from bot.category_emoji import parse_category_name

    parsed_emoji, clean_name = parse_category_name(name)
    if not clean_name:
        raise ValueError("Toifa nomi kerak")
    icon = (emoji or "").strip() or parsed_emoji
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id FROM categories WHERE id = ?",
            (int(category_id),),
        ).fetchone()
        if not row:
            raise ValueError("Toifa topilmadi")
        clash = conn.execute(
            "SELECT id FROM categories WHERE name = ? AND id != ?",
            (clean_name, int(category_id)),
        ).fetchone()
        if clash:
            raise ValueError("Bunday toifa nomi allaqachon bor")
        conn.execute(
            "UPDATE categories SET name = ?, emoji = ?, is_active = 1 WHERE id = ?",
            (clean_name, icon, int(category_id)),
        )


def set_category_emoji(category_id: int, emoji: str) -> None:
    icon = (emoji or "").strip() or "📦"
    with get_connection() as conn:
        conn.execute(
            "UPDATE categories SET emoji = ? WHERE id = ?",
            (icon, int(category_id)),
        )


def delete_category(category_id: int) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE products SET category_id = NULL WHERE category_id = ?",
            (category_id,),
        )
        conn.execute("DELETE FROM categories WHERE id = ?", (category_id,))


def get_products(active_only: bool = True, category_id: int | None = None) -> list[sqlite3.Row]:
    with get_connection() as conn:
        query = """
            SELECT p.*, c.name AS category_name, c.emoji AS category_emoji
            FROM products p
            LEFT JOIN categories c ON c.id = p.category_id
            WHERE 1=1
        """
        params: list[Any] = []
        if active_only:
            # Ombor yo'q: katalogda faqat faol mahsulotlar (stock=0 ham ko'rinadi)
            query += " AND p.is_active = 1"
        if category_id is not None:
            query += " AND p.category_id = ?"
            params.append(category_id)
        query += """
            ORDER BY
                CASE WHEN p.category_id IS NULL THEN 1 ELSE 0 END,
                c.id,
                p.name COLLATE NOCASE,
                p.id
        """
        rows = conn.execute(query, params).fetchall()
    return list(rows)


def get_product(product_id: int) -> sqlite3.Row | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT p.*, c.name AS category_name
            FROM products p
            LEFT JOIN categories c ON c.id = p.category_id
            WHERE p.id = ? AND p.is_active = 1
            """,
            (product_id,),
        ).fetchone()
    return row


def get_product_by_id(product_id: int) -> sqlite3.Row | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT p.*, c.name AS category_name
            FROM products p
            LEFT JOIN categories c ON c.id = p.category_id
            WHERE p.id = ?
            """,
            (product_id,),
        ).fetchone()
    return row


def create_product(
    name: str,
    price: int,
    description: str = "",
    category_id: int | None = None,
    barcode: str | None = None,
    stock: int | None = 100,
) -> int:
    code = (barcode or "").strip() or None
    initial_stock = max(0, int(stock if stock is not None else 100))
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO products (
                name, price, description, category_id, is_active, barcode, stock
            )
            VALUES (?, ?, ?, ?, 1, ?, ?)
            """,
            (name, price, description, category_id, code, initial_stock),
        )
        product_id = int(cursor.lastrowid)
        if initial_stock:
            conn.execute(
                """
                INSERT INTO stock_movements (
                    product_id, delta, stock_after, reason, note,
                    order_id, admin_id, created_at
                )
                VALUES (?, ?, ?, ?, ?, NULL, NULL, ?)
                """,
                (
                    product_id,
                    initial_stock,
                    initial_stock,
                    "in",
                    "Yangi mahsulot",
                    _now_iso(),
                ),
            )
        return product_id


def get_product_by_barcode(barcode: str) -> sqlite3.Row | None:
    code = (barcode or "").strip()
    if not code:
        return None
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT p.*, c.name AS category_name
            FROM products p
            LEFT JOIN categories c ON c.id = p.category_id
            WHERE p.barcode = ? AND p.is_active = 1
            """,
            (code,),
        ).fetchone()
    return row


def set_product_barcode(product_id: int, barcode: str | None) -> None:
    code = (barcode or "").strip() or None
    if code in {"0", "-", "none", "yo'q", "yoq"}:
        code = None
    with get_connection() as conn:
        if code:
            other = conn.execute(
                "SELECT id, name FROM products WHERE barcode = ? AND id != ?",
                (code, product_id),
            ).fetchone()
            if other:
                raise ValueError(
                    f"Kod boshqa mahsulotda: #{other['id']} {other['name']}"
                )
        conn.execute(
            "UPDATE products SET barcode = ? WHERE id = ?",
            (code, product_id),
        )


def update_product_price(product_id: int, price: int) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE products SET price = ? WHERE id = ?",
            (price, product_id),
        )


def update_product_name(product_id: int, name: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE products SET name = ? WHERE id = ?",
            (name, product_id),
        )


def set_product_active(product_id: int, is_active: bool) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE products SET is_active = ? WHERE id = ?",
            (1 if is_active else 0, product_id),
        )


def delete_product(product_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM cart_items WHERE product_id = ?", (product_id,))
        conn.execute("DELETE FROM product_variants WHERE product_id = ?", (product_id,))
        conn.execute("DELETE FROM products WHERE id = ?", (product_id,))


def get_variants(product_id: int, active_only: bool = True) -> list[sqlite3.Row]:
    with get_connection() as conn:
        if active_only:
            rows = conn.execute(
                """
                SELECT * FROM product_variants
                WHERE product_id = ? AND is_active = 1
                ORDER BY price, id
                """,
                (product_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT * FROM product_variants
                WHERE product_id = ?
                ORDER BY price, id
                """,
                (product_id,),
            ).fetchall()
    return list(rows)


def get_variant(variant_id: int) -> sqlite3.Row | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT v.*, p.name AS product_name, p.category_id, p.is_active AS product_active
            FROM product_variants v
            JOIN products p ON p.id = v.product_id
            WHERE v.id = ? AND v.is_active = 1 AND p.is_active = 1
            """,
            (variant_id,),
        ).fetchone()
    return row


def create_variant(product_id: int, name: str, price: int) -> int:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO product_variants (product_id, name, price, is_active)
            VALUES (?, ?, ?, 1)
            """,
            (product_id, name, price),
        )
        return int(cursor.lastrowid)


def delete_variant(variant_id: int) -> None:
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM cart_items WHERE variant_id = ?",
            (variant_id,),
        )
        conn.execute("DELETE FROM product_variants WHERE id = ?", (variant_id,))


def product_display_price(product: sqlite3.Row) -> str:
    variants = get_variants(product["id"])
    if not variants:
        base = int(product["price"] or 0)
        effective = effective_product_price(product)
        if effective < base:
            return f"🔥 {effective:,} so'm (~~{base:,}~~)"
        return f"{base:,} so'm"
    prices = [v["price"] for v in variants]
    low, high = min(prices), max(prices)
    if low == high:
        return f"{low:,} so'm"
    return f"{low:,} – {high:,} so'm"


def effective_product_price(product) -> int:
    try:
        base = int(product["price"] or 0)
    except (KeyError, IndexError, TypeError):
        return 0
    try:
        sale_price = product["sale_price"]
        sale_until = product["sale_until"]
    except (KeyError, IndexError, TypeError):
        return base
    if sale_price is None:
        return base
    try:
        sale_price = int(sale_price)
    except (TypeError, ValueError):
        return base
    if sale_price <= 0:
        return base
    today = now_tashkent().strftime("%Y-%m-%d")
    until = str(sale_until or "").strip()[:10]
    if until and until >= today:
        return sale_price
    return base


def set_product_sale(
    product_id: int, sale_price: int | None, sale_until: str | None
) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE products
            SET sale_price = ?, sale_until = ?
            WHERE id = ?
            """,
            (sale_price, sale_until, product_id),
        )


def add_to_cart(
    user_id: int,
    product_id: int,
    quantity: int = 1,
    variant_id: int = 0,
) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO cart_items (user_id, product_id, variant_id, quantity)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, product_id, variant_id) DO UPDATE SET
                quantity = cart_items.quantity + excluded.quantity
            """,
            (user_id, product_id, variant_id, quantity),
        )


def add_money_to_cart(
    user_id: int,
    product_id: int,
    *,
    amount: int,
    grams: int,
    label: str,
    quantity: int = 1,
) -> None:
    """Kg mahsulotdan so‘mlik (variant_id = -amount)."""
    amount = max(100, int(amount))
    grams = max(1, int(grams))
    label = (label or "").strip() or f"#{product_id}"
    variant_id = -amount
    add_to_cart(user_id, product_id, max(1, int(quantity)), variant_id)
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE cart_items
            SET custom_name = ?, grams = ?
            WHERE user_id = ? AND product_id = ? AND variant_id = ?
            """,
            (label, grams, user_id, product_id, variant_id),
        )


def get_ai_memory(user_id: int) -> list[dict[str, Any]]:
    import json

    with get_connection() as conn:
        row = conn.execute(
            "SELECT history_json FROM ai_memory WHERE user_id = ?",
            (user_id,),
        ).fetchone()
    if not row:
        return []
    try:
        data = json.loads(row["history_json"] or "[]")
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else []


def save_ai_memory(user_id: int, history: list[dict[str, Any]]) -> None:
    import json

    payload = json.dumps(history[-16:], ensure_ascii=False)
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO ai_memory (user_id, history_json, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                history_json = excluded.history_json,
                updated_at = excluded.updated_at
            """,
            (user_id, payload, _now_iso()),
        )


def set_cart_quantity(
    user_id: int,
    product_id: int,
    quantity: int,
    variant_id: int = 0,
) -> None:
    with get_connection() as conn:
        if quantity <= 0:
            conn.execute(
                """
                DELETE FROM cart_items
                WHERE user_id = ? AND product_id = ? AND variant_id = ?
                """,
                (user_id, product_id, variant_id),
            )
        else:
            conn.execute(
                """
                INSERT INTO cart_items (user_id, product_id, variant_id, quantity)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id, product_id, variant_id) DO UPDATE SET
                    quantity = excluded.quantity
                """,
                (user_id, product_id, variant_id, quantity),
            )


def remove_from_cart(
    user_id: int, product_id: int, variant_id: int = 0
) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            DELETE FROM cart_items
            WHERE user_id = ? AND product_id = ? AND variant_id = ?
            """,
            (user_id, product_id, variant_id),
        )


def clear_cart(user_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM cart_items WHERE user_id = ?", (user_id,))


def get_cart(user_id: int) -> list[sqlite3.Row]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                c.product_id,
                c.variant_id,
                c.quantity,
                p.name AS product_name,
                p.description,
                CASE
                    WHEN c.variant_id < 0 THEN COALESCE(NULLIF(c.custom_name, ''), p.name)
                    WHEN c.variant_id > 0 THEN v.name
                    ELSE NULL
                END AS variant_name,
                CASE
                    WHEN c.variant_id < 0 THEN abs(c.variant_id)
                    WHEN c.variant_id > 0 THEN v.price
                    WHEN p.sale_price IS NOT NULL
                         AND p.sale_price > 0
                         AND p.sale_until IS NOT NULL
                         AND date(p.sale_until) >= date('now', 'localtime')
                    THEN p.sale_price
                    ELSE p.price
                END AS price,
                CASE
                    WHEN c.variant_id < 0 THEN COALESCE(NULLIF(c.custom_name, ''), p.name)
                    WHEN c.variant_id > 0 THEN p.name || ' (' || v.name || ')'
                    ELSE p.name
                END AS name
            FROM cart_items c
            JOIN products p ON p.id = c.product_id
            LEFT JOIN product_variants v ON v.id = c.variant_id
            WHERE c.user_id = ?
              AND p.is_active = 1
              AND (c.variant_id <= 0 OR v.is_active = 1)
            ORDER BY name
            """,
            (user_id,),
        ).fetchall()
    return list(rows)


def get_cart_totals(user_id: int) -> tuple[int, int]:
    items = get_cart(user_id)
    count = sum(item["quantity"] for item in items)
    subtotal = sum(item["price"] * item["quantity"] for item in items)
    return count, subtotal


def format_cart(user_id: int) -> str:
    from bot.timeutil import money_html

    items = get_cart(user_id)
    if not items:
        from bot.config import delivery_rates_html, gift_drink_promo_html

        return (
            "🛒 Savatchangiz bo'sh\n\n"
            "🛍 Katalogdan mahsulot tanlang — bir bosishda qo'shiladi!\n\n"
            f"{delivery_rates_html()}\n\n"
            f"{gift_drink_promo_html()}"
        )

    lines = ["🛒 <b>Sizning savatchangiz</b>", "┄┄┄┄┄┄┄┄┄┄┄┄"]
    for i, item in enumerate(items, 1):
        line_total = item["price"] * item["quantity"]
        lines.append(
            f"{i}. {item['name']}\n"
            f"   {item['quantity']} × {item['price']:,} = "
            f"{money_html(line_total, with_emoji=False)}"
        )
    _, subtotal = get_cart_totals(user_id)
    delivery_fee, _ = get_delivery_fee(subtotal=subtotal)
    total = subtotal + delivery_fee
    lines.append("┄┄┄┄┄┄┄┄┄┄┄┄")
    lines.append(f"🛍 Mahsulotlar: {money_html(subtotal, with_emoji=False)}")
    lines.append(f"🚚 Yetkazish: {money_html(delivery_fee, with_emoji=False)}")
    from bot.config import delivery_rates_html, gift_drink_progress_html, gift_drink_promo_html

    lines.append(delivery_rates_html())
    lines.append(gift_drink_progress_html(subtotal))
    lines.append(f"✨ {money_html(total)} <b>← JAMI</b> ✨")
    return "\n".join(lines)


def create_order(
    user_id: int,
    pickup_address: str,
    delivery_address: str,
    description: str,
    phone: str,
    price: int,
    latitude: float | None = None,
    longitude: float | None = None,
    delivery_slot: str = "",
    promo_code: str = "",
    discount: int = 0,
    bonus_spent: int = 0,
    subtotal: int = 0,
) -> int:
    now = _now_iso()
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO orders (
                user_id, pickup_address, delivery_address, latitude, longitude,
                description, phone, price, status, payment_status, created_at, updated_at,
                delivery_slot, promo_code, discount, bonus_spent, subtotal
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'new', 'pending', ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                pickup_address,
                delivery_address,
                latitude,
                longitude,
                description,
                phone,
                price,
                now,
                now,
                delivery_slot,
                promo_code,
                discount,
                bonus_spent,
                subtotal,
            ),
        )
        return int(cursor.lastrowid)


def save_order_items(order_id: int, user_id: int) -> None:
    items = get_cart(user_id)
    with get_connection() as conn:
        conn.executemany(
            """
            INSERT INTO order_items (
                order_id, product_id, product_name, price, quantity
            ) VALUES (?, ?, ?, ?, ?)
            """,
            [
                (
                    order_id,
                    item["product_id"],
                    item["name"],
                    item["price"],
                    item["quantity"],
                )
                for item in items
            ],
        )


def save_order_items_direct(
    order_id: int, items: list[dict[str, Any]]
) -> None:
    """Mini App / tashqi buyurtma uchun."""
    with get_connection() as conn:
        conn.executemany(
            """
            INSERT INTO order_items (
                order_id, product_id, product_name, price, quantity
            ) VALUES (?, ?, ?, ?, ?)
            """,
            [
                (
                    order_id,
                    int(item["product_id"]),
                    str(item["name"]),
                    int(item["price"]),
                    int(item["quantity"]),
                )
                for item in items
            ],
        )


def get_order_items(order_id: int) -> list[sqlite3.Row]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM order_items
            WHERE order_id = ?
            ORDER BY id
            """,
            (order_id,),
        ).fetchall()
    return list(rows)


def get_order(order_id: int) -> sqlite3.Row | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM orders WHERE id = ?",
            (order_id,),
        ).fetchone()
    return row


def delete_order(order_id: int) -> bool:
    """Buyurtma va uning mahsulotlarini butunlay o'chiradi."""
    with get_connection() as conn:
        exists = conn.execute(
            "SELECT id FROM orders WHERE id = ?",
            (order_id,),
        ).fetchone()
        if not exists:
            return False
        conn.execute("DELETE FROM order_items WHERE order_id = ?", (order_id,))
        conn.execute("DELETE FROM orders WHERE id = ?", (order_id,))
    return True


def get_user_orders(user_id: int, limit: int = 10) -> list[sqlite3.Row]:
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


def get_last_delivery_address(user_id: int) -> str | None:
    """Oxirgi muvaffaqiyatli buyurtma manzili (lokatsiya emas, matn)."""
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT delivery_address FROM orders
            WHERE user_id = ?
              AND delivery_address IS NOT NULL
              AND delivery_address != ''
              AND delivery_address != 'Lokatsiya'
              AND status != 'cancelled'
            ORDER BY id DESC
            LIMIT 1
            """,
            (user_id,),
        ).fetchone()
    if not row:
        return None
    addr = (row["delivery_address"] or "").strip()
    return addr or None


def get_orders_by_status(
    status: str,
    limit: int = 20,
    *,
    oldest_first: bool = False,
) -> list[sqlite3.Row]:
    """Navbat uchun oldest_first=True (eski → yangi), tarix uchun False."""
    order_sql = "ASC" if oldest_first else "DESC"
    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT * FROM orders
            WHERE status = ?
            ORDER BY id {order_sql}
            LIMIT ?
            """,
            (status, limit),
        ).fetchall()
    return list(rows)


def get_queue_orders(
    statuses: list[str],
    limit: int = 30,
) -> list[sqlite3.Row]:
    """Bir nechta statusdagi buyurtmalar — navbat tartibida (id ASC)."""
    if not statuses:
        return []
    placeholders = ",".join("?" for _ in statuses)
    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT * FROM orders
            WHERE status IN ({placeholders})
            ORDER BY id ASC
            LIMIT ?
            """,
            (*statuses, limit),
        ).fetchall()
    return list(rows)


def get_orders_by_payment(
    payment_status: str,
    limit: int = 40,
) -> list[sqlite3.Row]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM orders
            WHERE payment_status = ?
              AND status != 'cancelled'
            ORDER BY id ASC
            LIMIT ?
            """,
            (payment_status, limit),
        ).fetchall()
    return list(rows)


def search_orders(query: str, limit: int = 30) -> list[sqlite3.Row]:
    """ID yoki telefon bo'yicha qidiruv."""
    q = (query or "").strip()
    if not q:
        return []
    with get_connection() as conn:
        if q.isdigit():
            rows = conn.execute(
                """
                SELECT * FROM orders
                WHERE id = ? OR phone LIKE ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (int(q), f"%{q}%", limit),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT * FROM orders
                WHERE phone LIKE ? OR delivery_address LIKE ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (f"%{q}%", f"%{q}%", limit),
            ).fetchall()
    return list(rows)


def update_order_status(order_id: int, status: str) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE orders
            SET status = ?, updated_at = ?
            WHERE id = ?
            """,
            (status, _now_iso(), order_id),
        )


def update_payment_status(order_id: int, payment_status: str) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE orders
            SET payment_status = ?, updated_at = ?
            WHERE id = ?
            """,
            (payment_status, _now_iso(), order_id),
        )


def format_order_items(order_id: int) -> str:
    items = get_order_items(order_id)
    if not items:
        return ""
    lines = ["🛍 Mahsulotlar:"]
    for item in items:
        lines.append(
            f"• {item['product_name']} x{item['quantity']} — "
            f"{item['price'] * item['quantity']:,} so'm"
        )
    return "\n".join(lines)


from bot.timeutil import money_html


def format_order(row: sqlite3.Row) -> str:
    status = ORDER_STATUS_LABELS.get(row["status"], row["status"])
    payment = PAYMENT_STATUS_LABELS.get(row["payment_status"], row["payment_status"])
    delivery = row["delivery_address"]
    if row["latitude"] is not None and row["longitude"] is not None:
        maps_url = f"https://maps.google.com/?q={row['latitude']},{row['longitude']}"
        delivery = f"{delivery}\n🗺 Xarita: {maps_url}"

    items_text = format_order_items(row["id"])
    parts = [
        f"📦 Buyurtma #{row['id']}",
        f"Holat: {status}",
        f"To'lov: {payment}",
        f"📅 Berilgan: ❰ {format_dt(row['created_at'])} ❱",
    ]
    if items_text:
        parts.append(items_text)
    slot = row["delivery_slot"] if "delivery_slot" in row.keys() else None
    if slot:
        parts.append(f"🕒 Yetkazish: ❰ {slot} ❱")
    promo = row["promo_code"] if "promo_code" in row.keys() else None
    discount = row["discount"] if "discount" in row.keys() else 0
    if promo:
        parts.append(f"🏷 Promo: {promo} (−{discount or 0:,} so'm)")
    bonus = row["bonus_spent"] if "bonus_spent" in row.keys() else 0
    if bonus:
        parts.append(f"🎁 Bonus: −{bonus:,} so'm")
    parts.extend(
        [
            f"📍 Qayerdan: {row['pickup_address']}",
            f"🏁 Qayerga: {delivery}",
            f"📝 Izoh: {row['description'] or '—'}",
            f"📞 Telefon: {row['phone']}",
            f"✨💰 JAMI: {row['price']:,} so'm ✨",
        ]
    )
    return "\n".join(parts)


def get_stats() -> dict[str, Any]:
    with get_connection() as conn:
        total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        total_orders = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        new_orders = conn.execute(
            "SELECT COUNT(*) FROM orders WHERE status = 'new'"
        ).fetchone()[0]
        active_orders = conn.execute(
            "SELECT COUNT(*) FROM orders WHERE status IN ('accepted', 'in_delivery')"
        ).fetchone()[0]
        delivered = conn.execute(
            "SELECT COUNT(*) FROM orders WHERE status = 'delivered'"
        ).fetchone()[0]
        revenue = conn.execute(
            """
            SELECT COALESCE(SUM(price), 0) FROM orders
            WHERE status != 'cancelled'
            """
        ).fetchone()[0]
        today_row = conn.execute(
            """
            SELECT COUNT(*) AS cnt, COALESCE(SUM(price), 0) AS total
            FROM orders
            WHERE date(created_at) = date('now', 'localtime')
              AND status != 'cancelled'
            """
        ).fetchone()
    return {
        "total_users": total_users,
        "total_orders": total_orders,
        "new_orders": new_orders,
        "active_orders": active_orders,
        "delivered_orders": delivered,
        "revenue_sum": int(revenue or 0),
        "today_orders": int(today_row["cnt"] or 0),
        "today_sum": int(today_row["total"] or 0),
    }


def search_products(query: str, limit: int = 20) -> list[sqlite3.Row]:
    q = f"%{query.strip()}%"
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT p.*, c.name AS category_name
            FROM products p
            LEFT JOIN categories c ON c.id = p.category_id
            WHERE p.is_active = 1
              AND (p.name LIKE ? OR IFNULL(p.description, '') LIKE ?)
            ORDER BY p.name
            LIMIT ?
            """,
            (q, q, limit),
        ).fetchall()
    return list(rows)


def add_favorite(user_id: int, product_id: int) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO favorites (user_id, product_id, created_at)
            VALUES (?, ?, ?)
            """,
            (user_id, product_id, _now_iso()),
        )


def remove_favorite(user_id: int, product_id: int) -> None:
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM favorites WHERE user_id = ? AND product_id = ?",
            (user_id, product_id),
        )


def is_favorite(user_id: int, product_id: int) -> bool:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT 1 FROM favorites WHERE user_id = ? AND product_id = ?",
            (user_id, product_id),
        ).fetchone()
    return row is not None


def get_favorites(user_id: int) -> list[sqlite3.Row]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT p.*, c.name AS category_name
            FROM favorites f
            JOIN products p ON p.id = f.product_id
            LEFT JOIN categories c ON c.id = p.category_id
            WHERE f.user_id = ? AND p.is_active = 1
            ORDER BY p.name COLLATE NOCASE
            """,
            (user_id,),
        ).fetchall()
    return list(rows)


def get_promo(code: str) -> sqlite3.Row | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT * FROM promo_codes
            WHERE UPPER(code) = UPPER(?) AND is_active = 1
            """,
            (code.strip(),),
        ).fetchone()
    return row


def get_promo_any(code: str) -> sqlite3.Row | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT * FROM promo_codes
            WHERE UPPER(code) = UPPER(?)
            """,
            (code.strip(),),
        ).fetchone()
    return row


def list_promos(active_only: bool = False) -> list[sqlite3.Row]:
    with get_connection() as conn:
        if active_only:
            rows = conn.execute(
                """
                SELECT * FROM promo_codes
                WHERE is_active = 1
                ORDER BY code COLLATE NOCASE
                """
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM promo_codes ORDER BY code COLLATE NOCASE"
            ).fetchall()
    return list(rows)


def upsert_promo(
    code: str,
    *,
    discount_percent: int = 0,
    discount_amount: int = 0,
    min_order: int = 0,
    is_active: bool = True,
) -> str:
    code_norm = (code or "").strip().upper()
    if not code_norm:
        raise ValueError("Promo kod kerak")
    with get_connection() as conn:
        existing = conn.execute(
            "SELECT code FROM promo_codes WHERE UPPER(code) = ?",
            (code_norm,),
        ).fetchone()
        if existing:
            conn.execute(
                """
                UPDATE promo_codes
                SET discount_percent = ?, discount_amount = ?,
                    min_order = ?, is_active = ?
                WHERE UPPER(code) = ?
                """,
                (
                    int(discount_percent or 0),
                    int(discount_amount or 0),
                    int(min_order or 0),
                    1 if is_active else 0,
                    code_norm,
                ),
            )
            return str(existing["code"])
        conn.execute(
            """
            INSERT INTO promo_codes
                (code, discount_percent, discount_amount, min_order, is_active)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                code_norm,
                int(discount_percent or 0),
                int(discount_amount or 0),
                int(min_order or 0),
                1 if is_active else 0,
            ),
        )
    return code_norm


def set_promo_active(code: str, is_active: bool) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE promo_codes SET is_active = ? WHERE UPPER(code) = UPPER(?)",
            (1 if is_active else 0, code.strip()),
        )


def calc_promo_discount(code: str, subtotal: int) -> tuple[int, str]:
    promo = get_promo(code)
    if not promo:
        return 0, "Promo kod topilmadi."
    if subtotal < promo["min_order"]:
        return 0, f"Minimal summa: {promo['min_order']:,} so'm"
    if promo["discount_percent"]:
        return int(subtotal * promo["discount_percent"] / 100), "OK"
    return int(promo["discount_amount"]), "OK"


def update_product_fields(
    product_id: int,
    *,
    name: str | None = None,
    price: int | None = None,
    description: str | None = None,
    category_id: int | None | object = ...,
    barcode: str | None | object = ...,
) -> None:
    """Mahsulot maydonlarini yangilaydi. category_id/barcode uchun ... = o'zgartirmaslik."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id FROM products WHERE id = ?", (product_id,)
        ).fetchone()
        if not row:
            raise ValueError("Mahsulot topilmadi")
        if name is not None:
            conn.execute(
                "UPDATE products SET name = ? WHERE id = ?",
                (name.strip(), product_id),
            )
        if price is not None:
            conn.execute(
                "UPDATE products SET price = ? WHERE id = ?",
                (int(price), product_id),
            )
        if description is not None:
            conn.execute(
                "UPDATE products SET description = ? WHERE id = ?",
                (description, product_id),
            )
        if category_id is not ...:
            cid = None if category_id in (None, 0, "") else int(category_id)  # type: ignore[arg-type]
            conn.execute(
                "UPDATE products SET category_id = ? WHERE id = ?",
                (cid, product_id),
            )
        if barcode is not ...:
            code = (str(barcode).strip() if barcode is not None else "") or None
            if code in {"0", "-", "none", "yo'q", "yoq"}:
                code = None
            if code:
                other = conn.execute(
                    "SELECT id, name FROM products WHERE barcode = ? AND id != ?",
                    (code, product_id),
                ).fetchone()
                if other:
                    raise ValueError(
                        f"Kod boshqa mahsulotda: #{other['id']} {other['name']}"
                    )
            conn.execute(
                "UPDATE products SET barcode = ? WHERE id = ?",
                (code, product_id),
            )


def get_range_report(date_from: str, date_to: str) -> dict[str, Any]:
    """Sana oralig'i bo'yicha savdo hisoboti (YYYY-MM-DD)."""
    d0 = (date_from or "").strip()[:10]
    d1 = (date_to or "").strip()[:10]
    if not d0 or not d1:
        raise ValueError("date_from va date_to kerak (YYYY-MM-DD)")
    with get_connection() as conn:
        orders = conn.execute(
            """
            SELECT COUNT(*) AS cnt, COALESCE(SUM(price), 0) AS total
            FROM orders
            WHERE date(created_at) BETWEEN date(?) AND date(?)
              AND status != 'cancelled'
            """,
            (d0, d1),
        ).fetchone()
        paid = conn.execute(
            """
            SELECT COUNT(*) AS cnt, COALESCE(SUM(price), 0) AS total
            FROM orders
            WHERE date(created_at) BETWEEN date(?) AND date(?)
              AND payment_status IN ('paid', 'cash')
            """,
            (d0, d1),
        ).fetchone()
        debt = conn.execute(
            """
            SELECT COUNT(*) AS cnt, COALESCE(SUM(price), 0) AS total
            FROM orders
            WHERE date(created_at) BETWEEN date(?) AND date(?)
              AND payment_status = 'debt'
              AND status != 'cancelled'
            """,
            (d0, d1),
        ).fetchone()
        cancelled = conn.execute(
            """
            SELECT COUNT(*) AS cnt, COALESCE(SUM(price), 0) AS total
            FROM orders
            WHERE date(created_at) BETWEEN date(?) AND date(?)
              AND status = 'cancelled'
            """,
            (d0, d1),
        ).fetchone()
        by_day = conn.execute(
            """
            SELECT date(created_at) AS d,
                   COUNT(*) AS cnt,
                   COALESCE(SUM(price), 0) AS total
            FROM orders
            WHERE date(created_at) BETWEEN date(?) AND date(?)
              AND status != 'cancelled'
            GROUP BY date(created_at)
            ORDER BY d
            """,
            (d0, d1),
        ).fetchall()
        top = conn.execute(
            """
            SELECT oi.product_name,
                   SUM(oi.quantity) AS qty,
                   SUM(oi.quantity * oi.price) AS revenue
            FROM order_items oi
            JOIN orders o ON o.id = oi.order_id
            WHERE date(o.created_at) BETWEEN date(?) AND date(?)
              AND o.status != 'cancelled'
            GROUP BY oi.product_name
            ORDER BY revenue DESC
            LIMIT 20
            """,
            (d0, d1),
        ).fetchall()
        # ABC: A = top 80% revenue, B = next 15%, C = rest
        abc_rows = []
        total_rev = sum(int(r["revenue"] or 0) for r in top)
        cum = 0
        for r in top:
            rev = int(r["revenue"] or 0)
            cum += rev
            share = (cum / total_rev * 100) if total_rev else 0
            if share <= 80:
                grade = "A"
            elif share <= 95:
                grade = "B"
            else:
                grade = "C"
            abc_rows.append(
                {
                    "product_name": r["product_name"],
                    "qty": int(r["qty"] or 0),
                    "revenue": rev,
                    "grade": grade,
                }
            )
    return {
        "date_from": d0,
        "date_to": d1,
        "orders_count": int(orders["cnt"] or 0),
        "orders_sum": int(orders["total"] or 0),
        "paid_count": int(paid["cnt"] or 0),
        "paid_sum": int(paid["total"] or 0),
        "debt_count": int(debt["cnt"] or 0),
        "debt_sum": int(debt["total"] or 0),
        "cancelled_count": int(cancelled["cnt"] or 0),
        "cancelled_sum": int(cancelled["total"] or 0),
        "profit_approx": int(paid["total"] or 0),  # COGS yo'q — to'langan savdo
        "by_day": [
            {
                "date": r["d"],
                "orders_count": int(r["cnt"] or 0),
                "revenue": int(r["total"] or 0),
            }
            for r in by_day
        ],
        "top": abc_rows,
        "abc": abc_rows,
    }


def get_bonus(user_id: int) -> int:
    user = get_user(user_id)
    if not user:
        return 0
    try:
        return int(user["bonus_points"] or 0)
    except (KeyError, IndexError, TypeError):
        return 0


def add_bonus(user_id: int, points: int) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE users SET bonus_points = COALESCE(bonus_points, 0) + ? WHERE user_id = ?",
            (points, user_id),
        )


def save_referral(referred_user_id: int, referrer_user_id: int) -> bool:
    """Yangi foydalanuvchi referralini saqlaydi. Takror bo'lsa False."""
    if referred_user_id == referrer_user_id:
        return False
    with get_connection() as conn:
        exists = conn.execute(
            "SELECT 1 FROM referrals WHERE referred_user_id = ?",
            (referred_user_id,),
        ).fetchone()
        if exists:
            return False
        if not get_user(referrer_user_id):
            return False
        conn.execute(
            """
            INSERT INTO referrals (referred_user_id, referrer_user_id, created_at, rewarded)
            VALUES (?, ?, ?, 1)
            """,
            (referred_user_id, referrer_user_id, _now_iso()),
        )
    return True


def spend_bonus(user_id: int, points: int) -> bool:
    if points <= 0:
        return True
    current = get_bonus(user_id)
    if current < points:
        return False
    with get_connection() as conn:
        conn.execute(
            "UPDATE users SET bonus_points = bonus_points - ? WHERE user_id = ?",
            (points, user_id),
        )
    return True


def set_product_stock(
    product_id: int,
    stock: int,
    *,
    reason: str = "inventory",
    note: str = "",
    admin_id: int | None = None,
    order_id: int | None = None,
) -> int:
    """Absolut qoldiqni o'rnatadi va jurnalga yozadi."""
    stock = max(0, int(stock))
    with get_connection() as conn:
        row = conn.execute(
            "SELECT COALESCE(stock, 0) AS stock FROM products WHERE id = ?",
            (int(product_id),),
        ).fetchone()
        if not row:
            raise ValueError("Mahsulot topilmadi")
        old = int(row["stock"])
        delta = stock - old
        conn.execute(
            "UPDATE products SET stock = ? WHERE id = ?",
            (stock, int(product_id)),
        )
        conn.execute(
            """
            INSERT INTO stock_movements (
                product_id, delta, stock_after, reason, note, order_id, admin_id, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                int(product_id),
                delta,
                stock,
                reason,
                (note or "").strip(),
                order_id,
                admin_id,
                _now_iso(),
            ),
        )
    return stock


def zero_category_stock(
    category_id: int,
    *,
    admin_id: int | None = None,
    note: str = "Toifa bo‘yicha 0",
) -> dict[str, int]:
    """Toifadagi barcha faol mahsulotlar qoldig‘ini 0 qiladi.

    Qaytaradi: updated (o‘zgarganlar), skipped (allaqachon 0), total.
    """
    cid = int(category_id)
    with get_connection() as conn:
        if cid == 0:
            rows = conn.execute(
                """
                SELECT id, COALESCE(stock, 0) AS stock
                FROM products
                WHERE is_active = 1 AND category_id IS NULL
                """
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT id, COALESCE(stock, 0) AS stock
                FROM products
                WHERE is_active = 1 AND category_id = ?
                """,
                (cid,),
            ).fetchall()
        updated = 0
        skipped = 0
        now = _now_iso()
        for row in rows:
            old = int(row["stock"])
            if old == 0:
                skipped += 1
                continue
            pid = int(row["id"])
            conn.execute(
                "UPDATE products SET stock = 0 WHERE id = ?",
                (pid,),
            )
            conn.execute(
                """
                INSERT INTO stock_movements (
                    product_id, delta, stock_after, reason, note,
                    order_id, admin_id, created_at
                ) VALUES (?, ?, 0, ?, ?, NULL, ?, ?)
                """,
                (
                    pid,
                    -old,
                    "inventory",
                    (note or "").strip(),
                    admin_id,
                    now,
                ),
            )
            updated += 1
    return {
        "updated": updated,
        "skipped": skipped,
        "total": updated + skipped,
    }


def adjust_product_stock(
    product_id: int,
    delta: int,
    *,
    reason: str = "adjust",
    note: str = "",
    admin_id: int | None = None,
    order_id: int | None = None,
) -> int:
    """Qoldiqni +/− qiladi va jurnalga yozadi."""
    delta = int(delta)
    with get_connection() as conn:
        row = conn.execute(
            "SELECT COALESCE(stock, 0) AS stock FROM products WHERE id = ?",
            (int(product_id),),
        ).fetchone()
        if not row:
            raise ValueError("Mahsulot topilmadi")
        new_stock = max(0, int(row["stock"]) + delta)
        actual_delta = new_stock - int(row["stock"])
        conn.execute(
            "UPDATE products SET stock = ? WHERE id = ?",
            (new_stock, int(product_id)),
        )
        if actual_delta != 0 or delta == 0:
            conn.execute(
                """
                INSERT INTO stock_movements (
                    product_id, delta, stock_after, reason, note,
                    order_id, admin_id, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    int(product_id),
                    actual_delta,
                    new_stock,
                    reason,
                    (note or "").strip(),
                    order_id,
                    admin_id,
                    _now_iso(),
                ),
            )
    return new_stock


def decrease_stock_for_cart(user_id: int, order_id: int | None = None) -> None:
    """Savatcha asosida ombordan chiqim (sotuv)."""
    items = get_cart(user_id)
    with get_connection() as conn:
        for item in items:
            pid = int(item["product_id"])
            qty = int(item["quantity"])
            row = conn.execute(
                "SELECT COALESCE(stock, 0) AS stock FROM products WHERE id = ?",
                (pid,),
            ).fetchone()
            if not row:
                continue
            old = int(row["stock"])
            new_stock = max(0, old - qty)
            conn.execute(
                "UPDATE products SET stock = ? WHERE id = ?",
                (new_stock, pid),
            )
            conn.execute(
                """
                INSERT INTO stock_movements (
                    product_id, delta, stock_after, reason, note,
                    order_id, admin_id, created_at
                ) VALUES (?, ?, ?, 'sale', ?, ?, NULL, ?)
                """,
                (
                    pid,
                    new_stock - old,
                    new_stock,
                    f"Buyurtma #{order_id}" if order_id else "Savatcha sotuvi",
                    order_id,
                    _now_iso(),
                ),
            )


def decrease_stock_for_order_items(order_id: int, items: list[dict]) -> None:
    """Mini App / tashqi buyurtma chiqimi."""
    with get_connection() as conn:
        for item in items:
            try:
                pid = int(item.get("product_id") or 0)
                qty = int(item.get("quantity") or 0)
            except (TypeError, ValueError):
                continue
            if pid <= 0 or qty <= 0:
                continue
            row = conn.execute(
                "SELECT COALESCE(stock, 0) AS stock FROM products WHERE id = ?",
                (pid,),
            ).fetchone()
            if not row:
                continue
            old = int(row["stock"])
            new_stock = max(0, old - qty)
            conn.execute(
                "UPDATE products SET stock = ? WHERE id = ?",
                (new_stock, pid),
            )
            conn.execute(
                """
                INSERT INTO stock_movements (
                    product_id, delta, stock_after, reason, note,
                    order_id, admin_id, created_at
                ) VALUES (?, ?, ?, 'sale', ?, ?, NULL, ?)
                """,
                (
                    pid,
                    new_stock - old,
                    new_stock,
                    f"Buyurtma #{order_id}",
                    order_id,
                    _now_iso(),
                ),
            )


def get_stock_movements(
    *,
    limit: int = 30,
    product_id: int | None = None,
    reason: str | None = None,
) -> list[sqlite3.Row]:
    clauses: list[str] = []
    params: list[Any] = []
    if product_id is not None:
        clauses.append("m.product_id = ?")
        params.append(int(product_id))
    if reason:
        clauses.append("m.reason = ?")
        params.append(reason)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    params.append(int(limit))
    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT m.*, p.name AS product_name
            FROM stock_movements m
            LEFT JOIN products p ON p.id = m.product_id
            {where}
            ORDER BY m.id DESC
            LIMIT ?
            """,
            params,
        ).fetchall()
    return list(rows)


def get_warehouse_summary() -> dict[str, int]:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT
              COUNT(*) AS products,
              COALESCE(SUM(COALESCE(stock, 0)), 0) AS units,
              COALESCE(SUM(CASE WHEN COALESCE(stock, 0) <= 0 THEN 1 ELSE 0 END), 0)
                AS zero_stock
            FROM products
            WHERE is_active = 1
            """
        ).fetchone()
        today = conn.execute(
            """
            SELECT
              COALESCE(SUM(CASE WHEN delta > 0 THEN delta ELSE 0 END), 0) AS in_qty,
              COALESCE(SUM(CASE WHEN delta < 0 THEN -delta ELSE 0 END), 0) AS out_qty,
              COUNT(*) AS moves
            FROM stock_movements
            WHERE date(created_at) = date('now', 'localtime')
            """
        ).fetchone()
    from bot.config import LOW_STOCK_THRESHOLD

    low = len(get_low_stock_products(LOW_STOCK_THRESHOLD))
    return {
        "products": int(row["products"] or 0),
        "units": int(row["units"] or 0),
        "zero_stock": int(row["zero_stock"] or 0),
        "low_stock": low,
        "today_in": int(today["in_qty"] or 0),
        "today_out": int(today["out_qty"] or 0),
        "today_moves": int(today["moves"] or 0),
    }


def set_product_image(product_id: int, file_id: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE products SET image_file_id = ? WHERE id = ?",
            (file_id, product_id),
        )


def refill_cart_from_order(user_id: int, order_id: int) -> int:
    items = get_order_items(order_id)
    clear_cart(user_id)
    added = 0
    for item in items:
        if not item["product_id"]:
            continue
        product = get_product(item["product_id"])
        if not product:
            continue
        add_to_cart(user_id, item["product_id"], item["quantity"], 0)
        added += 1
    return added


def get_all_user_ids() -> list[int]:
    with get_connection() as conn:
        rows = conn.execute("SELECT user_id FROM users").fetchall()
    return [int(r["user_id"]) for r in rows]


def issue_admin_login_code(admin_id: int, *, ttl_minutes: int = 10) -> str:
    """6 xonali bir martalik admin kirish kodi."""
    import secrets

    code = f"{secrets.randbelow(1_000_000):06d}"
    expires = (now_tashkent() + timedelta(minutes=max(1, ttl_minutes))).isoformat()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO admin_login_codes (admin_id, code, expires_at)
            VALUES (?, ?, ?)
            ON CONFLICT(admin_id) DO UPDATE SET
              code = excluded.code,
              expires_at = excluded.expires_at
            """,
            (int(admin_id), code, expires),
        )
    return code


def consume_admin_login_code(admin_id: int, code: str) -> bool:
    code = (code or "").strip()
    if not code:
        return False
    now = now_tashkent().isoformat()
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT code, expires_at FROM admin_login_codes
            WHERE admin_id = ?
            """,
            (int(admin_id),),
        ).fetchone()
        if not row:
            return False
        if str(row["expires_at"]) < now:
            conn.execute(
                "DELETE FROM admin_login_codes WHERE admin_id = ?",
                (int(admin_id),),
            )
            return False
        if str(row["code"]) != code:
            return False
        conn.execute(
            "DELETE FROM admin_login_codes WHERE admin_id = ?",
            (int(admin_id),),
        )
    return True


def create_admin_session(admin_id: int, *, days: int = 30) -> str:
    import secrets

    token = secrets.token_urlsafe(32)
    now = now_tashkent()
    expires = (now + timedelta(days=max(1, days))).isoformat()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO admin_sessions (token, admin_id, expires_at, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (token, int(admin_id), expires, now.isoformat()),
        )
    return token


def get_admin_id_by_session(token: str) -> int | None:
    token = (token or "").strip()
    if not token:
        return None
    now = now_tashkent().isoformat()
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT admin_id, expires_at FROM admin_sessions
            WHERE token = ?
            """,
            (token,),
        ).fetchone()
        if not row:
            return None
        if str(row["expires_at"]) < now:
            conn.execute("DELETE FROM admin_sessions WHERE token = ?", (token,))
            return None
        return int(row["admin_id"])


def revoke_admin_session(token: str) -> None:
    token = (token or "").strip()
    if not token:
        return
    with get_connection() as conn:
        conn.execute("DELETE FROM admin_sessions WHERE token = ?", (token,))


def get_daily_report() -> dict[str, Any]:
    today = now_tashkent().strftime("%Y-%m-%d")
    with get_connection() as conn:
        orders = conn.execute(
            """
            SELECT COUNT(*) AS cnt, COALESCE(SUM(price), 0) AS total
            FROM orders
            WHERE date(created_at) = date('now', 'localtime')
              AND status != 'cancelled'
            """
        ).fetchone()
        paid = conn.execute(
            """
            SELECT COUNT(*) AS cnt, COALESCE(SUM(price), 0) AS total
            FROM orders
            WHERE date(created_at) = date('now', 'localtime')
              AND payment_status IN ('paid', 'cash')
            """
        ).fetchone()
        waiting = conn.execute(
            """
            SELECT COUNT(*) AS cnt, COALESCE(SUM(price), 0) AS total
            FROM orders
            WHERE date(created_at) = date('now', 'localtime')
              AND payment_status IN ('pending', 'card_waiting')
              AND status != 'cancelled'
            """
        ).fetchone()
        top = conn.execute(
            """
            SELECT oi.product_name, SUM(oi.quantity) AS qty
            FROM order_items oi
            JOIN orders o ON o.id = oi.order_id
            WHERE date(o.created_at) = date('now', 'localtime')
              AND o.status != 'cancelled'
            GROUP BY oi.product_name
            ORDER BY qty DESC
            LIMIT 5
            """
        ).fetchall()
    return {
        "date": today,
        "orders_count": int(orders["cnt"] or 0),
        "orders_sum": int(orders["total"] or 0),
        "paid_count": int(paid["cnt"] or 0),
        "paid_sum": int(paid["total"] or 0),
        "waiting_count": int(waiting["cnt"] or 0),
        "waiting_sum": int(waiting["total"] or 0),
        "top": list(top),
    }


def export_products_csv() -> str:
    import csv
    from io import StringIO

    products = get_products(active_only=False)
    buf = StringIO()
    writer = csv.writer(buf)
    writer.writerow(["id", "name", "price", "description", "category_id", "stock", "is_active"])
    for p in products:
        writer.writerow(
            [
                p["id"],
                p["name"],
                p["price"],
                p["description"] or "",
                p["category_id"] or "",
                p["stock"] if "stock" in p.keys() else 100,
                p["is_active"],
            ]
        )
    return buf.getvalue()


def import_products_csv(text: str) -> int:
    import csv
    from io import StringIO

    reader = csv.DictReader(StringIO(text))
    count = 0
    with get_connection() as conn:
        for row in reader:
            name = (row.get("name") or "").strip()
            if not name:
                continue
            price = int(float(row.get("price") or 0))
            description = row.get("description") or ""
            category_id = row.get("category_id") or None
            stock = int(float(row.get("stock") or 100))
            is_active = int(float(row.get("is_active") or 1))
            pid = row.get("id")
            if pid:
                exists = conn.execute(
                    "SELECT id FROM products WHERE id = ?", (pid,)
                ).fetchone()
                if exists:
                    conn.execute(
                        """
                        UPDATE products
                        SET name=?, price=?, description=?, category_id=?, stock=?, is_active=?
                        WHERE id=?
                        """,
                        (name, price, description, category_id or None, stock, is_active, pid),
                    )
                    count += 1
                    continue
            conn.execute(
                """
                INSERT INTO products (name, price, description, category_id, stock, is_active)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (name, price, description, category_id or None, stock, is_active),
            )
            count += 1
    return count


def get_courier_orders() -> list[sqlite3.Row]:
    """Kuryer navbati: eski buyurtma birinchi."""
    return get_queue_orders(["accepted", "in_delivery"], limit=30)


# --- Contacts & debts ---
def create_contact(
    name: str,
    phone: str | None = None,
    note: str = "",
    telegram_user_id: int | None = None,
) -> int:
    now = _now_iso()
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO contacts (name, phone, note, telegram_user_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                name.strip(),
                (phone or "").strip() or None,
                (note or "").strip(),
                telegram_user_id,
                now,
                now,
            ),
        )
        return int(cur.lastrowid)


def update_contact(
    contact_id: int,
    *,
    name: str | None = None,
    phone: str | None = None,
    note: str | None = None,
) -> None:
    contact = get_contact(contact_id)
    if not contact:
        return
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE contacts
            SET name = ?, phone = ?, note = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                name if name is not None else contact["name"],
                phone if phone is not None else contact["phone"],
                note if note is not None else contact["note"],
                _now_iso(),
                contact_id,
            ),
        )


def get_contact(contact_id: int) -> sqlite3.Row | None:
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM contacts WHERE id = ?", (contact_id,)
        ).fetchone()


def find_contact_by_phone(phone: str) -> sqlite3.Row | None:
    digits = "".join(ch for ch in (phone or "") if ch.isdigit())
    if len(digits) < 9:
        return None
    tail = digits[-9:]
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM contacts WHERE phone IS NOT NULL"
        ).fetchall()
    for row in rows:
        p = "".join(ch for ch in (row["phone"] or "") if ch.isdigit())
        if p.endswith(tail):
            return row
    return None


def find_or_create_contact_for_order(order: sqlite3.Row) -> int:
    phone = (order["phone"] or "").strip()
    existing = find_contact_by_phone(phone) if phone else None
    if existing:
        if order["user_id"] and not existing["telegram_user_id"]:
            with get_connection() as conn:
                conn.execute(
                    """
                    UPDATE contacts
                    SET telegram_user_id = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (order["user_id"], _now_iso(), existing["id"]),
                )
        return int(existing["id"])
    user = get_user(order["user_id"]) if order["user_id"] else None
    name = (user["full_name"] if user else None) or f"Mijoz #{order['user_id']}"
    return create_contact(
        name=name,
        phone=phone or None,
        note=f"Buyurtma #{order['id']}",
        telegram_user_id=order["user_id"],
    )


def list_contacts(*, debtors_only: bool = False) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT c.*,
                   COALESCE((
                     SELECT SUM(
                       CASE WHEN kind='debt' THEN amount ELSE -amount END
                     )
                     FROM debt_ledger d WHERE d.contact_id = c.id
                   ), 0) AS balance
            FROM contacts c
            ORDER BY c.name COLLATE NOCASE
            """
        ).fetchall()
    result = []
    for row in rows:
        item = {k: row[k] for k in row.keys()}
        bal = int(item.get("balance") or 0)
        item["balance"] = bal
        if debtors_only and bal <= 0:
            continue
        result.append(item)
    if debtors_only:
        result.sort(key=lambda x: -x["balance"])
    return result


def get_contact_balance(contact_id: int) -> int:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT COALESCE(
              SUM(CASE WHEN kind='debt' THEN amount ELSE -amount END), 0
            )
            FROM debt_ledger WHERE contact_id = ?
            """,
            (contact_id,),
        ).fetchone()
    return int(row[0] if row else 0)


def add_debt_entry(
    contact_id: int,
    amount: int,
    *,
    kind: str = "debt",
    order_id: int | None = None,
    note: str = "",
    created_by: int | None = None,
) -> int:
    if amount <= 0:
        raise ValueError("Summa 0 dan katta bo'lsin")
    if kind not in {"debt", "payment"}:
        raise ValueError("kind noto'g'ri")
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO debt_ledger
                (contact_id, kind, amount, order_id, note, created_by, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                contact_id,
                kind,
                int(amount),
                order_id,
                (note or "").strip(),
                created_by,
                _now_iso(),
            ),
        )
        return int(cur.lastrowid)


def list_debt_ledger(contact_id: int, limit: int = 20) -> list[sqlite3.Row]:
    with get_connection() as conn:
        return list(
            conn.execute(
                """
                SELECT * FROM debt_ledger
                WHERE contact_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (contact_id, limit),
            ).fetchall()
        )


def debt_totals() -> dict[str, int]:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT
              COALESCE(SUM(CASE WHEN kind='debt' THEN amount ELSE 0 END), 0)
                AS debts,
              COALESCE(SUM(CASE WHEN kind='payment' THEN amount ELSE 0 END), 0)
                AS payments
            FROM debt_ledger
            """
        ).fetchone()
    debts = int(row["debts"])
    payments = int(row["payments"])
    return {"debts": debts, "payments": payments, "open": max(0, debts - payments)}


def mark_order_as_debt(
    order_id: int,
    *,
    created_by: int | None = None,
    contact_id: int | None = None,
) -> tuple[int, int]:
    """Buyurtmani qarzga yozadi. Qaytaradi: (contact_id, balance)."""
    order = get_order(order_id)
    if not order:
        raise ValueError("Buyurtma topilmadi")
    cid = contact_id or find_or_create_contact_for_order(order)
    with get_connection() as conn:
        exists = conn.execute(
            """
            SELECT id FROM debt_ledger
            WHERE order_id = ? AND kind = 'debt'
            """,
            (order_id,),
        ).fetchone()
    if not exists:
        add_debt_entry(
            cid,
            int(order["price"]),
            kind="debt",
            order_id=order_id,
            note=f"Buyurtma #{order_id}",
            created_by=created_by,
        )
    update_payment_status(order_id, "debt")
    return cid, get_contact_balance(cid)


# --- Language / zones / reviews / recurring / recommendations ---
def get_user_language(user_id: int) -> str:
    from bot.config import DEFAULT_LANG

    user = get_user(user_id)
    if not user:
        return DEFAULT_LANG or "uz"
    try:
        lang = user["language"]
    except (KeyError, IndexError, TypeError):
        return DEFAULT_LANG or "uz"
    return (lang or DEFAULT_LANG or "uz").strip().lower() or "uz"


def set_user_language(user_id: int, lang: str) -> None:
    lang = (lang or "uz").strip().lower()
    if lang not in ("uz", "ru"):
        lang = "uz"
    with get_connection() as conn:
        conn.execute(
            "UPDATE users SET language = ? WHERE user_id = ?",
            (lang, user_id),
        )


def get_delivery_fee(
    address: str = "",
    lat: float | None = None,
    lon: float | None = None,
    *,
    subtotal: int = 0,
) -> tuple[int, str]:
    """Mahsulot summasiga qarab yetkazish narxi.

    ≤ 50 000 → 5 000; undan yuqori → 10 000.
    """
    from bot.config import (
        DELIVERY_FEE_HIGH,
        DELIVERY_FEE_LOW,
        DELIVERY_FEE_THRESHOLD,
    )

    _ = (address, lat, lon)
    amount = max(0, int(subtotal or 0))
    if amount <= DELIVERY_FEE_THRESHOLD:
        return DELIVERY_FEE_LOW, "Yetkazish"
    return DELIVERY_FEE_HIGH, "Yetkazish"


def list_delivery_zones(active_only: bool = False) -> list[sqlite3.Row]:
    return []


def upsert_zone(
    *,
    zone_id: int | None = None,
    name: str,
    keywords: str = "",
    price: int,
    is_active: int = 1,
) -> int:
    return 0


def deactivate_zone(zone_id: int) -> bool:
    return False


def save_order_review(
    order_id: int, user_id: int, rating: int, comment: str = ""
) -> bool:
    rating = max(1, min(5, int(rating)))
    with get_connection() as conn:
        exists = conn.execute(
            "SELECT 1 FROM order_reviews WHERE order_id = ?",
            (order_id,),
        ).fetchone()
        if exists:
            return False
        conn.execute(
            """
            INSERT INTO order_reviews (order_id, user_id, rating, comment, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (order_id, user_id, rating, (comment or "").strip(), _now_iso()),
        )
    return True


def get_order_review(order_id: int) -> sqlite3.Row | None:
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM order_reviews WHERE order_id = ?",
            (order_id,),
        ).fetchone()


def get_recommended_products(user_id: int, limit: int = 6) -> list[sqlite3.Row]:
    with get_connection() as conn:
        past = conn.execute(
            """
            SELECT DISTINCT oi.product_id
            FROM order_items oi
            JOIN orders o ON o.id = oi.order_id
            WHERE o.user_id = ?
              AND oi.product_id IS NOT NULL
              AND o.status != 'cancelled'
            """,
            (user_id,),
        ).fetchall()
        past_ids = [int(r["product_id"]) for r in past if r["product_id"]]
        if past_ids:
            placeholders = ",".join("?" * len(past_ids))
            rows = conn.execute(
                f"""
                SELECT p.*, c.name AS category_name, COUNT(*) AS score
                FROM order_items oi
                JOIN orders o ON o.id = oi.order_id
                JOIN products p ON p.id = oi.product_id
                LEFT JOIN categories c ON c.id = p.category_id
                WHERE o.status != 'cancelled'
                  AND oi.product_id IS NOT NULL
                  AND oi.product_id NOT IN ({placeholders})
                  AND p.is_active = 1
                  AND o.id IN (
                    SELECT DISTINCT o2.id
                    FROM orders o2
                    JOIN order_items oi2 ON oi2.order_id = o2.id
                    WHERE oi2.product_id IN ({placeholders})
                      AND o2.status != 'cancelled'
                  )
                GROUP BY p.id
                ORDER BY score DESC, p.name COLLATE NOCASE
                LIMIT ?
                """,
                (*past_ids, *past_ids, limit),
            ).fetchall()
            if rows:
                return list(rows)
        rows = conn.execute(
            """
            SELECT p.*, c.name AS category_name, COALESCE(SUM(oi.quantity), 0) AS score
            FROM products p
            LEFT JOIN categories c ON c.id = p.category_id
            LEFT JOIN order_items oi ON oi.product_id = p.id
            LEFT JOIN orders o ON o.id = oi.order_id
              AND o.status != 'cancelled'
              AND date(o.created_at) >= date('now', '-30 day', 'localtime')
            WHERE p.is_active = 1
            GROUP BY p.id
            ORDER BY score DESC, p.name COLLATE NOCASE
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return list(rows)


def get_low_stock_products(threshold: int) -> list[sqlite3.Row]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM products
            WHERE is_active = 1
              AND COALESCE(stock, 0) <= ?
            ORDER BY stock ASC, name COLLATE NOCASE
            """,
            (int(threshold),),
        ).fetchall()
    return list(rows)


def get_inventory_products(
    *,
    low_only: bool = False,
    threshold: int | None = None,
    category_id: int | None = None,
    limit: int = 200,
) -> list[sqlite3.Row]:
    """Ombor paneli: mahsulotlar (toifa + qoldiq)."""
    from bot.config import LOW_STOCK_THRESHOLD

    thr = int(threshold if threshold is not None else LOW_STOCK_THRESHOLD)
    clauses = ["p.is_active = 1"]
    params: list[Any] = []
    if low_only:
        clauses.append("COALESCE(p.stock, 0) <= ?")
        params.append(thr)
    if category_id is not None:
        if int(category_id) == 0:
            clauses.append("p.category_id IS NULL")
        else:
            clauses.append("p.category_id = ?")
            params.append(int(category_id))
    where = " AND ".join(clauses)
    params.append(int(limit))
    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT p.*, c.name AS category_name
            FROM products p
            LEFT JOIN categories c ON c.id = p.category_id
            WHERE {where}
            ORDER BY c.name COLLATE NOCASE, p.name COLLATE NOCASE, p.id
            LIMIT ?
            """,
            params,
        ).fetchall()
    return list(rows)


def get_inventory_categories(
    *,
    low_only: bool = False,
    threshold: int | None = None,
) -> list[dict[str, Any]]:
    """Ombor: toifalar va mahsulot/qoldiq soni."""
    from bot.config import LOW_STOCK_THRESHOLD

    thr = int(threshold if threshold is not None else LOW_STOCK_THRESHOLD)
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
              c.id AS category_id,
              c.name AS category_name,
              COALESCE(NULLIF(c.emoji, ''), '📦') AS emoji,
              COUNT(p.id) AS product_count,
              COALESCE(SUM(CASE WHEN COALESCE(p.stock, 0) <= ? THEN 1 ELSE 0 END), 0)
                AS low_count,
              COALESCE(SUM(COALESCE(p.stock, 0)), 0) AS stock_sum
            FROM categories c
            LEFT JOIN products p
              ON p.category_id = c.id AND p.is_active = 1
            WHERE c.is_active = 1
            GROUP BY c.id, c.name, c.emoji
            HAVING product_count > 0
            ORDER BY c.name COLLATE NOCASE
            """,
            (thr,),
        ).fetchall()
        uncategorized = conn.execute(
            """
            SELECT
              COUNT(*) AS product_count,
              COALESCE(SUM(CASE WHEN COALESCE(stock, 0) <= ? THEN 1 ELSE 0 END), 0)
                AS low_count,
              COALESCE(SUM(COALESCE(stock, 0)), 0) AS stock_sum
            FROM products
            WHERE is_active = 1 AND category_id IS NULL
            """,
            (thr,),
        ).fetchone()

    result: list[dict[str, Any]] = [
        {
            "category_id": int(r["category_id"]),
            "category_name": r["category_name"],
            "emoji": r["emoji"] or "📦",
            "product_count": int(r["product_count"]),
            "low_count": int(r["low_count"]),
            "stock_sum": int(r["stock_sum"]),
        }
        for r in rows
    ]
    if uncategorized and int(uncategorized["product_count"] or 0) > 0:
        result.append(
            {
                "category_id": 0,
                "category_name": "Toifasiz",
                "emoji": "📦",
                "product_count": int(uncategorized["product_count"]),
                "low_count": int(uncategorized["low_count"]),
                "stock_sum": int(uncategorized["stock_sum"]),
            }
        )
    if low_only:
        result = [c for c in result if c["low_count"] > 0]
    return result


def create_recurring_order(
    user_id: int,
    source_order_id: int,
    interval_days: int,
    *,
    phone: str = "",
    address: str = "",
    slot: str = "",
    note: str = "",
) -> int:
    days = max(1, int(interval_days))
    next_run = (now_tashkent() + timedelta(days=days)).isoformat()
    order = get_order(source_order_id)
    if order:
        phone = phone or (order["phone"] or "")
        address = address or (order["delivery_address"] or "")
        try:
            slot = slot or (order["delivery_slot"] or "")
        except (KeyError, IndexError, TypeError):
            pass
        try:
            note = note or (order["description"] or "")
        except (KeyError, IndexError, TypeError):
            pass
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO recurring_orders (
                user_id, source_order_id, interval_days, next_run,
                phone, address, slot, note, is_active, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
            """,
            (
                user_id,
                source_order_id,
                days,
                next_run,
                phone,
                address,
                slot,
                note,
                _now_iso(),
            ),
        )
        return int(cur.lastrowid)


def get_due_recurring_orders() -> list[sqlite3.Row]:
    now = _now_iso()
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM recurring_orders
            WHERE is_active = 1
              AND datetime(next_run) <= datetime(?)
            ORDER BY next_run
            """,
            (now,),
        ).fetchall()
    return list(rows)


def mark_recurring_run(recurring_id: int, next_run_iso: str) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE recurring_orders
            SET next_run = ?
            WHERE id = ?
            """,
            (next_run_iso, recurring_id),
        )


def list_user_recurring(user_id: int) -> list[sqlite3.Row]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM recurring_orders
            WHERE user_id = ? AND is_active = 1
            ORDER BY next_run
            """,
            (user_id,),
        ).fetchall()
    return list(rows)


def deactivate_recurring(recurring_id: int, user_id: int | None = None) -> bool:
    with get_connection() as conn:
        if user_id is not None:
            cur = conn.execute(
                """
                UPDATE recurring_orders
                SET is_active = 0
                WHERE id = ? AND user_id = ?
                """,
                (recurring_id, user_id),
            )
        else:
            cur = conn.execute(
                """
                UPDATE recurring_orders
                SET is_active = 0
                WHERE id = ?
                """,
                (recurring_id,),
            )
        return cur.rowcount > 0


# --- Mening Shajaram share ---
def _new_shajara_code() -> str:
    import random
    import string

    alphabet = string.ascii_uppercase + string.digits
    alphabet = alphabet.replace("O", "").replace("0", "").replace("I", "").replace("1", "")
    return "".join(random.choice(alphabet) for _ in range(6))


def save_shajara_share(payload_json: str, code: str | None = None) -> str:
    """Yangi yoki mavjud kod bilan shajarani saqlaydi. Qaytaradi: code."""
    now = _now_iso()
    with get_connection() as conn:
        if code:
            code = code.strip().upper()
            row = conn.execute(
                "SELECT code FROM shajara_shares WHERE code = ?", (code,)
            ).fetchone()
            if row:
                conn.execute(
                    """
                    UPDATE shajara_shares
                    SET payload = ?, updated_at = ?
                    WHERE code = ?
                    """,
                    (payload_json, now, code),
                )
                return code
        for _ in range(12):
            candidate = _new_shajara_code()
            try:
                conn.execute(
                    """
                    INSERT INTO shajara_shares (code, payload, created_at, updated_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (candidate, payload_json, now, now),
                )
                return candidate
            except sqlite3.IntegrityError:
                continue
    raise RuntimeError("Share kod yaratilmadi")


def get_shajara_share(code: str) -> str | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT payload FROM shajara_shares WHERE code = ?",
            (code.strip().upper(),),
        ).fetchone()
    return str(row["payload"]) if row else None


def upsert_push_subscription(
    admin_id: int, endpoint: str, p256dh: str, auth: str
) -> None:
    now = _now_iso()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO push_subscriptions (endpoint, admin_id, p256dh, auth, created_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(endpoint) DO UPDATE SET
                admin_id = excluded.admin_id,
                p256dh = excluded.p256dh,
                auth = excluded.auth,
                created_at = excluded.created_at
            """,
            (endpoint, int(admin_id), p256dh, auth, now),
        )


def list_push_subscriptions() -> list[sqlite3.Row]:
    with get_connection() as conn:
        return list(
            conn.execute(
                "SELECT endpoint, admin_id, p256dh, auth, created_at "
                "FROM push_subscriptions"
            ).fetchall()
        )


def delete_push_subscription(endpoint: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM push_subscriptions WHERE endpoint = ?",
            (endpoint,),
        )


def delete_push_subscriptions_for_admin(admin_id: int) -> None:
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM push_subscriptions WHERE admin_id = ?",
            (int(admin_id),),
        )
