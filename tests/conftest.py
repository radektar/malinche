"""Session-wide test fixtures for Malinche.

This file serves two critical purposes:

1. **HOME isolation (module-level).** Before *any* test module imports
   ``src.logger`` or ``src.config``, this file redirects ``$HOME`` to a
   per-session temp directory. ``Path.home()`` returns that fake directory, so
   the lazily-initialised ``Config`` writes its ``STATE_FILE``,
   ``PROCESS_LOCK_FILE`` and ``LOG_FILE`` into a throw-away location instead of
   the developer's real ``~``.

2. **Regression guard (session fixture).** An autouse, session-scoped fixture
   snapshots the mtimes of the user-state artifacts that tests previously
   corrupted (``~/.olympus_transcriber_state.json``,
   ``~/.olympus_transcriber/transcriber.lock``,
   ``~/Library/Logs/olympus_transcriber.log``) and asserts at session teardown
   that they are unchanged. A regression that makes the test suite pollute the
   developer's HOME again will fail the build instead of silently corrupting
   the running Malinche instance.
"""

from __future__ import annotations

import os
import pwd
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Optional

import pytest

# --------------------------------------------------------------------------- #
# Module-level HOME redirection (runs BEFORE any test module is imported).
# --------------------------------------------------------------------------- #

# Resolve the REAL user home via getpwuid so we can always compare against it
# regardless of any subsequent $HOME changes.
_REAL_HOME = Path(pwd.getpwuid(os.getuid()).pw_dir)

# Fake HOME used for the whole session.
_FAKE_HOME = Path(tempfile.mkdtemp(prefix="malinche-test-home-"))
(_FAKE_HOME / "Library" / "Logs").mkdir(parents=True, exist_ok=True)
(_FAKE_HOME / "Library" / "Application Support" / "Malinche").mkdir(
    parents=True, exist_ok=True
)
(_FAKE_HOME / ".olympus_transcriber").mkdir(parents=True, exist_ok=True)

# Reassigning HOME here — at conftest module load time — guarantees that every
# subsequent ``Path.home()`` call (including the one inside
# ``Config.__post_init__``) resolves to the fake directory.
os.environ["HOME"] = str(_FAKE_HOME)

# Paths that production code writes to in ``_REAL_HOME``. If any of these get
# touched during the test session, the developer environment is being
# corrupted and we must fail loudly.
_USER_HOME_PROTECTED_PATHS = (
    _REAL_HOME / ".olympus_transcriber_state.json",
    _REAL_HOME / ".olympus_transcriber" / "transcriber.lock",
    _REAL_HOME / "Library" / "Logs" / "olympus_transcriber.log",
)


def _snapshot(paths) -> Dict[Path, Optional[float]]:
    """Capture current mtime (or None if missing) for every path."""
    snapshot: Dict[Path, Optional[float]] = {}
    for path in paths:
        try:
            snapshot[path] = path.stat().st_mtime
        except FileNotFoundError:
            snapshot[path] = None
    return snapshot


# --------------------------------------------------------------------------- #
# Fixtures.
# --------------------------------------------------------------------------- #


@pytest.fixture(scope="session")
def fake_home() -> Path:
    """Expose the session-wide fake HOME for tests that need it explicitly."""
    return _FAKE_HOME


@pytest.fixture(scope="session", autouse=True)
def _assert_real_home_untouched():
    """Fail the test run if any protected path under the real HOME changes.

    Rationale: in v2.0.0-alpha.2 we discovered that pytest runs were
    overwriting the live state file / log of the installed Malinche instance,
    which looked like the application had stopped detecting the recorder.
    This guard makes that failure mode impossible to merge unnoticed.
    """
    before = _snapshot(_USER_HOME_PROTECTED_PATHS)
    yield
    after = _snapshot(_USER_HOME_PROTECTED_PATHS)

    mutated = [
        path
        for path in _USER_HOME_PROTECTED_PATHS
        if before[path] != after[path]
    ]

    if mutated:
        details = "\n".join(
            f"  - {path}: mtime {before[path]!r} -> {after[path]!r}"
            for path in mutated
        )
        pytest.fail(
            "Test run mutated real user HOME artifacts. "
            "Tests must never write to ~/.olympus_* or the production log.\n"
            f"{details}",
            pytrace=False,
        )


def pytest_sessionfinish(session, exitstatus):
    """Clean up the session-wide fake HOME tempdir."""
    shutil.rmtree(_FAKE_HOME, ignore_errors=True)
