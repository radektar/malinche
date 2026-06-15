# Readiness criteria — doc-strategy rewrite (MCP-first PRO)

> **Scope of this document.** This is the Definition of Done for the *documentation
> strategy rewrite* that moved Malinche's PRO story from "hosted Claude proxy" to
> "MCP integration", with pricing left explicitly **TBD**. It does **not** cover the
> future PRO product build — that has its own acceptance gates in
> [TESTING-PRO-MCP.md](TESTING-PRO-MCP.md).
>
> Each criterion below maps to an automated test or a one-line command you can run.
> The solution is "done" when sections A and B are green. Section C is the forward
> contract (kept honest by the same tests). Section D lists repo-health items that
> are **out of scope** for this rewrite but worth tracking.

## A. Documentation coherence (the deliverable)

All enforced by `tests/test_docs_consistency.py` — pure-text, no `src` imports, fast and stable.

Run:

```bash
venv312/bin/python -m pytest tests/test_docs_consistency.py -v
```

Expected: **29 passed**.

| # | Criterion | Test |
|---|---|---|
| A1 | README.md, BACKLOG.md, PUBLIC-DISTRIBUTION-PLAN.md exist and are non-empty | `test_doc_exists_and_nonempty` |
| A2 | One pricing story — every product price token sits in a TBD/considered context; infra-cost lines are exempt | `test_no_declared_price` |
| A3 | No stale "PRO = hosted Claude / API proxy / server-side summaries" framing | `test_no_stale_hosted_ai_framing` |
| A4 | No leftover per-tier minute caps from the old subscription model | `test_no_stale_minute_caps` |
| A5 | MCP is visibly the flagship (≥ 3 mentions per doc) | `test_mcp_is_the_flagship` |
| A6 | All three usage levels (FREE / BYOK / PRO) described in every doc | `test_three_usage_levels_present` |
| A7 | Private personal-AI workspace (Cortex / Obsidian) does not leak | `test_no_private_workspace_leak` |
| A8 | BACKLOG and the distribution plan offer the *same* pricing options | `test_pricing_options_match_across_docs` |
| A9 | BYOK is explained, not just named (`ANTHROPIC_API_KEY` shown) | `test_byok_explained_not_just_named` |
| A10 | No legacy project names (Olympus / Transrec) | `test_no_legacy_project_names` |
| A11 | Relative markdown links resolve to real files | `test_internal_links_resolve` |

## B. Test infrastructure

| # | Criterion | Verification |
|---|---|---|
| B1 | PRO spec skeletons skip cleanly until `malinche_pro` ships (no errors) | `venv312/bin/python -m pytest tests/pro/ -v` → all skipped |
| B2 | The `pro` marker is registered (no `--strict-markers` failure) | declared in `pyproject.toml`; B1 passing proves it |
| B3 | Full non-integration suite runs on Python 3.12 | `venv312/bin/python -m pytest -q` (see §D for known failures) |

> **Python version note.** The committed `venv/` is 3.9.6 and cannot import `src`
> (the code uses 3.10+ `match` and `X | Y` unions). Use `venv312/` (Python 3.12.12)
> to run the suite. `venv312/` is local-only and should stay untracked.

## C. Forward contract (PRO product — not built yet)

The PRO product is specified, not implemented. Its acceptance gates live in
[TESTING-PRO-MCP.md](TESTING-PRO-MCP.md) and its executable specs in `tests/pro/`
(skipped via `pytest.importorskip("malinche_pro")`). The doc-consistency suite (§A)
guards the *story* so it stays coherent until that code lands; gate A7 in
TESTING-PRO-MCP.md re-asserts this.

## D. Out of scope — pre-existing repo-health items

These failed before this rewrite and are unrelated to it (the rewrite touched only
docs + new test files). Flagged for a separate decision, not blocking this DoD:

1. **`test_license.py` (×3)** — tier reads PRO because the repo `.env` carries a real
   `ANTHROPIC_API_KEY`; BYOK promotes the tier in the dev environment.
2. **`test_menu_bar_icons.py`** — `ModuleNotFoundError: PIL`; Pillow is not declared in
   `requirements.txt`.
3. **`test_versions_sync.py`** — `setup_app.py` `APP_VERSION = "2.0.0-beta.10"` vs the UI's
   `2.0.0-beta.8`.

Latest full run (Python 3.12): **380 passed, 5 failed, 7 skipped** — the 5 failures are
exactly the items above.
