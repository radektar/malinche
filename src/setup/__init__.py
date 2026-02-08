"""Setup utilities for Malinche."""

from src.setup.downloader import DependencyDownloader
from src.setup.errors import (
    DownloadError,
    ChecksumError,
    NetworkError,
    DiskSpaceError,
)
from src.setup.wizard import SetupWizard, WizardStep
from src.setup.permissions import (
    check_full_disk_access,
    open_fda_preferences,
    check_volume_access,
)

__all__ = [
    "DependencyDownloader",
    "DownloadError",
    "ChecksumError",
    "NetworkError",
    "DiskSpaceError",
    "SetupWizard",
    "WizardStep",
    "check_full_disk_access",
    "open_fda_preferences",
    "check_volume_access",
]

