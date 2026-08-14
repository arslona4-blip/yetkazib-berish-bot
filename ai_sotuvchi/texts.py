"""Professional matnlar va formatlash."""

from __future__ import annotations

from ai_sotuvchi.config import MIN_ORDER_AMOUNT, SHOP_HOURS, SHOP_NAME, SHOP_PHONE, money


STATUS_LABELS = {
    "new": "Yangi",
    "accepted": "Qabul qilindi",
    "delivering": "Yetkazilmoqda",
    "delivered": "Yetkazildi",
    "cancelled": "Bekor qilindi",
}

STATUS_ICON = {
    "new": "🆕",
    "accepted": "✅",
    "delivering": "🚚",
    "delivered": "📦",
    "cancelled": "❌",
}


def status_line(status: str) -> str:
    icon = STATUS_ICON.get(status, "•")
    label = STATUS_LABELS.get(status, status)
    return f"{icon} {label}"


def welcome_text(first_name: str | None = None) -> str:
    name = (first_name or "").strip() or "mijoz"
    return (
        f"<b>{SHOP_NAME}</b>\n"
        f"Assalomu alaykum, {name}!\n\n"
        "Men do‘koningizning raqamli sotuvchisiman.\n"
        "Mahsulot qidiraman, savat yig‘aman va buyurtmani qabul qilaman.\n\n"
        f"⏰ Ish vaqti: <b>{SHOP_HOURS}</b>\n"
        f"📞 Aloqa: <b>{SHOP_PHONE}</b>\n"
        f"💳 Minimal buyurtma: <b>{money(MIN_ORDER_AMOUNT)}</b>\n\n"
        "<i>Yozing:</i> «guruch bormi?» yoki «2 ta sut»\n"
        "yoki pastdagi menyudan boshlang."
    )


def shop_card() -> str:
    return (
        f"<b>{SHOP_NAME}</b>\n"
        "————————————\n"
        f"⏰ {SHOP_HOURS}\n"
        f"📞 {SHOP_PHONE}\n"
        f"💳 Minimal buyurtma: {money(MIN_ORDER_AMOUNT)}\n"
        "————————————\n"
        "Yetkazib berish — buyurtma berilganda tasdiqlanadi."
    )


def order_receipt(
    order_id: int,
    *,
    customer: str,
    phone: str,
    address: str,
    items: list[dict],
    total: int,
    status: str = "new",
) -> str:
    lines = [
        f"<b>Buyurtma #{order_id}</b>",
        status_line(status),
        "————————————",
        f"👤 {customer}",
        f"📞 {phone}",
        f"📍 {address}",
        "————————————",
    ]
    for it in items:
        lines.append(
            f"• {it.get('name')} × {it.get('quantity')} — "
            f"{money(int(it.get('line_total') or 0))}"
        )
    lines.append("————————————")
    lines.append(f"<b>Jami: {money(total)}</b>")
    return "\n".join(lines)


def cart_text(items: list[dict], total: int) -> str:
    if not items:
        return "Savat bo‘sh.\nKatalogdan mahsulot qo‘shing."
    lines = ["<b>Savat</b>", "————————————"]
    for it in items:
        lines.append(
            f"• {it['name']} × {it['quantity']} — {money(it['line_total'])}"
        )
    lines.append("————————————")
    lines.append(f"<b>Jami: {money(total)}</b>")
    if total < MIN_ORDER_AMOUNT:
        need = MIN_ORDER_AMOUNT - total
        lines.append(f"Minimal gacha yana: {money(need)}")
    return "\n".join(lines)


def admin_home(stats: dict) -> str:
    return (
        f"<b>Boshqaruv paneli</b> · {SHOP_NAME}\n"
        "————————————\n"
        f"Mahsulotlar: <b>{stats['products']}</b>\n"
        f"Yangi buyurtmalar: <b>{stats['new']}</b>\n"
        f"Jarayonda: <b>{stats.get('accepted', 0) + stats.get('delivering', 0)}</b>\n"
        f"Yetkazilgan: <b>{stats['delivered']}</b>\n"
        f"Tushum: <b>{money(stats['revenue'])}</b>\n"
        "————————————\n"
        "➕ Mahsulot — yangi mahsulot\n"
        "📦 Buyurtmalar — /orders\n"
        "📊 Statistika — /stats"
    )
