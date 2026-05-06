# Beta-1 FREE/PRO strategy (historical)

> **Status:** completed. The strategy below was implemented in beta-1 (PRO.1–PRO.5) and is still in force in beta.8.
>
> Supplement to [BETA-1-PLAN.md](BETA-1-PLAN.md). This document records the strategic decision and what shipped.

## Strategic decision: Option A — PRO = hosted convenience

For v1.0, BYOK remains a fully featured mode with all current capabilities. PRO becomes a convenience layer where Malinche hosts the API key (proxy to Anthropic / our own model), the user does not need their own console.anthropic.com account, and pays a flat subscription.

### Why Option A (and not B or C)

- **Option B** ("feature gate") would require 3–6 months of new code (diarization, domain lexicon, knowledge base) before anything could ship. We needed beta now.
- **Option C** ("organization tier only") requires cloud sync + SSO + admin (~6+ months). It can coexist with A in the future and is therefore deferred to v1.1+, not rejected.
- **Option A** is the cheapest to reverse: if we later move to a feature gate, "taking back" unlocked versioning from beta testers is acceptable (they signed up to a beta).

## What shipped in beta-1 (PRO.1–PRO.5)

### PRO.1 — Unlock current PRO flags for BYOK

`is_byok_configured()` was extracted to a single helper. Anywhere that previously checked `tier != FREE` now also accepts BYOK as enabled:

- `src/transcriber.py` — `can_version` is true for BYOK on FREE tier
- `src/menu_app.py` — Retranscribe submenu unlocked when BYOK is configured

### PRO.2 — Hide PRO activation UI in beta

`config.BETA_HIDE_PRO_UI = True` (default in beta). When set:
- Menu bar does not show "Activate PRO…"
- Status label does not switch between "Activate PRO…" and "Malinche PRO"
- `src/ui/pro_activation.py` module remains in the codebase and is reactivated for v1.0 with a real backend.

### PRO.3 — Privacy + beta disclaimer in the wizard

Wizard's AI step shows:

```
Privacy:
- Audio is processed locally by Whisper.
- Only the transcript is sent to Claude API (if a key is configured).

Beta:
- This is a closed beta. Paid features (PRO) are hidden.
- All AI features (summaries, tags, versioning) work with your own
  Anthropic key (BYOK).
- After beta we plan a hosted tier — BYOK will keep working.
```

### PRO.4 — `LicenseManager` is a beta no-op

The license module is unchanged functionally. `_verify_license()` always returns FREE — accurate from the system's perspective (no real license backend yet). A header comment in `src/config/license.py` documents the intent.

### PRO.5 — Communication in README + onboarding

`Docs/BETA-ONBOARDING.md` and `README.md` clarify: BYOK is a full product; the future PRO tier will be hosted convenience, not a feature gate.

## Feature status snapshot (still accurate in beta.8)

| Feature | Code state | In beta for BYOK |
|---|---|---|
| Whisper transcription | works | ✅ |
| Markdown export | works | ✅ |
| AI summary (Claude) | works via BYOK | ✅ |
| AI smart tags (Claude) | works via BYOK | ✅ |
| AI naming (filename from title) | works via BYOK | ✅ |
| Markdown versioning (v2/v3) | unlocked for BYOK | ✅ |
| Retranscribe menu | unlocked for BYOK | ✅ |
| Speaker diarization | enum only, no code | ❌ |
| Cloud sync | enum only | ❌ |
| Shared speaker DB | enum only | ❌ |
| Domain lexicon | enum only | ❌ |
| Knowledge base | enum + future doc | ❌ |
| Ollama summarizer | placeholder | ❌ |
| License activation UI | stub UI + no backend | hidden by `BETA_HIDE_PRO_UI` |

## Roadmap after beta (informational)

1. **beta-1 → beta-2** (4–6 weeks): bug fixes from tester feedback, stability. No new PRO features. (Status: shipped, currently at beta-8.)
2. **beta-2 survey**: short feedback survey in the menu validating Option A pricing (multiple choice: $5 / $10 / $20 / "won't pay"). Not in beta-1 by design.
3. **v1.0 implementation** — Option A:
   - Backend proxy to Anthropic API (FastAPI or Cloudflare Worker)
   - Stripe checkout + webhook → license key issuance
   - `LicenseManager.activate_license()` verifies key against backend (stub already in place)
   - Estimate: ~2–3 weeks of work + infrastructure setup
4. **v1.1+** (optional): PRO_ORG (Option C) as a separate tier coexisting with PRO Individual.

## Related documents

- [BETA-1-PLAN.md](BETA-1-PLAN.md) — main beta-1 plan (status: completed)
- [PUBLIC-DISTRIBUTION-PLAN.md](PUBLIC-DISTRIBUTION-PLAN.md) — full distribution plan
- [../BACKLOG.md](../BACKLOG.md) — current active and planned work
- [../CHANGELOG.md](../CHANGELOG.md) — release history
