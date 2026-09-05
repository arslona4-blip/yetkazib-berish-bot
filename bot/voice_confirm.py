"""Buyurtma qabul qilinganda o‘zbekcha ovozli tasdiq (edge-tts)."""

from __future__ import annotations

import io
import logging
from typing import Any

from telegram import InputFile

from bot.config import (
    SHOP_NAME,
    VOICE_CONFIRM_ENABLED,
    VOICE_CONFIRM_SCRIPT,
    VOICE_CONFIRM_VOICE,
)

logger = logging.getLogger(__name__)

_ONES = (
    "",
    "bir",
    "ikki",
    "uch",
    "to‘rt",
    "besh",
    "olti",
    "yetti",
    "sakkiz",
    "to‘qqiz",
)
_TENS = (
    "",
    "o‘n",
    "yigirma",
    "o‘ttiz",
    "qirq",
    "ellik",
    "oltmish",
    "yetmish",
    "sakson",
    "to‘qson",
)


def _under_thousand(n: int) -> str:
    """0..999 → o‘zbekcha (0 bo‘lsa bo‘sh)."""
    n = int(n) % 1000
    if n <= 0:
        return ""
    parts: list[str] = []
    hundreds = n // 100
    rest = n % 100
    if hundreds:
        if hundreds == 1:
            parts.append("yuz")
        else:
            parts.append(f"{_ONES[hundreds]} yuz")
    if rest:
        if rest < 10:
            parts.append(_ONES[rest])
        elif rest < 20:
            ones = rest % 10
            parts.append("o‘n" if ones == 0 else f"o‘n {_ONES[ones]}")
        else:
            tens = rest // 10
            ones = rest % 10
            parts.append(_TENS[tens] if ones == 0 else f"{_TENS[tens]} {_ONES[ones]}")
    return " ".join(parts)


def amount_to_uzbek_words(amount: int) -> str:
    """49000 → «qirq to‘qqiz ming» — TTS raqamni chalkashtirmasin."""
    n = max(0, int(amount or 0))
    if n == 0:
        return "nol"

    parts: list[str] = []
    milliards = n // 1_000_000_000
    millions = (n // 1_000_000) % 1000
    thousands = (n // 1000) % 1000
    rest = n % 1000

    if milliards:
        w = _under_thousand(milliards)
        parts.append(f"{w} milliard")
    if millions:
        w = _under_thousand(millions)
        parts.append(f"{w} million")
    if thousands:
        w = _under_thousand(thousands)
        parts.append(f"{w} ming")
    if rest:
        parts.append(_under_thousand(rest))

    return " ".join(p for p in parts if p).strip()


def _som_fmt(amount: int) -> str:
    return f"{max(0, int(amount or 0)):,}".replace(",", " ")


def confirmation_script(*, order_id: int, total: int, shop_name: str | None = None) -> str:
    name = (shop_name or SHOP_NAME or "Do‘kon").strip()
    total_words = amount_to_uzbek_words(total)
    order_words = amount_to_uzbek_words(int(order_id))
    template = (VOICE_CONFIRM_SCRIPT or "").strip() or (
        "Assalomu alaykum! Baraka Market yetkazib berish xizmatiga xush kelibsiz. "
        "Buyurtmangiz qabul qilindi. "
        "Buyurtma raqami: {order}. "
        "Jami: {total} so‘m. "
        "Buyurtmangiz uchun rahmat. "
        "Baraka Market yetkazib berish xodimlari sizdan mamnun."
    )
    try:
        return template.format(
            shop=name,
            order=order_words,
            total=total_words,
            order_id=int(order_id),
            amount=int(total),
        )
    except (KeyError, ValueError):
        return (
            f"Assalomu alaykum! Baraka Market yetkazib berish xizmatiga xush kelibsiz. "
            f"Buyurtmangiz qabul qilindi. "
            f"Buyurtma raqami: {order_words}. "
            f"Jami: {total_words} so‘m. "
            f"Buyurtmangiz uchun rahmat. "
            f"Baraka Market yetkazib berish xodimlari sizdan mamnun."
        )


async def synthesize_uzbek_mp3(text: str) -> bytes:
    import edge_tts

    voice = (VOICE_CONFIRM_VOICE or "uz-UZ-MadinaNeural").strip()
    communicate = edge_tts.Communicate(text, voice)
    buf = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            buf.write(chunk["data"])
    data = buf.getvalue()
    if len(data) < 200:
        raise RuntimeError("TTS audio juda qisqa")
    return data


async def send_order_voice_confirm(
    bot: Any,
    chat_id: int,
    *,
    order_id: int,
    total: int,
) -> bool:
    """Mijozga o‘zbekcha ovozli tasdiq. Xato bo‘lsa False — oqim to‘xtamaydi."""
    if not VOICE_CONFIRM_ENABLED:
        return False

    text = confirmation_script(order_id=order_id, total=total)
    caption = (
        f"🔊 Buyurtma #{int(order_id)} qabul qilindi\n"
        f"💰 {_som_fmt(total)} so‘m"
    )
    try:
        mp3 = await synthesize_uzbek_mp3(text)
    except Exception as exc:
        logger.warning("Ovozli tasdiq TTS xato #%s: %s", order_id, exc)
        return False

    try:
        await bot.send_audio(
            chat_id=chat_id,
            audio=InputFile(io.BytesIO(mp3), filename=f"buyurtma_{order_id}.mp3"),
            title=f"Buyurtma #{order_id}",
            performer=SHOP_NAME,
            caption=caption,
        )
        return True
    except Exception as exc:
        logger.warning("Ovozli tasdiq yuborilmadi #%s: %s", order_id, exc)
        return False
