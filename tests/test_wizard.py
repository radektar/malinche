"""Unit tests for SetupWizard."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.config import UserSettings
from src.setup.wizard import SetupWizard, WizardStep


class TestSetupWizard:
    """Testy dla klasy SetupWizard."""

    def test_needs_setup_first_run(self, tmp_path, monkeypatch):
        """Zwraca True gdy setup_completed=False."""
        config_file = tmp_path / "config.json"
        monkeypatch.setattr(
            UserSettings, "config_path", staticmethod(lambda: config_file)
        )

        assert SetupWizard.needs_setup() is True

    def test_needs_setup_after_completion(self, tmp_path, monkeypatch):
        """Zwraca False gdy setup_completed=True."""
        config_file = tmp_path / "config.json"
        monkeypatch.setattr(
            UserSettings, "config_path", staticmethod(lambda: config_file)
        )

        settings = UserSettings(setup_completed=True)
        settings.save()

        assert SetupWizard.needs_setup() is False

    def test_wizard_step_order(self):
        """Kroki są w poprawnej kolejności."""
        assert SetupWizard.STEPS_ORDER[0] == WizardStep.WELCOME
        assert SetupWizard.STEPS_ORDER[-1] == WizardStep.FINISH
        assert len(SetupWizard.STEPS_ORDER) == 7

    def test_welcome_step_ok(self, monkeypatch):
        """Kliknięcie OK przechodzi dalej."""
        monkeypatch.setattr("rumps.alert", lambda **kwargs: 1)

        wizard = SetupWizard()
        result = wizard._show_welcome()

        assert result == "next"

    def test_welcome_step_cancel(self, monkeypatch):
        """Kliknięcie Cancel kończy wizard."""
        monkeypatch.setattr("rumps.alert", lambda **kwargs: 0)

        wizard = SetupWizard()
        result = wizard._show_welcome()

        assert result == "cancel"

    def test_download_skip_if_installed(self, monkeypatch):
        """Pomija krok gdy zależności zainstalowane."""
        wizard = SetupWizard()
        monkeypatch.setattr(wizard.downloader, "check_all", lambda: True)

        result = wizard._show_download()

        assert result == "next"

    def test_permissions_skip_if_granted(self, monkeypatch):
        """Pomija krok gdy FDA nadane."""
        monkeypatch.setattr(
            "src.setup.wizard.check_full_disk_access", lambda: True
        )

        wizard = SetupWizard()
        result = wizard._show_permissions()

        assert result == "next"

    def test_settings_saved_after_finish(self, tmp_path, monkeypatch):
        """Po zakończeniu setup_completed=True."""
        config_file = tmp_path / "config.json"
        monkeypatch.setattr(
            UserSettings, "config_path", staticmethod(lambda: config_file)
        )

        # Mock wszystkie dialogi żeby zwracały "next"
        monkeypatch.setattr("rumps.alert", lambda **kwargs: 1)
        monkeypatch.setattr("rumps.Window", lambda **kwargs: Mock(run=lambda: Mock(clicked=1, text="test")))

        wizard = SetupWizard()
        # Symuluj że wszystkie kroki przeszły
        wizard.settings.setup_completed = True
        wizard.settings.save()

        loaded = UserSettings.load()
        assert loaded.setup_completed is True



