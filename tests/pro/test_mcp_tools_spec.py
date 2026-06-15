"""Executable spec for the PRO MCP server tools (v2.1.0).

These tests are SKIPPED until the private ``malinche_pro`` package exists.
They are committed now so the acceptance criteria for each MCP tool are
captured as code, not just prose. When ``malinche_pro`` lands, remove the
module-level skip and fill in the bodies against a real (or mocked) Supabase.

MCP MVP exposes 5 tools:
  search_transcripts(query, limit=10, since=None) -> list
  get_transcript(id) -> str
  list_recent(n=10) -> list[meta]
  list_by_date_range(start, end) -> list[meta]
  find_quotes(speaker_or_topic, context_chars=200) -> list

See Docs/TESTING-PRO-MCP.md for the full plan, fixtures and acceptance gates.
"""

import pytest

pytest.importorskip(
    "malinche_pro",
    reason="malinche_pro is a private package shipped with PRO (v2.1.0)",
)

pytestmark = pytest.mark.pro


class TestSearchTranscripts:
    def test_returns_semantic_matches_ranked_by_similarity(self):
        # GIVEN three transcripts, one mentioning "budget" semantically
        # WHEN search_transcripts("what did we decide about money")
        # THEN the budget transcript ranks first, limited to `limit`
        raise NotImplementedError

    def test_since_filter_excludes_older_transcripts(self):
        # WHEN search_transcripts(query, since=<date>)
        # THEN only transcripts created on/after `since` are returned
        raise NotImplementedError

    def test_only_returns_current_users_rows(self):
        # Supabase RLS: user A must never see user B's transcripts
        raise NotImplementedError


class TestGetTranscript:
    def test_returns_full_markdown_by_id(self):
        raise NotImplementedError

    def test_unknown_id_raises_not_found(self):
        raise NotImplementedError


class TestListRecent:
    def test_returns_n_most_recent_metadata_desc(self):
        raise NotImplementedError


class TestListByDateRange:
    def test_inclusive_bounds(self):
        raise NotImplementedError


class TestFindQuotes:
    def test_returns_snippets_with_surrounding_context(self):
        # context_chars worth of text on each side of the match
        raise NotImplementedError
