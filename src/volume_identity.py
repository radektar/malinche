"""Identyfikacja zewnętrznego volume macOS po Volume UUID.

Aplikacja zapamiętuje decyzje użytkownika o dyskach (whitelist/blacklist)
po stabilnym identyfikatorze, nie po zmiennej nazwie mount-pointu.
Preferowany identyfikator to ``VolumeUUID`` z ``diskutil info -plist``.

Gdy ``diskutil`` nie zwraca UUID (np. dla mount-pointów sieciowych
lub egzotycznych systemów plików), funkcja zwraca deterministyczny
fallback w postaci ``fallback:name:<name>:size:<bytes>:fs:<fs>``.
Fallback jest słabszy (zmiana nazwy/rozmiaru ⇒ inny identyfikator),
ale nadal lepszy niż akceptacja nieznanego dysku.
"""

from __future__ import annotations

import plistlib
import subprocess
from pathlib import Path
from typing import Optional

from src.logger import logger


_DISKUTIL_TIMEOUT_SECONDS = 3.0

# Stable, disk-bound identifiers in order of preference. ``VolumeUUID`` exists
# for APFS/HFS+ but is typically absent on FAT/exFAT recorder cards; for those
# ``DiskUUID`` (the GPT partition GUID) or ``MediaUUID`` (the whole-media id)
# are still stable across relabels, remounts and card readers — strictly better
# than the name-based composite fallback. Only when none are present do we fall
# back to ``fallback:name:…`` (see :func:`_build_fallback_uuid`).
_STABLE_UUID_KEYS = ("VolumeUUID", "DiskUUID", "MediaUUID")


def _run_diskutil_info(volume_path: Path) -> Optional[dict]:
    """Wywołaj ``diskutil info -plist`` i zwróć sparsowany dict albo None."""
    try:
        result = subprocess.run(
            ["diskutil", "info", "-plist", str(volume_path)],
            capture_output=True,
            timeout=_DISKUTIL_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        logger.debug(f"diskutil info nieudane dla {volume_path}: {error}")
        return None

    if result.returncode != 0 or not result.stdout:
        logger.debug(
            f"diskutil info zwróciło {result.returncode} dla {volume_path}"
        )
        return None

    try:
        return plistlib.loads(result.stdout)
    except (plistlib.InvalidFileException, ValueError) as error:
        logger.debug(f"Nie można sparsować plist dla {volume_path}: {error}")
        return None


def _extract_stable_uuid(info: dict) -> Optional[str]:
    """Return the first non-empty stable id from *info* (see _STABLE_UUID_KEYS)."""
    for key in _STABLE_UUID_KEYS:
        value = info.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _build_fallback_uuid(
    volume_path: Path,
    info: Optional[dict] = None,
) -> str:
    """Zbuduj kompozyt zaczynający się od ``fallback:`` dla volumes bez UUID."""
    name = volume_path.name
    size = ""
    fs = ""
    if info:
        size = str(info.get("TotalSize", "")) or ""
        fs = str(info.get("FilesystemName", "")) or ""
    return f"fallback:name:{name}:size:{size}:fs:{fs}"


def get_volume_uuid(volume_path: Path) -> str:
    """Zwróć stabilny identyfikator volume macOS.

    Args:
        volume_path: Mount-point volume, np. ``/Volumes/LS-P1``.

    Returns:
        A stable disk id (``VolumeUUID``/``DiskUUID``/``MediaUUID``) jeśli
        ``diskutil`` którykolwiek zwrócił, inaczej kompozyt
        ``fallback:name:<n>:size:<s>:fs:<fs>``.
    """
    info = _run_diskutil_info(volume_path)
    if info is None:
        return _build_fallback_uuid(volume_path, info=None)

    uuid = _extract_stable_uuid(info)
    if uuid is not None:
        return uuid

    return _build_fallback_uuid(volume_path, info=info)


def get_volume_metadata(volume_path: Path) -> dict:
    """Zwróć ``{name, size, filesystem, uuid}`` dla volumes (best-effort).

    Używane przy budowie ``TrustedVolume`` — ``uuid`` zawsze zwracany,
    pozostałe pola mogą być puste gdy ``diskutil`` zawiódł.
    """
    info = _run_diskutil_info(volume_path)
    if info is None:
        return {
            "name": volume_path.name,
            "size": None,
            "filesystem": None,
            "uuid": _build_fallback_uuid(volume_path, info=None),
        }

    uuid = _extract_stable_uuid(info)
    if uuid is None:
        uuid = _build_fallback_uuid(volume_path, info=info)

    return {
        "name": str(info.get("VolumeName") or volume_path.name),
        "size": info.get("TotalSize"),
        "filesystem": info.get("FilesystemName"),
        "uuid": uuid,
    }
