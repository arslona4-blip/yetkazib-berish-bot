from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup

STATUS_LABELS = {
    "new": "🆕 Yangi",
    "accepted": "✅ Qabul",
    "delivered": "📦 Yetkazildi",
    "cancelled": "❌ Bekor",
}


def main_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    rows = [
        ["💬 AI suhbat", "📦 Katalog"],
        ["🛒 Savat", "✅ Buyurtma"],
        ["📋 Mening buyurtmalarim", "ℹ️ Do‘kon"],
    ]
    if is_admin:
        rows.append(["🛠 Admin"])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)


def categories_keyboard(categories: list[str]) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton("📋 Hammasi", callback_data="cat:all")]
    ]
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
    buttons.append(
        [InlineKeyboardButton("◀️ Kategoriyalar", callback_data="cat:menu")]
    )
    return InlineKeyboardMarkup(buttons)


def search_results_keyboard(products: list) -> InlineKeyboardMarkup:
    buttons = []
    for p in products[:6]:
        buttons.append(
            [
                InlineKeyboardButton(
                    f"➕ {p['name']}",
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
                InlineKeyboardButton("➖", callback_data=f"qty:-:{pid}"),
                InlineKeyboardButton(
                    f"{it['name'][:18]} ×{it['quantity']}",
                    callback_data="noop",
                ),
                InlineKeyboardButton("➕", callback_data=f"qty:+:{pid}"),
            ]
        )
    buttons.append(
        [
            InlineKeyboardButton("🗑 Tozalash", callback_data="cart:clear"),
            InlineKeyboardButton("✅ Buyurtma", callback_data="cart:order"),
        ]
    )
    return InlineKeyboardMarkup(buttons)


def admin_order_keyboard(order_id: int, status: str = "new") -> InlineKeyboardMarkup:
    row = []
    if status == "new":
        row = [
            InlineKeyboardButton("✅ Qabul", callback_data=f"ord:ok:{order_id}"),
            InlineKeyboardButton("❌ Bekor", callback_data=f"ord:no:{order_id}"),
        ]
    elif status == "accepted":
        row = [
            InlineKeyboardButton(
                "📦 Yetkazildi", callback_data=f"ord:done:{order_id}"
            ),
            InlineKeyboardButton("❌ Bekor", callback_data=f"ord:no:{order_id}"),
        ]
    else:
        row = [InlineKeyboardButton("—", callback_data="noop")]
    return InlineKeyboardMarkup([row])
