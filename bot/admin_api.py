"""Admin PWA API — professional boshqaruv paneli."""

from __future__ import annotations

import logging
from typing import Any

from aiohttp import web

from bot.config import (
    ADMIN_APP_PIN,
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
    calc_promo_discount,
    consume_admin_login_code,
    create_admin_session,
    create_category,
    create_contact,
    create_order,
    create_product,
    decrease_stock_for_order_items,
    delete_order,
    export_products_csv,
    format_order,
    get_admin_id_by_session,
    get_all_user_ids,
    get_categories,
    get_category,
    get_contact,
    get_contact_balance,
    get_daily_report,
    get_inventory_categories,
    get_inventory_products,
    get_order,
    get_order_items,
    get_orders_by_payment,
    get_orders_by_status,
    get_product_by_barcode,
    get_product_by_id,
    get_products,
    get_promo_any,
    get_queue_orders,
    get_range_report,
    get_stats,
    get_stock_movements,
    get_warehouse_summary,
    import_products_csv,
    list_contacts,
    list_promos,
    revoke_admin_session,
    save_order_items_direct,
    search_orders,
    set_product_active,
    set_product_stock,
    set_promo_active,
    update_contact,
    update_payment_status,
    update_product_fields,
    update_product_price,
    update_order_status,
    upsert_promo,
)

logger = logging.getLogger(__name__)


def _require_admin(request: web.Request) -> int:
    """Telegram initData, session token, OTP/PIN. Qaytaradi: admin user_id."""
    from bot.webapp import extract_user_from_init_data

    init_data = (
        request.headers.get("X-Telegram-Init-Data")
        or request.headers.get("X-Init-Data")
        or request.rel_url.query.get("initData")
        or ""
    ).strip()
    if init_data:
        user_id, _, _ = extract_user_from_init_data(init_data)
        if user_id and user_id in ADMIN_IDS:
            return int(user_id)
        if user_id:
            raise web.HTTPForbidden(text="Admin emas — ADMIN_IDS ga qo'shing")
        raise web.HTTPForbidden(text="initData yaroqsiz yoki eskirgan")

    session = (
        request.headers.get("X-Admin-Session")
        or request.rel_url.query.get("session")
        or ""
    ).strip()
    if session:
        admin_id = get_admin_id_by_session(session)
        if admin_id and admin_id in ADMIN_IDS:
            return admin_id
        raise web.HTTPUnauthorized(text="Sessiya eskirgan — yangi kod oling")

    pin = (request.headers.get("X-Admin-Pin") or "").strip()
    code = (request.headers.get("X-Admin-Code") or "").strip()
    admin_raw = (request.headers.get("X-Admin-Id") or "").strip()
    if admin_raw.isdigit():
        admin_id = int(admin_raw)
        if admin_id not in ADMIN_IDS:
            raise web.HTTPForbidden(text="Bu ID admin ro'yxatida yo'q")
        if code and consume_admin_login_code(admin_id, code):
            return admin_id
        if ADMIN_APP_PIN and pin == ADMIN_APP_PIN:
            return admin_id
        if code:
            raise web.HTTPUnauthorized(text="Kod noto'g'ri yoki eskirgan")
        if pin:
            if not ADMIN_APP_PIN:
                raise web.HTTPUnauthorized(
                    text="PIN sozlanmagan. Botdan «🔑 Kirish kodi» oling."
                )
            raise web.HTTPUnauthorized(text="PIN noto'g'ri")

    raise web.HTTPUnauthorized(
        text="Botdan «🔑 Kirish kodi» oling yoki «🖥 Admin ilova»ni Telegram ichida oching."
    )


async def admin_login(request: web.Request) -> web.Response:
    """Brauzer: Admin ID + botdan kod → session token."""
    try:
        body = await request.json()
    except Exception as exc:
        raise web.HTTPBadRequest(text="JSON noto'g'ri") from exc
    admin_raw = str(body.get("admin_id") or "").strip()
    code = str(body.get("code") or "").strip()
    if not admin_raw.isdigit():
        raise web.HTTPBadRequest(text="Admin ID kerak")
    admin_id = int(admin_raw)
    if admin_id not in ADMIN_IDS:
        raise web.HTTPForbidden(text="Bu ID admin ro'yxatida yo'q")
    if not consume_admin_login_code(admin_id, code):
        raise web.HTTPUnauthorized(text="Kod noto'g'ri yoki eskirgan")
    token = create_admin_session(admin_id)
    logger.info("Admin %s login via OTP session", admin_id)
    return web.json_response(
        {
            "ok": True,
            "admin_id": admin_id,
            "session": token,
            "shop_name": SHOP_NAME,
        }
    )


async def admin_logout(request: web.Request) -> web.Response:
    session = (request.headers.get("X-Admin-Session") or "").strip()
    if session:
        revoke_admin_session(session)
    return web.json_response({"ok": True})


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
        "barcode": (row["barcode"] if "barcode" in keys and row["barcode"] else "")
        or "",
        "description": (
            row["description"] if "description" in keys and row["description"] else ""
        )
        or "",
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


def _promo_dict(row) -> dict[str, Any]:
    return {
        "code": row["code"],
        "discount_percent": int(row["discount_percent"] or 0),
        "discount_amount": int(row["discount_amount"] or 0),
        "min_order": int(row["min_order"] or 0),
        "is_active": bool(row["is_active"]),
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
    try:
        kwargs: dict[str, Any] = {}
        if "name" in body:
            kwargs["name"] = str(body["name"]).strip()
        if "price" in body:
            price = int(body["price"])
            if price < 0:
                raise web.HTTPBadRequest(text="price musbat bo'lsin")
            kwargs["price"] = price
            update_product_price(product_id, price)
        if "description" in body:
            kwargs["description"] = str(body["description"] or "")
        if "category_id" in body:
            kwargs["category_id"] = body["category_id"]
        if "barcode" in body:
            kwargs["barcode"] = body["barcode"]
        # price already updated above if present; avoid double via fields helper
        fields = {k: v for k, v in kwargs.items() if k != "price"}
        if fields:
            update_product_fields(product_id, **fields)
        if "is_active" in body:
            set_product_active(product_id, bool(body["is_active"]))
        if "stock" in body:
            set_product_stock(
                product_id,
                int(body["stock"]),
                reason="inventory",
                note="Admin panel",
                admin_id=admin_id,
            )
    except ValueError as exc:
        raise web.HTTPBadRequest(text=str(exc)) from exc
    except web.HTTPBadRequest:
        raise
    except (TypeError, ValueError) as exc:
        raise web.HTTPBadRequest(text=str(exc)) from exc
    product = get_product_by_id(product_id)
    logger.info("Admin %s patched product #%s", admin_id, product_id)
    return web.json_response({"ok": True, "product": _product_dict(product)})


async def admin_product_create(request: web.Request) -> web.Response:
    admin_id = _require_admin(request)
    try:
        body = await request.json()
    except Exception as exc:
        raise web.HTTPBadRequest(text="JSON noto'g'ri") from exc
    name = str(body.get("name") or "").strip()
    if not name:
        raise web.HTTPBadRequest(text="Nom kerak")
    try:
        price = int(body.get("price") or 0)
    except (TypeError, ValueError) as exc:
        raise web.HTTPBadRequest(text="price noto'g'ri") from exc
    if price < 0:
        raise web.HTTPBadRequest(text="price musbat bo'lsin")
    cat_raw = body.get("category_id")
    category_id = None
    if cat_raw not in (None, "", 0, "0"):
        try:
            category_id = int(cat_raw)
        except (TypeError, ValueError) as exc:
            raise web.HTTPBadRequest(text="category_id noto'g'ri") from exc
    barcode = str(body.get("barcode") or "").strip() or None
    description = str(body.get("description") or "").strip()
    if barcode:
        existing = get_product_by_barcode(barcode)
        if existing:
            raise web.HTTPBadRequest(
                text=f"Barkod band: #{existing['id']} {existing['name']}"
            )
    stock = 0
    stock_raw = body.get("stock")
    if stock_raw is not None and str(stock_raw).strip() != "":
        try:
            stock = max(0, int(stock_raw))
        except (TypeError, ValueError) as exc:
            raise web.HTTPBadRequest(text="stock noto'g'ri") from exc
    pid = create_product(
        name=name,
        price=price,
        description=description,
        category_id=category_id,
        barcode=barcode,
        stock=stock,
    )
    product = get_product_by_id(pid)
    logger.info("Admin %s created product #%s", admin_id, pid)
    return web.json_response({"ok": True, "product": _product_dict(product)})


async def admin_product_by_barcode(request: web.Request) -> web.Response:
    _require_admin(request)
    code = (request.match_info.get("code") or "").strip()
    if not code:
        raise web.HTTPBadRequest(text="Barkod kerak")
    product = get_product_by_barcode(code)
    if not product:
        raise web.HTTPNotFound(text="Mahsulot topilmadi")
    return web.json_response({"ok": True, "product": _product_dict(product)})


async def admin_categories_list(request: web.Request) -> web.Response:
    _require_admin(request)
    cats = get_categories(active_only=False)
    return web.json_response(
        {
            "ok": True,
            "categories": [
                {
                    "id": int(c["id"]),
                    "name": c["name"],
                    "emoji": (c["emoji"] if "emoji" in c.keys() else "") or "📦",
                    "is_active": bool(c["is_active"]),
                }
                for c in cats
            ],
        }
    )


async def admin_categories_create(request: web.Request) -> web.Response:
    admin_id = _require_admin(request)
    try:
        body = await request.json()
    except Exception as exc:
        raise web.HTTPBadRequest(text="JSON noto'g'ri") from exc
    name = str(body.get("name") or "").strip()
    if not name:
        raise web.HTTPBadRequest(text="Nom kerak")
    emoji = str(body.get("emoji") or "").strip() or None
    try:
        cid = create_category(name, emoji=emoji)
    except ValueError as exc:
        raise web.HTTPBadRequest(text=str(exc)) from exc
    cat = get_category(cid)
    logger.info("Admin %s created category #%s", admin_id, cid)
    return web.json_response(
        {
            "ok": True,
            "id": cid,
            "name": cat["name"] if cat else name,
            "emoji": (cat["emoji"] if cat and "emoji" in cat.keys() else "") or "📦",
        }
    )


async def admin_pos_sale(request: web.Request) -> web.Response:
    """Zifra kassa: do'kondagi sotuv (naqd / karta)."""
    admin_id = _require_admin(request)
    try:
        body = await request.json()
    except Exception as exc:
        raise web.HTTPBadRequest(text="JSON noto'g'ri") from exc
    raw_items = body.get("items") or []
    if not isinstance(raw_items, list) or not raw_items:
        raise web.HTTPBadRequest(text="items kerak")
    payment = str(body.get("payment") or "cash").strip().lower()
    if payment not in {"cash", "card"}:
        raise web.HTTPBadRequest(text="payment: cash|card")
    phone = str(body.get("phone") or "").strip() or "—"
    customer = str(body.get("customer_name") or "").strip() or "Kassa mijoz"
    note = str(body.get("note") or "").strip()
    promo_code = str(body.get("promo_code") or "").strip()
    contact_id = body.get("contact_id")
    cid: int | None = None
    if contact_id not in (None, "", 0, "0"):
        try:
            cid = int(contact_id)
        except (TypeError, ValueError) as exc:
            raise web.HTTPBadRequest(text="contact_id noto'g'ri") from exc
        if not get_contact(cid):
            raise web.HTTPNotFound(text="Kontakt topilmadi")

    lines: list[dict[str, Any]] = []
    subtotal = 0
    for it in raw_items:
        try:
            pid = int(it.get("product_id"))
            qty = int(it.get("quantity") or 1)
        except (TypeError, ValueError, AttributeError) as exc:
            raise web.HTTPBadRequest(text="items format noto'g'ri") from exc
        if qty <= 0:
            raise web.HTTPBadRequest(text="quantity > 0 bo'lsin")
        product = get_product_by_id(pid)
        if not product or not product["is_active"]:
            raise web.HTTPBadRequest(text=f"Mahsulot #{pid} topilmadi")
        stock = int(product["stock"] or 0) if "stock" in product.keys() else 0
        if stock < qty:
            raise web.HTTPBadRequest(
                text=f"{product['name']}: omborda faqat {stock} dona"
            )
        price = int(product["price"] or 0)
        lines.append(
            {
                "product_id": pid,
                "name": product["name"],
                "price": price,
                "quantity": qty,
            }
        )
        subtotal += price * qty

    discount = 0
    promo_used = ""
    if promo_code:
        discount, msg = calc_promo_discount(promo_code, subtotal)
        if msg != "OK":
            raise web.HTTPBadRequest(text=msg)
        promo_used = promo_code.upper()
    total = max(0, subtotal - discount)

    desc_parts = [f"Kassa sotuvi · {customer}"]
    if note:
        desc_parts.append(note)
    order_id = create_order(
        user_id=admin_id,
        pickup_address="Do'kon / Kassa",
        delivery_address="O'zi olib ketdi",
        description=" · ".join(desc_parts),
        phone=phone,
        price=total,
        promo_code=promo_used,
        discount=discount,
        subtotal=subtotal,
    )
    save_order_items_direct(order_id, lines)
    decrease_stock_for_order_items(order_id, lines)
    update_order_status(order_id, "delivered")

    if payment == "card":
        update_payment_status(order_id, "paid")
    else:
        update_payment_status(order_id, "cash")

    order = get_order(order_id)
    logger.info(
        "Admin %s POS sale #%s payment=%s total=%s",
        admin_id,
        order_id,
        payment,
        total,
    )
    return web.json_response(
        {
            "ok": True,
            "order": _order_dict(order),
            "items": [_item_dict(i) for i in get_order_items(order_id)],
            "subtotal": subtotal,
            "discount": discount,
            "total": total,
            "payment": payment,
            "contact_id": cid,
        }
    )


async def admin_promos_list(request: web.Request) -> web.Response:
    _require_admin(request)
    return web.json_response(
        {"ok": True, "promos": [_promo_dict(p) for p in list_promos()]}
    )


async def admin_promos_upsert(request: web.Request) -> web.Response:
    admin_id = _require_admin(request)
    try:
        body = await request.json()
    except Exception as exc:
        raise web.HTTPBadRequest(text="JSON noto'g'ri") from exc
    code = str(body.get("code") or "").strip()
    try:
        code_out = upsert_promo(
            code,
            discount_percent=int(body.get("discount_percent") or 0),
            discount_amount=int(body.get("discount_amount") or 0),
            min_order=int(body.get("min_order") or 0),
            is_active=bool(body.get("is_active", True)),
        )
    except ValueError as exc:
        raise web.HTTPBadRequest(text=str(exc)) from exc
    promo = get_promo_any(code_out)
    logger.info("Admin %s upsert promo %s", admin_id, code_out)
    return web.json_response({"ok": True, "promo": _promo_dict(promo)})


async def admin_promos_patch(request: web.Request) -> web.Response:
    admin_id = _require_admin(request)
    code = (request.match_info.get("code") or "").strip()
    promo = get_promo_any(code)
    if not promo:
        raise web.HTTPNotFound(text="Promo topilmadi")
    try:
        body = await request.json()
    except Exception as exc:
        raise web.HTTPBadRequest(text="JSON noto'g'ri") from exc
    if "is_active" in body and len(body) == 1:
        set_promo_active(code, bool(body["is_active"]))
    else:
        upsert_promo(
            code,
            discount_percent=int(
                body.get("discount_percent", promo["discount_percent"]) or 0
            ),
            discount_amount=int(
                body.get("discount_amount", promo["discount_amount"]) or 0
            ),
            min_order=int(body.get("min_order", promo["min_order"]) or 0),
            is_active=bool(body.get("is_active", promo["is_active"])),
        )
    promo = get_promo_any(code)
    logger.info("Admin %s patched promo %s", admin_id, code)
    return web.json_response({"ok": True, "promo": _promo_dict(promo)})


async def admin_reports(request: web.Request) -> web.Response:
    _require_admin(request)
    from bot.timeutil import now_tashkent

    today = now_tashkent().strftime("%Y-%m-%d")
    date_from = (request.rel_url.query.get("from") or today).strip()
    date_to = (request.rel_url.query.get("to") or today).strip()
    try:
        report = get_range_report(date_from, date_to)
    except ValueError as exc:
        raise web.HTTPBadRequest(text=str(exc)) from exc
    return web.json_response(
        {
            "ok": True,
            "report": report,
            "warehouse": get_warehouse_summary(),
        }
    )


def _contact_dict(c: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": int(c["id"]),
        "name": c.get("name") or "",
        "phone": c.get("phone") or "",
        "note": c.get("note") or "",
        "telegram_user_id": c.get("telegram_user_id"),
        "balance": int(c.get("balance") or 0),
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
    contacts = [_contact_dict(c) for c in list_contacts(debtors_only=False)]
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
        "balance": get_contact_balance(cid),
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
                "balance": get_contact_balance(contact_id),
                "created_at": contact["created_at"] or "",
                "updated_at": contact["updated_at"] or "",
            },
        }
    )


def register_admin_routes(app: web.Application) -> None:
    app.router.add_post("/api/admin/login", admin_login)
    app.router.add_post("/api/admin/logout", admin_logout)
    app.router.add_get("/api/admin/me", admin_me)
    app.router.add_get("/api/admin/stats", admin_stats)
    app.router.add_get("/api/admin/orders", admin_orders)
    app.router.add_get("/api/admin/orders/{order_id}", admin_order_detail)
    app.router.add_post("/api/admin/orders/{order_id}/status", admin_order_status)
    app.router.add_post("/api/admin/orders/{order_id}/payment", admin_order_payment)
    app.router.add_delete("/api/admin/orders/{order_id}", admin_order_delete)
    app.router.add_post("/api/admin/pos/sale", admin_pos_sale)
    app.router.add_get("/api/admin/promos", admin_promos_list)
    app.router.add_post("/api/admin/promos", admin_promos_upsert)
    app.router.add_patch("/api/admin/promos/{code}", admin_promos_patch)
    app.router.add_get("/api/admin/reports", admin_reports)
    app.router.add_get("/api/admin/categories", admin_categories_list)
    app.router.add_post("/api/admin/categories", admin_categories_create)
    app.router.add_get("/api/admin/warehouse/summary", admin_warehouse_summary)
    app.router.add_get("/api/admin/warehouse/categories", admin_warehouse_categories)
    app.router.add_get("/api/admin/warehouse/products", admin_warehouse_products)
    app.router.add_get("/api/admin/warehouse/movements", admin_warehouse_movements)
    app.router.add_post("/api/admin/warehouse/stock", admin_warehouse_stock)
    app.router.add_get("/api/admin/products", admin_products)
    app.router.add_post("/api/admin/products", admin_product_create)
    app.router.add_get("/api/admin/products/export", admin_products_export)
    app.router.add_post("/api/admin/products/import", admin_products_import)
    app.router.add_get("/api/admin/products/barcode/{code}", admin_product_by_barcode)
    app.router.add_patch("/api/admin/products/{product_id}", admin_product_patch)
    app.router.add_post("/api/admin/broadcast", admin_broadcast)
    app.router.add_get("/api/admin/contacts", admin_contacts_list)
    app.router.add_post("/api/admin/contacts", admin_contacts_create)
    app.router.add_patch("/api/admin/contacts/{contact_id}", admin_contacts_update)
