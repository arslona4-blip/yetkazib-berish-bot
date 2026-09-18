"""O‘zbekcha matnlar — Vositachi bot."""

from __future__ import annotations

WELCOME = (
    "🚕 <b>{bot_name}</b>\n\n"
    "Mijoz va haydovchini bog‘laymiz.\n"
    "Rolingizni tanlang:"
)

ROLE_CHOSEN_CUSTOMER = (
    "✅ Siz <b>mijoz</b> sifatida kirdingiz.\n"
    "«🚕 Safar so‘rash» tugmasini bosing."
)

ROLE_CHOSEN_DRIVER = (
    "✅ Siz <b>haydovchi</b> sifatida kirdingiz.\n"
    "Ishlash uchun «🟢 Onlayn» ni bosing."
)

ROLE_CHOSEN_ADMIN = (
    "✅ Admin panel.\n"
    "Safarlar, tarif, haydovchilar va statistika."
)

ASK_PICKUP = (
    "📍 <b>Qayerdan</b> olasiz?\n\n"
    "Manzilni yozing yoki lokatsiya yuboring."
)

ASK_DESTINATION = (
    "🏁 <b>Qayerga</b> borasiz?\n\n"
    "Manzilni yozing yoki lokatsiya yuboring."
)

ASK_PHONE = (
    "📞 Telefon (ixtiyoriy).\n\n"
    "Raqam yozing, kontakt ulashing yoki «O‘tkazib yuborish»."
)

REQUEST_CREATED = (
    "✅ So‘rov <b>#{ride_id}</b> yaratildi.\n\n"
    "📍 {pickup}\n"
    "🏁 {destination}\n"
    "📞 {phone}\n"
    "📏 ~{distance} km\n"
    "💰 Taxminiy narx: <b>{price}</b>\n"
    "🏷 Komissiya ({commission_pct}%): {commission}\n\n"
    "Onlayn haydovchilarga yuborildi. Kuting…"
)

NO_ONLINE_DRIVERS = (
    "⚠️ Hozir onlayn haydovchi yo‘q. So‘rovingiz ochiq — "
    "haydovchi chiqishi bilan ko‘radi."
)

NEW_RIDE_FOR_DRIVER = (
    "🆕 Yangi so‘rov <b>#{ride_id}</b>\n\n"
    "📍 {pickup}\n"
    "🏁 {destination}\n"
    "📞 {phone}\n"
    "📏 ~{distance} km\n"
    "💰 Taxminiy: <b>{price}</b>\n"
    "Mijoz: {customer}"
)

RIDE_ACCEPTED_CUSTOMER = (
    "✅ Haydovchi qabul qildi!\n\n"
    "So‘rov #{ride_id}\n"
    "💰 Kelishilgan / taxminiy: <b>{price}</b>\n"
    "Haydovchi: {driver}\n"
    "{contact_block}\n\n"
    "Bog‘laning yoki haydovchi qo‘ng‘iroq qiladi."
)

RIDE_ACCEPTED_DRIVER = (
    "✅ Qabul qildingiz — #{ride_id}\n\n"
    "📍 {pickup}\n"
    "🏁 {destination}\n"
    "💰 Narx: <b>{price}</b> (komissiya {commission})\n"
    "Mijoz: {customer}\n"
    "{contact_block}\n\n"
    "Narxni o‘zgartirish, yo‘lda boshlash yoki bekor."
)

PRICE_UPDATED = (
    "💵 #{ride_id} uchun yangi narx: <b>{price}</b>\n"
    "Komissiya ({pct}%): {commission}"
)

ALREADY_TAKEN = "❌ Bu so‘rov allaqachon olingan."

NOT_YOUR_RIDE = "❌ Bu safar sizniki emas."

STATUS_IN_PROGRESS = "🚗 Safar #{ride_id} yo‘lda. Narx: {price}"

STATUS_DONE = (
    "✅ Safar #{ride_id} tugadi.\n"
    "💰 {price}\n\n"
    "Hamkoringizni baholang (1–5):"
)

STATUS_CANCELLED = "🚫 Safar #{ride_id} bekor qilindi."

DRIVER_ONLINE = "🟢 Siz onlaynsiz. Yangi so‘rovlar keladi."

DRIVER_OFFLINE = "🔴 Siz oflaynsiz."

DRIVER_BLOCKED = "⛔ Hisobingiz bloklangan. Admin bilan bog‘laning."

OPEN_RIDES_EMPTY = "Ochiq so‘rov yo‘q."

OPEN_RIDES_HEADER = "📋 Ochiq so‘rovlar ({count}):"

ACTIVE_RIDES_HEADER = "🚗 Faol safarlar ({count}):"

DONE_RIDES_HEADER = "✅ So‘nggi tugaganlar ({count}):"

MY_ACTIVE_EMPTY = "Faol safaringiz yo‘q."

STATS = (
    "📊 <b>Statistika</b>\n\n"
    "Foydalanuvchilar: {users}\n"
    "Haydovchilar (onlayn): {drivers_online}/{drivers}\n"
    "Ochiq: {open}\n"
    "Qabul / yo‘lda: {accepted} / {in_progress}\n"
    "Tugagan: {done}\n"
    "Bekor: {cancelled}\n"
    "Tugagan summa: {done_sum}\n"
    "Komissiya (tugagan): {commission_sum}"
)

TARIFF_INFO = (
    "⚙️ <b>Tarif</b>\n\n"
    "Baza: {base}\n"
    "1 km: {per_km}\n"
    "Taxminiy km (lokatsiyasiz): {default_km}\n"
    "Komissiya: {commission_pct}%\n\n"
    "O‘zgartirish: /set_base 8000 · /set_km 2000\n"
    "/set_commission 10 · /set_default_km 5"
)

DRIVERS_HEADER = "🚗 Haydovchilar ({count}):"

ASK_OFFER_PRICE = (
    "💵 Yangi narxni so‘mda yozing (masalan: 25000).\n"
    "Bekor: /cancel"
)

RATING_THANKS = "⭐ Bahongiz qabul qilindi. Rahmat!"

RATING_ALREADY = "Bu safar allaqachon baholangan."

CANCEL_FLOW = "Bekor qilindi. Menyuga qaytdingiz."

NEED_ROLE = "Avval /start orqali rol tanlang."

ONLY_DRIVER = "Bu faqat haydovchilar uchun."

ONLY_CUSTOMER = "Bu faqat mijozlar uchun."

ONLY_ADMIN = "Bu faqat admin uchun."

HELP = (
    "🚕 <b>Vositachi</b>\n\n"
    "• Mijoz: safar so‘raydi, narxni ko‘radi, baholaydi\n"
    "• Haydovchi: onlayn/oflayn, qabul, narx, holat\n"
    "• Admin: tarif, safarlar, statistika\n\n"
    "/start — boshlash"
)

UNKNOWN = "Tushunmadim. Menyudan tugma tanlang yoki /start."
