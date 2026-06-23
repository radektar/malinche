"""Unit tests for the digest scheduler (no API)."""

from datetime import datetime, timedelta
from pathlib import Path

from src.config import config
from src.connections.scheduler import (
    DigestScheduler,
    enqueue_connection_analysis,
    get_scheduler,
    reset_scheduler_for_tests,
)


def test_is_due_truth_table(tmp_path):
    s = DigestScheduler(tmp_path / "cs.json")
    now = datetime(2026, 6, 23, 12, 0, 0)

    assert s.is_due(now) is False  # no new material
    s.register_new_notes(1)
    assert s.is_due(now) is True  # first run with material
    s.mark_ran(now)
    assert s.is_due(now) is False  # just ran, counter reset

    s.register_new_notes(1)
    s.last_digest_at = (now - timedelta(days=8)).isoformat(timespec="seconds")
    assert s.is_due(now) is True  # weekly cadence elapsed

    s.mark_ran(now)
    s.register_new_notes(6)
    s.last_digest_at = (now - timedelta(days=3)).isoformat(timespec="seconds")
    assert s.is_due(now) is True  # pattern-trigger (>=6 new, >=2 days)

    s.mark_ran(now)
    s.register_new_notes(2)
    s.last_digest_at = (now - timedelta(days=1)).isoformat(timespec="seconds")
    assert s.is_due(now) is False  # below pattern + below weekly + min-gap


def test_mark_ran_persists_and_resets(tmp_path):
    state_file = tmp_path / "cs.json"
    sched = DigestScheduler(state_file)
    sched.register_new_notes(3)
    now = datetime(2026, 6, 23, 12, 0, 0)
    sched.mark_ran(now, Path("/x/digest.md"))
    assert sched.new_notes == 0

    reloaded = DigestScheduler(state_file)
    assert reloaded.last_digest_at == now.isoformat(timespec="seconds")
    assert reloaded.last_digest_path == "/x/digest.md"


def test_enqueue_increments_singleton(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "CONNECTIONS_STATE_FILE", tmp_path / "cs.json")
    reset_scheduler_for_tests()
    try:
        enqueue_connection_analysis(None)
        enqueue_connection_analysis(None)
        assert get_scheduler().new_notes == 2
    finally:
        reset_scheduler_for_tests()
