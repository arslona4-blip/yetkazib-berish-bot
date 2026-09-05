"""Mahsulot rasmini reklamabop kartochkaga aylantirish (Pillow)."""

from __future__ import annotations

import io
from typing import Any

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

from bot.config import SHOP_NAME


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def _format_price(price: int) -> str:
    return f"{int(price):,}".replace(",", " ") + " so'm"


def _fit_center(img: Image.Image, box: tuple[int, int, int, int]) -> Image.Image:
    """Rasmni box ichiga cover qilib joylashtirish."""
    x0, y0, x1, y1 = box
    bw, bh = x1 - x0, y1 - y0
    fitted = ImageOps.fit(img, (bw, bh), method=Image.Resampling.LANCZOS, centering=(0.5, 0.45))
    return fitted


def make_product_ad_card(
    photo_bytes: bytes,
    *,
    name: str,
    price: int,
    shop_name: str | None = None,
    size: int = 1080,
) -> bytes:
    """Studiya uslubidagi yashil kartochka + narx badge."""
    shop = (shop_name or SHOP_NAME or "Baraka Market").strip()
    base = Image.new("RGB", (size, size), "#e8f3e4")
    draw = ImageDraw.Draw(base)

    # Fon gradient (sodda: ikki qatlam)
    for y in range(size):
        t = y / max(1, size - 1)
        r = int(232 + (247 - 232) * t)
        g = int(243 + (251 - 243) * t)
        b = int(228 + (245 - 228) * t)
        draw.line([(0, y), (size, y)], fill=(r, g, b))

    # Yuqori brand chiziq
    draw.rectangle([0, 0, size, 12], fill="#8dc63f")

    src = Image.open(io.BytesIO(photo_bytes)).convert("RGB")
    # Yengil yaxshilash
    src = ImageEnhance.Contrast(src).enhance(1.08)
    src = ImageEnhance.Color(src).enhance(1.06)
    src = ImageEnhance.Sharpness(src).enhance(1.15)

    # Markaziy foto maydoni (yumaloq burchakli "kartochka")
    margin = 70
    top = 110
    bottom = size - 220
    photo_box = (margin, top, size - margin, bottom)
    fitted = _fit_center(src, photo_box)

    # Soyali ramka
    frame = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    fdraw = ImageDraw.Draw(frame)
    fx0, fy0, fx1, fy1 = photo_box
    shadow = (fx0 + 8, fy0 + 12, fx1 + 8, fy1 + 12)
    fdraw.rounded_rectangle(shadow, radius=36, fill=(6, 61, 34, 45))
    fdraw.rounded_rectangle(photo_box, radius=36, fill=(255, 255, 255, 255))
    base = Image.alpha_composite(base.convert("RGBA"), frame).convert("RGB")

    # Fotoni mask bilan joylash
    mask = Image.new("L", (fx1 - fx0, fy1 - fy0), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, fx1 - fx0 - 1, fy1 - fy0 - 1], radius=32, fill=255
    )
    base.paste(fitted, (fx0, fy0), mask)

    draw = ImageDraw.Draw(base)
    title_font = _font(42, bold=True)
    price_font = _font(48, bold=True)
    shop_font = _font(28, bold=True)
    small_font = _font(24, bold=False)

    # Do‘kon nomi
    draw.text((margin, 40), shop[:40], fill="#054a28", font=shop_font)

    # Mahsulot nomi
    title = (name or "Mahsulot").strip()
    if len(title) > 42:
        title = title[:40] + "…"
    draw.text((margin, bottom + 24), title, fill="#122018", font=title_font)

    # Narx badge
    price_text = _format_price(price)
    tw = draw.textlength(price_text, font=price_font)
    badge_w = int(tw + 56)
    badge_h = 78
    bx1 = size - margin
    bx0 = bx1 - badge_w
    by0 = bottom + 90
    by1 = by0 + badge_h
    draw.rounded_rectangle([bx0, by0, bx1, by1], radius=22, fill="#8dc63f")
    draw.text(
        (bx0 + 28, by0 + 14),
        price_text,
        fill="#143018",
        font=price_font,
    )

    # Pastki yashil chiziq
    draw.rectangle([0, size - 10, size, size], fill="#006837")
    draw.text(
        (margin, size - 48),
        "Yetkazib berish · Baraka",
        fill="#567064",
        font=small_font,
    )

    out = io.BytesIO()
    base.save(out, format="JPEG", quality=92, optimize=True)
    return out.getvalue()


def guess_category_keywords(name: str, categories: list[Any]) -> int | None:
    """Oddiy kalit so‘zlar bo‘yicha toifa taxmini."""
    n = (name or "").lower()
    rules = [
        (("daftar", "ruchka", "qalam", "notebook", "pen", "maktab", "tetrad"), ("maktab", "daftar", "office", "ofis", "kanselyar", "stationery")),
        (("cola", "fanta", "pepsi", "ichimlik", "suv", "sharbat", "sok"), ("ichimlik", "napitok", "drink")),
        (("guruch", "shakar", "un", "yog", "moy", "makaron", "novvot"), ("oziq", "oziq-ovqat", "bakaleya", "food")),
        (("sut", "moloko", "yogurt", "qatiq", "smetana"), ("sut", "молоч", "dairy")),
        (("non", "bulochka", "pechenye", "pishiriq"), ("non", "pishiriq", "bread")),
        (
            ("gul", "bezak", "sun'iy", "suniy", "dekor", "guldon", "o‘simlik", "osimlik"),
            ("bayram", "bezak", "dekor", "gul", "holiday", "uy"),
        ),
        (("bolajon", "bola", "oyinchog", "o‘yinchoq", "podguznik", "nestogen"), ("bolajon", "bola", "дети", "child")),
        (("tozalash", "kir yuvish", "fairy", "domestos", "sovun"), ("tozalash", "cleaning", "быт")),
        (("shokolad", "konfet", "qandolat", "pechenye", "vafli"), ("qandolat", "конфет", "sweet")),
    ]
    for name_keys, cat_keys in rules:
        if not any(k in n for k in name_keys):
            continue
        for c in categories:
            cname = str(c["name"]).lower()
            if any(k in cname for k in cat_keys):
                return int(c["id"])
    return None
