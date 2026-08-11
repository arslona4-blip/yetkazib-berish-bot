# Mening Shajaram

Oila shajarasi PWA — telefonda ochiladi, uy ekraniga o‘rnatiladi.

## Online (Railway)

Deploy qilingandan keyin:

https://worker-production-1646.up.railway.app/shajara/

## Ishga tushirish (local)

```bash
cd mening-shajaram
npm install
npm run dev
```

Production build (Railway uchun `shajara/` papkasiga):

```bash
npm run build
rm -rf ../shajara && cp -R dist ../shajara
```

## MVP imkoniyatlar

- Shajara boshlash (markaziy shaxs)
- A’zo qo‘shish / tahrirlash / o‘chirish
- Ota, ona, turmush o‘rtog‘i bog‘lash
- Daraxt ko‘rinishi (ota-ona / markaz / farzandlar)
- Ma’lumotlar `localStorage` da (qurilmada)
- **Ulashish kodi** (bulut) + havola `?code=`
- **JSON zaxira** yuklab olish / tiklash

## Keyingi bosqich

- Akkaunt + doimiy bulut sinxron
- Export (PDF / rasm)
- Rasmlarni ham ulashish
