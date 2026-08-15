from telegram import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup

from ai_sotuvchi.config import money
from ai_sotuvchi.texts import STATUS_LABELS


def main_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    rows = [
        ["Katalog", "Savat"],
        ["Buyurtma berish", "Mening buyurtmalarim"],
        ["Do‘kon haqida"],
    ]
    if is_admin:
        rows.append(["Admin", "➕ Mahsulot"])
        rows.append(["📢 Xabar"])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)


def cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup([["Bekor qilish"]], resize_keyboard=True)


def skip_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup([["O‘tkazib yuborish"], ["Bekor qilish"]], resize_keyboard=True)


def categories_keyboard(categories: list[str]) -> InlineKeyboardMarkup:
    buttons = [[InlineKeyboardButton("Barchasi", callback_data="cat:all")]]
    row: list[InlineKeyboardButton] = []
    for cat in categories:
        row.append(InlineKeyboardButton(cat, callback_data=f"cat:{cat}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(buttons)


def catalog_keyboard(products: list) -> InlineKeyboardMarkup:
    buttons = []
    for p in products[:20]:
        price = money(int(p["price"])).replace(" so‘m", "")
        buttons.append(
            [
                InlineKeyboardButton(
                    f"{p['name']} — {price}",
                    callback_data=f"add:{p['id']}",
                )
            ]
        )
    if not buttons:
        buttons = [[InlineKeyboardButton("Bo‘sh", callback_data="noop")]]
    buttons.append([InlineKeyboardButton("← Kategoriyalar", callback_data="cat:menu")])
    return InlineKeyboardMarkup(buttons)


def search_results_keyboard(products: list) -> InlineKeyboardMarkup:
    """Qadoq + (kg bo‘lsa) 5000/10000 so‘mlik tugmalar."""
    from ai_sotuvchi.ai import _human_pack_label, kg_money_options

    buttons: list[list[InlineKeyboardButton]] = []
    for p in products[:8]:
        label = _human_pack_label(str(p["name"]))
        show = label if label != str(p["name"]) else str(p["name"])
        btn = f"{show} — {money(int(p['price']))}"
        if len(btn) > 64:
            btn = btn[:61] + "…"
        buttons.append(
            [
                InlineKeyboardButton(
                    btn,
                    callback_data=f"add:{p['id']}",
                )
            ]
        )
    for opt in kg_money_options(products):
        btn = f"{opt['label']} · {opt['detail']}"
        if len(btn) > 64:
            btn = btn[:61] + "…"
        buttons.append(
            [
                InlineKeyboardButton(
                    btn,
                    callback_data=f"addm:{opt['product_id']}:{opt['amount']}",
                )
            ]
        )
    return InlineKeyboardMarkup(buttons) if buttons else InlineKeyboardMarkup([])


def cart_keyboard(items: list | None = None) -> InlineKeyboardMarkup:
    buttons: list[list[InlineKeyboardButton]] = []
    for it in items or []:
        cid = it.get("cart_id") or it["product_id"]
        buttons.append(
            [
                InlineKeyboardButton("−", callback_data=f"qty:-:{cid}"),
                InlineKeyboardButton(
                    f"{it['name'][:16]} ×{it['quantity']}",
                    callback_data="noop",
                ),
                InlineKeyboardButton("+", callback_data=f"qty:+:{cid}"),
            ]
        )
    buttons.append(
        [
            InlineKeyboardButton("Tozalash", callback_data="cart:clear"),
            InlineKeyboardButton("Buyurtma berish", callback_data="cart:order"),
        ]
    )
    return InlineKeyboardMarkup(buttons)


def admin_order_keyboard(order_id: int, status: str = "new") -> InlineKeyboardMarkup:
    if status == "new":
        row = [
            InlineKeyboardButton("Qabul qilish", callback_data=f"ord:ok:{order_id}"),
            InlineKeyboardButton("Bekor", callback_data=f"ord:no:{order_id}"),
        ]
    elif status == "accepted":
        row = [
            InlineKeyboardButton("Yetkazishga", callback_data=f"ord:go:{order_id}"),
            InlineKeyboardButton("Bekor", callback_data=f"ord:no:{order_id}"),
        ]
    elif status == "delivering":
        row = [
            InlineKeyboardButton("Yetkazildi", callback_data=f"ord:done:{order_id}"),
        ]
    else:
        row = [
            InlineKeyboardButton(
                STATUS_LABELS.get(status, status), callback_data="noop"
            )
        ]
    return InlineKeyboardMarkup([row])


def admin_products_manage_keyboard(products: list) -> InlineKeyboardMarkup:
    """Toifa bo‘yicha mahsulotlar — tahrirlash uchun."""
    from collections import defaultdict

    grouped: dict[str, list] = defaultdict(list)
    for p in products:
        grouped[str(p["category"] or "Umumiy")].append(p)

    rows: list[list[InlineKeyboardButton]] = []
    for cat in sorted(grouped.keys(), key=lambda x: x.casefold()):
        items = sorted(
            grouped[cat],
            key=lambda p: (str(p["name"] or "").casefold(), int(p["id"])),
        )
        header = f"📁 {cat} · {len(items)}"
        if len(header) > 64:
            header = header[:61] + "…"
        rows.append([InlineKeyboardButton(header, callback_data="noop")])
        for p in items:
            mark = "✅" if p["is_active"] else "🚫"
            label = f"{mark} {p['name']} — {money(int(p['price']))}"
            if len(label) > 64:
                label = label[:61] + "…"
            rows.append(
                [
                    InlineKeyboardButton(
                        label, callback_data=f"ap:edit:{int(p['id'])}"
                    )
                ]
            )
    if not rows:
        rows = [[InlineKeyboardButton("Bo‘sh", callback_data="noop")]]
    return InlineKeyboardMarkup(rows)


def admin_product_keyboard(product_id: int, active: bool = True) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✏️ Tahrirlash", callback_data=f"ap:edit:{product_id}"
                ),
            ],
            [
                InlineKeyboardButton(
                    "Narx", callback_data=f"ap:price:{product_id}"
                ),
                InlineKeyboardButton(
                    "Yashirish" if active else "Yoqish",
                    callback_data=f"ap:toggle:{product_id}",
                ),
            ],
        ]
    )


def admin_product_edit_keyboard(product_id: int, active: bool = True) -> InlineKeyboardMarkup:
    """To‘liq tahrirlash menyusi."""
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("📝 Nom", callback_data=f"ap:name:{product_id}"),
                InlineKeyboardButton("💰 Narx", callback_data=f"ap:price:{product_id}"),
            ],
            [
                InlineKeyboardButton("📁 Toifa", callback_data=f"ap:cat:{product_id}"),
                InlineKeyboardButton("🖼 Rasm", callback_data=f"ap:photo:{product_id}"),
            ],
            [
                InlineKeyboardButton(
                    "📄 Izoh", callback_data=f"ap:desc:{product_id}"
                ),
                InlineKeyboardButton(
                    "🚫 Yashirish" if active else "✅ Yoqish",
                    callback_data=f"ap:toggle:{product_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    "← Spiskaga", callback_data="ap:list:0"
                ),
            ],
        ]
    )


def admin_edit_category_keyboard(product_id: int, categories: list[str] | tuple[str, ...]) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for cat in categories:
        row.append(
            InlineKeyboardButton(cat, callback_data=f"ap:setcat:{product_id}:{cat}")
        )
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append(
        [InlineKeyboardButton("← Orqaga", callback_data=f"ap:edit:{product_id}")]
    )
    return InlineKeyboardMarkup(rows)


def my_order_keyboard(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "Qayta buyurtma", callback_data=f"reorder:{order_id}"
                )
            ]
        ]
    )


def product_category_keyboard(categories: list[str] | tuple[str, ...]) -> InlineKeyboardMarkup:
    buttons: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for cat in categories:
        row.append(InlineKeyboardButton(cat, callback_data=f"pcat:{cat}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(buttons)


def bot_commands(is_admin: bool = False) -> list[BotCommand]:
    cmds = [
        BotCommand("start", "Bosh menyu"),
        BotCommand("katalog", "Mahsulotlar"),
        BotCommand("cart", "Savat"),
        BotCommand("myorders", "Mening buyurtmalarim"),
        BotCommand("info", "Do‘kon haqida"),
    ]
    if is_admin:
        cmds.extend(
            [
                BotCommand("admin", "Boshqaruv"),
                BotCommand("orders", "Buyurtmalar"),
                BotCommand("stats", "Statistika"),
                BotCommand("add", "Mahsulot qo‘shish"),
                BotCommand("broadcast", "Mijozlarga xabar"),
            ]
        )
    return cmds


# re-export
__all__ = ["STATUS_LABELS"]