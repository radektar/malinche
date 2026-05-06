# Public Distribution Plan — Malinche

**Plan version:** 1.2 (Freemium — Subscription Model)
**Created:** 2025-12-17
**Last updated:** 2026-05-05
**Status:** DRAFT — pending approval
**Model:** Freemium (FREE open-source + PRO subscription)

---

## Table of contents

1. [Executive summary](#1-executive-summary)
2. [Strategic decisions](#2-strategic-decisions)
3. [Target architecture](#3-target-architecture)
4. [Implementation plan — phases](#4-implementation-plan--phases)
5. [Testing strategy](#5-testing-strategy)
6. [Costs](#6-costs)
7. [Freemium summary](#7-freemium-summary)

---

## 1. Executive summary

### Project goal

Transform Malinche from a developer tool into a publicly distributable application with:
- One-step install (drag & drop into Applications)
- Support for any USB recorder or SD card
- Professional UX (code signing, notarization)
- Auto-download of dependencies (whisper.cpp + models)
- **Freemium model** (FREE + PRO Individual + PRO Organization)

### Business model

| Tier | Price | Features | Limits |
|---|---|---|---|
| **FREE** | $0 (open source) | Local transcription, MD export, any recorder | None |
| **PRO Individual** | Monthly subscription | FREE + AI summaries, AI tags, diarization | 300 min/month |
| **PRO Organization** | Monthly subscription | PRO + Knowledge Base, Shared Lexicon, Cloud Sync | 1000+ min/month |

### Key technical decisions

| Aspect | Decision | Rationale |
|---|---|---|
| **Packaging tool** | py2app + rumps | Tailored for menu bar apps, better than PyInstaller for this case |
| **CPU architecture** | Apple Silicon only (M1/M2/M3/M4) | Simpler build, 80%+ of new Macs |
| **whisper.cpp** | Download on first run | Smaller installer (~15 MB vs 550 MB) |
| **FFmpeg** | Statically bundled | No Homebrew dependency |
| **Code signing** | Yes ($99/yr) | Professional UX, no Gatekeeper warnings |
| **PRO backend** | FastAPI (Python) | Shares logic with the client; easy AI integration |
| **Payments** | LemonSqueezy / Stripe | Tax compliance, subscription + API key management |

---

## 2. Strategic decisions

### 2.1. Target platform

```
✅ Apple Silicon (ARM64) only

Rationale:
- 80%+ of new Macs are Apple Silicon (since 2020)
- Simplifies the build (single binary)
- Core ML acceleration only works on Apple Silicon
- Intel Mac users can run the dev version from source
```

### 2.2. Target user

```
✅ Non-technical user

Implications:
- All dependencies downloaded automatically
- No Homebrew required
- Wizard walks the user through setup
- Clear instructions for Full Disk Access
```

### 2.3. Distribution model

```
✅ Freemium (FREE + PRO)

┌─────────────────────────────────────────────────────────────────────────┐
│                         MALINCHE FREE                                   │
│                     (Open Source — GitHub)                               │
├─────────────────────────────────────────────────────────────────────────┤
│ ✅ Auto-detect recorders / SD cards                                     │
│ ✅ Local transcription (whisper.cpp)                                    │
│ ✅ Basic tags (#transcription, #audio)                                  │
│ ✅ Markdown export                                                      │
│ ✅ Menu bar app                                                         │
│ ✅ First-run wizard                                                     │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                         MALINCHE PRO INDIVIDUAL                         │
│                       (Monthly subscription)                            │
├─────────────────────────────────────────────────────────────────────────┤
│ ⭐ AI summaries (server-side via Claude/GPT)                            │
│ ⭐ Smart AI tags                                                        │
│ ⭐ Auto-titles for files                                                │
│ ⭐ Speaker diarization (local/server)                                   │
│ 📊 Limit: 300 minutes of processing per month                           │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                         MALINCHE PRO ORGANIZATION                       │
│                       (Monthly subscription)                            │
├─────────────────────────────────────────────────────────────────────────┤
│ 🏢 Shared speaker database                                              │
│ 🏢 Domain lexicon                                                       │
│ 🏢 Knowledge base extraction                                            │
│ 🏢 Cloud sync (Obsidian, S3, Azure)                                     │
│ 📊 Limit: 1000+ minutes of processing per month                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Target architecture

### 3.1. App layout (v2.0.0)

```
~/Applications/
└── Malinche.app/                        (~15 MB download)
    └── Contents/
        ├── MacOS/
        │   └── Malinche                 (main executable)
        ├── Resources/
        │   ├── icon.icns
        │   └── ffmpeg                   (static, ~15 MB)

~/Library/Application Support/Malinche/
├── bin/whisper-cli                      (downloaded on first run)
├── models/                              (GGML models)
├── config.json                          (user settings)
├── state.json                           (per-volume state)
├── runtime/transcriber.lock
├── recordings/                          (staging dir)
└── logs/malinche.log                    (rotating, 5×5 MB)
```

---

## 4. Implementation plan — phases

### Phase 1: Universal recording sources (DONE ✅)
Detect any external volume / SD card. New `UserSettings` system.

### Phase 2: Dependency download system (DONE ✅)
Automatic whisper.cpp + model downloads from GitHub / HuggingFace.

### Phase 3: First-run wizard (DONE ✅)
Friendly tutorial and initial configuration.

### Phase 4: py2app packaging (DONE ✅)
`.app` bundle generation.

### Phase 5: Code signing & notarization (IN PROGRESS)
Sign the application with an Apple Developer certificate; submit for notarization.

### Phase 6: Professional DMG (DONE ✅, unsigned beta)
DMG build scripts + tester instructions.

### Phase 7: GUI settings & polish (DONE ✅)
Settings window, folder picker, language and model selection.

### Phase 8: Freemium infrastructure (DONE ✅)
- Feature flags (FREE/PRO/PRO_ORG)
- License manager with offline cache (7 days)
- PRO gates in summarizer and tagger
- PRO activation UI in the menu bar

### Phase 9: UI redesign (DONE ✅)
- Wizard consolidation: single config step (folder + language + model)
- Settings: single panel instead of a sequence of alerts
- Menu bar state icons + new app icon + custom DMG background
- English UI; aztec accent palette

### Phase 10: PRO backend (PLANNED)
FastAPI service for `/v1/license`, `/v1/summarize`, `/v1/tags`. Hosted on Cloudflare Workers + LemonSqueezy.

---

## 5. Testing strategy

### 5.1. Coverage requirements

- **Minimum 80% coverage** for all new modules
- **100% coverage** for critical modules: `src/config/settings.py`, `src/config/license.py`, `src/file_monitor.py`

### 5.2. Manual tests (Phase 8)

- [ ] Activate invalid key → UI error
- [ ] Simulate offline → license cache used
- [ ] Cache expiry (7 days) → fall back to FREE
- [ ] Try to use AI on FREE tier → "Requires PRO" log + no action

---

## 6. Costs

### 6.1. Infrastructure cost (PRO)

| Service | Free tier | Estimated cost (100 PRO users) |
|---|---|---|
| Claude API (Haiku) | — | ~$10–20 / month |
| Diarization (VAD / embeddings) | Local | $0 (user-side CPU) |
| API hosting | CF Workers / Fly.io | $0–5 / month |
| **Total** | | **~$15–25 / month** |

### 6.2. Revenue projection

- Model: subscription (e.g. $8/mo Individual, $25/mo Organization)
- Break-even: ~5–10 active PRO subscriptions

---

## 7. Freemium summary

```
┌─────────────────────────────────────────────────────────────────┐
│                    FREEMIUM STRATEGY                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  FREE (GitHub, MIT)                                              │
│  ├─ Local transcription, no limits                               │
│  └─ Markdown export                                              │
│                                                                  │
│  PRO INDIVIDUAL (monthly subscription)                           │
│  ├─ AI summaries & smart tags                                    │
│  ├─ Speaker diarization                                          │
│  └─ Limit: 300 minutes / month                                   │
│                                                                  │
│  PRO ORGANIZATION (monthly subscription)                         │
│  ├─ Knowledge base                                               │
│  ├─ Domain lexicon                                               │
│  └─ Cloud sync & shared speaker DB                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

**Plan version:** 1.2 (Subscription Model)
**Approval:** [ ] Pending
