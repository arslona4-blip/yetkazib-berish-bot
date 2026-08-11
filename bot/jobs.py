"""PTB job_queue — kunlik hisobot, kam qoldiq, takroriy buyurtmalar."""

from __future__ import annotations

import logging
from datetime import time, timedelta

from telegram.ext import Application, ContextTypes

from bot.config import ADMIN_IDS, DAILY_REPORT_HOUR, LOW_STOCK_THRESHOLD
from bot.database import (
    get_daily_report,
    get_due_recurring_orders,
    get_low_stock_products,
    mark_recurring_run,
    refill_cart_from_order,
)
from bot.i18n import get_user_lang, t
from bot.timeutil import TZ, now_tashkent

logger = logging.getLogger(__name__)


async def daily_admin_report(context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        report = get_daily_report()
        lines = [
            t("daily_report_title", "uz", date=report["date"]),
            "",
            f"📦 Buyurtmalar: {report['orders_count']} ta",
            f"💰 Jami: {report['orders_sum']:,} so'm",
            f"✅ To'langan: {report['paid_count']} — {report['paid_sum']:,}",
            f"⏳ Kutilmoqda: {report['waiting_count']} — {report['waiting_sum']:,}",
            "",
            "🏆 Top:",
        ]
        if report["top"]:
            for row in report["top"]:
                lines.append(f"• {row['product_name']} — {row['qty']} dona")
        else:
            lines.append("• Hali yo'q")
        text = "\n".join(lines)
        for admin_id in ADMIN_IDS:
            try:
                await context.bot.send_message(admin_id, text)
            except Exception as exc:
                logger.warning("Daily report admin=%s: %s", admin_id, exc)
    except Exception:
        logger.exception("daily_admin_report failed")


async def low_stock_check(context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        products = get_low_stock_products(LOW_STOCK_THRESHOLD)
        if not products:
            return
        items = "\n".join(
            f"• {p['name']} — {p['stock']} dona" for p in products[:20]
        )
        text = t("low_stock_alert", "uz", items=items)
        for admin_id in ADMIN_IDS:
            try:
                await context.bot.send_message(admin_id, text)
            except Exception as exc:
                logger.warning("Low stock admin=%s: %s", admin_id, exc)
    except Exception:
        logger.exception("low_stock_check failed")


async def recurring_orders_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        due = get_due_recurring_orders()
        for row in due:
            try:
                user_id = int(row["user_id"])
                source_id = int(row["source_order_id"] or 0)
                days = max(1, int(row["interval_days"] or 7))
                added = 0
                if source_id:
                    added = refill_cart_from_order(user_id, source_id)
                lang = get_user_lang(user_id)
                msg = t("recurring_due", lang)
                if added:
                    msg += f"\n🛒 {added} ta mahsulot savatchada"
                try:
                    await context.bot.send_message(user_id, msg)
                except Exception as exc:
                    logger.warning("Recurring notify user=%s: %s", user_id, exc)
                next_run = (now_tashkent() + timedelta(days=days)).isoformat()
                mark_recurring_run(int(row["id"]), next_run)
            except Exception:
                logger.exception("Recurring row failed id=%s", row["id"])
    except Exception:
        logger.exception("recurring_orders_job failed")


def setup_jobs(application: Application) -> None:
    jq = application.job_queue
    if jq is None:
        logger.warning("job_queue mavjud emas — scheduled jobs o'chirilgan")
        return

    report_time = time(hour=int(DAILY_REPORT_HOUR) % 24, minute=0, tzinfo=TZ)
    jq.run_daily(daily_admin_report, time=report_time, name="daily_admin_report")
    jq.run_repeating(
        low_stock_check,
        interval=3600,
        first=90,
        name="low_stock_check",
    )
    jq.run_repeating(
        recurring_orders_job,
        interval=1800,
        first=120,
        name="recurring_orders",
    )
    logger.info(
        "Jobs registered: daily@%s, low_stock=60m, recurring=30m",
        report_time.strftime("%H:%M"),
    )
