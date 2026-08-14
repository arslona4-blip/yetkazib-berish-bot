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
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 1,
                PRIMARY KEY (user_id, product_id)
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
        count = conn.execute("SELECT COUNT(*) AS c FROM products").fetchone()["c"]
        if count == 0:
            seed = [
                ("Guruch 1kg", 18000, "Oq guruch, yumshoq", "Oziq-ovqat"),
                ("Sut 1L", 12000, "Pastörizatsiya qilingan", "Ichimliklar"),
                ("Non", 4000, "Yangi non", "Oziq-ovqat"),
                ("Coca-Cola 1.5L", 14000, "Gazli ichimlik", "Ichimliklar"),
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
        return int(cur.lastrowid)


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
        return cur.rowcount > 0


def set_product_active(product_id: int, active: bool) -> bool:
    with get_connection() as conn:
        cur = conn.execute(
            "UPDATE products SET is_active = ? WHERE id = ?",
            (1 if active else 0, int(product_id)),
        )
        return cur.rowcount > 0


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
    qty = max(1, int(qty))
    with get_connection() as conn:
        row = conn.execute(
            "SELECT quantity FROM cart WHERE user_id = ? AND product_id = ?",
            (user_id, product_id),
        ).fetchone()
        if row:
            conn.execute(
                "UPDATE cart SET quantity = quantity + ? WHERE user_id = ? AND product_id = ?",
                (qty, user_id, product_id),
            )
        else:
            conn.execute(
                "INSERT INTO cart (user_id, product_id, quantity) VALUES (?, ?, ?)",
                (user_id, product_id, qty),
            )


def cart_set_qty(user_id: int, product_id: int, qty: int) -> None:
    qty = int(qty)
    with get_connection() as conn:
        if qty <= 0:
            conn.execute(
                "DELETE FROM cart WHERE user_id = ? AND product_id = ?",
                (user_id, product_id),
            )
            return
        row = conn.execute(
            "SELECT quantity FROM cart WHERE user_id = ? AND product_id = ?",
            (user_id, product_id),
        ).fetchone()
        if row:
            conn.execute(
                "UPDATE cart SET quantity = ? WHERE user_id = ? AND product_id = ?",
                (qty, user_id, product_id),
            )
        else:
            conn.execute(
                "INSERT INTO cart (user_id, product_id, quantity) VALUES (?, ?, ?)",
                (user_id, product_id, qty),
            )


def cart_delta(user_id: int, product_id: int, delta: int) -> int:
    """Miqdorni o‘zgartiradi; yangi quantity qaytaradi (0 = o‘chirilgan)."""
    items = {i["product_id"]: i["quantity"] for i in get_cart(user_id)}
    cur = int(items.get(int(product_id), 0)) + int(delta)
    cart_set_qty(user_id, product_id, cur)
    return max(0, cur)


def cart_clear(user_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))


def get_cart(user_id: int) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT c.product_id, c.quantity, p.name, p.price
            FROM cart c
            JOIN products p ON p.id = c.product_id
            WHERE c.user_id = ? AND p.is_active = 1
            ORDER BY p.name
            """,
            (user_id,),
        ).fetchall()
    items = []
    for r in rows:
        items.append(
            {
                "product_id": int(r["product_id"]),
                "name": r["name"],
                "price": int(r["price"]),
                "quantity": int(r["quantity"]),
                "line_total": int(r["price"]) * int(r["quantity"]),
            }
        )
    return items


def cart_total(user_id: int) -> int:
    return sum(i["line_total"] for i in get_cart(user_id))


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
