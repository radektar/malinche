"""User configuration module."""

# Import UserSettings and defaults from this package
from src.config.settings import UserSettings
from src.config.defaults import (
    DEFAULT_OUTPUT_DIR,
    DEFAULT_WATCH_MODE,
    DEFAULT_LANGUAGE,
    DEFAULT_MODEL,
    SUPPORTED_LANGUAGES,
    SUPPORTED_MODELS,
    WATCH_MODES,
    SYSTEM_VOLUMES,
    CONFIG_DIR,
    CONFIG_FILE,
)

# Import Config and config from config.py module
# Using normal import instead of dynamic importlib to ensure single module instance
# This prevents issues with module reloading in tests and ensures deterministic behavior
from src.config.config import Config, config

__all__ = [
    "UserSettings",
    "Config",
    "config",
    "DEFAULT_OUTPUT_DIR",
    "DEFAULT_WATCH_MODE",
    "DEFAULT_LANGUAGE",
    "DEFAULT_MODEL",
    "SUPPORTED_LANGUAGES",
    "SUPPORTED_MODELS",
    "WATCH_MODES",
    "SYSTEM_VOLUMES",
    "CONFIG_DIR",
    "CONFIG_FILE",
]
