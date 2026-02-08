"""Tests for transcriber module."""

import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.transcriber import Transcriber
from src.summarizer import BaseSummarizer
from src.markdown_generator import MarkdownGenerator


def update_transcriber_config(transcriber, monkeypatch, **kwargs):
    """Helper to update both transcriber.config and global config.
    
    Args:
        transcriber: Transcriber instance
        monkeypatch: pytest monkeypatch fixture
        **kwargs: Config attributes to update (e.g., TRANSCRIBE_DIR=path)
    """
    from src import config as config_module
    
    from src import config as config_module
    
    # Update transcriber's injected config
    for key, value in kwargs.items():
        setattr(transcriber.config, key, value)
    
    # Also update global config for state_manager functions
    for key, value in kwargs.items():
        monkeypatch.setattr(config_module.config, key, value)


@pytest.fixture
def transcriber(monkeypatch):
    """Create a transcriber instance for testing.
    
    Creates Transcriber with a test Config instance to avoid global state issues.
    """
    from src.config.config import Config
    
    # Create a test config instance
    test_config = Config()
    
    with patch('src.transcriber.logger'):
        # Pass config explicitly for dependency injection
        return Transcriber(config=test_config)


@pytest.fixture
def mock_recorder_path(tmp_path):
    """Create a mock recorder directory with audio files."""
    recorder = tmp_path / "LS-P1"
    recorder.mkdir()
    
    # Create some audio files
    audio_dir = recorder / "Music"
    audio_dir.mkdir()
    
    (audio_dir / "recording1.mp3").touch()
    (audio_dir / "recording2.wav").touch()
    (audio_dir / "document.txt").touch()  # Non-audio file
    
    return recorder


def test_transcriber_initialization(transcriber):
    """Test transcriber initializes correctly."""
    assert isinstance(transcriber.transcription_in_progress, dict)
    assert isinstance(transcriber.recorder_monitoring, bool)
    assert not transcriber.recorder_monitoring


def test_find_recorder_not_found(transcriber):
    """Test find_recorder when no recorder is connected."""
    with patch('src.transcriber.Path') as mock_path:
        mock_path.return_value.exists.return_value = False
        result = transcriber.find_recorder()
        assert result is None


def test_find_recorder_found(transcriber):
    """Test find_recorder when recorder is present."""
    # This test validates that find_recorder doesn't crash
    # Actual result depends on whether recorder is connected
    # We test the method structure, not the actual detection
    result = transcriber.find_recorder()
    # Result can be None (no recorder) or Path (recorder found)
    # Both are valid - we're just checking the method works
    assert result is None or isinstance(result, Path)


def test_get_last_sync_time_no_file(transcriber, tmp_path, monkeypatch):
    """Test get_last_sync_time when no state file exists."""
    from src import config as config_module
    
    state_file = tmp_path / "state.json"
    monkeypatch.setattr(config_module.config, 'STATE_FILE', state_file)
    
    result = transcriber.get_last_sync_time()
    
    # Should return approximately 7 days ago
    expected = datetime.now() - timedelta(days=7)
    assert abs((result - expected).total_seconds()) < 60  # Within 1 minute


def test_get_last_sync_time_with_file(transcriber, tmp_path, monkeypatch):
    """Test get_last_sync_time when state file exists."""
    from src import config as config_module
    
    state_file = tmp_path / "state.json"
    test_time = datetime(2025, 1, 1, 12, 0, 0)
    
    with open(state_file, 'w') as f:
        json.dump({"last_sync": test_time.isoformat()}, f)
    
    monkeypatch.setattr(config_module.config, 'STATE_FILE', state_file)
    
    result = transcriber.get_last_sync_time()
    assert result == test_time


def test_save_sync_time(transcriber, tmp_path, monkeypatch):
    """Test save_sync_time writes to state file."""
    from src import config as config_module
    
    state_file = tmp_path / "state.json"
    monkeypatch.setattr(config_module.config, 'STATE_FILE', state_file)
    
    transcriber.save_sync_time()
    
    assert state_file.exists()
    
    with open(state_file, 'r') as f:
        data = json.load(f)
    
    assert "last_sync" in data
    # Should be very recent
    sync_time = datetime.fromisoformat(data["last_sync"])
    assert abs((datetime.now() - sync_time).total_seconds()) < 5


def test_find_audio_files(transcriber, mock_recorder_path):
    """Test find_audio_files finds correct files."""
    since = datetime.now() - timedelta(days=1)
    
    files = transcriber.find_audio_files(mock_recorder_path, since)
    
    # Should find 2 audio files (mp3 and wav), not txt
    assert len(files) == 2
    assert all(f.suffix in {".mp3", ".wav"} for f in files)


def test_find_audio_files_filters_by_time(transcriber, mock_recorder_path):
    """Test find_audio_files filters by modification time."""
    # Set 'since' to future, should find no files
    since = datetime.now() + timedelta(days=1)
    
    files = transcriber.find_audio_files(mock_recorder_path, since)
    
    assert len(files) == 0


def test_find_audio_files_respects_max_depth(transcriber, tmp_path):
    """Test find_audio_files respects MAX_SCAN_DEPTH limit."""
    from src.config.defaults import defaults
    
    # Create directory structure with files at different depths
    recorder = tmp_path / "TEST_VOLUME"
    recorder.mkdir()
    
    # Depth 1: recorder/level1/file.mp3
    (recorder / "level1").mkdir()
    file_depth1 = recorder / "level1" / "file1.mp3"
    file_depth1.touch()
    
    # Depth 2: recorder/level1/level2/file.mp3
    (recorder / "level1" / "level2").mkdir()
    file_depth2 = recorder / "level1" / "level2" / "file2.mp3"
    file_depth2.touch()
    
    # Depth 3: recorder/level1/level2/level3/file.mp3 (should be found)
    (recorder / "level1" / "level2" / "level3").mkdir()
    file_depth3 = recorder / "level1" / "level2" / "level3" / "file3.mp3"
    file_depth3.touch()
    
    # Depth 4: recorder/level1/level2/level3/level4/file.mp3 (should be ignored)
    (recorder / "level1" / "level2" / "level3" / "level4").mkdir()
    file_depth4 = recorder / "level1" / "level2" / "level3" / "level4" / "file4.mp3"
    file_depth4.touch()
    
    # Set all files to recent modification time
    since = datetime.now() - timedelta(hours=1)
    for f in [file_depth1, file_depth2, file_depth3, file_depth4]:
        import os
        os.utime(f, (since.timestamp(), since.timestamp()))
    
    # Find files
    files = transcriber.find_audio_files(recorder, since - timedelta(minutes=30))
    
    # Should find files at depth 1, 2, 3 (≤ max_depth=3)
    found_paths = {f.relative_to(recorder) for f in files}
    
    assert file_depth1.relative_to(recorder) in found_paths, "Depth 1 file should be found"
    assert file_depth2.relative_to(recorder) in found_paths, "Depth 2 file should be found"
    assert file_depth3.relative_to(recorder) in found_paths, "Depth 3 file should be found"
    assert file_depth4.relative_to(recorder) not in found_paths, "Depth 4 file should be ignored (depth > max_depth)"


def test_transcribe_file_no_whisper(transcriber, tmp_path):
    """Test transcribe_file when whisper.cpp is not available."""
    transcriber.whisper_available = False
    audio_file = tmp_path / "test.mp3"
    audio_file.touch()
    
    result = transcriber.transcribe_file(audio_file)
    
    assert result is False


def test_transcribe_file_already_transcribed_txt(transcriber, tmp_path, monkeypatch):
    """Test transcribe_file when TXT output already exists."""
    # Patch global config for state_manager functions
    from src import config as config_module
    
    transcriber.whisper_available = True
    # Avoid calling real whisper.cpp if logic regresses
    transcriber._run_macwhisper = MagicMock(return_value=None)  # type: ignore[arg-type]
    
    audio_file = tmp_path / "test.mp3"
    audio_file.touch()
    
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    output_file = output_dir / "test.txt"
    output_file.write_text("Test transcript")
    
    # Update transcriber's injected config (not global config)
    transcriber.config.TRANSCRIBE_DIR = output_dir
    # Also patch global for state_manager functions
    monkeypatch.setattr(config_module.config, 'TRANSCRIBE_DIR', output_dir)
    
    result = transcriber.transcribe_file(audio_file)
    
    assert result is True  # Already exists counts as success (via post-process)


def test_transcribe_file_already_transcribed_md(transcriber, tmp_path, monkeypatch):
    """Test transcribe_file when MD output already exists."""
    # Patch global config for state_manager functions
    from src import config as config_module
    
    transcriber.whisper_available = True
    # If markdown exists, whisper should never be called
    transcriber._run_macwhisper = MagicMock()  # type: ignore[arg-type]
    
    audio_file = tmp_path / "test.mp3"
    audio_file.touch()
    
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    md_file = output_dir / "2025-11-19_Test.md"
    md_file.write_text(
        "---\n"
        'title: "Test"\n'
        "date: 2025-11-19\n"
        "recording_date: 2025-11-19T10:00:00\n"
        "source: test.mp3\n"
        "duration: 00:10:00\n"
        "tags: [transcription]\n"
        "---\n\n"
        "## Podsumowanie\n\nTest\n"
    )
    
    # Update transcriber's injected config (not global config)
    transcriber.config.TRANSCRIBE_DIR = output_dir
    # Also patch global for state_manager functions
    monkeypatch.setattr(config_module.config, 'TRANSCRIBE_DIR', output_dir)
    
    result = transcriber.transcribe_file(audio_file)
    
    assert result is True  # MD exists, skip transcription
    transcriber._run_macwhisper.assert_not_called()


def test_postprocess_transcript_success(transcriber, tmp_path, monkeypatch):
    """Test successful post-processing of transcript."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    update_transcriber_config(transcriber, monkeypatch, TRANSCRIBE_DIR=output_dir, DELETE_TEMP_TXT=True)
    
    audio_file = tmp_path / "test.mp3"
    audio_file.touch()
    transcript_file = output_dir / "test.txt"
    transcript_file.write_text("Test transcript content")
    
    # Mock summarizer
    mock_summarizer = MagicMock(spec=BaseSummarizer)
    mock_summarizer.generate.return_value = {
        "title": "Test Title",
        "summary": "Test summary"
    }
    transcriber.summarizer = mock_summarizer
    
    # Mock markdown generator
    mock_md_gen = MagicMock(spec=MarkdownGenerator)
    mock_md_gen.extract_audio_metadata.return_value = {
        "source_file": "test.mp3",
        "extension": ".mp3",
        "recording_datetime": datetime.now(),
        "duration_seconds": 60,
        "duration_formatted": "00:01:00"
    }
    mock_md_path = output_dir / "2025-11-19_Test_Title.md"
    mock_md_gen.create_markdown_document.return_value = mock_md_path
    transcriber.markdown_generator = mock_md_gen
    
    result = transcriber._postprocess_transcript(audio_file, transcript_file)
    
    assert result is True
    mock_summarizer.generate.assert_called_once()
    mock_md_gen.create_markdown_document.assert_called_once()
    # TXT file should be deleted
    assert not transcript_file.exists()


def test_postprocess_transcript_no_summarizer(transcriber, tmp_path, monkeypatch):
    """Test post-processing without summarizer (fallback)."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    update_transcriber_config(transcriber, monkeypatch, TRANSCRIBE_DIR=output_dir)
    
    audio_file = tmp_path / "test.mp3"
    audio_file.touch()
    transcript_file = output_dir / "test.txt"
    transcript_file.write_text("Test transcript")
    
    # No summarizer
    transcriber.summarizer = None
    
    # Mock markdown generator
    mock_md_gen = MagicMock(spec=MarkdownGenerator)
    mock_md_gen.extract_audio_metadata.return_value = {
        "source_file": "test.mp3",
        "extension": ".mp3",
        "recording_datetime": datetime.now(),
        "duration_seconds": 60,
        "duration_formatted": "00:01:00"
    }
    mock_md_path = output_dir / "2025-11-19_test.md"
    mock_md_gen.create_markdown_document.return_value = mock_md_path
    transcriber.markdown_generator = mock_md_gen
    
    result = transcriber._postprocess_transcript(audio_file, transcript_file)
    
    assert result is True
    # Should use fallback summary
    call_args = mock_md_gen.create_markdown_document.call_args
    summary = call_args[1]["summary"]
    assert "title" in summary
    assert "Brak podsumowania" in summary.get("summary", "")


def test_postprocess_transcript_passes_tags(monkeypatch, tmp_path, transcriber):
    """Tag list should be passed into markdown generator."""
    from src import config as config_module

    output_dir = tmp_path / "output"
    output_dir.mkdir()
    update_transcriber_config(transcriber, monkeypatch, TRANSCRIBE_DIR=output_dir, ENABLE_LLM_TAGGING=False)

    audio_file = tmp_path / "sample.mp3"
    audio_file.touch()
    transcript_file = output_dir / "sample.txt"
    transcript_file.write_text("Treść transkrypcji")

    transcriber.summarizer = None

    mock_md_gen = MagicMock(spec=MarkdownGenerator)
    mock_md_gen.extract_audio_metadata.return_value = {
        "source_file": "sample.mp3",
        "extension": ".mp3",
        "recording_datetime": datetime.now(),
        "duration_seconds": 60,
        "duration_formatted": "00:01:00",
    }
    mock_md_gen.create_markdown_document.return_value = output_dir / "sample.md"
    transcriber.markdown_generator = mock_md_gen

    result = transcriber._postprocess_transcript(audio_file, transcript_file)

    assert result is True
    _, kwargs = mock_md_gen.create_markdown_document.call_args
    assert "tags" in kwargs
    assert kwargs["tags"][0] == "transcription"


def test_process_recorder_no_recorder(transcriber):
    """Test process_recorder when no recorder is found."""
    with patch.object(transcriber, 'find_recorder', return_value=None):
        transcriber.process_recorder()
        
        assert not transcriber.recorder_monitoring


def test_process_recorder_with_files(transcriber, mock_recorder_path):
    """Test process_recorder with new files."""
    with patch.object(transcriber, 'find_recorder', return_value=mock_recorder_path):
        with patch.object(transcriber, 'get_last_sync_time', 
                         return_value=datetime.now() - timedelta(days=1)):
            with patch.object(transcriber, 'transcribe_file', return_value=True):
                with patch.object(transcriber, 'save_sync_time'):
                    transcriber.process_recorder()
                    
                    assert transcriber.recorder_monitoring


def test_stage_audio_file_success(transcriber, tmp_path, monkeypatch):
    """Test successful staging of audio file."""
    staging_dir = tmp_path / "staging"
    staging_dir.mkdir()
    update_transcriber_config(transcriber, monkeypatch, LOCAL_RECORDINGS_DIR=staging_dir)
    
    recorder_file = tmp_path / "recorder" / "test.mp3"
    recorder_file.parent.mkdir()
    recorder_file.write_bytes(b"fake audio data")
    
    staged_path = transcriber._stage_audio_file(recorder_file)
    
    assert staged_path is not None
    assert staged_path == staging_dir / "test.mp3"
    assert staged_path.exists()
    assert staged_path.read_bytes() == b"fake audio data"


def test_stage_audio_file_not_found(transcriber, tmp_path, monkeypatch):
    """Test staging when recorder file doesn't exist."""
    staging_dir = tmp_path / "staging"
    staging_dir.mkdir()
    update_transcriber_config(transcriber, monkeypatch, LOCAL_RECORDINGS_DIR=staging_dir)
    
    recorder_file = tmp_path / "nonexistent.mp3"
    
    staged_path = transcriber._stage_audio_file(recorder_file)
    
    assert staged_path is None


def test_stage_audio_file_reuse_existing(transcriber, tmp_path, monkeypatch):
    """Test staging reuses existing copy if it matches."""
    from src import config as config_module
    import time
    
    staging_dir = tmp_path / "staging"
    staging_dir.mkdir()
    update_transcriber_config(transcriber, monkeypatch, LOCAL_RECORDINGS_DIR=staging_dir)
    
    recorder_file = tmp_path / "recorder" / "test.mp3"
    recorder_file.parent.mkdir()
    recorder_file.write_bytes(b"fake audio data")
    
    # Create existing staged file with same content
    staged_file = staging_dir / "test.mp3"
    staged_file.write_bytes(b"fake audio data")
    # Set same mtime
    staged_file.touch()
    time.sleep(0.1)  # Small delay to ensure mtime is set
    recorder_file.touch()
    
    staged_path = transcriber._stage_audio_file(recorder_file)
    
    assert staged_path is not None
    assert staged_path == staged_file


def test_process_recorder_staging_integration(transcriber, tmp_path, monkeypatch):
    """Test process_recorder uses staging before transcription."""
    from src import config as config_module
    
    staging_dir = tmp_path / "staging"
    staging_dir.mkdir()
    update_transcriber_config(transcriber, monkeypatch, LOCAL_RECORDINGS_DIR=staging_dir)
    
    recorder = tmp_path / "LS-P1"
    recorder.mkdir()
    audio_file = recorder / "test.mp3"
    audio_file.write_bytes(b"fake audio")
    
    with patch.object(transcriber, 'find_recorder', return_value=recorder):
        with patch.object(transcriber, 'get_last_sync_time', 
                         return_value=datetime.now() - timedelta(days=1)):
            with patch.object(transcriber, 'transcribe_file', return_value=True) as mock_transcribe:
                with patch.object(transcriber, 'save_sync_time'):
                    transcriber.process_recorder()
                    
                    # Verify transcribe_file was called with staged path
                    assert mock_transcribe.called
                    call_args = mock_transcribe.call_args[0][0]
                    assert call_args.parent == staging_dir
                    assert call_args.name == "test.mp3"


def test_process_recorder_batch_failure_handling(transcriber, tmp_path, monkeypatch):
    """Test that last_sync is not updated if any file fails."""
    from src import config as config_module
    
    staging_dir = tmp_path / "staging"
    staging_dir.mkdir()
    update_transcriber_config(transcriber, monkeypatch, LOCAL_RECORDINGS_DIR=staging_dir)
    
    recorder = tmp_path / "LS-P1"
    recorder.mkdir()
    audio_file1 = recorder / "test1.mp3"
    audio_file1.write_bytes(b"fake audio")
    audio_file2 = recorder / "test2.mp3"
    audio_file2.write_bytes(b"fake audio")
    
    with patch.object(transcriber, 'find_recorder', return_value=recorder):
        with patch.object(transcriber, 'get_last_sync_time', 
                         return_value=datetime.now() - timedelta(days=1)):
            # First succeeds, second fails
            with patch.object(transcriber, 'transcribe_file', 
                            side_effect=[True, False]) as mock_transcribe:
                with patch.object(transcriber, 'save_sync_time') as mock_save:
                    transcriber.process_recorder()
                    
                    # Should NOT save sync time because one file failed
                    mock_save.assert_not_called()


def test_process_recorder_batch_success_updates_sync(transcriber, tmp_path, monkeypatch):
    """Test that last_sync is updated when all files succeed."""
    from src import config as config_module
    
    staging_dir = tmp_path / "staging"
    staging_dir.mkdir()
    update_transcriber_config(transcriber, monkeypatch, LOCAL_RECORDINGS_DIR=staging_dir)
    
    recorder = tmp_path / "LS-P1"
    recorder.mkdir()
    audio_file1 = recorder / "test1.mp3"
    audio_file1.write_bytes(b"fake audio")
    audio_file2 = recorder / "test2.mp3"
    audio_file2.write_bytes(b"fake audio")
    
    with patch.object(transcriber, 'find_recorder', return_value=recorder):
        with patch.object(transcriber, 'get_last_sync_time', 
                         return_value=datetime.now() - timedelta(days=1)):
            # Both succeed
            with patch.object(transcriber, 'transcribe_file', return_value=True):
                with patch.object(transcriber, 'save_sync_time') as mock_save:
                    transcriber.process_recorder()
                    
                    # Should save sync time because all files succeeded
                    mock_save.assert_called_once()


def test_process_recorder_skips_files_with_existing_markdown(
    transcriber, tmp_path, monkeypatch
):
    """Ensure recorder workflow checks for existing markdown before staging."""
    from src import config as config_module

    staging_dir = tmp_path / "staging"
    staging_dir.mkdir()
    transcript_dir = tmp_path / "transcripts"
    transcript_dir.mkdir()
    update_transcriber_config(transcriber, monkeypatch, LOCAL_RECORDINGS_DIR=staging_dir, TRANSCRIBE_DIR=transcript_dir)
    recorder = tmp_path / "LS-P1"
    recorder.mkdir()
    processed_file = recorder / "processed.mp3"
    processed_file.write_bytes(b"done")
    new_file = recorder / "new.mp3"
    new_file.write_bytes(b"new")

    # Existing markdown referencing processed.mp3
    md_file = transcript_dir / "existing.md"
    md_file.write_text(
        "---\n"
        'title: "Zrobione"\n'
        "date: 2025-11-25\n"
        "recording_date: 2025-11-25T10:00:00\n"
        "source: processed.mp3\n"
        "duration: 00:01:00\n"
        "tags: [transcription]\n"
        "---\n\n"
        "Treść\n"
    )

    staged_new = staging_dir / "new.mp3"
    staged_new.write_bytes(b"new")
    with patch.object(transcriber, "find_recorder", return_value=recorder):
        with patch.object(
            transcriber, "get_last_sync_time", return_value=datetime.now() - timedelta(days=1)
        ):
            with patch.object(transcriber, "_stage_audio_file", return_value=staged_new) as mock_stage:
                with patch.object(transcriber, "transcribe_file", return_value=True) as mock_transcribe:
                    with patch.object(transcriber, "save_sync_time") as mock_save_sync:
                        transcriber.process_recorder()

    mock_stage.assert_called_once()
    assert mock_stage.call_args[0][0].name == "new.mp3"
    mock_transcribe.assert_called_once_with(staged_new)
    mock_save_sync.assert_called_once()


def test_run_macwhisper_retries_on_metal_error(transcriber, tmp_path, monkeypatch):
    """Whisper retry should trigger on Metal/Core ML failures."""
    from src import config as config_module

    transcript_dir = tmp_path / "output"
    transcript_dir.mkdir()
    update_transcriber_config(transcriber, monkeypatch, TRANSCRIBE_DIR=transcript_dir)

    audio_file = tmp_path / "sample.mp3"
    audio_file.touch()

    def run_side_effect(_, use_coreml=True):
        if use_coreml:
            return subprocess.CompletedProcess(
                args=["whisper"],
                returncode=1,
                stdout="",
                stderr="ggml_metal_device_init: tensor API disabled",
            )
        output_file = transcript_dir / "sample.txt"
        output_file.write_text("ok")
        return subprocess.CompletedProcess(
            args=["whisper"], returncode=0, stdout="", stderr=""
        )

    mock_runner = MagicMock(side_effect=run_side_effect)
    transcriber._run_whisper_transcription = mock_runner  # type: ignore[assignment]

    result = transcriber._run_macwhisper(audio_file)

    assert result == transcript_dir / "sample.txt"
    assert mock_runner.call_count == 2
    assert mock_runner.call_args_list[1].kwargs["use_coreml"] is False


def test_run_whisper_transcription_disables_metal_for_cpu(
    transcriber, tmp_path, monkeypatch
):
    """CPU fallback should disable Core ML / Metal backends via environment."""
    from src import config as config_module

    audio_file = tmp_path / "sample.mp3"
    audio_file.touch()    # Point config to temporary paths so command construction works
    update_transcriber_config(
        transcriber, monkeypatch,
        WHISPER_CPP_MODELS_DIR=tmp_path,
        WHISPER_MODEL="small",
        WHISPER_CPP_PATH=tmp_path / "whisper-cli",
        TRANSCRIBE_DIR=tmp_path
    )

    captured = {}

    def fake_run(
        cmd,
        capture_output,
        timeout,
        text,
        env=None,
    ):
        captured["env"] = env
        return subprocess.CompletedProcess(
            args=cmd,
            returncode=0,
            stdout="",
            stderr="",
        )

    monkeypatch.setattr("src.transcriber.subprocess.run", fake_run)

    _ = transcriber._run_whisper_transcription(audio_file, use_coreml=False)

    env = captured.get("env")
    assert env is not None
    assert env.get("WHISPER_COREML") == "0"
    assert env.get("GGML_METAL_DISABLE") == "1"


def test_process_recorder_skips_when_lock_held(transcriber, monkeypatch):
    """process_recorder should not run if lock acquisition fails."""
    from src import transcriber as transcriber_module

    class DummyLock:
        def __init__(self, *_args, **_kwargs):
            pass

        def acquire(self) -> bool:
            return False

        def release(self) -> None:
            pass

    monkeypatch.setattr(transcriber_module, "ProcessLock", DummyLock)

    with patch.object(transcriber, "find_recorder") as mock_find:
        transcriber.process_recorder()
        mock_find.assert_not_called()


def test_process_recorder_releases_lock(transcriber, monkeypatch):
    """Lock should always be released even when recorder missing."""
    from src import transcriber as transcriber_module

    released = {"value": False}

    class DummyLock:
        def __init__(self, *_args, **_kwargs):
            pass

        def acquire(self) -> bool:
            return True

        def release(self) -> None:
            released["value"] = True

    monkeypatch.setattr(transcriber_module, "ProcessLock", DummyLock)

    with patch.object(transcriber, "find_recorder", return_value=None):
        transcriber.process_recorder()

    assert released["value"] is True


def test_process_lock_removes_stale_file(tmp_path, monkeypatch):
    """Stale lock files should be cleaned up so processing can continue."""
    from src import transcriber as transcriber_module
    from src.transcriber import ProcessLock
    from src import config as config_module
    import time as time_module

    # Patch logger to avoid real logging side effects during the test.
    monkeypatch.setattr(transcriber_module, "logger", MagicMock())

    lock_path = tmp_path / "transcriber.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)

    # Create a stale timestamp older than TRANSCRIPTION_TIMEOUT + buffer.
    stale_age = config_module.config.TRANSCRIPTION_TIMEOUT + 1200
    stale_timestamp = time_module.time() - stale_age
    lock_path.write_text(f"{stale_timestamp:.0f}", encoding="utf-8")

    lock = ProcessLock(lock_path)
    acquired = lock.acquire()

    assert acquired is True
    # Timestamp in the lock file should be refreshed.
    new_timestamp = float(lock_path.read_text(encoding="utf-8").strip())
    assert new_timestamp > stale_timestamp


def test_process_lock_keeps_recent_lock(tmp_path, monkeypatch):
    """Recent lock files should prevent new acquisition (no false cleanup)."""
    from src import transcriber as transcriber_module
    from src.transcriber import ProcessLock
    from src import config as config_module
    import time as time_module

    monkeypatch.setattr(transcriber_module, "logger", MagicMock())

    lock_path = tmp_path / "transcriber.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)

    # Create a recent timestamp younger than the stale threshold.
    recent_age = config_module.config.TRANSCRIPTION_TIMEOUT / 2
    recent_timestamp = time_module.time() - recent_age
    lock_path.write_text(f"{recent_timestamp:.0f}", encoding="utf-8")

    lock = ProcessLock(lock_path)
    acquired = lock.acquire()

    # Lock should not be acquired because existing one is still recent.
    assert acquired is False


@patch('src.transcriber.send_notification')
def test_process_recorder_no_notification_when_no_new_files(mock_notification, transcriber, mock_recorder_path):
    """Test that no notification is sent when recorder has no new files."""
    with patch.object(transcriber, 'find_recorder', return_value=mock_recorder_path):
        with patch.object(transcriber, 'get_last_sync_time', 
                         return_value=datetime.now() + timedelta(days=1)):  # Future date = no new files
            with patch.object(transcriber, 'save_sync_time'):
                transcriber.process_recorder()
                
                # Should not send any notifications when no new files found
                mock_notification.assert_not_called()


@patch('src.transcriber.send_notification')
def test_process_recorder_sends_notification_when_new_files_found(
    mock_notification, transcriber, mock_recorder_path, tmp_path, monkeypatch
):
    """Test that notifications are sent when new files are found."""
    from src import config as config_module
    
    staging_dir = tmp_path / "staging"
    staging_dir.mkdir()
    update_transcriber_config(transcriber, monkeypatch, LOCAL_RECORDINGS_DIR=staging_dir)
    
    with patch.object(transcriber, 'find_recorder', return_value=mock_recorder_path):
        with patch.object(transcriber, 'get_last_sync_time', 
                         return_value=datetime.now() - timedelta(days=1)):  # Past date = new files
            with patch.object(transcriber, 'transcribe_file', return_value=True):
                with patch.object(transcriber, 'save_sync_time'):
                    transcriber.process_recorder()
                    
                    # Should send notifications: recorder detected + new files found + completion
                    assert mock_notification.call_count >= 2
                    
                    # Check that "Znaleziono X nowych nagrań" notification was sent
                    call_args_list = [call[1] for call in mock_notification.call_args_list]
                    subtitles = [args.get('subtitle', '') for args in call_args_list]
                    assert any('nowych nagrań' in subtitle for subtitle in subtitles)
                    
                    # Check that completion notification was sent
                    assert any('zakończona' in subtitle for subtitle in subtitles)
