# Ingliz

Ingliz tilini o‘rganish PWA — so‘zlar, gaplar, talaffuz va testlar (`/ingliz/`).

## Online

Deploy dan keyin:

`https://<host>/ingliz/`

## Lokal

```bash
cd ingliz-tili
npm install
npm run dev
```

Production build (bot uchun `ingliz/` papkasiga):

```bash
npm run build
rm -rf ../ingliz && cp -R dist ../ingliz
```

## Imkoniyatlar

- 8 ta dars (salomlashish → present simple)
- So‘z / gap kartochkalari + audio (Speech Synthesis)
- Har darsda quiz
- Progress `localStorage` da
- Offline PWA
