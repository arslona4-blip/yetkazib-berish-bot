""" /start uchun lokal welcome.gif — Ken Burns + yorug‘lik to‘lqini.

Tashqi URL ishlatilmaydi. GIF yo‘q bo‘lsa welcome.jpg dan yaratiladi.
"""

from __future__ import annotations

import logging
import math
from pathlib import Path

from bot.config import WELCOME_ANIMATION_PATH, WELCOME_PHOTO_PATH

logger = logging.getLogger(__name__)

ASSETS_DIR = Path(__file__).resolve().parent / "assets"
_OUT_SIZE = 448
_N_FRAMES = 16
_DURATION_MS = 95


def _generate_from_photo(src_path: Path, out_path: Path) -> bool:
    from PIL import Image, ImageDraw, ImageEnhance

    src = Image.open(src_path).convert("RGB")
    src = src.resize((_OUT_SIZE, _OUT_SIZE), Image.Resampling.LANCZOS)

    frames_rgb: list[Image.Image] = []
    banner_h = int(_OUT_SIZE * 0.26)

    for i in range(_N_FRAMES):
        t = i / _N_FRAMES
        zoom = 1.0 + 0.05 * (0.5 - 0.5 * math.cos(2 * math.pi * t))
        pan_y = int(5 * math.sin(2 * math.pi * t))
        nw = int(_OUT_SIZE * zoom)
        nh = int(_OUT_SIZE * zoom)
        scaled = src.resize((nw, nh), Image.Resampling.LANCZOS)
        left = (nw - _OUT_SIZE) // 2
        top = max(0, min(nh - _OUT_SIZE, (nh - _OUT_SIZE) // 2 + pan_y))
        frame = scaled.crop((left, top, left + _OUT_SIZE, top + _OUT_SIZE))

        bright = 1.0 + 0.03 * math.sin(2 * math.pi * t)
        frame = ImageEnhance.Brightness(frame).enhance(bright)

        overlay = Image.new("RGBA", (_OUT_SIZE, _OUT_SIZE), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        shine_x = int(-90 + (_OUT_SIZE + 180) * t)
        for dx in range(28):
            dist = abs(dx - 14) / 14
            alpha = int(38 * (1 - dist) ** 2)
            x = shine_x + dx
            draw.polygon(
                [
                    (x, 10),
                    (x + 22, 10),
                    (x + 48, banner_h - 6),
                    (x + 26, banner_h - 6),
                ],
                fill=(255, 255, 255, alpha),
            )

        composed = Image.alpha_composite(frame.convert("RGBA"), overlay)
        frames_rgb.append(composed.convert("RGB"))

    palette_img = frames_rgb[0].quantize(colors=80, method=Image.Quantize.MEDIANCUT)
    out_frames = [palette_img]
    for fr in frames_rgb[1:]:
        out_frames.append(
            fr.quantize(palette=palette_img, dither=Image.Dither.FLOYDSTEINBERG)
        )

    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    out_frames[0].save(
        out_path,
        save_all=True,
        append_images=out_frames[1:],
        duration=_DURATION_MS,
        loop=0,
        optimize=True,
        disposal=2,
    )
    return out_path.is_file() and out_path.stat().st_size > 100


def ensure_welcome_gif() -> Path | None:
    """welcome.gif ni qaytaradi; yo‘q bo‘lsa welcome.jpg dan yaratadi."""
    path = WELCOME_ANIMATION_PATH
    if path.is_file() and path.stat().st_size > 100:
        return path

    if not WELCOME_PHOTO_PATH.is_file():
        return None

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        if _generate_from_photo(WELCOME_PHOTO_PATH, path):
            logger.info("Welcome GIF yaratildi: %s (%s bayt)", path, path.stat().st_size)
            return path
    except Exception as exc:
        logger.warning("Welcome GIF yaratilmadi: %s", exc)
    return None


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = ensure_welcome_gif()
    if result is None:
        raise SystemExit("welcome.gif yaratilmadi")
    print(f"OK {result} ({result.stat().st_size} bytes)")
