"""Dedup integration tests for transcriber + vault index."""

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

