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
    dx, dy = 80, 28 + bounce

    def o(x: int, y: int) -> tuple[int, int]:
        return (dx + x, dy + y)

    # oyoq
    draw.rounded_rectangle([*o(-10, 78), *o(-2, 100)], radius=4, fill="#2d4a38")
    draw.rounded_rectangle([*o(6, 78), *o(14, 100)], radius=4, fill="#2d4a38")
    draw.ellipse([*o(-14, 98), *o(0, 106)], fill="#1a2e24")
    draw.ellipse([*o(2, 98), *o(16, 106)], fill="#1a2e24")
    # tana
    draw.rounded_rectangle([*o(-16, 46), *o(16, 82)], radius=12, fill="#006837")
    draw.rounded_rectangle([*o(-16, 58), *o(16, 82)], radius=10, fill="#8dc63f")
    draw.ellipse([*o(-3, 51), *o(3, 57)], fill="#ffffff")
    # chap qo‘l
    draw.rounded_rectangle([*o(-26, 50), *o(-16, 72)], radius=5, fill="#f0c4a0")
    # o‘ng qo‘l — ko‘rsatadi
    rad = math.radians(arm_deg)
    ax, ay = o(16, 52)
    hx = int(ax + 26 * math.cos(rad))
    hy = int(ay + 26 * math.sin(rad))
    draw.line([(ax, ay), (hx, hy)], fill="#f0c4a0", width=10)
    draw.ellipse([hx - 8, hy - 8, hx + 8, hy + 8], fill="#f0c4a0")
    # bosh
    draw.ellipse([*o(-16, 12), *o(16, 44)], fill="#f3c7a4")
    draw.ellipse([*o(-16, 8), *o(16, 28)], fill="#3a2418")
    draw.ellipse([*o(-8, 24), *o(-4, 30)], fill="#1a1a1a")
    draw.ellipse([*o(4, 24), *o(8, 30)], fill="#1a1a1a")
    draw.arc([*o(-6, 30), *o(6, 40)], start=20, end=160, fill="#c47a62", width=2)


def ensure_coach_gif() -> Path | None:
    if GIF_PATH.is_file() and GIF_PATH.stat().st_size > 400:
        return GIF_PATH
    try:
        from PIL import Image

        ASSETS_DIR.mkdir(parents=True, exist_ok=True)
        w, h, n = 160, 150, 12
        frames: list[Image.Image] = []
        for i in range(n):
            t = i / n
            bounce = int(-8 * math.sin(2 * math.pi * t))
            arm = -20 + 50 * (0.5 - 0.5 * math.cos(2 * math.pi * t))
            img = Image.new("RGB", (w, h), (231, 242, 227))
            _draw_person(img, bounce, arm)
            frames.append(img)
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
