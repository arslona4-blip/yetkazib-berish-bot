from telegram import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from ai_sotuvchi.config import money
from ai_sotuvchi.matching import human_pack_label, kg_money_options
from ai_sotuvchi.texts import STATUS_LABELS


def main_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    rows = [
        ["Katalog", "Savat"],
        ["Buyurtma berish", "Mening buyurtmalarim"],
        ["Do‘kon haqida"],
    ]
    if is_admin:
        rows.append(["Admin", "➕ Mahsulot"])
        rows.append(["📦 Mahsulotlar", "📢 Xabar"])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)


def cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup([["Bekor qilish"]], resize_keyboard=True)


def phone_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("📱 Raqamni yuborish", request_contact=True)],
            ["Bekor qilish"],
        ],
        resize_keyboard=True,
    )


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
    buttons = []
    money_opts = kg_money_options(products) if products else []
    for p in products[:8]:
        label = human_pack_label(str(p["name"]))
        show = label if label != str(p["name"]) else str(p["name"])
        price = money(int(p["price"])).replace(" so‘m", "")
        buttons.append(
            [
                InlineKeyboardButton(
                    f"{show} — {price}",
                    callback_data=f"add:{p['id']}",
                )
            ]
        )
    for opt in money_opts:
        buttons.append(
            [
                InlineKeyboardButton(
                    f"{opt['label']} ({opt['detail']})",
                    callback_data=f"som:{opt['product_id']}:{opt['amount']}",
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
                    f"{it['name'][:18]} ×{it['quantity']}",
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


def admin_product_keyboard(product_id: int, active: bool = True) -> InlineKeyboardMarkup:
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
                InlineKeyboardButton("📄 Izoh", callback_data=f"ap:desc:{product_id}"),
                InlineKeyboardButton(
                    "Yashirish" if active else "Yoqish",
                    callback_data=f"ap:toggle:{product_id}",
                ),
            ],
            [InlineKeyboardButton("← Spiska", callback_data="ap:list")],
        ]
    )


def admin_categories_keyboard(categories: list[str]) -> InlineKeyboardMarkup:
    buttons: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for cat in categories:
        row.append(InlineKeyboardButton(cat, callback_data=f"alist:{cat}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("Barchasi", callback_data="alist:")])
    return InlineKeyboardMarkup(buttons)


def admin_product_list_keyboard(products: list) -> InlineKeyboardMarkup:
    buttons = []
    for p in products[:40]:
        mark = "" if p["is_active"] else " 🚫"
        buttons.append(
            [
                InlineKeyboardButton(
                    f"{p['name']} — {money(int(p['price']))}{mark}",
                    callback_data=f"ap:view:{p['id']}",
                )
            ]
        )
    buttons.append([InlineKeyboardButton("← Toifalar", callback_data="ap:list")])
    return InlineKeyboardMarkup(buttons)


def saved_checkout_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Ha, shu bilan", callback_data="chk:yes"),
                InlineKeyboardButton("O‘zgartirish", callback_data="chk:no"),
            ]
        ]
    )


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