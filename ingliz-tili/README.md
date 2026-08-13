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

## 12 zamon

Filtr: **12 zamon** — har birida formula, signal so‘zlar va 7 ko‘nikma:

1. Present Simple  
2. Present Continuous  
3. Present Perfect  
4. Present Perfect Continuous  
5. Past Simple  
6. Past Continuous  
7. Past Perfect  
8. Past Perfect Continuous  
9. Future Simple (+ going to)  
10. Future Continuous  
11. Future Perfect  
12. Future Perfect Continuous  

## O‘yinlar

- Juftlash (EN↔UZ)
- Harflar (scramble)
- Xotira
- Chaqmoq (60s)

XP, streak va dars progress `localStorage` da saqlanadi.
