"""L3 quality test for connection synthesis (real Claude, gold cases).

Mirrors the skip discipline of ``test_summary_quality.py``: every test skips
cleanly when ``ANTHROPIC_API_KEY`` is absent, and turns billing/quota errors
into skips rather than failures. Marked slow/e2e so the unit suite stays fast.

For the full Opus-vs-Sonnet comparison use ``scripts/eval_synthesis.py``
(``make eval-synthesis``); this guards the two highest-signal gold cases as a
regression net.
"""

from __future__ import annotations

import os
from typing import Optional

import pytest

from src.connections.synthesis import APIBillingError, ConnectionSynthesizer
from tests.fixtures.synthesis_cases import GOLD_CASES

pytestmark = [pytest.mark.e2e, pytest.mark.slow]

_CASES = {c.name: c for c in GOLD_CASES}


def _get_api_key() -> Optional[str]:
    return os.environ.get("ANTHROPIC_API_KEY")


requires_claude = pytest.mark.skipif(
    _get_api_key() is None,
    reason="requires ANTHROPIC_API_KEY for real Claude calls",
)

# The model under test; override with SYNTH_EVAL_MODEL to spot-check a tier.
_MODEL = os.environ.get("SYNTH_EVAL_MODEL", "claude-haiku-4-5-20251001")


def _synthesize_or_skip(case_name: str, language: str):
    case = _CASES[case_name]
    synth = ConnectionSynthesizer(api_key=_get_api_key(), model=_MODEL)
    try:
        out = synth.synthesize(case.candidates(), language=language)
    except APIBillingError as exc:
        pytest.skip(f"Anthropic API unavailable (billing): {exc}")
    if out is None:
        pytest.skip("Anthropic API returned no result")
    return case, out


@requires_claude
def test_contradiction_over_time_is_detected():
    case, out = _synthesize_or_skip("contradiction-over-time", "en")
    ok, detail = case.check(out)
    assert ok, f"{detail}; got {[(c.type, c.notes) for c in out.connections]}"


@requires_claude
def test_unrelated_notes_stay_empty():
    case, out = _synthesize_or_skip("empty-restraint", "en")
    ok, detail = case.check(out)
    assert ok, f"{detail}; got {len(out.connections)} connections"
