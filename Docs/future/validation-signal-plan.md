# Validation signal — build plan (kept/dismiss instrument)

Closes the validation loop for the Insights "Konstelacja" window: every
Zachowaj/Odrzuć click appends one line to `{vault}/.malinche/signal.jsonl`, so
after 2–4 weeks `kept` vs `dismissed` **by connection type** is one `jq` away.

Decision record: `ADR-003` (in-session). Accepted with amendments A1–A3.
Pattern: **pure recorder (testable, AppKit-free) → thin controller wiring**,
mirroring `insight_pipeline.py` + `dashboard_window.py`.

Branch: `feat/validation-signal` (off current HEAD — does **not** touch the
uncommitted WIP on `transcriber/summarizer/app_core/settings_window`).

## Scope

- **In:** append-only event log; controller wiring; pure-module + user-scenario tests.
- **Out (by design):** tally/analysis tooling (`jq` suffices for N=weeks);
  kept→digest feedback loop (the flash copy "trafia do digestu" is aspirational,
  not behaviour — separate gap); model default (Opus vs Haiku stays an offline eval).

## Record schema (A2)

```json
{"v": 1, "ts": "2026-06-26T10:00:00", "action": "kept", "conn_type": "contradiction-over-time", "label": "…", "key": "a1b2c3d4"}
```

- `v` — schema version, so added fields never break old lines.
- `key` — stable hash of the connection's sorted note set → dedup the same
  insight surfaced across multiple digests.
- `action` — `kept` | `dismissed`.

## Checklist

- [ ] **Recorder** — `src/connections/validation_signal.py`:
      `record_signal(action, conn_type, label, *, key=None, path=None, now=None)`
      appends one JSON line. `signal_log_path()` derives from
      `insight_pipeline.latest_insights_file().parent` (**A3** — shared `.malinche`
      dir, can't drift). On write failure: `logger.warning` + swallow (**A1** —
      best-effort for UI, but a broken path surfaces in `make logs`, never silent).
      `signal_key(notes)` = short hash of sorted note paths.
- [ ] **Pure tests** — `tests/test_validation_signal.py` (no AppKit): writes a
      line, appends a second, creates a missing dir, bad input → warns (not raises),
      `key` stable for same notes / differs for different.
- [ ] **Controller wiring** — `dashboard_window.py`: in `keepClicked_` and
      `dismissClicked_`, capture `self._deck.active()` **before** the mutation,
      compute `key`, call `record_signal` inside try/except. Record **at click**
      (not in `afterKeepFlash_`) so closing the window mid-flash still logs.
- [ ] **User-scenario tests** — `tests/test_signal_scenarios.py` (`ui`-marked),
      driving the real handlers (see below).
- [ ] **Verify** — flake8 on changed files + full `make test` green.
- [ ] **Manual smoke** — Radek, live app on 3.12 (see manual checklist below).

---

## Test scenarios — "I test as the user"

Each scenario is framed as a user action and asserts the **observable artifact**
(a line in `signal.jsonl`), not internals. Automated ones drive the real
`keepClicked_`/`dismissClicked_` handlers headless against a temp signal path.

### Automated (pytest — run in the loop, gate the build)

| ID | Jako użytkownik… | Oczekiwany artefakt |
|----|------------------|---------------------|
| **US-1** | Zachowuję pokazany insight | 1 linia, `action=kept`, `conn_type` = typ pokazanego połączenia, `key` obecny |
| **US-2** | Odrzucam pokazany insight | 1 linia, `action=dismissed`, `conn_type` = typ **usuniętego** połączenia (złapany przed mutacją) |
| **US-3** | Triażuję sesję: Zachowaj → Zachowaj → Odrzuć (różne typy) | 3 linie, kolejność zachowana, typy poprawne, plik **dopisywany** nie nadpisywany |
| **US-4** | Ten sam insight wraca w drugim digeście, znów Zachowaj | 2 linie z **tym samym `key`** (dedup działa) |
| **US-5** | Klikam Zachowaj, gdy ścieżka vaulta jest zepsuta | deck się przesuwa (brak wyjątku), **0 linii**, `warning` w logu |
| **US-6** | Zachowuję i zamykam okno w trakcie złotego błysku | linia **jest** (zapis na klik, nie po 0.8s timerze) |
| **US-7** | Otwieram okno przy "Cisza w korpusie" (pusty deck) i klikam | keep/dismiss to no-op, **0 linii** |
| **US-8** | (pure) Recorder dostaje złą wartość | `warning`, brak `raise`; `key` stabilny dla tych samych notatek |

### Manual (Radek, live app on 3.12 — post-merge smoke)

- **M-1** Realny digest → otwórz Insights → Zachowaj →
  `cat "$TRANSCRIBE_DIR/.malinche/signal.jsonl"` pokazuje linię z poprawnym `conn_type`.
- **M-2** Odrzuć kolejny → druga linia, `action=dismissed`.
- **M-3** Zachowaj i zamknij okno zanim zgaśnie błysk → linia mimo to zapisana.
- **M-4** Po ~tygodniu: `jq -r '.action+" "+.conn_type' signal.jsonl | sort | uniq -c`
  daje sensowny rozkład kept-vs-dismissed per typ.

---

## Status — complete (2026-06-26)

Recorder + controller wiring shipped with A1–A3 baked in. **15 new tests**
(10 pure + 5 user-scenario); the insights+signal suite is **62 green** on 3.12,
flake8 clean on all changed files.

- ✅ `validation_signal.py` — `record_signal` / `signal_log_path` (shared `.malinche`,
  A3) / `signal_key`; failure logs + swallows (A1); `v`+`key` records (A2).
- ✅ `dashboard_window.py` — `_emit_signal` called at click in `keepClicked_` /
  `dismissClicked_`, active connection captured before mutation.
- ✅ Pure tests: write / append / mkdir / US-4 dedup / US-5 broken-path / US-8 coercion.
- ✅ Scenario tests (real handlers, headless): US-1 keep, US-2 dismiss, US-3 session,
  US-6 record-at-click (window closed mid-flash), US-7 empty deck.
- ⬜ Manual M-1…M-4 — Radek, live app on 3.12 after merge.

**Note (pre-existing, not from this change):** `tests/test_status_panel.py` +
`tests/test_dashboard_window.py` can't be collected in one process — both register
an ObjC class `_FlippedView` (collision lives in `main` since PR #37). Run the ui
tests scoped, or rename one class as a separate cleanup.
