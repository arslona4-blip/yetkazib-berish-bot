# Ofis nazorat (PC kamera)

Botga aloqasi yo‘q. Ofisga kim kirgan / kim chiqqanini PC webcam orqali yozadi.

## Brauzersiz (tavsiya)

### Windows
1. `ofis-nazorat` papkasini oching
2. **`start-desktop.bat`** ni ikki marta bosing
3. Birinchi marta `npm install` bo‘lishi mumkin — kuting
4. Oyna ochiladi (Chrome/Edge kerak emas)

### Terminal orqali
```bash
cd ofis-nazorat
npm install
npm run desktop
```

## Brauzerda (ixtiyoriy)
```bash
npm run dev
```
`http://localhost:5177`

## Qanday ishlatiladi
1. **Kamerani yoqish**
2. Ism → **Yuzni saqlash**
3. Eshik oldidan o‘tsa — avtomatik KIRISH / CHIQISH
4. Jurnalni **CSV** qilib saqlash mumkin

Ma’lumotlar faqat shu PC da saqlanadi.
