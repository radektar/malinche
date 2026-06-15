# Public Distribution Plan — Malinche

**Plan version:** 1.3 (MCP-first PRO model)
**Created:** 2025-12-17
**Last updated:** 2026-06-14
**Status:** DRAFT — pending approval
**Model:** Freemium (FREE/BYOK open-source + PRO subscription = MCP integration)

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
- **Freemium model** (FREE/BYOK open source + PRO subscription)

### Business model

The application is open source (MIT). AI features run locally via BYOK (the user's own `ANTHROPIC_API_KEY`). The paid PRO tier sells **MCP integration** — a hosted transcript database the user's LLM can search natively — not hosted AI summaries.

| Tier | Price | What it adds |
|---|---|---|
| **FREE (MIT)** | $0 | Local transcription, Markdown export, any recorder, basic tags |
| **+ BYOK** | $0 (user pays Anthropic directly) | AI summaries, smart tags, AI naming, versioning — all local with own key |
| **PRO Individual** | Subscription (amount TBD¹) | Cloud transcript DB + embeddings, local MCP server, auto-config for MCP clients, semantic search, cross-device sync |
| **PRO Organization** | Subscription (amount TBD¹) | PRO + org features (deferred — see §2.3) |

¹ Pricing is an open decision — see the open questions in [BACKLOG.md](../BACKLOG.md). Considered: subscription $5–$12/mo Individual; optional $25/mo Organization; or $79 lifetime. To be decided before Phase 10 (backend).

> **Key subtlety:** PRO does not replace BYOK. The fullest experience is **PRO + BYOK** — local AI summaries via the user's Anthropic key, plus a hosted, MCP-searchable transcript DB via the subscription.

### Key technical decisions

| Aspect | Decision | Rationale |
|---|---|---|
| **Packaging tool** | py2app + rumps | Tailored for menu bar apps, better than PyInstaller for this case |
| **CPU architecture** | Apple Silicon only (M1/M2/M3/M4) | Simpler build, 80%+ of new Macs |
| **whisper.cpp** | Download on first run | Smaller installer (~15 MB vs 550 MB) |
| **FFmpeg** | Statically bundled | No Homebrew dependency |
| **Code signing** | Yes ($99/yr) | Professional UX, no Gatekeeper warnings |
| **PRO value prop** | MCP integration | Defensible (DB + embeddings + MCP server) vs. a thin hosted-Claude wrapper; rides the growing MCP ecosystem |
| **PRO backend** | Supabase (Postgres + pgvector) + Cloudflare Workers | Managed DB with per-user RLS; thin stateless Workers for license + embeddings |
| **AI summaries** | Stay in MIT via BYOK | Not part of PRO; no Claude proxy on the backend |
| **Payments** | LemonSqueezy | Tax compliance; webhook → license_key issuance in Supabase |

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
✅ Freemium (FREE/BYOK open source + PRO subscription)

┌─────────────────────────────────────────────────────────────────────────┐
│                         MALINCHE FREE (MIT)                              │
│                     (Open Source — GitHub)                               │
├─────────────────────────────────────────────────────────────────────────┤
│ ✅ Auto-detect recorders / SD cards                                     │
│ ✅ Local transcription (whisper.cpp)                                    │
│ ✅ Basic tags (#transcription, #audio)                                  │
│ ✅ Markdown export                                                      │
│ ✅ Menu bar app + first-run wizard                                      │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                 MALINCHE + BYOK (own ANTHROPIC_API_KEY)                  │
│                 (still MIT — no subscription required)                   │
├─────────────────────────────────────────────────────────────────────────┤
│ ⭐ AI summaries (local, via your Claude key)                            │
│ ⭐ Smart AI tags                                                        │
│ ⭐ AI naming (auto-titles)                                              │
│ ⭐ Markdown versioning / Retranscribe                                   │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                    MALINCHE PRO INDIVIDUAL                               │
│                       (Subscription — amount TBD)                       │
├─────────────────────────────────────────────────────────────────────────┤
│ ⭐ Auto-pipeline transcript → hosted cloud DB + embeddings              │
│ ⭐ Local MCP server (search across all your transcripts)               │
│ ⭐ Auto-config for Claude Desktop / Cursor / Continue / Claude Code     │
│ ⭐ Semantic search across transcripts                                   │
│ ⭐ Cross-device sync                                                    │
│ (AI summaries still via BYOK — PRO does not host a Claude proxy)        │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│              MALINCHE PRO ORGANIZATION (deferred)                        │
│                       (Subscription — amount TBD)                       │
├─────────────────────────────────────────────────────────────────────────┤
│ 🏢 Org-only features (shared speaker DB, domain lexicon, knowledge base)│
│    are deferred and may ship as a separate product layered on the PRO   │
│    MCP server — not committed to the Malinche product scope at launch.  │
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

### 3.2. PRO data flow (v2.1.0)

PRO features live in a private `malinche_pro` package, lazy-loaded by the open-source app. The pipeline turns local transcripts into an LLM-searchable database:

```
[Malinche app FREE/MIT]                          [Malinche PRO add-on / private]
─────────────────                                ────────────────────────────────
Recorder → whisper.cpp → markdown in folder
                              │
                              │ (FREE: done here)
                              ▼
                    ┌────────────────────────┐
                    │ malinche_pro daemon    │  watches the .md folder
                    └────────────┬───────────┘
                                 │ upload + embedding request (JWT-auth)
                                 ▼
                    ┌────────────────────────┐
                    │ Supabase               │  Postgres + pgvector, per-user RLS
                    │  - transcripts         │
                    │  - transcript_embeddings│
                    └────────────┬───────────┘
                                 │ read (RLS-scoped)
                                 ▼
                    ┌────────────────────────┐
                    │ malinche_pro MCP server│  local stdio MCP
                    └────────────┬───────────┘
                                 │ MCP protocol
                                 ▼
                    Claude Desktop / Cursor / Continue / Claude Code / Zed
```

MCP MVP exposes 5 tools: `search_transcripts`, `get_transcript`, `list_recent`, `list_by_date_range`, `find_quotes`.

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

### Phase 10: PRO backend + MCP integration (PLANNED, post-publication, 6–12 weeks)

Does not block the open-source publication. Stack:

- **Supabase** (managed Postgres + pgvector), single-tenant with per-user RLS: tables `transcripts` and `transcript_embeddings`.
- **Cloudflare Workers** (thin, stateless): `POST /v1/license/validate` → JWT (`user_id + tier + expires_at`); `POST /v1/embeddings` → proxy to Voyage/OpenAI (computes chunk embeddings, does not store the transcript).
- **LemonSqueezy webhook** → creates/refreshes the user record + license_key in Supabase.
- **Private package `malinche_pro`**: `daemon.py` (folder watcher → upload), `mcp_server.py` (stdio MCP), `tools/` (5 MCP tools), `db_client.py`, `embedding_client.py`, `auto_config.py`, `license_jwt.py`.
- **Private repo `malinche-backend`**: Supabase migrations + Workers source. Not open source.

Out of scope: an AI-summaries proxy. BYOK stays in MIT — the backend never sees the user's Anthropic key and never generates summaries.

---

## 5. Testing strategy

### 5.1. Coverage requirements

- **Minimum 80% coverage** for all new modules
- **100% coverage** for critical modules: `src/config/settings.py`, `src/config/license.py`, `src/file_monitor.py`

### 5.2. Manual tests (Phase 8)

- [ ] Activate invalid key → UI error
- [ ] Simulate offline → license cache used
- [ ] Cache expiry (7 days) → fall back to FREE
- [ ] Use AI without BYOK configured → clear "set ANTHROPIC_API_KEY" prompt, no action
- [ ] Use MCP/cloud features without PRO → "Requires PRO subscription" log + no action

---

## 6. Costs

### 6.1. Infrastructure cost (PRO)

PRO does not host AI summaries (those are BYOK, paid by the user to Anthropic). The backend cost is the transcript DB + embeddings + license validation.

| Service | Free tier | Estimated cost (100 PRO users) |
|---|---|---|
| Embeddings (Voyage `voyage-3-lite`) | — | ~$0.05–0.20 / PRO user / month |
| Supabase (Postgres + pgvector) | Free tier covers early users | $0 → ~$25/mo (Pro) at scale |
| API hosting (Cloudflare Workers) | Generous free tier | $0–5 / month |
| **Total (100 users)** | | **~$10–50 / month** (mostly DB at scale) |

### 6.2. Revenue projection

- Model and amount: **TBD** — see open questions in [BACKLOG.md](../BACKLOG.md). Considered: subscription $5–$12/mo Individual; optional $25/mo Organization; or $79 lifetime.
- Break-even: a handful of active PRO subscriptions covers infrastructure.

---

## 7. Freemium summary

```
┌─────────────────────────────────────────────────────────────────┐
│                    FREEMIUM STRATEGY                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  FREE (GitHub, MIT)                                              │
│  ├─ Local transcription, no limits                               │
│  └─ Markdown export + basic tags                                 │
│                                                                  │
│  + BYOK (own ANTHROPIC_API_KEY, still MIT)                       │
│  ├─ AI summaries & smart tags & naming                           │
│  └─ Markdown versioning / retranscribe                           │
│                                                                  │
│  PRO INDIVIDUAL (subscription — amount TBD)                      │
│  ├─ Cloud transcript DB + embeddings                             │
│  ├─ Local MCP server + semantic search                           │
│  ├─ Auto-config for Claude Desktop / Cursor / Continue           │
│  └─ Cross-device sync                                            │
│                                                                  │
│  PRO ORGANIZATION (deferred)                                     │
│  └─ Org features may ship as a separate product on the PRO MCP   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

**Plan version:** 1.3 (MCP-first PRO model)
**Approval:** [ ] Pending
