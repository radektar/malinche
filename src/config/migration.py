"""Migration utilities for upgrading from old configuration format."""

import json
import os
import shutil
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
    malinche_config_dir = new_config_path.parent
    transrec_config_dir = Path.home() / "Library" / "Application Support" / "Transrec"

    def _migrate_transrec_assets(settings: UserSettings) -> None:
        """Move legacy Transrec binaries/models to Malinche directory once."""
        if settings.transrec_migrated:
            return

        moved_any = False
        for subdir in ("bin", "models"):
            src_dir = transrec_config_dir / subdir
            dst_dir = malinche_config_dir / subdir
            if not src_dir.exists() or not src_dir.is_dir():
                continue

            dst_dir.mkdir(parents=True, exist_ok=True)
            for src_item in src_dir.iterdir():
                if src_item.is_dir():
                    # Keep migration simple and explicit for expected flat directories.
                    continue

                dst_item = dst_dir / src_item.name
                try:
                    if not dst_item.exists():
                        shutil.move(str(src_item), str(dst_item))
                        moved_any = True
                        _get_logger().info(
                            "Migrated %s from Transrec to Malinche", src_item
                        )
                    else:
                        backup_path = src_item.with_name(f"{src_item.name}.transrec.bak")
                        if not backup_path.exists():
                            shutil.move(str(src_item), str(backup_path))
                            moved_any = True
                            _get_logger().warning(
                                "Collision during Transrec migration for %s; moved to %s",
                                dst_item,
                                backup_path,
                            )
                except Exception as error:
                    _get_logger().warning(
                        "Could not migrate legacy asset %s: %s", src_item, error
                    )

            # Remove empty legacy folders after migration.
            try:
                if src_dir.exists() and not any(src_dir.iterdir()):
                    src_dir.rmdir()
            except OSError:
                pass

        settings.transrec_migrated = True
        settings.save()
        if moved_any:
            _get_logger().info("✓ Legacy Transrec assets migration completed")
    
    # If new config (Malinche) exists, load and migrate any lingering legacy assets.
    if new_config_path.exists():
        settings = UserSettings.load()
        _migrate_transrec_assets(settings)
        return UserSettings.load()
    
    # Check for Transrec config (previous v2.0.0 format)
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
            
            # Optionally migrate remaining files from legacy folder.
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
            _migrate_transrec_assets(new_settings)
            return UserSettings.load()
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

