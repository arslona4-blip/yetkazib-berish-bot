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
    buttons = []
    for p in products[:6]:
        buttons.append(
            [
                InlineKeyboardButton(
                    f"Savatga · {p['name']}",
                    callback_data=f"add:{p['id']}",
                )
            ]
        )
    return InlineKeyboardMarkup(buttons) if buttons else InlineKeyboardMarkup([])


def cart_keyboard(items: list | None = None) -> InlineKeyboardMarkup:
    buttons: list[list[InlineKeyboardButton]] = []
    for it in items or []:
        pid = it["product_id"]
        buttons.append(
            [
                InlineKeyboardButton("−", callback_data=f"qty:-:{pid}"),
                InlineKeyboardButton(
                    f"{it['name'][:16]} ×{it['quantity']}",
                    callback_data="noop",
                ),
                InlineKeyboardButton("+", callback_data=f"qty:+:{pid}"),
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
                InlineKeyboardButton(
                    "Narxni o‘zgartirish", callback_data=f"ap:price:{product_id}"
                ),
                InlineKeyboardButton(
                    "Yashirish" if active else "Yoqish",
                    callback_data=f"ap:toggle:{product_id}",
                ),
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


# re-export
__all__ = ["STATUS_LABELS"]