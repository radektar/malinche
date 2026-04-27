# Plan: Malinche alpha.18 → beta-1 (closed beta dla testerów)

## Context

**Stan obecny**: Malinche v2.0.0-alpha.18 — apka funkcjonalnie kompletna dla FREE/BYOK tier. Wszystkie krytyczne bugi z alpha.10–alpha.18 naprawione (markdown brace-escape, billing circuit breaker, bootstrap idempotency, staged file fallback, thread safety). Test suite 335 pass. Działa end-to-end: whisper → markdown → Obsidian vault.

**Cel**: wypuścić **closed beta** dla wąskiej grupy testerów (~20-50 osób) z **BYOK only** (każdy tester wkleja własny `ANTHROPIC_API_KEY`). Brak monetyzacji, brak backendu, brak marketingu publicznego.

**Świadome odłożenia**:
- ❌ Apple Developer ID + notaryzacja → przyjdzie po pozytywnej walidacji bety (user nie ma jeszcze konta)
- ❌ License backend, Stripe/LemonSqueezy, PRO tier
- ❌ malinche.app strona, privacy policy hostowana publicznie
- ❌ Sparkle auto-install, telemetry/Sentry, pełna i18n
- ❌ Mac App Store

**Konsekwencja braku notaryzacji**: testerzy muszą zaakceptować UNSIGNED DMG. To OK dla closed beta, **nie OK** dla publicznego release'u. Scope bety = onboarding instructions + workaround dla Gatekeeper.

---

## Zakres pracy (3 fazy)

### Faza P0 — MUST HAVE przed wysłaniem testerom

#### Task P0.1 — Onboarding dla UNSIGNED DMG
**Problem**: Tester ściąga DMG, próbuje otworzyć Malinche.app, dostaje "Apple cannot verify this developer" → bounce. Bez instrukcji = 50% drop-off.

**Plik nowy**: [docs/BETA-ONBOARDING.md](docs/BETA-ONBOARDING.md) — krótki dokument (1 ekran):
- Jak otworzyć UNSIGNED DMG: prawy klik na `Malinche.app` w `/Applications` → **Open** → potwierdzenie. ALBO terminal: `xattr -d com.apple.quarantine /Applications/Malinche.app`
- Jak skonfigurować BYOK: link do `console.anthropic.com`, gdzie kliknąć w wizardzie
- Co zrobić jak coś nie działa: link do GitHub Issues
- Sekcja "Co z PRO?" — patrz [BETA-1-FREE-PRO-STRATEGY.md](BETA-1-FREE-PRO-STRATEGY.md) task PRO.5.

**Verification**: świeża maszyna macOS (lub user nowy), przejść onboarding ze świeżym DMG, zmierzyć ile kroków.

> **Decyzja wykonawcza**: `scripts/install_for_beta.sh` (curl-able installer) — **NIE robimy w beta-1**. Dystrybucja random shell scripta do mieszanej grupy testerów to podwyższone ryzyko UX/security; BETA-ONBOARDING.md wystarczy. Jeśli ≥3 testerów poprosi o CLI installer, dodamy w beta-2.

---

#### Task P0.2 — Update manual test checklist (alpha.8 → alpha.18)
**Problem**: [tests/MANUAL_TEST_CHECKLIST_ALPHA8.md](tests/MANUAL_TEST_CHECKLIST_ALPHA8.md) jest stale (10 wersji za stary). Brak scenariuszy: billing circuit breaker, staged file fallback, markdown brace-escape, NSWindow thread crash, model deprecation.

**Plik nowy**: [tests/MANUAL_TEST_CHECKLIST_BETA1.md](tests/MANUAL_TEST_CHECKLIST_BETA1.md) — kompletny checklist dla bety:
1. **Świeża instalacja** (wizard → folder picker → model download → permissions → AI config → finish)
2. **Wznowienie po przerwaniu** (kill app w trakcie download, restart, sprawdź resume)
3. **Recorder detection** (LS-P1 + dowolny inny vendor + SD card)
4. **Staged files bez recordera** (alpha.17 fallback)
5. **Plik whisper-unreadable** (alpha.16 — sesja-blacklist, raz spróbuj, nie pętla)
6. **Brak kredytów Anthropic** (alpha.14 — circuit breaker, alert raz, fallback markdown)
7. **Deprecated model 404** (alpha.15 — circuit breaker dla 404)
8. **AI summary z `{` lub `}`** (alpha.18 — markdown ma być utworzony, .txt skasowany)
9. **Reset memory** (UI flow — 7d, 30d, custom date)
10. **Settings: zmiana folderu / klucza / modelu Whisper post-setup**
11. **Restart app po crashu — vault_index nie ma zduplikowanych wpisów**

Każdy scenariusz: kroki + expected outcome + log/file checks.

**Plik usunięty**: stary `MANUAL_TEST_CHECKLIST_ALPHA8.md` (po commit nowego).

---

#### Task P0.3 — "Report bug" menu item z prefilled GitHub Issue
**Problem**: testerzy nie wiedzą gdzie zgłosić bug. Email = chaos. Slack/Discord = nadmiar dla 20 osób. GitHub Issues = idealne, ale wymaga klikania URL ręcznie.

**Plik**: [src/menu_app.py](src/menu_app.py) — dodać menu item **"Zgłoś błąd / Report bug"** poniżej "Otwórz logi". On-click:
1. Zbierz diagnostic info: `APP_VERSION`, macOS version (`platform.mac_ver()`), Python version, czy `anthropic` package zaimportowany, **last 30 linii loga** (limit URL ~8000 chars; pełny dump w schowku via P1.4).
2. URL-encode jako body do GitHub Issue: `https://github.com/radektar/transrec/issues/new?template=bug_report.md&body=<encoded>`
3. Otwórz URL przez `subprocess.Popen(["open", url])`.

**Plik nowy**: [.github/ISSUE_TEMPLATE/bug_report.md](.github/ISSUE_TEMPLATE/bug_report.md) — template z polami: opis, kroki repro, oczekiwane vs faktyczne, diagnostic info (auto-prefilled).

**Verification**: kliknij menu item → przeglądarka otwiera nowe issue z wypełnionym diagnostic info, można od razu napisać tylko opis problemu.

---

#### Task P0.4 — Log rotation
**Problem**: `~/Library/Application Support/Malinche/logs/malinche.log` rośnie bez końca (raport audytu — `FileHandler` bez `RotatingFileHandler`). U testerów może urosnąć do 100+ MB w tygodniu.

**Plik**: [src/logger.py](src/logger.py) — zamiana `FileHandler` na `RotatingFileHandler(maxBytes=10*1024*1024, backupCount=3)`. 10 MB × 4 pliki = 40 MB cap.

**Test nowy**: [tests/test_logger.py](tests/test_logger.py) — sprawdź że RotatingFileHandler jest skonfigurowany, mock 11 MB write, expect rotate.

---

#### Task P0.5 — Update check via GitHub Releases
**Problem**: tester instaluje beta-1, my wypuszczamy beta-2 z fixem, **tester nigdy się nie dowie**. Bez auto-install — minimum: notyfikacja w menu bar.

**Plik nowy**: [src/update_checker.py](src/update_checker.py):
- `check_latest_release() -> Optional[ReleaseInfo]`: HTTP GET `https://api.github.com/repos/radektar/transrec/releases/latest`, parse `tag_name`, porównaj z `APP_VERSION` używając `packaging.version.parse()`.
- Wywołanie: raz przy starcie (po `bootstrap.ensure_ready()`) **w bocznym wątku** przez `threading.Timer(0, ...)`, następnie co 24h przez kolejny `threading.Timer`. Cancellable na quit.
- Network failure: log warning + retry za 1h (nie crashuj UI).

**Plik**: [src/menu_app.py](src/menu_app.py):
- Jeśli nowsza wersja → menu item highlight `🆕 Dostępna nowsza wersja: vX.Y.Z` na samej górze.
- Click → `open` URL do GitHub release page (gdzie tester ściąga nowy DMG ręcznie).
- **UI mutacje** (`status_item.title`, dodawanie menu item) — **wyłącznie** przez `_run_on_main_thread()` (callback z bocznego wątku), wzorzec z alpha.13 NSWindow fix.

**Test nowy**: [tests/test_update_checker.py](tests/test_update_checker.py) — mock httpx, sprawdź comparison logic dla `2.0.0-beta.1` vs `2.0.0-beta.2`.

---

#### Task P0.6 — Privacy disclaimer w wizardzie
**Problem**: testerzy mogą się obawiać że Malinche wysyła audio gdzieś. Trzeba **w aplikacji** (nie tylko README) jasno powiedzieć: "Audio przetwarzane lokalnie. Tylko transkrypt (tekst) → Claude API."

**Plik**: [src/setup/wizard.py](src/setup/wizard.py) — w `AI_CONFIG` step, dodać tekst przed input dla API key:
```
🔒 Prywatność:
• Audio jest przetwarzane lokalnie przez Whisper na Twoim Macu.
• Tylko transkrypt (tekst) jest wysyłany do Claude API w celu wygenerowania
  podsumowania i tagów (jeśli skonfigurujesz klucz).
• Bez klucza Claude → markdown ma fallback summary, AI nie jest używane.
• Nigdy nie zbieramy danych telemetrycznych ani nie wysyłamy plików do nas.
```

**Plik**: [src/ui/constants.py](src/ui/constants.py) — dodać do `TEXTS` dict klucz `privacy_notice` z powyższym tekstem.

---

#### Task P0.7 — Bump → 2.0.0-beta.1, CHANGELOG, build & DMG
**Pliki**:
- [setup_app.py](setup_app.py): `APP_VERSION = "2.0.0-beta.1"`
- [src/ui/constants.py](src/ui/constants.py): `APP_VERSION = "2.0.0-beta.1"`
- [CHANGELOG.md](CHANGELOG.md): wpis `## [2.0.0-beta.1]` z bullet pointami P0.1-P0.6.
- Test [tests/test_versions_sync.py](tests/test_versions_sync.py) — sprawdza spójność, musi przejść.
- Run `./scripts/build_app.sh && ./scripts/create_dmg.sh`.
- Output: `dist/Malinche-2.0.0-beta.1-ARM64-UNSIGNED.dmg`.

**Verification**:
1. `pytest tests/ -q` → wszystkie pass.
2. Mount DMG, drag&drop do /Applications.
3. `xattr -d com.apple.quarantine /Applications/Malinche.app` (workaround).
4. Open Malinche → wizard → finish → transkrypcja test.mp3 → markdown w vault.
5. Menu item "Report bug" → otwiera GitHub Issue z wypełnionym diagnostic info.
6. Menu item "Otwórz logi" → log file jest, ma rozsądny rozmiar.

---

### Faza P1 — POWINNO BYĆ (do wysłania testerom, ale nie blocker dla pierwszego DMG)

#### Task P1.1 — GitHub Release page z DMG + checksums
**Plik**: [scripts/build_release.sh](scripts/build_release.sh) — sprawdzić czy generuje SHA-256 dla DMG, dodać upload do GitHub Releases via `gh release create`.

Po: `gh release create v2.0.0-beta.1 dist/Malinche-2.0.0-beta.1-ARM64-UNSIGNED.dmg --title "Beta 1" --notes-file docs/release-notes-beta1.md`.

#### Task P1.2 — README dla testerów
**Plik**: [README.md](README.md) — sekcja "🧪 Closed Beta" na górze: link do BETA-ONBOARDING.md, lista znanych ograniczeń (UNSIGNED DMG, BYOK only), kanał feedback (GitHub Issues).

#### Task P1.3 — Disable PRO/license UI w trakcie bety

**→ Zastąpione przez [BETA-1-FREE-PRO-STRATEGY.md](BETA-1-FREE-PRO-STRATEGY.md)**, taski PRO.1–PRO.5 (`BETA_HIDE_PRO_UI = True` + odblokowanie versioning/retranscribe dla BYOK + beta disclaimer w wizardzie).

**Wykonanie tasków PRO.1–PRO.5 wymagane PRZED P0.7 (bump beta.1)**, żeby DMG od razu miało clean UX.

#### Task P1.4 — Diagnostic info dump w schowku
**Plik**: [src/menu_app.py](src/menu_app.py) — menu item "Skopiuj info diagnostyczne" → wkleja do clipboard ten sam payload co P0.3 (wersja, OS, log tail), bez otwierania przeglądarki. Dla testerów którzy chcą wkleić info do innego kanału.

---

### Faza P2 — NICE TO HAVE (dopiero po pierwszych testach)

- **Sentry free tier** (5k events/mo) — jeśli okaże się że bug-reports z P0.3 są niewystarczające.
- **User-selectable LLM model post-setup** — obecnie hardcoded `claude-haiku-4-5-20251001`. Settings dropdown, jeśli testerzy proszą.
- **Discord / Slack workspace** dla testerów — jeśli > 30 osób i feedback robi się chaotyczny w GitHub Issues.
- **`OllamaSummarizer`** — stub w [src/summarizer.py:54](src/summarizer.py). Dokończyć dla testerów którzy nie mają budżetu na Anthropic.

---

## Krytyczne pliki

| Faza | Plik | Zmiana |
|------|------|--------|
| P0.1 | [docs/BETA-ONBOARDING.md](docs/BETA-ONBOARDING.md) | NEW |
| P0.2 | [tests/MANUAL_TEST_CHECKLIST_BETA1.md](tests/MANUAL_TEST_CHECKLIST_BETA1.md) | NEW |
| P0.2 | [tests/MANUAL_TEST_CHECKLIST_ALPHA8.md](tests/MANUAL_TEST_CHECKLIST_ALPHA8.md) | DELETE |
| P0.3 | [src/menu_app.py](src/menu_app.py) | menu item + collect diagnostic |
| P0.3 | [.github/ISSUE_TEMPLATE/bug_report.md](.github/ISSUE_TEMPLATE/bug_report.md) | NEW |
| P0.4 | [src/logger.py](src/logger.py) | RotatingFileHandler |
| P0.4 | [tests/test_logger.py](tests/test_logger.py) | NEW |
| P0.5 | [src/update_checker.py](src/update_checker.py) | NEW |
| P0.5 | [src/menu_app.py](src/menu_app.py) | update notification UI |
| P0.5 | [tests/test_update_checker.py](tests/test_update_checker.py) | NEW |
| P0.6 | [src/setup/wizard.py](src/setup/wizard.py) | privacy notice w AI_CONFIG |
| P0.6 | [src/ui/constants.py](src/ui/constants.py) | TEXTS["privacy_notice"] |
| P0.7 | [setup_app.py](setup_app.py), [src/ui/constants.py](src/ui/constants.py), [CHANGELOG.md](CHANGELOG.md) | bump beta.1 |
| P1.1 | [scripts/build_release.sh](scripts/build_release.sh) | gh release create |
| P1.2 | [README.md](README.md) | sekcja "Closed Beta" (publiczna w main) |
| P1.3 | — | zastąpione przez [BETA-1-FREE-PRO-STRATEGY.md](BETA-1-FREE-PRO-STRATEGY.md) PRO.1–PRO.5 |
| P1.4 | [src/menu_app.py](src/menu_app.py) | "Skopiuj info diagnostyczne" (pełny dump w schowku) |

---

## End-to-end weryfikacja przed wysłaniem testerom

1. ✅ `pytest tests/ -q` → 335+ pass (335 obecne + nowe testy).
2. ✅ Świeża macOS VM lub czysty profil: ściągnięcie `Malinche-2.0.0-beta.1-ARM64-UNSIGNED.dmg` z GitHub Releases, otwarcie wg [BETA-ONBOARDING.md](docs/BETA-ONBOARDING.md), wizard kompletny.
3. ✅ Test 4 plików audio: jeden zwykły MP3, jeden niczytelny (whisper fail), jeden krótki (<10s), jeden z polskimi znakami diakrytycznymi w treści. Wszystkie obsłużone bez infinite loop, markdown utworzony lub failed-fingerprint dodany.
4. ✅ Symulacja braku kredytów (zły API key) → alert raz, fallback markdown dla kolejnych plików, brak spamu HTTP w logu.
5. ✅ Menu "Report bug" → otwiera GitHub Issue z wypełnionym diagnostic info zawierającym `APP_VERSION=2.0.0-beta.1`.
6. ✅ Menu "Otwórz logi" → otwiera plik. Po wymuszeniu 11 MB writes (jakimś debug script), plik jest rotowany — istnieje `.log.1`.
7. ✅ Update checker: zmień APP_VERSION na lokalny `2.0.0-beta.0` przed buildem, zbuduj, zrestartuj — menu pokazuje banner "Dostępna nowsza wersja".

---

## Kolejność wykonania (dla agenta wykonującego plan)

1. P0.4 (log rotation) — najprostszy, izolowany. Warm-up.
2. P0.6 (privacy notice) — zmiana stringów + dialog tekst. Mała.
3. **PRO.1–PRO.5** ([BETA-1-FREE-PRO-STRATEGY.md](BETA-1-FREE-PRO-STRATEGY.md)) — odblokowanie BYOK + ukrycie PRO UI. Średnia.
4. P0.5 (update checker) — nowy moduł + test + integracja w menu_app. Średnia.
5. P0.3 (report bug) — nowy menu item + GitHub Issue template + diagnostic helper. Średnia.
6. P0.1 + P0.2 (dokumenty Markdown) — pisanie tekstu, brak kodu. Razem szybko.
7. P0.7 (bump + build + DMG) — finalizacja. Tylko po wszystkich powyższych.
8. P1.* — po pierwszym DMG, przed wysłaniem do testerów.

**Każde P0.X / PRO.X powinno być osobnym commitem** w stylu repo (one-liner + `[tests: pass]`), żeby `git log` był czytelny. Po P0.7 → `git tag v2.0.0-beta.1` + `gh release create`.

---

## Decyzje wykonawcze (zatwierdzone)

Wszystkie kierunki dla bety-1 są ustalone. Jeśli okoliczności się zmienią, każda z tych decyzji może być rewidowana w beta-2:

1. **Update checker** → `threading.Timer` w bocznym wątku; UI mutacje (`status_item.title`, dodawanie menu item) przez `_run_on_main_thread()` (wzorzec z alpha.13). Jeden HTTP call na 24h. Wykorzystane w P0.5.
2. **Diagnostic info do GitHub Issue** → tylko **30 linii** logu (URL limit ~8000 chars). Pełny dump dostępny w schowku przez P1.4. Wykorzystane w P0.3.
3. **`scripts/install_for_beta.sh`** → **NIE robimy w beta-1**. BETA-ONBOARDING.md wystarczy. Wykorzystane w P0.1.
4. **README sekcja "Closed Beta"** → **publiczna w main**. Repo jest public, testerzy lądują w README, mają jasny stan ("to jest beta, nie production"). Wykorzystane w P1.2.
5. **Repo URL we wszystkich miejscach** → `https://github.com/radektar/transrec` (NIE `malinche` — nazwa katalogu różni się od repo). Wykorzystane w P0.3 i P0.5.
6. **PRO/license UI w becie** → ukryte, BYOK odblokowuje wszystkie obecne flagi (versioning, retranscribe). Pełen scope w [BETA-1-FREE-PRO-STRATEGY.md](BETA-1-FREE-PRO-STRATEGY.md), zastępuje P1.3.
