#!/usr/bin/env python3
"""Generate Malinche app icon: macOS-native squircle, aztec earth palette.

Output:
  assets/icon_1024.png             — primary 1024×1024 master
  assets/malinche.iconset/*.png    — multi-resolution iconset
  assets/icon.icns                 — packaged via iconutil

Design:
  • Squircle (rounded rectangle, ~22% radius) — macOS Big Sur+ shape language
  • Background: terracotta → obsidian linear gradient (top-down)
  • Center M: cream-colored, geometric proportions, step-fret notches at base
  • Accent: thin jade border + four step-fret corner glyphs

Run:
  source venv/bin/activate
  python scripts/gen_aztec_icon.py
"""

from __future__ import annotations

import math
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

# Project root
ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
ICONSET = ASSETS / "malinche.iconset"

# Aztec earth palette (sync with src/ui/theme.py)
TERRACOTTA = (194, 64, 16, 255)        # #C24010
OBSIDIAN = (26, 26, 31, 255)           # #1A1A1F
JADE = (5, 120, 87, 255)               # #057857
GOLD = (214, 176, 51, 255)             # #D6B033
CREAM = (245, 233, 206, 255)           # warm off-white for M

MASTER = 1024
ICONSET_SIZES = [16, 32, 64, 128, 256, 512, 1024]
ICONSET_NAMES = {
    16:   ["icon_16x16.png"],
    32:   ["icon_16x16@2x.png", "icon_32x32.png"],
    64:   ["icon_32x32@2x.png"],
    128:  ["icon_128x128.png"],
    256:  ["icon_128x128@2x.png", "icon_256x256.png"],
    512:  ["icon_256x256@2x.png", "icon_512x512.png"],
    1024: ["icon_512x512@2x.png"],
}


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def make_squircle_mask(size: int, radius_ratio: float = 0.225) -> Image.Image:
    """Return a squircle alpha mask (L-mode) approximating macOS shape."""
    radius = int(size * radius_ratio)
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, size - 1, size - 1), radius=radius, fill=255)
    return mask


def make_gradient(size: int, top_color, bottom_color) -> Image.Image:
    """Vertical linear gradient between two RGBA colors."""
    img = Image.new("RGBA", (size, size), top_color)
    px = img.load()
    for y in range(size):
        t = y / (size - 1) if size > 1 else 0
        r = int(lerp(top_color[0], bottom_color[0], t))
        g = int(lerp(top_color[1], bottom_color[1], t))
        b = int(lerp(top_color[2], bottom_color[2], t))
        a = int(lerp(top_color[3], bottom_color[3], t))
        for x in range(size):
            px[x, y] = (r, g, b, a)
    return img


def add_radial_glow(img: Image.Image, color, intensity: float = 0.18) -> Image.Image:
    """Soft radial highlight at upper-third center."""
    w, h = img.size
    glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    cx, cy = w // 2, int(h * 0.32)
    radius = int(w * 0.45)
    for r in range(radius, 0, -8):
        alpha = int(255 * intensity * (r / radius) ** 2)
        gd.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(*color[:3], alpha))
    glow = glow.filter(ImageFilter.GaussianBlur(radius=18))
    return Image.alpha_composite(img, glow)


def draw_step_fret_corner(draw: ImageDraw.ImageDraw, cx: int, cy: int, unit: int, color):
    """Draw a small 3-step fret glyph at corner anchor (cx, cy).

    Aztec/Mixtec step-fret: a stylized stair pattern. We draw three nested
    squares offset to suggest steps.
    """
    for i in range(3):
        s = unit - i * (unit // 3)
        if s <= 0:
            continue
        draw.rectangle((cx - s, cy - s, cx + s, cy + s), outline=color, width=max(2, unit // 12))


def draw_M(img: Image.Image, color, accent):
    """Draw a geometric M with step-fret base notches centered on the canvas."""
    w, h = img.size
    draw = ImageDraw.Draw(img)

    # M bounding box (centered, leave padding for squircle border)
    pad_x = int(w * 0.22)
    pad_y_top = int(h * 0.24)
    pad_y_bottom = int(h * 0.30)
    left = pad_x
    right = w - pad_x
    top = pad_y_top
    bottom = h - pad_y_bottom
    box_w = right - left
    box_h = bottom - top

    # Stroke width — thick to read at 16×16
    stroke = int(w * 0.115)

    # M is built as four trapezoidal legs:
    # left vertical, valley-left, valley-right, right vertical
    # Use polygon for crisp geometry.
    valley_y = top + int(box_h * 0.55)
    mid_x = (left + right) // 2

    # Left vertical leg
    draw.polygon([
        (left,                top),
        (left + stroke,       top),
        (left + stroke,       bottom),
        (left,                bottom),
    ], fill=color)

    # Right vertical leg
    draw.polygon([
        (right - stroke,      top),
        (right,               top),
        (right,               bottom),
        (right - stroke,      bottom),
    ], fill=color)

    # Left valley diagonal: from top-left top to mid valley
    draw.polygon([
        (left,                          top),
        (left + stroke,                 top),
        (mid_x + stroke // 2,           valley_y),
        (mid_x - stroke // 2,           valley_y),
    ], fill=color)

    # Right valley diagonal: from top-right top to mid valley
    draw.polygon([
        (right - stroke,                top),
        (right,                         top),
        (mid_x + stroke // 2,           valley_y),
        (mid_x - stroke // 2,           valley_y),
    ], fill=color)

    # Step-fret base notches under each leg (geometric foot)
    notch_h = int(stroke * 0.55)
    notch_w = int(stroke * 1.6)
    # Left foot
    draw.rectangle((left - notch_h // 2, bottom, left + stroke + notch_h, bottom + notch_h), fill=color)
    # Right foot
    draw.rectangle((right - stroke - notch_h, bottom, right + notch_h // 2, bottom + notch_h), fill=color)

    # Tiny jade accent dots at the bottom of each leg (pre-Columbian peg motif)
    dot_r = int(stroke * 0.18)
    cy = bottom + notch_h + int(stroke * 0.45)
    for cx_dot in (left + stroke // 2, right - stroke // 2):
        draw.ellipse((cx_dot - dot_r, cy - dot_r, cx_dot + dot_r, cy + dot_r), fill=accent)


def draw_border_glyphs(img: Image.Image, color):
    """Four small step-fret glyphs near corners as accent."""
    w, h = img.size
    draw = ImageDraw.Draw(img)
    inset = int(w * 0.085)
    unit = int(w * 0.04)
    positions = [
        (inset,         inset),
        (w - inset,     inset),
        (inset,         h - inset),
        (w - inset,     h - inset),
    ]
    for cx, cy in positions:
        draw_step_fret_corner(draw, cx, cy, unit, color)


def build_icon(size: int = MASTER) -> Image.Image:
    """Produce a single squircle icon at the given size."""
    # Background gradient
    bg = make_gradient(size, TERRACOTTA, OBSIDIAN)

    # Subtle warm radial glow
    bg = add_radial_glow(bg, GOLD, intensity=0.22)

    # Apply squircle mask
    mask = make_squircle_mask(size, radius_ratio=0.225)
    rounded = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    rounded.paste(bg, (0, 0), mask)

    # Inner thin jade ring (stroke just inside the squircle edge)
    ring_layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    rd = ImageDraw.Draw(ring_layer)
    inset = max(2, size // 64)
    radius = int(size * 0.225) - inset
    rd.rounded_rectangle(
        (inset, inset, size - inset - 1, size - inset - 1),
        radius=radius,
        outline=JADE,
        width=max(2, size // 192),
    )
    rounded = Image.alpha_composite(rounded, ring_layer)

    # Corner step-fret accents (only at sizes where they read; skip <128)
    if size >= 128:
        draw_border_glyphs(rounded, JADE)

    # Center M with step-fret base + jade accent dots
    draw_M(rounded, CREAM, JADE)

    # Apply squircle mask again as final clip (defensive — corners stay clean)
    final = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    final.paste(rounded, (0, 0), mask)
    return final


def write_iconset(master: Image.Image) -> None:
    ICONSET.mkdir(parents=True, exist_ok=True)
    # Wipe any prior contents that aren't expected
    for existing in ICONSET.glob("*.png"):
        existing.unlink()
    for size, names in ICONSET_NAMES.items():
        # Re-render at native size for sharper small icons
        img = build_icon(size)
        for name in names:
            img.save(ICONSET / name, format="PNG")
            print(f"  wrote {ICONSET / name}")


def package_icns() -> Path:
    """Use macOS iconutil to bundle the iconset into icon.icns."""
    icns_path = ASSETS / "icon.icns"
    cmd = ["iconutil", "-c", "icns", str(ICONSET), "-o", str(icns_path)]
    subprocess.run(cmd, check=True)
    print(f"  wrote {icns_path}")
    return icns_path


def main() -> int:
    print("Building Malinche aztec squircle icon…")
    master = build_icon(MASTER)
    master_path = ASSETS / "icon_1024.png"
    master.save(master_path, format="PNG")
    print(f"  wrote {master_path}")

    write_iconset(master)
    package_icns()

    print("✅ Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
