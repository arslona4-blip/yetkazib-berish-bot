# AI Sotuvchi — Baraka Marketdan alohida loyiha

Do‘kon uchun **sun’iy sotuvchi** Telegram bot.

## 1) Token olish

1. Telegramda [@BotFather](https://t.me/BotFather) → `/newbot`
2. Nom bering (masalan: `AI Sotuvchi`)
3. Berilgan token ni saqlang — bu `AI_SOTUVCHI_BOT_TOKEN`

> Baraka Market `BOT_TOKEN`idan **boshqa** bo‘lishi shart.

## 2) Lokal ishga tushirish

```bash
# repo ildizida
cp ai_sotuvchi/.env.example ai_sotuvchi/.env
# .env ichida:
# AI_SOTUVCHI_BOT_TOKEN=123456:ABC...
# AI_SOTUVCHI_ADMIN_IDS=sizning_telegram_id

pip install -r requirements.txt
python -m ai_sotuvchi
```

Telegram ID: botga `/start` → yoki `@userinfobot`.

## 3) Railway (Baraka bilan birga)

Deploy allaqachon `python -m run_bots` ishlatadi.

Railway → Variables:

| Key | Qiymat |
|-----|--------|
| `AI_SOTUVCHI_BOT_TOKEN` | yangi bot tokeni |
| `AI_SOTUVCHI_ADMIN_IDS` | admin Telegram ID |
| `AI_SOTUVCHI_SHOP_NAME` | do‘kon nomi (ixtiyoriy) |
| `OPENAI_API_KEY` | ixtiyoriy |

Token qo‘yilmasa faqat Baraka ishlayveradi.

## Imkoniyatlar

- 💬 AI sotuvchi: mahsulot qidiradi, savat yig‘adi, buyurtma oladi
- 🔍 Fuzzy qidiruv (`Yubileniy Pechene` → Yubileyniy Pechene)
- 📦 Kg mahsulot: **250g / 500g / 1kg** + **5 000 / 10 000 so‘mlik**
- 🛒 Savat (+/−) · tezkor: `2 ta sut`, `guruch 5000 so‘mlik`
- ✅ Buyurtma · saqlangan telefon/manzil (ikkinchi marta tez)
- 📋 Mening buyurtmalarim · qayta buyurtma
- 🛠 Admin: mahsulot tahrir (nom, narx, toifa, rasm), `/orders` `/stats`

## Professional oqim

- Salomlashuv va chek ko‘rinishidagi buyurtma
- Katalog → savat → buyurtma
- Status: Yangi → Qabul → Yetkazilmoqda → Yetkazildi
- 1 kg narxi o‘zgarsa 250g/500g avtomatik hisoblanadi

## Mahsulot qo‘shish

1. **➕ Mahsulot**
2. Nom
3. Narx
4. Rasm yoki **O‘tkazib yuborish**

## Test

```bash
python -m unittest ai_sotuvchi.tests
```

