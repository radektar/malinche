# Testing plan — PRO / MCP integration (v2.1.0)

> **Status:** specification. The PRO product lives in a private `malinche_pro`
> package that does not exist yet (Phase 10 of
> [PUBLIC-DISTRIBUTION-PLAN.md](PUBLIC-DISTRIBUTION-PLAN.md)). This document
> defines how it will be tested so the acceptance criteria are agreed before
> code is written. Executable skeletons live in `tests/pro/` (skipped until the
> package ships).

## What is being tested

The PRO pipeline turns local transcripts into an LLM-searchable database:

```
markdown folder → malinche_pro daemon → Supabase (Postgres + pgvector)
                                              ↓ (RLS-scoped read)
                                    malinche_pro MCP server
                                              ↓ (MCP protocol)
                          Claude Desktop / Cursor / Continue / Claude Code
```

Four surfaces under test: **MCP tools**, **daemon/upload pipeline**,
**license/JWT**, **auto-config wizard**.

## How to run

```bash
# Today (skeletons are skipped — proves wiring + markers are valid):
make test
venv/bin/python -m pytest tests/pro/ -v        # → all skipped, no errors

# Once malinche_pro is installed (private package):
pip install -e ../malinche-pro
venv/bin/python -m pytest -m pro -v            # runs the real PRO suite
```

The skeletons use `pytest.importorskip("malinche_pro")`, so they automatically
activate the moment the package is importable — no edit needed to "turn them
on" beyond filling in the bodies.

## Fixtures to prepare

| Fixture | Purpose | Notes |
|---|---|---|
| `tmp_transcripts_dir` | Folder the daemon watches | reuse `tests/conftest.py` HOME isolation |
| `sample_transcripts` | 3–5 `.md` files with known content + frontmatter | one must mention a topic semantically (e.g. "budget") for search ranking |
| `fake_supabase` | In-memory / testcontainers Postgres + pgvector | per-user RLS must be exercised, not bypassed |
| `stub_embeddings` | Deterministic vector for a given text | avoid real Voyage/OpenAI calls in unit tests |
| `license_keys` | one valid, one expired, one invalid | drives JWT + offline-cache cases |
| `mcp_client_configs` | temp config files for Claude Desktop / Cursor / Continue / Claude Code | assert merge-not-overwrite |

## Test matrix

### 1. MCP tools (`tests/pro/test_mcp_tools_spec.py`)

| Tool | Key cases | Acceptance |
|---|---|---|
| `search_transcripts` | semantic match ranking; `since` filter; RLS isolation | top result is the semantically closest; never returns another user's rows |
| `get_transcript` | by id; unknown id | full markdown returned; unknown → not-found error, not crash |
| `list_recent` | n most recent, desc | metadata only, correct order |
| `list_by_date_range` | inclusive bounds | boundary dates included |
| `find_quotes` | snippet + `context_chars` | each hit carries the requested surrounding context |

### 2. Daemon / upload pipeline (`tests/pro/test_pipeline_spec.py`)

- New `.md` → upload + embedding request issued.
- **Idempotency**: same content (sha256) never duplicates a row.
- Updated file replaces the existing row.

### 3. License / JWT

- Valid key → JWT carrying `user_id + tier + expires_at`.
- Offline within 7 days → cached license honoured.
- Cache older than 7 days → fall back to FREE.
- Invalid key → actionable error message (matches the UI copy).

### 4. Privacy gate

- `/v1/embeddings` returns vectors only and persists **no** raw transcript.
- BYOK stays local: the backend never receives `ANTHROPIC_API_KEY`.

### 5. Auto-config wizard

- For each of Claude Desktop / Cursor / Continue / Claude Code: writes a valid
  MCP entry and **merges** (does not clobber existing entries).

## Acceptance gates (product-owner sign-off)

PRO is "done" for v2.1.0 when:

1. `pytest -m pro` is green against a real Supabase (testcontainers or staging).
2. RLS isolation test passes — a user cannot read another user's transcripts.
3. Idempotency holds — re-syncing a folder creates zero duplicate rows.
4. Offline license cache behaves per the 7-day rule.
5. Auto-config produces a working MCP entry verified by an actual round-trip:
   ask a connected Claude/Cursor "what did I record about X" and get a hit.
6. Privacy gate verified — no raw transcript stored by the embeddings endpoint.
7. The doc-consistency suite (`tests/test_docs_consistency.py`) still passes, so
   the public FREE/BYOK/PRO story stays coherent after any doc updates.

## Out of scope (do not test here)

- AI summaries / tags / naming — those are MIT + BYOK, covered by
  `tests/test_summarizer.py` and `tests/test_tagger.py`.
- Speaker diarization, shared speaker DB, domain lexicon, knowledge base —
  deferred (v2.2.0+) or out of product scope.
