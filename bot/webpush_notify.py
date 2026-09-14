"""Web Push for Baraka Admin PWA — free browser notifications."""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
from pathlib import Path

from bot.config import DATABASE_PATH

logger = logging.getLogger(__name__)

_VAPID_CACHE: tuple[str, str, str] | None = None


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _generate_vapid_keypair() -> tuple[str, str]:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ec

    private_key = ec.generate_private_key(ec.SECP256R1())
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("ascii")
    public_raw = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint,
    )
    return _b64url(public_raw), private_pem


def get_vapid_keys() -> tuple[str, str, str]:
    """Return (public_key, private_key, subject). Auto-persist if env missing."""
    global _VAPID_CACHE
    if _VAPID_CACHE is not None:
        return _VAPID_CACHE

    subject = (
        os.getenv("VAPID_SUBJECT", "mailto:admin@localhost").strip()
        or "mailto:admin@localhost"
    )
    public = os.getenv("VAPID_PUBLIC_KEY", "").strip()
    private = os.getenv("VAPID_PRIVATE_KEY", "").strip()
    if public and private:
        _VAPID_CACHE = (public, private, subject)
        return _VAPID_CACHE

    path = Path(DATABASE_PATH).parent / "vapid.json"
    try:
        if path.is_file():
            data = json.loads(path.read_text(encoding="utf-8"))
            pub = str(data.get("publicKey") or data.get("public_key") or "").strip()
            priv = str(
                data.get("privateKey") or data.get("private_key") or ""
            ).strip()
            sub = str(data.get("subject") or subject).strip() or subject
            if pub and priv:
                _VAPID_CACHE = (pub, priv, sub)
                return _VAPID_CACHE
    except Exception as exc:
        logger.warning("vapid.json o'qib bo'lmadi: %s", exc)

    public, private = _generate_vapid_keypair()
    payload = {
        "publicKey": public,
        "privateKey": private,
        "subject": subject,
    }
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info("VAPID kalitlar yaratildi: %s", path)
    except Exception as exc:
        logger.warning("vapid.json yozib bo'lmadi: %s", exc)

    _VAPID_CACHE = (public, private, subject)
    return _VAPID_CACHE


def _send_one(
    *,
    endpoint: str,
    p256dh: str,
    auth: str,
    payload: str,
    private_key: str,
    subject: str,
) -> int | None:
    """Sync webpush; returns HTTP status to delete on, or None."""
    from pywebpush import WebPushException, webpush

    try:
        webpush(
            subscription_info={
                "endpoint": endpoint,
                "keys": {"p256dh": p256dh, "auth": auth},
            },
            data=payload,
            vapid_private_key=private_key,
            vapid_claims={"sub": subject},
        )
        return None
    except WebPushException as exc:
        status = None
        if exc.response is not None:
            try:
                status = int(exc.response.status_code)
            except Exception:
                status = None
        if status in (404, 410):
            return status
        logger.warning("WebPush xato endpoint=%s: %s", endpoint[:80], exc)
        return None
    except Exception as exc:
        logger.warning("WebPush umumiy xato: %s", exc)
        return None


async def send_admin_push(
    title: str, body: str, url: str = "/admin/"
) -> None:
    """Notify all admin push subscriptions. Never raises."""
    try:
        from bot.database import delete_push_subscription, list_push_subscriptions

        public, private, subject = get_vapid_keys()
        _ = public  # public used by clients; private for send
        rows = list_push_subscriptions()
        if not rows:
            logger.info("send_admin_push: subscription yo'q")
            return
        payload = json.dumps(
            {"title": title, "body": body, "url": url or "/admin/"},
            ensure_ascii=False,
        )
        sent = 0
        for row in rows:
            endpoint = str(row["endpoint"])
            status = await asyncio.to_thread(
                _send_one,
                endpoint=endpoint,
                p256dh=str(row["p256dh"]),
                auth=str(row["auth"]),
                payload=payload,
                private_key=private,
                subject=subject,
            )
            if status in (404, 410):
                try:
                    delete_push_subscription(endpoint)
                    logger.info("Eskirgan push subscription o'chirildi")
                except Exception as exc:
                    logger.warning("Subscription o'chirish xato: %s", exc)
            elif status is None:
                sent += 1
        logger.info("send_admin_push: %s/%s yuborildi — %s", sent, len(rows), title)
    except Exception as exc:
        logger.warning("send_admin_push: %s", exc)
