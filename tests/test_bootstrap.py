"""End-to-end tests for bootstrap migration."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from src.bootstrap import ensure_ready
from src.ui.constants import APP_VERSION


def test_ensure_ready_migrates_legacy_layout(tmp_path, monkeypatch):
    """Bootstrap migrates legacy assets into Malinche layout."""
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    transrec_root = tmp_path / "Library" / "Application Support" / "Transrec"
    legacy_root = tmp_path / ".olympus_transcriber"
    legacy_logs = tmp_path / "Library" / "Logs"

    (transrec_root / "bin").mkdir(parents=True, exist_ok=True)
    (transrec_root / "models").mkdir(parents=True, exist_ok=True)
    legacy_root.mkdir(parents=True, exist_ok=True)
    legacy_logs.mkdir(parents=True, exist_ok=True)

    (transrec_root / "bin" / "whisper-cli").write_bytes(b"whisper")
    (transrec_root / "models" / "ggml-small.bin").write_bytes(b"model")
    (transrec_root / "config.json").write_text(
        json.dumps({"watch_mode": "auto", "whisper_model": "medium"}),
        encoding="utf-8",
    )
    (legacy_root / "transcriber.lock").write_text("123\n0", encoding="utf-8")
    (legacy_root / "recordings").mkdir(parents=True, exist_ok=True)
    (legacy_root / "recordings" / "a.mp3").write_bytes(b"audio")
    (tmp_path / ".olympus_transcriber_state.json").write_text(
        json.dumps({"last_sync": "2026-04-20T00:00:00"}),
        encoding="utf-8",
    )
    (legacy_logs / "olympus_transcriber.log").write_text("legacy", encoding="utf-8")

    settings = ensure_ready()

    malinche_root = tmp_path / "Library" / "Application Support" / "Malinche"
    assert (malinche_root / "bin" / "whisper-cli").exists()
    assert (malinche_root / "models" / "ggml-small.bin").exists()
    assert (malinche_root / "runtime" / "transcriber.lock").exists()
    assert (malinche_root / "recordings" / "a.mp3").exists()
    assert (malinche_root / "state.json").exists()
    assert (malinche_root / "logs" / "malinche.log").exists()

    assert not transrec_root.exists()
    assert not legacy_root.exists()
    assert not (tmp_path / ".olympus_transcriber_state.json").exists()

    assert settings.setup_version == APP_VERSION
    assert settings.transrec_migrated is True


def test_ensure_ready_is_idempotent(tmp_path, monkeypatch):
    """Second bootstrap run should not perform file moves."""
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    # Prepare already-migrated config.
    malinche_root = tmp_path / "Library" / "Application Support" / "Malinche"
    malinche_root.mkdir(parents=True, exist_ok=True)
    (malinche_root / "config.json").write_text("{}", encoding="utf-8")

    ensure_ready()

    with patch("src.bootstrap.shutil.move") as move_mock:
        ensure_ready()

    move_mock.assert_not_called()
