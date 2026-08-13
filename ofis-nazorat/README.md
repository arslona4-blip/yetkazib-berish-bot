# Ofis nazorat (PC kamera)

Botga aloqasi yo‘q. Ofisga kim kirgan / kim chiqqanini PC webcam orqali yozadi.

## Ishga tushirish (ofis kompyuterida)

```bash
cd ofis-nazorat
npm install
npm run dev
```

Brauzerda ochiladi (odatda `http://localhost:5173`). Kameraga **ruxsat** bering.

## Qanday ishlatiladi

1. **Kamerani yoqish** — doimiy ishlaydi (sahifa ochiq turgancha)
2. Ism yozing → **Yuzni saqlash** (har bir xodim uchun)
3. Eshik oldida kamera oldidan o‘tsa — avtomatik **KIRISH** / **CHIQISH**
4. Bir xodim uchun 45 soniya kutish (qayta-qayta yozilmasin)
5. Bugungi jurnalni **CSV** qilib saqlash mumkin

Ma’lumotlar faqat shu PC brauzerida (`localStorage`) saqlanadi.
