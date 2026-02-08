"""Full Disk Access permission checking."""

import subprocess
from pathlib import Path

from src.logger import logger


def check_full_disk_access() -> bool:
    """Sprawdź czy aplikacja ma Full Disk Access.

    Returns:
        True jeśli ma dostęp, False w przeciwnym razie
    """
    test_paths = [
        Path.home() / "Library" / "Mail",
        Path.home() / "Library" / "Safari",
    ]

    for path in test_paths:
        try:
            if path.exists():
                list(path.iterdir())
        except PermissionError:
            logger.debug(f"Brak dostępu do {path} - FDA nie nadane")
            return False

    return True


def open_fda_preferences() -> None:
    """Otwórz System Preferences -> Privacy -> Full Disk Access."""
    subprocess.run(
        [
            "open",
            "x-apple.systempreferences:com.apple.preference.security?Privacy_AllFiles",
        ]
    )


def check_volume_access(volume_path: Path) -> bool:
    """Sprawdź dostęp do konkretnego volumenu.

    Args:
        volume_path: Ścieżka do volumenu (np. /Volumes/LS-P1)

    Returns:
        True jeśli ma dostęp do odczytu
    """
    try:
        if volume_path.exists():
            list(volume_path.iterdir())
            return True
    except PermissionError:
        return False
    return False



