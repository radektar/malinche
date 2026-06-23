"""Unit tests for the DismissalStore (fcntl-safe, no API)."""

from src.config import config
from src.connections.dismissals import (
    DismissalStore,
    _parse_int_list,
    connection_signature,
)


def test_signature_is_order_independent():
    assert connection_signature(["b", "a"], "shared-thread") == connection_signature(
        ["a", "b"], "shared-thread"
    )
    assert connection_signature(["a", "b"], "shared-thread") != connection_signature(
        ["a", "b"], "emergent-idea"
    )


def test_dismiss_persists_across_reload(tmp_path):
    store = DismissalStore(tmp_path).load()
    sig = store.dismiss(["a", "b"], "shared-thread")
    assert store.is_dismissed(sig)
    assert DismissalStore(tmp_path).load().is_dismissed(sig)


def test_mute_note_persists(tmp_path):
    DismissalStore(tmp_path).load().mute_note("X")
    assert DismissalStore(tmp_path).load().note_muted("X")


def test_parse_int_list():
    assert _parse_int_list("[1, 3]") == [1, 3]
    assert _parse_int_list("[]") == []
    assert _parse_int_list("1,2,foo,3") == [1, 2, 3]
    assert _parse_int_list("") == []


def test_record_and_sync_frontmatter(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "TRANSCRIBE_DIR", tmp_path)
    digest = tmp_path / "digest.md"
    digest.write_text("---\ndismissed: [1]\n---\n\nbody", encoding="utf-8")
    meta = [
        {
            "sig": connection_signature(["a", "b"], "shared-thread"),
            "notes": ["a", "b"],
            "type": "shared-thread",
        },
        {
            "sig": connection_signature(["c", "d"], "emergent-idea"),
            "notes": ["c", "d"],
            "type": "emergent-idea",
        },
    ]
    DismissalStore(tmp_path).load().record_digest(digest, meta)

    store = DismissalStore(tmp_path).load()
    store.sync_frontmatter_dismissals()
    assert store.is_dismissed(connection_signature(["a", "b"], "shared-thread"))
    assert not store.is_dismissed(connection_signature(["c", "d"], "emergent-idea"))
    assert store.dismissed_descriptions() == ["[shared-thread] a, b"]
