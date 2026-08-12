# Ingliz

Ingliz tilini o‘rganish PWA — 6 ko‘nikma, talaffuz va o‘yinlar (`/ingliz/`).

## Online

`https://<host>/ingliz/`

## Lokal

```bash
cd ingliz-tili
npm install
npm run dev
```

Production:

```bash
npm run build
rm -rf ../ingliz && cp -R dist ../ingliz
```

## Ko‘nikmalar

- **Lug‘at** — so‘z/gap + eshitish
- **Listening** — audio → variant
- **Reading** — matn + savollar
- **Writing** — yozib tekshirish
- **Speaking** — mikrofon (Chrome)
- **Talaffuz** — sekin eshitish + takrorlash
- **Quiz** — bilim testi

## O‘yinlar

- Juftlash (EN↔UZ)
- Harflar (scramble)
- Xotira
- Chaqmoq (60s)

XP, streak va dars progress `localStorage` da saqlanadi.

## Bot

`MINIAPP_URL` sozlangan bo‘lsa:

- `/ingliz` buyrug‘i
- «⋯ Ko‘proq» → 🇬🇧 Ingliz
- `/start` dagi inline tugma
