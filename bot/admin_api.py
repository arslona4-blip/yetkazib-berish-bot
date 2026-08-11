"""Admin PWA API — professional boshqaruv paneli."""

from __future__ import annotations

import logging
import os
from typing import Any

from aiohttp import web

from bot.config import (
    ADMIN_IDS,
    LOW_STOCK_THRESHOLD,
    ORDER_STATUS_LABELS,
    PAYMENT_STATUS_LABELS,
    SHOP_NAME,
)
from bot.database import (
    adjust_product_stock,
    format_order,
    get_daily_report,
    get_inventory_categories,
    get_inventory_products,
    get_order,
    get_orders_by_status,
    get_product_by_id,
    get_products,
    get_queue_orders,
    get_stats,
    get_stock_movements,
    get_warehouse_summary,
    set_product_stock,
    update_order_status,
)

logger = logging.getLogger(__name__)

ADMIN_APP_PIN = os.getenv("ADMIN_APP_PIN", "").strip()


def _require_admin(request: web.Request) -> int:
    """Telegram initData (imzolangan) yoki PIN+admin_id. Qaytaradi: admin user_id."""
    from bot.webapp import extract_user_from_init_data, validate_webapp_init_data

    init_data = (
        request.headers.get("X-Telegram-Init-Data")
        or request.headers.get("X-Init-Data")
        or request.rel_url.query.get("initData")
        or ""
    ).strip()
    if init_data:
        if not validate_webapp_init_data(init_data):
            raise web.HTTPForbidden(text="initData yaroqsiz")
        user_id, _, _ = extract_user_from_init_data(init_data)
        if user_id and user_id in ADMIN_IDS:
            return int(user_id)
        raise web.HTTPForbidden(text="Admin emas")

    pin = (request.headers.get("X-Admin-Pin") or "").strip()
    admin_raw = (request.headers.get("X-Admin-Id") or "").strip()
    if ADMIN_APP_PIN and pin == ADMIN_APP_PIN and admin_raw.isdigit():
        admin_id = int(admin_raw)
        if admin_id in ADMIN_IDS:
            return admin_id
        raise web.HTTPForbidden(text="Bu ID admin ro'yxatida yo'q")

    raise web.HTTPUnauthorized(
        text="Kirish: Telegram Mini App yoki Admin PIN kerak"
    )


def _order_dict(row) -> dict[str, Any]:
    keys = row.keys()
    return {
        "id": int(row["id"]),
        "user_id": int(row["user_id"]),
        "status": row["status"],
        "status_label": ORDER_STATUS_LABELS.get(row["status"], row["status"]),
        "payment_status": row["payment_status"],
        "payment_label": PAYMENT_STATUS_LABELS.get(
            row["payment_status"], row["payment_status"]
        ),
        "price": int(row["price"] or 0),
        "phone": row["phone"] or "",
        "delivery_address": row["delivery_address"] or "",
        "pickup_address": row["pickup_address"] or "",
        "description": row["description"] or "",
        "delivery_slot": row["delivery_slot"] if "delivery_slot" in keys else "",
        "created_at": row["created_at"] or "",
        "text": format_order(row),
    }


def _product_dict(row) -> dict[str, Any]:
    keys = row.keys()
    return {
        "id": int(row["id"]),
        "name": row["name"],
        "price": int(row["price"] or 0),
        "stock": int(row["stock"] or 0) if "stock" in keys else 0,
        "category_id": int(row["category_id"]) if row["category_id"] else 0,
        "category_name": (
            row["category_name"] if "category_name" in keys and row["category_name"] else "Toifasiz"
        ),
        "is_active": bool(row["is_active"]),
    }


async def admin_me(request: web.Request) -> web.Response:
    admin_id = _require_admin(request)
    return web.json_response(
        {
            "ok": True,
            "admin_id": admin_id,
            "shop_name": SHOP_NAME,
            "pin_login_enabled": bool(ADMIN_APP_PIN),
        }
    )


async def admin_stats(request: web.Request) -> web.Response:
    _require_admin(request)
    stats = get_stats()
    wh = get_warehouse_summary()
    report = get_daily_report()
    return web.json_response(
        {
            "ok": True,
            "stats": stats,
            "warehouse": wh,
            "daily": {
                "orders_count": report.get("orders_count", 0),
                "revenue": report.get("orders_sum", 0),
                "date": report.get("date", ""),
            },
            "low_stock_threshold": LOW_STOCK_THRESHOLD,
        }
    )


async def admin_orders(request: web.Request) -> web.Response:
    _require_admin(request)
    status = (request.rel_url.query.get("status") or "new").strip().lower()
    if status == "active":
        orders = get_queue_orders(["accepted", "in_delivery"], limit=50)
    elif status == "delivered":
        orders = get_orders_by_status("delivered", limit=40)
    elif status == "cancelled":
        orders = get_orders_by_status("cancelled", limit=40)
    else:
        orders = get_queue_orders(["new"], limit=50)
    return web.json_response(
        {
            "ok": True,
            "status": status,
            "orders": [_order_dict(o) for o in orders],
        }
    )


async def admin_order_status(request: web.Request) -> web.Response:
    admin_id = _require_admin(request)
    try:
        order_id = int(request.match_info["order_id"])
    except ValueError as exc:
        raise web.HTTPBadRequest(text="order_id noto'g'ri") from exc
    try:
        body = await request.json()
    except Exception as exc:
        raise web.HTTPBadRequest(text="JSON noto'g'ri") from exc
    status = str(body.get("status") or "").strip()
    if status not in ORDER_STATUS_LABELS:
        raise web.HTTPBadRequest(text="status noto'g'ri")
    order = get_order(order_id)
    if not order:
        raise web.HTTPNotFound(text="Buyurtma topilmadi")
    update_order_status(order_id, status)
    order = get_order(order_id)
    logger.info("Admin %s order #%s -> %s", admin_id, order_id, status)
    return web.json_response({"ok": True, "order": _order_dict(order)})


async def admin_warehouse_summary(request: web.Request) -> web.Response:
    _require_admin(request)
    return web.json_response({"ok": True, **get_warehouse_summary()})


async def admin_warehouse_categories(request: web.Request) -> web.Response:
    _require_admin(request)
    low_only = request.rel_url.query.get("low_only") == "1"
    cats = get_inventory_categories(low_only=low_only)
    return web.json_response({"ok": True, "categories": cats})


async def admin_warehouse_products(request: web.Request) -> web.Response:
    _require_admin(request)
    low_only = request.rel_url.query.get("low_only") == "1"
    cat_raw = request.rel_url.query.get("category_id")
    category_id = int(cat_raw) if cat_raw is not None and cat_raw != "" else None
    products = get_inventory_products(
        low_only=low_only, category_id=category_id, limit=200
    )
    return web.json_response(
        {"ok": True, "products": [_product_dict(p) for p in products]}
    )


async def admin_warehouse_movements(request: web.Request) -> web.Response:
    _require_admin(request)
    limit = min(100, max(1, int(request.rel_url.query.get("limit") or 40)))
    reason = request.rel_url.query.get("reason") or None
    pid_raw = request.rel_url.query.get("product_id")
    product_id = int(pid_raw) if pid_raw and pid_raw.isdigit() else None
    moves = get_stock_movements(limit=limit, product_id=product_id, reason=reason)
    payload = []
    for m in moves:
        payload.append(
            {
                "id": int(m["id"]),
                "product_id": int(m["product_id"]),
                "product_name": m["product_name"] or "",
                "delta": int(m["delta"]),
                "stock_after": int(m["stock_after"]),
                "reason": m["reason"],
                "note": m["note"] or "",
                "order_id": m["order_id"],
                "admin_id": m["admin_id"],
                "created_at": m["created_at"] or "",
            }
        )
    return web.json_response({"ok": True, "movements": payload})


async def admin_warehouse_stock(request: web.Request) -> web.Response:
    admin_id = _require_admin(request)
    try:
        body = await request.json()
    except Exception as exc:
        raise web.HTTPBadRequest(text="JSON noto'g'ri") from exc
    try:
        product_id = int(body.get("product_id"))
        qty = int(body.get("qty"))
    except (TypeError, ValueError) as exc:
        raise web.HTTPBadRequest(text="product_id/qty noto'g'ri") from exc
    mode = str(body.get("mode") or "adjust").strip().lower()
    note = str(body.get("note") or "").strip()
    if qty < 0:
        raise web.HTTPBadRequest(text="qty musbat bo'lsin")
    product = get_product_by_id(product_id)
    if not product:
        raise web.HTTPNotFound(text="Mahsulot topilmadi")
    try:
        if mode == "in":
            stock = adjust_product_stock(
                product_id, qty, reason="in", note=note, admin_id=admin_id
            )
        elif mode == "out":
            stock = adjust_product_stock(
                product_id, -qty, reason="out", note=note, admin_id=admin_id
            )
        elif mode == "inventory":
            stock = set_product_stock(
                product_id, qty, reason="inventory", note=note, admin_id=admin_id
            )
        elif mode == "adjust":
            delta = int(body.get("delta") or qty)
            stock = adjust_product_stock(
                product_id, delta, reason="adjust", note=note, admin_id=admin_id
            )
        else:
            raise web.HTTPBadRequest(text="mode: in|out|inventory|adjust")
    except ValueError as exc:
        raise web.HTTPBadRequest(text=str(exc)) from exc
    return web.json_response(
        {
            "ok": True,
            "product_id": product_id,
            "name": product["name"],
            "stock": stock,
        }
    )


async def admin_products(request: web.Request) -> web.Response:
    _require_admin(request)
    products = get_products(active_only=False)
    # attach category names via inventory query is easier
    inv = {p["id"]: p for p in get_inventory_products(limit=500)}
    out = []
    for p in products:
        d = _product_dict(p)
        if p["id"] in inv:
            d["category_name"] = inv[p["id"]]["category_name"] or "Toifasiz"
            d["stock"] = int(inv[p["id"]]["stock"] or 0)
        out.append(d)
    return web.json_response({"ok": True, "products": out})


def register_admin_routes(app: web.Application) -> None:
    app.router.add_get("/api/admin/me", admin_me)
    app.router.add_get("/api/admin/stats", admin_stats)
    app.router.add_get("/api/admin/orders", admin_orders)
    app.router.add_post("/api/admin/orders/{order_id}/status", admin_order_status)
    app.router.add_get("/api/admin/warehouse/summary", admin_warehouse_summary)
    app.router.add_get("/api/admin/warehouse/categories", admin_warehouse_categories)
    app.router.add_get("/api/admin/warehouse/products", admin_warehouse_products)
    app.router.add_get("/api/admin/warehouse/movements", admin_warehouse_movements)
    app.router.add_post("/api/admin/warehouse/stock", admin_warehouse_stock)
    app.router.add_get("/api/admin/products", admin_products)
