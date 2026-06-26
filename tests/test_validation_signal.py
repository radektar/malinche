"""Pure tests for the validation signal recorder (no AppKit)."""

from __future__ import annotations

import json
from datetime import datetime

from src.connections import validation_signal as vsig


def _lines(path):
    return [json.loads(ln) for ln in path.read_text(encoding="utf-8").splitlines()]


def test_records_a_line(tmp_path):
    p = tmp_path / "signal.jsonl"
    ok = vsig.record_signal(
        vsig.KEPT,
        "contradiction-over-time",
        "Sprzeczność w czasie",
        notes=["a.md", "b.md"],
        path=p,
        now=datetime(2026, 6, 26, 10, 0, 0),
    )
    assert ok is True
    rows = _lines(p)
    assert len(rows) == 1
    r = rows[0]
    assert r["v"] == vsig.SCHEMA_VERSION
    assert r["action"] == "kept"
    assert r["conn_type"] == "contradiction-over-time"
    assert r["label"] == "Sprzeczność w czasie"
    assert r["ts"] == "2026-06-26T10:00:00"
    assert r["key"]  # derived from notes


def test_appends_rather_than_overwrites(tmp_path):
    p = tmp_path / "signal.jsonl"
    vsig.record_signal(vsig.KEPT, "shared-thread", notes=["a.md", "b.md"], path=p)
    vsig.record_signal(vsig.DISMISSED, "emergent-idea", notes=["c.md", "d.md"], path=p)
    rows = _lines(p)
    assert [r["action"] for r in rows] == ["kept", "dismissed"]
    assert [r["conn_type"] for r in rows] == ["shared-thread", "emergent-idea"]


def test_creates_missing_directory(tmp_path):
    p = tmp_path / "nested" / "deeper" / "signal.jsonl"
    assert not p.parent.exists()
    ok = vsig.record_signal(vsig.KEPT, "shared-thread", notes=["a.md"], path=p)
    assert ok is True
    assert p.exists()


def test_us4_same_notes_yield_same_key(tmp_path):
    """US-4: the same insight surfaced in two digests dedups by key."""
    p = tmp_path / "signal.jsonl"
    vsig.record_signal(vsig.KEPT, "shared-thread", notes=["a.md", "b.md"], path=p)
    # later digest, notes in a different order — same set
    vsig.record_signal(vsig.KEPT, "shared-thread", notes=["b.md", "a.md"], path=p)
    rows = _lines(p)
    assert rows[0]["key"] == rows[1]["key"]


def test_key_differs_for_different_notes():
    assert vsig.signal_key(["a.md", "b.md"]) != vsig.signal_key(["a.md", "c.md"])


def test_key_is_order_independent():
    assert vsig.signal_key(["a.md", "b.md"]) == vsig.signal_key(["b.md", "a.md"])


def test_key_handles_empty_notes():
    # empty / None must still produce a stable, comparable key, not raise
    assert vsig.signal_key([]) == vsig.signal_key(None)


def test_us5_unwritable_path_warns_and_returns_false(tmp_path, caplog):
    """US-5: a broken vault path never raises — it logs and returns False."""
    blocker = tmp_path / "blocker"
    blocker.write_text("i am a file, not a dir", encoding="utf-8")
    bad = blocker / "sub" / "signal.jsonl"  # parent is a file → mkdir fails
    ok = vsig.record_signal(vsig.KEPT, "shared-thread", notes=["a.md"], path=bad)
    assert ok is False
    assert not bad.exists()


def test_us8_odd_conn_type_is_coerced_not_raised(tmp_path):
    """US-8: a malformed value is stringified, never raised."""
    p = tmp_path / "signal.jsonl"
    ok = vsig.record_signal(vsig.KEPT, 12345, label=None, notes=None, path=p)
    assert ok is True
    r = _lines(p)[0]
    assert r["conn_type"] == "12345"
    assert r["label"] == ""


def test_explicit_key_overrides_notes(tmp_path):
    p = tmp_path / "signal.jsonl"
    vsig.record_signal(
        vsig.KEPT, "shared-thread", key="fixed123", notes=["x.md"], path=p
    )
    assert _lines(p)[0]["key"] == "fixed123"
