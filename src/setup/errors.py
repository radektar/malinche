"""Custom exceptions for dependency downloader."""


class DownloadError(Exception):
    """Błąd podczas pobierania pliku."""

    pass


class ChecksumError(Exception):
    """Checksum nie zgadza się."""

    pass


class NetworkError(Exception):
    """Brak połączenia z internetem."""

    pass


class DiskSpaceError(Exception):
    """Brak miejsca na dysku."""

    pass


class DependencyRuntimeError(DownloadError):
    """Zależność jest pobrana, ale nie uruchamia się poprawnie."""

    pass



