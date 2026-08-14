import logging

from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    PreCheckoutQueryHandler,
    filters,
)

from bot.config import (
    BOT_TOKEN,
    SHOP_ADDRESS,
    SHOP_HOURS,
    SHOP_NAME,
    SHOP_PHONE,
    WEBAPP_PORT,
    WEBHOOK_PATH,
    WEBHOOK_PORT,
    WEBHOOK_URL,
    delivery_rates_plain,
)
from bot.contacts import build_contact_conversations, contact_callback
from bot.database import init_db
from bot.extras import (
    build_extra_conversations,
    cancel_order_callback,
    courier_panel,
    fav_callback,
    reorder_callback,
    show_bonus,
    show_favorites,
)
from bot.features_handlers import (
    ask_language,
    language_callback,
    rating_callback,
    recur_callback,
    show_recommendations,
    show_recurring_list,
    stop_recur_command,
)
from bot.handlers import (
    admin_awaiting_text,
    admin_callback,
    admin_delete_order_callback,
    admin_orders_panel,
    admin_panel,
    admin_product_callback,
    admin_status_callback,
    back_to_main_menu,
    build_order_conversation,
    build_product_admin_conversation,
    cart_callback,
    contact_info,
    help_command,
    my_orders,
    payment_callback,
    precheckout_callback,
    product_callback,
    share_invite,
    show_cart_message,
    show_catalog,
    show_more_menu,
    show_my_id,
    start,
    successful_payment,
    webapp_scan_data,
)
from bot.jobs import setup_jobs
from bot.webapp import set_bot, start_webapp_server


def _start_health_server() -> None:
    return


def _acquire_single_instance_lock() -> None:
    import socket

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(("127.0.0.1", 47291))
    except OSError as exc:
        sock.close()
        raise SystemExit(
            "Bot allaqachon ishlamoqda. Avval eski jarayonni to'xtating."
        ) from exc

    global _BOT_LOCK_FILE  # noqa: PLW0603
    _BOT_LOCK_FILE = sock


_BOT_LOCK_FILE = None


def _bot_description_uz() -> str:
    """Bo'sh chatda flamingo o'rnida ko'rinadigan matn (max 512)."""
    return (
        f"🏪 {SHOP_NAME}\n"
        f"🚚 Uyingizgacha tez yetkazib beramiz\n\n"
        f"📍 {SHOP_ADDRESS}\n"
        f"🕐 {SHOP_HOURS}\n"
        f"📞 {SHOP_PHONE}\n\n"
        f"🛒 Do'kon — katalog va buyurtma\n"
        f"📷 Skaner — shtrix-kod bilan savatga\n"
        f"📋 Mening buyurtmalarim — holatni kuzating\n\n"
        f"{delivery_rates_plain()}\n\n"
        f"Boshlash: /start"
    )


def _bot_short_description_uz() -> str:
    """Bot profilida qisqa tavsif (max 120)."""
    text = f"{SHOP_NAME} — uyga yetkazib berish. /start bosing."
    return text[:120]


async def _set_bot_profile_texts(application: Application) -> None:
    """Telegram bo'sh chatda bot haqida ma'lumot ko'rsatadi."""
    bot = application.bot
    description = _bot_description_uz()[:512]
    short = _bot_short_description_uz()
    try:
        await bot.set_my_description(description=description)
        await bot.set_my_short_description(short_description=short)
        await bot.set_my_description(
            description=(
                f"🏪 {SHOP_NAME}\n"
                f"🚚 Быстрая доставка домой\n\n"
                f"📍 {SHOP_ADDRESS}\n"
                f"🕐 {SHOP_HOURS}\n"
                f"📞 {SHOP_PHONE}\n\n"
                f"Нажмите /start чтобы начать"
            )[:512],
            language_code="ru",
        )
        await bot.set_my_short_description(
            short_description=f"{SHOP_NAME} — доставка на дом. /start"[:120],
            language_code="ru",
        )
    except Exception as exc:
        logging.getLogger(__name__).warning("Bot description o'rnatilmadi: %s", exc)


def main() -> None:
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )

    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN .env faylida ko'rsatilmagan.")

    _acquire_single_instance_lock()
    _start_health_server()
    start_webapp_server()
    init_db()

    async def post_init(application: Application) -> None:
        set_bot(application.bot)
        setup_jobs(application)
        await _set_bot_profile_texts(application)

    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, admin_awaiting_text),
        group=-1,
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("id", show_my_id))
    app.add_handler(CommandHandler("stop_recur", stop_recur_command))
    app.add_handler(build_order_conversation())
    app.add_handler(build_product_admin_conversation())
    for conv in build_extra_conversations():
        app.add_handler(conv)
    for conv in build_contact_conversations():
        app.add_handler(conv)

    app.add_handler(MessageHandler(filters.Regex("^🛍 Katalog$"), show_catalog))
    app.add_handler(MessageHandler(filters.Regex("^🛒 Savatcha$"), show_cart_message))
    app.add_handler(MessageHandler(filters.Regex("^⋯ Ko'proq$"), show_more_menu))
    app.add_handler(MessageHandler(filters.Regex("^⬅️ Asosiy menyu$"), back_to_main_menu))
    app.add_handler(MessageHandler(filters.Regex("^⭐ Sevimlilar$"), show_favorites))
    app.add_handler(MessageHandler(filters.Regex("^🎁 Bonus$"), show_bonus))
    app.add_handler(MessageHandler(filters.Regex("^👥 Ulashish$"), share_invite))
    app.add_handler(MessageHandler(filters.Regex("^📋 Mening buyurtmalarim$"), my_orders))
    app.add_handler(MessageHandler(filters.Regex("^ℹ️ Yordam$"), help_command))
    app.add_handler(MessageHandler(filters.Regex("^📞 Aloqa$"), contact_info))
    app.add_handler(MessageHandler(filters.Regex("^📦 Buyurtmalar$"), admin_orders_panel))
    app.add_handler(MessageHandler(filters.Regex("^🛠 Admin panel$"), admin_panel))
    app.add_handler(MessageHandler(filters.Regex("^🚴 Kuryer panel$"), courier_panel))
    app.add_handler(MessageHandler(filters.Regex(r"^(🌐 Til|🌐 Язык)$"), ask_language))
    app.add_handler(
        MessageHandler(
            filters.Regex(r"^(✨ Tavsiyalar|✨ Рекомендации)$"),
            show_recommendations,
        )
    )
    app.add_handler(
        MessageHandler(
            filters.Regex(r"^(🔁 Takroriy buyurtmalar|🔁 Повторные заказы)$"),
            show_recurring_list,
        )
    )

    app.add_handler(CallbackQueryHandler(product_callback, pattern=r"^(product:|catalog:)"))
    app.add_handler(CallbackQueryHandler(cart_callback, pattern=r"^cart"))
    app.add_handler(CallbackQueryHandler(fav_callback, pattern=r"^fav:\d+$"))
    app.add_handler(CallbackQueryHandler(reorder_callback, pattern=r"^reorder:\d+$"))
    app.add_handler(CallbackQueryHandler(cancel_order_callback, pattern=r"^cancel_order:\d+$"))
    app.add_handler(CallbackQueryHandler(language_callback, pattern=r"^lang:(uz|ru)$"))
    app.add_handler(CallbackQueryHandler(rating_callback, pattern=r"^rate:\d+:\d+$"))
    app.add_handler(
        CallbackQueryHandler(recur_callback, pattern=r"^(recur:|recur_set:|recur_cancel)")
    )
    app.add_handler(
        CallbackQueryHandler(
            contact_callback,
            pattern=r"^contact:(home|list|debtors|view:\d+|hist:\d+|debt:\d+|pay:\d+)$",
        )
    )
    app.add_handler(CallbackQueryHandler(admin_callback, pattern=r"^admin:"))
    app.add_handler(
        CallbackQueryHandler(
            admin_product_callback,
            pattern=r"^admin_prod:(list|cats|viewcat:\d+|item:\d+|toggle:\d+|del:\d+|delcat:\d+|delsize:\d+|addcat)$",
        )
    )
    app.add_handler(CallbackQueryHandler(admin_status_callback, pattern=r"^admin_status:"))
    app.add_handler(
        CallbackQueryHandler(admin_delete_order_callback, pattern=r"^admin_del_order")
    )
    app.add_handler(CallbackQueryHandler(payment_callback, pattern=r"^pay"))
    app.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, webapp_scan_data))

    print("Bot ishga tushdi...")
    if WEBHOOK_URL:
        listen_port = WEBHOOK_PORT or WEBAPP_PORT
        webhook_url = f"{WEBHOOK_URL}/{WEBHOOK_PATH.lstrip('/')}"
        print(f"Webhook: {webhook_url} (listen :{listen_port})")
        app.run_webhook(
            listen="0.0.0.0",
            port=listen_port,
            url_path=WEBHOOK_PATH,
            webhook_url=webhook_url,
            allowed_updates=["message", "callback_query", "pre_checkout_query"],
        )
    else:
        app.run_polling(
            allowed_updates=["message", "callback_query", "pre_checkout_query"]
        )


if __name__ == "__main__":
    main()
