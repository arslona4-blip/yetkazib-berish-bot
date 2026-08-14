FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bot ./bot
COPY ai_sotuvchi ./ai_sotuvchi
COPY run_bots.py ./run_bots.py
COPY miniapp ./miniapp
COPY shajara ./shajara
COPY admin ./admin
COPY arduino ./arduino
COPY jadval ./jadval
COPY kichkintoy ./kichkintoy
COPY slayd ./slayd

RUN mkdir -p /data

ENV PYTHONUNBUFFERED=1
ENV DATABASE_PATH=/data/bot.db
ENV AI_SOTUVCHI_DB=/data/ai_sotuvchi.db
ENV WEBAPP_PORT=8088

# Baraka + (token bo‘lsa) AI Sotuvchi
CMD ["python", "-m", "run_bots"]
