# Beta-1 plan (historical)

> **Status:** completed. Beta-1 shipped on 2026-04 with closed beta DMG. Subsequent betas (beta.2 through beta.8) followed.
>
> This document is preserved as a record of what shipped in the alpha.18 → beta.1 milestone. Active work and the current roadmap live in [BACKLOG.md](../BACKLOG.md).

## Goal at the time

Move Malinche v2.0.0-alpha.18 to a **closed beta** for ~20–50 testers using **BYOK only** (each tester pastes their own `ANTHROPIC_API_KEY`). No monetization, no backend, no public marketing.

## Intentional deferrals (still valid for beta)

- ❌ Apple Developer ID + notarization — pending validation of the beta
- ❌ License backend, Stripe/LemonSqueezy, PRO tier
- ❌ malinche.app site, hosted privacy policy
- ❌ Sparkle auto-updates, telemetry/Sentry, full i18n
- ❌ Mac App Store

Consequence: testers must accept the UNSIGNED DMG. Acceptable for closed beta, not acceptable for public release.

## Phase P0 — shipped in beta-1

- **P0.1** Onboarding doc for the unsigned DMG (right-click → Open or `xattr -d com.apple.quarantine`)
- **P0.2** Manual test checklist refreshed for alpha.16/.17/.18 scenarios
- **P0.3** "Report bug" menu item with prefilled GitHub Issue (diagnostic info, last 30 log lines)
- **P0.4** Log rotation (`RotatingFileHandler`, 5 × 5 MB)
- **P0.5** Update check via GitHub Releases API (background thread, 24h cadence)
- **P0.6** Privacy disclaimer in the wizard's AI step
- **P0.7** Version bump to `2.0.0-beta.1`, CHANGELOG entry, build & DMG

## Phase P1 — shipped after first DMG

- **P1.1** GitHub Release page with DMG + checksums via `gh release create`
- **P1.2** "Closed Beta" section added to README (public-facing)
- **P1.3** PRO/license UI hidden behind feature flag — see [BETA-1-FREE-PRO-STRATEGY.md](BETA-1-FREE-PRO-STRATEGY.md)
- **P1.4** Diagnostic info dump to clipboard (`Copy diagnostics` menu item)

## Phase P2 — deferred to beta-2+

- Sentry free tier (5k events/month) if P0.3 bug reports prove insufficient
- User-selectable LLM model from Settings (currently hardcoded `claude-haiku-4-5-20251001`)
- Discord/Slack workspace for testers (only if >30 active testers)
- `OllamaSummarizer` for testers without Anthropic budget — stub at [src/summarizer.py](../src/summarizer.py)

## Decisions confirmed at the time (still in force)

1. **Update checker** uses `threading.Timer` on a side thread; UI mutations go through `_run_on_main_thread()` (alpha.13 pattern). Single HTTP call every 24 h.
2. **Diagnostic info to GitHub Issue:** 30 log lines only (URL limit ~8000 chars). Full dump available via clipboard (P1.4).
3. **`scripts/install_for_beta.sh`:** not shipped — onboarding doc was sufficient.
4. **README "Closed Beta" section:** public, in `main`. Repo is public; testers land there with a clear "this is beta, not production" message.
5. **Repository URL:** since 2026-05 the repo is `https://github.com/radektar/malinche` (it was `radektar/transrec` during beta-1 — auto-redirect handles old links).
6. **PRO/license UI in beta:** hidden. BYOK unlocks all current flags (versioning, retranscribe).

## Related documents

- [BETA-1-FREE-PRO-STRATEGY.md](BETA-1-FREE-PRO-STRATEGY.md) — feature-flag strategy for the beta
- [PUBLIC-DISTRIBUTION-PLAN.md](PUBLIC-DISTRIBUTION-PLAN.md) — full distribution plan
- [CHANGELOG.md](../CHANGELOG.md) — release history
- [BACKLOG.md](../BACKLOG.md) — active and planned work
