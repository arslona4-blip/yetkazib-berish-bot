# Vositachi — taksi vositachilik boti

Mijoz va haydovchini bog‘laydigan Telegram bot (O‘zbekiston). UX — o‘zbekcha.

## MVP

1. **Tezkor bog‘lash** — so‘rov → onlayn haydovchilar → qabul → kontakt
2. **Narx** — baza + km tarif, haydovchi qo‘lda narx, komissiya %
3. **Admin** — ochiq/faol/tugagan, bekor, statistika, haydovchi blok/oflayn
4. **Baho** (1–5) va haydovchi onlayn/oflayn

## 1) Token

1. [@BotFather](https://t.me/BotFather) → `/newbot`
2. Tokenni saqlang — bu `VOSITACHI_BOT_TOKEN`
3. Baraka Market `BOT_TOKEN`idan **boshqa** bo‘lishi shart

## 2) Lokal ishga tushirish

```bash
# repo ildizida
cp vositachi/.env.example vositachi/.env
# vositachi/.env:
#   VOSITACHI_BOT_TOKEN=123456:ABC...
#   VOSITACHI_ADMIN_IDS=sizning_telegram_id

pip install -r requirements.txt
python -m vositachi
```

Telegram ID: `@userinfobot` yoki botga `/start` qilib logdan ko‘ring.

Root `.env` ga ham yozish mumkin (bir xil kalitlar).

## 3) Admin buyruqlar

| Buyruq | Ma’nosi |
|--------|---------|
| `/stats` | Statistika |
| `/open` | Ochiq so‘rovlar |
| `/tariff` | Joriy tarif |
| `/set_base 8000` | Baza narx |
| `/set_km 2000` | 1 km narxi |
| `/set_commission 10` | Komissiya % |
| `/set_default_km 5` | Lokatsiyasiz taxminiy km |

## 4) Oqim (qisqa)

- **Mijoz**: rol → Safar so‘rash → qayerdan/qayerga → telefon → kutish → bog‘lanish → baho
- **Haydovchi**: Onlayn → so‘rov qabul → (ixtiyoriy) narx → Yo‘lda → Tugadi → baho
- **Admin**: tarif, ro‘yxatlar, bekor, haydovchilar

## Env

| Key | Majburiy | Izoh |
|-----|----------|------|
| `VOSITACHI_BOT_TOKEN` | ha | BotFather token |
| `VOSITACHI_ADMIN_IDS` | ha | vergul bilan ID lar |
| `VOSITACHI_BOT_NAME` | yo‘q | default: Vositachi |
| `VOSITACHI_DB` | yo‘q | default: `data/vositachi.db` |

Sirlar inventar qilinmaydi — faqat `.env.example` namunasi.
