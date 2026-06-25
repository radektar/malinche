# Insights Dashboard — build plan (Direction B)

Implementing the chosen design (`design-system/pages/dashboard-screens.html`) as a
native AppKit window. Branch: `feat/insights-dashboard`. Loop-driven; check items
off as they land. Pattern: **pure model + geometry (testable) → thin AppKit view**,
mirroring `status_panel.py` / `status_panel_model.py`.

Spec source of truth: `design-system/pages/dashboard-screens.html` + `insights-engine.js`.
v1 scope = czytnik + szyna + sygnał. Activity tab + skeleton are in-design but lower priority.

## Checklist

- [x] **Pure data model** — `src/ui/insight_model.py`: `InsightConnection` (type, label,
      layout, snippet, notes, rationale, directions, tcolor) + `InsightDeck`
      (queue, active index, navigate, keep/dismiss, unseen count). AppKit-free. + tests. ✅ 12 tests
- [x] **Constellation geometry** — `src/ui/constellation_geometry.py`: pure node/arc/bloom
      coordinates per layout (contradiction/thread/triad), scaled. Port of `insights-engine.js`
      `LAY` + arc control points. + tests. ✅ 8 tests
- [x] **Constellation view** — `NSView.drawRect_` (Core Graphics): nodes (radial glow),
      arcs (quadratic bézier + glow), golden bloom. ✅ `constellation_view.py`, 8 ui tests,
      offscreen render verified vs mock. Entrance animation deferred to the window pass.
- [x] **Dashboard window shell** — `src/ui/dashboard_window.py`: `NSWindow` + native dark
      titlebar (transparent, full-size content), dark radial bg, grid (rail | reader),
      resizable w/ min-size. AppKit-optional guard. ✅ rendered & verified vs mock.
- [x] **Rail (connection list)** — dot + label + 2-line snippet; active = gold rail; kept =
      dimmed + ✓; "Ostatnie transkrypty" foot. ✅ (manual stacked rows; NSTableView only if N grows.)
- [x] **Reader** — constellation stage + type + rationale + note chips + directions +
      Zachowaj/Odrzuć wired to the deck (select/keep/dismiss re-render). ✅
- [x] **States** — empty ("Cisza w korpusie") ✅. Keep-flash ✅. Transcribing skeleton
      ("● Transkrybuję…" badge + grey placeholders when open + working + no insight yet) ✅;
      driven by `setTranscribing_` from `menu_app._update_icon`. All verified.
- [x] **Dark surface depth** — backdrop drawRect subview fills deep obsidian (#100E15) + soft top
      halo; pixel-verified (18,17,23). ✅ (Full-window offscreen capture greys it — capture artifact,
      not the real render; the constellation/text capture fine.)
- [ ] **Activity tab** — recent transcripts + connection counts (reuse `PanelModel`). **[v1.1 —
      deferred on purpose:** standing v1 rec was reader + rail + signal; the tab is a second surface
      that doesn't change validation. Build after the digest-window bet is tested.]
- [x] **Menu integration** — native `NSMenu` is the click surface again (popover hijack
      retired: `_install_status_panel` removed, `_status_panel=None`); `Insights…` item opens
      the window; dashboard controller built in `__init__`. ✅ py_compile + flake8-neutral.
      `✦ Nowy insight (N)` count badge waits on the pipeline (needs the unseen count).
- [x] **Signal** — notification carries the *thesis* ✅; menu count badge `✦ Insights (N)` ✅;
      gold-dot menu-bar icon when an unseen insight waits ✅ (`render_symbol_png(dot=True)` —
      non-template grey glyph + gold dot, readable on light/dark; visually verified). Driven by
      `_unseen_insights`, picked up on the status tick. (Notification-click-to-open: nice-to-have.)
- [x] **Pipeline** — `digest_writer` persists a structured `{vault}/.malinche/insights-latest.json`
      (type/notes/rationale/directions) on each digest; `insight_pipeline.py` loads it into an
      `InsightDeck`; the window defaults to `latest_deck() or sample_deck()`. ✅ 7 tests.
      Sidecar write is best-effort (never disturbs the digest).
- [ ] **Token reconciliation (Faza 0)** — *not a bug:* the dashboard's dark-surface jade `#46B17E`
      is intentionally brighter than the light-UI `theme.jade()` `#057857` (dark needs brighter
      tints). Open *cleanup:* centralise the dark-surface insight tints into `theme.py`. Chrome:
      shipped with the **native dark titlebar** (cheaper, consistent) per the v1 rec.
- [x] **Wire into `menu_app.py`** ✅ + new suite green (47 tests) + flake8 clean on all changed
      files + `menu_app` py_compile clean (can't import on the 3.9 venv — pre-existing `match` in
      `volume_utils`; the app runs 3.12+).

---

## Status — v1 complete (2026-06-26)

The Insights "Konstelacja" window is implemented natively per the design and wired into the app.
**10 commits** on `feat/insights-dashboard`; **47 tests**; flake8 clean. Done: constellation engine
+ Core Graphics view (3 types), window (chrome / rail / reader / empty / skeleton / keep-flash),
native-menu entry (popover-as-click retired), real-digest pipeline, signal (thesis notification +
`✦ Insights (N)` badge + gold-dot icon), deep-obsidian surface.

**Open decisions (user's call, not autonomous):** (1) Activity tab — build now or keep deferred?
(2) push / open PR — the branch is **stacked on `fix/llm-key-hot-reload-401`** (its 2 commits are
included; `rebase --onto main` once that merges) and there is **uncommitted WIP** left untouched.
(3) token-centralisation cleanup.
