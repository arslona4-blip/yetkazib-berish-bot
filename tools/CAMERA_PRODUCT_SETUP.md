# Baraka Market — kamera orqali mahsulot

Foto → AI (yoki demo) → admin tasdiqi → `products` jadvali.

## Telegram

1. `ADMIN_IDS` ichidagi akkauntdan botga `/foto_mahsulot` yoki Admin → Mahsulotlar → **📷 Foto bilan qo‘shish**.
2. Mahsulot rasmini yuboring.
3. Nom / narx / toifani tekshiring → **✅ Bazaga yozish**.

## Admin PWA (`/admin/`)

1. Mahsulotlar → **📷 Foto / kamera**.
2. AI/demo maydonlarni to‘ldiradi.
3. Forma orqali tahrirlab **Saqlash**.

## Env

| O‘zgaruvchi | Majburiy | Izoh |
|-------------|----------|------|
| `OPENAI_API_KEY` | yo‘q | Bo‘sh → demo/mock draft |
| `OPENAI_BASE_URL` | yo‘q | default OpenAI |
| `OPENAI_MODEL` | yo‘q | `gpt-4o-mini` |
| `OPENAI_VISION_MODEL` | yo‘q | bo‘sh → `OPENAI_MODEL` |

Kalitlarni commit qilmang — faqat `.env` / hosting secrets.

## Kod

- `bot/product_vision.py` — provider interfeys (OpenAI + mock)
- `bot/camera_intake.py` — Telegram conversation
- `POST /api/admin/products/from-photo` — web draft
- Saqlash: mavjud `create_product` / `POST /api/admin/products`
