"""Self-test for ``tests/fixtures/audio_factory.py``.

Verifies the acceptance criteria for the sample corpus generator: real speech
masters, transcoding into every supported format, deterministic caching, the
edge cases that reproduce historical regressions, and graceful behaviour when
the toolchain is absent. See ``Docs/TESTING-E2E-STRATEGY.md``.

Tests that need actual audio rendering skip when ``say``/``ffmpeg`` are missing;
the pure-logic tests (format-list drift, zero-byte, corrupted) always run.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from tests.fixtures import audio_factory as af
from tests.fixtures.audio_factory import AudioFactory

# --------------------------------------------------------------------------- #
# Helpers.
# --------------------------------------------------------------------------- #


def _probe(path: Path) -> dict:
    """Return the first audio stream's properties via ffprobe (or raise)."""
    proc = subprocess.run(
        [
            "ffprobe",
            "-hide_banner",
            "-loglevel",
            "error",
            "-select_streams",
            "a:0",
            "-show_entries",
            "stream=codec_name,sample_rate,channels",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"ffprobe failed for {path}: {proc.stderr.strip()}")
    data = json.loads(proc.stdout)
    stream = (data.get("streams") or [{}])[0]
    stream["_duration"] = float(data.get("format", {}).get("duration", 0) or 0)
    return stream


def _decodes(path: Path) -> bool:
    """True when ffmpeg can fully decode *path* (proxy for 'whisper can read')."""
    proc = subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(path),
            "-f",
            "null",
            "-",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.returncode == 0


requires_tooling = pytest.mark.skipif(
    not (af.say_available() and af.ffmpeg_available()),
    reason="requires macOS `say` and `ffmpeg`",
)
requires_ffprobe = pytest.mark.skipif(
    shutil.which("ffprobe") is None, reason="requires ffprobe"
)


@pytest.fixture(scope="module")
def factory(tmp_path_factory) -> AudioFactory:
    """A factory with an isolated cache dir (so cache tests are hermetic)."""
    cache = tmp_path_factory.mktemp("audio-cache")
    return AudioFactory(cache_dir=cache)


# --------------------------------------------------------------------------- #
# AC: format list never drifts from production (pure, always runs).
# --------------------------------------------------------------------------- #


def test_format_list_matches_production_defaults():
    """The corpus must cover exactly the formats Malinche claims to support."""
    from src.config import defaults

    assert set(af.AUDIO_EXTENSIONS) == set(defaults.AUDIO_EXTENSIONS), (
        "audio_factory.AUDIO_EXTENSIONS drifted from "
        "src.config.defaults.AUDIO_EXTENSIONS"
    )


def test_cache_dir_is_not_under_home(factory):
    """The cache must never live under the user's real HOME (conftest guard)."""
    home = Path.home().resolve()
    assert home not in factory.cache_dir.resolve().parents


# --------------------------------------------------------------------------- #
# AC: edge cases that need no toolchain (always run).
# --------------------------------------------------------------------------- #


def test_zero_byte_is_empty(factory):
    path = factory.zero_byte(ext=".mp3")
    assert path.exists() and path.stat().st_size == 0
    assert path.suffix == ".mp3"


@requires_ffprobe
def test_corrupted_file_does_not_decode(factory):
    """A corrupted file must be undecodable — this is the alpha.16 trigger."""
    path = factory.corrupted(ext=".mp3")
    assert path.exists() and path.stat().st_size > 0
    assert not _decodes(path)


# --------------------------------------------------------------------------- #
# AC: voice discovery.
# --------------------------------------------------------------------------- #


@requires_tooling
def test_voice_discovery_finds_languages():
    voices = af.list_voices()
    assert voices, "expected `say` to report at least one voice"
    # English is present on every stock macOS; assert the parser produced
    # clean names (no leftover language column).
    assert any(code.startswith("en_") for code in voices)
    for names in voices.values():
        assert all(name and "  " not in name for name in names)


@requires_tooling
def test_resolve_voice_falls_back_across_region():
    # A made-up region should fall back to any voice sharing the prefix.
    assert af.resolve_voice("en_ZZ") is not None


# --------------------------------------------------------------------------- #
# AC: speech master + per-format rendering.
# --------------------------------------------------------------------------- #


@requires_tooling
@requires_ffprobe
def test_master_wav_is_16k_mono(factory):
    path = factory.master_wav(lang="en_US")
    assert path.suffix == ".wav"
    info = _probe(path)
    assert info["sample_rate"] == str(af.TARGET_SAMPLE_RATE)
    assert info["channels"] == af.TARGET_CHANNELS
    assert info["_duration"] > 0.3, "master should contain real speech"


@requires_tooling
@requires_ffprobe
@pytest.mark.parametrize("ext", af.AUDIO_EXTENSIONS)
def test_every_format_renders_and_decodes(factory, ext):
    path = factory.make(lang="en_US", ext=ext)
    assert path.exists() and path.stat().st_size > 0
    assert path.suffix == ext
    assert _decodes(path), f"{ext} sample should decode cleanly"
    info = _probe(path)
    assert info["sample_rate"] == str(af.TARGET_SAMPLE_RATE)
    assert info["channels"] == af.TARGET_CHANNELS


@requires_tooling
def test_all_formats_returns_full_set(factory):
    samples = factory.all_formats(lang="en_US")
    assert set(samples) == set(af.AUDIO_EXTENSIONS)
    assert all(p.exists() for p in samples.values())


@requires_tooling
def test_multilang_masters_are_distinct(factory):
    """Each language renders different audio (different bytes)."""
    paths = {
        lang: factory.master_wav(lang=lang)
        for lang in ("pl_PL", "en_US", "de_DE")
        if af.resolve_voice(lang) is not None
    }
    if len(paths) < 2:
        pytest.skip("need at least two installed language voices")
    digests = {p.read_bytes()[:2000] for p in paths.values()}
    assert len(digests) == len(paths), "languages produced identical audio"


# --------------------------------------------------------------------------- #
# AC: deterministic caching.
# --------------------------------------------------------------------------- #


@requires_tooling
def test_caching_is_idempotent(factory):
    """Same request → same path, and the file is not re-rendered."""
    first = factory.make(lang="en_US", ext=".mp3")
    mtime = first.stat().st_mtime_ns
    second = factory.make(lang="en_US", ext=".mp3")
    assert first == second
    assert second.stat().st_mtime_ns == mtime, "cache hit re-rendered the file"


# --------------------------------------------------------------------------- #
# AC: remaining edge cases.
# --------------------------------------------------------------------------- #


@requires_tooling
@requires_ffprobe
def test_silence_is_valid_but_silent(factory):
    path = factory.silence(duration=1.5)
    assert _decodes(path)
    info = _probe(path)
    assert 1.0 < info["_duration"] < 2.5


@requires_tooling
@requires_ffprobe
def test_wrong_sample_rate(factory):
    path = factory.wrong_sample_rate(lang="en_US", rate=44100)
    assert _probe(path)["sample_rate"] == "44100"


@requires_tooling
@requires_ffprobe
def test_stereo_has_two_channels(factory):
    path = factory.stereo(lang="en_US")
    assert _probe(path)["channels"] == 2


@requires_tooling
def test_named_copy_preserves_awkward_filename(factory):
    """alpha.18 regression: filenames with `{}` and Polish chars must survive."""
    src = factory.master_wav(lang="en_US")
    awkward = "nagranie {projekt} zażółć.wav"
    dst = factory.named_copy(src, awkward)
    assert dst.name == awkward
    assert dst.exists() and dst.read_bytes() == src.read_bytes()
