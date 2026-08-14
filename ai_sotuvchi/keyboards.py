from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup


def main_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    rows = [
        ["💬 AI suhbat", "📦 Katalog"],
        ["🛒 Savat", "✅ Buyurtma"],
        ["ℹ️ Do‘kon"],
    ]
    if is_admin:
        rows.append(["🛠 Admin"])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)


def catalog_keyboard(products: list) -> InlineKeyboardMarkup:
    buttons = []
    for p in products[:20]:
        buttons.append(
            [
                InlineKeyboardButton(
                    f"➕ {p['name']} · {int(p['price']):,}".replace(",", " "),
                    callback_data=f"add:{p['id']}",
                )
            ]
        )
    if not buttons:
        buttons = [[InlineKeyboardButton("Mahsulot yo‘q", callback_data="noop")]]
    return InlineKeyboardMarkup(buttons)


def cart_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🗑 Tozalash", callback_data="cart:clear"),
                InlineKeyboardButton("✅ Buyurtma", callback_data="cart:order"),
            ]
        ]
    )


def admin_order_keyboard(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ Qabul", callback_data=f"ord:ok:{order_id}"
                ),
                InlineKeyboardButton(
                    "❌ Bekor", callback_data=f"ord:no:{order_id}"
                ),
            ]
        ]
    )
