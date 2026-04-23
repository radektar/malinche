"""Tests for lightweight download window wrapper."""

from src.ui.download_window import DownloadWindow


def test_download_window_state_updates_without_appkit():
    window = DownloadWindow(title="Test", detail="Start")
    window.update(detail="Half", progress=0.5)
    assert window.state.detail == "Half"
    assert window.state.progress == 0.5
    window.close()
    assert window.state.closed is True

