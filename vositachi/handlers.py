from __future__ import annotations

import logging
from typing import Any

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from vositachi import database as db
from vositachi import texts
from vositachi.config import ADMIN_IDS, BOT_NAME
from vositachi.keyboards import (
    accept_keyboard,
    admin_driver_keyboard,
    admin_menu,
    admin_ride_keyboard,
    cancel_kb,
    customer_menu,
    driver_menu,
    location_kb,
    phone_skip_kb,
    rating_keyboard,
    role_keyboard,
    trip_actions_keyboard,
)

logger = logging.getLogger("vositachi")

WAIT_PICKUP, WAIT_DEST, WAIT_PHONE, WAIT_PRICE = range(4)

STATUS_LABEL = {
    db.STATUS_OPEN: "ochiq",
    db.STATUS_ACCEPTED: "qabul",
    db.STATUS_IN_PROGRESS: "yo‘lda",
    db.STATUS_DONE: "tugagan",
    db.STATUS_CANCELLED: "bekor",
}


def _uid(update: Update) -> int | None:
    user = update.effective_user
    return user.id if user else None


def _full_name(update: Update) -> str:
    user = update.effective_user
    if not user:
        return ""
    return (user.full_name or user.first_name or "").strip()


def _ensure_user(update: Update) -> int | None:
    user = update.effective_user
    if not user:
        return None
    db.upsert_user(user.id, _full_name(update), user.username)
    return user.id


def _is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def _menu_for(user: dict[str, Any] | None, user_id: int):
    role = (user or {}).get("role")
    if role == "customer":
        return customer_menu()
    if role == "driver":
        return driver_menu(online=bool((user or {}).get("driver_online")))
    if role == "admin" and _is_admin(user_id):
        return admin_menu()
    return role_keyboard(user_id)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    uid = _ensure_user(update)
    if uid is None or not update.message:
        return ConversationHandler.END
    context.user_data.clear()
    await update.message.reply_html(
        texts.WELCOME.format(bot_name=BOT_NAME),
        reply_markup=role_keyboard(uid),
    )
    return ConversationHandler.END


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_html(texts.HELP)


async def cancel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    uid = _ensure_user(update)
    if uid is None or not update.message:
        return ConversationHandler.END
    context.user_data.clear()
    user = db.get_user(uid)
    await update.message.reply_text(
        texts.CANCEL_FLOW,
        reply_markup=_menu_for(user, uid),
    )
    return ConversationHandler.END


async def choose_role(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    uid = _ensure_user(update)
    if uid is None or not update.message:
        return
    text = (update.message.text or "").strip()
    if text == "👤 Mijoz":
        db.set_role(uid, "customer")
        await update.message.reply_html(
            texts.ROLE_CHOSEN_CUSTOMER,
            reply_markup=customer_menu(),
        )
        return
    if text == "🚗 Haydovchi":
        db.set_role(uid, "driver")
        user = db.get_user(uid)
        await update.message.reply_html(
            texts.ROLE_CHOSEN_DRIVER,
            reply_markup=driver_menu(online=bool((user or {}).get("driver_online"))),
        )
        return
    if text == "🛠 Admin":
        if not _is_admin(uid):
            await update.message.reply_text(texts.ONLY_ADMIN)
            return
        db.set_role(uid, "admin")
        await update.message.reply_html(
            texts.ROLE_CHOSEN_ADMIN,
            reply_markup=admin_menu(),
        )


async def switch_role(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    uid = _ensure_user(update)
    if uid is None or not update.message:
        return
    await update.message.reply_html(
        texts.WELCOME.format(bot_name=BOT_NAME),
        reply_markup=role_keyboard(uid),
    )


# --- Customer ride request ---


async def start_ride_request(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    uid = _ensure_user(update)
    if uid is None or not update.message:
        return ConversationHandler.END
    user = db.get_user(uid)
    if not user or user.get("role") != "customer":
        await update.message.reply_text(texts.ONLY_CUSTOMER)
        return ConversationHandler.END
    context.user_data["ride"] = {}
    await update.message.reply_html(texts.ASK_PICKUP, reply_markup=location_kb())
    return WAIT_PICKUP


async def receive_pickup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    uid = _ensure_user(update)
    if uid is None or not update.message:
        return ConversationHandler.END
    if (update.message.text or "").strip() == "❌ Bekor":
        return await cancel_cmd(update, context)

    ride_draft: dict[str, Any] = context.user_data.setdefault("ride", {})
    if update.message.location:
        loc = update.message.location
        ride_draft["pickup"] = f"Lokatsiya ({loc.latitude:.5f}, {loc.longitude:.5f})"
        ride_draft["pickup_lat"] = loc.latitude
        ride_draft["pickup_lon"] = loc.longitude
    else:
        text = (update.message.text or "").strip()
        if not text or text.startswith("/"):
            await update.message.reply_html(texts.ASK_PICKUP, reply_markup=location_kb())
            return WAIT_PICKUP
        ride_draft["pickup"] = text[:200]
        ride_draft.pop("pickup_lat", None)
        ride_draft.pop("pickup_lon", None)

    await update.message.reply_html(texts.ASK_DESTINATION, reply_markup=location_kb())
    return WAIT_DEST


async def receive_dest(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    uid = _ensure_user(update)
    if uid is None or not update.message:
        return ConversationHandler.END
    if (update.message.text or "").strip() == "❌ Bekor":
        return await cancel_cmd(update, context)

    ride_draft: dict[str, Any] = context.user_data.setdefault("ride", {})
    if update.message.location:
        loc = update.message.location
        ride_draft["destination"] = (
            f"Lokatsiya ({loc.latitude:.5f}, {loc.longitude:.5f})"
        )
        ride_draft["dest_lat"] = loc.latitude
        ride_draft["dest_lon"] = loc.longitude
    else:
        text = (update.message.text or "").strip()
        if not text or text.startswith("/"):
            await update.message.reply_html(
                texts.ASK_DESTINATION, reply_markup=location_kb()
            )
            return WAIT_DEST
        ride_draft["destination"] = text[:200]
        ride_draft.pop("dest_lat", None)
        ride_draft.pop("dest_lon", None)

    await update.message.reply_html(texts.ASK_PHONE, reply_markup=phone_skip_kb())
    return WAIT_PHONE


async def receive_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    uid = _ensure_user(update)
    if uid is None or not update.message:
        return ConversationHandler.END
    text = (update.message.text or "").strip()
    if text == "❌ Bekor":
        return await cancel_cmd(update, context)

    phone = ""
    if update.message.contact and update.message.contact.phone_number:
        phone = update.message.contact.phone_number
    elif text and text != "⏭ O‘tkazib yuborish":
        phone = text[:40]

    if phone:
        db.set_phone(uid, phone)

    ride_draft: dict[str, Any] = context.user_data.get("ride") or {}
    pickup = ride_draft.get("pickup") or ""
    destination = ride_draft.get("destination") or ""
    if not pickup or not destination:
        await update.message.reply_text(texts.CANCEL_FLOW, reply_markup=customer_menu())
        context.user_data.clear()
        return ConversationHandler.END

    ride = db.create_ride(
        customer_id=uid,
        pickup=pickup,
        destination=destination,
        phone=phone or (db.get_user(uid) or {}).get("phone") or "",
        pickup_lat=ride_draft.get("pickup_lat"),
        pickup_lon=ride_draft.get("pickup_lon"),
        dest_lat=ride_draft.get("dest_lat"),
        dest_lon=ride_draft.get("dest_lon"),
    )
    context.user_data.clear()

    msg = texts.REQUEST_CREATED.format(
        ride_id=ride["id"],
        pickup=ride["pickup"],
        destination=ride["destination"],
        phone=ride.get("phone") or "—",
        distance=ride.get("distance_km") or "—",
        price=db.money(ride.get("estimated_price")),
        commission_pct=ride.get("commission_pct") or 0,
        commission=db.money(ride.get("commission_amount")),
    )
    await update.message.reply_html(msg, reply_markup=customer_menu())

    drivers = db.list_online_drivers(exclude_id=uid)
    if not drivers:
        await update.message.reply_text(texts.NO_ONLINE_DRIVERS)
    else:
        customer = db.get_user(uid)
        notify = texts.NEW_RIDE_FOR_DRIVER.format(
            ride_id=ride["id"],
            pickup=ride["pickup"],
            destination=ride["destination"],
            phone=ride.get("phone") or "—",
            distance=ride.get("distance_km") or "—",
            price=db.money(ride.get("estimated_price")),
            customer=db.display_name(customer),
        )
        for drv in drivers:
            try:
                await context.bot.send_message(
                    chat_id=drv["user_id"],
                    text=notify,
                    parse_mode="HTML",
                    reply_markup=accept_keyboard(ride["id"]),
                )
            except Exception as exc:
                logger.warning("Driver notify failed %s: %s", drv["user_id"], exc)

    # Notify admins
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=f"🆕 Yangi so‘rov #{ride['id']} — {db.money(ride.get('estimated_price'))}",
                reply_markup=admin_ride_keyboard(ride["id"]),
            )
        except Exception:
            pass

    return ConversationHandler.END


# --- Driver ---


async def driver_go_online(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    uid = _ensure_user(update)
    if uid is None or not update.message:
        return
    user = db.get_user(uid)
    if not user or user.get("role") != "driver":
        await update.message.reply_text(texts.ONLY_DRIVER)
        return
    if user.get("driver_blocked"):
        await update.message.reply_text(texts.DRIVER_BLOCKED)
        return
    db.set_driver_online(uid, True)
    await update.message.reply_text(
        texts.DRIVER_ONLINE,
        reply_markup=driver_menu(online=True),
    )


async def driver_go_offline(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    uid = _ensure_user(update)
    if uid is None or not update.message:
        return
    user = db.get_user(uid)
    if not user or user.get("role") != "driver":
        await update.message.reply_text(texts.ONLY_DRIVER)
        return
    db.set_driver_online(uid, False)
    await update.message.reply_text(
        texts.DRIVER_OFFLINE,
        reply_markup=driver_menu(online=False),
    )


async def show_open_rides(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    uid = _ensure_user(update)
    if uid is None or not update.message:
        return
    user = db.get_user(uid)
    rides = db.list_open_rides()
    if not rides:
        await update.message.reply_text(texts.OPEN_RIDES_EMPTY)
        return
    await update.message.reply_text(texts.OPEN_RIDES_HEADER.format(count=len(rides)))
    for ride in rides:
        price = db.money(ride.get("estimated_price"))
        body = (
            f"#{ride['id']}\n"
            f"📍 {ride['pickup']}\n"
            f"🏁 {ride['destination']}\n"
            f"💰 {price}"
        )
        kb = None
        if user and user.get("role") == "driver" and not user.get("driver_blocked"):
            kb = accept_keyboard(ride["id"])
        elif _is_admin(uid):
            kb = admin_ride_keyboard(ride["id"])
        await update.message.reply_text(body, reply_markup=kb)


async def show_active_ride(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    uid = _ensure_user(update)
    if uid is None or not update.message:
        return
    ride = db.get_driver_active_ride(uid)
    if not ride:
        await update.message.reply_text(texts.MY_ACTIVE_EMPTY)
        return
    customer = db.get_user(ride["customer_id"])
    price = ride.get("agreed_price") or ride.get("estimated_price")
    body = (
        f"🚕 #{ride['id']} — {STATUS_LABEL.get(ride['status'], ride['status'])}\n"
        f"📍 {ride['pickup']}\n"
        f"🏁 {ride['destination']}\n"
        f"💰 {db.money(price)}\n"
        f"{db.contact_block(customer)}"
    )
    await update.message.reply_html(body, reply_markup=trip_actions_keyboard(ride["id"]))


async def my_rides(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    uid = _ensure_user(update)
    if uid is None or not update.message:
        return
    rides = db.list_user_rides(uid)
    if not rides:
        await update.message.reply_text("Hali safar yo‘q.")
        return
    lines = [db.format_ride_short(r) for r in rides]
    await update.message.reply_text("📋 Mening safarlarim:\n" + "\n".join(lines))


# --- Callbacks: accept / status / price / rate / admin ---


async def callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int | None:
    query = update.callback_query
    if not query or not query.data:
        return None
    await query.answer()
    uid = _ensure_user(update)
    if uid is None:
        return None
    parts = query.data.split(":")
    if len(parts) < 2:
        return None

    if parts[0] == "ride":
        return await _ride_callback(update, context, parts)
    if parts[0] == "rate":
        await _rate_callback(update, context, parts)
        return None
    if parts[0] == "admin":
        await _admin_callback(update, context, parts)
        return None
    return None


async def _ride_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE, parts: list[str]
) -> int | None:
    query = update.callback_query
    assert query is not None
    uid = _uid(update)
    assert uid is not None
    action = parts[1]
    try:
        ride_id = int(parts[2])
    except (IndexError, ValueError):
        return None

    user = db.get_user(uid)

    if action == "accept":
        if not user or user.get("role") != "driver":
            await query.edit_message_text(texts.ONLY_DRIVER)
            return None
        if user.get("driver_blocked"):
            await query.edit_message_text(texts.DRIVER_BLOCKED)
            return None
        if not user.get("driver_online"):
            db.set_driver_online(uid, True)
        ride = db.accept_ride(ride_id, uid)
        if not ride:
            await query.edit_message_text(texts.ALREADY_TAKEN)
            return None
        customer = db.get_user(ride["customer_id"])
        driver = db.get_user(uid)
        price = ride.get("agreed_price") or ride.get("estimated_price")
        await query.edit_message_text(
            texts.RIDE_ACCEPTED_DRIVER.format(
                ride_id=ride_id,
                pickup=ride["pickup"],
                destination=ride["destination"],
                price=db.money(price),
                commission=db.money(ride.get("commission_amount")),
                customer=db.display_name(customer),
                contact_block=db.contact_block(customer),
            ),
            parse_mode="HTML",
            reply_markup=trip_actions_keyboard(ride_id),
        )
        try:
            await context.bot.send_message(
                chat_id=ride["customer_id"],
                text=texts.RIDE_ACCEPTED_CUSTOMER.format(
                    ride_id=ride_id,
                    price=db.money(price),
                    driver=db.display_name(driver),
                    contact_block=db.contact_block(driver),
                ),
                parse_mode="HTML",
            )
        except Exception as exc:
            logger.warning("Customer notify: %s", exc)
        return None

    ride = db.get_ride(ride_id)
    if not ride:
        await query.answer("Topilmadi", show_alert=True)
        return None

    if action == "price":
        if ride.get("driver_id") != uid:
            await query.answer(texts.NOT_YOUR_RIDE, show_alert=True)
            return None
        context.user_data["offer_ride_id"] = ride_id
        await query.message.reply_text(texts.ASK_OFFER_PRICE, reply_markup=cancel_kb())
        return WAIT_PRICE

    if action == "progress":
        updated = db.update_ride_status(
            ride_id, db.STATUS_IN_PROGRESS, by_driver_id=uid
        )
        if not updated:
            await query.answer(texts.NOT_YOUR_RIDE, show_alert=True)
            return None
        price = db.money(updated.get("agreed_price") or updated.get("estimated_price"))
        msg = texts.STATUS_IN_PROGRESS.format(ride_id=ride_id, price=price)
        await query.edit_message_reply_markup(reply_markup=trip_actions_keyboard(ride_id))
        await query.message.reply_text(msg)
        try:
            await context.bot.send_message(chat_id=updated["customer_id"], text=msg)
        except Exception:
            pass
        return None

    if action == "done":
        updated = db.update_ride_status(ride_id, db.STATUS_DONE, by_driver_id=uid)
        if not updated:
            await query.answer(texts.NOT_YOUR_RIDE, show_alert=True)
            return None
        price = db.money(updated.get("agreed_price") or updated.get("estimated_price"))
        done_msg = texts.STATUS_DONE.format(ride_id=ride_id, price=price)
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text(
            done_msg,
            reply_markup=rating_keyboard(ride_id, as_customer=False),
        )
        try:
            await context.bot.send_message(
                chat_id=updated["customer_id"],
                text=done_msg,
                reply_markup=rating_keyboard(ride_id, as_customer=True),
            )
        except Exception:
            pass
        return None

    if action == "cancel":
        updated = db.cancel_ride(ride_id, by_user_id=uid)
        if not updated:
            await query.answer(texts.NOT_YOUR_RIDE, show_alert=True)
            return None
        msg = texts.STATUS_CANCELLED.format(ride_id=ride_id)
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text(msg)
        other = (
            updated["customer_id"]
            if uid == updated.get("driver_id")
            else updated.get("driver_id")
        )
        if other:
            try:
                await context.bot.send_message(chat_id=other, text=msg)
            except Exception:
                pass
        return None

    return None


async def receive_price_offer(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    uid = _ensure_user(update)
    if uid is None or not update.message:
        return ConversationHandler.END
    text = (update.message.text or "").strip()
    if text == "❌ Bekor":
        context.user_data.pop("offer_ride_id", None)
        user = db.get_user(uid)
        await update.message.reply_text(
            texts.CANCEL_FLOW, reply_markup=_menu_for(user, uid)
        )
        return ConversationHandler.END

    ride_id = context.user_data.get("offer_ride_id")
    digits = "".join(ch for ch in text if ch.isdigit())
    if not ride_id or not digits:
        await update.message.reply_text(texts.ASK_OFFER_PRICE)
        return WAIT_PRICE
    price = int(digits)
    if price < 1000:
        await update.message.reply_text("Narx juda kichik. Qayta yozing.")
        return WAIT_PRICE

    ride = db.set_agreed_price(int(ride_id), uid, price)
    context.user_data.pop("offer_ride_id", None)
    if not ride:
        await update.message.reply_text(texts.NOT_YOUR_RIDE, reply_markup=driver_menu(
            online=bool((db.get_user(uid) or {}).get("driver_online"))
        ))
        return ConversationHandler.END

    msg = texts.PRICE_UPDATED.format(
        ride_id=ride["id"],
        price=db.money(price),
        pct=ride.get("commission_pct") or 0,
        commission=db.money(ride.get("commission_amount")),
    )
    user = db.get_user(uid)
    await update.message.reply_html(msg, reply_markup=_menu_for(user, uid))
    try:
        await context.bot.send_message(
            chat_id=ride["customer_id"],
            text=msg,
            parse_mode="HTML",
        )
    except Exception:
        pass
    return ConversationHandler.END


async def _rate_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE, parts: list[str]
) -> None:
    query = update.callback_query
    assert query is not None
    uid = _uid(update)
    assert uid is not None
    # rate:c:ride_id:stars or rate:d:...
    try:
        who = parts[1]
        ride_id = int(parts[2])
        stars = int(parts[3])
    except (IndexError, ValueError):
        return
    by_customer = who == "c"
    ride = db.get_ride(ride_id)
    if not ride:
        return
    if by_customer and ride.get("customer_id") != uid:
        await query.answer(texts.NOT_YOUR_RIDE, show_alert=True)
        return
    if not by_customer and ride.get("driver_id") != uid:
        await query.answer(texts.NOT_YOUR_RIDE, show_alert=True)
        return
    updated = db.set_rating(ride_id, by_customer=by_customer, stars=stars)
    if not updated:
        await query.answer(texts.RATING_ALREADY, show_alert=True)
        return
    await query.edit_message_text(texts.RATING_THANKS)


async def _admin_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE, parts: list[str]
) -> None:
    query = update.callback_query
    assert query is not None
    uid = _uid(update)
    assert uid is not None
    if not _is_admin(uid):
        await query.answer(texts.ONLY_ADMIN, show_alert=True)
        return
    action = parts[1]
    try:
        target = int(parts[2])
    except (IndexError, ValueError):
        return

    if action == "cancel":
        ride = db.cancel_ride(target, force=True)
        if not ride:
            await query.answer("Bekor qilib bo‘lmadi", show_alert=True)
            return
        msg = texts.STATUS_CANCELLED.format(ride_id=target)
        await query.edit_message_text(msg)
        for chat_id in {ride.get("customer_id"), ride.get("driver_id")} - {None}:
            try:
                await context.bot.send_message(chat_id=chat_id, text=msg)
            except Exception:
                pass
        return

    if action == "block":
        db.set_driver_blocked(target, True)
        await query.edit_message_text(f"⛔ Haydovchi {target} bloklandi.")
        return
    if action == "unblock":
        db.set_driver_blocked(target, False)
        await query.edit_message_text(f"✅ Haydovchi {target} blokdan chiqarildi.")
        return
    if action == "offline":
        db.set_driver_online(target, False)
        await query.answer("Oflayn qilindi")
        return


# --- Admin panels ---


async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    uid = _ensure_user(update)
    if uid is None or not update.message:
        return
    if not _is_admin(uid):
        await update.message.reply_text(texts.ONLY_ADMIN)
        return
    s = db.get_stats()
    await update.message.reply_html(
        texts.STATS.format(
            users=s["users"],
            drivers=s["drivers"],
            drivers_online=s["drivers_online"],
            open=s["open"],
            accepted=s["accepted"],
            in_progress=s["in_progress"],
            done=s["done"],
            cancelled=s["cancelled"],
            done_sum=db.money(s["done_sum"]),
            commission_sum=db.money(s["commission_sum"]),
        ),
        reply_markup=admin_menu(),
    )


async def admin_tariff(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    uid = _ensure_user(update)
    if uid is None or not update.message:
        return
    if not _is_admin(uid):
        await update.message.reply_text(texts.ONLY_ADMIN)
        return
    t = db.get_tariff()
    await update.message.reply_html(
        texts.TARIFF_INFO.format(
            base=db.money(t["base_fare"]),
            per_km=db.money(t["per_km"]),
            default_km=t["default_estimate_km"],
            commission_pct=t["commission_pct"],
        ),
        reply_markup=admin_menu(),
    )


async def admin_set_number(
    update: Update, context: ContextTypes.DEFAULT_TYPE, key: str
) -> None:
    uid = _ensure_user(update)
    if uid is None or not update.message:
        return
    if not _is_admin(uid):
        await update.message.reply_text(texts.ONLY_ADMIN)
        return
    args = context.args or []
    if not args:
        await update.message.reply_text(f"Misól: /{update.message.text.split()[0][1:]} 10")
        return
    raw = args[0].replace(",", ".")
    try:
        val = float(raw)
    except ValueError:
        await update.message.reply_text("Raqam kiriting.")
        return
    db.set_setting(key, str(val))
    await update.message.reply_text(f"✅ {key} = {val}")
    await admin_tariff(update, context)


async def cmd_set_base(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await admin_set_number(update, context, "base_fare")


async def cmd_set_km(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await admin_set_number(update, context, "per_km")


async def cmd_set_commission(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await admin_set_number(update, context, "commission_pct")


async def cmd_set_default_km(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await admin_set_number(update, context, "default_estimate_km")


async def admin_list_status(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    statuses: tuple[str, ...],
    header: str,
) -> None:
    uid = _ensure_user(update)
    if uid is None or not update.message:
        return
    if not _is_admin(uid):
        await update.message.reply_text(texts.ONLY_ADMIN)
        return
    rides = db.list_rides_by_status(statuses)
    if not rides:
        await update.message.reply_text("Ro‘yxat bo‘sh.")
        return
    await update.message.reply_text(header.format(count=len(rides)))
    for ride in rides[:15]:
        await update.message.reply_text(
            db.format_ride_short(ride),
            reply_markup=admin_ride_keyboard(ride["id"])
            if ride["status"] in (db.STATUS_OPEN, db.STATUS_ACCEPTED, db.STATUS_IN_PROGRESS)
            else None,
        )


async def admin_open(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await admin_list_status(
        update, context, (db.STATUS_OPEN,), texts.OPEN_RIDES_HEADER
    )


async def admin_active(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await admin_list_status(
        update,
        context,
        (db.STATUS_ACCEPTED, db.STATUS_IN_PROGRESS),
        texts.ACTIVE_RIDES_HEADER,
    )


async def admin_done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await admin_list_status(
        update, context, (db.STATUS_DONE,), texts.DONE_RIDES_HEADER
    )


async def admin_drivers(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    uid = _ensure_user(update)
    if uid is None or not update.message:
        return
    if not _is_admin(uid):
        await update.message.reply_text(texts.ONLY_ADMIN)
        return
    drivers = db.list_drivers()
    if not drivers:
        await update.message.reply_text("Haydovchi yo‘q.")
        return
    await update.message.reply_text(texts.DRIVERS_HEADER.format(count=len(drivers)))
    for d in drivers:
        online = "🟢" if d.get("driver_online") else "🔴"
        blocked = " ⛔" if d.get("driver_blocked") else ""
        body = (
            f"{online}{blocked} {db.display_name(d)}\n"
            f"⭐ {db.avg_rating(d)} · id={d['user_id']}"
        )
        await update.message.reply_text(
            body,
            reply_markup=admin_driver_keyboard(
                d["user_id"], blocked=bool(d.get("driver_blocked"))
            ),
        )


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Fallback menu router for reply keyboard buttons."""
    if not update.message or not update.message.text:
        return
    # If waiting for price offer outside ConversationHandler edge case
    if context.user_data.get("offer_ride_id"):
        await receive_price_offer(update, context)
        return

    uid = _ensure_user(update)
    if uid is None:
        return
    text = update.message.text.strip()
    user = db.get_user(uid)

    if text in ("👤 Mijoz", "🚗 Haydovchi", "🛠 Admin"):
        await choose_role(update, context)
        return
    if text == "🔄 Rol almashtirish":
        await switch_role(update, context)
        return
    if text == "🚕 Safar so‘rash":
        # Conversation handled separately; nudge
        await update.message.reply_text(
            "Safar so‘rash uchun tugmani qayta bosing yoki /start."
        )
        return
    if text == "🟢 Onlayn":
        await driver_go_online(update, context)
        return
    if text == "🔴 Oflayn":
        await driver_go_offline(update, context)
        return
    if text == "📋 Ochiq so‘rovlar":
        await show_open_rides(update, context)
        return
    if text == "🚕 Faol safar":
        await show_active_ride(update, context)
        return
    if text == "📋 Mening safarlarim":
        await my_rides(update, context)
        return
    if text == "📊 Statistika":
        await admin_stats(update, context)
        return
    if text == "⚙️ Tarif":
        await admin_tariff(update, context)
        return
    if text == "📋 Ochiq":
        await admin_open(update, context)
        return
    if text == "🚗 Faol":
        await admin_active(update, context)
        return
    if text == "✅ Tugagan":
        await admin_done(update, context)
        return
    if text == "👥 Haydovchilar":
        await admin_drivers(update, context)
        return

    if not user or not user.get("role"):
        await update.message.reply_html(
            texts.WELCOME.format(bot_name=BOT_NAME),
            reply_markup=role_keyboard(uid),
        )
        return
    await update.message.reply_text(texts.UNKNOWN, reply_markup=_menu_for(user, uid))
