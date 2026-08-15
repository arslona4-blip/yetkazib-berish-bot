"""AI Sotuvchi bot — ishga tushirish: python -m ai_sotuvchi"""

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

from ai_sotuvchi.config import ADMIN_IDS, BOT_TOKEN
from ai_sotuvchi.database import init_db
from ai_sotuvchi.handlers import (
    WAIT_ADDRESS,
    WAIT_BROADCAST,
    WAIT_NAME,
    WAIT_NOTE,
    WAIT_PHONE,
    WAIT_PROD_CAT,
    WAIT_PROD_NAME,
    WAIT_PROD_PHOTO,
    WAIT_PROD_PRICE,
    add_product_category,
    add_product_name,
    add_product_photo,
    add_product_price,
    admin_off_cmd,
    admin_on_cmd,
    admin_orders_cmd,
    admin_panel,
    admin_stats_cmd,
    broadcast_message,
    callback_router,
    cancel_add_product,
    cancel_order_flow,
    on_admin_photo,
    on_text,
    order_address,
    order_name,
    order_note,
    order_phone,
    shop_info,
    show_cart,
    show_catalog,
    show_my_orders,
    start,
    start_add_product,
    start_broadcast,
    start_order,
    start_order_callback,
)
from ai_sotuvchi.keyboards import bot_commands


logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("ai_sotuvchi")


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
            "AI_SOTUVCHI_BOT_TOKEN o‘rnatilmagan.\n"
            "BotFather tokenini .env ga yozing, so‘ng: python -m ai_sotuvchi"
        )
        sys.exit(1)

    init_db()
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(_post_init)
        .build()
    )

    order_conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex(r"^Buyurtma berish$"), start_order),
            MessageHandler(filters.Regex(r"^✅ Buyurtma$"), start_order),
            MessageHandler(filters.Regex(r"^Buyurtma$"), start_order),
            CallbackQueryHandler(start_order_callback, pattern=r"^cart:order$"),
        ],
        states={
            WAIT_PHONE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, order_phone)
            ],
            WAIT_ADDRESS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, order_address)
            ],
            WAIT_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, order_name)
            ],
            WAIT_NOTE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, order_note)
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_order_flow),
            MessageHandler(filters.Regex(r"(?i)^bekor"), cancel_order_flow),
        ],
        allow_reentry=True,
    )

    add_product_conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex(r"^➕ Mahsulot$"), start_add_product),
            MessageHandler(filters.Regex(r"^Mahsulot$"), start_add_product),
            CommandHandler("add", start_add_product),
        ],
        states={
            WAIT_PROD_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_name)
            ],
            WAIT_PROD_PRICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_price)
            ],
            WAIT_PROD_PHOTO: [
                MessageHandler(filters.PHOTO, add_product_photo),
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_photo),
            ],
            WAIT_PROD_CAT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_category)
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_add_product),
            MessageHandler(filters.Regex(r"^Bekor qilish$"), cancel_add_product),
            MessageHandler(filters.Regex(r"(?i)^bekor"), cancel_add_product),
        ],
        allow_reentry=True,
    )

    broadcast_conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex(r"^📢 Xabar$"), start_broadcast),
            MessageHandler(filters.Regex(r"^Xabar$"), start_broadcast),
            CommandHandler("broadcast", start_broadcast),
        ],
        states={
            WAIT_BROADCAST: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_message)
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_add_product),
            MessageHandler(filters.Regex(r"^Bekor qilish$"), cancel_add_product),
        ],
        allow_reentry=True,
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("katalog", show_catalog))
    app.add_handler(CommandHandler("cart", show_cart))
    app.add_handler(CommandHandler("orders_mine", show_my_orders))
    app.add_handler(CommandHandler("myorders", show_my_orders))
    app.add_handler(CommandHandler("info", shop_info))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("orders", admin_orders_cmd))
    app.add_handler(CommandHandler("stats", admin_stats_cmd))
    app.add_handler(CommandHandler("off", admin_off_cmd))
    app.add_handler(CommandHandler("on", admin_on_cmd))
    app.add_handler(add_product_conv)
    app.add_handler(order_conv)
    app.add_handler(broadcast_conv)
    app.add_handler(CallbackQueryHandler(callback_router))
    app.add_handler(MessageHandler(filters.PHOTO, on_admin_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))

    logger.info("AI Sotuvchi (pro+) ishga tushdi")
    app.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()
