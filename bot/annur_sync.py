"""An-Nur kassa bilan bitta ombor: katalog kassadan olinadi, bot buyurtmalari kassaga yuboriladi.

ANNUR_URL va ANNUR_BOT_KEY berilmasa modul hech narsa qilmaydi.
"""

from __future__ import annotations

import logging
import math
import os
import sqlite3

import aiohttp
from telegram.ext import Application, ContextTypes

from bot.config import ADMIN_IDS
from bot.database import get_connection
from bot.timeutil import now_tashkent

logger = logging.getLogger(__name__)

ANNUR_URL = os.getenv("ANNUR_URL", "").strip().rstrip("/")
ANNUR_BOT_KEY = os.getenv("ANNUR_BOT_KEY", "").strip()
HIDE_OUT_OF_STOCK = os.getenv("ANNUR_HIDE_OUT_OF_STOCK", "").strip().lower() in ("1", "true", "ha", "yes")
# Kassada bundan kam faol mahsulot bo'lsa, botdagi "ortiqcha" mahsulotlar o'chirilmaydi.
MIN_CATALOG_FOR_PRUNE = int(os.getenv("ANNUR_MIN_CATALOG", "5"))
PULL_EVERY_RUNS = 2
TIMEOUT = aiohttp.ClientTimeout(total=20)

KASSA_STATUS = {"delivered": "done", "cancelled": "cancelled"}


def enabled() -> bool:
    return bool(ANNUR_URL and ANNUR_BOT_KEY)


def _headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {ANNUR_BOT_KEY}"}


def _ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute("CREATE TABLE IF NOT EXISTS annur_state (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    product_cols = {r[1] for r in conn.execute("PRAGMA table_info(products)").fetchall()}
    if "annur_id" not in product_cols:
        conn.execute("ALTER TABLE products ADD COLUMN annur_id INTEGER")
    order_cols = {r[1] for r in conn.execute("PRAGMA table_info(orders)").fetchall()}
    if "annur_ref" not in order_cols:
        conn.execute("ALTER TABLE orders ADD COLUMN annur_ref TEXT")
    if "annur_status" not in order_cols:
        conn.execute("ALTER TABLE orders ADD COLUMN annur_status TEXT")


def _since(conn: sqlite3.Connection) -> str:
    """Ulanish yoqilgan paytdan oldingi buyurtmalar kassaga yuborilmaydi."""
    row = conn.execute("SELECT value FROM annur_state WHERE key = 'since'").fetchone()
    if row:
        return row["value"]
    since = os.getenv("ANNUR_SYNC_SINCE", "").strip() or now_tashkent().isoformat()
    conn.execute("INSERT INTO annur_state (key, value) VALUES ('since', ?)", (since,))
    return since


def _category_id(conn: sqlite3.Connection, cache: dict[str, int], name: str | None) -> int | None:
    name = (name or "").strip()
    if not name:
        return None
    key = name.lower()
    if key not in cache:
        row = conn.execute("SELECT id FROM categories WHERE LOWER(name) = ?", (key,)).fetchone()
        if row:
            cache[key] = row["id"]
        else:
            cur = conn.execute("INSERT INTO categories (name, is_active) VALUES (?, 1)", (name,))
            cache[key] = int(cur.lastrowid)
    return cache[key]


def apply_catalog(data: dict) -> dict[str, int]:
    """Kassa katalogini bot mahsulotlariga yozadi. Rasm, tavsif va aksiya narxi botda qoladi."""
    stats = {"updated": 0, "created": 0, "hidden": 0}
    if not data.get("live"):
        logger.warning("An-Nur: kassada hali namuna mahsulotlar — katalog olinmadi")
        return stats
    items = data.get("products") or []
    with get_connection() as conn:
        _ensure_schema(conn)
        rows = conn.execute("SELECT id, name, barcode, annur_id FROM products").fetchall()
        by_annur = {r["annur_id"]: r["id"] for r in rows if r["annur_id"] is not None}
        unlinked = [r for r in rows if r["annur_id"] is None]
        by_barcode = {r["barcode"].strip(): r["id"] for r in unlinked if (r["barcode"] or "").strip()}
        by_name = {r["name"].strip().lower(): r["id"] for r in unlinked if r["name"]}
        categories: dict[str, int] = {}
        seen: set[int] = set()
        active_in_kassa = 0

        for p in items:
            annur_id = int(p["id"])
            barcode = (p.get("barcode") or "").strip()
            name = (p.get("name") or "").strip()
            bot_id = by_annur.get(annur_id) or by_barcode.get(barcode) or by_name.get(name.lower())
            kassa_active = bool(p.get("active"))
            stock = max(0, math.floor(float(p.get("stock") or 0)))
            if kassa_active:
                active_in_kassa += 1
            show = 1 if kassa_active and (stock > 0 or not HIDE_OUT_OF_STOCK) else 0
            price = int(round(float(p.get("price") or 0)))
            cat_id = _category_id(conn, categories, p.get("category"))

            if bot_id is None:
                if not kassa_active:
                    continue
                cur = conn.execute(
                    "INSERT INTO products (name, price, category_id, is_active, stock, annur_id) VALUES (?, ?, ?, ?, ?, ?)",
                    (name, price, cat_id, show, stock, annur_id),
                )
                bot_id = int(cur.lastrowid)
                stats["created"] += 1
            else:
                conn.execute(
                    """UPDATE products SET annur_id = ?, name = ?, price = ?, stock = ?, is_active = ?,
                       category_id = COALESCE(?, category_id) WHERE id = ?""",
                    (annur_id, name, price, stock, show, cat_id, bot_id),
                )
                stats["updated"] += 1
            seen.add(bot_id)
            if barcode:
                try:
                    conn.execute("UPDATE products SET barcode = ? WHERE id = ?", (barcode, bot_id))
                except sqlite3.IntegrityError:
                    logger.warning("An-Nur: shtrix-kod %s boshqa mahsulotda bor (bot id=%s)", barcode, bot_id)

        if active_in_kassa >= MIN_CATALOG_FOR_PRUNE and seen:
            marks = ",".join("?" * len(seen))
            cur = conn.execute(
                f"UPDATE products SET is_active = 0 WHERE is_active = 1 AND id NOT IN ({marks})",
                tuple(seen),
            )
            stats["hidden"] = cur.rowcount
    return stats


def _payment(payment_status: str | None) -> str:
    return "otkazma" if payment_status in ("paid", "card_waiting") else "naqd"


def _order_payload(conn: sqlite3.Connection, order: sqlite3.Row) -> dict | None:
    lines = conn.execute(
        """SELECT oi.product_name, oi.price, oi.quantity, p.annur_id
           FROM order_items oi LEFT JOIN products p ON p.id = oi.product_id WHERE oi.order_id = ?""",
        (order["id"],),
    ).fetchall()
    items = [
        {"product_id": l["annur_id"], "qty": l["quantity"], "price": l["price"]}
        for l in lines
        if l["annur_id"] is not None and l["quantity"]
    ]
    if not items:
        return None
    keys = order.keys()
    subtotal = order["subtotal"] if "subtotal" in keys else None
    discount = int(order["discount"] or 0) if "discount" in keys else 0
    bonus = int(order["bonus_spent"] or 0) if "bonus_spent" in keys else 0
    fee = max(0, int(order["price"] or 0) - int(subtotal) + discount + bonus) if subtotal else 0
    note = [f"Telegram bot #{order['id']}"]
    missing = [l["product_name"] for l in lines if l["annur_id"] is None]
    if missing:
        note.append("Kassada yo'q: " + ", ".join(missing))
    if discount:
        note.append(f"Promo chegirma: {discount}")
    if bonus:
        note.append(f"Bonus: {bonus}")
    note.append(f"Mijoz to'laydi: {int(order['price'] or 0)}")
    return {
        # Sana qo'shilgan: bot bazasi qayta yaratilsa ham eski kassa buyurtmasi bilan to'qnashmaydi.
        "external_ref": f"bot-{order['id']}-{str(order['created_at'])[:19]}",
        "customer_name": order["full_name"] or "Bot mijozi",
        "phone": order["phone"] or "—",
        "address": order["delivery_address"] or "—",
        "delivery_fee": fee,
        "note": ". ".join(note),
        "items": items,
    }


async def _notify_admins(context: ContextTypes.DEFAULT_TYPE, text: str) -> None:
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(admin_id, text)
        except Exception:
            logger.debug("An-Nur: admin %s ga xabar yuborilmadi", admin_id)


async def push_orders(session: aiohttp.ClientSession, context: ContextTypes.DEFAULT_TYPE) -> None:
    with get_connection() as conn:
        _ensure_schema(conn)
        since = _since(conn)
        pending = conn.execute(
            """SELECT o.*, u.full_name FROM orders o LEFT JOIN users u ON u.user_id = o.user_id
               WHERE o.annur_ref IS NULL AND o.created_at >= ? AND o.status != 'cancelled'
               ORDER BY o.id LIMIT 20""",
            (since,),
        ).fetchall()
        payloads = [(o["id"], _order_payload(conn, o)) for o in pending]

    for order_id, payload in payloads:
        if payload is None:
            with get_connection() as conn:
                conn.execute("UPDATE orders SET annur_ref = 'skip' WHERE id = ?", (order_id,))
            continue
        async with session.post(f"{ANNUR_URL}/api/integration/orders", json=payload, headers=_headers()) as resp:
            if resp.status == 200:
                with get_connection() as conn:
                    conn.execute(
                        "UPDATE orders SET annur_ref = ?, annur_status = 'new' WHERE id = ?",
                        (payload["external_ref"], order_id),
                    )
            elif 400 <= resp.status < 500 and resp.status not in (401, 403, 429):
                error = (await resp.text())[:200]
                with get_connection() as conn:
                    conn.execute("UPDATE orders SET annur_ref = 'error' WHERE id = ?", (order_id,))
                logger.warning("An-Nur: buyurtma #%s qabul qilinmadi: %s", order_id, error)
                await _notify_admins(context, f"⚠️ Buyurtma #{order_id} kassaga tushmadi: {error}")
            else:
                logger.warning("An-Nur: buyurtma #%s yuborilmadi (HTTP %s), keyin qayta urinadi", order_id, resp.status)
                return


async def push_statuses(session: aiohttp.ClientSession) -> None:
    with get_connection() as conn:
        _ensure_schema(conn)
        rows = conn.execute(
            """SELECT id, status, payment_status, annur_ref FROM orders
               WHERE annur_ref LIKE 'bot-%' AND status IN ('delivered', 'cancelled')
                 AND COALESCE(annur_status, '') != status LIMIT 50"""
        ).fetchall()

    for r in rows:
        body = {
            "external_ref": r["annur_ref"],
            "status": KASSA_STATUS[r["status"]],
            "payment_method": _payment(r["payment_status"]),
        }
        async with session.post(f"{ANNUR_URL}/api/integration/orders/status", json=body, headers=_headers()) as resp:
            if resp.status == 200 or resp.status == 404:
                with get_connection() as conn:
                    conn.execute("UPDATE orders SET annur_status = ? WHERE id = ?", (r["status"], r["id"]))
            else:
                logger.warning("An-Nur: #%s holati yuborilmadi (HTTP %s)", r["id"], resp.status)
                return


async def pull_catalog(session: aiohttp.ClientSession) -> None:
    async with session.get(f"{ANNUR_URL}/api/integration/products", headers=_headers()) as resp:
        if resp.status != 200:
            logger.warning("An-Nur: katalog olinmadi (HTTP %s)", resp.status)
            return
        data = await resp.json()
    stats = apply_catalog(data)
    logger.info("An-Nur katalog: %s", stats)


async def annur_sync_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    runs = context.job.data["runs"] = context.job.data.get("runs", 0) + 1
    try:
        async with aiohttp.ClientSession(timeout=TIMEOUT) as session:
            await push_orders(session, context)
            await push_statuses(session)
            if runs % PULL_EVERY_RUNS == 1:
                await pull_catalog(session)
    except Exception:
        logger.exception("An-Nur sinxronlash xatosi")


def setup_annur_sync(application: Application) -> None:
    if not enabled():
        return
    jq = application.job_queue
    if jq is None:
        return
    jq.run_repeating(annur_sync_job, interval=60, first=20, name="annur_sync", data={})
    logger.info("An-Nur sinxronlash yoqildi: %s", ANNUR_URL)
