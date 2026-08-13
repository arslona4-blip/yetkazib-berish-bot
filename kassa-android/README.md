# Do'kon Kassa (Android)

Mavjud Admin kassani Android ilova qilib o‘raydi. **Onlayn to‘lov yo‘q** — faqat **naqd**.

## Nima ochiladi

`/admin/?mode=kassa` — kassa, tovar, ombor. Karta/qarz menyulari yashirilgan.

## APK olish

GitHub Actions (`Kassa Android APK`) ishlagandan keyin:

1. Repo → **Actions** → **Kassa Android APK**
2. Oxirgi run → **Artifacts** → `kassa-android-apk`
3. Telefonga o‘rnatish (noma’lum manbalarga ruxsat)

## Lokal (Android Studio)

```bash
cd kassa-android
npm install
npx cap add android   # birinchi marta
npx cap sync android
npx cap open android
```

Android Studio da **Build → Build APK(s)**.

## Server manzili

`capacitor.config.json` ichidagi `server.url` ni o‘z Railway `/admin/?mode=kassa` manzilingizga qo‘ying.
