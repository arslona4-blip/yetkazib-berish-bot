"""Baraka Market + (ixtiyoriy) AI Sotuvchi birga.

Railway/Docker: CMD python -m run_bots
AI Sotuvchi faqat AI_SOTUVCHI_BOT_TOKEN bo‘lsa ishga tushadi.
"""

from __future__ import annotations

import logging
import os
import signal
import subprocess
import sys
import time

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("run_bots")

_children: list[subprocess.Popen] = []


def _start(cmd: list[str], name: str) -> subprocess.Popen:
    logger.info("Start: %s → %s", name, " ".join(cmd))
    proc = subprocess.Popen(cmd)  # noqa: S603
    _children.append(proc)
    return proc


def _shutdown(*_args: object) -> None:
    logger.info("To‘xtatilmoqda...")
    for proc in _children:
        if proc.poll() is None:
            proc.terminate()
    deadline = time.time() + 8
    for proc in _children:
        remaining = max(0.1, deadline - time.time())
        try:
            proc.wait(timeout=remaining)
        except subprocess.TimeoutExpired:
            proc.kill()
    sys.exit(0)


def main() -> None:
    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)

    py = sys.executable
    baraka = _start([py, "-m", "bot.main"], "Baraka Market")

    ai_token = os.getenv("AI_SOTUVCHI_BOT_TOKEN", "").strip()
    ai_proc: subprocess.Popen | None = None
    if ai_token:
        # Baraka BOT_TOKEN bilan bir xil bo‘lmasin
        main_token = os.getenv("BOT_TOKEN", "").strip()
        if main_token and ai_token == main_token:
            logger.error(
                "AI_SOTUVCHI_BOT_TOKEN va BOT_TOKEN bir xil — "
                "AI Sotuvchi o‘tkazib yuborildi. BotFather’dan yangi bot oling."
            )
        else:
            ai_proc = _start([py, "-m", "ai_sotuvchi"], "AI Sotuvchi")
    else:
        logger.info(
            "AI_SOTUVCHI_BOT_TOKEN yo‘q — faqat Baraka Market ishlaydi. "
            "AI uchun Railway Variables ga token qo‘ying."
        )

    # Asosiy jarayon yiqilsa — hammasi to‘xtaydi
    while True:
        code = baraka.poll()
        if code is not None:
            logger.error("Baraka Market chiqdi: code=%s", code)
            _shutdown()
        if ai_proc is not None:
            ai_code = ai_proc.poll()
            if ai_code is not None:
                logger.error("AI Sotuvchi chiqdi: code=%s — qayta start", ai_code)
                ai_proc = _start([py, "-m", "ai_sotuvchi"], "AI Sotuvchi")
        time.sleep(2)


if __name__ == "__main__":
    main()
