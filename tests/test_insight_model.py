"""Tests for the pure Insights data model (src/ui/insight_model.py)."""

from __future__ import annotations

from src.ui import insight_model as im


def test_make_connection_tuples_and_defaults():
    c = im.make_connection(
        im.CONTRADICTION,
        "A long rationale sentence that explains the connection clearly.",
        ["Note A", "Note B"],
        ["Question one?", "Question two?"],
    )
    assert isinstance(c.notes, tuple)
    assert isinstance(c.directions, tuple)
    assert c.notes == ("Note A", "Note B")
    # label / colour / layout resolve from the type metadata
    assert c.resolved_label() == "Sprzeczność w czasie"
    assert c.resolved_tcolor() == "#E0633A"
    assert c.layout() == "contradiction"


def test_snippet_falls_back_to_clipped_rationale():
    long = "x" * 200
    c = im.make_connection(im.SHARED, long, ["A", "B"])
    assert c.snippet.endswith("…")
    assert len(c.snippet) <= 86


def test_explicit_label_and_colour_override_type_defaults():
    c = im.make_connection(
        im.EMERGENT, "r", ["A", "B"], label="Custom", tcolor="#123456"
    )
    assert c.resolved_label() == "Custom"
    assert c.resolved_tcolor() == "#123456"
    # layout still derives from the type
    assert c.layout() == "triad"


def test_layout_for_each_type():
    assert im.layout_for_type(im.CONTRADICTION) == "contradiction"
    assert im.layout_for_type(im.SHARED) == "thread"
    assert im.layout_for_type(im.EMERGENT) == "triad"
    assert im.layout_for_type("nonsense") == "thread"


def test_empty_deck():
    deck = im.InsightDeck()
    assert len(deck) == 0
    assert deck.is_empty
    assert deck.active() is None
    assert deck.unseen_count == 0
    # navigation/triage on empty is a no-op, never raises
    deck.next()
    deck.prev()
    deck.keep()
    deck.dismiss()
    assert deck.active() is None


def _deck3():
    return im.InsightDeck(
        [
            im.make_connection(im.CONTRADICTION, "r1", ["A", "B"]),
            im.make_connection(im.SHARED, "r2", ["C", "D"]),
            im.make_connection(im.EMERGENT, "r3", ["E", "F"]),
        ]
    )


def test_navigation_clamps():
    deck = _deck3()
    assert deck.active_index == 0
    deck.prev()
    assert deck.active_index == 0  # clamped low
    deck.next()
    deck.next()
    assert deck.active_index == 2
    deck.next()
    assert deck.active_index == 2  # clamped high
    deck.select(1)
    assert deck.active().rationale == "r2"
    deck.select(99)  # out of range — ignored
    assert deck.active_index == 1


def test_keep_marks_and_advances():
    deck = _deck3()
    assert deck.unseen_count == 3
    deck.keep()  # keep #0
    assert deck.is_kept(0)
    assert deck.unseen_count == 2
    # advanced to the next un-kept (#1)
    assert deck.active_index == 1


def test_keep_wraps_to_earlier_unkept():
    deck = _deck3()
    deck.select(2)
    deck.keep()  # keep last; no later un-kept → wrap to #0
    assert deck.active_index == 0
    assert deck.unseen_count == 2


def test_dismiss_retags_and_advances_within_new_view():
    deck = _deck3()
    deck.select(1)
    deck.dismiss()  # r2 leaves the New view → advance to the next New (r3)
    assert len(deck) == 3  # nothing deleted — Odrzuć is reversible
    assert deck.counts()["dismissed"] == 1
    assert deck.active().rationale == "r3"
    # r2 is now recoverable from the Dismissed view
    deck.set_view(im.DISMISSED)
    assert [c.rationale for _, c in deck.visible()] == ["r2"]


def test_dismiss_at_end_wraps_to_first_new():
    deck = _deck3()
    deck.select(2)
    deck.dismiss()  # no later New → wrap to the first New (r1)
    assert len(deck) == 3
    assert deck.active().rationale == "r1"
    assert deck.counts()["dismissed"] == 1


def test_dismiss_all_leaves_new_view_empty_but_deck_intact():
    deck = _deck3()
    deck.dismiss()
    deck.dismiss()
    deck.dismiss()
    assert not deck.is_empty  # the connections still exist…
    assert deck.active() is None  # …but the New view is now empty
    assert deck.counts() == {"new": 0, "kept": 0, "dismissed": 3}
    deck.set_view(im.DISMISSED)
    assert deck.visible_count == 3


def test_recover_a_dismissed_connection_via_keep():
    deck = _deck3()
    deck.select(0)
    deck.dismiss()
    deck.set_view(im.DISMISSED)
    deck.select(0)  # r1, now in the Dismissed view
    deck.keep()  # recover → moves to Kept, leaves the Dismissed view
    assert deck.counts()["dismissed"] == 0
    assert deck.counts()["kept"] == 1


def test_triage_seed_from_signal_applies_prior_state():
    a = im.make_connection(im.CONTRADICTION, "r1", ["A", "B"], sig="sig-a")
    b = im.make_connection(im.SHARED, "r2", ["C", "D"], sig="sig-b")
    c = im.make_connection(im.EMERGENT, "r3", ["E", "F"], sig="sig-c")
    triage = {"sig-a": "kept", "sig-b": "dismissed"}  # c has no prior signal
    deck = im.InsightDeck([a, b, c], triage=triage)
    assert deck.counts() == {"new": 1, "kept": 1, "dismissed": 1}
    deck.set_view(im.KEPT)
    assert [conn.rationale for _, conn in deck.visible()] == ["r1"]
    deck.set_view(im.NEW)
    assert [conn.rationale for _, conn in deck.visible()] == ["r3"]


def test_empty_sig_is_never_seeded_from_triage():
    # A connection with no sig can't be joined to a logged action — stays New.
    a = im.make_connection(im.CONTRADICTION, "r1", ["A", "B"])  # sig defaults ""
    deck = im.InsightDeck([a], triage={"": "dismissed"})
    assert deck.counts()["new"] == 1


def test_sample_deck_is_the_three_real_connections():
    deck = im.sample_deck()
    assert len(deck) == 3
    types = [c.conn_type for c in deck.items]
    assert types == [im.CONTRADICTION, im.SHARED, im.EMERGENT]
    # every connection carries full content for the reader
    for c in deck.items:
        assert c.rationale
        assert len(c.notes) >= 2
        assert len(c.directions) >= 2
