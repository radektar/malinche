"""Tests for the shared volume detection utilities.

These tests cover the code path that unifies ``FileMonitor`` and
``Transcriber`` recorder detection. They protect against the regression
where ``Transcriber.find_recorder`` ignored volumes in ``auto`` mode
because it iterated over a hardcoded list of names.
"""

from pathlib import Path

import pytest

from src.config.settings import UserSettings
from src.volume_utils import (
    find_matching_volumes,
    has_audio_files,
    should_process_volume,
)


def _make_volume(root: Path, name: str, audio_file: str | None = "rec.mp3") -> Path:
    """Create a fake volume and optionally seed it with an audio file."""
    volume = root / name
    volume.mkdir()
    if audio_file:
        (volume / audio_file).touch()
    else:
        (volume / "notes.txt").touch()
    return volume


def test_has_audio_files_detects_top_level(tmp_path):
    """A single audio file directly under the volume must be detected."""
    (tmp_path / "memo.wav").touch()
    assert has_audio_files(tmp_path) is True


def test_has_audio_files_detects_within_subdirectory(tmp_path):
    """Audio inside a nested folder (within max_depth) must be detected."""
    nested = tmp_path / "A" / "B"
    nested.mkdir(parents=True)
    (nested / "track.mp3").touch()
    assert has_audio_files(tmp_path) is True


def test_has_audio_files_ignores_non_audio(tmp_path):
    """Volumes with only non-audio files must return False."""
    (tmp_path / "readme.txt").touch()
    assert has_audio_files(tmp_path) is False


def test_has_audio_files_respects_max_depth(tmp_path):
    """Files beyond max_depth must not trigger detection."""
    deep = tmp_path / "a" / "b" / "c" / "d"
    deep.mkdir(parents=True)
    (deep / "far.mp3").touch()
    # max_depth=1 means only files up to one directory deep are considered
    assert has_audio_files(tmp_path, max_depth=1) is False


def test_should_process_volume_auto_mode_accepts_audio_volume(tmp_path):
    """Auto mode must accept any non-system volume containing audio."""
    volume = _make_volume(tmp_path, "IC RECORDER")
    settings = UserSettings(watch_mode="auto", watched_volumes=[])
    assert should_process_volume(volume, settings) is True


def test_should_process_volume_auto_mode_rejects_empty_volume(tmp_path):
    """Auto mode must reject volumes without audio."""
    volume = _make_volume(tmp_path, "EMPTY_STICK", audio_file=None)
    settings = UserSettings(watch_mode="auto", watched_volumes=[])
    assert should_process_volume(volume, settings) is False


def test_should_process_volume_rejects_system_volume(tmp_path):
    """System volumes like 'Macintosh HD' must always be rejected."""
    volume = _make_volume(tmp_path, "Macintosh HD")
    settings = UserSettings(watch_mode="auto", watched_volumes=[])
    assert should_process_volume(volume, settings) is False


def test_should_process_volume_specific_mode_requires_watchlist(tmp_path):
    """Specific mode must only accept volumes whose names are watchlisted."""
    volume_ok = _make_volume(tmp_path, "LS-P1")
    volume_other = _make_volume(tmp_path, "RANDOM")

    settings = UserSettings(watch_mode="specific", watched_volumes=["LS-P1"])
    assert should_process_volume(volume_ok, settings) is True
    assert should_process_volume(volume_other, settings) is False


def test_should_process_volume_manual_mode_never_accepts(tmp_path):
    """Manual mode must always return False (user-driven detection)."""
    volume = _make_volume(tmp_path, "LS-P1")
    settings = UserSettings(watch_mode="manual", watched_volumes=["LS-P1"])
    assert should_process_volume(volume, settings) is False


def test_find_matching_volumes_auto_returns_all_audio_volumes(tmp_path):
    """Auto mode must return every non-system volume with audio files."""
    _make_volume(tmp_path, "IC RECORDER")
    _make_volume(tmp_path, "SD_CARD", audio_file="a.wav")
    _make_volume(tmp_path, "NoAudio", audio_file=None)
    _make_volume(tmp_path, "Macintosh HD")

    settings = UserSettings(watch_mode="auto", watched_volumes=[])
    result = find_matching_volumes(settings, volumes_root=tmp_path)

    assert sorted(v.name for v in result) == ["IC RECORDER", "SD_CARD"]


def test_find_matching_volumes_returns_deterministic_order(tmp_path):
    """Results must be sorted alphabetically for deterministic iteration."""
    _make_volume(tmp_path, "ZETA")
    _make_volume(tmp_path, "ALPHA")
    _make_volume(tmp_path, "MIKE")

    settings = UserSettings(watch_mode="auto", watched_volumes=[])
    result = find_matching_volumes(settings, volumes_root=tmp_path)

    assert [v.name for v in result] == ["ALPHA", "MIKE", "ZETA"]


def test_find_matching_volumes_missing_root_returns_empty(tmp_path):
    """When /Volumes does not exist we must return an empty list."""
    settings = UserSettings(watch_mode="auto", watched_volumes=[])
    missing = tmp_path / "does-not-exist"
    assert find_matching_volumes(settings, volumes_root=missing) == []
