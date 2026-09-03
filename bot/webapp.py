"""Telegram Mini App — aiohttp server."""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import re
import threading
import time
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, unquote

from aiohttp import ClientSession, ClientTimeout, web

from bot.config import (
    ADMIN_IDS,
    BASE_DIR,
    BOT_TOKEN,
    CARD_NUMBER,
    CLICK_LINK,
    DATABASE_PATH,
    DELIVERY_FEE_HIGH,
    DELIVERY_FEE_LOW,
    DELIVERY_FEE_THRESHOLD,
    DELIVERY_PRICE,
    GIFT_DRINK_THRESHOLD,
    MIN_ORDER_AMOUNT,
    PAYME_LINK,
    SHOP_ADDRESS,
    SHOP_HOURS,
    SHOP_NAME,
    SHOP_PHONE,
    SHOP_TELEGRAM,
    WEBAPP_PORT,
    card_payment_enabled,
    payment_link_with_amount,
)
from bot.database import (
    calc_promo_discount,
    create_order,
    effective_product_price,
    format_order,
    get_bonus,
    get_categories,
    get_delivery_fee,
    get_order,
    get_product,
    get_product_by_barcode,
    get_products,
    get_shajara_share,
    get_user,
    get_variant,
    get_variants,
    product_display_price,
    save_order_items_direct,
    save_shajara_share,
    set_user_phone,
    spend_bonus,
    update_payment_status,
    upsert_user,
)
from bot.timeutil import get_delivery_slots

logger = logging.getLogger(__name__)

_bot = None
MINIAPP_DIR = BASE_DIR / "miniapp"
SHAJARA_DIR = BASE_DIR / "shajara"
ADMINAPP_DIR = BASE_DIR / "admin"
ARDUINO_DIR = BASE_DIR / "arduino"
JADVAL_DIR = BASE_DIR / "jadval"
# Maxfiy public path — eski /jadval/ yopilgan. Railway: JADVAL_PATH=jadval-xxxx
JADVAL_PATH = (os.getenv("JADVAL_PATH") or "jadval-fedd3d").strip().strip("/")
KICHKINTOY_DIR = BASE_DIR / "kichkintoy"
SLAYD_DIR = BASE_DIR / "slayd"
PHOTOS_DIR = Path(DATABASE_PATH).resolve().parent / "photos"


def set_bot(bot) -> None:
    global _bot
    _bot = bot


def get_bot():
    return _bot


def photo_cache_path(product_id: int) -> Path:
    return PHOTOS_DIR / f"{product_id}.jpg"


async def fetch_telegram_file_bytes(file_id: str) -> bytes:
    """PTB event loop bilan aralashmaslik uchun to'g'ridan-to'g'ri Bot API."""
    if not BOT_TOKEN or not file_id:
        raise ValueError("BOT_TOKEN yoki file_id yo'q")
    async with ClientSession() as session:
        async with session.get(
            f"https://api.telegram.org/bot{BOT_TOKEN}/getFile",
            params={"file_id": file_id},
            timeout=ClientTimeout(total=20),
        ) as meta_resp:
            meta = await meta_resp.json()
        if not meta.get("ok"):
            raise RuntimeError(meta.get("description") or "getFile xato")
        file_path = (meta.get("result") or {}).get("file_path")
        if not file_path:
            raise RuntimeError("file_path yo'q")
        async with session.get(
            f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}",
            timeout=ClientTimeout(total=40),
        ) as file_resp:
            if file_resp.status != 200:
                raise RuntimeError(f"file download HTTP {file_resp.status}")
            return await file_resp.read()


async def cache_product_photo(product_id: int, file_id: str) -> Path | None:
    try:
        data = await fetch_telegram_file_bytes(file_id)
    except Exception as exc:
        logger.warning("Rasm cache xatosi product=%s: %s", product_id, exc)
        return None
    PHOTOS_DIR.mkdir(parents=True, exist_ok=True)
    path = photo_cache_path(product_id)
    path.write_bytes(data)
    return path


def _parse_init_data_pairs(init_data: str) -> dict[str, str]:
    """initData query-string ni juftliklarga ajratadi."""
    parsed: dict[str, str] = {}
    for chunk in init_data.split("&"):
        if not chunk or "=" not in chunk:
            continue
        key, raw_val = chunk.split("=", 1)
        parsed[key] = unquote(raw_val)
    # Ba'zi klientlar + ni bo'shliq qilib yuboradi — qayta urinish
    if "user" not in parsed:
        for key, value in parse_qsl(init_data, keep_blank_values=True):
            parsed[key] = value
    return parsed


def validate_webapp_init_data(init_data: str) -> dict[str, Any] | None:
    """Telegram WebApp initData HMAC tekshiruvi."""
    if not init_data or not BOT_TOKEN:
        return None
    token = BOT_TOKEN.strip().strip('"').strip("'")
    try:
        parsed = _parse_init_data_pairs(init_data)
    except Exception:
        return None

    received_hash = parsed.pop("hash", None)
    # Yangi Telegram: Ed25519 signature — bot HMAC hashiga kirmaydi
    parsed.pop("signature", None)
    if not received_hash:
        logger.warning("initData: hash yo'q, len=%s", len(init_data))
        return None

    auth_raw = parsed.get("auth_date", "")
    if auth_raw.isdigit() and time.time() - int(auth_raw) > 86400:
        logger.info("initData eskirgan: auth_date=%s", auth_raw)
        return None

    data_check_string = "\n".join(
        f"{key}={value}" for key, value in sorted(parsed.items())
    )
    secret_key = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
    calculated = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(calculated, received_hash):
        logger.warning(
            "initData hash mos kelmadi keys=%s",
            ",".join(sorted(parsed.keys())),
        )
        return None

    result: dict[str, Any] = dict(parsed)
    user_raw = parsed.get("user")
    if user_raw:
        try:
            result["user"] = json.loads(user_raw)
        except json.JSONDecodeError:
            return None
    return result


def parse_init_data_user_fallback(init_data: str) -> dict[str, Any] | None:
    """Hash yaroqsiz bo'lsa ham user id ni olish (auth_date 24 soat)."""
    if not init_data:
        return None
    try:
        parsed = _parse_init_data_pairs(init_data)
    except Exception:
        return None
    auth_raw = parsed.get("auth_date", "")
    if not auth_raw.isdigit() or time.time() - int(auth_raw) > 86400:
        return None
    user_raw = parsed.get("user")
    if not user_raw:
        return None
    try:
        user = json.loads(user_raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(user, dict) or not user.get("id"):
        return None
    return user


_MAX_PACK_GRAMS = 50_000
_MAX_PACK_AMOUNT = 5_000_000
_MAX_PACK_ML = 10_000


def _int_field(raw: dict[str, Any], key: str) -> int:
    value = raw.get(key)
    if value in (None, "", 0, "0"):
        return 0
    return int(value)


def _kg_line_from_pack(product: Any, pack_grams: int, pack_amount: int) -> tuple[str, int]:
    """Kg mahsulot: 250g/500g yoki so‘mlik. Narxni server hisoblaydi."""
    from bot.shop_ai import _money_label, _product_grams, grams_for_money

    prod_grams = _product_grams(product)
    if not prod_grams:
        raise ValueError(f"'{product['name']}' uchun gramm/so'mlik yo'q")
    price = int(effective_product_price(product))
    price_kg = max(1, int(round(price * 1000.0 / prod_grams)))
    if pack_amount:
        grams = grams_for_money(price_kg, pack_amount)
        if grams < 1:
            raise ValueError("So'mlik hisoblanmadi")
        return _money_label(str(product["name"]), grams, pack_amount), pack_amount
    if pack_grams == prod_grams:
        return str(product["name"]), price
    unit_price = max(100, int(round(price_kg * pack_grams / 1000.0)))
    stem = re.sub(
        r"\d+(?:\.\d+)?\s*(kg|g|gr|gramm)\b",
        "",
        str(product["name"]),
        flags=re.I,
    )
    stem = re.sub(r"\s+", " ", stem).strip() or str(product["name"])
    if pack_grams >= 1000 and pack_grams % 1000 == 0:
        label = f"{pack_grams // 1000} kg"
    else:
        label = f"{pack_grams} gramm"
    return f"{stem} {label}".strip(), unit_price


def _liter_line_from_pack(product: Any, pack_ml: int) -> tuple[str, int]:
    """Ichimlik hajmi faqat katalogdagi mahsulot narxi bilan."""
    from bot.shop_ai import _product_ml, expand_liter_packs, liter_family_for_product

    prod_ml = _product_ml(product)
    price = int(effective_product_price(product))
    if prod_ml and pack_ml == prod_ml:
        return str(product["name"]), price
    _key, family = liter_family_for_product(product)
    for opt in expand_liter_packs(family):
        if int(opt["ml"]) == int(pack_ml):
            real = get_product(int(opt["product_id"]))
            if not real:
                break
            return str(real["name"]), int(effective_product_price(real))
    raise ValueError("Bu hajm katalogda yo'q")


def _kg_api_fields(product: Any) -> dict[str, Any]:
    from bot.shop_ai import (
        _product_grams,
        _product_ml,
        exact_name_family_for_product,
        expand_exact_name_packs,
        expand_kg_packs,
        expand_real_gram_packs,
        kg_family_for_product,
        kg_money_options,
    )

    packs: list = []
    money_opts: list = []
    liter_packs: list = []
    piece_packs: list = []

    _etitle, efamily = exact_name_family_for_product(product)
    exact_packs = expand_exact_name_packs(efamily)
    if exact_packs:
        piece_packs = exact_packs
    elif _product_grams(product) and not _product_ml(product):
        _query, family = kg_family_for_product(product)
        packs = expand_kg_packs(family)
        if not packs:
            packs = expand_real_gram_packs(family)
        money_opts = kg_money_options(family)

    return {
        "kg_packs": [
            {
                "grams": int(opt["grams"]),
                "price": int(opt["price"]),
                "label": opt["label"],
                "virtual": bool(opt["virtual"]),
                "product_id": int(opt["product_id"]),
                "kg_product_id": int(opt["kg_product_id"]),
            }
            for opt in packs
        ],
        "kg_money": [
            {
                "product_id": int(opt["product_id"]),
                "amount": int(opt["amount"]),
                "grams": int(opt["grams"]),
                "label": opt["label"],
                "detail": opt["detail"],
            }
            for opt in money_opts
        ],
        "liter_packs": liter_packs,
        "piece_packs": [
            {
                "product_id": int(opt["product_id"]),
                "price": int(opt["price"]),
                "label": opt["label"],
                "name": opt["name"],
            }
            for opt in piece_packs
        ],
    }


def _product_api_payload(product: Any, *, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    variants = get_variants(int(product["id"]), active_only=True)
    has_photo = bool(product["image_file_id"]) if "image_file_id" in product.keys() else False
    payload: dict[str, Any] = {
        "id": int(product["id"]),
        "name": product["name"],
        "price": int(product["price"]),
        "display_price": product_display_price(product),
        "description": product["description"] or "",
        "category_id": product["category_id"],
        "category_name": (
            product["category_name"] if "category_name" in product.keys() else None
        ),
        "photo_url": f"/api/photo/{product['id']}" if has_photo else None,
        "variants": [
            {
                "id": int(v["id"]),
                "name": v["name"],
                "price": int(v["price"]),
            }
            for v in variants
        ],
    }
    payload.update(_kg_api_fields(product))
    pieces = payload.get("piece_packs") or []
    real_kg = [x for x in (payload.get("kg_packs") or []) if not x.get("virtual")]
    priced = pieces if len(pieces) >= 2 else real_kg if len(real_kg) >= 2 else payload.get("kg_packs") or []
    if len(priced) >= 2:
        from bot.shop_ai import display_stem_name

        payload["card_name"] = display_stem_name(str(product["name"]))
        prices = [int(x["price"]) for x in priced]
        lo, hi = min(prices), max(prices)
        if lo != hi:
            payload["display_price"] = (
                f"{lo:,} – {hi:,} so'm".replace(",", " ")
            )
    from bot.shop_ai import PIECE_QTY_PRESETS, asks_piece_qty, qty_card_name

    if asks_piece_qty(product) and not payload.get("variants"):
        payload["ask_qty"] = True
        payload["qty_unit"] = "dona"
        payload["qty_presets"] = list(PIECE_QTY_PRESETS)
        payload["card_name"] = qty_card_name(product)
        payload["display_price"] = (
            f"{int(product['price']):,} so'm / dona".replace(",", " ")
        )
    if extra:
        payload.update(extra)
    return payload


def resolve_order_items(
    items_raw: list,
) -> tuple[list[dict[str, Any]], int]:
    """Mini App savatidan order_items + subtotal."""
    order_items: list[dict[str, Any]] = []
    subtotal = 0
    for raw in items_raw:
        product_id = int(raw["product_id"])
        quantity = int(raw.get("quantity") or 1)
        if quantity < 1:
            raise ValueError("Miqdor 1 dan kam bo'lmasin")
        variant_id_raw = raw.get("variant_id")
        variant_id = (
            int(variant_id_raw)
            if variant_id_raw not in (None, "", 0, "0")
            else 0
        )
        pack_grams = _int_field(raw, "pack_grams")
        pack_amount = _int_field(raw, "pack_amount")
        pack_ml = _int_field(raw, "pack_ml")
        if pack_grams < 0 or pack_amount < 0 or pack_ml < 0:
            raise ValueError("Hajm noto'g'ri")
        if pack_grams > _MAX_PACK_GRAMS:
            raise ValueError("Hajm juda katta")
        if pack_amount > _MAX_PACK_AMOUNT:
            raise ValueError("Summa juda katta")
        if pack_ml > _MAX_PACK_ML:
            raise ValueError("Hajm juda katta")
        product = get_product(product_id)
        if not product:
            raise ValueError(f"Mahsulot topilmadi: {product_id}")
        if pack_ml:
            name, unit_price = _liter_line_from_pack(product, pack_ml)
        elif pack_grams or pack_amount:
            name, unit_price = _kg_line_from_pack(product, pack_grams, pack_amount)
        elif variant_id:
            variant = get_variant(variant_id)
            if not variant or int(variant["product_id"]) != product_id:
                raise ValueError(f"Variant topilmadi: {variant_id}")
            unit_price = int(variant["price"])
            name = f"{product['name']} ({variant['name']})"
        else:
            variants = get_variants(product_id, active_only=True)
            if variants:
                raise ValueError(f"'{product['name']}' uchun o'lcham tanlang")
            unit_price = int(effective_product_price(product))
            name = str(product["name"])
        subtotal += unit_price * quantity
        order_items.append(
            {
                "product_id": product_id,
                "name": name,
                "price": unit_price,
                "quantity": quantity,
            }
        )
    return order_items, subtotal


def place_miniapp_order(
    *,
    user_id: int,
    full_name: str,
    username: str | None,
    phone: str,
    address: str,
    slot: str,
    note: str,
    items_raw: list,
    promo_code: str = "",
    bonus_spent: int = 0,
    payment_method: str = "pending",
) -> tuple[int, int, int, int, str]:
    """Buyurtmani DB ga yozadi. Qaytaradi: order_id, total, subtotal, delivery, text."""
    if not phone:
        raise ValueError("Telefon majburiy")
    if not address:
        raise ValueError("Manzil majburiy")
    if not isinstance(items_raw, list) or not items_raw:
        raise ValueError("Savatcha bo'sh")
    order_items, subtotal = resolve_order_items(items_raw)
    if subtotal < MIN_ORDER_AMOUNT:
        raise ValueError(f"Minimal buyurtma: {MIN_ORDER_AMOUNT:,} so'm")

    promo_code = (promo_code or "").strip()
    discount = 0
    if promo_code:
        discount, msg = calc_promo_discount(promo_code, subtotal)
        if msg != "OK" or discount <= 0:
            raise ValueError(msg or "Promo kod yaroqsiz")
        promo_code = promo_code.upper()

    delivery_fee, _zone = get_delivery_fee(address, subtotal=subtotal)
    try:
        bonus_spent = max(0, int(bonus_spent or 0))
    except (TypeError, ValueError) as exc:
        raise ValueError("Bonus noto'g'ri") from exc
    total = max(0, subtotal + delivery_fee - discount - bonus_spent)

    allowed_pay = {"pending", "cash", "card_waiting"}
    payment_method = (payment_method or "pending").strip().lower()
    if payment_method not in allowed_pay:
        payment_method = "pending"

    upsert_user(user_id, full_name, username)
    set_user_phone(user_id, phone)

    if bonus_spent and not spend_bonus(user_id, bonus_spent):
        raise ValueError("Bonus yetarli emas")

    order_id = create_order(
        user_id=user_id,
        pickup_address=SHOP_ADDRESS,
        delivery_address=address,
        description=note,
        phone=phone,
        price=total,
        delivery_slot=slot,
        promo_code=promo_code,
        discount=discount,
        bonus_spent=bonus_spent,
        subtotal=subtotal,
    )
    save_order_items_direct(order_id, order_items)
    from bot.database import decrease_stock_for_order_items

    decrease_stock_for_order_items(order_id, order_items)
    if payment_method != "pending":
        update_payment_status(order_id, payment_method)
    order_row = get_order(order_id)
    text = format_order(order_row) if order_row else f"Buyurtma #{order_id}"
    return order_id, total, subtotal, delivery_fee, text


def extract_user_from_init_data(
    init_data: str,
) -> tuple[int | None, str, str | None]:
    """validate_webapp_init_data yoki auth_date fallback orqali user."""
    full_name = "Mini App mijoz"
    username: str | None = None
    if not init_data:
        return None, full_name, username

    validated = validate_webapp_init_data(init_data)
    if validated and isinstance(validated.get("user"), dict):
        user = validated["user"]
        full_name = (
            f"{user.get('first_name') or ''} {user.get('last_name') or ''}".strip()
            or full_name
        )
        return int(user.get("id")), full_name, user.get("username")

    fallback = parse_init_data_user_fallback(init_data)
    if fallback:
        logger.warning(
            "initData hash o'tmadi, auth_date bilan fallback user=%s",
            fallback.get("id"),
        )
        full_name = (
            f"{fallback.get('first_name') or ''} "
            f"{fallback.get('last_name') or ''}".strip()
            or full_name
        )
        return int(fallback["id"]), full_name, fallback.get("username")
    return None, full_name, username


def extract_user_from_request(
    request: web.Request, body: dict[str, Any] | None = None
) -> tuple[int | None, str, str | None]:
    """X-Telegram-Init-Data / query / body dan user."""
    body = body or {}
    init_data = (
        (request.headers.get("X-Telegram-Init-Data") or "").strip()
        or (request.rel_url.query.get("initData") or "").strip()
        or (request.rel_url.query.get("init_data") or "").strip()
        or str(body.get("initData") or body.get("init_data") or "").strip()
    )
    user_id, full_name, username = extract_user_from_init_data(init_data)
    if user_id is not None:
        return user_id, full_name, username

    unsafe = body.get("telegram_user") or {}
    if isinstance(unsafe, dict) and str(unsafe.get("id", "")).isdigit():
        full_name = (
            f"{unsafe.get('first_name') or ''} {unsafe.get('last_name') or ''}".strip()
            or full_name
        )
        return int(unsafe["id"]), full_name, unsafe.get("username")
    return None, full_name, username


@web.middleware
async def cors_middleware(request: web.Request, handler):
    if request.method == "OPTIONS":
        response = web.Response(status=204)
    else:
        try:
            response = await handler(request)
        except web.HTTPException as exc:
            response = exc
            _add_cors(response)
            raise
        except Exception:
            raise
    _add_cors(response)
    return response


def _add_cors(response: web.StreamResponse) -> None:
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = (
        "Content-Type, Authorization, X-Telegram-Init-Data"
    )


def _row_to_dict(row) -> dict[str, Any]:
    return {key: row[key] for key in row.keys()}


async def api_health(_request: web.Request) -> web.Response:
    return web.Response(text="ok")


async def api_config(_request: web.Request) -> web.Response:
    return web.json_response(
        {
            "shop_name": SHOP_NAME,
            "shop_address": SHOP_ADDRESS,
            "shop_phone": SHOP_PHONE,
            "shop_telegram": SHOP_TELEGRAM,
            "shop_hours": SHOP_HOURS,
            "delivery_price": DELIVERY_PRICE,
            "delivery_fee_threshold": DELIVERY_FEE_THRESHOLD,
            "delivery_fee_low": DELIVERY_FEE_LOW,
            "delivery_fee_high": DELIVERY_FEE_HIGH,
            "gift_drink_threshold": GIFT_DRINK_THRESHOLD,
            "min_order": MIN_ORDER_AMOUNT,
            "slots": get_delivery_slots(),
            "payme_link": PAYME_LINK or payment_link_with_amount("", 0, 0),
            "click_link": CLICK_LINK or payment_link_with_amount("", 0, 0),
            "card_enabled": card_payment_enabled(),
            "card_number": CARD_NUMBER if card_payment_enabled() else "",
        }
    )


async def api_user(request: web.Request) -> web.Response:
    user_id, _full_name, _username = extract_user_from_request(request)
    if user_id is None:
        raise web.HTTPUnauthorized(text="initData kerak")
    user = get_user(user_id)
    return web.json_response(
        {
            "user_id": user_id,
            "bonus_points": get_bonus(user_id),
            "full_name": (user["full_name"] if user else ""),
        }
    )


async def api_promo(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except Exception as exc:
        raise web.HTTPBadRequest(text="JSON noto'g'ri") from exc
    code = str(body.get("code") or body.get("promo_code") or "").strip()
    try:
        subtotal = int(body.get("subtotal") or 0)
    except (TypeError, ValueError):
        subtotal = 0
    if not code:
        return web.json_response(
            {
                "ok": False,
                "discount": 0,
                "message": "Promo kod bo'sh",
                "code": "",
            }
        )
    discount, msg = calc_promo_discount(code, subtotal)
    ok = msg == "OK" and discount > 0
    return web.json_response(
        {
            "ok": ok,
            "discount": discount if ok else 0,
            "message": msg,
            "code": code.upper() if ok else code,
        }
    )


async def api_categories(_request: web.Request) -> web.Response:
    from bot.category_emoji import category_label

    cats = get_categories(active_only=True)
    return web.json_response(
        [
            {
                "id": int(c["id"]),
                "name": c["name"],
                "emoji": (c["emoji"] if "emoji" in c.keys() else "") or "📦",
                "label": category_label(c),
            }
            for c in cats
        ]
    )


async def api_products(request: web.Request) -> web.Response:
    category_id_raw = request.rel_url.query.get("category_id")
    category_id: int | None = None
    if category_id_raw not in (None, ""):
        try:
            category_id = int(category_id_raw)
        except ValueError:
            raise web.HTTPBadRequest(text="category_id noto'g'ri")

    products = get_products(active_only=True, category_id=category_id)
    from bot.shop_ai import collapse_catalog_families

    products = collapse_catalog_families(list(products))
    payload = [_product_api_payload(p) for p in products]
    return web.json_response(payload)


async def api_barcode(request: web.Request) -> web.Response:
    code = (request.match_info.get("code") or "").strip()
    if not code:
        raise web.HTTPBadRequest(text="Kod bo'sh")
    product = get_product_by_barcode(code)
    if not product:
        raise web.HTTPNotFound(text="Mahsulot topilmadi")
    return web.json_response(
        _product_api_payload(product, extra={"barcode": code})
    )


async def api_photo(request: web.Request) -> web.Response:
    try:
        product_id = int(request.match_info["product_id"])
    except (KeyError, ValueError):
        raise web.HTTPBadRequest(text="product_id noto'g'ri")

    cache = photo_cache_path(product_id)
    if cache.is_file() and cache.stat().st_size > 0:
        return web.FileResponse(cache, headers={"Cache-Control": "public, max-age=86400"})

    product = get_product(product_id)
    if not product:
        raise web.HTTPNotFound(text="Mahsulot topilmadi")
    file_id = None
    if "image_file_id" in product.keys():
        file_id = product["image_file_id"]
    if not file_id:
        raise web.HTTPNotFound(text="Rasm yo'q")

    try:
        data = await fetch_telegram_file_bytes(str(file_id))
        PHOTOS_DIR.mkdir(parents=True, exist_ok=True)
        cache.write_bytes(data)
    except Exception as exc:
        logger.warning("Rasm yuklash xatosi product=%s: %s", product_id, exc)
        raise web.HTTPBadGateway(text="Rasm yuklanmadi") from exc

    return web.Response(
        body=data,
        content_type="image/jpeg",
        headers={"Cache-Control": "public, max-age=86400"},
    )


async def api_order(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except Exception as exc:
        raise web.HTTPBadRequest(text="JSON noto'g'ri") from exc

    user_id, full_name, username = extract_user_from_request(request, body)
    if user_id is None:
        # Telegram WebView ba'zan initData bermaydi — klient yuborgan user
        unsafe = body.get("telegram_user") or {}
        if isinstance(unsafe, dict) and str(unsafe.get("id", "")).isdigit():
            user_id = int(unsafe["id"])
            full_name = (
                f"{unsafe.get('first_name') or ''} {unsafe.get('last_name') or ''}".strip()
                or full_name
            )
            username = unsafe.get("username")
            logger.warning("Order via telegram_user fallback user=%s", user_id)
    if user_id is None:
        dev_raw = body.get("dev_user_id")
        if dev_raw is not None and str(dev_raw).strip().isdigit():
            user_id = int(dev_raw)
            full_name = f"Dev user {user_id}"
        else:
            init_data = str(body.get("initData") or body.get("init_data") or "")
            logger.warning(
                "Order 401: initData_len=%s has_unsafe=%s",
                len(init_data),
                bool(body.get("telegram_user")),
            )
            raise web.HTTPUnauthorized(
                text="initData yaroqsiz. Botdan «🛒 Do'kon» tugmasini qayta oching."
            )

    try:
        bonus_raw = body.get("bonus_spent") or 0
        bonus_spent = int(bonus_raw)
    except (TypeError, ValueError):
        raise web.HTTPBadRequest(text="bonus_spent noto'g'ri")

    try:
        order_id, total, subtotal, delivery_fee, text = place_miniapp_order(
            user_id=user_id,
            full_name=full_name,
            username=username,
            phone=str(body.get("phone") or "").strip(),
            address=str(body.get("address") or "").strip(),
            slot=str(body.get("slot") or "").strip(),
            note=str(body.get("note") or "").strip(),
            items_raw=body.get("items") or [],
            promo_code=str(body.get("promo_code") or "").strip(),
            bonus_spent=bonus_spent,
            payment_method=str(body.get("payment_method") or "pending"),
        )
    except ValueError as exc:
        raise web.HTTPBadRequest(text=str(exc)) from exc
    except (KeyError, TypeError) as exc:
        raise web.HTTPBadRequest(text="items format noto'g'ri") from exc

    if _bot is not None:
        from bot.keyboards import admin_order_keyboard, payment_keyboard

        for admin_id in ADMIN_IDS:
            try:
                await _bot.send_message(
                    admin_id,
                    f"🆕 Mini App\n{text}",
                    reply_markup=admin_order_keyboard(order_id),
                )
            except Exception as exc:
                logger.warning("Admin xabar xatosi %s: %s", admin_id, exc)
        try:
            await _bot.send_message(
                user_id,
                f"✅ Buyurtmangiz qabul qilindi!\n\n{text}",
            )
            await _bot.send_message(
                user_id,
                "💵 <b>To‘lov faqat naqd</b>\n"
                "🙏 Qarzga berilmaydi — tushunganingiz uchun rahmat.\n\n"
                "To‘lov usulini tanlang:",
                reply_markup=payment_keyboard(order_id, amount=total),
                parse_mode="HTML",
            )
        except Exception as exc:
            logger.warning("Mijoz xabar xatosi %s: %s", user_id, exc)
        try:
            from bot.voice_confirm import send_order_voice_confirm

            await send_order_voice_confirm(
                _bot,
                user_id,
                order_id=order_id,
                total=total,
            )
        except Exception as exc:
            logger.warning("Ovozli tasdiq xato %s: %s", user_id, exc)

    return web.json_response(
        {
            "ok": True,
            "order_id": order_id,
            "total": total,
            "subtotal": subtotal,
            "delivery_price": delivery_fee,
        }
    )


async def api_shajara_share_create(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except Exception as exc:
        raise web.HTTPBadRequest(text="JSON noto'g'ri") from exc
    tree = body.get("tree")
    if not isinstance(tree, dict) or tree.get("version") != 1:
        raise web.HTTPBadRequest(text="tree noto'g'ri")
    people = tree.get("people")
    if not isinstance(people, list) or len(people) > 200:
        raise web.HTTPBadRequest(text="people limiti: 200")
    # Rasmlarni serverga yozmaslik — hajm
    cleaned_people = []
    for p in people:
        if not isinstance(p, dict):
            continue
        item = dict(p)
        item["photoDataUrl"] = ""
        cleaned_people.append(item)
    tree = {**tree, "people": cleaned_people}
    code = body.get("code")
    code_str = str(code).strip().upper() if code else None
    try:
        saved = save_shajara_share(json.dumps(tree, ensure_ascii=False), code_str)
    except Exception as exc:
        logger.warning("shajara share: %s", exc)
        raise web.HTTPBadRequest(text="Saqlash xato") from exc
    base = str(request.url.origin())
    return web.json_response(
        {
            "ok": True,
            "code": saved,
            "url": f"{base}/shajara/?code={saved}",
        }
    )


async def api_shajara_share_get(request: web.Request) -> web.Response:
    code = request.match_info.get("code", "")
    payload = get_shajara_share(code)
    if not payload:
        raise web.HTTPNotFound(text="Kod topilmadi")
    try:
        tree = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise web.HTTPBadGateway(text="Ma'lumot buzilgan") from exc
    return web.json_response({"ok": True, "code": code.strip().upper(), "tree": tree})


async def serve_index(_request: web.Request) -> web.FileResponse:
    index = MINIAPP_DIR / "index.html"
    if not index.is_file():
        raise web.HTTPNotFound(text="index.html topilmadi")
    return web.FileResponse(
        index,
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate",
            "Pragma": "no-cache",
        },
    )


async def serve_shajara_index(_request: web.Request) -> web.FileResponse:
    index = SHAJARA_DIR / "index.html"
    if not index.is_file():
        raise web.HTTPNotFound(text="Mening Shajaram topilmadi")
    return web.FileResponse(index)


async def serve_admin_index(_request: web.Request) -> web.FileResponse:
    index = ADMINAPP_DIR / "index.html"
    if not index.is_file():
        raise web.HTTPNotFound(text="Admin ilova topilmadi")
    return web.FileResponse(index)


async def serve_arduino_index(_request: web.Request) -> web.FileResponse:
    index = ARDUINO_DIR / "index.html"
    if not index.is_file():
        raise web.HTTPNotFound(text="Arduino Darslik topilmadi")
    return web.FileResponse(index)


async def serve_jadval_index(_request: web.Request) -> web.FileResponse:
    index = JADVAL_DIR / "index.html"
    if not index.is_file():
        raise web.HTTPNotFound(text="Dars Jadvali topilmadi")
    return web.FileResponse(index)


async def serve_jadval_gone(_request: web.Request) -> web.Response:
    """Eski /jadval/ — maxfiy manzilga o‘tkazilgan, yangi path oshkor etilmaydi."""
    html = """<!doctype html><html lang="uz"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Link yopilgan</title>
<style>
body{font-family:system-ui,sans-serif;background:#0b4f8a;color:#fff;min-height:100vh;
display:grid;place-items:center;margin:0;padding:24px;text-align:center}
.card{max-width:420px;background:rgba(255,255,255,.1);border-radius:16px;padding:28px}
h1{margin:0 0 10px;font-size:1.4rem}p{margin:0;opacity:.9;line-height:1.45}
</style></head><body><div class="card">
<h1>Bu link yopilgan</h1>
<p>Dars jadvali manzili o‘zgartirilgan. Yangi linkni admin / o‘qituvchidan so‘rang.</p>
</div></body></html>"""
    return web.Response(text=html, content_type="text/html", status=410)


async def serve_kichkintoy_index(_request: web.Request) -> web.FileResponse:
    index = KICHKINTOY_DIR / "index.html"
    if not index.is_file():
        raise web.HTTPNotFound(text="Kichkintoy AI topilmadi")
    return web.FileResponse(index)


async def serve_slayd_index(_request: web.Request) -> web.FileResponse:
    index = SLAYD_DIR / "index.html"
    if not index.is_file():
        raise web.HTTPNotFound(text="Slayd Studio topilmadi")
    return web.FileResponse(index)


def create_app() -> web.Application:
    from bot.admin_api import register_admin_routes

    app = web.Application(middlewares=[cors_middleware])
    app.router.add_get("/health", api_health)
    app.router.add_get("/api/config", api_config)
    app.router.add_get("/api/user", api_user)
    app.router.add_post("/api/promo", api_promo)
    app.router.add_get("/api/categories", api_categories)
    app.router.add_get("/api/products", api_products)
    app.router.add_get("/api/barcode/{code}", api_barcode)
    app.router.add_get("/api/photo/{product_id}", api_photo)
    app.router.add_post("/api/order", api_order)
    app.router.add_post("/api/shajara/share", api_shajara_share_create)
    app.router.add_get("/api/shajara/share/{code}", api_shajara_share_get)
    register_admin_routes(app)
    app.router.add_route("OPTIONS", "/api/{tail:.*}", lambda r: web.Response(status=204))

    if SHAJARA_DIR.is_dir():
        app.router.add_get("/shajara", serve_shajara_index)
        app.router.add_get("/shajara/", serve_shajara_index)
        app.router.add_static("/shajara/", SHAJARA_DIR, show_index=False)
    else:
        logger.warning("shajara papkasi topilmadi: %s", SHAJARA_DIR)

    if ADMINAPP_DIR.is_dir() and (ADMINAPP_DIR / "index.html").is_file():
        app.router.add_get("/admin", serve_admin_index)
        app.router.add_get("/admin/", serve_admin_index)
        app.router.add_static("/admin/", ADMINAPP_DIR, show_index=False)
    else:
        logger.warning("admin papkasi topilmadi: %s", ADMINAPP_DIR)

    if ARDUINO_DIR.is_dir() and (ARDUINO_DIR / "index.html").is_file():
        app.router.add_get("/arduino", serve_arduino_index)
        app.router.add_get("/arduino/", serve_arduino_index)
        app.router.add_static("/arduino/", ARDUINO_DIR, show_index=False)
    else:
        logger.warning("arduino papkasi topilmadi: %s", ARDUINO_DIR)

    if JADVAL_DIR.is_dir() and (JADVAL_DIR / "index.html").is_file():
        secret = f"/{JADVAL_PATH}"
        app.router.add_get(secret, serve_jadval_index)
        app.router.add_get(f"{secret}/", serve_jadval_index)
        app.router.add_static(f"{secret}/", JADVAL_DIR, show_index=False)
        # Eski ochiq link — yopiq (yangi manzil oshkor etilmaydi)
        app.router.add_get("/jadval", serve_jadval_gone)
        app.router.add_get("/jadval/", serve_jadval_gone)
        app.router.add_route("*", "/jadval/{tail:.*}", serve_jadval_gone)
        logger.info("Dars Jadvali: %s/ (eski /jadval/ yopiq)", secret)
    else:
        logger.warning("jadval papkasi topilmadi: %s", JADVAL_DIR)

    if KICHKINTOY_DIR.is_dir() and (KICHKINTOY_DIR / "index.html").is_file():
        app.router.add_get("/kichkintoy", serve_kichkintoy_index)
        app.router.add_get("/kichkintoy/", serve_kichkintoy_index)
        app.router.add_static("/kichkintoy/", KICHKINTOY_DIR, show_index=False)
    else:
        logger.warning("kichkintoy papkasi topilmadi: %s", KICHKINTOY_DIR)

    if SLAYD_DIR.is_dir() and (SLAYD_DIR / "index.html").is_file():
        app.router.add_get("/slayd", serve_slayd_index)
        app.router.add_get("/slayd/", serve_slayd_index)
        app.router.add_static("/slayd/", SLAYD_DIR, show_index=False)
    else:
        logger.warning("slayd papkasi topilmadi: %s", SLAYD_DIR)

    if MINIAPP_DIR.is_dir():
        app.router.add_get("/", serve_index)
        app.router.add_static("/", MINIAPP_DIR, show_index=False)
    else:
        logger.warning("miniapp papkasi topilmadi: %s", MINIAPP_DIR)

    return app


def start_webapp_server(port: int | None = None) -> None:
    """aiohttp ni daemon thread da ishga tushiradi."""
    listen_port = port if port is not None else WEBAPP_PORT

    def _run() -> None:
        app = create_app()
        logger.info("Mini App server: http://0.0.0.0:%s", listen_port)
        web.run_app(
            app,
            host="0.0.0.0",
            port=listen_port,
            handle_signals=False,
            print=lambda *args: None,
        )

    thread = threading.Thread(target=_run, name="miniapp-web", daemon=True)
    thread.start()
    print(f"Mini App server ishga tushdi: http://0.0.0.0:{listen_port}")
