from __future__ import annotations

from telegram import (
    BotCommand,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

from vositachi.config import ADMIN_IDS


def role_keyboard(user_id: int | None = None) -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton("👤 Mijoz"), KeyboardButton("🚗 Haydovchi")],
    ]
    if user_id is not None and user_id in ADMIN_IDS:
        rows.append([KeyboardButton("🛠 Admin")])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)


def customer_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("🚕 Safar so‘rash")],
            [
                KeyboardButton("📋 Mening safarlarim"),
                KeyboardButton("🔄 Rol almashtirish"),
            ],
        ],
        resize_keyboard=True,
    )


def driver_menu(*, online: bool) -> ReplyKeyboardMarkup:
    status_btn = "🔴 Oflayn" if online else "🟢 Onlayn"
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton(status_btn), KeyboardButton("📋 Ochiq so‘rovlar")],
            [
                KeyboardButton("🚕 Faol safar"),
                KeyboardButton("🔄 Rol almashtirish"),
            ],
        ],
        resize_keyboard=True,
    )


def admin_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("📊 Statistika"), KeyboardButton("⚙️ Tarif")],
            [
                KeyboardButton("📋 Ochiq"),
                KeyboardButton("🚗 Faol"),
                KeyboardButton("✅ Tugagan"),
            ],
            [KeyboardButton("👥 Haydovchilar"), KeyboardButton("🔄 Rol almashtirish")],
        ],
        resize_keyboard=True,
    )


def cancel_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [[KeyboardButton("❌ Bekor")]],
        resize_keyboard=True,
    )


def phone_skip_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("📞 Telefonni ulashish", request_contact=True)],
            [KeyboardButton("⏭ O‘tkazib yuborish"), KeyboardButton("❌ Bekor")],
        ],
        resize_keyboard=True,
    )


def location_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("📍 Lokatsiya yuborish", request_location=True)],
            [KeyboardButton("❌ Bekor")],
        ],
        resize_keyboard=True,
    )


def accept_keyboard(ride_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ Qabul qilish",
                    callback_data=f"ride:accept:{ride_id}",
                )
            ]
        ]
    )


def trip_actions_keyboard(ride_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "💵 Narx",
                    callback_data=f"ride:price:{ride_id}",
                ),
                InlineKeyboardButton(
                    "🚗 Yo‘lda",
                    callback_data=f"ride:progress:{ride_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    "✅ Tugadi",
                    callback_data=f"ride:done:{ride_id}",
                ),
                InlineKeyboardButton(
                    "🚫 Bekor",
                    callback_data=f"ride:cancel:{ride_id}",
                ),
            ],
        ]
    )


def rating_keyboard(ride_id: int, *, as_customer: bool) -> InlineKeyboardMarkup:
    who = "c" if as_customer else "d"
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    f"{n}★",
                    callback_data=f"rate:{who}:{ride_id}:{n}",
                )
                for n in range(1, 6)
            ]
        ]
    )


def admin_ride_keyboard(ride_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🚫 Bekor qilish",
                    callback_data=f"admin:cancel:{ride_id}",
                )
            ]
        ]
    )


def admin_driver_keyboard(user_id: int, *, blocked: bool) -> InlineKeyboardMarkup:
    if blocked:
        btn = InlineKeyboardButton(
            "✅ Blokdan chiqarish",
            callback_data=f"admin:unblock:{user_id}",
        )
    else:
        btn = InlineKeyboardButton(
            "⛔ Bloklash",
            callback_data=f"admin:block:{user_id}",
        )
    offline = InlineKeyboardButton(
        "🔴 Oflayn qilish",
        callback_data=f"admin:offline:{user_id}",
    )
    return InlineKeyboardMarkup([[btn], [offline]])


def remove_kb() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()


def bot_commands(*, is_admin: bool = False) -> list[BotCommand]:
    cmds = [
        BotCommand("start", "Boshlash / rol tanlash"),
        BotCommand("help", "Yordam"),
        BotCommand("cancel", "Joriy amalni bekor qilish"),
    ]
    if is_admin:
        cmds.extend(
            [
                BotCommand("stats", "Statistika"),
                BotCommand("open", "Ochiq so‘rovlar"),
                BotCommand("tariff", "Tarif"),
            ]
        )
    return cmds
