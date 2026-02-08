"""Migration utilities for upgrading from old configuration format."""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any

from src.config.settings import UserSettings
from src.config.defaults import defaults


def _get_logger():
    """Lazy import logger to avoid circular imports."""
    from src.logger import logger
    return logger


def migrate_from_old_config() -> Optional[UserSettings]:
    """Migrate settings from old configuration format.
    
    This function reads the old state file (~/.olympus_transcriber_state.json)
    and environment variables, then creates a new UserSettings instance.
    
    Returns:
        UserSettings instance if migration successful, None otherwise
    """
    old_state_file = Path.home() / ".olympus_transcriber_state.json"
    old_config = {}
    
    # Try to read old state file
    if old_state_file.exists():
        try:
            with open(old_state_file, "r", encoding="utf-8") as f:
                old_config = json.load(f)
            _get_logger().info(f"Found old state file: {old_state_file}")
        except Exception as e:
            _get_logger().warning(f"Could not read old state file: {e}")
    
    # Create new settings with defaults
    new_settings = UserSettings()
    
    # Migrate output directory from environment or old config
    env_dir = os.getenv("MALINCHE_TRANSCRIBE_DIR") or os.getenv("OLYMPUS_TRANSCRIBE_DIR")
    if env_dir:
        new_settings.output_dir = Path(env_dir).expanduser().resolve()
        _get_logger().info(f"Migrated output_dir from env: {new_settings.output_dir}")
    elif old_config.get("transcribe_dir"):
        new_settings.output_dir = Path(old_config["transcribe_dir"]).expanduser().resolve()
        _get_logger().info(f"Migrated output_dir from old config: {new_settings.output_dir}")
    
    # Migrate language setting
    if old_config.get("language"):
        new_settings.language = old_config["language"]
    
    # Migrate whisper model
    if old_config.get("whisper_model"):
        new_settings.whisper_model = old_config["whisper_model"]
    
    # Migrate AI settings (if API key exists)
    ai_api_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY")
    if ai_api_key:
        new_settings.enable_ai_summaries = True
        new_settings.ai_api_key = ai_api_key
        _get_logger().info("Migrated AI API key from environment")
    
    # Migrate watched volumes from old RECORDER_NAMES
    # Old config used hardcoded ["LS-P1", "OLYMPUS", "RECORDER"]
    # We'll set watch_mode to "specific" and add these volumes
    old_recorder_names = old_config.get("recorder_names", ["LS-P1", "OLYMPUS", "RECORDER"])
    if old_recorder_names:
        new_settings.watch_mode = "specific"
        new_settings.watched_volumes = old_recorder_names
        _get_logger().info(f"Migrated watched volumes: {new_settings.watched_volumes}")
    
    # Mark setup as completed if we have any migrated settings
    if old_config or env_dir:
        new_settings.setup_completed = True
        _get_logger().info("Marked setup as completed (migrated from old config)")
    
    return new_settings


def perform_migration_if_needed() -> UserSettings:
    """Perform migration if new config doesn't exist but old config does.
    
    Returns:
        UserSettings instance (either migrated or loaded from new config)
    """
    new_config_path = UserSettings.config_path()
    
    # If new config (Malinche) exists, just load it
    if new_config_path.exists():
        return UserSettings.load()
    
    # Check for Transrec config (previous v2.0.0 format)
    transrec_config_dir = Path.home() / "Library" / "Application Support" / "Transrec"
    transrec_config_path = transrec_config_dir / "config.json"
    
    if transrec_config_path.exists():
        _get_logger().info("Transrec configuration detected, migrating to Malinche...")
        try:
            # Load from Transrec
            with open(transrec_config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Create new settings and save to Malinche path
            new_settings = UserSettings(**data)
            new_settings.save()
            
            # Optionally migrate bin/models if they exist
            import shutil
            for sub in ["bin", "models", "state.json"]:
                old_path = transrec_config_dir / sub
                new_path = new_config_path.parent / sub
                if old_path.exists() and not new_path.exists():
                    try:
                        if old_path.is_dir():
                            shutil.copytree(old_path, new_path)
                        else:
                            shutil.copy2(old_path, new_path)
                        _get_logger().info(f"Migrated {sub} from Transrec to Malinche")
                    except Exception as e:
                        _get_logger().warning(f"Could not migrate {sub}: {e}")
            
            _get_logger().info("✓ Migration from Transrec completed")
            return new_settings
        except Exception as e:
            _get_logger().error(f"Migration from Transrec failed: {e}")

    # Check if old config (v1.x format) exists
    old_state_file = Path.home() / ".olympus_transcriber_state.json"
    env_dir = os.getenv("OLYMPUS_TRANSCRIBE_DIR") or os.getenv("MALINCHE_TRANSCRIBE_DIR")
    
    if old_state_file.exists() or env_dir:
        _get_logger().info("Old configuration detected, performing migration...")
        migrated = migrate_from_old_config()
        
        if migrated:
            # Save migrated settings
            migrated.save()
            _get_logger().info("✓ Migration completed successfully")
            return migrated
    
    # No old config, return defaults
    return UserSettings()

