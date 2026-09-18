"""Vositachi bot — ishga tushirish: python -m vositachi"""

from __future__ import annotations

import logging
import sys

from telegram import BotCommandScopeChat
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from vositachi.config import ADMIN_IDS, BOT_TOKEN
from vositachi.database import init_db
from vositachi.handlers import (
    WAIT_DEST,
    WAIT_PHONE,
    WAIT_PICKUP,
    WAIT_PRICE,
    admin_active,
    admin_done,
    admin_drivers,
    admin_open,
    admin_stats,
    admin_tariff,
    callback_router,
    cancel_cmd,
    cmd_set_base,
    cmd_set_commission,
    cmd_set_default_km,
    cmd_set_km,
    help_cmd,
    on_text,
    receive_dest,
    receive_phone,
    receive_pickup,
    receive_price_offer,
    start,
    start_ride_request,
)
from vositachi.keyboards import bot_commands

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("vositachi")


async def _post_init(application: Application) -> None:
    try:
        await application.bot.set_my_commands(bot_commands(is_admin=False))
        for admin_id in ADMIN_IDS:
            try:
                await application.bot.set_my_commands(
                    bot_commands(is_admin=True),
                    scope=BotCommandScopeChat(chat_id=admin_id),
                )
            except Exception:
                logger.warning("Admin commands o‘rnatilmadi: %s", admin_id)
    except Exception as exc:
        logger.warning("Bot commands: %s", exc)


def main() -> None:
    if not BOT_TOKEN:
        logger.error(
            "VOSITACHI_BOT_TOKEN o‘rnatilmagan.\n"
            "BotFather tokenini .env ga yozing, so‘ng: python -m vositachi"
        )
        sys.exit(1)

    init_db()
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(_post_init)
        .build()
    )

    ride_conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex(r"^🚕 Safar so‘rash$"), start_ride_request),
            MessageHandler(filters.Regex(r"^Safar so‘rash$"), start_ride_request),
        ],
        states={
            WAIT_PICKUP: [
                MessageHandler(filters.LOCATION, receive_pickup),
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_pickup),
            ],
            WAIT_DEST: [
                MessageHandler(filters.LOCATION, receive_dest),
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_dest),
            ],
            WAIT_PHONE: [
                MessageHandler(filters.CONTACT, receive_phone),
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_phone),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_cmd),
            MessageHandler(filters.Regex(r"^❌ Bekor$"), cancel_cmd),
        ],
        allow_reentry=True,
    )

    price_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(callback_router, pattern=r"^ride:price:\d+$"),
        ],
        states={
            WAIT_PRICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_price_offer),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_cmd),
            MessageHandler(filters.Regex(r"^❌ Bekor$"), cancel_cmd),
        ],
        allow_reentry=True,
        per_message=False,
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("cancel", cancel_cmd))
    app.add_handler(CommandHandler("stats", admin_stats))
    app.add_handler(CommandHandler("open", admin_open))
    app.add_handler(CommandHandler("tariff", admin_tariff))
    app.add_handler(CommandHandler("set_base", cmd_set_base))
    app.add_handler(CommandHandler("set_km", cmd_set_km))
    app.add_handler(CommandHandler("set_commission", cmd_set_commission))
    app.add_handler(CommandHandler("set_default_km", cmd_set_default_km))
    app.add_handler(ride_conv)
    app.add_handler(price_conv)
    app.add_handler(CallbackQueryHandler(callback_router))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))

    logger.info("Vositachi bot ishga tushdi")
    app.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()
