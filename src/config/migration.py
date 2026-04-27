"""Legacy wrapper for bootstrap migration API."""

from typing import Optional

from src.bootstrap import ensure_ready, migrate_from_old_config as _bootstrap_migrate
from src.config.settings import UserSettings


def migrate_from_old_config() -> Optional[UserSettings]:
    """Backward-compatible wrapper for old migration API."""
    return _bootstrap_migrate()


def perform_migration_if_needed() -> UserSettings:
    """Backward-compatible wrapper for bootstrap initialization."""
    return ensure_ready()

