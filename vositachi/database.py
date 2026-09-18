from __future__ import annotations

import math
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Iterator

from vositachi.config import DATABASE_PATH

STATUS_OPEN = "open"
STATUS_ACCEPTED = "accepted"
STATUS_IN_PROGRESS = "in_progress"
STATUS_DONE = "done"
STATUS_CANCELLED = "cancelled"

DEFAULT_SETTINGS = {
    "base_fare": "8000",
    "per_km": "2000",
    "commission_pct": "10",
    "default_estimate_km": "5",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                phone TEXT,
                role TEXT,
                driver_online INTEGER NOT NULL DEFAULT 0,
                driver_blocked INTEGER NOT NULL DEFAULT 0,
                rating_sum REAL NOT NULL DEFAULT 0,
                rating_count INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS rides (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                driver_id INTEGER,
                pickup TEXT NOT NULL,
                pickup_lat REAL,
                pickup_lon REAL,
                destination TEXT NOT NULL,
                dest_lat REAL,
                dest_lon REAL,
                phone TEXT,
                distance_km REAL,
                estimated_price INTEGER,
                agreed_price INTEGER,
                commission_pct REAL,
                commission_amount INTEGER,
                status TEXT NOT NULL DEFAULT 'open',
                customer_rating INTEGER,
                driver_rating INTEGER,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (customer_id) REFERENCES users(user_id),
                FOREIGN KEY (driver_id) REFERENCES users(user_id)
            );

            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_rides_status ON rides(status);
            CREATE INDEX IF NOT EXISTS idx_rides_customer ON rides(customer_id);
            CREATE INDEX IF NOT EXISTS idx_rides_driver ON rides(driver_id);
            CREATE INDEX IF NOT EXISTS idx_users_role_online
                ON users(role, driver_online);
            """
        )
        for key, value in DEFAULT_SETTINGS.items():
            conn.execute(
                """
                INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)
                """,
                (key, value),
            )


def get_setting(key: str, default: str = "") -> str:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT value FROM settings WHERE key = ?", (key,)
        ).fetchone()
    if row:
        return str(row["value"])
    return DEFAULT_SETTINGS.get(key, default)


def set_setting(key: str, value: str) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO settings (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (key, str(value)),
        )


def get_tariff() -> dict[str, float]:
    return {
        "base_fare": float(get_setting("base_fare", "8000")),
        "per_km": float(get_setting("per_km", "2000")),
        "commission_pct": float(get_setting("commission_pct", "10")),
        "default_estimate_km": float(get_setting("default_estimate_km", "5")),
    }


def haversine_km(
    lat1: float, lon1: float, lat2: float, lon2: float
) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    )
    return 2 * r * math.asin(math.sqrt(a))


def estimate_price(distance_km: float | None = None) -> tuple[float, int]:
    """Return (km_used, estimated_price_som)."""
    tariff = get_tariff()
    km = distance_km if distance_km and distance_km > 0 else tariff["default_estimate_km"]
    price = int(round(tariff["base_fare"] + tariff["per_km"] * km))
    return km, price


def commission_for(price: int) -> tuple[float, int]:
    pct = get_tariff()["commission_pct"]
    amount = int(round(price * pct / 100.0))
    return pct, amount


def upsert_user(
    user_id: int,
    full_name: str,
    username: str | None = None,
) -> None:
    now = _now_iso()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO users (
                user_id, username, full_name, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                full_name = excluded.full_name,
                updated_at = excluded.updated_at
            """,
            (user_id, username, full_name, now, now),
        )


def set_role(user_id: int, role: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE users SET role = ?, updated_at = ? WHERE user_id = ?",
            (role, _now_iso(), user_id),
        )


def set_phone(user_id: int, phone: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE users SET phone = ?, updated_at = ? WHERE user_id = ?",
            (phone.strip(), _now_iso(), user_id),
        )


def set_driver_online(user_id: int, online: bool) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE users
            SET driver_online = ?, updated_at = ?
            WHERE user_id = ?
            """,
            (1 if online else 0, _now_iso(), user_id),
        )


def set_driver_blocked(user_id: int, blocked: bool) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE users
            SET driver_blocked = ?, driver_online = CASE
                WHEN ? THEN 0 ELSE driver_online END,
                updated_at = ?
            WHERE user_id = ?
            """,
            (1 if blocked else 0, 1 if blocked else 0, _now_iso(), user_id),
        )


def get_user(user_id: int) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()
    return dict(row) if row else None


def list_drivers(limit: int = 50) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM users
            WHERE role = 'driver'
            ORDER BY driver_online DESC, full_name ASC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


def list_online_drivers(*, exclude_id: int | None = None) -> list[dict[str, Any]]:
    with get_connection() as conn:
        if exclude_id is not None:
            rows = conn.execute(
                """
                SELECT * FROM users
                WHERE role = 'driver' AND driver_online = 1
                  AND driver_blocked = 0 AND user_id != ?
                """,
                (exclude_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT * FROM users
                WHERE role = 'driver' AND driver_online = 1
                  AND driver_blocked = 0
                """
            ).fetchall()
    return [dict(r) for r in rows]


def create_ride(
    *,
    customer_id: int,
    pickup: str,
    destination: str,
    phone: str = "",
    pickup_lat: float | None = None,
    pickup_lon: float | None = None,
    dest_lat: float | None = None,
    dest_lon: float | None = None,
) -> dict[str, Any]:
    distance_km: float | None = None
    if (
        pickup_lat is not None
        and pickup_lon is not None
        and dest_lat is not None
        and dest_lon is not None
    ):
        distance_km = round(
            haversine_km(pickup_lat, pickup_lon, dest_lat, dest_lon), 2
        )
    km_used, estimated = estimate_price(distance_km)
    if distance_km is None:
        distance_km = km_used
    pct, commission = commission_for(estimated)
    now = _now_iso()
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO rides (
                customer_id, pickup, pickup_lat, pickup_lon,
                destination, dest_lat, dest_lon, phone,
                distance_km, estimated_price, agreed_price,
                commission_pct, commission_amount,
                status, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, ?, ?, ?, ?)
            """,
            (
                customer_id,
                pickup.strip(),
                pickup_lat,
                pickup_lon,
                destination.strip(),
                dest_lat,
                dest_lon,
                (phone or "").strip(),
                distance_km,
                estimated,
                pct,
                commission,
                STATUS_OPEN,
                now,
                now,
            ),
        )
        ride_id = int(cur.lastrowid)
    ride = get_ride(ride_id)
    assert ride is not None
    return ride


def get_ride(ride_id: int) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM rides WHERE id = ?", (ride_id,)
        ).fetchone()
    return dict(row) if row else None


def list_rides_by_status(
    statuses: tuple[str, ...] | list[str],
    limit: int = 30,
) -> list[dict[str, Any]]:
    if not statuses:
        return []
    placeholders = ",".join("?" * len(statuses))
    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT * FROM rides
            WHERE status IN ({placeholders})
            ORDER BY id DESC
            LIMIT ?
            """,
            (*statuses, limit),
        ).fetchall()
    return [dict(r) for r in rows]


def list_open_rides(limit: int = 20) -> list[dict[str, Any]]:
    return list_rides_by_status((STATUS_OPEN,), limit)


def list_user_rides(user_id: int, limit: int = 10) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM rides
            WHERE customer_id = ? OR driver_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (user_id, user_id, limit),
        ).fetchall()
    return [dict(r) for r in rows]


def get_driver_active_ride(driver_id: int) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT * FROM rides
            WHERE driver_id = ? AND status IN (?, ?)
            ORDER BY id DESC
            LIMIT 1
            """,
            (driver_id, STATUS_ACCEPTED, STATUS_IN_PROGRESS),
        ).fetchone()
    return dict(row) if row else None


def accept_ride(ride_id: int, driver_id: int) -> dict[str, Any] | None:
    now = _now_iso()
    with get_connection() as conn:
        cur = conn.execute(
            """
            UPDATE rides
            SET driver_id = ?, status = ?,
                agreed_price = COALESCE(agreed_price, estimated_price),
                updated_at = ?
            WHERE id = ? AND status = ?
            """,
            (driver_id, STATUS_ACCEPTED, now, ride_id, STATUS_OPEN),
        )
        if cur.rowcount != 1:
            return None
        row = conn.execute(
            "SELECT * FROM rides WHERE id = ?", (ride_id,)
        ).fetchone()
        if row:
            price = int(row["agreed_price"] or row["estimated_price"] or 0)
            pct = float(row["commission_pct"] or 0)
            conn.execute(
                "UPDATE rides SET commission_amount = ? WHERE id = ?",
                (int(round(price * pct / 100.0)), ride_id),
            )
            row = conn.execute(
                "SELECT * FROM rides WHERE id = ?", (ride_id,)
            ).fetchone()
    return dict(row) if row else None


def set_agreed_price(ride_id: int, driver_id: int, price: int) -> dict[str, Any] | None:
    pct = get_tariff()["commission_pct"]
    commission = int(round(price * pct / 100.0))
    now = _now_iso()
    with get_connection() as conn:
        cur = conn.execute(
            """
            UPDATE rides
            SET agreed_price = ?, commission_pct = ?, commission_amount = ?,
                updated_at = ?
            WHERE id = ? AND driver_id = ?
              AND status IN (?, ?)
            """,
            (
                price,
                pct,
                commission,
                now,
                ride_id,
                driver_id,
                STATUS_ACCEPTED,
                STATUS_IN_PROGRESS,
            ),
        )
        if cur.rowcount != 1:
            return None
        row = conn.execute(
            "SELECT * FROM rides WHERE id = ?", (ride_id,)
        ).fetchone()
    return dict(row) if row else None


def update_ride_status(
    ride_id: int,
    status: str,
    *,
    by_driver_id: int | None = None,
) -> dict[str, Any] | None:
    now = _now_iso()
    with get_connection() as conn:
        if by_driver_id is not None:
            cur = conn.execute(
                """
                UPDATE rides
                SET status = ?, updated_at = ?
                WHERE id = ? AND driver_id = ?
                  AND status IN (?, ?)
                """,
                (
                    status,
                    now,
                    ride_id,
                    by_driver_id,
                    STATUS_ACCEPTED,
                    STATUS_IN_PROGRESS,
                ),
            )
        else:
            cur = conn.execute(
                """
                UPDATE rides
                SET status = ?, updated_at = ?
                WHERE id = ?
                """,
                (status, now, ride_id),
            )
        if cur.rowcount != 1:
            return None
        row = conn.execute(
            "SELECT * FROM rides WHERE id = ?", (ride_id,)
        ).fetchone()
    return dict(row) if row else None


def cancel_ride(
    ride_id: int,
    *,
    by_user_id: int | None = None,
    force: bool = False,
) -> dict[str, Any] | None:
    now = _now_iso()
    with get_connection() as conn:
        if force:
            cur = conn.execute(
                """
                UPDATE rides
                SET status = ?, updated_at = ?
                WHERE id = ? AND status IN (?, ?, ?)
                """,
                (
                    STATUS_CANCELLED,
                    now,
                    ride_id,
                    STATUS_OPEN,
                    STATUS_ACCEPTED,
                    STATUS_IN_PROGRESS,
                ),
            )
        elif by_user_id is not None:
            cur = conn.execute(
                """
                UPDATE rides
                SET status = ?, updated_at = ?
                WHERE id = ?
                  AND status IN (?, ?, ?)
                  AND (customer_id = ? OR driver_id = ?)
                """,
                (
                    STATUS_CANCELLED,
                    now,
                    ride_id,
                    STATUS_OPEN,
                    STATUS_ACCEPTED,
                    STATUS_IN_PROGRESS,
                    by_user_id,
                    by_user_id,
                ),
            )
        else:
            return None
        if cur.rowcount != 1:
            return None
        row = conn.execute(
            "SELECT * FROM rides WHERE id = ?", (ride_id,)
        ).fetchone()
    return dict(row) if row else None


def set_rating(
    ride_id: int,
    *,
    by_customer: bool,
    stars: int,
) -> dict[str, Any] | None:
    stars = max(1, min(5, int(stars)))
    ride = get_ride(ride_id)
    if not ride or ride["status"] != STATUS_DONE:
        return None
    field = "customer_rating" if by_customer else "driver_rating"
    if ride.get(field):
        return None  # already rated
    target_id = ride["driver_id"] if by_customer else ride["customer_id"]
    if not target_id:
        return None
    now = _now_iso()
    with get_connection() as conn:
        conn.execute(
            f"UPDATE rides SET {field} = ?, updated_at = ? WHERE id = ?",
            (stars, now, ride_id),
        )
        conn.execute(
            """
            UPDATE users
            SET rating_sum = rating_sum + ?,
                rating_count = rating_count + 1,
                updated_at = ?
            WHERE user_id = ?
            """,
            (float(stars), now, target_id),
        )
        row = conn.execute(
            "SELECT * FROM rides WHERE id = ?", (ride_id,)
        ).fetchone()
    return dict(row) if row else None


def avg_rating(user: dict[str, Any] | None) -> str:
    if not user:
        return "—"
    count = int(user.get("rating_count") or 0)
    if count <= 0:
        return "baho yo‘q"
    avg = float(user.get("rating_sum") or 0) / count
    return f"{avg:.1f}★ ({count})"


def get_stats() -> dict[str, Any]:
    with get_connection() as conn:
        users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        drivers = conn.execute(
            "SELECT COUNT(*) FROM users WHERE role = 'driver'"
        ).fetchone()[0]
        drivers_online = conn.execute(
            """
            SELECT COUNT(*) FROM users
            WHERE role = 'driver' AND driver_online = 1 AND driver_blocked = 0
            """
        ).fetchone()[0]

        def _count(status: str) -> int:
            return int(
                conn.execute(
                    "SELECT COUNT(*) FROM rides WHERE status = ?",
                    (status,),
                ).fetchone()[0]
            )

        done_sum = conn.execute(
            """
            SELECT COALESCE(SUM(COALESCE(agreed_price, estimated_price)), 0)
            FROM rides WHERE status = ?
            """,
            (STATUS_DONE,),
        ).fetchone()[0]
        commission_sum = conn.execute(
            """
            SELECT COALESCE(SUM(commission_amount), 0)
            FROM rides WHERE status = ?
            """,
            (STATUS_DONE,),
        ).fetchone()[0]

        return {
            "users": int(users),
            "drivers": int(drivers),
            "drivers_online": int(drivers_online),
            "open": _count(STATUS_OPEN),
            "accepted": _count(STATUS_ACCEPTED),
            "in_progress": _count(STATUS_IN_PROGRESS),
            "done": _count(STATUS_DONE),
            "cancelled": _count(STATUS_CANCELLED),
            "done_sum": int(done_sum or 0),
            "commission_sum": int(commission_sum or 0),
        }


def money(som: int | float | None) -> str:
    if som is None:
        return "—"
    return f"{int(som):,}".replace(",", " ") + " so‘m"


def display_name(user: dict[str, Any] | None) -> str:
    if not user:
        return "—"
    name = (user.get("full_name") or "").strip() or "Foydalanuvchi"
    uname = (user.get("username") or "").strip()
    if uname:
        return f"{name} (@{uname})"
    return name


def contact_block(user: dict[str, Any] | None) -> str:
    if not user:
        return "Kontakt: —"
    parts: list[str] = []
    phone = (user.get("phone") or "").strip()
    uname = (user.get("username") or "").strip()
    if phone:
        parts.append(f"📞 {phone}")
    if uname:
        parts.append(f"Telegram: @{uname}")
    else:
        parts.append(f"Telegram ID: {user.get('user_id')}")
    rating = avg_rating(user)
    parts.append(f"⭐ {rating}")
    return "\n".join(parts)


def format_ride_short(ride: dict[str, Any]) -> str:
    price = ride.get("agreed_price") or ride.get("estimated_price")
    return (
        f"#{ride['id']} [{ride['status']}] "
        f"{ride.get('pickup') or '—'} → {ride.get('destination') or '—'} "
        f"| {money(price)}"
    )
