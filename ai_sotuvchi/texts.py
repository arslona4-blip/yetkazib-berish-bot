"""Professional matnlar va formatlash."""

from __future__ import annotations

from ai_sotuvchi.config import (
    DELIVERY_FEE,
    MIN_ORDER_AMOUNT,
    SHOP_HOURS,
    SHOP_NAME,
    SHOP_PHONE,
    money,
)


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
        f"💳 Minimal buyurtma: <b>{money(MIN_ORDER_AMOUNT)}</b>\n"
        f"🚚 Yetkazish: <b>{money(DELIVERY_FEE)}</b>\n\n"
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
        f"🚚 Yetkazish: {money(DELIVERY_FEE)}\n"
        "————————————\n"
        "Buyurtmadan keyin admin tasdiqlaydi."
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
    note: str = "",
    subtotal: int | None = None,
    delivery_fee: int | None = None,
) -> str:
    lines = [
        f"<b>Buyurtma #{order_id}</b>",
        status_line(status),
        "————————————",
        f"👤 {customer}",
        f"📞 {phone}",
        f"📍 {address}",
    ]
    if note:
        lines.append(f"📝 {note}")
    lines.append("————————————")
    for it in items:
        lines.append(
            f"• {it.get('name')} × {it.get('quantity')} — "
            f"{money(int(it.get('line_total') or 0))}"
        )
    lines.append("————————————")
    if subtotal is not None:
        lines.append(f"Mahsulotlar: {money(subtotal)}")
    if delivery_fee is not None:
        lines.append(f"Yetkazish: {money(delivery_fee)}")
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
    lines.append(f"Mahsulotlar: {money(total)}")
    lines.append(f"Yetkazish: {money(DELIVERY_FEE)}")
    lines.append(f"<b>Jami: {money(total + DELIVERY_FEE)}</b>")
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
        "➕ Mahsulot · /orders · /stats\n"
        "📢 Xabar — /broadcast"
    )


def admin_products_spiska(groups: list[tuple[str, list]]) -> str:
    """Toifa bo‘yicha alifbo tartibidagi mahsulotlar spiskasi."""
    if not groups:
        return "<b>Mahsulotlar</b>\nHozircha mahsulot yo‘q."
    total = sum(len(items) for _, items in groups)
    lines = [
        f"<b>Mahsulotlar spiskasi</b> · {total} ta",
        f"Toifa: <b>{len(groups)}</b> ta · alifbo tartibida",
        "————————————",
    ]
    for cat, items in groups:
        lines.append(f"\n📁 <b>{cat}</b> ({len(items)})")
        for p in items:
            mark = "✅" if p["is_active"] else "🚫"
            lines.append(
                f"{mark} {p['name']} — {money(int(p['price']))} "
                f"<code>#{p['id']}</code>"
            )
    lines.append("\n————————————")
    lines.append("<i>Pastda har bir mahsulot uchun tugmalar.</i>")
    return "\n".join(lines)
