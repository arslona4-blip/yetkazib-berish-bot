# Admin PWA

Professional admin panel for the delivery bot (`/admin/`).

```bash
npm install
npm run dev     # proxy /api -> :8088
npm run build   # then copy dist/ -> ../admin/
```

Auth: Telegram WebApp `initData` (ADMIN_IDS) or `ADMIN_APP_PIN` + Admin ID.

## Foto orqali mahsulot (AI)

1. Bot webapp ishlayotgan bo‘lsin (`WEBAPP_PORT`, default 8088) va `OPENAI_API_KEY` env da bo‘lsin.
2. Admin PWA → **Mahsulotlar** → **📷 Foto / kamera** → rasm (kamera yoki galereya).
3. AI draft maydonlarni to‘ldiradi (`name`, `price`, toifa, birlik, izoh) — tekshirib **Saqlash**.
4. Kalit yo‘q bo‘lsa: aniq xato — `OPENAI_API_KEY sozlanmagan…` (HTTP 503).

Env (repo ildizi `.env.example`):

```
OPENAI_API_KEY=
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
OPENAI_VISION_MODEL=   # ixtiyoriy; bo‘sh → OPENAI_MODEL
```

API: `POST /api/admin/products/from-photo` (multipart `image`) → draft; saqlash `POST /api/admin/products`.
