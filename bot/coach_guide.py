"""Botdagi jonli odamcha — GIF + o‘zbekcha ovoz + Do‘kon tugmasi."""

from __future__ import annotations

import io
import logging
import math
from pathlib import Path
from typing import Any

from telegram import InlineKeyboardMarkup, InputFile

from bot.keyboards import shop_inline_button
from bot.webapp import COACH_VOICE_LINES

logger = logging.getLogger(__name__)

ASSETS_DIR = Path(__file__).resolve().parent / "assets"
GIF_PATH = ASSETS_DIR / "coach-person.gif"

COACH_SCRIPT = " ".join(
    [
        COACH_VOICE_LINES["shop"],
        COACH_VOICE_LINES["product"],
        COACH_VOICE_LINES["cart"],
        COACH_VOICE_LINES["address"],
        COACH_VOICE_LINES["order"],
        COACH_VOICE_LINES["done"],
    ]
)

COACH_CAPTION = (
    "🧭 <b>Men yo‘l ko‘rsataman!</b>\n\n"
    "1️⃣ Pastdagi <b>🛒 Do'kon</b> tugmasini bosing\n"
    "2️⃣ Mahsulot tanlang — «Qo'shish»\n"
    "3️⃣ <b>Savatchani</b> oching\n"
    "4️⃣ Manzil yoki lokatsiya\n"
    "5️⃣ <b>Buyurtma berish</b>\n\n"
    "Tayyor! Shu yo‘l bilan buyurtma berasiz."
)


def _draw_person(img, bounce: int, arm_deg: float) -> None:
    from PIL import ImageDraw

    draw = ImageDraw.Draw(img)
    dx, dy = 120, 8 + bounce

    def o(x: int, y: int) -> tuple[int, int]:
        return (dx + x, dy + y)

    # shim
    draw.rounded_rectangle([*o(-16, 92), *o(-2, 128)], radius=4, fill="#243044")
    draw.rounded_rectangle([*o(4, 92), *o(18, 128)], radius=4, fill="#1b2638")
    draw.ellipse([*o(-20, 124), *o(2, 134)], fill="#121820")
    draw.ellipse([*o(0, 124), *o(22, 134)], fill="#121820")
    # pidjak
    draw.polygon(
        [o(-28, 54), o(0, 48), o(28, 54), o(30, 96), o(-30, 96)],
        fill="#1e3a5f",
    )
    draw.polygon([o(0, 52), o(28, 56), o(30, 96), o(0, 96)], fill="#16304d")
    # oq ko‘ylak + galstuk
    draw.polygon([o(-8, 52), o(0, 62), o(8, 52), o(8, 96), o(-8, 96)], fill="#f7f9fc")
    draw.polygon([o(0, 62), o(-5, 74), o(0, 94), o(5, 74)], fill="#006837")
    # chap yeng
    draw.line([o(-24, 58), o(-34, 92)], fill="#1e3a5f", width=14)
    draw.ellipse([*o(-40, 88), *o(-26, 102)], fill="#f2c7a6")
    # o‘ng qo‘l — ko‘rsatadi
    rad = math.radians(arm_deg)
    ax, ay = o(24, 58)
    hx = int(ax + 38 * math.cos(rad))
    hy = int(ay + 38 * math.sin(rad))
    draw.line([(ax, ay), (hx, hy)], fill="#1e3a5f", width=14)
    draw.ellipse([hx - 10, hy - 10, hx + 10, hy + 10], fill="#f2c7a6")
    # yuz — soch yuzni yopmasin
    draw.ellipse([*o(-24, 8), *o(24, 56)], fill="#f4c9a8")
    draw.pieslice([*o(-24, 4), *o(24, 40)], start=200, end=340, fill="#3b2a1d")
    # ko‘z oqi + qorachiq
    draw.ellipse([*o(-14, 26), *o(-4, 38)], fill="#ffffff")
    draw.ellipse([*o(4, 26), *o(14, 38)], fill="#ffffff")
    draw.ellipse([*o(-11, 29), *o(-6, 35)], fill="#2a1c14")
    draw.ellipse([*o(7, 29), *o(12, 35)], fill="#2a1c14")
    draw.ellipse([*o(-10, 30), *o(-8, 32)], fill="#ffffff")
    draw.ellipse([*o(8, 30), *o(10, 32)], fill="#ffffff")
    draw.arc([*o(-15, 22), *o(-3, 28)], start=200, end=340, fill="#2a1c14", width=2)
    draw.arc([*o(3, 22), *o(15, 28)], start=200, end=340, fill="#2a1c14", width=2)
    draw.ellipse([*o(-18, 36), *o(-10, 42)], fill="#f0a090")
    draw.ellipse([*o(10, 36), *o(18, 42)], fill="#f0a090")
    draw.arc([*o(-8, 40), *o(8, 52)], start=20, end=160, fill="#c45d55", width=3)


def ensure_coach_gif() -> Path | None:
    if GIF_PATH.is_file() and GIF_PATH.stat().st_size > 20000:
        return GIF_PATH
    try:
        from PIL import Image

        ASSETS_DIR.mkdir(parents=True, exist_ok=True)
        w, h, n = 200, 170, 12
        frames: list[Image.Image] = []
        for i in range(n):
            t = i / n
            bounce = int(-10 * math.sin(2 * math.pi * t))
            arm = -35 + 55 * (0.5 - 0.5 * math.cos(2 * math.pi * t))
            hi = Image.new("RGB", (w * 2, h * 2), (231, 242, 227))
            _draw_person(hi, bounce * 2, arm)
            frames.append(hi.resize((w, h), Image.Resampling.LANCZOS))
        frames[0].save(
            GIF_PATH,
            save_all=True,
            append_images=frames[1:],
            duration=90,
            loop=0,
            optimize=True,
        )
        if GIF_PATH.is_file() and GIF_PATH.stat().st_size > 400:
            return GIF_PATH
    except Exception as exc:
        logger.warning("Coach GIF yaratilmadi: %s", exc)
        if GIF_PATH.is_file() and GIF_PATH.stat().st_size > 400:
            return GIF_PATH
    return None


def coach_keyboard() -> InlineKeyboardMarkup | None:
    btn = shop_inline_button("🛒 Do'konni ochish")
    if not btn:
        return None
    return InlineKeyboardMarkup([[btn]])


async def send_coach_guide(bot: Any, chat_id: int) -> bool:
    """Odamcha GIF + ovoz + Do‘kon tugmasi."""
    markup = coach_keyboard()
    gif = ensure_coach_gif()
    sent_media = False
    if gif is not None:
        try:
            with gif.open("rb") as anim:
                await bot.send_animation(
                    chat_id=chat_id,
                    animation=InputFile(anim, filename="coach-person.gif"),
                    caption=COACH_CAPTION,
                    parse_mode="HTML",
                    reply_markup=markup,
                )
            sent_media = True
        except Exception as exc:
            logger.warning("Coach GIF yuborilmadi: %s", exc)

    if not sent_media:
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=COACH_CAPTION,
                parse_mode="HTML",
                reply_markup=markup,
            )
            sent_media = True
        except Exception as exc:
            logger.warning("Coach matn HTML yuborilmadi: %s", exc)
            try:
                await bot.send_message(
                    chat_id=chat_id,
                    text=(
                        "Men yo‘l ko‘rsataman!\n\n"
                        "1) Do'kon tugmasini bosing\n"
                        "2) Mahsulot tanlang\n"
                        "3) Savatchani oching\n"
                        "4) Manzil yoki lokatsiya\n"
                        "5) Buyurtma berish"
                    ),
                    reply_markup=markup,
                )
                sent_media = True
            except Exception as exc2:
                logger.warning("Coach matn yuborilmadi: %s", exc2)
                return False

    try:
        from bot.voice_confirm import synthesize_uzbek_mp3

        mp3 = await synthesize_uzbek_mp3(COACH_SCRIPT)
        await bot.send_audio(
            chat_id=chat_id,
            audio=InputFile(io.BytesIO(mp3), filename="yol_korsatma.mp3"),
            title="Yo‘l ko‘rsatma",
            performer="Baraka Market",
            caption="🔊 Men yo‘l ko‘rsataman — Do‘kon tugmasini bosing",
        )
    except Exception as exc:
        logger.warning("Coach ovoz yuborilmadi: %s", exc)
    return sent_media
