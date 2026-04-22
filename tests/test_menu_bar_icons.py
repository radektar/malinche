"""Assets-level tests for menu bar status icons."""

from pathlib import Path


ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets" / "menu_bar"
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"

EXPECTED_ICONS = [
    "idle.png",
    "scanning.png",
    "transcribing.png",
    "migrating.png",
    "error.png",
]


def test_menu_bar_icons_exist():
    for filename in EXPECTED_ICONS:
        path = ASSETS_DIR / filename
        assert path.exists(), f"Missing menu bar icon: {path}"


def test_menu_bar_icons_are_valid_png():
    for filename in EXPECTED_ICONS:
        path = ASSETS_DIR / filename
        header = path.read_bytes()[:8]
        assert header == PNG_MAGIC, f"Invalid PNG header for {path}"


def test_menu_bar_icons_have_reasonable_size():
    """Catch corrupted/stale placeholders.

    Real template PNGs for a 44x44 canvas are typically 200-1500 bytes.
    Anything absurdly small or large is almost certainly broken.
    """
    for filename in EXPECTED_ICONS:
        path = ASSETS_DIR / filename
        size = path.stat().st_size
        assert size > 100, f"{path} suspiciously small: {size} bytes"
        assert size < 20_000, f"{path} suspiciously large: {size} bytes"


def test_menu_bar_icons_are_monochrome_template():
    """Template icons must have RGBA with only black pixels + alpha.

    If the PNG contains non-black colours it will render as a coloured
    blob in the menu bar instead of adapting to light/dark mode.
    """
    from PIL import Image  # type: ignore[import-untyped]

    for filename in EXPECTED_ICONS:
        path = ASSETS_DIR / filename
        img = Image.open(path)
        assert img.mode == "RGBA", f"{path} must be RGBA, got {img.mode}"
        for r, g, b, a in img.getdata():
            if a == 0:
                continue
            assert (r, g, b) == (0, 0, 0), (
                f"{path} contains non-black pixel ({r},{g},{b}) with alpha={a}"
            )
