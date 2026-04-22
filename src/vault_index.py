"""Vault index for multi-device deduplication and versioning."""

import json
import logging
import os
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import fcntl

logger = logging.getLogger(__name__)


@dataclass
class IndexEntry:
    """Single fingerprint entry in index."""

    fingerprint: str
    source_filename: str
    source_volume: str
    markdown_path: str
    versions: list[dict[str, Any]] = field(default_factory=list)


class VaultIndex:
    """Index manager backed by .malinche/index.json."""

    def __init__(self, vault_dir: Path):
        self.vault_dir = Path(vault_dir)
        self.index_dir = self.vault_dir / ".malinche"
        self.index_path = self.index_dir / "index.json"
        self.lock_path = self.index_dir / "index.lock"
        self._data: Dict[str, Any] = {"version": 1, "entries": {}}

    def load(self) -> None:
        """Load index from disk, or initialize empty index."""
        self.index_dir.mkdir(parents=True, exist_ok=True)
        if not self.index_path.exists():
            self._save()
            return
        try:
            self._data = json.loads(self.index_path.read_text(encoding="utf-8"))
            if "entries" not in self._data:
                self._data["entries"] = {}
        except (json.JSONDecodeError, OSError) as error:
            logger.warning("Index load failed (%s), rebuilding empty index", error)
            self._data = {"version": 1, "entries": {}}
            self._save()

    def lookup(self, fingerprint: str) -> Optional[IndexEntry]:
        """Return index entry for fingerprint."""
        row = self._data.get("entries", {}).get(fingerprint)
        if not row:
            return None
        return IndexEntry(
            fingerprint=row.get("fingerprint", fingerprint),
            source_filename=row.get("source_filename", ""),
            source_volume=row.get("source_volume", ""),
            markdown_path=row.get("markdown_path", ""),
            versions=list(row.get("versions", [])),
        )

    def entry_count(self) -> int:
        """Return number of fingerprint entries currently loaded."""
        return len(self._data.get("entries", {}))

    def add(self, fingerprint: str, entry: IndexEntry) -> None:
        """Add or replace entry in index."""
        with self._locked_reload():
            self._data.setdefault("entries", {})[fingerprint] = {
                "fingerprint": entry.fingerprint,
                "source_filename": entry.source_filename,
                "source_volume": entry.source_volume,
                "markdown_path": entry.markdown_path,
                "versions": list(entry.versions),
            }
            self._save()

    def add_version(self, fingerprint: str, version_info: Dict[str, Any]) -> None:
        """Append version info to an existing fingerprint."""
        with self._locked_reload():
            entries = self._data.setdefault("entries", {})
            if fingerprint not in entries:
                return
            existing = entries[fingerprint].setdefault("versions", [])
            if version_info not in existing:
                existing.append(version_info)
            ts = version_info.get("transcribed_at")
            if ts:
                entries[fingerprint]["markdown_path"] = version_info.get(
                    "markdown_path", entries[fingerprint].get("markdown_path", "")
                )
            self._save()

    @contextmanager
    def _locked_reload(self):
        self.index_dir.mkdir(parents=True, exist_ok=True)
        fd = os.open(self.lock_path, os.O_CREAT | os.O_RDWR)
        fcntl.flock(fd, fcntl.LOCK_EX)
        try:
            try:
                if self.index_path.exists():
                    self._data = json.loads(self.index_path.read_text(encoding="utf-8"))
                    self._data.setdefault("entries", {})
            except (json.JSONDecodeError, OSError):
                self._data = {"version": 1, "entries": {}}
            yield
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)
            os.close(fd)

    def _save(self) -> None:
        self.index_dir.mkdir(parents=True, exist_ok=True)
        tmp_path = self.index_path.with_suffix(".json.tmp")
        tmp_path.write_text(
            json.dumps(self._data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        os.replace(tmp_path, self.index_path)

    @staticmethod
    def current_iso_timestamp() -> str:
        """Return current timestamp for version metadata."""
        return datetime.now().isoformat(timespec="seconds")


def is_icloud_synced(path: Path) -> bool:
    """Check if path is likely inside iCloud synced container."""
    expanded = path.expanduser().resolve()
    iCloud_root = (Path.home() / "Library" / "Mobile Documents").resolve()
    try:
        expanded.relative_to(iCloud_root)
        return True
    except ValueError:
        return False

