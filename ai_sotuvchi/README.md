# AI Sotuvchi — Baraka Marketdan alohida loyiha

Do‘kon uchun **sun’iy sotuvchi** Telegram bot:
mijoz yozadi → bot javob beradi / mahsulot topadi → savat → buyurtma → admin tasdiq.

## Imkoniyatlar

- 💬 AI suhbat (OpenAI yoki mahalliy qidiruv)
- 📦 Katalog kategoriyalar bilan
- 🛒 Savat (+/− miqdor)
- Tezkor qo‘shish: `2 ta sut` / `cola qo‘sh`
- ✅ Buyurtma (telefon, manzil, ism)
- 📋 Mening buyurtmalarim + status
- 🛠 Admin: `/add`, `/off`, `/on`, `/orders`, `/stats`

## Tezkor start

1. [@BotFather](https://t.me/BotFather) dan **yangi** bot oling (Baraka tokenidan boshqa).
2. Sozlamalar:

```bash
cd /path/to/yetkazib-berish-bot
cp ai_sotuvchi/.env.example .env   # yoki ai_sotuvchi/.env
# AI_SOTUVCHI_BOT_TOKEN va AI_SOTUVCHI_ADMIN_IDS ni to‘ldiring
```

3. Ishga tushirish (repo ildizidan):

```bash
pip install -r requirements.txt
python -m ai_sotuvchi
```

## AI yoqish (ixtiyoriy)

```
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

Kalit bo‘lmasa ham bot ishlaydi: mahsulot nomidan qidiradi.

## Admin buyruqlari

| Buyruq | Vazifa |
|--------|--------|
| `/admin` | Panel + statistika |
| `/stats` | Tushum / buyurtmalar |
| `/orders` | Yangi buyurtmalar |
| `/orders accepted` | Qabul qilinganlar |
| `/add Nom \| 12000 \| Kategoriya` | Mahsulot qo‘shish |
| `/off 3` | Mahsulotni yashirish |
| `/on 3` | Qayta yoqish |

## Baraka Market bilan

Alohida DB va token: `data/ai_sotuvchi.db`, `AI_SOTUVCHI_BOT_TOKEN`.
Asosiy yetkazib berish botiga tegmaydi.
