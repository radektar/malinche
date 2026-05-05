#!/usr/bin/env python3
"""Generate DMG installer background — aztec earth gradient with step-fret border.

Output:
  assets/dmg_background.png   — 600×400 PNG used by scripts/create_dmg.sh

Design:
  • Background: warm cream (#F5E9CE) with horizontal terracotta band
  • Top + bottom step-fret friezes in jade
  • Centered subtitle "Drag Malinche → Applications" rendered as a thin guide
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

# Sync with theme.py
TERRACOTTA = (194, 64, 16, 255)
OBSIDIAN = (26, 26, 31, 255)
JADE = (5, 120, 87, 255)
GOLD = (214, 176, 51, 255)
CREAM_LIGHT = (250, 240, 215, 255)
CREAM_DARK = (235, 218, 184, 255)

WIDTH, HEIGHT = 600, 400


def lerp(a, b, t):
    return a + (b - a) * t


def vertical_gradient(size, top, bottom):
    img = Image.new("RGBA", size, top)
    px = img.load()
    w, h = size
    for y in range(h):
        t = y / max(1, h - 1)
        c = tuple(int(lerp(top[i], bottom[i], t)) for i in range(4))
        for x in range(w):
            px[x, y] = c
    return img


def draw_step_fret_band(draw: ImageDraw.ImageDraw, y: int, height: int, color, *, count: int = 24):
    """Stylized aztec step-fret repeated horizontally as a thin band.

    Each tile is a stepped-square (3 nested concentric squares).
    """
    tile_w = WIDTH / count
    for i in range(count):
        cx = int(i * tile_w + tile_w / 2)
        cy = y + height // 2
        unit = int(min(tile_w, height) * 0.45)
        for k in range(3):
            s = unit - k * (unit // 3)
            if s <= 0:
                continue
            draw.rectangle(
                (cx - s, cy - s, cx + s, cy + s),
                outline=color,
                width=max(2, unit // 14),
            )


def add_terracotta_band(img: Image.Image) -> Image.Image:
    """Soft horizontal terracotta haze through the middle."""
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    band_top = HEIGHT // 2 - 70
    band_bottom = HEIGHT // 2 + 70
    for y in range(band_top, band_bottom):
        # Bell-shaped alpha distribution
        rel = (y - HEIGHT / 2) / 70
        alpha = int(70 * (1 - min(1, abs(rel))) ** 2)
        draw.line((0, y, WIDTH, y), fill=(*TERRACOTTA[:3], alpha))
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=8))
    return Image.alpha_composite(img, overlay)


def main() -> int:
    base = vertical_gradient((WIDTH, HEIGHT), CREAM_LIGHT, CREAM_DARK)
    base = add_terracotta_band(base)

    draw = ImageDraw.Draw(base)
    draw_step_fret_band(draw, y=8, height=24, color=JADE, count=22)
    draw_step_fret_band(draw, y=HEIGHT - 32, height=24, color=JADE, count=22)

    # Thin terracotta hairlines just below/above the friezes
    draw.line((20, 36, WIDTH - 20, 36), fill=TERRACOTTA, width=1)
    draw.line((20, HEIGHT - 36, WIDTH - 20, HEIGHT - 36), fill=TERRACOTTA, width=1)

    out = ASSETS / "dmg_background.png"
    base.convert("RGB").save(out, format="PNG", optimize=True)
    print(f"  wrote {out} ({WIDTH}×{HEIGHT})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
