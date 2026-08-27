"""Buyurtma qabul qilinganda o‘zbekcha ovozli tasdiq (edge-tts)."""

from __future__ import annotations

import io
import logging
from typing import Any

from telegram import InputFile

from bot.config import SHOP_NAME, VOICE_CONFIRM_ENABLED, VOICE_CONFIRM_VOICE

logger = logging.getLogger(__name__)


def _som_fmt(amount: int) -> str:
    return f"{max(0, int(amount or 0)):,}".replace(",", " ")


def confirmation_script(*, order_id: int, total: int, shop_name: str | None = None) -> str:
    name = (shop_name or SHOP_NAME or "Do‘kon").strip()
    return (
        f"Assalomu alaykum! {name}. "
        f"Buyurtmangiz qabul qilindi. "
        f"Buyurtma raqami: {int(order_id)}. "
        f"Jami: {_som_fmt(total)} so‘m. "
        f"Tez orada yetkazib beramiz. Rahmat!"
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
