"""First-run setup wizard."""

import rumps
import threading
from enum import Enum, auto
from pathlib import Path
from typing import Optional

from src.config import UserSettings, SUPPORTED_LANGUAGES, SUPPORTED_MODELS
from src.setup.downloader import DependencyDownloader
from src.setup.dependency_manager import DependencyManager
from src.setup.permissions import check_full_disk_access, open_fda_preferences
from src.logger import logger
from src.ui.dialogs import choose_folder_dialog
from src.ui.constants import TEXTS
from src.ui.constants import APP_VERSION
from src.ui.download_window import DownloadWindow
from src.vault_index import is_icloud_synced


class WizardStep(Enum):
    """Kroki wizarda konfiguracji."""

    WELCOME = auto()
    DOWNLOAD = auto()
    PERMISSIONS = auto()
    SOURCE_CONFIG = auto()
    BASIC_CONFIG = auto()
    AI_CONFIG = auto()
    FINISH = auto()


class SetupWizard:
    """First-run setup wizard."""

    STEPS_ORDER = [
        WizardStep.WELCOME,
        WizardStep.SOURCE_CONFIG,
        WizardStep.BASIC_CONFIG,
        WizardStep.DOWNLOAD,
        WizardStep.PERMISSIONS,
        WizardStep.AI_CONFIG,
        WizardStep.FINISH,
    ]

    def __init__(self):
        """Inicjalizacja wizarda."""
        self.current_step_index = 0
        self.settings = UserSettings.load()
        self.downloader = DependencyDownloader(
            progress_callback=self._on_progress
        )
        self.dependency_manager = DependencyManager(self.downloader)
        self._download_status = ""
        self._download_in_progress = False
        self._download_error: Optional[Exception] = None
        self._download_complete = False
        self._wizard_completed = False
        self._download_window: Optional[DownloadWindow] = None
        self._restore_step_from_settings()

    def _restore_step_from_settings(self) -> None:
        """Restore wizard position from persisted setup_stage when available."""
        stage_name = (self.settings.setup_stage or "").lower()
        stage_map = {
            "welcome": WizardStep.WELCOME,
            "source_config": WizardStep.SOURCE_CONFIG,
            "basic_config": WizardStep.BASIC_CONFIG,
            "download": WizardStep.DOWNLOAD,
            "permissions": WizardStep.PERMISSIONS,
            "ai_config": WizardStep.AI_CONFIG,
            "finish": WizardStep.FINISH,
        }
        step = stage_map.get(stage_name)
        if step in self.STEPS_ORDER:
            self.current_step_index = self.STEPS_ORDER.index(step)

    def _persist_stage(self) -> None:
        """Persist current stage to support wizard resume after interruption."""
        self.settings.setup_stage = self.current_step.name.lower()
        self.settings.save()

    @staticmethod
    def _version_line(version: str) -> str:
        """Return major.minor part used for setup compatibility checks."""
        parts = (version or "").split(".")
        if len(parts) < 2:
            return version or ""
        return ".".join(parts[:2])

    @staticmethod
    def needs_setup() -> bool:
        """Sprawdź czy wizard jest potrzebny."""
        settings = UserSettings.load()
        if not settings.setup_completed:
            return True

        # Re-run wizard only when compatibility line changes (major.minor),
        # not for alpha/patch bumps inside the same release line.
        return SetupWizard._version_line(settings.setup_version) != SetupWizard._version_line(
            APP_VERSION
        )

    @property
    def current_step(self) -> WizardStep:
        """Zwróć aktualny krok wizarda."""
        return self.STEPS_ORDER[self.current_step_index]

    def run(self) -> bool:
        """Uruchom wizard. Zwraca True jeśli ukończony pomyślnie."""
        logger.info("Uruchamianie Setup Wizard")
        
        self._wizard_completed = False
        
        # Uruchom pierwszy krok - wizard działa synchronicznie
        # Każdy krok blokuje do zakończenia (włącznie z pobieraniem)
        self._process_wizard_step()
        
        return self._wizard_completed

    def _process_wizard_step(self):
        """Przetwórz aktualny krok wizarda."""
        self._persist_stage()
        if self.current_step == WizardStep.FINISH:
            # Finalizacja
            self._show_finish()
            self.settings.setup_completed = True
            self.settings.setup_version = APP_VERSION
            self.settings.setup_stage = WizardStep.FINISH.name.lower()
            self.settings.save()
            logger.info("Setup Wizard zakończony pomyślnie")
            self._wizard_completed = True
            return
        
        result = self._run_current_step()

        if result == "cancel":
            logger.info("Wizard anulowany przez użytkownika")
            self._wizard_completed = False
            return
        elif result == "back" and self.current_step_index > 0:
            self.current_step_index -= 1
            # Kontynuuj natychmiast (synchronicznie)
            self._process_wizard_step()
        elif result == "next":
            self.current_step_index += 1
            # Kontynuuj natychmiast (synchronicznie)
            self._process_wizard_step()

    def _run_current_step(self) -> str:
        """Wykonaj aktualny krok."""
        step_handlers = {
            WizardStep.WELCOME: self._show_welcome,
            WizardStep.DOWNLOAD: self._show_download,
            WizardStep.PERMISSIONS: self._show_permissions,
            WizardStep.SOURCE_CONFIG: self._show_source_config,
            WizardStep.BASIC_CONFIG: self._show_basic_config,
            WizardStep.AI_CONFIG: self._show_ai_config,
        }
        handler = step_handlers.get(self.current_step)
        if handler:
            return handler()
        return "next"

    def _on_progress(self, name: str, progress: float):
        """Callback postępu pobierania - wywoływany z wątku pobierania."""
        self._download_status = f"{name}: {int(progress * 100)}%"
        logger.debug(f"Pobieranie: {self._download_status}")

        if self._download_window is not None:
            self._download_window.update(
                detail=f"Pobieranie: {name}",
                progress=progress,
            )

        # Wyślij notyfikację co 25% postępu
        percent = int(progress * 100)
        if percent in {25, 50, 75, 100}:
            rumps.notification(
                title="Malinche - Pobieranie",
                subtitle=f"{name}",
                message=f"Postęp: {percent}%"
            )

    def _show_welcome(self) -> str:
        """Ekran powitalny."""
        response = rumps.alert(
            title="🎙️ Witaj w Malinche!",
            message=(
                "Malinche automatycznie transkrybuje nagrania "
                "z Twojego dyktafonu lub karty SD.\n\n"
                "Przeprowadzimy Cię przez szybką konfigurację.\n\n"
                "Zajmie to około 3-5 minut."
            ),
            ok="Rozpocznij →",
            cancel="Anuluj",
        )
        return "next" if response == 1 else "cancel"

    def _show_download(self) -> str:
        """Pobieranie zależności dla wybranego modelu."""
        status = self.dependency_manager.status()
        if status.ready:
            logger.info("Zależności już zainstalowane - pomijam krok")
            return "next"

        model = self.settings.whisper_model
        total_mb = status.total_missing_size / 1_000_000
        response = rumps.alert(
            title="📥 Pobieranie silnika transkrypcji",
            message=(
                f"Wybrany model: {model}\n"
                f"Brakujące dane do pobrania: ~{total_mb:.0f} MB\n\n"
                "Czy pobrać teraz? Możesz wrócić i zmienić model."
            ),
            ok="Pobierz teraz",
            cancel="Zmień model",
            other="Anuluj",
        )

        if response == 0:
            return "back"
        if response != 1:
            return "cancel"

        self._download_in_progress = True
        self._download_complete = False
        self._download_error = None
        self._download_status = "Rozpoczynanie..."

        self._download_window = DownloadWindow(
            title="Pobieranie zależności",
            detail=f"Model: {model}",
        )
        self._download_window.show()
        self._download_in_background()

        # Pobieranie kontynuuje się w tle. Wizard idzie dalej od razu -
        # użytkownik widzi postęp w `DownloadWindow`, które zamknie się
        # samo po sukcesie (lub pozostanie z komunikatem błędu).
        return "next"

    def _download_in_background(self):
        """Start asynchronous download and update wizard flags from callbacks."""
        logger.info("Rozpoczęto pobieranie zależności w tle")

        def _done() -> None:
            self._download_complete = True
            self._download_in_progress = False
            if self._download_window is not None:
                self._download_window.update(
                    detail="✓ Pobrano pomyślnie", progress=1.0
                )
                self._download_window.close_after(1.2)
            try:
                rumps.notification(
                    title="Malinche",
                    subtitle="Pobieranie zakończone",
                    message="Silnik transkrypcji jest gotowy.",
                )
            except Exception:
                pass
            logger.info("✓ Pobieranie zakończone pomyślnie")

        def _error(exc: Exception) -> None:
            self._download_error = exc
            self._download_in_progress = False
            if self._download_window is not None:
                self._download_window.update(detail=f"❌ Błąd: {exc}")
            try:
                rumps.notification(
                    title="Malinche",
                    subtitle="Pobieranie nie powiodło się",
                    message=str(exc),
                )
            except Exception:
                pass
            logger.error(f"Błąd podczas pobierania: {exc}", exc_info=True)

        started = self.dependency_manager.download_async(
            on_progress=self._on_progress,
            on_done=_done,
            on_error=_error,
        )
        if not started:
            self._download_in_progress = True

    def _show_permissions(self) -> str:
        """Instrukcje Full Disk Access - skip jeśli już nadane."""
        if check_full_disk_access():
            logger.info("FDA już nadane - pomijam krok")
            return "next"

        response = rumps.alert(
            title="🔐 Uprawnienia dostępu do dysków",
            message=(
                "Aby automatycznie wykrywać dyktafon, Malinche "
                "potrzebuje uprawnień 'Full Disk Access'.\n\n"
                "Instrukcja:\n"
                "1. Kliknij 'Otwórz Ustawienia'\n"
                "2. Odblokuj kłódkę 🔒 (hasło administratora)\n"
                "3. Znajdź 'Malinche' i zaznacz ☑\n"
                "4. Wróć do tej aplikacji\n\n"
                "Możesz też pominąć ten krok i wybierać pliki ręcznie."
            ),
            ok="Otwórz Ustawienia",
            cancel="Pomiń",
            other="Anuluj",
        )

        if response == -1:  # Anuluj (other button)
            return "cancel"
        elif response == 1:  # Otwórz Ustawienia
            open_fda_preferences()
            rumps.alert(
                title="Gotowe?",
                message="Kliknij OK gdy nadasz uprawnienia w Ustawieniach Systemowych.",
                ok="OK",
            )

        return "next"

    def _show_source_config(self) -> str:
        """Konfiguracja źródeł nagrań.

        v2.0.0-beta.2: tryb ``auto`` został usunięty. Każdy dysk musi być
        świadomie zatwierdzony (przez dialog Tak/Nie/Raz przy podpięciu lub
        legacy ``specific`` z listą nazw).
        """
        response = rumps.alert(
            title="📁 Źródła nagrań",
            message=(
                "Skąd pobierać nagrania do transkrypcji?\n\n"
                "• Pytaj przy każdym nowym dysku (zalecane) — "
                "Malinche zapyta przy pierwszym podłączeniu nowego dysku, "
                "czy to recorder. Decyzja jest zapamiętywana.\n\n"
                "• Określone nazwy dysków (zaawansowane) — tylko volumes "
                "o podanych nazwach (np. LS-P1, ZOOM-H6)."
            ),
            ok="Pytaj przy nowym dysku",
            cancel="Określone nazwy dysków",
            other="Anuluj",
        )

        if response == -1:  # Anuluj (other button)
            return "cancel"
        elif response == 1:  # Pytaj — manual + whitelist UUID
            self.settings.watch_mode = "manual"
            self.settings.watched_volumes = []
            self.settings.needs_volume_onboarding = False
        else:  # Określone dyski (legacy specific)
            window = rumps.Window(
                title="Nazwy dysków",
                message="Wpisz nazwy dysków oddzielone przecinkami\n(np. LS-P1, ZOOM-H6):",
                default_text="LS-P1",
                ok="OK",
                cancel="Wstecz",
                dimensions=(300, 24),
            )
            result = window.run()

            if result.clicked == 0:  # Cancel/Wstecz
                return "back"

            volumes = [v.strip() for v in result.text.split(",") if v.strip()]
            self.settings.watch_mode = "specific"
            self.settings.watched_volumes = volumes
            self.settings.needs_volume_onboarding = False

        return "next"

    def _show_basic_config(self) -> str:
        """Unified step for output folder, language and model."""
        try:
            from AppKit import NSAlert, NSView, NSRect, NSTextField, NSPopUpButton

            from src.ui.folder_picker import (
                FolderPickerTarget,
                PICK_FOLDER_RESPONSE,
                apply_basic_settings,
                make_folder_picker_button,
                select_folder_with_warning,
            )

            language_codes = list(SUPPORTED_LANGUAGES.keys())
            model_codes = list(SUPPORTED_MODELS.keys())
            selected_folder = str(self.settings.output_dir)
            selected_language = (
                self.settings.language
                if self.settings.language in language_codes
                else language_codes[0]
            )
            selected_model = (
                self.settings.whisper_model
                if self.settings.whisper_model in model_codes
                else model_codes[0]
            )

            picker_target = FolderPickerTarget.alloc().init()

            while True:
                alert = NSAlert.alloc().init()
                alert.setMessageText_(TEXTS["wizard_basic_title"])
                alert.setInformativeText_(TEXTS["wizard_basic_message"])
                alert.addButtonWithTitle_("Dalej")
                alert.addButtonWithTitle_("Wstecz")
                alert.addButtonWithTitle_("Anuluj")

                accessory = NSView.alloc().initWithFrame_(NSRect((0, 0), (460, 170)))

                folder_label = NSTextField.alloc().initWithFrame_(NSRect((0, 140), (130, 20)))
                folder_label.setStringValue_("Folder docelowy:")
                folder_label.setBezeled_(False)
                folder_label.setDrawsBackground_(False)
                folder_label.setEditable_(False)
                folder_label.setSelectable_(False)
                accessory.addSubview_(folder_label)

                folder_value = NSTextField.alloc().initWithFrame_(NSRect((130, 140), (330, 20)))
                display_folder = (
                    selected_folder
                    if len(selected_folder) <= 60
                    else "..." + selected_folder[-57:]
                )
                folder_value.setStringValue_(display_folder)
                folder_value.setBezeled_(False)
                folder_value.setDrawsBackground_(False)
                folder_value.setEditable_(False)
                folder_value.setSelectable_(True)
                accessory.addSubview_(folder_value)

                pick_button = make_folder_picker_button(
                    NSRect((130, 108), (200, 28)),
                    target=picker_target,
                    title="Wybierz folder...",
                )
                if pick_button is not None:
                    accessory.addSubview_(pick_button)

                language_label = NSTextField.alloc().initWithFrame_(NSRect((0, 68), (130, 20)))
                language_label.setStringValue_("Język:")
                language_label.setBezeled_(False)
                language_label.setDrawsBackground_(False)
                language_label.setEditable_(False)
                language_label.setSelectable_(False)
                accessory.addSubview_(language_label)

                language_popup = NSPopUpButton.alloc().initWithFrame_(NSRect((130, 64), (330, 26)))
                for code, name in SUPPORTED_LANGUAGES.items():
                    language_popup.addItemWithTitle_(f"{name} ({code})")
                language_popup.selectItemAtIndex_(language_codes.index(selected_language))
                accessory.addSubview_(language_popup)

                model_label = NSTextField.alloc().initWithFrame_(NSRect((0, 28), (130, 20)))
                model_label.setStringValue_("Model:")
                model_label.setBezeled_(False)
                model_label.setDrawsBackground_(False)
                model_label.setEditable_(False)
                model_label.setSelectable_(False)
                accessory.addSubview_(model_label)

                model_popup = NSPopUpButton.alloc().initWithFrame_(NSRect((130, 24), (330, 26)))
                for code, name in SUPPORTED_MODELS.items():
                    model_popup.addItemWithTitle_(f"{code.upper()}: {name}")
                model_popup.selectItemAtIndex_(model_codes.index(selected_model))
                accessory.addSubview_(model_popup)

                alert.setAccessoryView_(accessory)
                response = alert.runModal()

                selected_language = language_codes[language_popup.indexOfSelectedItem()]
                selected_model = model_codes[model_popup.indexOfSelectedItem()]

                if response == PICK_FOLDER_RESPONSE:
                    picked = select_folder_with_warning(
                        choose_folder_dialog,
                        warn_non_icloud=lambda _p: rumps.alert(
                            title="Folder poza iCloud",
                            message=(
                                "Wybrany folder nie jest w iCloud. "
                                "Multi-device dedup będzie lokalny dla tego Maca."
                            ),
                            ok="OK",
                        ),
                        is_icloud_check=lambda p: is_icloud_synced(Path(p)),
                        title=TEXTS["folder_picker_title"],
                        message=TEXTS["folder_picker_message"],
                    )
                    if picked:
                        selected_folder = picked
                    continue

                if response == 1001:
                    return "back"
                if response == 1002:
                    return "cancel"

                apply_basic_settings(
                    self.settings,
                    selected_folder=selected_folder,
                    selected_language=selected_language,
                    selected_model=selected_model,
                    supported_languages=SUPPORTED_LANGUAGES,
                    supported_models=SUPPORTED_MODELS,
                )
                return "next"

        except ImportError:
            logger.warning("AppKit not available, fallback to legacy config steps")
            output_result = self._show_output_config()
            if output_result != "next":
                return output_result
            return self._show_language()

    def _show_output_config(self) -> str:
        """Konfiguracja folderu docelowego."""
        # Używamy rumps.alert z trzema przyciskami: ok, cancel, other
        # ok = Wybierz folder, cancel = Użyj domyślnego, other = Wstecz
        # Dodamy opcję "Anuluj" w drugim dialogu jeśli użytkownik wybierze folder
        response = rumps.alert(
            title=TEXTS["folder_picker_title"],
            message=(
                f"{TEXTS['folder_picker_message']}\n\n"
                f"Aktualnie: {self.settings.output_dir}"
            ),
            ok=TEXTS["folder_picker_select"],
            cancel=TEXTS["folder_picker_default"],
            other=TEXTS["folder_picker_back"],
        )
        
        if response == -1:  # other = Wstecz (w rumps -1 to other)
            return "back"
        elif response == 0:  # Użyj domyślnego
            return "next"
        # else response == 1: Wybierz folder
        
        # Wybierz folder przez NSOpenPanel
        folder_path = choose_folder_dialog()
        if folder_path:
            self.settings.output_dir = folder_path
            return "next"
        else:
            # User cancelled folder picker - zapytaj czy chce użyć domyślnego czy anulować
            response2 = rumps.alert(
                title=TEXTS["folder_picker_title"],
                message="Anulowano wybór folderu. Co chcesz zrobić?",
                ok="Użyj domyślnego",
                cancel="Anuluj konfigurację",
                other="Wstecz",
            )
            
            if response2 == -1:  # Wstecz
                return "back"
            elif response2 == 0:  # Anuluj konfigurację
                return "cancel"
            else:  # Użyj domyślnego
                return "next"

    def _show_language(self) -> str:
        """Konfiguracja języka transkrypcji z dropdown."""
        try:
            from AppKit import NSAlert, NSPopUpButton, NSRect
            
            alert = NSAlert.alloc().init()
            alert.setMessageText_("🗣️ Język transkrypcji")
            alert.setInformativeText_(
                "Wybierz domyślny język dla wszystkich nagrań.\n\n"
                "Możesz zmienić to później w Ustawieniach."
            )
            
            # Utwórz dropdown
            popup = NSPopUpButton.alloc().initWithFrame_(NSRect((0, 0), (250, 24)))
            for code, name in SUPPORTED_LANGUAGES.items():
                popup.addItemWithTitle_(f"{name} ({code})")
            
            # Ustaw aktualną wartość
            lang_codes = list(SUPPORTED_LANGUAGES.keys())
            if self.settings.language in lang_codes:
                current_idx = lang_codes.index(self.settings.language)
                popup.selectItemAtIndex_(current_idx)
            
            # Dodaj do alertu
            alert.setAccessoryView_(popup)
            alert.addButtonWithTitle_("OK")
            alert.addButtonWithTitle_("Wstecz")
            alert.addButtonWithTitle_("Anuluj")
            
            response = alert.runModal()
            # NSAlert button responses: 1000=OK, 1001=Wstecz, 1002=Anuluj
            if response == 1000:  # OK
                selected_idx = popup.indexOfSelectedItem()
                selected_code = lang_codes[selected_idx]
                self.settings.language = selected_code
                return "next"
            elif response == 1001:  # Wstecz
                return "back"
            else:  # Anuluj (1002)
                return "cancel"
        except ImportError:
            # Fallback do starej metody jeśli AppKit nie dostępny
            logger.warning("AppKit not available, using text input fallback")
            lang_options = "\n".join(
                [f"• {code}: {name}" for code, name in SUPPORTED_LANGUAGES.items()]
            )
            
            window = rumps.Window(
                title="🗣️ Język transkrypcji",
                message=(
                    f"W jakim języku są Twoje nagrania?\n\n"
                    f"Dostępne opcje:\n{lang_options}\n\n"
                    f"Wpisz kod języka:"
                ),
                default_text=self.settings.language,
                ok="OK",
                cancel="Wstecz",
                dimensions=(200, 24),
            )
            result = window.run()
            
            if result.clicked == 0:
                return "back"
            
            lang = result.text.strip().lower()
            if lang in SUPPORTED_LANGUAGES:
                self.settings.language = lang
            
            return "next"

    def _show_ai_config(self) -> str:
        """Konfiguracja AI podsumowań (opcjonalne)."""
        response = rumps.alert(
            title="🤖 AI Podsumowania (opcjonalne)",
            message=(
                "Malinche może generować inteligentne podsumowania "
                "i tytuły używając Claude AI.\n\n"
                "Wymaga to klucza API z anthropic.com\n"
                "(koszt ~$0.01-0.05 za transkrypcję)\n\n"
                "Możesz to skonfigurować później w Ustawieniach."
            ),
            ok="Pomiń",
            cancel="Skonfiguruj API",
            other="Anuluj",
        )

        if response == -1:  # Anuluj (other button)
            return "cancel"
        elif response == 1:  # Pomiń
            self.settings.enable_ai_summaries = False
            return "next"

        # Konfiguracja API key
        window = rumps.Window(
            title="Klucz API Claude",
            message="Wklej klucz API z anthropic.com:",
            default_text="",
            ok="Zapisz",
            cancel="Pomiń",
            dimensions=(350, 24),
        )
        result = window.run()

        if result.clicked == 1 and result.text.strip():
            self.settings.enable_ai_summaries = True
            self.settings.ai_api_key = result.text.strip()
        else:
            self.settings.enable_ai_summaries = False

        return "next"

    def _show_finish(self) -> str:
        """Ekran zakończenia."""
        rumps.alert(
            title="✅ Malinche jest gotowy!",
            message=(
                "Konfiguracja zakończona.\n\n"
                "Podłącz dyktafon lub kartę SD, a Malinche "
                "automatycznie przetworzy Twoje nagrania.\n\n"
                "Ikona 🎙️ pojawi się w pasku menu (góra ekranu).\n\n"
                "Miłego transkrybowania!"
            ),
            ok="🎉 Rozpocznij!",
        )
        return "next"


