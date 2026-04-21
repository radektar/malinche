"""First-run setup wizard."""

import rumps
import threading
from enum import Enum, auto
from typing import Optional

from src.config import UserSettings, SUPPORTED_LANGUAGES, SUPPORTED_MODELS
from src.setup.downloader import DependencyDownloader
from src.setup.permissions import check_full_disk_access, open_fda_preferences
from src.setup.errors import NetworkError, DiskSpaceError, DownloadError
from src.logger import logger
from src.ui.dialogs import choose_folder_dialog
from src.ui.constants import TEXTS


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
        WizardStep.DOWNLOAD,
        WizardStep.PERMISSIONS,
        WizardStep.SOURCE_CONFIG,
        WizardStep.BASIC_CONFIG,
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
        self._download_status = ""
        self._download_in_progress = False
        self._download_error: Optional[Exception] = None
        self._download_complete = False
        self._wizard_completed = False

    @staticmethod
    def needs_setup() -> bool:
        """Sprawdź czy wizard jest potrzebny."""
        settings = UserSettings.load()
        return not settings.setup_completed

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
        if self.current_step == WizardStep.FINISH:
            # Finalizacja
            self._show_finish()
            self.settings.setup_completed = True
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
        
        # Wyślij notyfikację co 10% postępu
        percent = int(progress * 100)
        if percent % 10 == 0 or percent == 100:
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
        """Pobieranie zależności - skip jeśli już pobrane."""
        if self.downloader.check_all():
            logger.info("Zależności już zainstalowane - pomijam krok")
            return "next"

        response = rumps.alert(
            title="📥 Pobieranie silnika transkrypcji",
            message=(
                "Malinche wymaga pobrania silnika transkrypcji (~500MB).\n\n"
                "Wymagane komponenty:\n"
                "• whisper.cpp (~10MB)\n"
                "• ffmpeg (~15MB)\n"
                "• Model transkrypcji (~466MB)\n\n"
                "Wymagane jest połączenie z internetem.\n\n"
                "Pobieranie może potrwać kilka minut."
            ),
            ok="Pobierz teraz",
            cancel="Anuluj",
        )

        if response != 1:
            return "cancel"

        # Resetuj flagi
        self._download_in_progress = True
        self._download_complete = False
        self._download_error = None
        self._download_status = "Rozpoczynanie..."

        # Uruchom pobieranie w osobnym wątku
        download_thread = threading.Thread(
            target=self._download_in_background,
            daemon=True,
            name="WizardDownload"
        )
        download_thread.start()

        # Pokaż okno z informacją o pobieraniu (blokuje UI aż do zakończenia)
        # Używamy pętli z alertami co kilka sekund aby informować o postępie
        import time
        while self._download_in_progress:
            # Pokaż aktualny status
            response = rumps.alert(
                title="⏳ Pobieranie w toku...",
                message=(
                    f"Status: {self._download_status}\n\n"
                    "Proszę czekać, pobieranie może potrwać kilka minut.\n"
                    "Nie zamykaj tego okna."
                ),
                ok="Sprawdź status",
                cancel=None,  # Brak przycisku anuluj - nie można przerwać
            )
            # Krótka pauza przed kolejnym sprawdzeniem
            time.sleep(2)

        # Pobieranie zakończone - sprawdź wynik
        if self._download_error:
            error_msg = str(self._download_error)
            if isinstance(self._download_error, NetworkError):
                rumps.alert(
                    title="❌ Brak połączenia",
                    message=f"Brak połączenia z internetem:\n\n{error_msg}",
                    ok="OK",
                )
            elif isinstance(self._download_error, DiskSpaceError):
                rumps.alert(
                    title="❌ Brak miejsca",
                    message=f"Brak miejsca na dysku:\n\n{error_msg}",
                    ok="OK",
                )
            elif isinstance(self._download_error, DownloadError):
                rumps.alert(
                    title="❌ Błąd pobierania",
                    message=f"Nie udało się pobrać zależności:\n\n{error_msg}",
                    ok="OK",
                )
            else:
                rumps.alert(
                    title="❌ Błąd",
                    message=f"Nieoczekiwany błąd:\n\n{error_msg}",
                    ok="OK",
                )
            return "cancel"

        if self._download_complete:
            rumps.alert(
                title="✅ Pobrano",
                message="Silnik transkrypcji został pobrany pomyślnie.",
                ok="Dalej",
            )
            return "next"

        # Nieoczekiwany stan
        return "cancel"

    def _download_in_background(self):
        """Wykonaj pobieranie w tle (w osobnym wątku)."""
        try:
            logger.info("Rozpoczęto pobieranie zależności w tle")
            self.downloader.download_all()
            self._download_complete = True
            logger.info("✓ Pobieranie zakończone pomyślnie")
        except Exception as e:
            logger.error(f"Błąd podczas pobierania: {e}", exc_info=True)
            self._download_error = e
        finally:
            self._download_in_progress = False

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
        """Konfiguracja źródeł nagrań."""
        response = rumps.alert(
            title="📁 Źródła nagrań",
            message=(
                "Skąd pobierać nagrania do transkrypcji?\n\n"
                "• Automatycznie - wykrywa każdy nowy dysk/kartę SD\n"
                "  (zalecane dla większości użytkowników)\n\n"
                "• Określone dyski - tylko wybrane nazwy dysków\n"
                "  (np. LS-P1, ZOOM-H6)"
            ),
            ok="Automatycznie",
            cancel="Określone dyski",
            other="Anuluj",
        )

        if response == -1:  # Anuluj (other button)
            return "cancel"
        elif response == 1:  # Automatycznie
            self.settings.watch_mode = "auto"
            self.settings.watched_volumes = []
        else:  # Określone dyski
            # Pytaj o nazwy dysków
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

        return "next"

    def _show_basic_config(self) -> str:
        """Unified step for output folder, language and model."""
        try:
            from AppKit import NSAlert, NSView, NSRect, NSTextField, NSPopUpButton

            language_codes = list(SUPPORTED_LANGUAGES.keys())
            model_codes = list(SUPPORTED_MODELS.keys())
            selected_folder = self.settings.output_dir
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

            while True:
                alert = NSAlert.alloc().init()
                alert.setMessageText_("⚙️ Podstawowa konfiguracja")
                alert.setInformativeText_(
                    "Skonfiguruj folder docelowy, język i model transkrypcji."
                )
                alert.addButtonWithTitle_("Dalej")
                alert.addButtonWithTitle_("Wstecz")
                alert.addButtonWithTitle_("Anuluj")
                alert.addButtonWithTitle_("Zmień folder...")

                accessory = NSView.alloc().initWithFrame_(NSRect((0, 0), (420, 138)))

                folder_label = NSTextField.alloc().initWithFrame_(NSRect((0, 112), (120, 20)))
                folder_label.setStringValue_("Folder docelowy:")
                folder_label.setBezeled_(False)
                folder_label.setDrawsBackground_(False)
                folder_label.setEditable_(False)
                folder_label.setSelectable_(False)
                accessory.addSubview_(folder_label)

                folder_value = NSTextField.alloc().initWithFrame_(NSRect((120, 112), (300, 20)))
                display_folder = selected_folder if len(selected_folder) <= 60 else "..." + selected_folder[-57:]
                folder_value.setStringValue_(display_folder)
                folder_value.setBezeled_(False)
                folder_value.setDrawsBackground_(False)
                folder_value.setEditable_(False)
                folder_value.setSelectable_(False)
                accessory.addSubview_(folder_value)

                language_label = NSTextField.alloc().initWithFrame_(NSRect((0, 72), (120, 20)))
                language_label.setStringValue_("Język:")
                language_label.setBezeled_(False)
                language_label.setDrawsBackground_(False)
                language_label.setEditable_(False)
                language_label.setSelectable_(False)
                accessory.addSubview_(language_label)

                language_popup = NSPopUpButton.alloc().initWithFrame_(NSRect((120, 68), (300, 26)))
                for code, name in SUPPORTED_LANGUAGES.items():
                    language_popup.addItemWithTitle_(f"{name} ({code})")
                language_popup.selectItemAtIndex_(language_codes.index(selected_language))
                accessory.addSubview_(language_popup)

                model_label = NSTextField.alloc().initWithFrame_(NSRect((0, 32), (120, 20)))
                model_label.setStringValue_("Model:")
                model_label.setBezeled_(False)
                model_label.setDrawsBackground_(False)
                model_label.setEditable_(False)
                model_label.setSelectable_(False)
                accessory.addSubview_(model_label)

                model_popup = NSPopUpButton.alloc().initWithFrame_(NSRect((120, 28), (300, 26)))
                for code, name in SUPPORTED_MODELS.items():
                    model_popup.addItemWithTitle_(f"{code.upper()}: {name}")
                model_popup.selectItemAtIndex_(model_codes.index(selected_model))
                accessory.addSubview_(model_popup)

                alert.setAccessoryView_(accessory)
                response = alert.runModal()

                selected_language = language_codes[language_popup.indexOfSelectedItem()]
                selected_model = model_codes[model_popup.indexOfSelectedItem()]

                if response == 1003:
                    folder_path = choose_folder_dialog(
                        title=TEXTS["folder_picker_title"],
                        message=TEXTS["folder_picker_message"],
                    )
                    if folder_path:
                        selected_folder = folder_path
                    continue

                if response == 1001:
                    return "back"
                if response == 1002:
                    return "cancel"

                self.settings.output_dir = selected_folder
                self.settings.language = selected_language
                self.settings.whisper_model = selected_model
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


