"""Dedup integration tests for transcriber + vault index."""

from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

from src.config.config import Config
from src.transcriber import Transcriber
from src.vault_index import IndexEntry


def test_transcriber_skips_when_fingerprint_exists_free(tmp_path: Path) -> None:
    """FREE tier skips already indexed fingerprints."""
    cfg = Config()
    cfg.TRANSCRIBE_DIR = tmp_path
    transcriber = Transcriber(config=cfg)
    fp = "sha256:exists"
    transcriber.vault_index.add(
        fp,
        IndexEntry(
            fingerprint=fp,
            source_filename="a.mp3",
            source_volume="LS-P1",
            markdown_path="a.md",
            versions=[{"version": 1}],
        ),
    )
    audio = tmp_path / "a.mp3"
    audio.write_bytes(b"123")
    with patch("src.transcriber.compute_fingerprint", return_value=fp), patch(
        "src.transcriber.license_manager.get_current_tier"
    ) as tier_mock:
        from src.config.features import FeatureTier

        tier_mock.return_value = FeatureTier.FREE
        assert transcriber.transcribe_file(audio) is True


def test_fallback_match_upgrades_index_to_sha256(tmp_path: Path) -> None:
    """Fallback source-based match should cache canonical fingerprint in index."""
    cfg = Config()
    cfg.TRANSCRIBE_DIR = tmp_path
    cfg.LOCAL_RECORDINGS_DIR = tmp_path / "staged"
    cfg.PROCESS_LOCK_FILE = tmp_path / "process.lock"

    with patch.object(Transcriber, "_run_index_migration_if_needed", return_value=None):
        transcriber = Transcriber(config=cfg)

    recorder = tmp_path / "LS-P1"
    recorder.mkdir()
    audio = recorder / "DS0001.mp3"
    audio.write_bytes(b"audio-content")

    md = tmp_path / "existing.md"
    md.write_text(
        "\n".join(
            [
                "---",
                "source: DS0001.mp3",
                "source_volume: LS-P1",
                "version: 1",
                "transcribed_on: old-mac",
                "model: small",
                "language: pl",
                "recording_date: 2026-04-20T10:00:00",
                "---",
                "",
                "legacy transcript",
            ]
        ),
        encoding="utf-8",
    )

    with (
        patch("src.transcriber.send_notification", return_value=None),
        patch.object(transcriber, "find_recorder", return_value=recorder),
        patch.object(
            transcriber,
            "get_last_sync_time",
            return_value=datetime.now() - timedelta(days=30),
        ),
        patch.object(transcriber, "find_audio_files", return_value=[audio]),
        patch.object(transcriber, "_stage_audio_file") as stage_mock,
        patch("src.transcriber.compute_fingerprint", return_value="sha256:new-fp"),
    ):
        transcriber.process_recorder()

    stage_mock.assert_not_called()
    entry = transcriber.vault_index.lookup("sha256:new-fp")
    assert entry is not None
    assert entry.source_filename == "DS0001.mp3"
    assert entry.markdown_path == "existing.md"
    assert entry.versions

