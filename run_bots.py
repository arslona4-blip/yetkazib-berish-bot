"""Baraka Market (yetkazib berish) boti + ixtiyoriy Vositachi.

Railway/Docker: CMD python -m run_bots
AI Sotuvchi (Annur) o‘chirilgan — ishga tushmaydi.
Vositachi: VOSITACHI_BOT_TOKEN bo‘lsa parallel ishga tushadi.
"""

from __future__ import annotations

import logging
import os
import signal
import subprocess
import sys
import time

from dotenv import load_dotenv

load_dotenv()

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
    logger.info("AI Sotuvchi (@ai_sotuvchi_annur_bot) o‘chirilgan.")

    vositachi_token = os.getenv("VOSITACHI_BOT_TOKEN", "").strip()
    if vositachi_token:
        _start([py, "-m", "vositachi"], "Vositachi")
    else:
        logger.info("Vositachi o‘chirilgan (VOSITACHI_BOT_TOKEN yo‘q).")

    # Asosiy jarayon yiqilsa — hammasi to‘xtaydi
    while True:
        code = baraka.poll()
        if code is not None:
            logger.error("Baraka Market chiqdi: code=%s", code)
            _shutdown()
        for proc in _children[1:]:
            child_code = proc.poll()
            if child_code is not None:
                logger.error("Qo‘shimcha bot chiqdi: code=%s", child_code)
                _shutdown()
        time.sleep(2)


if __name__ == "__main__":
    main()
