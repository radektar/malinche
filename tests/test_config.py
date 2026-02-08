"""Tests for configuration module."""

import pytest
from pathlib import Path
from src.config import Config


def test_config_initialization():
    """Test that Config initializes with default values."""
    config = Config()
    
    assert config.RECORDER_NAMES == ["LS-P1", "OLYMPUS", "RECORDER"]
    assert config.TRANSCRIPTION_TIMEOUT == 3600  # 60 minutes
    assert config.PERIODIC_CHECK_INTERVAL == 30
    assert config.MOUNT_MONITOR_DELAY == 1


def test_config_paths():
    """Test that Config creates proper paths."""
    config = Config()
    
    assert isinstance(config.TRANSCRIBE_DIR, Path)
    assert isinstance(config.LOG_DIR, Path)
    assert isinstance(config.LOCAL_RECORDINGS_DIR, Path)
    assert isinstance(config.STATE_FILE, Path)
    assert isinstance(config.LOG_FILE, Path)
    
    # Check paths contain expected components
    assert "11-Transcripts" in str(config.TRANSCRIBE_DIR) or "Transcriptions" in str(config.TRANSCRIBE_DIR)
    assert "Logs" in str(config.LOG_DIR)
    assert ".olympus_transcriber" in str(config.LOCAL_RECORDINGS_DIR)
    assert "recordings" in str(config.LOCAL_RECORDINGS_DIR)
    assert ".olympus_transcriber_state.json" in str(config.STATE_FILE)
    assert "olympus_transcriber.log" in str(config.LOG_FILE)


def test_config_audio_extensions():
    """Test that audio extensions are properly set."""
    config = Config()
    
    # Should include all supported audio formats
    assert config.AUDIO_EXTENSIONS == {".mp3", ".wav", ".m4a", ".wma", ".flac", ".aac", ".ogg"}


def test_config_whisper_cpp_paths():
    """Test that whisper.cpp paths are set."""
    config = Config()
    
    assert config.WHISPER_CPP_PATH is not None
    assert isinstance(config.WHISPER_CPP_PATH, Path)
    assert config.WHISPER_CPP_MODELS_DIR is not None
    assert isinstance(config.WHISPER_CPP_MODELS_DIR, Path)


def test_config_tagging_defaults(monkeypatch):
    """Tagging configuration should have sane defaults."""
    from src.config.settings import UserSettings
    
    # Mock UserSettings.load() to return settings with AI enabled
    mock_settings = UserSettings()
    mock_settings.enable_ai_summaries = True
    mock_settings.ai_api_key = "dummy-key"
    
    # Patch UserSettings.load() to return our mock settings
    monkeypatch.setattr(UserSettings, "load", classmethod(lambda cls: mock_settings))
    
    cfg = Config()

    assert cfg.ENABLE_LLM_TAGGING is True
    assert cfg.MAX_TAGS_PER_NOTE == 6
    assert cfg.MAX_EXISTING_TAGS_IN_PROMPT == 150
    assert cfg.MAX_TAGGER_SUMMARY_CHARS == 3000
    assert cfg.MAX_TAGGER_TRANSCRIPT_CHARS == 1500


def test_config_disables_tagging_when_summarization_off(monkeypatch):
    """Tagging should be disabled automatically if summarization is off."""
    from src.config.settings import UserSettings
    
    # Remove API key from environment
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    
    # Mock UserSettings.load() to return settings with AI disabled and no API key
    # Config now uses UserSettings.load() instead of perform_migration_if_needed()
    mock_settings = UserSettings()
    mock_settings.enable_ai_summaries = False
    mock_settings.ai_api_key = None
    
    # Patch UserSettings.load() to return our mock settings
    monkeypatch.setattr(UserSettings, "load", classmethod(lambda cls: mock_settings))
    
    from src.config import Config
    cfg = Config()

    # Even if API key exists in environment, summarization should be False
    # because enable_ai_summaries is False in UserSettings
    assert cfg.ENABLE_SUMMARIZATION is False
    assert cfg.ENABLE_LLM_TAGGING is False


def test_config_ensure_directories(tmp_path, monkeypatch):
    """Test that ensure_directories creates needed directories."""
    config = Config()
    
    # Override paths to use temp directory
    config.TRANSCRIBE_DIR = tmp_path / "transcriptions"
    config.LOG_DIR = tmp_path / "logs"
    config.LOCAL_RECORDINGS_DIR = tmp_path / "recordings"
    
    # Ensure they don't exist yet
    assert not config.TRANSCRIBE_DIR.exists()
    assert not config.LOG_DIR.exists()
    assert not config.LOCAL_RECORDINGS_DIR.exists()
    
    # Call ensure_directories
    config.ensure_directories()
    
    # Check they were created
    assert config.TRANSCRIBE_DIR.exists()
    assert config.LOG_DIR.exists()
    assert config.LOCAL_RECORDINGS_DIR.exists()





