"""Tests for vault index module."""

from pathlib import Path

from src.vault_index import IndexEntry, VaultIndex


def test_vault_index_add_and_lookup(tmp_path: Path) -> None:
    """Can add and read a fingerprint entry."""
    idx = VaultIndex(tmp_path)
    idx.load()
    fingerprint = "sha256:test"
    idx.add(
        fingerprint,
        IndexEntry(
            fingerprint=fingerprint,
            source_filename="DS0001.MP3",
            source_volume="LS-P1",
            markdown_path="note.md",
            versions=[{"version": 1, "transcribed_at": "2026-01-01T00:00:00"}],
        ),
    )
    loaded = idx.lookup(fingerprint)
    assert loaded is not None
    assert loaded.markdown_path == "note.md"


def test_vault_index_add_version(tmp_path: Path) -> None:
    """Can append additional versions."""
    idx = VaultIndex(tmp_path)
    idx.load()
    fingerprint = "sha256:test"
    idx.add(
        fingerprint,
        IndexEntry(
            fingerprint=fingerprint,
            source_filename="DS0001.MP3",
            source_volume="LS-P1",
            markdown_path="note.md",
            versions=[],
        ),
    )
    idx.add_version(
        fingerprint,
        {
            "version": 2,
            "transcribed_at": "2026-01-01T01:00:00",
            "markdown_path": "note.v2.md",
        },
    )
    loaded = idx.lookup(fingerprint)
    assert loaded is not None
    assert loaded.markdown_path == "note.v2.md"
    assert len(loaded.versions) == 1

