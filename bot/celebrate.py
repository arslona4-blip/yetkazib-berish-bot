"""100 000+ so'm buyurtmada mijozni tabriklash (bonus + bayram).

Tashqi Giphy URL ishlatilmaydi — lokal GIF + emoji fallback.
"""

from __future__ import annotations

import io
import logging
import math
import struct
from pathlib import Path
from typing import Any

from telegram import InputFile

from bot.config import BONUS_PERCENT, GIFT_DRINK_THRESHOLD

logger = logging.getLogger(__name__)

ASSETS_DIR = Path(__file__).resolve().parent / "assets"
CELEBRATE_GIF_PATH = ASSETS_DIR / "celebrate.gif"

# Minimal single-frame fallback if hand-built GIF fails
_MINIMAL_GIF_BYTES = bytes(
    [
        0x47, 0x49, 0x46, 0x38, 0x39, 0x61, 0x01, 0x00, 0x01, 0x00, 0x80, 0x00, 0x00,
        0xFF, 0x00, 0x00, 0x00, 0x00, 0x00, 0x21, 0xF9, 0x04, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x2C, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0x02, 0x02,
        0x44, 0x01, 0x00, 0x3B,
    ]
)


def _som(amount: int) -> str:
    return f"{int(amount):,}".replace(",", " ")


def should_celebrate(subtotal: int, total: int | None = None) -> bool:
    """True if subtotal OR total reaches the gift threshold."""
    thr = int(GIFT_DRINK_THRESHOLD)
    if int(subtotal or 0) >= thr:
        return True
    if total is not None and int(total or 0) >= thr:
        return True
    return False


def celebration_bonus_points(order_total: int) -> int:
    return max(1, int(int(order_total or 0) * BONUS_PERCENT / 100))


def celebration_html(*, subtotal: int, total: int) -> str:
    """Mijozga yuboriladigan bayram matni (HTML)."""
    _ = total
    from bot.config import gift_drink_promo_text

    return (
        "🎊 <b>Tabriklaymiz!</b> 🎊\n\n"
        f"Siz <b>{_som(subtotal)} so‘m</b>lik buyurtma berdingiz!\n\n"
        f"{gift_drink_promo_text().replace(chr(10), ' ')}\n\n"
        "🎈🎈🎈 Salyutlar! 🎆"
    )


def _write_minimal_gif(path: Path) -> None:
    """Write a small night-sky fireworks GIF without Pillow."""
    width, height = 96, 72
    n_frames = 12
    sky = (6, 8, 22)
    bursts = [
        # (cx, cy, color, start_frame, max_radius)
        (24, 28, (255, 80, 90), 0, 18),
        (70, 22, (255, 220, 90), 3, 16),
        (48, 36, (90, 200, 255), 6, 20),
        (30, 18, (255, 140, 255), 2, 14),
        (62, 40, (120, 255, 160), 8, 15),
    ]
    frames_rgb = []
    for frame_i in range(n_frames):
        pixels = bytearray()
        for y in range(height):
            for x in range(width):
                r, g, b = sky
                # faint stars
                if ((x * 17 + y * 31) % 47 == 0) and y < height - 8:
                    r, g, b = (40, 48, 70)
                for cx, cy, (cr, cg, cb), start, max_r in bursts:
                    age = frame_i - start
                    if age < 0 or age > 7:
                        continue
                    radius = 2 + int(max_r * (age + 1) / 8)
                    dx = x - cx
                    dy = y - cy
                    dist2 = dx * dx + dy * dy
                    dist = int(math.sqrt(dist2)) if dist2 else 0
                    ring = abs(dist - radius)
                    # expanding ring sparks
                    if ring <= 1 and dist2 > 0:
                        ang = int((math.atan2(dy, dx) + math.pi) * 8 / math.pi) % 16
                        if (ang + age) % 2 == 0 or ring == 0:
                            fade = max(0.35, 1.0 - age * 0.1)
                            r = min(255, int(cr * fade + 40))
                            g = min(255, int(cg * fade + 20))
                            b = min(255, int(cb * fade))
                    # falling trail dots under burst
                    if age >= 3 and dx * dx <= 4:
                        fall_y = cy + radius + (age - 2) * 3 + (x % 5)
                        if abs(y - fall_y) <= 1 and y > cy:
                            r, g, b = (min(255, cr), min(255, cg // 2 + 40), min(255, cb // 2))
                    # bright center flash early
                    if age <= 1 and dist2 <= 6:
                        r, g, b = (255, 255, 240)
                pixels.extend((r, g, b))
        frames_rgb.append(bytes(pixels))

    try:
        path.write_bytes(_build_animated_gif_rgb(frames_rgb, width, height, delay_cs=10))
    except Exception as exc:
        logger.warning("Minimal GIF build xato, 1x1 fallback: %s", exc)
        path.write_bytes(_MINIMAL_GIF_BYTES)


def _build_animated_gif_rgb(
    frames: list[bytes], width: int, height: int, delay_cs: int = 10
) -> bytes:
    """Build a simple animated GIF from raw RGB frames (no Pillow)."""
    # Build global palette from all pixels (max 256)
    palette: list[tuple[int, int, int]] = [(12, 40, 48)]
    index_map: dict[tuple[int, int, int], int] = {(12, 40, 48): 0}

    def idx(rgb: tuple[int, int, int]) -> int:
        if rgb in index_map:
            return index_map[rgb]
        if len(palette) >= 256:
            # nearest
            best_i, best_d = 0, 10**9
            r, g, b = rgb
            for i, (pr, pg, pb) in enumerate(palette):
                d = (r - pr) ** 2 + (g - pg) ** 2 + (b - pb) ** 2
                if d < best_d:
                    best_d, best_i = d, i
            return best_i
        i = len(palette)
        palette.append(rgb)
        index_map[rgb] = i
        return i

    indexed_frames: list[bytes] = []
    for raw in frames:
        out = bytearray()
        for i in range(0, len(raw), 3):
            out.append(idx((raw[i], raw[i + 1], raw[i + 2])))
        indexed_frames.append(bytes(out))

    # pad palette to power of 2
    ncolors = max(2, len(palette))
    bits = max(1, math.ceil(math.log2(ncolors)))
    size_flag = bits - 1
    full = 1 << bits
    while len(palette) < full:
        palette.append((0, 0, 0))

    pal_bytes = bytearray()
    for r, g, b in palette:
        pal_bytes.extend((r, g, b))

    out = bytearray()
    out.extend(b"GIF89a")
    out.extend(struct.pack("<HH", width, height))
    # GCT flag | color resolution | sort | size
    out.append(0x80 | (size_flag << 4) | size_flag)
    out.append(0)  # bg
    out.append(0)  # aspect
    out.extend(pal_bytes)

    # Netscape loop
    out.extend(b"!\xff\x0bNETSCAPE2.0\x03\x01\x00\x00\x00")

    for frame in indexed_frames:
        # Graphic Control Extension
        out.extend(b"!\xf9\x04\x04")  # disposal=1
        out.extend(struct.pack("<H", delay_cs))
        out.append(0)  # transparent index unused
        out.append(0)
        # Image Descriptor
        out.extend(b",")
        out.extend(struct.pack("<HHHH", 0, 0, width, height))
        out.append(0)  # no local palette
        # LZW
        min_code_size = max(2, bits)
        out.append(min_code_size)
        compressed = _lzw_encode(frame, min_code_size)
        for i in range(0, len(compressed), 255):
            chunk = compressed[i : i + 255]
            out.append(len(chunk))
            out.extend(chunk)
        out.append(0)

    out.append(0x3B)  # trailer
    return bytes(out)


def _lzw_encode(indices: bytes, min_code_size: int) -> bytes:
    clear = 1 << min_code_size
    end = clear + 1
    code_size = min_code_size + 1
    next_code = end + 1
    table: dict[bytes, int] = {bytes([i]): i for i in range(clear)}

    bit_buf = 0
    bit_len = 0
    out = bytearray()

    def write_code(code: int) -> None:
        nonlocal bit_buf, bit_len, code_size, next_code, table
        bit_buf |= code << bit_len
        bit_len += code_size
        while bit_len >= 8:
            out.append(bit_buf & 0xFF)
            bit_buf >>= 8
            bit_len -= 8

    write_code(clear)
    w = bytes([indices[0]]) if indices else b""
    for bi in indices[1:]:
        k = bytes([bi])
        wk = w + k
        if wk in table:
            w = wk
            continue
        write_code(table[w])
        if next_code < 4096:
            table[wk] = next_code
            next_code += 1
            if next_code == (1 << code_size) and code_size < 12:
                code_size += 1
        else:
            write_code(clear)
            table = {bytes([i]): i for i in range(clear)}
            code_size = min_code_size + 1
            next_code = end + 1
        w = k
    if w:
        write_code(table[w])
    write_code(end)
    if bit_len:
        out.append(bit_buf & 0xFF)
    return bytes(out)


def _generate_pillow_gif(path: Path) -> bool:
    """Realistic night-sky fireworks / salutes GIF."""
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        logger.warning("Pillow yo'q — minimal GIF ishlatiladi")
        return False

    import random

    width, height = 320, 240
    n_frames = 20
    duration_ms = 110
    sky = (4, 6, 18)
    rng = random.Random(7)

    burst_colors = [
        (255, 70, 85),
        (255, 210, 70),
        (80, 200, 255),
        (255, 120, 255),
        (120, 255, 150),
        (255, 160, 60),
        (255, 255, 255),
    ]

    # Staggered firework launches: explode at (cx,cy) on start_frame
    bursts_spec = [
        (80, 70, 0, burst_colors[0]),
        (220, 55, 3, burst_colors[1]),
        (160, 95, 6, burst_colors[2]),
        (55, 110, 8, burst_colors[3]),
        (265, 100, 11, burst_colors[4]),
        (140, 50, 14, burst_colors[5]),
        (200, 130, 5, burst_colors[6]),
    ]

    def make_burst(cx: float, cy: float, color: tuple[int, int, int], start: int) -> list[dict]:
        sparks = []
        n = rng.randint(36, 52)
        for i in range(n):
            ang = (2 * math.pi * i / n) + rng.uniform(-0.08, 0.08)
            speed = rng.uniform(2.2, 5.8)
            sparks.append(
                {
                    "cx": cx,
                    "cy": cy,
                    "vx": math.cos(ang) * speed,
                    "vy": math.sin(ang) * speed,
                    "color": color,
                    "start": start,
                    "life": rng.uniform(9, 14),
                    "r0": rng.uniform(1.6, 3.2),
                    "trail": rng.random() < 0.55,
                }
            )
        # secondary smaller sparklets
        for _ in range(18):
            ang = rng.uniform(0, 2 * math.pi)
            speed = rng.uniform(1.0, 3.2)
            sparks.append(
                {
                    "cx": cx,
                    "cy": cy,
                    "vx": math.cos(ang) * speed,
                    "vy": math.sin(ang) * speed,
                    "color": (255, 255, 230),
                    "start": start,
                    "life": rng.uniform(5, 9),
                    "r0": rng.uniform(1.0, 1.8),
                    "trail": False,
                }
            )
        return sparks

    sparks: list[dict] = []
    for cx, cy, start, color in bursts_spec:
        sparks.extend(make_burst(float(cx), float(cy), color, start))

    # rising rocket trails before some bursts
    rockets = [
        {"x": 80.0, "y0": height - 8, "cy": 70.0, "start": 0, "color": (255, 220, 160)},
        {"x": 220.0, "y0": height - 8, "cy": 55.0, "start": 3, "color": (255, 240, 180)},
        {"x": 160.0, "y0": height - 8, "cy": 95.0, "start": 6, "color": (200, 230, 255)},
    ]

    # fixed starfield
    stars = [
        (rng.randint(2, width - 3), rng.randint(2, height // 2), rng.randint(90, 180))
        for _ in range(48)
    ]

    frames = []
    gravity = 0.14

    for frame_i in range(n_frames):
        img = Image.new("RGB", (width, height), sky)
        draw = ImageDraw.Draw(img)

        for sx, sy, bright in stars:
            twinkle = bright + (8 if (frame_i + sx) % 5 == 0 else 0)
            c = min(255, twinkle)
            draw.point((sx, sy), fill=(c, c, min(255, c + 30)))

        # rocket ascent (2 frames before burst)
        for rk in rockets:
            age = frame_i - (rk["start"] - 2)
            if 0 <= age < 2:
                t = (age + 1) / 2.0
                y = rk["y0"] + (rk["cy"] - rk["y0"]) * t
                x = rk["x"]
                draw.ellipse((x - 2, y - 2, x + 2, y + 2), fill=rk["color"])
                draw.line((x, y + 3, x, y + 14), fill=(180, 120, 60), width=1)

        for sp in sparks:
            age = frame_i - sp["start"]
            if age < 0 or age > sp["life"]:
                continue
            # expand then gravity fall
            x = sp["cx"] + sp["vx"] * age
            y = sp["cy"] + sp["vy"] * age + 0.5 * gravity * age * age
            fade = max(0.0, 1.0 - age / sp["life"])
            if fade < 0.05:
                continue
            r = max(1, int(sp["r0"] * (0.55 + 0.45 * fade)))
            cr, cg, cb = sp["color"]
            fill = (
                min(255, int(cr * fade + 20)),
                min(255, int(cg * fade + 10)),
                min(255, int(cb * fade)),
            )
            draw.ellipse((x - r, y - r, x + r, y + r), fill=fill)

            # short trail behind spark
            if sp["trail"] and age > 0:
                tx = sp["cx"] + sp["vx"] * (age - 1.2)
                ty = sp["cy"] + sp["vy"] * (age - 1.2) + 0.5 * gravity * (age - 1.2) ** 2
                trail_c = (
                    min(255, int(cr * fade * 0.55)),
                    min(255, int(cg * fade * 0.45)),
                    min(255, int(cb * fade * 0.4)),
                )
                draw.line((tx, ty, x, y), fill=trail_c, width=1)

            # falling ember after mid-life
            if age > sp["life"] * 0.45 and (int(x) + int(y) + frame_i) % 3 == 0:
                ey = y + 4 + ((int(x) + frame_i) % 5)
                draw.point((int(x), int(ey)), fill=(fill[0] // 2, fill[1] // 3, 20))

        # bright flash at burst centers on start frame
        for cx, cy, start, color in bursts_spec:
            if frame_i == start:
                draw.ellipse((cx - 5, cy - 5, cx + 5, cy + 5), fill=(255, 255, 245))
                draw.ellipse((cx - 10, cy - 10, cx + 10, cy + 10), outline=color, width=2)
            elif frame_i == start + 1:
                draw.ellipse((cx - 3, cy - 3, cx + 3, cy + 3), fill=color)

        frames.append(img)

    frames[0].save(
        path,
        save_all=True,
        append_images=frames[1:],
        duration=duration_ms,
        loop=0,
        optimize=True,
    )
    return True


def ensure_celebrate_gif() -> Path:
    """Ensure local celebrate.gif exists; generate if missing."""
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    if CELEBRATE_GIF_PATH.is_file() and CELEBRATE_GIF_PATH.stat().st_size > 100:
        return CELEBRATE_GIF_PATH

    try:
        if _generate_pillow_gif(CELEBRATE_GIF_PATH):
            logger.info("Celebration GIF (Pillow) yaratildi: %s", CELEBRATE_GIF_PATH)
            return CELEBRATE_GIF_PATH
    except Exception as exc:
        logger.warning("Pillow GIF yaratish xato: %s", exc)

    try:
        _write_minimal_gif(CELEBRATE_GIF_PATH)
        logger.info("Celebration GIF (minimal) yaratildi: %s", CELEBRATE_GIF_PATH)
    except Exception as exc:
        logger.error("Celebration GIF yaratilmadi: %s", exc)
        raise
    return CELEBRATE_GIF_PATH


async def send_customer_celebration(
    bot: Any,
    chat_id: int,
    *,
    subtotal: int,
    total: int,
) -> None:
    """Lokal celebrate.gif + caption; GIF bo‘lmasa faqat HTML matn."""
    if not should_celebrate(subtotal, total):
        return

    text = celebration_html(subtotal=subtotal, total=total)

    try:
        gif_path = ensure_celebrate_gif()
        gif_bytes = gif_path.read_bytes()
        await bot.send_animation(
            chat_id=chat_id,
            animation=InputFile(io.BytesIO(gif_bytes), filename="celebrate.gif"),
            caption=text,
            parse_mode="HTML",
        )
    except Exception as exc:
        logger.warning("Celebration lokal GIF xato: %s", exc)
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode="HTML",
            )
        except Exception as exc2:
            logger.warning("Celebration matn xato: %s", exc2)
