# Insight → Action — plan (next phase)

**Status:** Proposed · agreed direction, integration spec pending
**Date:** 2026-06-27
**Context:** sparring session (radek-product). Follows the Insights window
interactivity work (PR #41, beta.13).

---

## The problem this fixes

Today a surfaced insight's whole afterlife is "Zachowaj → a line in a digest
note in Obsidian." That is storage, not survival — we add to the graveyard of
voice notes instead of resolving it. The connection can be brilliant; if nothing
changes in what the user *does*, the value delivered is zero.

Two structural flaws exposed:

1. **The insight layer is wrongly coupled to Obsidian.** Transcripts → Obsidian
   is correct (storage is the right job for a transcript). Insights → Obsidian
   is wrong (storage is the wrong job for an insight). The insight layer must be
   **Obsidian-agnostic**; without Obsidian, the value of an insight does not
   change, because its value was never in being filed.
2. **"Keep" is a like button — it lies.** "Kept" means "couldn't be bothered to
   delete," not "this was valuable." The only honest signal of value is whether
   the user *did something* because of the insight.

## Thesis (the ultimate value)

> Malinche turns a graveyard of voice notes into a small number of **provoked
> actions** — decisions made, ideas developed, things committed to — that would
> not have happened otherwise.

Transcript = storage. Insight = spark. **Action = value.** The goal is not for
an insight to *survive* (a preserved-but-inert insight is worthless) but to be
**metabolized** — consumed and turned into something else.

Positioning bet (named explicitly): we build an **action engine** (KPI =
action rate), not a **thinking mirror** (KPI = reflection). This narrows the
audience to doers; accepted for the N=1 validation phase (Radek is the user).

## Design — decided

### The gesture: a flat action menu, human decides

When an insight is shown, the user picks the action. **Flat menu, no
model-suggested default, regardless of insight type** — the human decides every
time. (Decision 2026-06-27, overriding the earlier "model suggests" lean.)

```
emergent-idea: "Recorder + Obsidian = one product"
[Rozwiń]  [Zadanie]  [Kalendarz]  [Kopiuj]               [Odrzuć]
```

Why flat / human-decides for now: it produces **clean, unbiased preference
data** ("given a free choice, what does the user do with an insight of type X").
A model-suggested default would contaminate the signal via default-bias — we'd
measure suggestion-acceptance, not true intent. The flat menu is the instrument
that *earns the right* to a smart-default ("first move") version later: the
`action_taken` log becomes the training data for what a future router should
suggest. We do not build the router before we have watched unbiased choices.

### The mechanism: handoff packages, not in-app hosting

A gesture = **package the insight's context and hand it off to an external
tool.** Malinche does not host the conversation or store the action. It packages
and throws over the wall.

- The synthesis already emits, per connection, a `directions` field (2-4
  "A: Could you…?" options). **These are already the action candidates** — today
  they are inert read-only text. Make each handoff carry the insight + source
  summaries + the relevant direction(s) as the seeded payload. Repurpose, don't
  invent a new layer.

### Handoff targets — tiered by integration cost

1. **Deep links — zero OAuth (the real minimum).** Feel like integration, cost
   nothing:
   - LLM thread → `claude.ai/new?q=<seeded prompt>` (handoff to the user's tool;
     in-app LLM is explicitly *out*).
   - Calendar → generate an `.ics` file and `open` it → macOS Calendar.app
     prompts to add. Local, offline, on-brand for a Mac app. (Google Calendar
     render URL as the alternative.)
2. **Clipboard — fallback** for long context or tools without a URL scheme.
3. **API integrations (Linear, Google Calendar) — later, gated on conversion.**
   Auto-create issues/events. Needs OAuth. Build only once the handoff proves it
   converts.

Minimum to ship = **LLM-thread + .ics + clipboard fallback** (not calendar
alone — calendar mis-routes the majority: emergent-idea, the most common type,
wants development, not a time slot).

### Action maturity varies per insight

Some insights are ready-to-act; some need more thought first (a conversation).
The flat menu already covers both: "Rozwiń" (→ LLM) for the not-yet-ready,
"Zadanie"/"Kalendarz" for the ready. No type-locked routing — the human reads
the insight and picks.

## Validation — the gesture *is* the instrument

Extend `{vault}/.malinche/signal.jsonl`: replace the kept/dismissed event with
**`action_taken: {kind, target}`** (kind = develop | do | decide | none; target
= llm | calendar | task | clipboard). **Action-rate replaces keep-rate** as the
core KPI. The act of using an insight is the measurement; no separate survey.

- **Success signal (binary):** a non-trivial share of surfaced insights produce
  at least one handoff (action), not just a keep/dismiss.
- **Kill condition:** users engage insights but never hand off to action →
  "interesting but useless"; revisit synthesis quality or the whole thesis
  before building heavier integrations.

## Sequence (hypothesis discipline)

0. **First, look at real insights.** The API key is verified live (2026-06-26);
   run the digest on the real vault and eyeball N=5-10. Shallow → fix synthesis
   first; the afterlife is moot. Good → proceed. *(Gate — hours, not weeks.)*
1. Build the flat action row + handoff packages (LLM-thread + .ics + clipboard).
   Demote "Zachowaj" to a secondary archive; keep "Odrzuć".
2. Instrument `action_taken` in `signal.jsonl`.
3. Measure action-rate on real use (Radek, N=1) for 2-4 weeks.
4. Only if it converts: API integrations + the smart-default ("first move")
   router trained on the collected `action_taken` data.

## Design locks (decided during the 2026-06-27 code review)

These are constraints the integration spec must honour — locked now so step 2
builds on them rather than retrofitting:

- **One canonical connection signature.** Today three writers disagree:
  `validation_signal.signal_key` (no type, truncated, `\n` join),
  `dismissals.connection_signature` (with type, full sha1, `|` join), and the
  digest `conn_meta.sig`. The `action_taken` instrument is worthless if its
  events can't be joined back to the connection they measure — so step 2
  unifies on a **single `signature(notes, synthesis_type)`** shared by the
  digest sidecar, the dismissal store, and the action log. **The sidecar/deck
  must carry the original `synthesis_type` (or the precomputed sig)** — today
  `deck_from_dicts` maps synthesis→UI type and loses it, so the window can't
  reconstruct the signature. Add it to the sidecar contract.
- **"Odrzuć" is a signal, not a suppressor.** The window dismiss records
  `action_taken: {kind: none}` only; it does **not** persist to the dismissal
  store. Durable suppression stays the Obsidian-native `dismissed:` frontmatter
  path. (Resolves the "nie wróci" copy: change it, don't wire persistence.)

## Next deliverable (explicit TODO)

**The integration / call spec** — the concrete list of targets, their handoff
mechanisms (URL schemes, `.ics` shape, clipboard payload format), the seeded-
prompt templates per insight type, and the `action_taken` schema (carrying the
canonical signature above). Out of scope for this doc; it is the next step, to
be written before implementation.

## Open / parked

- Smart-default router (Option A) and the subtle-hint hybrid — parked until
  `action_taken` data justifies them.
- Non-doer (reflection) audience — explicitly *not* served by this direction.
- **Transcript-corpus divergence** (code-review #3). `candidate_assembly` scans
  top-level `*.md` only; the Insights recent-rail disk fallback scans
  recursively. A transcript nested in a subfolder would show in the rail but be
  invisible to synthesis. **Low impact for now** — Malinche writes transcripts
  flat to the vault root, so the live data agrees. Parked; fix by extracting one
  `iter_transcript_notes(vault)` if/when we touch the corpus loader, or by
  declaring top-level the contract and making the rail match.
