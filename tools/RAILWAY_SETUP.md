# Railway — 24/7 bot

## Muhim
- Railway ishlaganda kompyuterdagi botni OCHIRING (409 Conflict).
- Startup / watchdog ni ham ochiring.
- SQLite uchun Volume: mount path /data

## Qadamlar
1. Kod GitHubga push (`main` branch)
2. https://railway.app — GitHub bilan kiring
3. New Project → Deploy from GitHub → yetkazib-berish-bot
4. Variables (kamida):
   - `BOT_TOKEN`
   - `ADMIN_IDS` (Telegram ID, vergul bilan)
   - `COURIER_IDS` (ixtiyoriy; bo'sh bo'lsa ADMIN_IDS ishlatiladi)
   - `DATABASE_PATH=/data/bot.db`
   - `SHOP_NAME`, `SHOP_ADDRESS=Saruyz mahallasi`, `SHOP_PHONE`, …
   - `DELIVERY_AREA=Saruyz mahallasi`
   - `DELIVERY_AREA_KEYWORDS=saruyz,saruiz`
   - `DELIVERY_PRICE`, `MINIAPP_URL` (HTTPS)
5. Settings → Volumes → Add → `/data`
6. Deploy → Logs: Application started
7. Telegramda `/start`, keyin `/id` — ID ni ko'ring

## Merge dan keyin qayta deploy
Railway odatda `main` yangilanganda avto-deploy qiladi.
Bo'lmasa: Project → Deployments → Redeploy.

Lokal bot va Railway BIRGA ishlamasin.
