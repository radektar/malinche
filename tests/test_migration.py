"""Tests for migration from old configuration (v2.0.0)."""

import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch, mock_open
from src.config.migration import migrate_from_old_config, perform_migration_if_needed
from src.config.settings import UserSettings


class TestMigration:
    """Test suite for configuration migration."""
    
    def test_migration_from_old_state_file(self, tmp_path, monkeypatch):
        """Test migration from old state file."""
        # Create old state file
        old_state_file = tmp_path / ".olympus_transcriber_state.json"
        old_state_data = {
            "last_sync": "2024-01-01T12:00:00",
            "transcribe_dir": str(tmp_path / "old_transcriptions"),
            "language": "en",
            "whisper_model": "medium",
            "recorder_names": ["LS-P1", "OLYMPUS"]
        }
        old_state_file.write_text(json.dumps(old_state_data))
        
        # Mock home directory
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        
        migrated = migrate_from_old_config()
        
        assert migrated is not None
        assert migrated.output_dir == tmp_path / "old_transcriptions"
        assert migrated.language == "en"
        assert migrated.whisper_model == "medium"
        assert migrated.watch_mode == "specific"
        assert migrated.watched_volumes == ["LS-P1", "OLYMPUS"]
        assert migrated.setup_completed is True
    
    def test_migration_from_environment_variable(self, tmp_path, monkeypatch):
        """Test migration from OLYMPUS_TRANSCRIBE_DIR environment variable."""
        test_dir = tmp_path / "env_transcriptions"
        test_dir.mkdir()
        
        monkeypatch.setenv("OLYMPUS_TRANSCRIBE_DIR", str(test_dir))
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        
        migrated = migrate_from_old_config()
        
        assert migrated is not None
        assert migrated.output_dir == test_dir
        assert migrated.setup_completed is True
    
    def test_migration_with_ai_api_key(self, tmp_path, monkeypatch):
        """Test migration includes AI API key from environment."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-key-123")
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        
        migrated = migrate_from_old_config()
        
        assert migrated is not None
        assert migrated.enable_ai_summaries is True
        assert migrated.ai_api_key == "sk-test-key-123"
    
    def test_migration_no_old_config(self, tmp_path, monkeypatch):
        """Test migration when no old config exists."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        
        migrated = migrate_from_old_config()
        
        # Should still return settings (with defaults)
        assert migrated is not None
        assert migrated.setup_completed is False  # Not completed if no old config
    
    def test_perform_migration_if_needed_new_config_exists(self, tmp_path, monkeypatch):
        """Test that migration is skipped if new config exists."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        
        # Create new config file
        new_config = UserSettings()
        new_config.watch_mode = "specific"
        new_config.watched_volumes = ["SD_CARD"]
        new_config.save()
        
        # Should load existing config, not migrate
        result = perform_migration_if_needed()
        assert result.watch_mode == "specific"
        assert result.watched_volumes == ["SD_CARD"]
    
    def test_perform_migration_if_needed_migrates_when_needed(self, tmp_path, monkeypatch):
        """Test that migration happens when new config doesn't exist."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        
        # Create old state file
        old_state_file = tmp_path / ".olympus_transcriber_state.json"
        old_state_data = {
            "transcribe_dir": str(tmp_path / "old_transcriptions"),
            "recorder_names": ["LS-P1"]
        }
        old_state_file.write_text(json.dumps(old_state_data))
        
        result = perform_migration_if_needed()
        
        # Should have migrated
        assert result.watch_mode == "specific"
        assert result.watched_volumes == ["LS-P1"]
        assert result.setup_completed is True
        
        # Should have saved migrated config
        config_path = tmp_path / "Library" / "Application Support" / "Malinche" / "config.json"
        assert config_path.exists()
    
    def test_perform_migration_if_needed_no_old_config(self, tmp_path, monkeypatch):
        """Test that defaults are used when no old config exists."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        
        result = perform_migration_if_needed()
        
        # Should use defaults
        assert result.watch_mode == "auto"
        assert result.setup_completed is False

