"""Deterministic audio sample factory for Malinche's E2E / scenario tests.

The unit suite mocks every process boundary (whisper, Claude, ffmpeg), so we
have no coverage of the one thing the product actually does: turn real audio
into a Markdown note. This factory produces the raw material for the L2/L3
layers described in ``Docs/TESTING-E2E-STRATEGY.md``:

- spoken-word samples in PL/EN/ES/DE/FR via the built-in macOS ``say`` voices,
- the same utterance rendered into every format in ``AUDIO_EXTENSIONS``
  (``mp3, wav, m4a, wma, flac, aac, ogg``) via ffmpeg,
- edge cases that reproduce historical regressions: silence, a zero-byte file,
  a corrupted header, a non-16kHz sample rate, a stereo file, and a filename
  carrying Polish characters and ``{braces}`` (the alpha.18 crash).

Design contract
---------------
- **Deterministic & cached.** The same ``(text, voice, format)`` request maps
  to the same file via a content-addressed cache, so a full test run renders
  each sample at most once. ``Date``/randomness are deliberately avoided.
- **Lives outside the repo and outside ``$HOME``.** Cache defaults to the OS
  temp dir; it never writes near the developer's real home (the ``conftest``
  HOME guard stays intact). Override with ``MALINCHE_TEST_AUDIO_CACHE``.
- **Importable without pytest.** No test framework import at module load, so
  scripts and the self-test can both use it.
- **Degrades gracefully.** When ``say`` or ``ffmpeg`` is missing,
  :meth:`AudioFactory.available` is ``False`` and callers skip rather than fail.

This module has no dependency on ``src`` and is safe to import anywhere.
"""

from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

# --------------------------------------------------------------------------- #
# Constants.
# --------------------------------------------------------------------------- #

#: The format set Malinche claims to support. Kept in sync (by the self-test)
#: with ``src.config.defaults.AUDIO_EXTENSIONS`` so the corpus can never silently
#: drift from the production list.
AUDIO_EXTENSIONS = (".mp3", ".wav", ".m4a", ".wma", ".flac", ".aac", ".ogg")

#: Whisper resamples everything to 16 kHz mono; that is also our canonical
#: master format, so samples match what production actually feeds the model.
TARGET_SAMPLE_RATE = 16000
TARGET_CHANNELS = 1

#: ffmpeg encoder per extension. All emit 16 kHz mono unless a test asks
#: otherwise (e.g. :meth:`AudioFactory.wrong_sample_rate`).
_CODEC_FOR_EXT: Dict[str, List[str]] = {
    ".wav": ["-c:a", "pcm_s16le"],
    ".mp3": ["-c:a", "libmp3lame", "-q:a", "4"],
    ".m4a": ["-c:a", "aac", "-b:a", "64k"],
    ".aac": ["-c:a", "aac", "-b:a", "64k"],
    ".flac": ["-c:a", "flac"],
    ".ogg": ["-c:a", "libvorbis", "-q:a", "3"],
    ".wma": ["-c:a", "wmav2", "-b:a", "64k"],
}

#: Default short utterances per language. Short on purpose: keeps `say`
#: rendering and (in L3) Claude calls cheap while still being transcribable.
DEFAULT_TEXTS: Dict[str, str] = {
    "pl_PL": "To jest testowe nagranie po polsku do automatycznych testow.",
    "en_US": "This is an English test recording for the automated test suite.",
    "es_ES": "Esta es una grabacion de prueba en espanol para las pruebas.",
    "de_DE": "Dies ist eine deutsche Testaufnahme fuer die automatischen Tests.",
    "fr_FR": "Ceci est un enregistrement de test en francais pour les tests.",
}

_DEFAULT_CACHE_DIRNAME = "malinche-test-audio"


# --------------------------------------------------------------------------- #
# Environment probes.
# --------------------------------------------------------------------------- #


def say_available() -> bool:
    """True when the macOS ``say`` binary is on PATH."""
    return shutil.which("say") is not None


def ffmpeg_available() -> bool:
    """True when ``ffmpeg`` is on PATH."""
    return shutil.which("ffmpeg") is not None


_VOICE_LINE = re.compile(r"^(?P<name>.+?)\s{2,}(?P<lang>[a-z]{2}_[A-Z]{2})\b")


def list_voices() -> Dict[str, List[str]]:
    """Map BCP-ish language code (``pl_PL``) → ordered list of voice names.

    Parsed from ``say -v '?'``. Returns an empty dict when ``say`` is absent.
    Robust to voice names that contain spaces or parentheses (e.g.
    ``"Eddy (English (US))"``) by splitting on the run of whitespace that
    precedes the fixed-shape language column.
    """
    if not say_available():
        return {}
    proc = subprocess.run(
        ["say", "-v", "?"],
        capture_output=True,
        text=True,
        check=False,
    )
    voices: Dict[str, List[str]] = {}
    for line in proc.stdout.splitlines():
        match = _VOICE_LINE.match(line)
        if not match:
            continue
        voices.setdefault(match["lang"], []).append(match["name"].strip())
    return voices


def resolve_voice(lang: str) -> Optional[str]:
    """Pick a concrete voice for *lang*, tolerating region fallbacks.

    Tries an exact language-code match first (``es_ES``), then any voice whose
    language shares the same two-letter prefix (``es_MX`` for ``es``), so the
    corpus still builds on a machine that ships only a regional variant.
    Returns ``None`` when nothing matches.
    """
    voices = list_voices()
    if lang in voices and voices[lang]:
        return voices[lang][0]
    prefix = lang.split("_", 1)[0]
    for code, names in sorted(voices.items()):
        if code.startswith(prefix + "_") and names:
            return names[0]
    return None


# --------------------------------------------------------------------------- #
# Factory.
# --------------------------------------------------------------------------- #


class AudioFactory:
    """Render and cache deterministic audio samples for tests.

    All generated files are content-addressed under :attr:`cache_dir`, so
    repeated requests are cheap and stable across runs.
    """

    def __init__(self, cache_dir: Optional[Path] = None) -> None:
        if cache_dir is None:
            env = os.environ.get("MALINCHE_TEST_AUDIO_CACHE")
            cache_dir = (
                Path(env)
                if env
                else Path(tempfile.gettempdir()) / _DEFAULT_CACHE_DIRNAME
            )
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    # -- capability -------------------------------------------------------- #

    @property
    def available(self) -> bool:
        """True when both ``say`` and ``ffmpeg`` are present.

        Speech generation needs ``say``; everything past the WAV master needs
        ``ffmpeg``. Edge-case helpers that touch neither (``zero_byte``,
        ``corrupted``) work regardless and document that on themselves.
        """
        return say_available() and ffmpeg_available()

    # -- internals --------------------------------------------------------- #

    @staticmethod
    def _key(*parts: object) -> str:
        raw = "\x1f".join(str(p) for p in parts)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    def _cached(self, key: str, ext: str) -> Path:
        return self.cache_dir / f"{key}{ext}"

    @staticmethod
    def _tmp_for(out: Path) -> Path:
        """A sibling temp path that keeps *out*'s extension.

        ffmpeg infers the muxer from the output extension, so the temp file
        must share the final suffix (it cannot end in ``.part``). A leading dot
        keeps it hidden and out of the way until the atomic ``replace``.
        """
        return out.with_name("." + out.name)

    @staticmethod
    def _ffmpeg(args: List[str]) -> None:
        cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args]
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            raise RuntimeError(
                f"ffmpeg failed ({proc.returncode}): {' '.join(cmd)}\n"
                f"{proc.stderr.strip()}"
            )

    def _require(self) -> None:
        if not self.available:
            raise RuntimeError(
                "AudioFactory requires `say` and `ffmpeg`. Guard tests with "
                "`if not factory.available: pytest.skip(...)`."
            )

    # -- speech masters ---------------------------------------------------- #

    def master_wav(
        self,
        text: Optional[str] = None,
        lang: str = "en_US",
        voice: Optional[str] = None,
    ) -> Path:
        """Render *text* as a 16 kHz mono WAV via ``say``; cached.

        ``say`` writes WAVE/LEI16@16000 directly, so the master needs no ffmpeg
        pass. *voice* defaults to the first voice resolved for *lang*.
        """
        self._require()
        if text is None:
            text = DEFAULT_TEXTS.get(lang, DEFAULT_TEXTS["en_US"])
        if voice is None:
            voice = resolve_voice(lang)
        if voice is None:
            raise RuntimeError(
                f"No `say` voice available for language {lang!r}. "
                f"Installed: {sorted(list_voices())}"
            )
        key = self._key("master", text, voice, TARGET_SAMPLE_RATE)
        out = self._cached(key, ".wav")
        if out.exists() and out.stat().st_size > 0:
            return out
        tmp = out.with_suffix(".wav.part")
        proc = subprocess.run(
            [
                "say",
                "-v",
                voice,
                "--file-format=WAVE",
                f"--data-format=LEI16@{TARGET_SAMPLE_RATE}",
                "-o",
                str(tmp),
                text,
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0 or not tmp.exists():
            raise RuntimeError(
                f"`say` failed for voice {voice!r}: {proc.stderr.strip()}"
            )
        tmp.replace(out)
        return out

    def make(
        self,
        text: Optional[str] = None,
        ext: str = ".wav",
        lang: str = "en_US",
        voice: Optional[str] = None,
    ) -> Path:
        """Render *text* into a single *ext* file (16 kHz mono); cached."""
        ext = ext.lower()
        if ext not in _CODEC_FOR_EXT:
            raise ValueError(
                f"Unsupported format {ext!r}; expected one of "
                f"{sorted(_CODEC_FOR_EXT)}"
            )
        master = self.master_wav(text=text, lang=lang, voice=voice)
        if ext == ".wav":
            return master
        key = self._key("fmt", master.name, ext)
        out = self._cached(key, ext)
        if out.exists() and out.stat().st_size > 0:
            return out
        tmp = self._tmp_for(out)
        self._ffmpeg(
            [
                "-i",
                str(master),
                "-ar",
                str(TARGET_SAMPLE_RATE),
                "-ac",
                str(TARGET_CHANNELS),
                *_CODEC_FOR_EXT[ext],
                str(tmp),
            ]
        )
        tmp.replace(out)
        return out

    def all_formats(
        self,
        text: Optional[str] = None,
        lang: str = "en_US",
        voice: Optional[str] = None,
    ) -> Dict[str, Path]:
        """Render the same utterance into every ``AUDIO_EXTENSIONS`` format."""
        return {
            ext: self.make(text=text, ext=ext, lang=lang, voice=voice)
            for ext in AUDIO_EXTENSIONS
        }

    # -- edge cases -------------------------------------------------------- #

    def silence(self, duration: float = 2.0, ext: str = ".wav") -> Path:
        """A valid but silent clip — exercises empty-transcript handling."""
        self._require()
        ext = ext.lower()
        key = self._key("silence", duration, ext, TARGET_SAMPLE_RATE)
        out = self._cached(key, ext)
        if out.exists() and out.stat().st_size > 0:
            return out
        tmp = self._tmp_for(out)
        self._ffmpeg(
            [
                "-f",
                "lavfi",
                "-i",
                f"anullsrc=r={TARGET_SAMPLE_RATE}:cl=mono",
                "-t",
                str(duration),
                *_CODEC_FOR_EXT[ext],
                str(tmp),
            ]
        )
        tmp.replace(out)
        return out

    def wrong_sample_rate(
        self,
        text: Optional[str] = None,
        lang: str = "en_US",
        rate: int = 44100,
        ext: str = ".wav",
    ) -> Path:
        """Speech at a non-16kHz rate — whisper must resample, not choke."""
        self._require()
        ext = ext.lower()
        master = self.master_wav(text=text, lang=lang)
        key = self._key("rate", master.name, rate, ext)
        out = self._cached(key, ext)
        if out.exists() and out.stat().st_size > 0:
            return out
        tmp = self._tmp_for(out)
        self._ffmpeg(
            [
                "-i",
                str(master),
                "-ar",
                str(rate),
                "-ac",
                "1",
                *_CODEC_FOR_EXT[ext],
                str(tmp),
            ]
        )
        tmp.replace(out)
        return out

    def stereo(
        self,
        text: Optional[str] = None,
        lang: str = "en_US",
        ext: str = ".wav",
    ) -> Path:
        """A 2-channel clip — exercises the mono-downmix path."""
        self._require()
        ext = ext.lower()
        master = self.master_wav(text=text, lang=lang)
        key = self._key("stereo", master.name, ext)
        out = self._cached(key, ext)
        if out.exists() and out.stat().st_size > 0:
            return out
        tmp = self._tmp_for(out)
        self._ffmpeg(
            [
                "-i",
                str(master),
                "-ar",
                str(TARGET_SAMPLE_RATE),
                "-ac",
                "2",
                *_CODEC_FOR_EXT[ext],
                str(tmp),
            ]
        )
        tmp.replace(out)
        return out

    def zero_byte(self, ext: str = ".mp3") -> Path:
        """An empty file with an audio extension. No tooling required."""
        out = self._cached(self._key("zero", ext), ext)
        out.write_bytes(b"")
        return out

    def corrupted(self, ext: str = ".mp3") -> Path:
        """Audio-looking magic bytes followed by garbage — must fail to decode.

        Reproduces the alpha.16 condition (whisper cannot read the file). No
        ``say``/``ffmpeg`` required, so it works even on a CI box without them.
        Deterministic content (no randomness).
        """
        out = self._cached(self._key("corrupt", ext), ext)
        payload = b"ID3" + b"\x00" * 7 + bytes(range(256)) * 4
        out.write_bytes(payload)
        return out

    def named_copy(self, src: Path, filename: str) -> Path:
        """Copy *src* to a file literally named *filename* (subdir of cache).

        Used for the ``{braces}`` / Polish-character filename regression
        (alpha.18). The name lives in its own subdir so two odd names cannot
        collide in the flat cache.
        """
        subdir = self.cache_dir / ("named-" + self._key("name", filename))
        subdir.mkdir(parents=True, exist_ok=True)
        dst = subdir / filename
        shutil.copy2(src, dst)
        return dst

    # -- maintenance ------------------------------------------------------- #

    def clear_cache(self) -> None:
        """Remove all cached samples (next request regenerates)."""
        shutil.rmtree(self.cache_dir, ignore_errors=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
