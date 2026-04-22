"""Generate bold monochrome menu bar icons for Malinche.

Template images for NSStatusItem require fully black pixels + alpha.
macOS tints them automatically for light/dark menu bar.
"""

from pathlib import Path

from PIL import Image, ImageDraw


OUT_DIR = Path(__file__).resolve().parent.parent / "assets" / "menu_bar"
SIZE = 44  # @2x for Retina; macOS scales down to ~22pt on non-Retina.
OPAQUE = 255


def _new_canvas() -> Image.Image:
    return Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))


def _draw_microphone(draw: ImageDraw.ImageDraw, center_x: int = SIZE // 2) -> None:
    """Draw a thick, bold microphone template."""
    body_width = 16
    body_height = 22
    body_top = 6
    body_left = center_x - body_width // 2
    body_right = center_x + body_width // 2
    body_bottom = body_top + body_height

    draw.rounded_rectangle(
        (body_left, body_top, body_right, body_bottom),
        radius=8,
        fill=(0, 0, 0, OPAQUE),
    )

    stand_arc_top = body_top + body_height // 2
    stand_arc_bottom = body_bottom + 6
    stand_arc_left = center_x - 12
    stand_arc_right = center_x + 12
    draw.arc(
        (stand_arc_left, stand_arc_top, stand_arc_right, stand_arc_bottom),
        start=0,
        end=180,
        fill=(0, 0, 0, OPAQUE),
        width=3,
    )

    draw.line(
        (center_x, stand_arc_bottom - 2, center_x, SIZE - 4),
        fill=(0, 0, 0, OPAQUE),
        width=3,
    )

    base_width = 16
    base_y = SIZE - 4
    draw.line(
        (center_x - base_width // 2, base_y, center_x + base_width // 2, base_y),
        fill=(0, 0, 0, OPAQUE),
        width=3,
    )


def _draw_badge(draw: ImageDraw.ImageDraw, glyph: str) -> None:
    """Draw a small status badge in the top-right corner."""
    badge_size = 16
    badge_x = SIZE - badge_size - 1
    badge_y = 1
    draw.ellipse(
        (badge_x, badge_y, badge_x + badge_size, badge_y + badge_size),
        fill=(0, 0, 0, OPAQUE),
    )
    # Cut-out to keep the glyph visible via transparency.
    inner_margin = 3
    ix0 = badge_x + inner_margin
    iy0 = badge_y + inner_margin
    ix1 = badge_x + badge_size - inner_margin
    iy1 = badge_y + badge_size - inner_margin

    if glyph == "scan":
        draw.ellipse((ix0, iy0, ix1, iy1), fill=(0, 0, 0, 0))
        draw.ellipse((ix0 + 2, iy0 + 2, ix1 - 2, iy1 - 2), fill=(0, 0, 0, OPAQUE))
    elif glyph == "work":
        cx = (ix0 + ix1) // 2
        cy = (iy0 + iy1) // 2
        draw.line((ix0, cy, ix1, cy), fill=(0, 0, 0, 0), width=2)
        draw.line((cx - 3, iy0, cx + 3, iy0), fill=(0, 0, 0, 0), width=2)
        draw.line((cx - 3, iy1 - 1, cx + 3, iy1 - 1), fill=(0, 0, 0, 0), width=2)
    elif glyph == "sync":
        draw.arc((ix0, iy0, ix1, iy1), start=0, end=270, fill=(0, 0, 0, 0), width=2)
    elif glyph == "error":
        cx = (ix0 + ix1) // 2
        draw.line((cx, iy0 + 1, cx, iy1 - 3), fill=(0, 0, 0, 0), width=2)
        draw.ellipse((cx - 1, iy1 - 2, cx + 1, iy1), fill=(0, 0, 0, 0))
    # "idle" deliberately has no badge — clean microphone.


def build(name: str, glyph: str | None) -> Path:
    img = _new_canvas()
    draw = ImageDraw.Draw(img)
    _draw_microphone(draw)
    if glyph is not None:
        _draw_badge(draw, glyph)
    out = OUT_DIR / f"{name}.png"
    img.save(out, "PNG")
    return out


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    specs = {
        "idle": None,
        "scanning": "scan",
        "transcribing": "work",
        "migrating": "sync",
        "error": "error",
    }
    for name, glyph in specs.items():
        path = build(name, glyph)
        print(f"Generated {path}")


if __name__ == "__main__":
    main()
