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

- 💬 AI suhbat (OpenAI yoki mahalliy qidiruv)
- 📦 Katalog kategoriyalar bilan
- 🛒 Savat (+/−) · tezkor: `2 ta sut`
- ✅ Buyurtma · 📋 Mening buyurtmalarim
- 🛠 `/add` `/off` `/on` `/orders` `/stats`

## Admin

| Buyruq | Vazifa |
|--------|--------|
| `/admin` | Panel |
| `/stats` | Statistika |
| `/orders` | Yangi buyurtmalar |
| `/add Nom \| 12000 \| Kategoriya` | Mahsulot |
| `/off 3` / `/on 3` | Yashirish / yoqish |
