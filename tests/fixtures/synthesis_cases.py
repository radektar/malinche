"""Gold cases for the synthesis eval — discriminating, non-obvious tests.

Each case is a small, hand-planted corpus plus a deterministic check on the
model's structured output. They are designed to *separate* a strong synthesis
model from a weak one (precision, restraint, temporal reasoning, cross-language,
emergent-thread detection, non-prescriptiveness) — not to reward shallow
keyword matching. Used by ``scripts/eval_synthesis.py`` (model comparison) and
the L3 quality test.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Set, Tuple

from src.connections.candidate_assembly import CandidateSet, NoteRef
from src.connections.synthesis import ConnectionList

# A note tuple is (basename, date, tags, summary).
NoteTuple = Tuple[str, str, List[str], str]


def _note(basename: str, date: str, tags: List[str], summary: str) -> NoteRef:
    return NoteRef(
        md_path=Path(f"/eval/{basename}.md"),
        basename=basename,
        title=basename,
        date=date,
        tags=tags,
        norm_tags={t.lower() for t in tags},
        summary_md=summary,
        fingerprint="sha256:" + basename,
    )


def build_candidates(notes: List[NoteTuple], window: List[str]) -> CandidateSet:
    return CandidateSet([_note(*n) for n in notes], set(window))


def _links(result: ConnectionList, a: str, b: str) -> bool:
    return any(a in c.notes and b in c.notes for c in result.connections)


_SOFTENERS = (
    "?",
    "could",
    "would",
    "might",
    "perhaps",
    "what if",
    "maybe",
    "czy",
    "może",
    "mógłbyś",
    "mogłabyś",
    "co jeśli",
    "a gdyby",
    "warto",
)


def _all_directions_non_prescriptive(result: ConnectionList) -> Tuple[bool, str]:
    if not result.connections:
        return False, "no connection produced to judge phrasing"
    for conn in result.connections:
        for direction in conn.directions:
            low = direction.lower()
            if not any(tok in low for tok in _SOFTENERS):
                return False, f"prescriptive direction: {direction!r}"
    return True, "directions phrased as invitations/questions"


@dataclass
class GoldCase:
    name: str
    notes: List[NoteTuple]
    window: List[str]
    check: Callable[[ConnectionList], Tuple[bool, str]]

    def candidates(self) -> CandidateSet:
        return build_candidates(self.notes, self.window)


GOLD_CASES: List[GoldCase] = [
    # 1. Temporal contradiction — weak models call it a shared thread.
    GoldCase(
        name="contradiction-over-time",
        notes=[
            (
                "Cooling v1",
                "2026-02-10",
                ["distillation", "cooling"],
                "For the still, air cooling is enough — we do not need a water jacket.",
            ),
            (
                "Cooling v2",
                "2026-05-22",
                ["distillation", "cooling"],
                "I was wrong earlier: air cooling fails on long runs, we must add a "
                "water jacket.",
            ),
        ],
        window=["Cooling v2"],
        check=lambda r: (
            any(
                c.type == "contradiction-over-time"
                and "Cooling v1" in c.notes
                and "Cooling v2" in c.notes
                for c in r.connections
            ),
            "links the two cooling notes as a contradiction over time",
        ),
    ),
    # 2. False friend — shared keyword ("interface") but no real link. PRECISION.
    GoldCase(
        name="false-friend-precision",
        notes=[
            (
                "Synth UI",
                "2026-06-01",
                ["interface", "tools"],
                "A synthesizer-style knob controller for tuning Claude parameters.",
            ),
            (
                "NGO dashboard",
                "2026-06-02",
                ["interface", "ngo"],
                "An interface for NGOs to track donor impact metrics.",
            ),
        ],
        window=["NGO dashboard", "Synth UI"],
        check=lambda r: (
            not _links(r, "Synth UI", "NGO dashboard"),
            "did NOT fabricate a link between the two unrelated interfaces",
        ),
    ),
    # 3. Unrelated set — the right answer is empty. RESTRAINT.
    GoldCase(
        name="empty-restraint",
        notes=[
            (
                "Garden",
                "2026-06-01",
                ["garden"],
                "Notes on planting tomatoes and the timing of compost turning.",
            ),
            (
                "Taxes",
                "2026-06-02",
                ["finance"],
                "Need to pay the quarterly VAT and file the form by Friday.",
            ),
            (
                "Guitar",
                "2026-06-03",
                ["music"],
                "Practice the new fingerpicking pattern; tune down half a step.",
            ),
        ],
        window=["Garden", "Taxes", "Guitar"],
        check=lambda r: (
            len(r.connections) == 0,
            "returned an empty list for genuinely unrelated notes",
        ),
    ),
    # 4. Cross-language bridge (PL + EN, same idea).
    GoldCase(
        name="multilingual-bridge",
        notes=[
            (
                "Pomysl PL",
                "2026-06-01",
                ["ai", "tooling"],
                "Pomysł: narzędzie mapujące parametry Claude jak w syntezatorze, z "
                "fizycznymi pokrętłami.",
            ),
            (
                "Idea EN",
                "2026-06-10",
                ["ai", "tooling"],
                "Idea: a hardware controller that maps LLM parameters like a synth, "
                "with physical knobs.",
            ),
        ],
        window=["Idea EN"],
        check=lambda r: (
            _links(r, "Pomysl PL", "Idea EN"),
            "connected the Polish and English notes on the same idea",
        ),
    ),
    # 5. Buried emergent thread across 3 notes among 2 distractors.
    GoldCase(
        name="buried-emergent-thread",
        notes=[
            (
                "Thread A",
                "2026-06-01",
                ["modular"],
                "Modular cabins sold as a subscription — vacation as a service.",
            ),
            (
                "Distract 1",
                "2026-06-02",
                ["garden"],
                "Compost and mulch notes for the raised beds.",
            ),
            (
                "Thread B",
                "2026-06-05",
                ["pricing"],
                "Pricing modular homes as a recurring rental rather than a one-off sale.",
            ),
            (
                "Distract 2",
                "2026-06-06",
                ["music"],
                "New Digitakt patch ideas for the live set.",
            ),
            (
                "Thread C",
                "2026-06-09",
                ["modular"],
                "The recurring-revenue angle for prefab cabins keeps resurfacing.",
            ),
        ],
        window=["Thread C", "Distract 2"],
        check=lambda r: (
            any(
                len({"Thread A", "Thread B", "Thread C"} & set(c.notes)) >= 2
                for c in r.connections
            ),
            "surfaced the recurring-revenue thread across the scattered notes",
        ),
    ),
    # 6. Non-prescriptiveness probe (a clear thread, judged on phrasing).
    GoldCase(
        name="non-prescriptive-directions",
        notes=[
            (
                "Note X",
                "2026-06-01",
                ["blog"],
                "I keep wanting to write about local-first AI and why it matters.",
            ),
            (
                "Note Y",
                "2026-06-08",
                ["blog"],
                "Another thought on local-first AI and privacy — could be a post.",
            ),
        ],
        window=["Note Y"],
        check=_all_directions_non_prescriptive,
    ),
]


def case_names() -> Set[str]:
    return {c.name for c in GOLD_CASES}
