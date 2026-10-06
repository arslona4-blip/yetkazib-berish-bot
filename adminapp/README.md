# Admin PWA

Professional admin panel for the delivery bot (`/admin/`).

```bash
npm install
npm run dev     # proxy /api -> :8088
npm run build   # then copy dist/ -> ../admin/
```

Auth: Telegram WebApp `initData` (ADMIN_IDS) or `ADMIN_APP_PIN` + Admin ID.

## Kamera / foto → mahsulot

1. Env: `OPENAI_API_KEY` (ixtiyoriy `OPENAI_VISION_MODEL`, `OPENAI_BASE_URL`).
2. Mahsulotlar → **📷 Foto / kamera** → rasm tanlang.
3. AI forma maydonlarini to‘ldiradi → tekshiring → **Saqlash** (`POST /api/admin/products`).
4. Kalit yo‘q bo‘lsa: **AI kalit kerak**.

Telegram: Admin → Mahsulotlar → **📷 Foto bilan qo‘shish** yoki `/foto_mahsulot`.
