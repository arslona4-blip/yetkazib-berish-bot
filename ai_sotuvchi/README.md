# AI Sotuvchi — Baraka Marketdan alohida loyiha

Do‘kon uchun **sun’iy sotuvchi** Telegram bot:
mijoz yozadi → bot javob beradi / mahsulot topadi → savat → buyurtma → admin tasdiq.

## Imkoniyatlar (MVP)

- 💬 AI suhbat (OpenAI yoki mahalliy qidiruv)
- 📦 Katalog + tugma bilan savatga qo‘shish
- 🛒 Savat va minimal summa
- ✅ Buyurtma (telefon, manzil, ism)
- 🛠 Admin: `/add`, `/orders`, qabul/bekor

## Tezkor start

1. [@BotFather](https://t.me/BotFather) dan **yangi** bot oling (Baraka tokenidan boshqa).
2. Sozlamalar:

```bash
cd /path/to/yetkazib-berish-bot
cp ai_sotuvchi/.env.example ai_sotuvchi/.env
# AI_SOTUVCHI_BOT_TOKEN va AI_SOTUVCHI_ADMIN_IDS ni to‘ldiring
```

3. Ishga tushirish (repo ildizidan):

```bash
pip install -r requirements.txt
python -m ai_sotuvchi
```

## AI yoqish (ixtiyoriy)

`.env` ga qo‘ying:

```
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

Kalit bo‘lmasa ham bot ishlaydi: mahsulot nomidan qidiradi.

## Admin buyruqlari

| Buyruq | Vazifa |
|--------|--------|
| `/admin` | Panel |
| `/orders` | Yangi buyurtmalar |
| `/add Nom \| 12000 \| Kategoriya` | Mahsulot qo‘shish |

## Baraka Market bilan

Bu loyiha **alohida** DB va token ishlatadi (`data/ai_sotuvchi.db`).
Asosiy yetkazib berish botiga tegmaydi.
