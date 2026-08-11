"""Admin PWA API — professional boshqaruv paneli."""

from __future__ import annotations

import logging
import os
from typing import Any

from aiohttp import web

from bot.config import (
    ADMIN_IDS,
    BONUS_PERCENT,
    LOW_STOCK_THRESHOLD,
    ORDER_STATUS_LABELS,
    PAYMENT_STATUS_LABELS,
    SHOP_NAME,
)
from bot.database import (
    add_bonus,
    adjust_product_stock,
    create_contact,
    delete_order,
    export_products_csv,
    format_order,
    get_all_user_ids,
    get_contact,
    get_daily_report,
    get_inventory_categories,
    get_inventory_products,
    get_order,
    get_order_items,
    get_orders_by_payment,
    get_orders_by_status,
    get_product_by_id,
    get_products,
    get_queue_orders,
    get_stats,
    get_stock_movements,
    get_warehouse_summary,
    import_products_csv,
    list_contacts,
    search_orders,
    set_product_active,
    set_product_stock,
    update_contact,
    update_payment_status,
    update_product_price,
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


def _item_dict(row) -> dict[str, Any]:
    return {
        "id": int(row["id"]),
        "product_id": int(row["product_id"]) if row["product_id"] else None,
        "product_name": row["product_name"] or "",
        "price": int(row["price"] or 0),
        "quantity": int(row["quantity"] or 0),
        "line_total": int(row["price"] or 0) * int(row["quantity"] or 0),
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
            row["category_name"]
            if "category_name" in keys and row["category_name"]
            else "Toifasiz"
        ),
        "is_active": bool(row["is_active"]),
    }


def _daily_payload(report: dict[str, Any]) -> dict[str, Any]:
    top = []
    for row in report.get("top") or []:
        top.append(
            {
                "product_name": row["product_name"],
                "qty": int(row["qty"] or 0),
            }
        )
    return {
        "date": report.get("date", ""),
        "orders_count": report.get("orders_count", 0),
        "revenue": report.get("orders_sum", 0),
        "paid_count": report.get("paid_count", 0),
        "paid_sum": report.get("paid_sum", 0),
        "waiting_count": report.get("waiting_count", 0),
        "waiting_sum": report.get("waiting_sum", 0),
        "top": top,
    }


async def _notify_user(user_id: int, text: str, reply_markup=None) -> None:
    from bot.webapp import get_bot

    bot = get_bot()
    if bot is None:
        return
    try:
        await bot.send_message(chat_id=user_id, text=text, reply_markup=reply_markup)
    except Exception as exc:
        logger.warning("Mijoz xabar xatosi %s: %s", user_id, exc)


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
    waiting = get_orders_by_payment("card_waiting", limit=50)
    return web.json_response(
        {
            "ok": True,
            "stats": stats,
            "warehouse": wh,
            "daily": _daily_payload(report),
            "payments_waiting": len(waiting),
            "low_stock_threshold": LOW_STOCK_THRESHOLD,
        }
    )


async def admin_orders(request: web.Request) -> web.Response:
    _require_admin(request)
    status = (request.rel_url.query.get("status") or "new").strip().lower()
    q = (request.rel_url.query.get("q") or "").strip()
    if q:
        orders = search_orders(q, limit=40)
    elif status == "active":
        orders = get_queue_orders(["accepted", "in_delivery"], limit=50)
    elif status == "delivered":
        orders = get_orders_by_status("delivered", limit=40)
    elif status == "cancelled":
        orders = get_orders_by_status("cancelled", limit=40)
    elif status == "payments":
        orders = get_orders_by_payment("card_waiting", limit=50)
    else:
        orders = get_queue_orders(["new"], limit=50)
    return web.json_response(
        {
            "ok": True,
            "status": status,
            "q": q,
            "orders": [_order_dict(o) for o in orders],
        }
    )


async def admin_order_detail(request: web.Request) -> web.Response:
    _require_admin(request)
    try:
        order_id = int(request.match_info["order_id"])
    except ValueError as exc:
        raise web.HTTPBadRequest(text="order_id noto'g'ri") from exc
    order = get_order(order_id)
    if not order:
        raise web.HTTPNotFound(text="Buyurtma topilmadi")
    items = [_item_dict(i) for i in get_order_items(order_id)]
    return web.json_response(
        {"ok": True, "order": _order_dict(order), "items": items}
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

    text = (
        f"🔔 Buyurtma #{order_id} holati yangilandi:\n"
        f"{format_order(order)}"
    )
    markup = None
    if order["payment_status"] in {"pending", "rejected"}:
        from bot.keyboards import payment_keyboard

        text += "\n\nTo'lov qilish uchun pastdagi tugmalardan foydalaning:"
        markup = payment_keyboard(order_id)
    await _notify_user(int(order["user_id"]), text, markup)
    if status == "delivered":
        try:
            from bot.i18n import get_user_lang, t
            from bot.keyboards import rating_keyboard

            lang = get_user_lang(int(order["user_id"]))
            await _notify_user(
                int(order["user_id"]),
                t("rating_ask", lang, order_id=order_id),
                rating_keyboard(order_id),
            )
        except Exception as exc:
            logger.warning("Rating so'rov xato: %s", exc)

    return web.json_response({"ok": True, "order": _order_dict(order)})


async def admin_order_payment(request: web.Request) -> web.Response:
    admin_id = _require_admin(request)
    try:
        order_id = int(request.match_info["order_id"])
    except ValueError as exc:
        raise web.HTTPBadRequest(text="order_id noto'g'ri") from exc
    try:
        body = await request.json()
    except Exception as exc:
        raise web.HTTPBadRequest(text="JSON noto'g'ri") from exc
    action = str(body.get("action") or "").strip().lower()
    order = get_order(order_id)
    if not order:
        raise web.HTTPNotFound(text="Buyurtma topilmadi")
    if action == "confirm":
        update_payment_status(order_id, "paid")
        order = get_order(order_id)
        points = max(1, int(order["price"] * BONUS_PERCENT / 100))
        add_bonus(int(order["user_id"]), points)
        await _notify_user(
            int(order["user_id"]),
            f"✅ To'lovingiz tasdiqlandi!\nBuyurtma #{order_id} qabul qilindi.",
        )
    elif action == "reject":
        update_payment_status(order_id, "rejected")
        order = get_order(order_id)
        from bot.keyboards import payment_keyboard

        await _notify_user(
            int(order["user_id"]),
            f"❌ Buyurtma #{order_id} to'lovi tasdiqlanmadi.\n"
            "Qayta to'lov qiling yoki admin bilan bog'laning.",
            payment_keyboard(order_id),
        )
    else:
        raise web.HTTPBadRequest(text="action: confirm|reject")
    logger.info("Admin %s payment #%s -> %s", admin_id, order_id, action)
    return web.json_response({"ok": True, "order": _order_dict(order)})


async def admin_order_delete(request: web.Request) -> web.Response:
    admin_id = _require_admin(request)
    try:
        order_id = int(request.match_info["order_id"])
    except ValueError as exc:
        raise web.HTTPBadRequest(text="order_id noto'g'ri") from exc
    if not delete_order(order_id):
        raise web.HTTPNotFound(text="Buyurtma topilmadi")
    logger.info("Admin %s deleted order #%s", admin_id, order_id)
    return web.json_response({"ok": True, "deleted": order_id})


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
    inv = {p["id"]: p for p in get_inventory_products(limit=500)}
    out = []
    for p in products:
        d = _product_dict(p)
        if p["id"] in inv:
            d["category_name"] = inv[p["id"]]["category_name"] or "Toifasiz"
            d["stock"] = int(inv[p["id"]]["stock"] or 0)
        out.append(d)
    return web.json_response({"ok": True, "products": out})


async def admin_product_patch(request: web.Request) -> web.Response:
    admin_id = _require_admin(request)
    try:
        product_id = int(request.match_info["product_id"])
    except ValueError as exc:
        raise web.HTTPBadRequest(text="product_id noto'g'ri") from exc
    product = get_product_by_id(product_id)
    if not product:
        raise web.HTTPNotFound(text="Mahsulot topilmadi")
    try:
        body = await request.json()
    except Exception as exc:
        raise web.HTTPBadRequest(text="JSON noto'g'ri") from exc
    if "price" in body:
        try:
            price = int(body["price"])
        except (TypeError, ValueError) as exc:
            raise web.HTTPBadRequest(text="price noto'g'ri") from exc
        if price < 0:
            raise web.HTTPBadRequest(text="price musbat bo'lsin")
        update_product_price(product_id, price)
    if "is_active" in body:
        set_product_active(product_id, bool(body["is_active"]))
    product = get_product_by_id(product_id)
    logger.info("Admin %s patched product #%s", admin_id, product_id)
    return web.json_response({"ok": True, "product": _product_dict(product)})


def _contact_dict(c: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": int(c["id"]),
        "name": c.get("name") or "",
        "phone": c.get("phone") or "",
        "note": c.get("note") or "",
        "telegram_user_id": c.get("telegram_user_id"),
        "created_at": c.get("created_at") or "",
        "updated_at": c.get("updated_at") or "",
    }


async def admin_broadcast(request: web.Request) -> web.Response:
    admin_id = _require_admin(request)
    try:
        body = await request.json()
    except Exception as exc:
        raise web.HTTPBadRequest(text="JSON noto'g'ri") from exc
    text = str(body.get("text") or "").strip()
    if len(text) < 2:
        raise web.HTTPBadRequest(text="Matn juda qisqa")
    if len(text) > 3500:
        raise web.HTTPBadRequest(text="Matn juda uzun (3500 belgidan oshmasin)")
    from bot.webapp import get_bot

    bot = get_bot()
    if bot is None:
        raise web.HTTPServiceUnavailable(text="Bot ulanmagan — keyinroq urinib ko'ring")
    users = get_all_user_ids()
    ok = 0
    fail = 0
    message = f"📣 {SHOP_NAME}\n\n{text}"
    for uid in users:
        try:
            await bot.send_message(uid, message)
            ok += 1
        except Exception:
            fail += 1
    logger.info("Admin %s broadcast ok=%s fail=%s", admin_id, ok, fail)
    return web.json_response(
        {"ok": True, "sent": ok, "failed": fail, "total": len(users)}
    )


async def admin_products_export(request: web.Request) -> web.Response:
    _require_admin(request)
    csv_text = export_products_csv()
    return web.Response(
        text=csv_text,
        content_type="text/csv",
        headers={
            "Content-Disposition": 'attachment; filename="products.csv"',
        },
    )


async def admin_products_import(request: web.Request) -> web.Response:
    admin_id = _require_admin(request)
    ctype = (request.headers.get("Content-Type") or "").lower()
    if "multipart/form-data" in ctype:
        reader = await request.multipart()
        field = await reader.next()
        if field is None:
            raise web.HTTPBadRequest(text="Fayl topilmadi")
        data = await field.read(decode=False)
        text = data.decode("utf-8", errors="ignore")
    else:
        try:
            body = await request.json()
            text = str(body.get("csv") or body.get("text") or "")
        except Exception as exc:
            raw = await request.text()
            if not raw.strip():
                raise web.HTTPBadRequest(text="CSV yuboring") from exc
            text = raw
    if not text.strip():
        raise web.HTTPBadRequest(text="CSV bo'sh")
    count = import_products_csv(text)
    logger.info("Admin %s imported %s product rows", admin_id, count)
    return web.json_response({"ok": True, "imported": count})


async def admin_contacts_list(request: web.Request) -> web.Response:
    _require_admin(request)
    contacts = [_contact_dict(c) for c in list_contacts()]
    return web.json_response({"ok": True, "contacts": contacts})


async def admin_contacts_create(request: web.Request) -> web.Response:
    admin_id = _require_admin(request)
    try:
        body = await request.json()
    except Exception as exc:
        raise web.HTTPBadRequest(text="JSON noto'g'ri") from exc
    name = str(body.get("name") or "").strip()
    if not name:
        raise web.HTTPBadRequest(text="Ism kerak")
    phone = str(body.get("phone") or "").strip()
    note = str(body.get("note") or "").strip()
    cid = create_contact(name=name, phone=phone or None, note=note)
    contact = get_contact(cid)
    logger.info("Admin %s created contact #%s", admin_id, cid)
    payload = {
        "id": cid,
        "name": contact["name"] if contact else name,
        "phone": (contact["phone"] if contact else phone) or "",
        "note": (contact["note"] if contact else note) or "",
        "telegram_user_id": contact["telegram_user_id"] if contact else None,
        "created_at": contact["created_at"] if contact else "",
        "updated_at": contact["updated_at"] if contact else "",
    }
    return web.json_response({"ok": True, "contact": payload})


async def admin_contacts_update(request: web.Request) -> web.Response:
    admin_id = _require_admin(request)
    try:
        contact_id = int(request.match_info["contact_id"])
    except ValueError as exc:
        raise web.HTTPBadRequest(text="contact_id noto'g'ri") from exc
    contact = get_contact(contact_id)
    if not contact:
        raise web.HTTPNotFound(text="Kontakt topilmadi")
    try:
        body = await request.json()
    except Exception as exc:
        raise web.HTTPBadRequest(text="JSON noto'g'ri") from exc
    update_contact(
        contact_id,
        name=str(body["name"]).strip() if "name" in body else None,
        phone=str(body["phone"]).strip() if "phone" in body else None,
        note=str(body["note"]).strip() if "note" in body else None,
    )
    contact = get_contact(contact_id)
    logger.info("Admin %s updated contact #%s", admin_id, contact_id)
    return web.json_response(
        {
            "ok": True,
            "contact": {
                "id": int(contact["id"]),
                "name": contact["name"] or "",
                "phone": contact["phone"] or "",
                "note": contact["note"] or "",
                "telegram_user_id": contact["telegram_user_id"],
                "created_at": contact["created_at"] or "",
                "updated_at": contact["updated_at"] or "",
            },
        }
    )


def register_admin_routes(app: web.Application) -> None:
    app.router.add_get("/api/admin/me", admin_me)
    app.router.add_get("/api/admin/stats", admin_stats)
    app.router.add_get("/api/admin/orders", admin_orders)
    app.router.add_get("/api/admin/orders/{order_id}", admin_order_detail)
    app.router.add_post("/api/admin/orders/{order_id}/status", admin_order_status)
    app.router.add_post("/api/admin/orders/{order_id}/payment", admin_order_payment)
    app.router.add_delete("/api/admin/orders/{order_id}", admin_order_delete)
    app.router.add_get("/api/admin/warehouse/summary", admin_warehouse_summary)
    app.router.add_get("/api/admin/warehouse/categories", admin_warehouse_categories)
    app.router.add_get("/api/admin/warehouse/products", admin_warehouse_products)
    app.router.add_get("/api/admin/warehouse/movements", admin_warehouse_movements)
    app.router.add_post("/api/admin/warehouse/stock", admin_warehouse_stock)
    app.router.add_get("/api/admin/products", admin_products)
    app.router.add_get("/api/admin/products/export", admin_products_export)
    app.router.add_post("/api/admin/products/import", admin_products_import)
    app.router.add_patch("/api/admin/products/{product_id}", admin_product_patch)
    app.router.add_post("/api/admin/broadcast", admin_broadcast)
    app.router.add_get("/api/admin/contacts", admin_contacts_list)
    app.router.add_post("/api/admin/contacts", admin_contacts_create)
    app.router.add_patch("/api/admin/contacts/{contact_id}", admin_contacts_update)
