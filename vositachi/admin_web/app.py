"""FastAPI admin panel — bot bilan bir xil SQLite (`DATA_DIR` / `VOSITACHI_DB`)."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from vositachi import config as cfg
from vositachi.admin_web import auth
from vositachi.database import (
    STATUS_ACCEPTED,
    STATUS_CANCELLED,
    STATUS_DONE,
    STATUS_IN_PROGRESS,
    STATUS_OPEN,
    avg_rating,
    cancel_ride,
    display_name,
    get_stats,
    get_tariff,
    get_user,
    init_db,
    list_drivers,
    list_rides_by_status,
    money,
    set_driver_online,
    set_setting,
)

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

STATUS_LABELS = {
    STATUS_OPEN: "Ochiq",
    STATUS_ACCEPTED: "Qabul qilingan",
    STATUS_IN_PROGRESS: "Yo‘lda",
    STATUS_DONE: "Tugagan",
    STATUS_CANCELLED: "Bekor",
}

ACTIVE_STATUSES = (STATUS_ACCEPTED, STATUS_IN_PROGRESS)

app = FastAPI(title="Saryuz Vositachi Admin", docs_url=None, redoc_url=None)
auth.add_session_middleware(app)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def _ctx(request: Request, **extra):
    data = {
        "bot_name": cfg.BOT_NAME,
        "area_label": getattr(cfg, "AREA_LABEL", "Bekobod / Saryuz"),
        "status_labels": STATUS_LABELS,
        "db_path": cfg.DATABASE_PATH,
        "flash": request.session.pop("flash", None),
        "flash_error": request.session.pop("flash_error", None),
    }
    data.update(extra)
    return data


def _flash(request: Request, message: str, *, error: bool = False) -> None:
    key = "flash_error" if error else "flash"
    request.session[key] = message


@app.on_event("startup")
def _startup() -> None:
    init_db()


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    if auth.is_logged_in(request):
        return RedirectResponse("/", status_code=303)
    password_configured = bool(auth.admin_password())
    return templates.TemplateResponse(
        request,
        "login.html",
        _ctx(request, password_configured=password_configured),
    )


@app.post("/login")
async def login_submit(
    request: Request,
    password: str = Form(""),
):
    if not auth.admin_password():
        _flash(
            request,
            "VOSITACHI_ADMIN_PASSWORD env o‘rnatilmagan.",
            error=True,
        )
        return RedirectResponse("/login", status_code=303)
    if auth.check_password(password):
        auth.login_user(request)
        return RedirectResponse("/", status_code=303)
    _flash(request, "Parol noto‘g‘ri.", error=True)
    return RedirectResponse("/login", status_code=303)


@app.post("/logout")
async def logout(request: Request):
    auth.logout_user(request)
    return RedirectResponse("/login", status_code=303)


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    redir = auth.require_login(request)
    if redir:
        return redir
    stats = get_stats()
    stats["active"] = int(stats.get("accepted", 0)) + int(
        stats.get("in_progress", 0)
    )
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        _ctx(request, stats=stats, money=money),
    )


@app.get("/rides", response_class=HTMLResponse)
async def rides_page(
    request: Request,
    status: str = Query("open"),
):
    redir = auth.require_login(request)
    if redir:
        return redir

    status = (status or "open").strip().lower()
    if status == "active":
        statuses = ACTIVE_STATUSES
        current = "active"
    elif status in STATUS_LABELS:
        statuses = (status,)
        current = status
    else:
        statuses = (STATUS_OPEN,)
        current = STATUS_OPEN

    rides = list_rides_by_status(statuses, limit=80)
    enriched = []
    for ride in rides:
        customer = get_user(int(ride["customer_id"])) if ride.get("customer_id") else None
        driver = get_user(int(ride["driver_id"])) if ride.get("driver_id") else None
        enriched.append(
            {
                **ride,
                "customer_name": display_name(customer),
                "driver_name": display_name(driver) if driver else "—",
                "price_label": money(
                    ride.get("agreed_price") or ride.get("estimated_price")
                ),
                "cancellable": ride.get("status")
                in (STATUS_OPEN, STATUS_ACCEPTED, STATUS_IN_PROGRESS),
            }
        )

    tabs = [
        ("open", "Ochiq"),
        ("active", "Faol"),
        ("done", "Tugagan"),
        ("cancelled", "Bekor"),
        ("accepted", "Qabul"),
        ("in_progress", "Yo‘lda"),
    ]
    return templates.TemplateResponse(
        request,
        "rides.html",
        _ctx(
            request,
            rides=enriched,
            current_status=current,
            tabs=tabs,
        ),
    )


@app.post("/rides/{ride_id}/cancel")
async def rides_cancel(request: Request, ride_id: int):
    redir = auth.require_login(request)
    if redir:
        return redir
    result = cancel_ride(ride_id, force=True)
    if result:
        _flash(request, f"Safar #{ride_id} bekor qilindi.")
    else:
        _flash(request, f"Safar #{ride_id} bekor qilinmadi.", error=True)
    referer = request.headers.get("referer") or "/rides"
    return RedirectResponse(referer, status_code=303)


@app.get("/drivers", response_class=HTMLResponse)
async def drivers_page(request: Request):
    redir = auth.require_login(request)
    if redir:
        return redir
    drivers = list_drivers(limit=100)
    rows = []
    for d in drivers:
        rows.append(
            {
                **d,
                "name": display_name(d),
                "online": bool(d.get("driver_online")),
                "blocked": bool(d.get("driver_blocked")),
                "rating": avg_rating(d),
            }
        )
    return templates.TemplateResponse(
        request,
        "drivers.html",
        _ctx(request, drivers=rows),
    )


@app.post("/drivers/{user_id}/offline")
async def drivers_force_offline(request: Request, user_id: int):
    redir = auth.require_login(request)
    if redir:
        return redir
    user = get_user(user_id)
    if not user or user.get("role") != "driver":
        _flash(request, "Haydovchi topilmadi.", error=True)
    else:
        set_driver_online(user_id, False)
        _flash(request, f"Haydovchi {display_name(user)} oflayn qilindi.")
    return RedirectResponse("/drivers", status_code=303)


@app.get("/tariff", response_class=HTMLResponse)
async def tariff_page(request: Request):
    redir = auth.require_login(request)
    if redir:
        return redir
    tariff = get_tariff()
    return templates.TemplateResponse(
        request,
        "tariff.html",
        _ctx(request, tariff=tariff),
    )


@app.post("/tariff")
async def tariff_save(
    request: Request,
    base_fare: str = Form(""),
    per_km: str = Form(""),
    commission_pct: str = Form(""),
    default_estimate_km: str = Form(""),
):
    redir = auth.require_login(request)
    if redir:
        return redir

    try:
        base = float(base_fare.replace(",", ".").strip())
        km_price = float(per_km.replace(",", ".").strip())
        commission = float(commission_pct.replace(",", ".").strip())
        default_km = float(default_estimate_km.replace(",", ".").strip())
        if base < 0 or km_price < 0 or commission < 0 or default_km < 0:
            raise ValueError("negative")
        if commission > 100:
            raise ValueError("commission")
    except ValueError:
        _flash(request, "Noto‘g‘ri qiymatlar. Raqam kiriting.", error=True)
        return RedirectResponse("/tariff", status_code=303)

    set_setting("base_fare", str(int(base) if base == int(base) else base))
    set_setting("per_km", str(int(km_price) if km_price == int(km_price) else km_price))
    set_setting(
        "commission_pct",
        str(int(commission) if commission == int(commission) else commission),
    )
    set_setting(
        "default_estimate_km",
        str(int(default_km) if default_km == int(default_km) else default_km),
    )
    _flash(request, "Tarif saqlandi.")
    return RedirectResponse("/tariff", status_code=303)
