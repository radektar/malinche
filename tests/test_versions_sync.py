"""Version consistency checks for release metadata."""

import ast
from pathlib import Path

from src.ui.constants import APP_VERSION as UI_APP_VERSION


def _read_setup_app_version() -> str:
    setup_path = Path(__file__).resolve().parents[1] / "setup_app.py"
    module = ast.parse(setup_path.read_text(encoding="utf-8"))
    for node in module.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "APP_VERSION":
                    value = node.value
                    if isinstance(value, ast.Constant) and isinstance(value.value, str):
                        return value.value
    raise AssertionError("APP_VERSION not found in setup_app.py")


def test_app_version_is_synced_between_setup_and_ui() -> None:
    """UI and bundled metadata must expose the same app version."""
    assert _read_setup_app_version() == UI_APP_VERSION
