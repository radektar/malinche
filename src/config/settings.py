"""User settings management."""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from src.config.defaults import defaults


@dataclass
class UserSettings:
    """Ustawienia użytkownika (persystentne w JSON)."""

    # Źródła nagrań
    watch_mode: str = defaults.WATCH_MODE
    watched_volumes: List[str] = field(default_factory=list)

    # Ścieżki
    output_dir: Path = field(default_factory=lambda: defaults.DEFAULT_OUTPUT_DIR)

    # Transkrypcja
    language: str = defaults.DEFAULT_LANGUAGE
    whisper_model: str = defaults.DEFAULT_WHISPER_MODEL

    # AI (PRO)
    enable_ai_summaries: bool = defaults.DEFAULT_ENABLE_AI_SUMMARIES
    ai_api_key: Optional[str] = None

    # UI
    show_notifications: bool = defaults.DEFAULT_SHOW_NOTIFICATIONS
    start_at_login: bool = defaults.DEFAULT_START_AT_LOGIN

    # Stan wizarda
    setup_completed: bool = defaults.DEFAULT_SETUP_COMPLETED

    def __post_init__(self) -> None:
        """Normalize types after init (e.g., JSON-loaded values)."""
        if isinstance(self.output_dir, str):
            # Path.resolve() may map /tmp → /private/tmp on macOS; tests allow this.
            self.output_dir = Path(self.output_dir).expanduser().resolve()

    @classmethod
    def load(cls) -> "UserSettings":
        """Wczytaj ustawienia z pliku JSON."""
        config_path = cls.config_path()
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return cls(**data)
            except (json.JSONDecodeError, TypeError):
                pass
        return cls()

    def save(self) -> None:
        """Zapisz ustawienia do pliku JSON."""
        config_path = self.config_path()
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    def to_dict(self) -> dict:
        """Serialize settings to JSON-friendly dict."""
        return {
            "watch_mode": self.watch_mode,
            "watched_volumes": list(self.watched_volumes),
            "output_dir": str(self.output_dir),
            "language": self.language,
            "whisper_model": self.whisper_model,
            "enable_ai_summaries": self.enable_ai_summaries,
            "ai_api_key": self.ai_api_key,
            "show_notifications": self.show_notifications,
            "start_at_login": self.start_at_login,
            "setup_completed": self.setup_completed,
        }

    @staticmethod
    def config_path() -> Path:
        """Zwróć ścieżkę do pliku konfiguracji."""
        # Compute dynamically so tests can monkeypatch Path.home()
        return (
            Path.home()
            / "Library"
            / "Application Support"
            / "Transrec"
            / "config.json"
        )

    # Backward-compatibility alias used by migration/older code.
    @classmethod
    def _config_path(cls) -> Path:
        """Backward compatible alias for config_path()."""
        return cls.config_path()

    def ensure_directories(self) -> None:
        """Ensure output directory exists."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
