"""Tests for tagger module."""

from unittest.mock import MagicMock, patch

from src import tagger as tagger_module
from src.config import Config
from src.config.features import FeatureFlags
from src.tagger import ClaudeTagger, get_tagger


def _patch_anthropic(monkeypatch, response_text: str) -> None:
    """Patch Anthropic client used by ClaudeTagger to return response_text."""

    class FakeMessages:
        def __init__(self, text: str) -> None:
            self._text = text

        def create(self, *_, **__):
            chunk = type("Chunk", (), {"text": self._text})()
            return type("Message", (), {"content": [chunk]})()

    class FakeClient:
        def __init__(self, *_args, **_kwargs) -> None:
            self.messages = FakeMessages(response_text)

    monkeypatch.setattr(tagger_module, "Anthropic", FakeClient)


def test_claude_tagger_parses_json(monkeypatch):
    """ClaudeTagger should parse unique tags from JSON response."""
    _patch_anthropic(monkeypatch, '["sauna", "zdrowie", "zamówienie telefoniczne"]')
    monkeypatch.setattr(tagger_module.config, "ENABLE_LLM_TAGGING", True)

    tagger = ClaudeTagger(api_key="test", model="claude-test")

    tags = tagger.generate_tags(
        transcript="To jest przykładowa transkrypcja.",
        summary_markdown="## Podsumowanie\n\nTreść",
        existing_tags=["sauna"],
    )

    assert isinstance(tags, list)
    assert "sauna" in tags
    assert "zamowienie-telefoniczne" in tags
    assert len(tags) <= Config().MAX_TAGS_PER_NOTE


def test_claude_tagger_invalid_json_returns_empty(monkeypatch):
    """Invalid JSON should result in empty tag list."""
    _patch_anthropic(monkeypatch, "Brak JSON")
    monkeypatch.setattr(tagger_module.config, "ENABLE_LLM_TAGGING", True)

    tagger = ClaudeTagger(api_key="test", model="claude-test")

    tags = tagger.generate_tags("Test", "Summary", [])

    assert tags == []


def test_get_tagger_no_license(monkeypatch):
    """Test that get_tagger returns None if license doesn't allow AI tags."""
    with patch('src.tagger.license_manager.get_features') as mock_features:
        mock_features.return_value = FeatureFlags(ai_smart_tags=False)
        assert get_tagger() is None


def test_get_tagger_byok_no_key_still_none(monkeypatch):
    """FREE tier + no API key → no tagger."""
    monkeypatch.setattr(tagger_module.config, "ENABLE_LLM_TAGGING", True)
    monkeypatch.setattr(tagger_module.config, "LLM_PROVIDER", "claude")
    monkeypatch.setattr(tagger_module.config, "LLM_API_KEY", None)
    with patch("src.tagger.license_manager.get_features") as mock_features:
        mock_features.return_value = FeatureFlags(ai_smart_tags=False)
        assert get_tagger() is None


@patch("src.tagger.ClaudeTagger", return_value=MagicMock())
def test_get_tagger_byok_with_claude_key(mock_ct, monkeypatch):
    """FREE tier but own Claude key → tagger is created (BYOK)."""
    monkeypatch.setattr(tagger_module.config, "ENABLE_LLM_TAGGING", True)
    monkeypatch.setattr(tagger_module.config, "LLM_PROVIDER", "claude")
    monkeypatch.setattr(tagger_module.config, "LLM_API_KEY", "sk-test")
    monkeypatch.setattr(tagger_module.config, "LLM_MODEL", "claude-3-haiku-20240307")
    with patch("src.tagger.license_manager.get_features") as mock_features:
        mock_features.return_value = FeatureFlags(ai_smart_tags=False)
        assert get_tagger() is not None
    mock_ct.assert_called_once_with(api_key="sk-test", model="claude-3-haiku-20240307")


def test_get_tagger_with_license(monkeypatch):
    """Test that get_tagger returns instance if license and config allow it."""
    monkeypatch.setattr(tagger_module.config, "ENABLE_LLM_TAGGING", True)
    monkeypatch.setattr(tagger_module.config, "LLM_PROVIDER", "claude")
    monkeypatch.setattr(tagger_module.config, "LLM_API_KEY", "test-key")
    
    with patch('src.tagger.license_manager.get_features') as mock_features:
        mock_features.return_value = FeatureFlags(ai_smart_tags=True)
        # Mock ClaudeTagger initialization to avoid actual Anthropic import issues if any
        with patch('src.tagger.ClaudeTagger', return_value=MagicMock()):
            assert get_tagger() is not None
