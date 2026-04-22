"""Simulated multi-device dedup tests on a single machine."""

from pathlib import Path
from unittest.mock import patch

from src.config.config import Config
from src.config.features import FeatureTier
from src.transcriber import Transcriber
from src.vault_index import IndexEntry, VaultIndex


def test_device_b_skips_after_device_a_transcribed(tmp_path: Path) -> None:
    """Device B should skip when index from Device A is already synced."""
    vault_dir = tmp_path / "iCloudVault"
    vault_dir.mkdir()

    fingerprint = "sha256:deadbeef"

    # Device A writes the entry that would later be synced through iCloud.
    index_a = VaultIndex(vault_dir)
    index_a.load()
    index_a.add(
        fingerprint,
        IndexEntry(
            fingerprint=fingerprint,
            source_filename="sample.m4a",
            source_volume="Recordings",
            markdown_path="sample.md",
            versions=[{"version": 1, "markdown_path": "sample.md"}],
        ),
    )

    # Device B starts with a fresh VaultIndex instance (simulating another Mac).
    index_b = VaultIndex(vault_dir)
    index_b.load()
    assert index_b.lookup(fingerprint) is not None

    cfg = Config()
    cfg.TRANSCRIBE_DIR = vault_dir
    transcriber_b = Transcriber(config=cfg)
    transcriber_b.whisper_available = True

    audio = vault_dir / "sample.m4a"
    audio.write_bytes(b"same audio")

    with patch("src.transcriber.compute_fingerprint", return_value=fingerprint), patch(
        "src.transcriber.license_manager.get_current_tier", return_value=FeatureTier.FREE
    ), patch.object(transcriber_b, "_run_macwhisper") as run_mock:
        assert transcriber_b.transcribe_file(audio) is True
        run_mock.assert_not_called()

    assert len(list(vault_dir.glob("*.md"))) == 0
