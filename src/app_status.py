"""Application status management for Malinche."""

import threading
from enum import Enum
from typing import Optional


class AppStatus(Enum):
    """Application status states."""

    IDLE = "idle"
    SCANNING = "scanning"
    TRANSCRIBING = "transcribing"
    ERROR = "error"


class AppState:
    """Thread-safe application state container.

    Attributes:
        status: Current application status
        current_file: Name of file currently being transcribed (if any)
        error_message: Last error message (if status is ERROR)
    """

    def __init__(self):
        """Initialize application state."""
        self._lock = threading.Lock()
        self._status = AppStatus.IDLE
        self._current_file: Optional[str] = None
        self._error_message: Optional[str] = None

    @property
    def status(self) -> AppStatus:
        """Get current status."""
        with self._lock:
            return self._status

    @status.setter
    def status(self, value: AppStatus) -> None:
        """Set current status."""
        with self._lock:
            self._status = value

    @property
    def current_file(self) -> Optional[str]:
        """Get current file being transcribed."""
        with self._lock:
            return self._current_file

    @current_file.setter
    def current_file(self, value: Optional[str]) -> None:
        """Set current file being transcribed."""
        with self._lock:
            self._current_file = value

    @property
    def error_message(self) -> Optional[str]:
        """Get last error message."""
        with self._lock:
            return self._error_message

    @error_message.setter
    def error_message(self, value: Optional[str]) -> None:
        """Set last error message."""
        with self._lock:
            self._error_message = value

    def get_status_string(self) -> str:
        """Get human-readable status string.

        Returns:
            Formatted status string for UI display
        """
        with self._lock:
            if self._status == AppStatus.IDLE:
                return "Oczekiwanie na recorder..."
            elif self._status == AppStatus.SCANNING:
                return "Skanowanie recordera..."
            elif self._status == AppStatus.TRANSCRIBING:
                if self._current_file:
                    return f"Przetwarzam: {self._current_file}"
                return "Przetwarzanie..."
            elif self._status == AppStatus.ERROR:
                if self._error_message:
                    return f"Błąd: {self._error_message}"
                return "Błąd"
            return "Nieznany status"

