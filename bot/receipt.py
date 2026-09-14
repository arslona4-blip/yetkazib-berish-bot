"""Elektron chek — Telegram PNG/PDF + ochiq web sahifa."""

from __future__ import annotations

import hashlib
import hmac
import html
import logging
import os
from typing import Any

from bot.config import (
    BOT_TOKEN,
    MINIAPP_URL,
    ORDER_STATUS_LABELS,
    PAYMENT_STATUS_LABELS,
    SHOP_ADDRESS,
    SHOP_HOURS,
    SHOP_NAME,
    SHOP_PHONE,
    WEBHOOK_URL,
)
from bot.database import get_order, get_order_items, get_user
from bot.timeutil import format_dt

logger = logging.getLogger(__name__)


def _money(n: int | float) -> str:
    return f"{int(n):,}".replace(",", " ")


def _row_get(row, key: str, default=None):
    try:
        keys = row.keys()
    except Exception:
        return default
    if key in keys:
        val = row[key]
        return default if val is None else val
    return default


def _is_pos_pickup(pickup: str) -> bool:
    low = (pickup or "").lower()
    return "kassa" in low or "pos" in low


def _receipt_secret() -> str:
    return (os.getenv("RECEIPT_SECRET") or BOT_TOKEN or "receipt-dev").strip()


def build_receipt_token(order_id: int) -> str:
    """Imzolangan token — URL taxmin qilinmasin."""
    oid = int(order_id)
    digest = hmac.new(
        _receipt_secret().encode("utf-8"),
        str(oid).encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()[:24]
    return f"{oid}.{digest}"


def parse_receipt_token(token: str) -> int | None:
    """Token yaroqli bo'lsa order_id, aks holda None."""
    raw = (token or "").strip()
    if not raw or "." not in raw:
        return None
    left, sig = raw.split(".", 1)
    if not left.isdigit() or not sig:
        return None
    order_id = int(left)
    expected = build_receipt_token(order_id)
    if not hmac.compare_digest(expected, f"{order_id}.{sig}"):
        return None
    return order_id


def receipt_base_url() -> str:
    """Public host: MINIAPP_URL, yo'q bo'lsa WEBHOOK_URL."""
    return (MINIAPP_URL or WEBHOOK_URL or "").rstrip("/")


def receipt_public_url(order_id: int) -> str:
    token = build_receipt_token(order_id)
    base = receipt_base_url()
    if base:
        return f"{base}/chek/{token}"
    return f"/chek/{token}"


def _finalize_receipt_data(data: dict[str, Any]) -> dict[str, Any]:
    """Yetkazish haqqi va boshqa hisoblar."""
    subtotal = int(data.get("subtotal") or 0)
    discount = int(data.get("discount") or 0)
    bonus = int(data.get("bonus") or 0)
    total = int(data.get("total") or 0)
    if subtotal > 0:
        delivery = max(0, total - subtotal + discount + bonus)
        data["delivery_fee"] = delivery
    return data


def load_receipt_data(order_id: int) -> dict[str, Any] | None:
    """Chek uchun buyurtma ma'lumoti. POS/kassa → None."""
    order = get_order(order_id)
    if not order:
        return None
    if _is_pos_pickup(str(_row_get(order, "pickup_address", "") or "")):
        return None

    items_raw = get_order_items(order_id)
    user = get_user(int(order["user_id"]))
    items: list[dict[str, Any]] = []
    for item in items_raw:
        qty = int(item["quantity"] or 0)
        price = int(item["price"] or 0)
        items.append(
            {
                "name": str(item["product_name"] or "Mahsulot"),
                "qty": qty,
                "price": price,
                "line_total": qty * price,
            }
        )

    data = {
        "order_id": int(order_id),
        "shop_name": str(SHOP_NAME or "Do'kon"),
        "created": format_dt(_row_get(order, "created_at")),
        "status": ORDER_STATUS_LABELS.get(order["status"], order["status"]),
        "payment": PAYMENT_STATUS_LABELS.get(
            order["payment_status"], order["payment_status"]
        ),
        "items": items,
        "subtotal": int(_row_get(order, "subtotal", 0) or 0),
        "discount": int(_row_get(order, "discount", 0) or 0),
        "bonus": int(_row_get(order, "bonus_spent", 0) or 0),
        "total": int(order["price"] or 0),
        "delivery_fee": 0,
        "gift": str(_row_get(order, "gift_choice", "") or "").strip(),
        "customer": str(_row_get(user, "full_name", "") or "") if user else "",
        "phone": str(order["phone"] or ""),
        "delivery_address": str(_row_get(order, "delivery_address", "") or "—"),
        "shop_address": str(SHOP_ADDRESS or ""),
        "shop_phone": str(SHOP_PHONE or ""),
        "shop_hours": str(SHOP_HOURS or ""),
    }
    return _finalize_receipt_data(data)


def format_electronic_receipt_html(order_id: int) -> str:
    """Telegram parse_mode=HTML uchun elektron chek matni."""
    data = load_receipt_data(order_id)
    if not data:
        return ""

    e = html.escape
    shop = e(data["shop_name"])
    lines: list[str] = [
        f"🧾 <b>Elektron chek</b>",
        f"<b>{shop}</b>",
        "━━━━━━━━━━━━━━",
        f"Buyurtma: <b>#{data['order_id']}</b>",
        f"Sana: {e(data['created'])}",
        f"Holat: {e(str(data['status']))}",
        f"To'lov: {e(str(data['payment']))}",
        "━━━━━━━━━━━━━━",
        "<b>Mahsulotlar</b>",
    ]

    if not data["items"]:
        lines.append("<i>— Mahsulotlar yo'q —</i>")
    else:
        for it in data["items"]:
            lines.append(e(it["name"]))
            lines.append(
                f"  {it['qty']} × {_money(it['price'])} = "
                f"<b>{_money(it['line_total'])}</b> so'm"
            )

    lines.append("━━━━━━━━━━━━━━")
    if data["subtotal"] > 0:
        lines.append(f"Oraliq jami: {_money(data['subtotal'])} so'm")
    if data.get("delivery_fee", 0) > 0:
        lines.append(f"Yetkazish: {_money(data['delivery_fee'])} so'm")
    if data["discount"] > 0:
        lines.append(f"Chegirma: −{_money(data['discount'])} so'm")
    if data["bonus"] > 0:
        lines.append(f"Bonus: −{_money(data['bonus'])} so'm")
    if data.get("gift"):
        lines.append(f"Sovg‘a: {e(data['gift'])}")
    lines.append(f"<b>JAMI: {_money(data['total'])} so'm</b>")
    lines.append("━━━━━━━━━━━━━━")

    if data["customer"]:
        lines.append(f"Mijoz: {e(data['customer'])}")
    lines.append(f"Telefon: {e(data['phone'] or '—')}")
    lines.append(f"Yetkazish: {e(data['delivery_address'])}")

    shop_bits = [
        x for x in (data["shop_address"], data["shop_phone"], data["shop_hours"]) if x
    ]
    if shop_bits:
        lines.append(e(" · ".join(shop_bits)))

    url = receipt_public_url(order_id)
    lines.append("")
    lines.append(f'To\'liq chek: <a href="{html.escape(url, quote=True)}">{e(url)}</a>')
    lines.append("")
    lines.append("Rahmat! Yana kutib qolamiz 🌿")
    return "\n".join(lines)


def render_receipt_page_html(order_id: int) -> str | None:
    """Brauzer uchun chiroyli HTML sahifa."""
    data = load_receipt_data(order_id)
    if not data:
        return None

    e = html.escape
    item_rows = ""
    if not data["items"]:
        item_rows = '<tr><td colspan="3" class="muted">Mahsulotlar yo\'q</td></tr>'
    else:
        for it in data["items"]:
            item_rows += (
                f"<tr>"
                f"<td>{e(it['name'])}</td>"
                f"<td class='num'>{it['qty']} × {_money(it['price'])}</td>"
                f"<td class='num'><b>{_money(it['line_total'])}</b></td>"
                f"</tr>"
            )

    extras = ""
    if data["subtotal"] > 0:
        extras += (
            f"<div class='row'><span>Oraliq jami</span>"
            f"<span>{_money(data['subtotal'])} so'm</span></div>"
        )
    if data.get("delivery_fee", 0) > 0:
        extras += (
            f"<div class='row'><span>Yetkazish</span>"
            f"<span>{_money(data['delivery_fee'])} so'm</span></div>"
        )
    if data["discount"] > 0:
        extras += (
            f"<div class='row'><span>Chegirma</span>"
            f"<span>−{_money(data['discount'])} so'm</span></div>"
        )
    if data["bonus"] > 0:
        extras += (
            f"<div class='row'><span>Bonus</span>"
            f"<span>−{_money(data['bonus'])} so'm</span></div>"
        )
    if data.get("gift"):
        extras += (
            f"<div class='row'><span>Sovg‘a</span>"
            f"<span>{e(data['gift'])}</span></div>"
        )

    customer_block = ""
    if data["customer"]:
        customer_block = f"<p><span class='lbl'>Mijoz</span> {e(data['customer'])}</p>"

    shop_bits = [
        x for x in (data["shop_address"], data["shop_phone"], data["shop_hours"]) if x
    ]
    shop_footer = e(" · ".join(shop_bits)) if shop_bits else ""

    return f"""<!doctype html>
<html lang="uz">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Elektron chek · #{data['order_id']}</title>
<style>
:root {{
  --green: #228b4a;
  --green-dark: #166e37;
  --bg: #f4faf6;
  --card: #ffffff;
  --text: #1c201e;
  --muted: #647065;
  --line: #d2dcd6;
}}
* {{ box-sizing: border-box; }}
body {{
  margin: 0; padding: 20px 14px 40px;
  font-family: "Segoe UI", system-ui, -apple-system, sans-serif;
  background: linear-gradient(180deg, #e8f5ec 0%, var(--bg) 40%, #eef6f1 100%);
  color: var(--text); min-height: 100vh;
}}
.wrap {{ max-width: 440px; margin: 0 auto; }}
.header {{
  background: linear-gradient(135deg, var(--green), var(--green-dark));
  color: #fff; border-radius: 16px 16px 0 0;
  padding: 22px 20px 18px; text-align: center;
}}
.header .eyebrow {{ opacity: .9; font-size: .85rem; margin: 0 0 6px; }}
.header h1 {{ margin: 0; font-size: 1.35rem; font-weight: 700; }}
.card {{
  background: var(--card); border-radius: 0 0 16px 16px;
  padding: 18px 18px 22px;
  box-shadow: 0 8px 28px rgba(22, 110, 55, .12);
}}
.meta {{ font-size: .92rem; color: var(--muted); line-height: 1.55; margin-bottom: 14px; }}
.meta b {{ color: var(--text); }}
hr {{ border: 0; border-top: 1px solid var(--line); margin: 14px 0; }}
h2 {{ margin: 0 0 10px; font-size: 1rem; }}
table {{ width: 100%; border-collapse: collapse; font-size: .92rem; }}
td {{ padding: 8px 0; vertical-align: top; border-bottom: 1px solid #eef3f0; }}
td.num {{ text-align: right; white-space: nowrap; color: var(--muted); padding-left: 10px; }}
.row {{ display: flex; justify-content: space-between; gap: 12px; font-size: .92rem; color: var(--muted); margin: 4px 0; }}
.total {{
  margin-top: 10px; background: #e8f5ec; border-radius: 10px;
  padding: 12px 14px; display: flex; justify-content: space-between;
  font-weight: 700; color: var(--green-dark); font-size: 1.05rem;
}}
.lbl {{ color: var(--muted); display: inline-block; min-width: 72px; }}
.addr p {{ margin: 6px 0; font-size: .92rem; line-height: 1.45; }}
.footer {{ margin-top: 16px; text-align: center; color: var(--muted); font-size: .85rem; line-height: 1.45; }}
.thanks {{ margin-top: 14px; text-align: center; color: var(--green); font-weight: 600; }}
.dl {{ display: flex; gap: 8px; margin-top: 16px; }}
.dl a {{
  flex: 1; text-align: center; text-decoration: none; font-weight: 600;
  font-size: .9rem; padding: 10px 8px; border-radius: 10px;
  background: #e8f5ec; color: var(--green-dark);
}}
</style>
</head>
<body>
<div class="wrap">
  <div class="header">
    <p class="eyebrow">Elektron chek</p>
    <h1>{e(data['shop_name'])}</h1>
  </div>
  <div class="card">
    <div class="meta">
      Buyurtma <b>#{data['order_id']}</b><br/>
      Sana: {e(data['created'])}<br/>
      Holat: {e(str(data['status']))}<br/>
      To'lov: {e(str(data['payment']))}
    </div>
    <hr/>
    <h2>Mahsulotlar</h2>
    <table>{item_rows}</table>
    {extras}
    <div class="total"><span>JAMI</span><span>{_money(data['total'])} so'm</span></div>
    <hr/>
    <div class="addr">
      {customer_block}
      <p><span class="lbl">Telefon</span> {e(data['phone'] or '—')}</p>
      <p><span class="lbl">Manzil</span> {e(data['delivery_address'])}</p>
    </div>
    <p class="thanks">Rahmat! Yana kutib qolamiz</p>
    <div class="footer">{shop_footer}</div>
    <div class="dl">
      <a href="/chek/{e(build_receipt_token(order_id))}.png">PNG</a>
      <a href="/chek/{e(build_receipt_token(order_id))}.pdf">PDF</a>
    </div>
  </div>
</div>
</body>
</html>"""


def _font_paths(bold: bool = False) -> list[str]:
    if bold:
        return [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            r"C:\Windows\Fonts\arialbd.ttf",
            r"C:\Windows\Fonts\segoeuib.ttf",
        ]
    return [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\segoeui.ttf",
    ]


def _load_font(size: int, bold: bool = False):
    from PIL import ImageFont

    for path in _font_paths(bold):
        if os.path.isfile(path):
            try:
                return ImageFont.truetype(path, size=size)
            except Exception:
                continue
    return ImageFont.load_default()


def _wrap_text(draw, text: str, font, max_width: int) -> list[str]:
    words = str(text or "").split()
    if not words:
        return [""]
    lines: list[str] = []
    cur = words[0]
    for word in words[1:]:
        trial = f"{cur} {word}"
        if draw.textlength(trial, font=font) <= max_width:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    lines.append(cur)
    return lines


def render_receipt_image(order_id: int):
    """Pillow Image (RGB) — chek rasmi."""
    from PIL import Image, ImageDraw

    data = load_receipt_data(order_id)
    if not data:
        return None

    width = 720
    pad = 36
    green = (34, 139, 74)
    green_dark = (22, 110, 55)
    text_c = (28, 32, 30)
    muted = (100, 112, 101)
    line_c = (210, 220, 214)
    bg = (255, 255, 255)
    soft = (232, 245, 236)

    font_title = _load_font(30, bold=True)
    font_h = _load_font(22, bold=True)
    font = _load_font(20)
    font_sm = _load_font(17)
    font_bold = _load_font(20, bold=True)
    font_total = _load_font(24, bold=True)

    # Estimate height
    content_w = width - pad * 2
    y_est = 160
    y_est += 90  # meta
    items = data["items"] or []
    # rough: each item ~56px
    y_est += max(40, len(items) * 56) + 40
    y_est += 160  # totals + address + footer
    height = max(900, y_est + 80)

    img = Image.new("RGB", (width, height), bg)
    draw = ImageDraw.Draw(img)

    # Header bar
    draw.rectangle((0, 0, width, 118), fill=green)
    draw.text(
        (width // 2, 28),
        "Elektron chek",
        fill=(230, 245, 235),
        font=font_sm,
        anchor="mt",
    )
    draw.text(
        (width // 2, 58),
        data["shop_name"],
        fill=(255, 255, 255),
        font=font_title,
        anchor="mt",
    )

    y = 140
    meta_lines = [
        f"Buyurtma #{data['order_id']}",
        f"Sana: {data['created']}",
        f"Holat: {data['status']}",
        f"To'lov: {data['payment']}",
    ]
    for line in meta_lines:
        draw.text((pad, y), line, fill=muted, font=font_sm)
        y += 26

    y += 10
    draw.line((pad, y, width - pad, y), fill=line_c, width=1)
    y += 16
    draw.text((pad, y), "Mahsulotlar", fill=text_c, font=font_h)
    y += 36

    if not items:
        draw.text((pad, y), "— Mahsulotlar yo'q —", fill=muted, font=font)
        y += 32
    else:
        for it in items:
            name_lines = _wrap_text(draw, it["name"], font, content_w - 8)
            for nl in name_lines:
                draw.text((pad, y), nl, fill=text_c, font=font)
                y += 26
            detail = (
                f"{it['qty']} × {_money(it['price'])} = "
                f"{_money(it['line_total'])} so'm"
            )
            draw.text((pad, y), detail, fill=muted, font=font_sm)
            y += 30
            draw.line((pad, y, width - pad, y), fill=(238, 243, 240), width=1)
            y += 10

    y += 6
    draw.line((pad, y, width - pad, y), fill=line_c, width=1)
    y += 16

    def money_row(label: str, value: str, *, bold: bool = False, color=muted):
        nonlocal y
        f = font_bold if bold else font_sm
        draw.text((pad, y), label, fill=color, font=f)
        draw.text((width - pad, y), value, fill=color, font=f, anchor="ra")
        y += 28

    if data["subtotal"] > 0:
        money_row("Oraliq jami", f"{_money(data['subtotal'])} so'm")
    if data.get("delivery_fee", 0) > 0:
        money_row("Yetkazish", f"{_money(data['delivery_fee'])} so'm")
    if data["discount"] > 0:
        money_row("Chegirma", f"−{_money(data['discount'])} so'm")
    if data["bonus"] > 0:
        money_row("Bonus", f"−{_money(data['bonus'])} so'm")
    if data.get("gift"):
        money_row("Sovg‘a", str(data["gift"]))

    y += 6
    draw.rounded_rectangle(
        (pad, y, width - pad, y + 52),
        radius=12,
        fill=soft,
    )
    draw.text((pad + 16, y + 14), "JAMI", fill=green_dark, font=font_total)
    draw.text(
        (width - pad - 16, y + 14),
        f"{_money(data['total'])} so'm",
        fill=green_dark,
        font=font_total,
        anchor="ra",
    )
    y += 68

    draw.line((pad, y, width - pad, y), fill=line_c, width=1)
    y += 16
    if data["customer"]:
        for nl in _wrap_text(draw, f"Mijoz: {data['customer']}", font_sm, content_w):
            draw.text((pad, y), nl, fill=text_c, font=font_sm)
            y += 24
    draw.text((pad, y), f"Telefon: {data['phone'] or '—'}", fill=text_c, font=font_sm)
    y += 26
    for nl in _wrap_text(
        draw, f"Manzil: {data['delivery_address']}", font_sm, content_w
    ):
        draw.text((pad, y), nl, fill=text_c, font=font_sm)
        y += 24

    y += 18
    draw.text(
        (width // 2, y),
        "Rahmat! Yana kutib qolamiz",
        fill=green,
        font=font_bold,
        anchor="mt",
    )
    y += 36
    shop_bits = [
        x for x in (data["shop_address"], data["shop_phone"], data["shop_hours"]) if x
    ]
    if shop_bits:
        for nl in _wrap_text(draw, " · ".join(shop_bits), font_sm, content_w):
            draw.text((width // 2, y), nl, fill=muted, font=font_sm, anchor="mt")
            y += 22

    # Crop unused bottom
    final_h = min(height, y + 40)
    return img.crop((0, 0, width, final_h))


def render_receipt_png_bytes(order_id: int) -> bytes | None:
    img = render_receipt_image(order_id)
    if img is None:
        return None
    import io

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def render_receipt_pdf_bytes(order_id: int) -> bytes | None:
    img = render_receipt_image(order_id)
    if img is None:
        return None
    import io

    buf = io.BytesIO()
    # RGB → PDF (bitta sahifa)
    img.convert("RGB").save(buf, format="PDF", resolution=120.0)
    return buf.getvalue()


async def send_order_receipt(bot, order_id: int) -> bool:
    """Yetkazilgan buyurtma uchun chek: PNG + PDF + qisqa matn."""
    if bot is None:
        return False
    order = get_order(order_id)
    if not order:
        return False
    if _is_pos_pickup(str(_row_get(order, "pickup_address", "") or "")):
        return False

    data = load_receipt_data(order_id)
    if not data:
        return False

    from telegram import InputFile
    import io

    chat_id = int(order["user_id"])
    url = receipt_public_url(order_id)
    caption = (
        f"🧾 Chek #{order_id}\n"
        f"Jami: {_money(data['total'])} so'm\n"
        f"To‘liq: {url}"
    )
    ok = False

    try:
        png = render_receipt_png_bytes(order_id)
        if png:
            await bot.send_photo(
                chat_id=chat_id,
                photo=InputFile(io.BytesIO(png), filename=f"chek_{order_id}.png"),
                caption=caption[:1024],
            )
            ok = True
    except Exception as exc:
        logger.warning("Chek PNG yuborish xato #%s: %s", order_id, exc)

    try:
        pdf = render_receipt_pdf_bytes(order_id)
        if pdf:
            await bot.send_document(
                chat_id=chat_id,
                document=InputFile(io.BytesIO(pdf), filename=f"chek_{order_id}.pdf"),
                caption=f"PDF chek #{order_id}",
            )
            ok = True
    except Exception as exc:
        logger.warning("Chek PDF yuborish xato #%s: %s", order_id, exc)

    if not ok:
        # Fallback: matn
        text = format_electronic_receipt_html(order_id)
        if not text:
            return False
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode="HTML",
                disable_web_page_preview=False,
            )
            return True
        except Exception as exc:
            logger.warning("Elektron chek yuborish xato #%s: %s", order_id, exc)
            return False
    return True
