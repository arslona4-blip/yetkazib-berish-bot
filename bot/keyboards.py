from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    WebAppInfo,
)

from bot.config import MINIAPP_URL, ORDER_STATUS_LABELS


def miniapp_shop_url() -> str:
    return (MINIAPP_URL or "").rstrip("/")


def admin_app_url() -> str:
    """MINIAPP_URL dan /admin/ manzilini hosil qiladi."""
    url = miniapp_shop_url()
    if not url:
        return ""
    if url.endswith("/miniapp"):
        return f"{url[: -len('/miniapp')]}/admin/"
    # origin yoki boshqa path — host + /admin/
    from urllib.parse import urlsplit, urlunsplit

    parts = urlsplit(url)
    if not parts.scheme or not parts.netloc:
        return ""
    return urlunsplit((parts.scheme, parts.netloc, "/admin/", "", ""))


def shop_reply_button(label: str = "🛒 Do'kon") -> KeyboardButton | None:
    url = miniapp_shop_url()
    if not url:
        return None
    return KeyboardButton(label, web_app=WebAppInfo(url=url))


def shop_inline_button(label: str = "🛒 Do'kon") -> InlineKeyboardButton | None:
    url = miniapp_shop_url()
    if not url:
        return None
    return InlineKeyboardButton(label, web_app=WebAppInfo(url=url))


def admin_app_inline_button(
    label: str = "🖥 Admin ilova",
) -> InlineKeyboardButton | None:
    url = admin_app_url()
    if not url:
        return None
    return InlineKeyboardButton(label, web_app=WebAppInfo(url=url))


def admin_app_reply_button(
    label: str = "🖥 Admin ilova",
) -> KeyboardButton | None:
    url = admin_app_url()
    if not url:
        return None
    return KeyboardButton(label, web_app=WebAppInfo(url=url))


def is_main_menu_text(text: str) -> bool:
    """Asosiy / qo‘shimcha menyu tugmasi — admin FSM ni to‘xtatish uchun."""
    t = (text or "").strip()
    return t in {
        "🛍 Katalog",
        "🛒 Savatcha",
        "📞 Aloqa",
        "⋯ Ko'proq",
        "🖥 Admin ilova",
        "📦 Buyurtmalar",
        "🛠 Admin panel",
        "🚴 Kuryer panel",
        "⬅️ Asosiy menyu",
        "⭐ Sevimlilar",
        "🎁 Bonus",
        "👥 Ulashish",
        "📋 Mening buyurtmalarim",
        "ℹ️ Yordam",
        "📚 Qo‘llanma",
        "🌐 Til",
        "🌐 Язык",
        "🛒 Do'kon",
        "🔍 Qidiruv",
        "✨ Tavsiyalar",
        "🔁 Takroriy buyurtmalar",
        "🤖 AI sotuvchi",
    }


def main_menu_keyboard(is_admin: bool = False, is_courier: bool = False) -> ReplyKeyboardMarkup:
    rows: list[list] = []
    shop_btn = shop_reply_button()
    if shop_btn:
        rows.append([shop_btn])
        rows.append(["🛒 Savatcha", "📋 Mening buyurtmalarim"])
        rows.append(["🛍 Katalog", "📞 Aloqa"])
        rows.append(["⋯ Ko'proq"])
    else:
        rows.append(["🛍 Katalog", "🛒 Savatcha"])
        rows.append(["📋 Mening buyurtmalarim", "📞 Aloqa"])
        rows.append(["⋯ Ko'proq"])
    staff_row = []
    if is_admin:
        admin_app = admin_app_reply_button()
        if admin_app:
            rows.append([admin_app])
        staff_row.append("📦 Buyurtmalar")
        staff_row.append("🛠 Admin panel")
    if is_courier:
        staff_row.append("🚴 Kuryer panel")
    if staff_row:
        rows.append(staff_row)
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)


def barcode_attach_keyboard() -> ReplyKeyboardMarkup:
    rows: list[list] = []
    rows.append(["⏭ O‘chirish (0)"])
    rows.append(["❌ Bekor qilish"])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)


def new_product_barcode_keyboard() -> ReplyKeyboardMarkup:
    """Yangi mahsulot: shtrix-kod yozish yoki o'tkazib yuborish."""
    rows: list[list] = []
    rows.append(["⏭ O'tkazib yuborish"])
    rows.append(["❌ Bekor qilish"])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)


def suggested_name_keyboard(name: str) -> ReplyKeyboardMarkup:
    label = name if len(name) <= 40 else name[:37] + "…"
    return ReplyKeyboardMarkup(
        [[f"✅ {label}"], ["✏️ Boshqa nom yozaman"], ["❌ Bekor qilish"]],
        resize_keyboard=True,
    )


def miniapp_keyboard() -> InlineKeyboardMarkup | None:
    """Mini App ochish tugmasi (faqat MINIAPP_URL sozlanganda)."""
    btn = shop_inline_button("🛒 Do'konni ochish")
    if not btn:
        return None
    return InlineKeyboardMarkup([[btn]])


def more_menu_keyboard() -> ReplyKeyboardMarkup:
    rows = [
        ["🔍 Qidiruv", "⭐ Sevimlilar"],
        ["🎁 Bonus", "👥 Ulashish"],
        ["✨ Tavsiyalar", "🔁 Takroriy buyurtmalar"],
        ["🤖 AI sotuvchi", "ℹ️ Yordam"],
        ["📚 Qo‘llanma", "🌐 Til"],
        ["⬅️ Asosiy menyu"],
    ]
    shop = shop_reply_button("🛒 Do'kon")
    if shop:
        rows.insert(0, [shop])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)


def contact_keyboard(last_phone: str | None = None) -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton("📱 Kontaktni yuborish", request_contact=True)],
    ]
    if last_phone:
        short = last_phone if len(last_phone) <= 28 else last_phone[:25] + "..."
        rows.append([f"✅ Shu raqam: {short}"])
    rows.append(["❌ Bekor qilish"])
    return ReplyKeyboardMarkup(
        rows,
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def location_keyboard(last_address: str | None = None) -> ReplyKeyboardMarkup:
    rows = [[KeyboardButton("📍 Joylashuvni yuborish", request_location=True)]]
    if last_address:
        short = last_address if len(last_address) <= 40 else last_address[:37] + "..."
        rows.append([f"🏠 {short}"])
    rows.append(["❌ Bekor qilish"])
    return ReplyKeyboardMarkup(
        rows,
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup([["❌ Bekor qilish"]], resize_keyboard=True)


def catalog_categories_keyboard(categories) -> InlineKeyboardMarkup:
    from bot.category_emoji import category_label
    from bot.database import get_products
    from bot.shop_ai import collapse_catalog_families

    rows = []
    for category in categories:
        count = len(
            collapse_catalog_families(get_products(category_id=category["id"]))
        )
        label = f"{category_label(category)} · {count} ta"
        if len(label) > 64:
            label = label[:61] + "..."
        rows.append(
            [
                InlineKeyboardButton(
                    label,
                    callback_data=f"catalog:cat:{category['id']}",
                )
            ]
        )
    rows.append(
        [
            InlineKeyboardButton("🔍 Qidiruv", callback_data="catalog:search"),
            InlineKeyboardButton("⭐ Sevimlilar", callback_data="catalog:favs"),
        ]
    )
    rows.append(
        [InlineKeyboardButton("🛒 Savatchaga o'tish", callback_data="cart:view")]
    )
    return InlineKeyboardMarkup(rows)


def catalog_keyboard(
    products,
    category_id: int | None = None,
    cart_qty: dict[int, int] | None = None,
) -> InlineKeyboardMarkup:
    from bot.database import product_display_price
    from bot.shop_ai import (
        collapse_catalog_families,
        display_stem_name,
        expand_exact_name_packs,
        expand_gram_family_packs,
        expand_liter_packs,
        exact_name_family_for_product,
        kg_family_for_product,
        liter_family_for_product,
        asks_piece_qty,
        qty_card_name,
        _product_ml,
    )

    cart_qty = cart_qty or {}
    products = collapse_catalog_families(list(products))
    rows = []
    for product in products:
        callback = f"product:{product['id']}"
        qty = cart_qty.get(product["id"], 0)
        mark = f" ✅ x{qty}" if qty else ""
        label_name = str(product["name"])
        _etitle, efamily = exact_name_family_for_product(product)
        if expand_exact_name_packs(efamily):
            label_name = str(product["name"]).strip()
        elif _product_ml(product):
            _lk, lfamily = liter_family_for_product(product)
            if len(expand_liter_packs(lfamily)) >= 2:
                label_name = display_stem_name(str(product["name"]))
        else:
            _query, family = kg_family_for_product(product)
            if len(expand_gram_family_packs(family)) >= 2:
                label_name = display_stem_name(str(product["name"]))
        if asks_piece_qty(product):
            label_name = qty_card_name(product)
        btn_text = f"{label_name} — {product_display_price(product)}{mark}"
        rows.append(
            [
                InlineKeyboardButton(
                    btn_text,
                    callback_data=callback,
                )
            ]
        )

    total_qty = sum(cart_qty.values())
    cart_label = f"🛒 Savatcha ({total_qty})" if total_qty else "🛒 Savatcha"
    rows.append(
        [
            InlineKeyboardButton("⬅️ Toifalar", callback_data="catalog:list"),
            InlineKeyboardButton(cart_label, callback_data="cart:view"),
        ]
    )
    return InlineKeyboardMarkup(rows)


def product_keyboard(
    product_id: int,
    category_id: int | None = None,
    variants=None,
    cart_variant_qty: dict[int, int] | None = None,
) -> InlineKeyboardMarkup:
    back_data = (
        f"catalog:cat:{category_id}" if category_id else "catalog:list"
    )
    cart_variant_qty = cart_variant_qty or {}
    rows = []
    if variants:
        for variant in variants:
            qty = cart_variant_qty.get(variant["id"], 0)
            mark = f" ✅ x{qty}" if qty else ""
            rows.append(
                [
                    InlineKeyboardButton(
                        f"{variant['name']} — {variant['price']:,} so'm{mark}",
                        callback_data=f"cart_add:{product_id}:{variant['id']}",
                    )
                ]
            )
    else:
        qty = cart_variant_qty.get(0, 0)
        mark = f" ✅ x{qty}" if qty else ""
        rows.append(
            [
                InlineKeyboardButton(
                    f"➕ Savatchaga qo'shish{mark}",
                    callback_data=f"cart_add:{product_id}:0",
                )
            ]
        )
    rows.append(
        [
            InlineKeyboardButton("⭐", callback_data=f"fav:{product_id}"),
            InlineKeyboardButton("⬅️ Orqaga", callback_data=back_data),
            InlineKeyboardButton("🛒", callback_data="cart:view"),
        ]
    )
    return InlineKeyboardMarkup(rows)


def qty_pick_keyboard(product_id: int, category_id: int | None = None) -> InlineKeyboardMarkup:
    from bot.shop_ai import PIECE_QTY_PRESETS

    back_data = (
        f"catalog:cat:{category_id}" if category_id else "catalog:list"
    )
    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for n in (1, *PIECE_QTY_PRESETS):
        row.append(
            InlineKeyboardButton(
                f"{n} dona",
                callback_data=f"qty_add:{product_id}:{n}",
            )
        )
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton("⬅️ Orqaga", callback_data=back_data)])
    return InlineKeyboardMarkup(rows)


def shop_ai_results_keyboard(products) -> InlineKeyboardMarkup | None:
    """AI qidiruv: qadoq + (kg bo‘lsa) so‘mlik tugmalar."""
    if not products:
        return None
    from bot.shop_ai import (
        _human_pack_label,
        _tier_brand_stems,
        catalog_tier_key,
        expand_kg_packs,
        expand_exact_name_packs,
        expand_liter_packs,
        kg_money_options,
        money,
    )

    buttons: list[list[InlineKeyboardButton]] = []
    tier_keys = {catalog_tier_key(p) for p in products}
    is_tier = (
        len(products) >= 2
        and None not in tier_keys
        and len(tier_keys) == 1
        and len(_tier_brand_stems(products)) >= 2
    )
    packs = expand_kg_packs(products) if not is_tier else []
    liter_packs = [] if packs or is_tier else expand_liter_packs(products)
    if packs:
        for opt in packs:
            btn = f"{opt['label']} — {money(int(opt['price']))}"
            if len(btn) > 64:
                btn = btn[:61] + "…"
            if opt["virtual"]:
                cb = f"ai_p:{opt['kg_product_id']}:{opt['grams']}"
            else:
                cb = f"cart_add:{opt['product_id']}:0"
            buttons.append([InlineKeyboardButton(btn, callback_data=cb)])
    elif liter_packs:
        for opt in liter_packs:
            btn = f"{opt['label']} — {money(int(opt['price']))}"
            if len(btn) > 64:
                btn = btn[:61] + "…"
            if opt["virtual"]:
                cb = f"ai_l:{opt['liter_product_id']}:{opt['ml']}"
            else:
                cb = f"cart_add:{opt['product_id']}:0"
            buttons.append([InlineKeyboardButton(btn, callback_data=cb)])
    else:
        exact_packs = expand_exact_name_packs(products)
        if exact_packs:
            for opt in exact_packs:
                btn = str(opt["label"])
                if len(btn) > 64:
                    btn = btn[:61] + "…"
                buttons.append(
                    [
                        InlineKeyboardButton(
                            btn,
                            callback_data=f"cart_add:{int(opt['product_id'])}:0",
                        )
                    ]
                )
        else:
            sorted_products = sorted(
                products, key=lambda p: (int(p["price"]), str(p["name"]))
            )
            for p in sorted_products[:20]:
                show = str(p["name"])
                btn = f"{show} — {money(int(p['price']))}"
                if len(btn) > 64:
                    btn = btn[:61] + "…"
                buttons.append(
                    [InlineKeyboardButton(btn, callback_data=f"cart_add:{int(p['id'])}:0")]
                )
    for opt in kg_money_options(products):
        btn = f"{opt['label']} · {opt['detail']}"
        if len(btn) > 64:
            btn = btn[:61] + "…"
        buttons.append(
            [
                InlineKeyboardButton(
                    btn,
                    callback_data=f"ai_m:{opt['product_id']}:{opt['amount']}",
                )
            ]
        )
    buttons.append([InlineKeyboardButton("🛒 Savatcha", callback_data="cart:view")])
    return InlineKeyboardMarkup(buttons) if buttons else None


def category_pick_keyboard(categories) -> InlineKeyboardMarkup:
    from bot.category_emoji import category_label

    rows = []
    for category in categories:
        label = category_label(category)
        if len(label) > 64:
            label = label[:61] + "..."
        rows.append(
            [
                InlineKeyboardButton(
                    label,
                    callback_data=f"admin_prod:setcat:{category['id']}",
                )
            ]
        )
    return InlineKeyboardMarkup(rows)


def cart_keyboard(items) -> InlineKeyboardMarkup:
    rows = []
    for item in items:
        pid = item["product_id"]
        vid = item["variant_id"]
        rows.append(
            [
                InlineKeyboardButton("➖", callback_data=f"cart_dec:{pid}:{vid}"),
                InlineKeyboardButton(
                    f"{item['name']} x{item['quantity']}",
                    callback_data=f"product:{pid}",
                ),
                InlineKeyboardButton("➕", callback_data=f"cart_inc:{pid}:{vid}"),
            ]
        )
    rows.append(
        [
            InlineKeyboardButton(
                "✅ Buyurtma berish", callback_data="cart:checkout"
            )
        ]
    )
    rows.append(
        [
            InlineKeyboardButton("🛍 Yana tanlash", callback_data="catalog:list"),
            InlineKeyboardButton("🧹 Tozalash", callback_data="cart:clear"),
        ]
    )
    return InlineKeyboardMarkup(rows)


def confirm_order_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ Ha, buyurtma beraman", callback_data="order:confirm"
                )
            ],
            [
                InlineKeyboardButton("❌ Bekor", callback_data="order:cancel"),
            ],
        ]
    )


def payment_keyboard(
    order_id: int, amount: int | None = None
) -> InlineKeyboardMarkup:
    from bot.config import (
        CLICK_LINK,
        PAYME_LINK,
        online_payment_enabled,
        payment_link_with_amount,
    )
    from bot.database import get_order

    if amount is None:
        order = get_order(order_id)
        amount = int(order["price"]) if order else 0

    rows = [
        [
            InlineKeyboardButton(
                "💵 Naqd to'lash",
                callback_data=f"pay_cash:{order_id}",
            )
        ],
        [
            InlineKeyboardButton(
                "💳 Kartaga o'tkazish",
                callback_data=f"pay_card:{order_id}",
            )
        ],
    ]
    payme_url = payment_link_with_amount(PAYME_LINK, amount, order_id)
    if payme_url:
        rows.append([InlineKeyboardButton("🟢 Payme", url=payme_url)])
        rows.append(
            [
                InlineKeyboardButton(
                    "✅ Payme orqali to'ladim",
                    callback_data=f"pay_done:{order_id}",
                )
            ]
        )
    click_url = payment_link_with_amount(CLICK_LINK, amount, order_id)
    if click_url:
        rows.append([InlineKeyboardButton("🔵 Click", url=click_url)])
        rows.append(
            [
                InlineKeyboardButton(
                    "✅ Click orqali to'ladim",
                    callback_data=f"pay_done:{order_id}",
                )
            ]
        )
    if online_payment_enabled():
        rows.append(
            [
                InlineKeyboardButton(
                    "🤖 Telegram orqali to'lov",
                    callback_data=f"pay_online:{order_id}",
                )
            ]
        )
    return InlineKeyboardMarkup(rows)


def card_paid_keyboard(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ Men to'lov qildim",
                    callback_data=f"pay_done:{order_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Orqaga",
                    callback_data=f"pay_menu:{order_id}",
                )
            ],
        ]
    )


def admin_payment_keyboard(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ To'lovni tasdiqlash",
                    callback_data=f"pay_confirm:{order_id}",
                ),
                InlineKeyboardButton(
                    "❌ Rad etish",
                    callback_data=f"pay_reject:{order_id}",
                ),
            ],
        ]
    )


def admin_orders_keyboard() -> InlineKeyboardMarkup:
    """Admin: buyurtmalar paneli (yangi / faol)."""
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🆕 Yangi buyurtmalar", callback_data="admin:new")],
            [
                InlineKeyboardButton(
                    "🚚 Faol buyurtmalar", callback_data="admin:active"
                )
            ],
            [
                InlineKeyboardButton(
                    "📦 Yetkazilganlar", callback_data="admin:delivered"
                )
            ],
            [InlineKeyboardButton("⬅️ Admin panel", callback_data="admin:menu")],
        ]
    )


def admin_menu_keyboard() -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    shop = shop_inline_button("🛒 Do'kon")
    admin_app = admin_app_inline_button()
    if shop:
        rows.append([shop])
    if admin_app:
        rows.append([admin_app])
    rows.extend(
        [
            [
                InlineKeyboardButton(
                    "🔑 Kirish kodi", callback_data="admin:login_code"
                )
            ],
            [InlineKeyboardButton("📦 Buyurtmalar", callback_data="admin:orders")],
            [InlineKeyboardButton("🆕 Yangi buyurtmalar", callback_data="admin:new")],
            [
                InlineKeyboardButton(
                    "🚚 Faol buyurtmalar", callback_data="admin:active"
                )
            ],
            [InlineKeyboardButton("🛍 Mahsulotlar", callback_data="admin:products")],
            [
                InlineKeyboardButton(
                    "👥 Kontaktlar", callback_data="admin:contacts"
                ),
            ],
            [InlineKeyboardButton("📊 Statistika", callback_data="admin:stats")],
            [InlineKeyboardButton("📈 Kunlik hisobot", callback_data="admin:report")],
            [InlineKeyboardButton("📣 Broadcast", callback_data="admin:broadcast")],
            [InlineKeyboardButton("📤 Excel eksport", callback_data="admin:export")],
            [InlineKeyboardButton("📥 Excel import", callback_data="admin:import")],
        ]
    )
    return InlineKeyboardMarkup(rows)



def delivery_slots_keyboard(slots) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(slot, callback_data=f"slot:{i}")]
        for i, slot in enumerate(slots)
    ]
    rows.append([InlineKeyboardButton("❌ Bekor qilish", callback_data="order:cancel")])
    return InlineKeyboardMarkup(rows)


def promo_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("⏭ Promo yo'q", callback_data="promo:skip")],
            [InlineKeyboardButton("❌ Bekor qilish", callback_data="order:cancel")],
        ]
    )


def bonus_keyboard(bonus: int) -> InlineKeyboardMarkup:
    rows = []
    if bonus > 0:
        rows.append(
            [
                InlineKeyboardButton(
                    f"🎁 Bonus ishlatish ({bonus:,})",
                    callback_data="bonus:use",
                )
            ]
        )
    rows.append([InlineKeyboardButton("⏭ O'tkazib yuborish", callback_data="bonus:skip")])
    return InlineKeyboardMarkup(rows)


def order_actions_keyboard(order_id: int, can_pay: bool, can_cancel: bool) -> InlineKeyboardMarkup:
    rows = []
    if can_pay:
        rows.append(
            [InlineKeyboardButton("💳 To'lov", callback_data=f"pay_menu:{order_id}")]
        )
    rows.append(
        [
            InlineKeyboardButton(
                "🔁 Yana buyurtma", callback_data=f"reorder:{order_id}"
            )
        ]
    )
    rows.append(
        [
            InlineKeyboardButton(
                "🔄 Takroriy qilish", callback_data=f"recur:{order_id}"
            )
        ]
    )
    if can_cancel:
        rows.append(
            [
                InlineKeyboardButton(
                    "❌ Bekor qilish", callback_data=f"cancel_order:{order_id}"
                )
            ]
        )
    return InlineKeyboardMarkup(rows)


def favorite_toggle_keyboard(product_id: int, is_fav: bool) -> InlineKeyboardMarkup:
    label = "💔 Sevimlidan olib tashlash" if is_fav else "⭐ Sevimliga"
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(label, callback_data=f"fav:{product_id}")]]
    )


def admin_products_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "📋 Mahsulotlar spiskasi", callback_data="admin_prod:list"
                )
            ],
            [
                InlineKeyboardButton(
                    "➕ Yangi mahsulot", callback_data="admin_prod:add"
                )
            ],
            [
                InlineKeyboardButton(
                    "🗂 Toifalar", callback_data="admin_prod:cats"
                )
            ],
            [
                InlineKeyboardButton(
                    "➕ Yangi toifa", callback_data="admin_prod:addcat"
                )
            ],
            [InlineKeyboardButton("⬅️ Orqaga", callback_data="admin:menu")],
        ]
    )


def admin_all_products_list_keyboard(products) -> InlineKeyboardMarkup:
    """Mahsulotlar toifa bo'yicha guruhlangan spiska."""
    from collections import defaultdict

    grouped: dict[str, list] = defaultdict(list)
    for product in products:
        cat_name = product["category_name"] or "Toifasiz"
        grouped[cat_name].append(product)

    rows = [
        [
            InlineKeyboardButton(
                "➕ Yangi mahsulot", callback_data="admin_prod:add"
            )
        ],
        [
            InlineKeyboardButton("🗂 Toifalar", callback_data="admin_prod:cats"),
            InlineKeyboardButton("⬅️ Orqaga", callback_data="admin:products"),
        ],
    ]
    max_buttons = 100
    truncated = False
    for cat_name in sorted(grouped.keys(), key=lambda x: x.casefold()):
        if len(rows) >= max_buttons - 2:
            truncated = True
            break
        items = sorted(
            grouped[cat_name],
            key=lambda p: (p["name"] or "").casefold(),
        )
        cat_id = items[0]["category_id"] if items else None
        # Toifa — ajralib turadigan sarlavha (mahsulotdan farqli)
        header = f"━━ 📁 {cat_name} · {len(items)} ta ━━"
        if len(header) > 64:
            header = f"━━ 📁 {cat_name[:40]}… ━━"
        rows.append(
            [
                InlineKeyboardButton(
                    header,
                    callback_data=(
                        f"admin_prod:viewcat:{cat_id}"
                        if cat_id
                        else "admin_prod:cats"
                    ),
                )
            ]
        )
        for product in items:
            if len(rows) >= max_buttons - 1:
                truncated = True
                break
            mark = "✅" if product["is_active"] else "🚫"
            try:
                has_photo = bool(product["image_file_id"])
            except (KeyError, IndexError):
                has_photo = False
            pic = "🖼" if has_photo else "📷·"
            # Mahsulot — oddiyroq, chekinish belgisiga o'xshash
            label = f"　　{mark}{pic} {product['name']} — {product['price']:,}"
            if len(label) > 64:
                label = label[:61] + "..."
            rows.append(
                [
                    InlineKeyboardButton(
                        label,
                        callback_data=f"admin_prod:item:{product['id']}",
                    )
                ]
            )
        if truncated:
            break

    if truncated:
        rows.append(
            [
                InlineKeyboardButton(
                    "📁 Toifadan ko‘ring — to‘liq ro‘yxat",
                    callback_data="admin_prod:cats",
                )
            ]
        )

    return InlineKeyboardMarkup(rows)


def admin_categories_list_keyboard(categories_with_counts) -> InlineKeyboardMarkup:
    """Bitta xabarda toifalar spiskasi."""
    from bot.category_emoji import category_label

    rows = []
    for category, count in categories_with_counts:
        label = f"{category_label(category)} ({count})"
        if len(label) > 64:
            label = label[:61] + "..."
        rows.append(
            [
                InlineKeyboardButton(
                    label,
                    callback_data=f"admin_prod:viewcat:{category['id']}",
                )
            ]
        )
    rows.append(
        [
            InlineKeyboardButton(
                "➕ Yangi toifa", callback_data="admin_prod:addcat"
            )
        ]
    )
    rows.append(
        [InlineKeyboardButton("⬅️ Orqaga", callback_data="admin:products")]
    )
    return InlineKeyboardMarkup(rows)


def admin_category_item_keyboard(category_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "📋 Mahsulotlar",
                    callback_data=f"admin_prod:viewcat:{category_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    "➕ Mahsulot qo'shish",
                    callback_data=f"admin_prod:addin:{category_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    "🗑 Toifani o'chirish",
                    callback_data=f"admin_prod:delcat:{category_id}",
                )
            ],
        ]
    )


def admin_category_products_list_keyboard(
    category_id: int, products
) -> InlineKeyboardMarkup:
    """Toifa ichidagi mahsulotlar — bitta spiska."""
    rows = [
        [
            InlineKeyboardButton(
                "➕ Mahsulot qo'shish",
                callback_data=f"admin_prod:addin:{category_id}",
            )
        ],
        [
            InlineKeyboardButton(
                "⬅️ Toifalar",
                callback_data="admin_prod:cats",
            ),
        ],
    ]
    max_buttons = 100
    for product in products:
        if len(rows) >= max_buttons - 1:
            break
        mark = "✅" if product["is_active"] else "🚫"
        rows.append(
            [
                InlineKeyboardButton(
                    f"{mark} {product['name']} — {product['price']:,}",
                    callback_data=f"admin_prod:item:{product['id']}",
                )
            ]
        )
    rows.append(
        [
            InlineKeyboardButton(
                "🗑 Toifani o'chirish",
                callback_data=f"admin_prod:delcat:{category_id}",
            ),
        ]
    )
    return InlineKeyboardMarkup(rows)


def admin_category_products_header_keyboard(category_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "➕ Mahsulot qo'shish",
                    callback_data=f"admin_prod:addin:{category_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Toifalar",
                    callback_data="admin_prod:cats",
                )
            ],
        ]
    )


def admin_product_item_keyboard(product_id: int, is_active: bool) -> InlineKeyboardMarkup:
    toggle_label = "🚫 Yashirish" if is_active else "✅ Ko'rsatish"
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "📝 Nom", callback_data=f"admin_prod:name:{product_id}"
                ),
                InlineKeyboardButton(
                    "💰 Narx", callback_data=f"admin_prod:price:{product_id}"
                ),
            ],
            [
                InlineKeyboardButton(
                    "📁 Toifa", callback_data=f"admin_prod:cat:{product_id}"
                ),
                InlineKeyboardButton(
                    "📄 Izoh", callback_data=f"admin_prod:desc:{product_id}"
                ),
            ],
            [
                InlineKeyboardButton(
                    "📐 O'lcham", callback_data=f"admin_prod:size:{product_id}"
                ),
                InlineKeyboardButton(
                    "🖼 Rasm", callback_data=f"admin_prod:photo:{product_id}"
                ),
            ],
            [
                InlineKeyboardButton(
                    "🔥 Aksiya", callback_data=f"admin_prod:sale:{product_id}"
                ),
            ],
            [
                InlineKeyboardButton(
                    toggle_label, callback_data=f"admin_prod:toggle:{product_id}"
                ),
                InlineKeyboardButton(
                    "🗑 O'chirish", callback_data=f"admin_prod:del:{product_id}"
                ),
            ],
        ]
    )


def admin_variant_item_keyboard(variant_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🗑 O'lchamni o'chirish",
                    callback_data=f"admin_prod:delsize:{variant_id}",
                )
            ]
        ]
    )


def admin_order_keyboard(order_id: int) -> InlineKeyboardMarkup:
    buttons = []
    for status_key, label in ORDER_STATUS_LABELS.items():
        if status_key == "new":
            continue
        buttons.append(
            InlineKeyboardButton(
                label,
                callback_data=f"admin_status:{order_id}:{status_key}",
            )
        )

    rows = [buttons[i : i + 2] for i in range(0, len(buttons), 2)]
    rows.append(
        [
            InlineKeyboardButton(
                "🗑 Ma'lumotni o'chirish",
                callback_data=f"admin_del_order:{order_id}",
            )
        ]
    )
    return InlineKeyboardMarkup(rows)


def admin_delete_order_confirm_keyboard(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ Ha, o'chirilsin",
                    callback_data=f"admin_del_order_yes:{order_id}",
                ),
                InlineKeyboardButton(
                    "❌ Yo'q",
                    callback_data=f"admin_del_order_no:{order_id}",
                ),
            ]
        ]
    )


def courier_order_keyboard(order_id: int) -> InlineKeyboardMarkup:
    """Kuryer uchun: faqat accepted / in_delivery / delivered."""
    allowed = ("accepted", "in_delivery", "delivered")
    buttons = [
        InlineKeyboardButton(
            ORDER_STATUS_LABELS[status],
            callback_data=f"admin_status:{order_id}:{status}",
        )
        for status in allowed
        if status in ORDER_STATUS_LABELS
    ]
    rows = [buttons[i : i + 2] for i in range(0, len(buttons), 2)]
    return InlineKeyboardMarkup(rows)


def rating_keyboard(order_id: int) -> InlineKeyboardMarkup:
    stars = [
        InlineKeyboardButton("⭐" * n, callback_data=f"rate:{order_id}:{n}")
        for n in range(1, 6)
    ]
    return InlineKeyboardMarkup([stars[:3], stars[3:]])


def language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="lang:uz"),
                InlineKeyboardButton("🇷🇺 Русский", callback_data="lang:ru"),
            ]
        ]
    )


def recurring_interval_keyboard(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("7 kun", callback_data=f"recur_set:{order_id}:7"),
                InlineKeyboardButton("14 kun", callback_data=f"recur_set:{order_id}:14"),
                InlineKeyboardButton("30 kun", callback_data=f"recur_set:{order_id}:30"),
            ],
            [InlineKeyboardButton("❌ Bekor", callback_data="recur_cancel")],
        ]
    )
