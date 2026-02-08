"""Configuration module for Malinche (backward compatible wrapper)."""

import os
import shutil
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from src.config.config import Config

from src.config.settings import UserSettings
from src.config.defaults import defaults


@dataclass
class Config:
    """Backward-compatible configuration wrapper for Malinche.
    
    This class maintains the old Config interface while using UserSettings
    internally. This allows existing code to continue working while we
    transition to the new configuration system.
    
    Attributes:
        RECORDER_NAMES: List of possible volume names (from watched_volumes or defaults)
        TRANSCRIBE_DIR: Directory where transcriptions are saved (from output_dir)
        STATE_FILE: JSON file tracking last sync time (legacy)
        LOG_DIR: Directory for application logs
        LOG_FILE: Path to main log file
        WHISPER_MODEL: Whisper model size (from whisper_model)
        WHISPER_LANGUAGE: Language code for transcription (from language)
        WHISPER_DEVICE: Device to use (cpu or auto-detect)
        WHISPER_CPP_PATH: Path to whisper.cpp binary executable
        WHISPER_CPP_MODELS_DIR: Directory containing whisper.cpp models
        TRANSCRIPTION_TIMEOUT: Maximum time allowed for transcription (60 minutes)
        PERIODIC_CHECK_INTERVAL: Fallback check interval (seconds)
        MOUNT_MONITOR_DELAY: Wait time after mount detection (seconds)
        AUDIO_EXTENSIONS: Supported audio file formats
        ENABLE_SUMMARIZATION: Whether to generate summaries using LLM (from enable_ai_summaries)
        LLM_PROVIDER: LLM provider name (claude, openai, ollama)
        LLM_MODEL: Model name for the selected provider
        LLM_API_KEY: API key for LLM provider (from ai_api_key)
        SUMMARY_MAX_WORDS: Maximum words in generated summary
        TITLE_MAX_LENGTH: Maximum length for generated title (characters)
        DELETE_TEMP_TXT: Whether to delete temporary TXT files after MD creation
        LOCAL_RECORDINGS_DIR: Local staging directory for copied recorder files
    """
    
    # Recorder detection
    RECORDER_NAMES: List[str] = None
    
    # Directories
    TRANSCRIBE_DIR: Path = None
    LOG_DIR: Path = None
    LOCAL_RECORDINGS_DIR: Path = None  # Local staging area for recorder files
    PROCESS_LOCK_FILE: Path = None  # Lock file preventing overlapping runs
    
    # Files
    STATE_FILE: Path = None
    LOG_FILE: Path = None
    
    # Whisper configuration
    WHISPER_MODEL: str = "small"  # Balanced speed/accuracy: tiny, base, small, medium, large
    WHISPER_LANGUAGE: str = "pl"  # Polish default, can be "en" or None for auto-detect
    WHISPER_DEVICE: str = "cpu"  # Use CPU (whisper.cpp handles Core ML acceleration)
    WHISPER_CPP_PATH: Path = None  # Path to whisper.cpp binary
    WHISPER_CPP_MODELS_DIR: Path = None  # Path to whisper.cpp models directory
    FFMPEG_PATH: Path = None  # Path to ffmpeg binary (Faza 2)
    
    # Timeouts and intervals (seconds)
    TRANSCRIPTION_TIMEOUT: int = 3600  # 60 minutes (increased from 30)
    PERIODIC_CHECK_INTERVAL: int = 30  # 30 seconds
    MOUNT_MONITOR_DELAY: int = 1  # 1 second
    
    # Audio formats
    AUDIO_EXTENSIONS: set = None
    
    # LLM/Summarization configuration
    ENABLE_SUMMARIZATION: bool = True
    LLM_PROVIDER: str = "claude"
    LLM_MODEL: str = "claude-3-haiku-20240307"
    LLM_API_KEY: Optional[str] = None
    SUMMARY_MAX_WORDS: int = 200
    TITLE_MAX_LENGTH: int = 60
    DELETE_TEMP_TXT: bool = True

    # Tagging configuration
    ENABLE_LLM_TAGGING: bool = True
    MAX_TAGS_PER_NOTE: int = 6
    MAX_EXISTING_TAGS_IN_PROMPT: int = 150
    MAX_TAGGER_SUMMARY_CHARS: int = 3000
    MAX_TAGGER_TRANSCRIPT_CHARS: int = 1500
    
    # Markdown template
    MD_TEMPLATE: str = """---
title: "{title}"
date: {date}
recording_date: {recording_date}
source: {source_file}
duration: {duration}
tags: [{tags}]
---

{summary}

## Transkrypcja

{transcript}
"""
    
    def __post_init__(self):
        """Initialize default values after dataclass initialization.
        
        This method loads UserSettings and maps values to the old Config interface
        for backward compatibility.
        
        Note: Migration should be performed explicitly before creating Config instances
        (e.g., in main() or app startup). This ensures deterministic behavior and
        prevents side effects during initialization.
        """
        # Load user settings (migration should have been performed already)
        # This makes Config deterministic and testable
        self._user_settings = UserSettings.load()
        
        # Map UserSettings to old Config attributes
        if self.RECORDER_NAMES is None:
            # Use watched_volumes if in specific mode, otherwise use defaults
            if self._user_settings.watch_mode == "specific" and self._user_settings.watched_volumes:
                self.RECORDER_NAMES = self._user_settings.watched_volumes
            else:
                # Legacy default for backward compatibility
                self.RECORDER_NAMES = ["LS-P1", "OLYMPUS", "RECORDER"]
        
        if self.TRANSCRIBE_DIR is None:
            # UserSettings stores output_dir as str (JSON), but legacy Config expects Path
            out_dir = self._user_settings.output_dir
            if isinstance(out_dir, Path):
                self.TRANSCRIBE_DIR = out_dir
            else:
                self.TRANSCRIBE_DIR = Path(str(out_dir)).expanduser()
        
        if self.LOG_DIR is None:
            self.LOG_DIR = Path.home() / "Library" / "Logs"
        
        if self.STATE_FILE is None:
            # Keep legacy state file path for backward compatibility
            self.STATE_FILE = Path.home() / ".olympus_transcriber_state.json"
        
        if self.LOG_FILE is None:
            self.LOG_FILE = self.LOG_DIR / "olympus_transcriber.log"
        
        if self.LOCAL_RECORDINGS_DIR is None:
            # Default to ~/.olympus_transcriber/recordings for staging
            self.LOCAL_RECORDINGS_DIR = Path.home() / ".olympus_transcriber" / "recordings"
        
        if self.PROCESS_LOCK_FILE is None:
            self.PROCESS_LOCK_FILE = Path.home() / ".olympus_transcriber" / "transcriber.lock"
        
        if self.AUDIO_EXTENSIONS is None:
            self.AUDIO_EXTENSIONS = defaults.AUDIO_EXTENSIONS
        
        # Map whisper settings from UserSettings
        # Always use UserSettings values (they are the source of truth)
        self.WHISPER_MODEL = self._user_settings.whisper_model
        self.WHISPER_LANGUAGE = self._user_settings.language or "pl"
        
        if self.WHISPER_CPP_PATH is None:
            # Nowa lokalizacja: ~/Library/Application Support/Malinche/bin/
            support_dir = (
                Path.home() / "Library" / "Application Support" / "Malinche"
            )
            new_whisper_path = support_dir / "bin" / "whisper-cli"
            
            # Sprawdź nową lokalizację (Faza 2)
            if new_whisper_path.exists():
                self.WHISPER_CPP_PATH = new_whisper_path
            else:
                # Fallback do starych lokalizacji (backward compatibility)
                whisper_base = Path.home() / "whisper.cpp"
                if (whisper_base / "build" / "bin" / "whisper-cli").exists():
                    self.WHISPER_CPP_PATH = (
                        whisper_base / "build" / "bin" / "whisper-cli"
                    )
                elif (whisper_base / "build" / "bin" / "main").exists():
                    self.WHISPER_CPP_PATH = whisper_base / "build" / "bin" / "main"
                elif (whisper_base / "main").exists():
                    self.WHISPER_CPP_PATH = whisper_base / "main"
                else:
                    # Default - nowa lokalizacja (będzie pobrana przez downloader)
                    self.WHISPER_CPP_PATH = new_whisper_path
        
        if self.WHISPER_CPP_MODELS_DIR is None:
            # Nowa lokalizacja: ~/Library/Application Support/Transrec/models/
            support_dir = (
                Path.home() / "Library" / "Application Support" / "Transrec"
            )
            new_models_dir = support_dir / "models"
            
            # Sprawdź nową lokalizację
            if new_models_dir.exists():
                self.WHISPER_CPP_MODELS_DIR = new_models_dir
            else:
                # Fallback do starej lokalizacji
                self.WHISPER_CPP_MODELS_DIR = Path.home() / "whisper.cpp" / "models"
        
        if self.FFMPEG_PATH is None:
            # Nowa lokalizacja: ~/Library/Application Support/Transrec/bin/ffmpeg
            support_dir = (
                Path.home() / "Library" / "Application Support" / "Transrec"
            )
            new_ffmpeg_path = support_dir / "bin" / "ffmpeg"
            
            # Sprawdź nową lokalizację (Faza 2)
            if new_ffmpeg_path.exists():
                self.FFMPEG_PATH = new_ffmpeg_path
            else:
                # Fallback do systemowego ffmpeg (shutil.which)
                system_ffmpeg = shutil.which("ffmpeg")
                if system_ffmpeg:
                    self.FFMPEG_PATH = Path(system_ffmpeg)
                else:
                    # Default - nowa lokalizacja (będzie pobrana przez downloader)
                    self.FFMPEG_PATH = new_ffmpeg_path
        
        # Load LLM API key from UserSettings only
        # Environment variables should be migrated to UserSettings via perform_migration_if_needed()
        # This ensures deterministic behavior and prevents runtime ENV reading
        if self.LLM_API_KEY is None:
            if self._user_settings.ai_api_key:
                self.LLM_API_KEY = self._user_settings.ai_api_key
            elif self.LLM_PROVIDER == "ollama":
                # Ollama doesn't require API key, but we can use base URL (default)
                # This is a default value, not reading from ENV
                self.LLM_API_KEY = "http://localhost:11434"

        # Map AI settings from UserSettings, with backward-compatible defaults.
        #
        # If enable_ai_summaries is True in UserSettings, enable summarization (if API key available).
        # If enable_ai_summaries is False, don't enable summarization even if API key exists.
        # Exception: Ollama always enables summarization (no API key required).
        enable_summarization = bool(self._user_settings.enable_ai_summaries)
        
        # Only enable summarization if user explicitly enabled it in settings
        # If enable_ai_summaries is False, summarization stays False regardless of API key
        if enable_summarization:
            if self.LLM_PROVIDER == "ollama":
                enable_summarization = True
            elif self.LLM_PROVIDER != "ollama":
                # Disable summarization if API key is missing
                if not self.LLM_API_KEY:
                    enable_summarization = False
        # else: enable_summarization is already False, keep it False

        self.ENABLE_SUMMARIZATION = enable_summarization

        # Tagging requires summarization to be enabled (shared LLM availability).
        if self.ENABLE_LLM_TAGGING and not self.ENABLE_SUMMARIZATION:
            self.ENABLE_LLM_TAGGING = False
    
    def ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        self.TRANSCRIBE_DIR.mkdir(parents=True, exist_ok=True)
        self.LOG_DIR.mkdir(parents=True, exist_ok=True)
        self.LOCAL_RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)


# Global configuration instance
# This will be initialized after migration in main() or app startup
# For backward compatibility, we create it lazily on first access
_config_instance: Optional[Config] = None


def get_config() -> Config:
    """Get the global Config instance, creating it if necessary.
    
    Note: In production, migration should be performed before calling this.
    For testing, you can set _config_instance directly.
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance


# Backward compatibility: expose config as a property-like object
# This allows existing code using `from src.config import config` to continue working
class _ConfigProxy:
    """Proxy for global config instance to maintain backward compatibility."""
    
    def __getattr__(self, name: str):
        return getattr(get_config(), name)
    
    def __setattr__(self, name: str, value):
        # Allow setting attributes on the actual config instance
        setattr(get_config(), name, value)
    
    def ensure_directories(self) -> None:
        """Forward ensure_directories call to config instance."""
        get_config().ensure_directories()


config = _ConfigProxy()

