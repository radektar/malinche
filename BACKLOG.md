# Malinche Backlog

> Active work and planned features. For shipped items see [CHANGELOG.md](CHANGELOG.md).
>
> **Related:**
> - [Docs/PUBLIC-DISTRIBUTION-PLAN.md](Docs/PUBLIC-DISTRIBUTION-PLAN.md) — distribution strategy
> - [Docs/BETA-1-PLAN.md](Docs/BETA-1-PLAN.md) — beta program

---

## Business model: Freemium

```
┌─────────────────────────────────┬───────────────────────────────┐
│  FREE (GitHub, open source)     │  PRO ($79 lifetime)           │
├─────────────────────────────────┼───────────────────────────────┤
│  ✅ Recorder auto-detection     │  ✅ Everything in FREE +      │
│  ✅ Local transcription         │  ⭐ AI summaries              │
│  ✅ Markdown export             │  ⭐ AI tags                   │
│  ✅ Basic tags                  │  ⭐ Cloud sync (planned)      │
│  ❌ AI features                 │  ⭐ Web dashboard (planned)   │
└─────────────────────────────────┴───────────────────────────────┘
```

---

## v2.0.0 FREE — remaining work

- [ ] **Code signing & notarization** (requires $99 Apple Developer Program)
- [ ] **py2app bundle size optimization** (currently 43 MB, target <20 MB excluding models)
  - Audit largest dependencies (`du -sh dist/Malinche.app/Contents/Resources/*`)
  - Tighten py2app `excludes` for unused PyObjC frameworks
  - Consider switching to `pyinstaller` if savings are material

## v2.1.0 PRO — backend & features

- [ ] **PRO backend** (Cloudflare Workers + LemonSqueezy)
  - Endpoints: `/v1/license`, `/v1/summarize`, `/v1/tags`
  - License validation in `src/config/license.py`
- [ ] **Marketing site** at `malinche.app` with checkout flow
- [ ] **AI summaries integration** (currently gated behind feature flag)
- [ ] **AI tagging** (gated)
- [ ] **Cloud sync** for transcripts (post-launch)

## v2.2.0+ Knowledge Base (PRO future)

- [ ] **Speaker diarization** — identify speakers across recordings
- [ ] **Domain lexicon engine** — recognize jargon per industry
- [ ] **Knowledge base builder** — extract facts and build a queryable knowledge base
- [ ] See `Docs/future/knowledge-base-engine.md` for design notes

---

## Open questions (need decisions)

- [ ] Apple Developer Program registration ($99/year)
- [ ] Architectures: Apple Silicon only, or also Intel?
- [ ] PRO pricing: $79 lifetime vs subscription model?

---

## Improvements / nice-to-have

### Configurable Core ML mode

- New setting `WHISPER_COREML_MODE` with values `auto | off | force`
  - `auto` — try Core ML, fall back to CPU on failure (current behavior)
  - `off` — always CPU
  - `force` — Core ML only, error on failure (debug)
- Heuristic detection: if N out of last M whisper runs failed with Core ML errors, auto-disable for the session

### Native menu bar wrapper

The current Python-based menu bar app (rumps + PyObjC) works but ships 43 MB of Python runtime. A Swift launcher could:
- Set `PATH`/`PYTHONPATH` and start the Python daemon as a child process
- Reduce the standalone bundle size if the daemon stays separate

This is a follow-up after py2app size optimization fails to hit the <20 MB target.

### Documentation

- [ ] Translate `Docs/archive/` and `Docs/testing-archive/` (low priority — historical)
- [ ] Translate `CHANGELOG.md` historical entries (low priority — frozen text)

---

## Recent shipped work

For the full release log see [CHANGELOG.md](CHANGELOG.md). Highlights since v1.x:

- v2.0.0-beta.8: UI redesign (English UI, settings tabs, log viewer, aztec accent palette)
- v2.0.0-beta.6: Multi-device deduplication and versioned retranscription
- v2.0.0-beta.4: First-run wizard polish, py2app bundle, DMG release
- v2.0.0-beta.1 → beta.3: Universal recorder support, dependency download, settings UI
