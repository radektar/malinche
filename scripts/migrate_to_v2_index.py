#!/usr/bin/env python3
"""Migrate legacy markdown transcripts to VaultIndex format."""

from pathlib import Path
from typing import Dict, Optional

from src.config import UserSettings
from src.fingerprint import compute_fingerprint
from src.hostinfo import get_hostname
from src.logger import logger
from src.vault_index import IndexEntry, VaultIndex


def _read_frontmatter(md_path: Path) -> Dict[str, str]:
    data: Dict[str, str] = {}
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


def _find_audio(vault_dir: Path, source_name: str) -> Optional[Path]:
    if not source_name:
        return None
    staged = Path.home() / ".olympus_transcriber" / "recordings" / source_name
    if staged.exists():
        return staged
    for candidate in vault_dir.glob(source_name):
        if candidate.exists():
            return candidate
    return None


def migrate() -> int:
    settings = UserSettings.load()
    vault_dir = Path(settings.output_dir)
    index = VaultIndex(vault_dir)
    index.load()

    if settings.index_migrated:
        logger.info("Index migration already completed.")
        return 0

    markdown_files = sorted(vault_dir.glob("*.md"))
    logger.info("Migrating %d markdown file(s) to v2 index...", len(markdown_files))

    for md_path in markdown_files:
        fm = _read_frontmatter(md_path)
        fingerprint = fm.get("fingerprint")
        source_name = fm.get("source", "")
        audio_path = _find_audio(vault_dir, source_name)
        if not fingerprint and audio_path:
            try:
                fingerprint = compute_fingerprint(audio_path)
            except OSError:
                fingerprint = None
        if not fingerprint:
            fingerprint = f"legacy:{md_path.stem}"

        version_info = {
            "version": int(fm.get("version", "1") or "1"),
            "transcribed_at": fm.get("recording_date", ""),
            "hostname": fm.get("transcribed_on", get_hostname()),
            "model": fm.get("model", ""),
            "language": fm.get("language", ""),
            "markdown_path": md_path.name,
        }
        existing = index.lookup(fingerprint)
        if existing:
            index.add_version(fingerprint, version_info)
            continue
        index.add(
            fingerprint,
            IndexEntry(
                fingerprint=fingerprint,
                source_filename=source_name,
                source_volume=fm.get("source_volume", ""),
                markdown_path=md_path.name,
                versions=[version_info],
            ),
        )

    settings.index_migrated = True
    settings.save()
    logger.info("Migration complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(migrate())

