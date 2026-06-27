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


# --- action_taken (v2, ADR-004) ----------------------------------------- #


def test_record_action_writes_v2_event(tmp_path):
    p = tmp_path / "signal.jsonl"
    ok = vsig.record_action(
        vsig.TARGET_LLM,
        sig="abc123",
        conn_type="contradiction-over-time",
        directions=[0, 2],
        tool="claude",
        path=p,
        now=datetime(2026, 6, 27, 10, 0, 0),
    )
    assert ok is True
    r = _lines(p)[0]
    assert r["v"] == 2
    assert r["action"] == "action_taken"
    assert r["kind"] == "develop"  # derived from target=llm
    assert r["target"] == "llm"
    assert r["sig"] == "abc123"
    assert r["directions"] == [0, 2]
    assert r["n_dir"] == 2
    assert r["tool"] == "claude"


def test_record_action_kind_derives_from_target(tmp_path):
    p = tmp_path / "signal.jsonl"
    vsig.record_action(vsig.TARGET_TASK, sig="s", path=p)
    vsig.record_action(vsig.TARGET_CALENDAR, sig="s", path=p)
    vsig.record_action(vsig.TARGET_NONE, sig="s", path=p)  # dismiss
    assert [r["kind"] for r in _lines(p)] == ["do", "decide", "none"]


def test_record_action_recomputes_canonical_sig_when_absent(tmp_path):
    # No sig carried → fall back to the canonical type-inclusive signature, NOT
    # the legacy notes-only key, so the event still joins back to the connection.
    from src.connections.signature import connection_signature

    p = tmp_path / "signal.jsonl"
    vsig.record_action(
        vsig.TARGET_CLIPBOARD,
        conn_type="emergent-idea",
        notes=["b", "a"],
        path=p,
    )
    assert _lines(p)[0]["sig"] == connection_signature(["a", "b"], "emergent-idea")


def test_record_action_dismiss_is_none_none(tmp_path):
    # "Odrzuć" is a signal, not a suppressor: kind:none, target:none, no notes.
    p = tmp_path / "signal.jsonl"
    vsig.record_action(vsig.TARGET_NONE, sig="x", path=p)
    r = _lines(p)[0]
    assert r["kind"] == "none" and r["target"] == "none" and r["n_dir"] == 0


def test_record_action_never_raises_on_bad_path(tmp_path):
    blocker = tmp_path / "blocker"
    blocker.write_text("file", encoding="utf-8")
    bad = blocker / "sub" / "signal.jsonl"
    assert vsig.record_action(vsig.TARGET_LLM, sig="x", path=bad) is False
