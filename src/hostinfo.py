"""Host metadata helpers."""

import socket


def get_hostname() -> str:
    """Return hostname used for transcription metadata."""
    return socket.gethostname()

