"""Application bootstrap and one-time legacy migration."""

from __future__ import annotations

import json
import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from src.config.settings import UserSettings
from src.env_loader import load_env_file
from src.runtime_deps import ensure_importable
from src.ui.constants import APP_VERSION


def _logger() -> logging.Logger:
    """Return bootstrap logger without importing runtime config."""
    return logging.getLogger("malinche")


def _safe_json_read(path: Path) -> Dict[str, Any]:
    """Read JSON file and return empty dict on failures."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        if isinstance(data, dict):
            return data
    except Exception:
        return {}
    return {}


def _legacy_paths(home: Path) -> Dict[str, Path]:
    """Resolve all legacy and target paths for migration."""
    malinche_root = home / "Library" / "Application Support" / "Malinche"
    transrec_root = home / "Library" / "Application Support" / "Transrec"
    return {
        "home": home,
        "malinche_root": malinche_root,
        "transrec_root": transrec_root,
        "legacy_runtime_root": home / ".olympus_transcriber",
        "legacy_state_file": home / ".olympus_transcriber_state.json",
        "legacy_log_file": home / "Library" / "Logs" / "olympus_transcriber.log",
        "new_config_file": malinche_root / "config.json",
        "new_state_file": malinche_root / "state.json",
        "new_runtime_dir": malinche_root / "runtime",
        "new_lock_file": malinche_root / "runtime" / "transcriber.lock",
        "new_recordings_dir": malinche_root / "recordings",
        "new_logs_dir": malinche_root / "logs",
        "new_log_file": malinche_root / "logs" / "malinche.log",
    }


def _newer_or_equal(src: Path, dst: Path) -> bool:
    """Return True when destination is newer or same age as source."""
    if not dst.exists():
        return False
    try:
        return dst.stat().st_mtime >= src.stat().st_mtime
    except OSError:
        return False


def _move_with_backup(
    src: Path,
    dst: Path,
    backup_suffix: str = ".transrec.bak",
) -> bool:
    """Move file/dir from src to dst, preserving collisions with source backup."""
    if not src.exists():
        return False

    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        backup = src.with_name(f"{src.name}{backup_suffix}")
        if backup.exists():
            return False
        shutil.move(str(src), str(backup))
        _logger().warning("[bootstrap] collision: moved %s -> %s", src, backup)
        return True

    shutil.move(str(src), str(dst))
    _logger().info("[bootstrap] moved %s -> %s", src, dst)
    return True


def _cleanup_legacy_root(legacy_root: Path, malinche_root: Path) -> int:
    """Remove empty legacy root or archive remaining leftovers."""
    if not legacy_root.exists():
        return 0

    moved = 0
    try:
        next(legacy_root.iterdir())
    except StopIteration:
        legacy_root.rmdir()
        _logger().info("[bootstrap] removed empty legacy dir %s", legacy_root)
        return 0
    except OSError:
        return 0

    stamp = datetime.now().strftime("%Y%m%d")
    archive_root = malinche_root / f".legacy-{stamp}" / legacy_root.name
    archive_root.mkdir(parents=True, exist_ok=True)

    for item in list(legacy_root.iterdir()):
        target = archive_root / item.name
        if _move_with_backup(item, target, backup_suffix=".legacy.bak"):
            moved += 1

    try:
        legacy_root.rmdir()
        _logger().info("[bootstrap] removed legacy dir %s", legacy_root)
    except OSError:
        pass

    return moved


def migrate_from_old_config() -> Optional[UserSettings]:
    """Build settings object from v1 legacy files/env."""
    paths = _legacy_paths(Path.home())
    old_config = _safe_json_read(paths["legacy_state_file"])

    settings = UserSettings()
    env_dir = os.getenv("MALINCHE_TRANSCRIBE_DIR") or os.getenv("OLYMPUS_TRANSCRIBE_DIR")
    if env_dir:
        settings.output_dir = Path(env_dir).expanduser().resolve()
    elif old_config.get("transcribe_dir"):
        settings.output_dir = Path(old_config["transcribe_dir"]).expanduser().resolve()

    if old_config.get("language"):
        settings.language = str(old_config["language"])
    if old_config.get("whisper_model"):
        settings.whisper_model = str(old_config["whisper_model"])

    ai_api_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY")
    if ai_api_key:
        settings.enable_ai_summaries = True
        settings.ai_api_key = ai_api_key

    old_recorder_names = old_config.get(
        "recorder_names", ["LS-P1", "OLYMPUS", "RECORDER"]
    )
    if old_recorder_names:
        settings.watch_mode = "specific"
        settings.watched_volumes = list(old_recorder_names)

    if old_config or env_dir:
        settings.setup_completed = True
        return settings
    return None


def ensure_ready() -> UserSettings:
    """Ensure runtime is initialized and legacy paths migrated."""
    load_env_file()
    paths = _legacy_paths(Path.home())
    moved_count = 0

    settings: UserSettings
    if paths["new_config_file"].exists():
        settings = UserSettings.load()
    else:
        transrec_config = paths["transrec_root"] / "config.json"
        if transrec_config.exists():
            data = _safe_json_read(transrec_config)
            settings = UserSettings(**data) if data else UserSettings()
            settings.save()
        else:
            migrated = migrate_from_old_config()
            if migrated is None:
                settings = UserSettings()
            else:
                settings = migrated
                settings.save()

    transrec_root = paths["transrec_root"]
    malinche_root = paths["malinche_root"]
    if transrec_root.exists():
        for name in ("bin", "models", "config.json", "state.json"):
            moved_count += int(
                _move_with_backup(
                    transrec_root / name, malinche_root / name, ".transrec.bak"
                )
            )

    legacy_state = paths["legacy_state_file"]
    if legacy_state.exists() and not _newer_or_equal(legacy_state, paths["new_state_file"]):
        moved_count += int(_move_with_backup(legacy_state, paths["new_state_file"]))

    legacy_lock = paths["legacy_runtime_root"] / "transcriber.lock"
    moved_count += int(_move_with_backup(legacy_lock, paths["new_lock_file"]))

    legacy_recordings = paths["legacy_runtime_root"] / "recordings"
    moved_count += int(_move_with_backup(legacy_recordings, paths["new_recordings_dir"]))

    legacy_log = paths["legacy_log_file"]
    if legacy_log.exists() and not paths["new_log_file"].exists():
        moved_count += int(_move_with_backup(legacy_log, paths["new_log_file"]))

    moved_count += _cleanup_legacy_root(paths["legacy_runtime_root"], malinche_root)
    moved_count += _cleanup_legacy_root(paths["transrec_root"], malinche_root)

    # Best-effort safeguard: do not block startup when offline.
    ensure_importable("anthropic")

    settings = UserSettings.load()
    settings.transrec_migrated = True
    settings.setup_version = APP_VERSION
    settings.save()

    if moved_count:
        _logger().info("[bootstrap] migrated %s items", moved_count)
    else:
        _logger().info("[bootstrap] nothing to migrate")

    return UserSettings.load()
