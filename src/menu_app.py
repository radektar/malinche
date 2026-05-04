"""macOS menu bar application for Malinche."""

import sys
import threading
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List

from src.bootstrap import ensure_ready

# Bootstrap must run before any config-dependent imports.
ensure_ready()

try:
    import rumps
    RUMPS_AVAILABLE = True
except ImportError:
    RUMPS_AVAILABLE = False

try:
    from PyObjCTools import AppHelper
    _APPHELPER_AVAILABLE = True
except ImportError:
    _APPHELPER_AVAILABLE = False

try:
    from AppKit import NSThread
    _NSTHREAD_AVAILABLE = True
except ImportError:
    _NSTHREAD_AVAILABLE = False


def _is_main_thread() -> bool:
    """True gdy obecny wątek to Cocoa main thread."""
    if _NSTHREAD_AVAILABLE:
        try:
            return bool(NSThread.isMainThread())
        except Exception:
            return False
    return False


def _run_on_main_thread(func):
    """Schedule *func* on the main thread; fall back to direct call in tests.

    Gdy już jesteśmy na main thread, wywołujemy synchronicznie — schedule
    przez ``AppHelper.callAfter`` w połączeniu z blokującym ``Event.wait``
    powodował deadlock (callback czekał na runloop, który stał na wait).
    """
    if _is_main_thread():
        func()
        return
    if _APPHELPER_AVAILABLE:
        AppHelper.callAfter(func)
    else:
        func()

import threading

from src.config import config
from src.config.settings import UserSettings
from src.file_monitor import (
    DECISION_BLOCKED,
    DECISION_ONCE,
    DECISION_TRUSTED,
)
from src.logger import logger
from src.app_core import MalincheTranscriber
from src.app_status import AppStatus
from src.state_manager import reset_state
from src.transcriber import RetranscribeLockBusyError, send_notification
from src.setup.downloader import DependencyDownloader
from src.setup.dependency_manager import DependencyManager
from src.setup.errors import NetworkError, DiskSpaceError, DownloadError
from src.setup import SetupWizard
from src.ui.dialogs import choose_date_dialog, show_about_dialog
from src.ui.constants import TEXTS
from src.ui.settings_window import show_settings_window
from src.ui.pro_activation import show_pro_activation, show_pro_status
from src.ui.download_window import DownloadWindow
from src.config.license import license_manager
from src.config.features import FeatureTier


class MalincheMenuApp(rumps.App):
    """macOS menu bar application wrapper for Malinche."""

    def __init__(self):
        """Initialize menu bar application."""
        if not RUMPS_AVAILABLE:
            raise ImportError(
                "rumps not available. Install with: pip install rumps"
            )

        super(MalincheMenuApp, self).__init__(
            "Malinche",
            title=None,
            icon=None,
            template=True,
        )
        self._icon_paths = self._resolve_icon_paths()
        self._update_icon(AppStatus.IDLE)

        self.transcriber: Optional[MalincheTranscriber] = None
        self.daemon_thread: Optional[threading.Thread] = None
        self._running = False
        self._retranscription_in_progress = False
        self._retranscription_file: Optional[str] = None
        self._download_active = False
        self._download_manager = DependencyManager()
        self._download_window: Optional[DownloadWindow] = None

        # Create menu items
        self.status_item = rumps.MenuItem("Status: Inicjalizacja...")
        self.menu.add(self.status_item)
        self.menu.add(rumps.separator)

        self.open_logs_item = rumps.MenuItem(
            "Otwórz logi",
            callback=self._open_logs
        )
        self.menu.add(self.open_logs_item)

        self.reset_memory_item = rumps.MenuItem(
            "Resetuj pamięć od...",
            callback=self._reset_memory
        )
        self.menu.add(self.reset_memory_item)

        self.repair_whisper_item = rumps.MenuItem(
            "Napraw whisper-cli...",
            callback=self._repair_whisper_clicked,
        )
        self.menu.add(self.repair_whisper_item)

        self.manage_volumes_item = rumps.MenuItem(
            "Zarządzaj dyskami...",
            callback=self._manage_volumes_clicked,
        )
        self.menu.add(self.manage_volumes_item)

        # Retranscribe submenu
        self.retranscribe_menu = rumps.MenuItem("Retranskrybuj plik...")
        self.menu.add(self.retranscribe_menu)

        self.menu.add(rumps.separator)

        self.settings_item = rumps.MenuItem(
            "Ustawienia...",
            callback=self._show_settings
        )
        self.menu.add(self.settings_item)

        # PRO Activation / Status
        self.pro_item = rumps.MenuItem(
            "Aktywuj PRO...",
            callback=self._show_pro
        )
        self.menu.add(self.pro_item)

        self.about_item = rumps.MenuItem(
            "O aplikacji...",
            callback=self._show_about
        )
        self.menu.add(self.about_item)

        self.menu.add(rumps.separator)

        self.quit_item = rumps.MenuItem(
            "Zakończ",
            callback=self._quit_app
        )
        self.menu.add(self.quit_item)

        # Start status update timer
        rumps.Timer(self._update_status, 2).start()  # Update every 2 seconds
        
        # Start retranscribe menu refresh timer
        rumps.Timer(self._refresh_retranscribe_menu, 10).start()  # Update every 10 seconds
        
        # Check if wizard is needed (first run)
        self._dependencies_checked = False
        if SetupWizard.needs_setup():
            # Wizard will handle dependencies
            self._dependencies_checked = True
            rumps.Timer(self._run_wizard_if_needed, 0.5).start()
        else:
            # Normal start - check dependencies
            rumps.Timer(self._delayed_check_dependencies, 1).start()

    def _resolve_icon_paths(self) -> dict[AppStatus, Optional[str]]:
        """Resolve menu bar status icon paths for dev and bundled app."""
        candidates = []
        if getattr(sys, "frozen", False):
            candidates.append(Path(getattr(sys, "_MEIPASS", "")))
            candidates.append(Path(sys.executable).resolve().parent.parent / "Resources")
        candidates.append(Path(__file__).resolve().parent.parent / "assets")

        mapping = {
            AppStatus.IDLE: "idle.png",
            AppStatus.SCANNING: "scanning.png",
            AppStatus.TRANSCRIBING: "transcribing.png",
            AppStatus.DOWNLOADING: "transcribing.png",
            AppStatus.MIGRATING: "migrating.png",
            AppStatus.RECORDER_IDLE: "recorder_idle.png",
            AppStatus.RECORDER_PENDING: "recorder_pending.png",
            AppStatus.ERROR: "error.png",
        }
        resolved: dict[AppStatus, Optional[str]] = {key: None for key in mapping}

        for base in candidates:
            icon_dir = base / "menu_bar"
            for status, filename in mapping.items():
                if resolved[status]:
                    continue
                icon_path = icon_dir / filename
                try:
                    # A PNG header is at least 8 bytes + IHDR; anything smaller is
                    # a stale/corrupted placeholder we must ignore.
                    if icon_path.exists() and icon_path.stat().st_size > 64:
                        resolved[status] = str(icon_path)
                except OSError:
                    continue
        return resolved

    def _update_icon(self, status: AppStatus) -> None:
        """Update menu bar icon based on app status.

        When a template image is available we always clear the title so macOS
        does not render both the icon and a stray emoji/name fallback next to
        each other in the status bar.
        """
        icon_path = self._icon_paths.get(status)
        if icon_path:
            self.title = None
            self.template = True
            self.icon = icon_path
            return

        fallback_titles = {
            AppStatus.IDLE: "🎙️",
            AppStatus.SCANNING: "🔎",
            AppStatus.TRANSCRIBING: "⏳",
            AppStatus.DOWNLOADING: "⬇️",
            AppStatus.MIGRATING: "🔄",
            AppStatus.RECORDER_IDLE: "🟢",
            AppStatus.RECORDER_PENDING: "🟡",
            AppStatus.ERROR: "⚠️",
        }
        self.icon = None
        self.title = fallback_titles.get(status, "🎙️")

    def _run_wizard_if_needed(self, timer):
        """Uruchom wizard jeśli to pierwsze uruchomienie."""
        timer.stop()
        logger.info("Uruchamianie Setup Wizard...")
        wizard = SetupWizard()
        if wizard.run():
            # Wizard zakończony pomyślnie - start transcribera
            logger.info("Wizard zakończony - uruchamiam transcriber")
            self._start_daemon()
        else:
            # Użytkownik anulował
            self.status_item.title = "Status: Wymagana konfiguracja"
            rumps.alert(
                title="Konfiguracja niekompletna",
                message=(
                    "Malinche wymaga konfiguracji do działania.\n\n"
                    "Uruchom aplikację ponownie, aby dokończyć konfigurację."
                ),
                ok="OK",
            )

    def _delayed_check_dependencies(self, timer):
        """Sprawdź zależności po uruchomieniu aplikacji (z opóźnieniem)."""
        # Stop timer after first call
        timer.stop()

        if self._dependencies_checked:
            return

        self._dependencies_checked = True
        self._check_dependencies()
        # Onboarding banner po starcie (nieblokujący, jednorazowy per uruchomienie).
        self._maybe_run_volume_onboarding()

    def _maybe_run_volume_onboarding(self) -> None:
        """Pokaż banner migracji + (opcjonalnie) review podłączonych dysków.

        Wykonuje się gdy ``UserSettings.needs_volume_onboarding`` to True
        (typowo: świeża migracja z trybu ``auto`` → ``manual`` w v2.0.0-beta.2).
        """
        try:
            settings = UserSettings.load()
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Nie można załadować ustawień dla onboardingu: {exc}")
            return
        if not settings.needs_volume_onboarding:
            return

        choice = rumps.alert(
            title="🛡 Tryb bezpieczeństwa zaktualizowany",
            message=(
                "Od teraz każdy nowy dysk podłączony do komputera musi być "
                "zatwierdzony zanim Malinche zacznie z niego transkrybować. "
                "To zapobiega przypadkowemu skanowaniu np. dysków z muzyką.\n\n"
                "Czy chcesz teraz przejrzeć podłączone dyski i zdecydować, "
                "które są recorderami?"
            ),
            ok="Przejrzyj teraz",
            cancel="Później",
        )

        if choice != 1:
            # Odłożone — flaga zostaje, banner pokaże się przy następnym starcie.
            logger.info("Volume onboarding postponed by user")
            return

        # Reuse manualnej ścieżki — ta sama logika.
        self._review_mounted_volumes(settings)

    def _manage_volumes_clicked(self, _) -> None:
        """Menu item: zarządzanie listą zaufanych/zablokowanych dysków."""
        try:
            settings = UserSettings.load()
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Nie można załadować ustawień: {exc}")
            rumps.alert(title="Błąd", message=str(exc), ok="OK")
            return

        trusted = [tv for tv in settings.trusted_volumes if tv.decision == "trusted"]
        blocked = [tv for tv in settings.trusted_volumes if tv.decision == "blocked"]

        lines = []
        if trusted:
            lines.append("✅ Zaufane (transkrybowane):")
            for tv in trusted:
                lines.append(f"   • {tv.name}")
        if blocked:
            if lines:
                lines.append("")
            lines.append("🚫 Zablokowane (pomijane):")
            for tv in blocked:
                lines.append(f"   • {tv.name}")
        if not lines:
            lines.append("Brak zatwierdzonych dysków.")
            lines.append("Podłącz dysk lub wybierz 'Przejrzyj /Volumes' poniżej.")

        message = "\n".join(lines) + "\n\nCo chcesz zrobić?"

        choice = rumps.alert(
            title="🛡 Zarządzaj dyskami",
            message=message,
            ok="Przejrzyj /Volumes",
            cancel="Zamknij",
            other="Wyczyść decyzje",
        )

        if choice == 1:  # Przejrzyj /Volumes
            self._review_mounted_volumes(settings)
        elif choice == -1:  # Wyczyść decyzje (other button)
            confirm = rumps.alert(
                title="Wyczyścić decyzje?",
                message=(
                    "Wszystkie zaufane i zablokowane dyski zostaną usunięte z listy. "
                    "Przy następnym podłączeniu dysku app zapyta od nowa."
                ),
                ok="Wyczyść",
                cancel="Anuluj",
            )
            if confirm == 1:
                settings.trusted_volumes = []
                settings.save()
                rumps.alert(title="Wyczyszczono", message="Lista decyzji jest pusta.", ok="OK")

    def _review_mounted_volumes(self, settings: UserSettings) -> None:
        """Iteruj po podłączonych /Volumes i pytaj o nieznane dyski.

        Współdzielona ścieżka między onboardingiem a manualnym przeglądem.
        """
        from pathlib import Path
        from src.config.defaults import defaults as _defaults
        from src.volume_identity import get_volume_uuid

        volumes_root = Path("/Volumes")
        if not volumes_root.exists():
            rumps.alert(title="Brak /Volumes", message="Katalog /Volumes nie istnieje.", ok="OK")
            return

        try:
            candidates = sorted(volumes_root.iterdir(), key=lambda p: p.name)
        except OSError as error:
            logger.error(f"Manage volumes: could not list /Volumes: {error}")
            rumps.alert(title="Błąd", message=str(error), ok="OK")
            return

        skipped_existing = 0
        skipped_system = 0
        reviewed = 0
        for candidate in candidates:
            if not candidate.is_dir():
                continue
            if candidate.name in _defaults.SYSTEM_VOLUMES:
                skipped_system += 1
                continue
            uuid = get_volume_uuid(candidate)
            if settings.find_trusted_volume(uuid) is not None:
                skipped_existing += 1
                continue
            decision = self._prompt_unknown_volume(candidate, uuid)
            if decision == DECISION_TRUSTED:
                settings.add_trusted_volume(uuid, candidate.name, "trusted")
                reviewed += 1
            elif decision == DECISION_BLOCKED:
                settings.add_trusted_volume(uuid, candidate.name, "blocked")
                reviewed += 1

        settings.needs_volume_onboarding = False
        settings.save()

        summary_lines = [f"Przejrzano dyski w /Volumes:"]
        summary_lines.append(f"• Zatwierdzono nowych decyzji: {reviewed}")
        if skipped_existing:
            summary_lines.append(f"• Pominięto już znane: {skipped_existing}")
        if skipped_system:
            summary_lines.append(f"• Pominięto systemowe: {skipped_system}")
        rumps.alert(title="Zakończono", message="\n".join(summary_lines), ok="OK")

    def _check_dependencies(self):
        """Sprawdź czy wszystkie zależności są zainstalowane."""
        try:
            status = self._download_manager.status()
            if status.ready:
                # Płytkie sprawdzenie OK — teraz głęboka weryfikacja (checksum + runtime).
                health = self._download_manager.health_check()
                if health.ok:
                    logger.info("✓ Wszystkie zależności zainstalowane i zweryfikowane")
                    return True

                logger.warning(
                    "Health check NIEUDANY: %s (repair=%s)",
                    health.reason,
                    health.needs_whisper_repair,
                )
                if health.needs_whisper_repair:
                    self._prompt_whisper_repair(health.reason or "")
                else:
                    self.status_item.title = "Status: Wymagana naprawa zależności"
                return False
            
            # Brakuje zależności - pokaż komunikat
            logger.warning("Brakuje zależności - wymagane pobranie")
            model = config.WHISPER_MODEL
            size_mb = status.total_missing_size / 1_000_000
            response = rumps.alert(
                title="📥 Pobieranie zależności",
                message=(
                    f"Wybrany model: {model}\n"
                    f"Brakujące dane: ~{size_mb:.0f}MB.\n\n"
                    "Czy chcesz pobrać teraz?\n\n"
                    "Pobieranie działa w tle - aplikacja pozostanie responsywna."
                ),
                ok="Pobierz teraz",
                cancel="Pomiń"
            )
            
            if response == 1:  # OK clicked
                self._download_dependencies()
            else:
                logger.info("Użytkownik pominął pobieranie zależności")
                self.status_item.title = "Status: Wymagane pobranie zależności"
            
            return False
            
        except (NetworkError, DiskSpaceError, DownloadError) as e:
            logger.error(f"Błąd podczas sprawdzania zależności: {e}")
            rumps.alert(
                title="⚠️ Błąd",
                message=f"Nie można pobrać zależności:\n\n{str(e)}",
                ok="OK"
            )
            self.status_item.title = "Status: Błąd pobierania zależności"
            return False
        except Exception as e:
            logger.error(f"Nieoczekiwany błąd: {e}", exc_info=True)
            return False
    
    def _download_dependencies(self):
        """Pobierz wszystkie brakujące zależności asynchronicznie."""
        if self._download_active:
            return
        self._download_active = True
        self._update_icon(AppStatus.DOWNLOADING)
        self.status_item.title = "Status: Pobieranie zależności..."
        self._download_window = DownloadWindow(
            title="Pobieranie zależności",
            detail="Start pobierania...",
        )
        self._download_window.show()

        def progress_callback(name: str, progress: float):
            """Update status z postępem pobierania."""
            percent = int(progress * 100)
            self.status_item.title = f"Status: Pobieranie {name}... {percent}%"
            if self._download_window is not None:
                self._download_window.update(
                    detail=f"Pobieranie: {name}",
                    progress=progress,
                )
            logger.debug(f"Pobieranie {name}: {percent}%")

        def done_callback():
            def _on_main() -> None:
                self._download_active = False
                if self._download_window is not None:
                    self._download_window.update(detail="Pobieranie zakończone", progress=1.0)
                    self._download_window.close()
                logger.info("✓ Wszystkie zależności pobrane")
                rumps.alert(
                    title="✅ Gotowe",
                    message="Wszystkie zależności zostały pobrane.\n\nAplikacja jest gotowa do użycia.",
                    ok="OK"
                )
                self.status_item.title = "Status: Gotowe"
                self._update_icon(AppStatus.IDLE)
            _run_on_main_thread(_on_main)

        def error_callback(exc: Exception):
            def _on_main() -> None:
                self._download_active = False
                if self._download_window is not None:
                    self._download_window.update(detail=f"Błąd: {exc}")
                if isinstance(exc, NetworkError):
                    logger.error(f"Brak połączenia: {exc}")
                    rumps.alert(
                        title="⚠️ Brak połączenia",
                        message=(
                            "Brak połączenia z internetem.\n\n"
                            "Malinche wymaga jednorazowego pobrania silnika transkrypcji (~500MB).\n"
                            "Połącz się z internetem i spróbuj ponownie."
                        ),
                        ok="OK"
                    )
                    self.status_item.title = "Status: Brak połączenia"
                elif isinstance(exc, DiskSpaceError):
                    logger.error(f"Brak miejsca: {exc}")
                    rumps.alert(
                        title="⚠️ Brak miejsca",
                        message=str(exc),
                        ok="OK"
                    )
                    self.status_item.title = "Status: Brak miejsca"
                elif isinstance(exc, DownloadError):
                    logger.error(f"Błąd pobierania: {exc}")
                    rumps.alert(
                        title="⚠️ Błąd pobierania",
                        message=f"Nie udało się pobrać zależności:\n\n{str(exc)}\n\nSpróbuj ponownie później.",
                        ok="OK"
                    )
                    self.status_item.title = "Status: Błąd pobierania"
                else:
                    logger.error(f"Nieoczekiwany błąd: {exc}", exc_info=True)
                    rumps.alert(
                        title="⚠️ Błąd",
                        message=f"Nieoczekiwany błąd:\n\n{str(exc)}",
                        ok="OK"
                    )
                    self.status_item.title = "Status: Błąd"
                self._update_icon(AppStatus.ERROR)
            _run_on_main_thread(_on_main)

        started = self._download_manager.download_async(
            on_progress=progress_callback,
            on_done=done_callback,
            on_error=error_callback,
        )
        if not started:
            self._download_active = True

    def _prompt_whisper_repair(self, reason: str) -> None:
        """Pokaż dialog naprawy whisper-cli i opcjonalnie ją uruchom."""
        self.status_item.title = "Status: Wymagana naprawa whisper-cli"
        self._update_icon(AppStatus.ERROR)
        response = rumps.alert(
            title="⚠️ Whisper-cli wymaga naprawy",
            message=(
                f"{reason}\n\n"
                "Pobranie ~3 MB poprawnego pliku zwykle naprawia transkrypcję.\n"
                "Pobieranie działa w tle - aplikacja pozostanie responsywna."
            ),
            ok="Napraw teraz",
            cancel="Pomiń",
        )
        if response == 1:
            self._run_repair_whisper()

    def _repair_whisper_clicked(self, _) -> None:
        """Manualne uruchomienie naprawy z menu."""
        if self._download_active:
            rumps.alert(
                title="Pobieranie w toku",
                message="Poczekaj aż aktualne pobieranie się zakończy.",
                ok="OK",
            )
            return
        confirm = rumps.alert(
            title="Naprawa whisper-cli",
            message=(
                "Usunie się obecny plik whisper-cli i pobierze ponownie z release.\n"
                "Pobieranie działa w tle (~3 MB)."
            ),
            ok="Napraw",
            cancel="Anuluj",
        )
        if confirm == 1:
            self._run_repair_whisper()

    def _run_repair_whisper(self) -> None:
        """Uruchomienie naprawy whisper-cli w tle (wspólna ścieżka)."""
        if self._download_active:
            return
        self._download_active = True
        self._update_icon(AppStatus.DOWNLOADING)
        self.status_item.title = "Status: Naprawa whisper-cli..."
        self._download_window = DownloadWindow(
            title="Naprawa whisper-cli",
            detail="Usuwanie i ponowne pobranie whisper-cli...",
        )
        self._download_window.show()

        def progress_callback(name: str, progress: float) -> None:
            percent = int(progress * 100)
            self.status_item.title = f"Status: Naprawa {name}... {percent}%"
            if self._download_window is not None:
                self._download_window.update(
                    detail=f"Pobieranie: {name}",
                    progress=progress,
                )

        def done_callback() -> None:
            def _on_main() -> None:
                self._download_active = False
                if self._download_window is not None:
                    self._download_window.update(detail="Naprawa zakończona", progress=1.0)
                    self._download_window.close()
                logger.info("✓ Whisper-cli naprawiony")
                rumps.alert(
                    title="✅ Naprawiono",
                    message="Whisper-cli pobrany ponownie. Transkrypcja powinna już działać.",
                    ok="OK",
                )
                self.status_item.title = "Status: Gotowe"
                self._update_icon(AppStatus.IDLE)
            _run_on_main_thread(_on_main)

        def error_callback(exc: Exception) -> None:
            def _on_main() -> None:
                self._download_active = False
                if self._download_window is not None:
                    self._download_window.update(detail=f"Błąd: {exc}")
                logger.error("Naprawa whisper-cli nieudana: %s", exc, exc_info=True)
                rumps.alert(
                    title="⚠️ Błąd naprawy",
                    message=f"Nie udało się pobrać whisper-cli:\n\n{exc}",
                    ok="OK",
                )
                self.status_item.title = "Status: Błąd naprawy"
                self._update_icon(AppStatus.ERROR)
            _run_on_main_thread(_on_main)

        started = self._download_manager.repair_whisper_async(
            on_progress=progress_callback,
            on_done=done_callback,
            on_error=error_callback,
        )
        if not started:
            self._download_active = False
            logger.warning("Naprawa whisper-cli nie wystartowała (download w toku)")

    def _prompt_unknown_volume(self, volume_path, uuid: str) -> str:
        """Synchronicznie zapytaj usera o nieznany dysk: Tak/Nie/Raz.

        Wywoływane z wątku FileMonitora. Dialog rumps musi działać na main
        thread, więc używamy AppHelper + threading.Event do synchronizacji.

        Returns:
            Jedną z DECISION_TRUSTED / DECISION_BLOCKED / DECISION_ONCE.
        """
        result = {"decision": DECISION_BLOCKED}
        done = threading.Event()
        volume_name = volume_path.name if hasattr(volume_path, "name") else str(volume_path)

        def _ask_on_main() -> None:
            try:
                response = rumps.alert(
                    title="🛡 Nowy dysk wykryty",
                    message=(
                        f"Czy '{volume_name}' to recorder do transkrypcji?\n\n"
                        "• Tak — zapamiętaj jako recorder i transkrybuj\n"
                        "• Nie — zapamiętaj jako niezaufany i zignoruj\n"
                        "• Tylko raz — transkrybuj teraz, ale nie zapamiętuj"
                    ),
                    ok="Tak",
                    cancel="Nie",
                    other="Tylko raz",
                )
                if response == 1:
                    result["decision"] = DECISION_TRUSTED
                elif response == -1:
                    result["decision"] = DECISION_ONCE
                else:
                    result["decision"] = DECISION_BLOCKED
            except Exception as exc:  # noqa: BLE001
                logger.error(
                    f"Dialog _prompt_unknown_volume failed: {exc}",
                    exc_info=True,
                )
                result["decision"] = DECISION_BLOCKED
            finally:
                done.set()

        _run_on_main_thread(_ask_on_main)
        # Czekaj na decyzję; UI się nie zawiesi (rumps.alert na main jest modalny).
        done.wait(timeout=600)
        decision = result["decision"]
        logger.info(
            f"Volume '{volume_name}' (uuid={uuid}) decision={decision}"
        )
        return decision


    def _update_status(self, _):
        """Update status menu item based on current state."""
        # Update PRO item label based on current tier
        tier = license_manager.get_current_tier()
        if tier == FeatureTier.FREE:
            self.pro_item.title = "Aktywuj PRO..."
        else:
            self.pro_item.title = "💎 Malinche PRO"

        if not self.transcriber:
            self.status_item.title = "Status: Nie uruchomiono"
            self._update_icon(AppStatus.IDLE)
            return

        # Check retranscription first (takes priority)
        if self._retranscription_in_progress:
            filename = self._retranscription_file or "..."
            self.status_item.title = f"Status: Retranskrybowanie {filename}"
            self._update_icon(AppStatus.TRANSCRIBING)
            return

        if self._download_active:
            self._update_icon(AppStatus.DOWNLOADING)
            return

        state = self.transcriber.state
        status_str = state.get_status_string()
        self.status_item.title = f"Status: {status_str}"

        self._update_icon(state.status)

    def _open_logs(self, _):
        """Open log file in default editor."""
        log_file = config.LOG_FILE
        if not log_file.exists():
            rumps.alert(
                "Błąd",
                f"Plik logów nie istnieje: {log_file}",
                "OK"
            )
            return

        try:
            # Use macOS 'open' command to open in default editor
            subprocess.run(
                ["open", "-t", str(log_file)],
                check=True,
                timeout=5.0
            )
        except subprocess.TimeoutExpired:
            rumps.alert("Błąd", "Timeout przy otwieraniu logów", "OK")
        except Exception as e:
            rumps.alert(
                "Błąd",
                f"Nie można otworzyć logów: {e}",
                "OK"
            )

    def _reset_memory(self, _):
        """Reset transcription memory to a specific date."""
        target_date = choose_date_dialog(default_days=7)
        
        if target_date is None:
            logger.info("User cancelled reset memory dialog")
            return  # User cancelled
        
        logger.info(f"Resetting memory to date: {target_date.strftime('%Y-%m-%d')}")
        success = reset_state(target_date)

        if success:
            logger.info(f"Memory reset successful, sending notification for date: {target_date.strftime('%Y-%m-%d')}")
            # Use send_notification instead of rumps.notification for better reliability
            # Note: send_notification signature is (title, message, subtitle="")
            send_notification(
                title="Malinche",
                message=f"Od: {target_date.strftime('%Y-%m-%d')}",
                subtitle=TEXTS["reset_memory_success"]
            )
        else:
            logger.error("Failed to reset memory state")
            rumps.alert(
                "Błąd",
                TEXTS["reset_memory_error"],
                ok="OK"
            )

    def _show_settings(self, _):
        """Show settings window."""
        show_settings_window()

    def _show_pro(self, _):
        """Show PRO activation or status dialog."""
        show_pro_status()

    def _show_about(self, _):
        """Show About dialog with app information."""
        show_about_dialog()

    def _get_staged_files(self) -> List[Path]:
        """Get list of audio files in staging directory.
        
        Returns:
            List of audio file paths, sorted by modification time
            (newest first), limited to 10 files
        """
        if not config.LOCAL_RECORDINGS_DIR.exists():
            return []
        
        files = []
        for ext in config.AUDIO_EXTENSIONS:
            # Search both lowercase and uppercase extensions
            files.extend(config.LOCAL_RECORDINGS_DIR.glob(f"*{ext}"))
            files.extend(config.LOCAL_RECORDINGS_DIR.glob(f"*{ext.upper()}"))
        
        # Sort by modification time (newest first) and limit to 10
        sorted_files = sorted(
            files,
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )[:10]
        
        return sorted_files

    def _refresh_retranscribe_menu(self, _):
        """Refresh the retranscribe submenu with current staged files."""
        if license_manager.get_current_tier() == FeatureTier.FREE:
            self.retranscribe_menu.title = "Retranskrypcja (PRO)"
            try:
                if self.retranscribe_menu._menu is not None:
                    self.retranscribe_menu.clear()
            except (AttributeError, TypeError):
                pass
            locked_item = rumps.MenuItem("Upgrade do PRO, aby tworzyć wersje v2/v3")
            locked_item.set_callback(None)
            self.retranscribe_menu.add(locked_item)
            return

        self.retranscribe_menu.title = "Retranskrybuj plik..."
        # Clear existing submenu items (handle case when _menu is not yet initialized)
        try:
            if self.retranscribe_menu._menu is not None:
                self.retranscribe_menu.clear()
        except (AttributeError, TypeError):
            pass
        
        # Show busy state during retranscription
        if self._retranscription_in_progress:
            busy_item = rumps.MenuItem(
                f"⏳ Retranskrybowanie: {self._retranscription_file or '...'}"
            )
            busy_item.set_callback(None)
            self.retranscribe_menu.add(busy_item)
            return
        
        staged_files = self._get_staged_files()
        
        if not staged_files:
            empty_item = rumps.MenuItem("(brak plików w staging)")
            empty_item.set_callback(None)
            self.retranscribe_menu.add(empty_item)
            return
        
        for audio_file in staged_files:
            try:
                mtime = datetime.fromtimestamp(audio_file.stat().st_mtime)
                date_str = mtime.strftime("%d.%m.%Y %H:%M")
                label = f"📁 {audio_file.name} ({date_str})"
            except OSError:
                label = f"📁 {audio_file.name}"
            
            item = rumps.MenuItem(label)
            # Store file path for callback
            item._audio_path = audio_file
            item.set_callback(self._retranscribe_file_callback)
            self.retranscribe_menu.add(item)

    def _retranscribe_file_callback(self, sender):
        """Handle retranscribe menu item click."""
        audio_path = getattr(sender, '_audio_path', None)
        if not audio_path:
            return
        
        # Check if retranscription already in progress
        if self._retranscription_in_progress:
            rumps.alert(
                "Retranskrypcja w toku",
                f"Poczekaj na zakończenie retranskrypcji:\n{self._retranscription_file}",
                ok="OK"
            )
            return
        
        # Check if automatic transcription is in progress
        if self.transcriber and self.transcriber.state.status == AppStatus.TRANSCRIBING:
            rumps.alert(
                "Transkrypcja w toku",
                "Poczekaj na zakończenie bieżącej transkrypcji.",
                ok="OK"
            )
            return
        
        # Confirm with user
        response = rumps.alert(
            "Retranskrypcja",
            f"Czy na pewno chcesz ponownie transkrybować:\n\n"
            f"{audio_path.name}\n\n"
            f"Istniejąca transkrypcja zostanie usunięta.",
            ok="Tak, retranskrybuj",
            cancel="Anuluj"
        )
        
        if response != 1:  # Cancel
            return
        
        # Set flag BEFORE starting thread
        self._retranscription_in_progress = True
        self._retranscription_file = audio_path.name
        
        # Send start notification
        send_notification(
            title="Malinche",
            subtitle="Rozpoczęto retranskrypcję",
            message=f"Plik: {audio_path.name}"
        )
        
        # Run retranscription in background thread
        def do_retranscribe():
            try:
                if self.transcriber and self.transcriber.transcriber:
                    success = self.transcriber.transcriber.force_retranscribe(audio_path)

                    if success:
                        send_notification(
                            title="Malinche",
                            subtitle="Retranskrypcja zakończona",
                            message=f"Plik: {audio_path.name}"
                        )
                    else:
                        send_notification(
                            title="Malinche",
                            subtitle="Retranskrypcja nieudana",
                            message=f"Sprawdź logi: {audio_path.name}"
                        )
            except RetranscribeLockBusyError:
                logger.info(
                    "Retranscribe lock-busy for %s — informing user",
                    audio_path.name,
                )
                def _on_main_lock_busy() -> None:
                    rumps.alert(
                        title="⏳ Auto transkrypcja w toku",
                        message=(
                            "Aplikacja właśnie przetwarza inny plik z dyktafonu.\n\n"
                            "Spróbuj ponownie za kilka minut, gdy automatyczna "
                            "transkrypcja się zakończy."
                        ),
                        ok="OK",
                    )
                _run_on_main_thread(_on_main_lock_busy)
            except Exception as e:
                logger.error(f"Retranscribe error: {e}", exc_info=True)
                send_notification(
                    title="Malinche",
                    subtitle="Błąd",
                    message=str(e)[:50]
                )
            finally:
                # Always clear flag when done
                self._retranscription_in_progress = False
                self._retranscription_file = None
        
        thread = threading.Thread(target=do_retranscribe, daemon=True)
        thread.start()

    def _quit_app(self, _):
        """Quit application gracefully."""
        response = rumps.alert(
            "Zakończ",
            "Czy na pewno chcesz zakończyć aplikację?",
            ok="Tak",
            cancel="Anuluj"
        )

        if response == 1:  # "OK" button (1 = OK, 0 = Cancel)
            self._shutdown()
            rumps.quit_application()

    def _shutdown(self):
        """Shutdown transcriber daemon."""
        if self.transcriber:
            logger.info("Shutting down transcriber from menu app...")
            self.transcriber.stop()
            self._running = False

            # Wait for daemon thread to finish
            if self.daemon_thread and self.daemon_thread.is_alive():
                self.daemon_thread.join(timeout=5.0)

    def _notify_billing_error(self, exc: Exception) -> None:
        """Show a one-time alert when Claude API hits a permanent error."""
        exc_str = str(exc).lower()
        if "credit balance" in exc_str:
            title = "⚠️ Claude API: Niedostateczne kredyty"
            message = (
                "Twoje konto Anthropic (BYOK) ma wyczerpane kredyty.\n\n"
                "Doładuj je w: https://console.anthropic.com/account/billing\n\n"
                "Do końca tej sesji Malinche transkrybuje bez AI "
                "podsumowań i tagów (Whisper działa normalnie)."
            )
        elif "not_found" in exc_str or "model" in exc_str:
            title = "⚠️ Claude API: Nieznany model"
            message = (
                "Model Claude skonfigurowany w ustawieniach nie istnieje "
                "lub został wycofany.\n\n"
                "Zmień model w Ustawieniach → AI.\n\n"
                "Do końca tej sesji Malinche transkrybuje bez AI "
                "podsumowań i tagów (Whisper działa normalnie)."
            )
        else:
            title = "⚠️ Claude API: Błąd trwały"
            message = (
                f"Claude API zwróciło błąd trwały:\n{exc}\n\n"
                "Do końca tej sesji Malinche transkrybuje bez AI "
                "podsumowań i tagów (Whisper działa normalnie)."
            )

        def _on_main() -> None:
            try:
                rumps.alert(title=title, message=message, ok="Zrozumiano")
            except Exception as alert_exc:  # noqa: BLE001
                logger.error("AI error alert failed to display: %s", alert_exc)

        _run_on_main_thread(_on_main)

    def _run_daemon(self):
        """Run transcriber daemon in background thread."""
        try:
            logger.info("Starting transcriber daemon from menu app...")
            # Don't setup signal handlers in background thread
            self.transcriber = MalincheTranscriber(setup_signals=False)
            self.transcriber.set_ai_billing_callback(self._notify_billing_error)
            self.transcriber.set_unknown_volume_callback(self._prompt_unknown_volume)
            self.transcriber.start()
        except Exception as e:
            logger.error(f"Error in daemon thread: {e}", exc_info=True)
            rumps.notification(
                title="Malinche",
                subtitle="Błąd",
                message=f"Błąd uruchomienia: {e}"
            )

    def _start_daemon(self):
        """Uruchom daemon transcribera w tle."""
        if self._running:
            return  # Already running
        
        logger.info("Uruchamianie daemona transcribera...")
        self._running = True
        self.daemon_thread = threading.Thread(
            target=self._run_daemon,
            daemon=True,
            name="TranscriberDaemon"
        )
        self.daemon_thread.start()

    def run(self):
        """Start the menu bar application."""
        logger.info("=" * 60)
        logger.info("🚀 Malinche Menu App starting...")
        logger.info("=" * 60)

        # If wizard is not needed, start daemon immediately
        if not SetupWizard.needs_setup():
            self._start_daemon()

        # Run menu app (blocks until quit)
        super(MalincheMenuApp, self).run()


def main():
    """Main entry point for menu app."""
    if not RUMPS_AVAILABLE:
        print("ERROR: rumps not available. Install with: pip install rumps")
        sys.exit(1)

    try:
        app = MalincheMenuApp()
        app.run()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

