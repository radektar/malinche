"""Tests for file monitor module."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from src.file_monitor import FileMonitor
from src.config.settings import UserSettings
from src.config.defaults import defaults


@pytest.fixture
def mock_callback():
    """Create a mock callback function."""
    return Mock()


def test_file_monitor_initialization(mock_callback):
    """Test FileMonitor initializes correctly."""
    monitor = FileMonitor(mock_callback)
    
    assert monitor.callback == mock_callback
    assert monitor.observer is None
    assert not monitor.is_monitoring


def test_file_monitor_start_without_fsevents(mock_callback):
    """Test start when FSEvents is not available."""
    with patch('src.file_monitor.FSEVENTS_AVAILABLE', False):
        monitor = FileMonitor(mock_callback)
        monitor.start()
        
        assert not monitor.is_monitoring


@patch('src.file_monitor.FSEVENTS_AVAILABLE', True)
@patch('src.file_monitor.Observer')
@patch('src.file_monitor.Stream')
def test_file_monitor_start_success(mock_stream, mock_observer, mock_callback):
    """Test successful start of file monitor."""
    monitor = FileMonitor(mock_callback)
    
    mock_observer_instance = MagicMock()
    mock_observer.return_value = mock_observer_instance
    
    monitor.start()
    
    assert monitor.is_monitoring
    mock_observer_instance.start.assert_called_once()


@patch('src.file_monitor.FSEVENTS_AVAILABLE', True)
def test_file_monitor_start_already_running(mock_callback):
    """Test start when already monitoring."""
    monitor = FileMonitor(mock_callback)
    monitor.is_monitoring = True
    
    with patch('src.file_monitor.Observer'):
        monitor.start()
        # Should not create new observer


def test_file_monitor_stop(mock_callback):
    """Test stop method."""
    monitor = FileMonitor(mock_callback)
    
    mock_observer = MagicMock()
    monitor.observer = mock_observer
    monitor.is_monitoring = True
    
    monitor.stop()
    
    mock_observer.stop.assert_called_once()
    mock_observer.join.assert_called_once()
    assert not monitor.is_monitoring


def test_file_monitor_stop_no_observer(mock_callback):
    """Test stop when no observer exists."""
    monitor = FileMonitor(mock_callback)
    monitor.observer = None
    
    # Should not raise any errors
    monitor.stop()


@patch('src.file_monitor.FSEVENTS_AVAILABLE', True)
@patch('src.file_monitor.Observer')
@patch('src.file_monitor.Stream')
def test_file_monitor_ignores_system_directories(mock_stream, mock_observer, mock_callback):
    """Test that system directories like .Spotlight-V100 are ignored."""
    from src.file_monitor import FileMonitor
    import time
    
    monitor = FileMonitor(mock_callback)
    monitor._last_trigger_time = 0.0  # Reset debounce timer
    
    mock_observer_instance = MagicMock()
    mock_observer.return_value = mock_observer_instance
    
    # Capture the on_change callback
    on_change_callback = None
    def capture_stream(callback, path, **kwargs):
        nonlocal on_change_callback
        on_change_callback = callback
        return MagicMock()
    
    mock_stream.side_effect = capture_stream
    
    monitor.start()
    
    # Simulate FSEvents callback with system directory path
    if on_change_callback:
        on_change_callback("/Volumes/LS-P1/.Spotlight-V100/Store-V2", 0)
        time.sleep(0.1)  # Small delay to ensure callback processing
    
    # Callback should not have been called
    mock_callback.assert_not_called()


@patch('src.file_monitor.FSEVENTS_AVAILABLE', True)
@patch('src.file_monitor.Observer')
@patch('src.file_monitor.Stream')
@patch('src.file_monitor.time.sleep')
@patch('src.file_monitor.UserSettings')
def test_file_monitor_triggers_on_valid_path(mock_user_settings, mock_sleep, mock_stream, mock_observer, mock_callback, tmp_path):
    """Test that valid recorder paths trigger the callback."""
    from src.file_monitor import FileMonitor
    from src.config.settings import UserSettings
    import time
    
    # Create mock volume structure
    volumes_dir = tmp_path / "Volumes"
    volumes_dir.mkdir()
    ls_p1_volume = volumes_dir / "LS-P1"
    ls_p1_volume.mkdir()
    (ls_p1_volume / "Folder").mkdir()
    (ls_p1_volume / "Folder" / "audio.mp3").touch()
    
    # Mock UserSettings to return auto mode
    mock_settings = UserSettings()
    mock_settings.watch_mode = "auto"
    mock_user_settings.load.return_value = mock_settings
    
    # Mock Path("/Volumes") to return our test volumes directory
    original_path = Path
    def mock_path_constructor(path_str):
        if path_str == "/Volumes":
            return volumes_dir
        return original_path(path_str)
    
    monitor = FileMonitor(mock_callback)
    monitor._last_trigger_time = 0.0  # Reset debounce timer
    
    mock_observer_instance = MagicMock()
    mock_observer.return_value = mock_observer_instance
    
    # Capture the on_change callback
    on_change_callback = None
    def capture_stream(callback, path, **kwargs):
        nonlocal on_change_callback
        on_change_callback = callback
        return MagicMock()
    
    mock_stream.side_effect = capture_stream
    
    # Patch Path("/Volumes") in file_monitor module
    with patch('src.file_monitor.Path', side_effect=mock_path_constructor):
        monitor.start()
        
        # Simulate FSEvents callback with valid audio file path
        if on_change_callback:
            on_change_callback(str(ls_p1_volume / "Folder" / "audio.mp3"), 0)
            time.sleep(0.1)  # Small delay to ensure callback processing
        
        # Callback should have been called
        mock_callback.assert_called_once()


@patch('src.file_monitor.FSEVENTS_AVAILABLE', True)
@patch('src.file_monitor.Observer')
@patch('src.file_monitor.Stream')
def test_file_monitor_ignores_non_recorder_paths(mock_stream, mock_observer, mock_callback):
    """Test that paths not under recorder volumes are ignored."""
    from src.file_monitor import FileMonitor
    import time
    
    monitor = FileMonitor(mock_callback)
    monitor._last_trigger_time = 0.0  # Reset debounce timer
    
    mock_observer_instance = MagicMock()
    mock_observer.return_value = mock_observer_instance
    
    # Capture the on_change callback
    on_change_callback = None
    def capture_stream(callback, path, **kwargs):
        nonlocal on_change_callback
        on_change_callback = callback
        return MagicMock()
    
    mock_stream.side_effect = capture_stream
    
    monitor.start()
    
    # Simulate FSEvents callback with path not under recorder
    if on_change_callback:
        on_change_callback("/Volumes/OtherDisk/file.txt", 0)
        time.sleep(0.1)  # Small delay to ensure callback processing
    
    # Callback should not have been called
    mock_callback.assert_not_called()


class TestFileMonitorVolumeDetection:
    """Test suite for universal volume detection (v2.0.0)."""
    
    def test_should_process_volume_auto_mode_with_audio(self, tmp_path):
        """Test auto mode detects volumes with audio files."""
        monitor = FileMonitor(Mock())
        
        # Create temp directory with audio file
        test_volume = tmp_path / "USB_DRIVE"
        test_volume.mkdir()
        (test_volume / "audio.mp3").touch()
        
        settings = UserSettings()
        settings.watch_mode = "auto"
        
        result = monitor._should_process_volume(test_volume, settings)
        assert result is True
    
    def test_should_process_volume_auto_mode_no_audio(self, tmp_path):
        """Test auto mode ignores volumes without audio files."""
        monitor = FileMonitor(Mock())
        
        # Create temp directory without audio files
        test_volume = tmp_path / "EMPTY_DRIVE"
        test_volume.mkdir()
        (test_volume / "readme.txt").touch()
        
        settings = UserSettings()
        settings.watch_mode = "auto"
        
        result = monitor._should_process_volume(test_volume, settings)
        assert result is False
    
    def test_should_process_volume_specific_mode_in_list(self, tmp_path):
        """Test specific mode processes volumes in watched list."""
        monitor = FileMonitor(Mock())
        
        test_volume = tmp_path / "SD_CARD"
        test_volume.mkdir()
        
        settings = UserSettings()
        settings.watch_mode = "specific"
        settings.watched_volumes = ["SD_CARD", "USB_DRIVE"]
        
        result = monitor._should_process_volume(test_volume, settings)
        assert result is True
    
    def test_should_process_volume_specific_mode_not_in_list(self, tmp_path):
        """Test specific mode ignores volumes not in watched list."""
        monitor = FileMonitor(Mock())
        
        test_volume = tmp_path / "OTHER_DRIVE"
        test_volume.mkdir()
        
        settings = UserSettings()
        settings.watch_mode = "specific"
        settings.watched_volumes = ["SD_CARD", "USB_DRIVE"]
        
        result = monitor._should_process_volume(test_volume, settings)
        assert result is False
    
    def test_should_process_volume_manual_mode(self, tmp_path):
        """Test manual mode never auto-processes."""
        monitor = FileMonitor(Mock())
        
        test_volume = tmp_path / "ANY_DRIVE"
        test_volume.mkdir()
        (test_volume / "audio.mp3").touch()
        
        settings = UserSettings()
        settings.watch_mode = "manual"
        
        result = monitor._should_process_volume(test_volume, settings)
        assert result is False
    
    def test_should_process_volume_ignores_system_volumes(self, tmp_path):
        """Test that system volumes are always ignored."""
        monitor = FileMonitor(Mock())
        
        # Test with system volume name
        test_volume = tmp_path / "Macintosh HD"
        test_volume.mkdir()
        (test_volume / "audio.mp3").touch()  # Even with audio
        
        settings = UserSettings()
        settings.watch_mode = "auto"
        
        result = monitor._should_process_volume(test_volume, settings)
        assert result is False
    
    def test_should_process_volume_unknown_mode(self, tmp_path, caplog):
        """Test that unknown watch mode defaults to False."""
        monitor = FileMonitor(Mock())
        
        test_volume = tmp_path / "TEST_DRIVE"
        test_volume.mkdir()
        
        settings = UserSettings()
        settings.watch_mode = "invalid_mode"
        
        result = monitor._should_process_volume(test_volume, settings)
        assert result is False
        assert "Unknown watch_mode" in caplog.text


class TestFileMonitorAudioDetection:
    """Test suite for audio file detection."""
    
    def test_has_audio_files_detects_mp3(self, tmp_path):
        """Test detection of .mp3 files."""
        monitor = FileMonitor(Mock())
        
        test_dir = tmp_path / "test"
        test_dir.mkdir()
        (test_dir / "audio.mp3").touch()
        
        result = monitor._has_audio_files(test_dir)
        assert result is True
    
    def test_has_audio_files_detects_wav(self, tmp_path):
        """Test detection of .wav files."""
        monitor = FileMonitor(Mock())
        
        test_dir = tmp_path / "test"
        test_dir.mkdir()
        (test_dir / "recording.wav").touch()
        
        result = monitor._has_audio_files(test_dir)
        assert result is True
    
    def test_has_audio_files_detects_m4a(self, tmp_path):
        """Test detection of .m4a files."""
        monitor = FileMonitor(Mock())
        
        test_dir = tmp_path / "test"
        test_dir.mkdir()
        (test_dir / "audio.m4a").touch()
        
        result = monitor._has_audio_files(test_dir)
        assert result is True
    
    def test_has_audio_files_detects_flac(self, tmp_path):
        """Test detection of .flac files."""
        monitor = FileMonitor(Mock())
        
        test_dir = tmp_path / "test"
        test_dir.mkdir()
        (test_dir / "audio.flac").touch()
        
        result = monitor._has_audio_files(test_dir)
        assert result is True
    
    def test_has_audio_files_detects_aac(self, tmp_path):
        """Test detection of .aac files."""
        monitor = FileMonitor(Mock())
        
        test_dir = tmp_path / "test"
        test_dir.mkdir()
        (test_dir / "audio.aac").touch()
        
        result = monitor._has_audio_files(test_dir)
        assert result is True
    
    def test_has_audio_files_detects_ogg(self, tmp_path):
        """Test detection of .ogg files."""
        monitor = FileMonitor(Mock())
        
        test_dir = tmp_path / "test"
        test_dir.mkdir()
        (test_dir / "audio.ogg").touch()
        
        result = monitor._has_audio_files(test_dir)
        assert result is True
    
    def test_has_audio_files_case_insensitive(self, tmp_path):
        """Test that audio detection is case-insensitive."""
        monitor = FileMonitor(Mock())
        
        test_dir = tmp_path / "test"
        test_dir.mkdir()
        (test_dir / "AUDIO.MP3").touch()  # Uppercase extension
        
        result = monitor._has_audio_files(test_dir)
        assert result is True
    
    def test_has_audio_files_ignores_non_audio(self, tmp_path):
        """Test that non-audio files are ignored."""
        monitor = FileMonitor(Mock())
        
        test_dir = tmp_path / "test"
        test_dir.mkdir()
        (test_dir / "document.txt").touch()
        (test_dir / "image.jpg").touch()
        (test_dir / "video.mp4").touch()
        
        result = monitor._has_audio_files(test_dir)
        assert result is False
    
    def test_has_audio_files_nested_directories(self, tmp_path):
        """Test detection in nested directories."""
        monitor = FileMonitor(Mock())
        
        test_dir = tmp_path / "test"
        test_dir.mkdir()
        (test_dir / "folder1" / "folder2").mkdir(parents=True)
        (test_dir / "folder1" / "folder2" / "audio.mp3").touch()
        
        result = monitor._has_audio_files(test_dir)
        assert result is True
    
    def test_has_audio_files_respects_max_depth(self, tmp_path):
        """Test that max_depth limits scanning depth."""
        monitor = FileMonitor(Mock())
        
        test_dir = tmp_path / "test"
        test_dir.mkdir()
        
        # Create file beyond max_depth (default is 3)
        deep_path = test_dir
        for i in range(5):  # 5 levels deep
            deep_path = deep_path / f"level{i}"
            deep_path.mkdir()
        (deep_path / "audio.mp3").touch()
        
        # Should not find it due to depth limit
        result = monitor._has_audio_files(test_dir, max_depth=3)
        assert result is False
        
        # Should find it with higher depth
        result = monitor._has_audio_files(test_dir, max_depth=6)
        assert result is True
    
    def test_has_audio_files_handles_permission_error(self, tmp_path, monkeypatch):
        """Test that permission errors are handled gracefully."""
        monitor = FileMonitor(Mock())
        
        test_dir = tmp_path / "test"
        test_dir.mkdir()
        
        # Mock Path.rglob to raise PermissionError when called on test_dir
        original_rglob = Path.rglob
        def mock_rglob(self, pattern):
            if self == test_dir:
                raise PermissionError("Access denied")
            return original_rglob(self, pattern)
        
        monkeypatch.setattr(Path, "rglob", mock_rglob)
        
        result = monitor._has_audio_files(test_dir)
        assert result is False
    
    def test_has_audio_files_empty_directory(self, tmp_path):
        """Test that empty directory returns False."""
        monitor = FileMonitor(Mock())
        
        test_dir = tmp_path / "test"
        test_dir.mkdir()
        
        result = monitor._has_audio_files(test_dir)
        assert result is False
    
    def test_has_audio_files_only_directories(self, tmp_path):
        """Test that directories without files return False."""
        monitor = FileMonitor(Mock())
        
        test_dir = tmp_path / "test"
        test_dir.mkdir()
        (test_dir / "subfolder").mkdir()
        
        result = monitor._has_audio_files(test_dir)
        assert result is False



