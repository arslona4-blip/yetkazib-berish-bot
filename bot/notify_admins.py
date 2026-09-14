"""Adminlarga yangi buyurtma haqida Telegram xabar (asosiy bildirishnoma)."""

from __future__ import annotations

import logging
import os
from typing import Any

from bot.config import ADMIN_IDS

logger = logging.getLogger(__name__)


def admin_chat_ids() -> list[int]:
    """ADMIN_IDS + optional ADMIN_CHAT_ID (guruh)."""
    ids: list[int] = sorted(ADMIN_IDS)
    raw = os.getenv("ADMIN_CHAT_ID", "").strip()
    if raw.lstrip("-").isdigit():
        chat_id = int(raw)
        if chat_id not in ids:
            ids.append(chat_id)
    return ids


def _push_body(text: str, max_len: int = 180) -> str:
    """Web Push uchun qisqa matn (HTML teglarsiz)."""
    import re

    plain = re.sub(r"<[^>]+>", "", str(text or ""))
    plain = re.sub(r"\s+", " ", plain).strip()
    if len(plain) <= max_len:
        return plain
    return plain[: max_len - 1].rstrip() + "…"


async def notify_admins_text(
    bot: Any | None,
    text: str,
    *,
    reply_markup: Any = None,
    latitude: float | None = None,
    longitude: float | None = None,
    order_id: int | None = None,
    voice_alert: bool = False,
    push: bool = True,
) -> int:
    """
    Telegram + (ixtiyoriy) Web Push orqali adminga xabar.
    bot=None bo‘lsa faqat Web Push uriniladi.
    Qaytadi: muvaffaqiyatli Telegram yuborilganlar soni.
    voice_alert=True bo‘lsa qisqa ovozli signal ham yuboriladi.
    """
    sent = 0
    targets = admin_chat_ids()
    if bot is None:
        logger.error("Bot yo'q — Telegram admin xabari yuborib bo'lmaydi")
    elif not targets:
        logger.error("ADMIN_IDS bo'sh — adminlarga xabar yuborib bo'lmaydi")
    else:
        for chat_id in targets:
            try:
                await bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    reply_markup=reply_markup,
                    disable_notification=False,
                )
                if latitude is not None and longitude is not None:
                    try:
                        await bot.send_location(
                            chat_id=chat_id,
                            latitude=latitude,
                            longitude=longitude,
                            disable_notification=False,
                        )
                    except Exception as exc:
                        logger.warning(
                            "Admin lokatsiya xato chat=%s: %s", chat_id, exc
                        )
                if voice_alert:
                    try:
                        from bot.voice_confirm import send_admin_new_order_voice

                        await send_admin_new_order_voice(
                            bot, chat_id, order_id=order_id
                        )
                    except Exception as exc:
                        logger.warning(
                            "Admin ovoz xato chat=%s: %s", chat_id, exc
                        )
                sent += 1
            except Exception as exc:
                logger.warning("Admin xabar xato chat=%s: %s", chat_id, exc)
        logger.info("Admin Telegram xabar: %s/%s", sent, len(targets))

    if push:
        try:
            from bot.webpush_notify import send_admin_push

            title = (
                f"Yangi buyurtma #{int(order_id)}"
                if order_id is not None
                else "Yangi buyurtma"
            )
            await send_admin_push(title, _push_body(text), url="/admin/")
        except Exception as exc:
            logger.warning("Admin Web Push xato: %s", exc)

    return sent
