"""Unit tests for digest rendering/writing (no API)."""

from src.config import config
from src.connections.digest_writer import render_digest, write_digest_note
from src.connections.synthesis import Connection


def _conn(conn_type="shared-thread", notes=("a", "b")):
    return Connection(
        type=conn_type,
        notes=list(notes),
        rationale="why these connect",
        directions=["A: a path?", "B: another?"],
    )


def test_render_has_frontmatter_links_and_dismiss_tokens():
    body = render_digest([_conn()], 5)
    assert "type: malinche-digest" in body
    assert "dismissed: []" in body
    assert "[[a]]" in body and "[[b]]" in body
    assert "`dismiss: 1`" in body
    assert "Shared thread" in body


def test_render_type_labels():
    body = render_digest([_conn("contradiction-over-time"), _conn("emergent-idea")], 5)
    assert "Contradiction over time" in body
    assert "Emergent idea" in body


def test_write_digest_returns_meta_and_is_collision_safe(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "TRANSCRIBE_DIR", tmp_path)
    p1, meta1 = write_digest_note([_conn()], 5)
    p2, meta2 = write_digest_note([_conn()], 5)
    assert p1.exists() and p2.exists() and p1 != p2  # collision-safe
    assert meta1[0]["type"] == "shared-thread"
    assert set(meta1[0].keys()) == {"sig", "notes", "type"}
    assert (tmp_path / config.DIGEST_DIR_NAME).is_dir()
