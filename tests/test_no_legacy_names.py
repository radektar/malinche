"""Ensure legacy path names are isolated to bootstrap module."""

from pathlib import Path


def test_legacy_names_only_in_bootstrap():
    """`Transrec` and `.olympus_transcriber` must not leak outside bootstrap."""
    src_root = Path("src")
    offenders: list[str] = []
    patterns = ("Transrec", ".olympus_transcriber", "olympus_transcriber")

    for file_path in src_root.rglob("*.py"):
        if file_path == Path("src/bootstrap.py"):
            continue
        content = file_path.read_text(encoding="utf-8")
        if any(pattern in content for pattern in patterns):
            offenders.append(str(file_path))

    assert offenders == [], f"Legacy names found outside bootstrap: {offenders}"
