# Ofis nazorat (PC kamera)

Botga aloqasi yo‘q. Ofisga kim kirgan / kim chiqqanini PC webcam orqali yozadi.

## Eng oson (tavsiya)

1. **`OfisNazorat.exe`** ni yuklab oling
2. Ikki marta bosing
3. Kamerani yoqing → xodim yuzini saqlang

Node.js va brauzer kerak emas.

GitHub Actions: repo → **Actions** → **Ofis Nazorat Windows exe** → oxirgi run → **Artifacts** → `OfisNazorat-Windows`

Yoki o‘zingiz yig‘ish:
```bash
cd ofis-nazorat
npm install
npm run dist:win
```
Natija: `ofis-nazorat/release/OfisNazorat.exe`

## Qanday ishlatiladi
1. Kamerani yoqish (doimiy ishlaydi)
2. Ism → Yuzni saqlash
3. Eshik oldidan o‘tsa — avtomatik KIRISH / CHIQISH
4. Jurnalni CSV qilib saqlash mumkin

Ma’lumotlar faqat shu PC da saqlanadi.
