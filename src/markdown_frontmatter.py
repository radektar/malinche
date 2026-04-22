"""Utilities for reading YAML-like frontmatter from markdown notes."""

from pathlib import Path


def read_frontmatter(md_path: Path) -> dict[str, str]:
    """Read top-of-file frontmatter block as a flat key/value dict."""
    data: dict[str, str] = {}
    try:
        lines = md_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return data

    if not lines or lines[0].strip() != "---":
        return data

    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip('"')
    return data
