"""Oddiy uz/ru tarjimalar."""

from __future__ import annotations

from bot.config import DEFAULT_LANG

STRINGS: dict[str, dict[str, str]] = {
    "welcome": {
        "uz": "Assalomu alaykum, {name}! 👋\n{shop} ga xush kelibsiz.",
        "ru": "Здравствуйте, {name}! 👋\nДобро пожаловать в {shop}.",
    },
    "help_short": {
        "uz": "🛍 Katalog → savatcha → buyurtma.\nYordam: /help",
        "ru": "🛍 Каталог → корзина → заказ.\nПомощь: /help",
    },
    "cart_empty": {
        "uz": "🛒 Savatchangiz bo'sh",
        "ru": "🛒 Ваша корзина пуста",
    },
    "order_status_updated": {
        "uz": "🔔 Buyurtma #{order_id} holati yangilandi:\n{status}",
        "ru": "🔔 Статус заказа #{order_id} обновлён:\n{status}",
    },
    "rating_ask": {
        "uz": "⭐ Buyurtma #{order_id} qanday o'tdi? Baholang:",
        "ru": "⭐ Как прошёл заказ #{order_id}? Оцените:",
    },
    "rating_thanks": {
        "uz": "Rahmat! Bahoyingiz qabul qilindi ⭐",
        "ru": "Спасибо! Ваша оценка принята ⭐",
    },
    "low_stock_alert": {
        "uz": "⚠️ Kam qoldiq:\n{items}",
        "ru": "⚠️ Мало на складе:\n{items}",
    },
    "daily_report_title": {
        "uz": "📈 Kunlik hisobot ({date})",
        "ru": "📈 Дневной отчёт ({date})",
    },
    "lang_set": {
        "uz": "✅ Til: O'zbekcha",
        "ru": "✅ Язык: Русский",
    },
    "choose_lang": {
        "uz": "🌐 Tilni tanlang:",
        "ru": "🌐 Выберите язык:",
    },
    "recommend_title": {
        "uz": "✨ Sizga tavsiya qilamiz",
        "ru": "✨ Рекомендуем вам",
    },
    "recurring_saved": {
        "uz": "✅ Takroriy buyurtma saqlandi (har {days} kun)",
        "ru": "✅ Повторный заказ сохранён (каждые {days} дн.)",
    },
    "recurring_due": {
        "uz": "Bugun takroriy buyurtma kuni — savatchaga qo'shildi",
        "ru": "Сегодня день повторного заказа — добавлено в корзину",
    },
    "zone_delivery": {
        "uz": "🚚 Yetkazish: {price:,} so'm",
        "ru": "🚚 Доставка: {price:,} сум",
    },
    "no_recommendations": {
        "uz": "Hozircha tavsiyalar yo'q.",
        "ru": "Пока нет рекомендаций.",
    },
    "no_recurring": {
        "uz": "Faol takroriy buyurtmalar yo'q.",
        "ru": "Нет активных повторных заказов.",
    },
}


def normalize_lang(lang: str | None) -> str:
    lang = (lang or DEFAULT_LANG or "uz").strip().lower()
    return lang if lang in ("uz", "ru") else "uz"


def t(key: str, lang: str = "uz", **kwargs) -> str:
    lang = normalize_lang(lang)
    entry = STRINGS.get(key) or {}
    text = entry.get(lang) or entry.get("uz") or key
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, ValueError):
            return text
    return text


def get_user_lang(user_id: int) -> str:
    from bot.database import get_user_language

    return normalize_lang(get_user_language(user_id))


def set_user_lang(user_id: int, lang: str) -> None:
    from bot.database import set_user_language

    set_user_language(user_id, normalize_lang(lang))
