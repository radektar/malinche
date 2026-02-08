"""Unit tests for dependency downloader."""

import hashlib
import shutil
import socket
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch
from urllib.error import HTTPError, URLError

import pytest

from src.setup.downloader import DependencyDownloader, MAX_RETRIES
from src.setup.errors import (
    ChecksumError,
    DiskSpaceError,
    DownloadError,
    NetworkError,
)


class TestDependencyDownloader:
    """Testy dla klasy DependencyDownloader."""

    @pytest.fixture
    def downloader(self, tmp_path, monkeypatch):
        """Fixture tworzący downloader z tymczasowym katalogiem."""
        # Utwórz downloader i nadpisz ścieżki
        d = DependencyDownloader()
        d.support_dir = tmp_path / "Transrec"
        d.bin_dir = d.support_dir / "bin"
        d.models_dir = d.support_dir / "models"
        d.downloads_dir = d.support_dir / "downloads"
        
        # Utwórz katalogi
        d.bin_dir.mkdir(parents=True, exist_ok=True)
        d.models_dir.mkdir(parents=True, exist_ok=True)
        d.downloads_dir.mkdir(parents=True, exist_ok=True)
        
        return d

    def test_check_network_online(self, downloader, monkeypatch):
        """Test sprawdzania połączenia sieciowego - online."""
        # Mock socket.create_connection - sukces
        mock_connection = Mock()
        monkeypatch.setattr(
            socket, "create_connection", lambda *args, **kwargs: mock_connection
        )

        result = downloader.check_network()
        assert result is True

    def test_check_network_offline(self, downloader, monkeypatch):
        """Test sprawdzania połączenia sieciowego - offline."""
        # Mock socket.create_connection - błąd
        def mock_connection(*args, **kwargs):
            raise OSError("Network unreachable")

        monkeypatch.setattr(socket, "create_connection", mock_connection)

        with pytest.raises(NetworkError, match="Brak połączenia"):
            downloader.check_network()

    def test_check_disk_space_ok(self, downloader, monkeypatch):
        """Test sprawdzania miejsca na dysku - wystarczająco."""
        # Mock shutil.disk_usage - wystarczająco miejsca
        mock_usage = Mock()
        mock_usage.free = 1_000_000_000  # 1GB
        monkeypatch.setattr(shutil, "disk_usage", lambda path: mock_usage)

        result = downloader.check_disk_space()
        assert result is True

    def test_check_disk_space_full(self, downloader, monkeypatch):
        """Test sprawdzania miejsca na dysku - za mało."""
        # Mock shutil.disk_usage - za mało miejsca
        mock_usage = Mock()
        mock_usage.free = 100_000_000  # 100MB (< 500MB wymagane)
        monkeypatch.setattr(shutil, "disk_usage", lambda path: mock_usage)

        with pytest.raises(DiskSpaceError, match="Brak miejsca"):
            downloader.check_disk_space()

    def test_verify_checksum_valid(self, downloader, tmp_path):
        """Test weryfikacji checksum - poprawny."""
        # Utwórz plik testowy
        test_file = tmp_path / "test.bin"
        test_file.write_bytes(b"test content")

        # Oblicz SHA256
        sha256 = hashlib.sha256()
        sha256.update(b"test content")
        expected_checksum = sha256.hexdigest()

        result = downloader.verify_checksum(test_file, expected_checksum)
        assert result is True

    def test_verify_checksum_invalid(self, downloader, tmp_path):
        """Test weryfikacji checksum - błędny."""
        # Utwórz plik testowy
        test_file = tmp_path / "test.bin"
        test_file.write_bytes(b"test content")

        # Błędny checksum
        wrong_checksum = "wrong" * 16

        result = downloader.verify_checksum(test_file, wrong_checksum)
        assert result is False

    def test_verify_checksum_empty(self, downloader, tmp_path):
        """Test weryfikacji checksum - brak checksum (pomija weryfikację)."""
        test_file = tmp_path / "test.bin"
        test_file.write_bytes(b"test content")

        # Pusty checksum - powinno zwrócić True (pomija weryfikację)
        result = downloader.verify_checksum(test_file, "")
        assert result is True

    def test_is_whisper_installed_true(self, downloader):
        """Test sprawdzania whisper - zainstalowany."""
        # Utwórz plik whisper-cli
        whisper_path = downloader.bin_dir / "whisper-cli"
        whisper_path.write_bytes(b"fake binary")
        whisper_path.chmod(0o755)

        result = downloader.is_whisper_installed()
        assert result is True

    def test_is_whisper_installed_false(self, downloader):
        """Test sprawdzania whisper - nie zainstalowany."""
        result = downloader.is_whisper_installed()
        assert result is False

    def test_is_ffmpeg_installed_true(self, downloader):
        """Test sprawdzania ffmpeg - zainstalowany."""
        # Utwórz plik ffmpeg
        ffmpeg_path = downloader.bin_dir / "ffmpeg"
        ffmpeg_path.write_bytes(b"fake binary")
        ffmpeg_path.chmod(0o755)

        result = downloader.is_ffmpeg_installed()
        assert result is True

    def test_is_ffmpeg_installed_false(self, downloader):
        """Test sprawdzania ffmpeg - nie zainstalowany."""
        result = downloader.is_ffmpeg_installed()
        assert result is False

    def test_is_model_installed_true(self, downloader):
        """Test sprawdzania modelu - zainstalowany."""
        # Utwórz plik modelu
        model_path = downloader.models_dir / "ggml-small.bin"
        model_path.write_bytes(b"fake model")

        result = downloader.is_model_installed()
        assert result is True

    def test_is_model_installed_false(self, downloader):
        """Test sprawdzania modelu - nie zainstalowany."""
        result = downloader.is_model_installed()
        assert result is False

    def test_check_all_true(self, downloader, monkeypatch):
        """Test check_all - wszystkie zainstalowane."""
        # Utwórz wszystkie pliki
        (downloader.bin_dir / "whisper-cli").write_bytes(b"fake")
        (downloader.bin_dir / "ffmpeg").write_bytes(b"fake")
        (downloader.models_dir / "ggml-small.bin").write_bytes(b"fake")
        
        # Mock checksum verification to return True (test files don't have real checksums)
        monkeypatch.setattr(downloader, "verify_checksum", lambda path, checksum: True)

        result = downloader.check_all()
        assert result is True

    def test_check_all_false(self, downloader):
        """Test check_all - brakuje zależności."""
        result = downloader.check_all()
        assert result is False

    @pytest.mark.skip(reason="Wymaga przepisania na httpx - używamy testów integracyjnych")
    @patch("src.setup.downloader.urlopen")
    def test_download_with_retry_success(
        self, mock_urlopen, downloader, monkeypatch
    ):
        """Test pobierania z retry - sukces po retry."""
        # Mock check_network i check_disk_space
        monkeypatch.setattr(downloader, "check_network", lambda: True)
        monkeypatch.setattr(downloader, "check_disk_space", lambda *args: True)

        # Pierwsza próba - HTTP 500, druga - sukces
        mock_response_200 = MagicMock()
        mock_response_200.status = 200
        mock_response_200.headers.get.return_value = "10"
        mock_response_200.read.side_effect = [b"data", b""]
        mock_response_200.__enter__ = Mock(return_value=mock_response_200)
        mock_response_200.__exit__ = Mock(return_value=False)

        mock_urlopen.side_effect = [
            HTTPError("url", 500, "Internal Server Error", None, None),
            mock_response_200,
        ]

        # Mock URLS
        with patch("src.setup.downloader.URLS", {"whisper": "http://test.com/file"}):
            with patch("src.setup.downloader.SIZES", {"whisper-cli-arm64": 10}):
                with patch("src.setup.downloader.CHECKSUMS", {}):
                    with patch("platform.machine", return_value="arm64"):
                        downloader.download_whisper()

        assert mock_urlopen.call_count == 2

    @pytest.mark.skip(reason="Wymaga przepisania na httpx - używamy testów integracyjnych")
    @patch("src.setup.downloader.urlopen")
    def test_download_max_retries_exceeded(
        self, mock_urlopen, downloader, monkeypatch
    ):
        """Test pobierania - przekroczono max retries."""
        # Mock check_network i check_disk_space
        monkeypatch.setattr(downloader, "check_network", lambda: True)
        monkeypatch.setattr(downloader, "check_disk_space", lambda *args: True)

        # Wszystkie próby - HTTP 500
        mock_urlopen.side_effect = HTTPError(
            "url", 500, "Internal Server Error", None, None
        )

        # Mock URLS
        with patch("src.setup.downloader.URLS", {"whisper": "http://test.com/file"}):
            with patch("src.setup.downloader.SIZES", {"whisper-cli-arm64": 10}):
                with patch("src.setup.downloader.CHECKSUMS", {}):
                    with patch("platform.machine", return_value="arm64"):
                        with pytest.raises(DownloadError):
                            downloader.download_whisper()

        assert mock_urlopen.call_count == MAX_RETRIES

    @pytest.mark.skip(reason="Wymaga przepisania na httpx - używamy testów integracyjnych")
    def test_download_progress_callback(self, downloader, monkeypatch):
        """Test progress callback podczas pobierania."""
        callback_calls = []

        def progress_callback(name: str, progress: float):
            callback_calls.append((name, progress))

        downloader.progress_callback = progress_callback

        # Mock urlopen z context manager support
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.headers.get.return_value = "20"  # 20 bajtów
        mock_response.read.side_effect = [b"x" * 10, b"x" * 10, b""]
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)

        mock_urlopen = Mock(return_value=mock_response)

        with patch("src.setup.downloader.urlopen", mock_urlopen):
            monkeypatch.setattr(downloader, "check_network", lambda: True)
            monkeypatch.setattr(downloader, "check_disk_space", lambda *args: True)

            with patch("src.setup.downloader.URLS", {"whisper": "http://test.com"}):
                with patch("src.setup.downloader.SIZES", {"whisper-cli-arm64": 20}):
                    with patch("src.setup.downloader.CHECKSUMS", {}):
                        with patch("platform.machine", return_value="arm64"):
                            downloader.download_whisper()

        # Sprawdź czy callback był wywoływany
        assert len(callback_calls) > 0
        assert all(0.0 <= progress <= 1.0 for _, progress in callback_calls)

    @pytest.mark.skip(reason="Wymaga przepisania na httpx - używamy testów integracyjnych")
    def test_resume_partial_download(self, downloader, monkeypatch):
        """Test wznowienia częściowego pobierania."""
        # Utwórz częściowy plik .tmp
        temp_file = downloader.downloads_dir / "whisper-cli.tmp"
        temp_file.write_bytes(b"partial")

        # Mock urlopen z Range header
        mock_response = MagicMock()
        mock_response.status = 206  # Partial Content
        mock_response.headers.get.return_value = "10"
        mock_response.read.side_effect = [b"complete", b""]
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)

        mock_urlopen = Mock(return_value=mock_response)

        with patch("src.setup.downloader.urlopen", mock_urlopen):
            monkeypatch.setattr(downloader, "check_network", lambda: True)
            monkeypatch.setattr(downloader, "check_disk_space", lambda *args: True)

            with patch("src.setup.downloader.URLS", {"whisper": "http://test.com"}):
                with patch("src.setup.downloader.SIZES", {"whisper-cli-arm64": 20}):
                    with patch("src.setup.downloader.CHECKSUMS", {}):
                        with patch("platform.machine", return_value="arm64"):
                            downloader.download_whisper()

        # Sprawdź czy Range header był użyty
        if mock_urlopen.called:
            call_args = mock_urlopen.call_args
            if call_args and len(call_args[0]) > 0:
                request = call_args[0][0]
                if hasattr(request, "headers"):
                    assert "Range" in request.headers or request.headers.get("Range")

    @pytest.mark.skip(reason="Wymaga przepisania na httpx - używamy testów integracyjnych")
    def test_cleanup_temp_files(self, downloader, monkeypatch):
        """Test usuwania plików tymczasowych po sukcesie."""
        # Mock urlopen
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.headers.get.return_value = "10"
        mock_response.read.side_effect = [b"data", b""]
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)

        mock_urlopen = Mock(return_value=mock_response)

        with patch("src.setup.downloader.urlopen", mock_urlopen):
            monkeypatch.setattr(downloader, "check_network", lambda: True)
            monkeypatch.setattr(downloader, "check_disk_space", lambda *args: True)

            with patch("src.setup.downloader.URLS", {"whisper": "http://test.com"}):
                with patch("src.setup.downloader.SIZES", {"whisper-cli-arm64": 10}):
                    with patch("src.setup.downloader.CHECKSUMS", {}):
                        with patch("platform.machine", return_value="arm64"):
                            downloader.download_whisper()

        # Sprawdź czy pliki .tmp zostały usunięte (plik został przeniesiony do bin_dir)
        temp_files = list(downloader.downloads_dir.glob("*.tmp"))
        assert len(temp_files) == 0
        # Sprawdź czy plik docelowy istnieje
        assert (downloader.bin_dir / "whisper-cli").exists()

