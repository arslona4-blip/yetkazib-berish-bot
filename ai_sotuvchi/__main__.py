"""AI Sotuvchi bot — ishga tushirish: python -m ai_sotuvchi"""

from __future__ import annotations

import logging
import sys

from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from ai_sotuvchi.config import BOT_TOKEN
from ai_sotuvchi.database import init_db
from ai_sotuvchi.handlers import (
    WAIT_ADDRESS,
    WAIT_NAME,
    WAIT_PHONE,
    WAIT_PROD_NAME,
    WAIT_PROD_PRICE,
    add_product_name,
    add_product_price,
    admin_add_cmd,
    admin_off_cmd,
    admin_on_cmd,
    admin_orders_cmd,
    admin_panel,
    admin_stats_cmd,
    callback_router,
    cancel_add_product,
    cancel_order_flow,
    on_text,
    order_address,
    order_name,
    order_phone,
    shop_info,
    show_cart,
    show_catalog,
    show_my_orders,
    start,
    start_add_product,
    start_order,
)


logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("ai_sotuvchi")


def main() -> None:
    if not BOT_TOKEN:
        logger.error(
            "AI_SOTUVCHI_BOT_TOKEN o‘rnatilmagan.\n"
            "1) BotFather → /newbot\n"
            "2) Token ni .env yoki Railway Variables ga yozing:\n"
            "   AI_SOTUVCHI_BOT_TOKEN=...\n"
            "   AI_SOTUVCHI_ADMIN_IDS=telegram_id\n"
            "3) python -m ai_sotuvchi"
        )
        sys.exit(1)

    init_db()
    app = Application.builder().token(BOT_TOKEN).build()

    order_conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex(r"^✅ Buyurtma$"), start_order),
            MessageHandler(filters.Regex(r"^Buyurtma$"), start_order),
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
        },
        fallbacks=[
            CommandHandler("cancel", cancel_add_product),
            MessageHandler(filters.Regex(r"^❌ Bekor$"), cancel_add_product),
            MessageHandler(filters.Regex(r"(?i)^bekor"), cancel_add_product),
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
    # Eski /add Nom|narx saqlanadi, lekin asosiy — suhbat orqali
    app.add_handler(add_product_conv)
    app.add_handler(CommandHandler("add_old", admin_add_cmd))
    app.add_handler(order_conv)
    app.add_handler(CallbackQueryHandler(callback_router))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))

    logger.info("AI Sotuvchi ishga tushdi (polling)")
    app.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()
