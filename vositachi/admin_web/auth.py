"""Oddiy parol + sessiya autentifikatsiyasi."""

from __future__ import annotations

import os
import secrets

from fastapi import Request
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

SESSION_KEY = "vositachi_admin_ok"


def admin_password() -> str:
    return os.getenv("VOSITACHI_ADMIN_PASSWORD", "").strip()


def session_secret() -> str:
    secret = os.getenv("VOSITACHI_ADMIN_SESSION_SECRET", "").strip()
    if secret:
        return secret
    # Dev fallback — productionda VOSITACHI_ADMIN_SESSION_SECRET qo‘ying
    return os.getenv("VOSITACHI_ADMIN_PASSWORD", "") or secrets.token_hex(32)


def is_logged_in(request: Request) -> bool:
    return bool(request.session.get(SESSION_KEY))


def login_user(request: Request) -> None:
    request.session[SESSION_KEY] = True


def logout_user(request: Request) -> None:
    request.session.clear()


def check_password(password: str) -> bool:
    expected = admin_password()
    if not expected:
        return False
    return secrets.compare_digest(password, expected)


def require_login(request: Request) -> RedirectResponse | None:
    if is_logged_in(request):
        return None
    return RedirectResponse(url="/login", status_code=303)


def add_session_middleware(app) -> None:
    app.add_middleware(
        SessionMiddleware,
        secret_key=session_secret(),
        session_cookie="vositachi_admin_session",
        same_site="lax",
        https_only=False,
        max_age=60 * 60 * 12,
    )
