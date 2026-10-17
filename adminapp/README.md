# Admin PWA

Professional admin panel for the delivery bot (`/admin/`).

```bash
npm install
npm run dev     # proxy /api -> :8088
npm run build   # then copy dist/ -> ../admin/
```

Auth: Telegram WebApp `initData` (ADMIN_IDS) or `ADMIN_APP_PIN` + Admin ID.

## Kamera mahsulot

Mahsulotlar → **📷 Foto / kamera** — rasm yuklash → AI/demo draft → forma tekshiruvi → Saqlash.

Backend: `POST /api/admin/products/from-photo`. Kalit yo‘q bo‘lsa demo maydonlar. Batafsil: `tools/CAMERA_PRODUCT_SETUP.md`.
