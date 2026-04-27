# Plan suplement: strategia FREE / PRO dla beta-1

> Suplement do planu [`BETA-1-PLAN.md`](BETA-1-PLAN.md) ("alpha.18 → beta-1").
> Pokrywa: **status funkcjonalności FREE/PRO, kierunek strategiczny, konkretny scope dla bety, roadmap po becie.**
>
> **Status decyzji**: **Opcja A (PRO = hosted convenience) — ZATWIERDZONA dla v1.0**. Wszystkie taski PRO.1–PRO.5 poniżej są wykonalne bez dalszych pytań. Sekcja "Alternatywy rozważane" zachowana jako appendix (kontekst decyzji).

---

## Context

Plan beta-1 zakłada „BYOK only, no PRO tier" i jako P1.3 zostawia tylko jednolinijkowy `BETA_HIDE_PRO_UI = True`. Ale to nie wystarczy — bez świadomej decyzji co PRO **ma być** w v1.0, każda zmiana w UI/kodzie bety podnosi koszt późniejszej migracji albo wprowadza testerów w błąd.

Audyt kodu (alpha.18) pokazuje, że **stan FREE/PRO jest bardziej zaawansowany niż "stub"**, ale niespójny:

### Co już w kodzie istnieje

| Komponent | Lokalizacja | Stan |
|---|---|---|
| `FeatureTier` enum (FREE / PRO / PRO_ORG) | [src/config/features.py:5](src/config/features.py#L5) | gotowe |
| `FeatureFlags` per-tier | [src/config/features.py:14](src/config/features.py#L14) | gotowe |
| `LicenseManager._verify_license()` | [src/config/license.py:79](src/config/license.py#L79) | **stub — zawsze zwraca FREE** |
| `activate_license()` | [src/config/license.py:38](src/config/license.py#L38) | **stub — zwraca `(False, "Aktywacja licencji nie jest jeszcze dostępna w wersji FREE")`** |
| Cache `license.json` / `license_cache.json` | [src/config/license.py:117](src/config/license.py#L117) | działa, ale nieużywane (brak backendu) |
| Backend URL `https://api.transrec.app/v1/license` | [src/config/license.py:20](src/config/license.py#L20) | **NIE ISTNIEJE** (brak hostowanego API) |

### Co JEST gated za PRO w aktualnym kodzie

| Funkcjonalność | Lokalizacja | Co robi gating |
|---|---|---|
| Wersjonowanie markdown (v2/v3) | [src/transcriber.py:1193](src/transcriber.py#L1193) | `can_version = tier != FREE`. FREE → `version=1` zawsze, brak rewrite. |
| Retranskrypcja w menu | [src/menu_app.py:505-515](src/menu_app.py#L505-L515) | FREE → label "Retranskrypcja (PRO)", item zablokowany bez callbacku. |
| Status label w menu bar | [src/menu_app.py:382-387](src/menu_app.py#L382) | FREE → "Aktywuj PRO..." vs PRO → "💎 Malinche PRO". |
| Pro activation dialog | [src/ui/pro_activation.py](src/ui/pro_activation.py) | "Kup PRO" → `https://transrec.app/pro` (dead link), "Mam już klucz" → activate stub. |

### Co JEST w `FeatureFlags` PRO ale **nie ma implementacji**

- `ai_summaries`, `ai_smart_tags`, `ai_naming` — formalnie PRO-only, ale **BYOK path je odblokowuje** ([src/summarizer.py:384-399](src/summarizer.py#L384-L399), [src/tagger.py:211-228](src/tagger.py#L211-L228)). Czyli każdy BYOK user de facto ma "PRO summary/tags".
- `speaker_diarization` (PRO) — **brak kodu** poza wpisem we flagach.
- `cloud_sync`, `shared_speaker_db`, `domain_lexicon`, `knowledge_base` (PRO_ORG) — **brak kodu**.
- `OllamaSummarizer` ([src/summarizer.py:425](src/summarizer.py#L425)) — pełen placeholder.

### Wniosek z audytu

Obecny "PRO" w kodzie to **mieszanka trzech rzeczy**:
1. Realne, działające flagi (versioning, retranscribe).
2. Flagi które BYOK i tak omija (AI summary/tags) → de facto FREE+BYOK = "PRO lite".
3. Aspiracje (diarization, cloud sync, knowledge base) — same nazwy.

Wysyłanie testerom apki gdzie widzą "Aktywuj PRO..." które prowadzi do dead linku i komunikatu "nie jest jeszcze dostępna" — to niepotrzebny śmieć w UX. Sam flag `BETA_HIDE_PRO_UI = True` nie wystarczy — trzeba też odpowiedzieć co PRO ma być w v1.0, żeby decyzje wykonawcze (czy odblokować versioning dla BYOK, jaki tekst dać testerom) były spójne z tym kierunkiem.

---

## Decyzja strategiczna: Opcja A — PRO = hosted convenience

**Kierunek dla v1.0**: BYOK pozostaje *pełnoprawnym* trybem ze wszystkimi feature'ami. PRO = wygoda — Malinche hostuje API key (proxy do Anthropic / własny model), user nie zakłada konta na console.anthropic.com, płaci jednolitą subskrypcję ($X/mc).

**Konsekwencje dla bety-1** (wszystkie wcielone w taski PRO.1–PRO.5):
- ✅ Markdown versioning dla BYOK **odblokowany** (PRO.1) — to nie jest "premium", to jest poprawność techniczna.
- ✅ Retranscribe menu **odblokowane** dla BYOK (PRO.1).
- ✅ Całe license UI **ukryte** w becie (PRO.2). Bez waitlistu, bez "coming soon" buttonów — w beta-1 pricing nie jest jeszcze ustalony, więc waitlist bez konkretnej oferty = niska konwersja + niska wartość.
- ✅ Privacy notice w wizardzie wzmocniony o disclaimer beta (PRO.3): "Beta = BYOK only. Po becie planujemy hostowany tier dla wygody, ale BYOK pozostanie w pełni działający."
- ✅ Komunikacja w README + onboarding doc (PRO.5): "PRO planowany w v1.0, hostowane API key, nie blokada feature'ów".

**Dlaczego A, nie B/C** (dla pełnego porównania patrz appendix poniżej):
- B (feature gate) wymaga 3-6 miesięcy kodu (diarization, domain lexicon, KB) zanim cokolwiek pójdzie do bety.
- C (PRO_ORG only) wymaga cloud sync + SSO + admin (~6+ mies). Może koegzystować z A w przyszłości — niezależne od decyzji indywidualnej.
- A jest **najtańsza w odwrocie** — jeśli po becie wrócimy do feature gate, "odebranie" odblokowanego versioning testerom bety = OK (są beta testerzy, podpisani na ten kontrakt).

---

## Konkretny scope dla beta-1 (zastępuje P1.3 z głównego planu)

### Task PRO.1 — Odblokuj wszystkie obecne flagi PRO dla BYOK

Dla każdego miejsca które dziś sprawdza `tier != FREE`, dodaj alternatywny warunek `BYOK_CLAUDE` (BYOK ma własny klucz Anthropic — czyli efektywnie ma AI). Jeśli BYOK skonfigurowany → traktuj jak PRO.

**Plik**: [src/transcriber.py:1193](src/transcriber.py#L1193)
```python
# było:
can_version = license_manager.get_current_tier() != FeatureTier.FREE
# będzie:
can_version = (
    license_manager.get_current_tier() != FeatureTier.FREE
    or _has_byok_configured()
)
```
Helper `is_byok_configured()` (sprawdza `config.LLM_PROVIDER == "claude" and bool(config.LLM_API_KEY)`) **wyekstrahować do [src/config/__init__.py](src/config/__init__.py)** jako single source of truth — identyczny check JEST już zduplikowany w [src/summarizer.py:386](src/summarizer.py#L386) i [src/tagger.py:215](src/tagger.py#L215). Po extracji obie te lokalizacje + nowy call w [src/transcriber.py:1193](src/transcriber.py#L1193) i [src/menu_app.py:505](src/menu_app.py#L505) używają wspólnego helpera.

**Plik**: [src/menu_app.py:505-515](src/menu_app.py#L505) — `_refresh_retranscribe_menu`. Ten sam pattern: jeśli BYOK lub PRO → odblokuj item. Inaczej (czysty FREE bez BYOK) → label "Retranskrypcja (wymaga klucza Claude)" (nie "(PRO)").

**Test nowy**: [tests/test_transcriber.py](tests/test_transcriber.py) — `test_versioning_enabled_with_byok_on_free_tier` (mock `LLM_API_KEY = "sk-..."`, tier FREE → `can_version == True`).

### Task PRO.2 — Ukryj PRO activation UI w becie

Feature flag w [src/config/config.py](src/config/config.py): `BETA_HIDE_PRO_UI: bool = True` (default w becie).

**Plik**: [src/menu_app.py:111-116](src/menu_app.py#L111) — owinięte `if not config.BETA_HIDE_PRO_UI: ... self.menu.add(self.pro_item)`.

**Plik**: [src/menu_app.py:382-387](src/menu_app.py#L382) — status label nie wyświetla "Aktywuj PRO..." / "💎 Malinche PRO". Po prostu pomija ten branch (pokazuje normalny status: idle / transcribing / itd.).

**Plik**: [src/ui/pro_activation.py](src/ui/pro_activation.py) — **nie usuwać**. Zostawić moduł, po prostu nie wywoływany z UI. Wraca w v1.0 z prawdziwym backendem (lub zostaje do skasowania jeśli wybierzemy opcję B/C).

**Test nowy**: [tests/test_menu_app_pro_visibility.py](tests/test_menu_app_pro_visibility.py) (nowy plik — istniejące `tests/test_menu_app_download.py` ma inny scope) — `test_pro_menu_hidden_when_beta_flag_set` (`BETA_HIDE_PRO_UI=True` → menu nie ma "Aktywuj PRO") i `test_pro_menu_visible_when_flag_disabled` (flag False → menu ma item — dla v1.0).

### Task PRO.3 — Privacy notice + tier disclaimer w wizardzie

Rozszerzyć tekst z P0.6 oryginalnego planu:

```
🔒 Prywatność:
• Audio przetwarzane lokalnie przez Whisper.
• Tylko transkrypt → Claude API (jeśli skonfigurowano klucz).

📦 Wersja beta:
• To jest closed beta. Funkcje płatne (PRO) zostały ukryte.
• Wszystkie funkcje AI (podsumowania, tagi, wersjonowanie) działają
  z Twoim własnym kluczem Anthropic (BYOK).
• Po becie planujemy hostowany tier — ale BYOK pozostanie w pełni działający.
```

**Plik**: [src/setup/wizard.py](src/setup/wizard.py) — krok `AI_CONFIG`, dodać przed input dla API key.
**Plik**: [src/ui/constants.py](src/ui/constants.py) — `TEXTS["beta_disclaimer"]`.

### Task PRO.4 — `license_manager` runtime safety w becie

Pozostawiamy [src/config/license.py](src/config/license.py) bez zmian funkcjonalnych. `_verify_license()` zawsze zwraca FREE — to nadal jest **prawda** z perspektywy systemu (brak prawdziwego license backendu). Nie usuwamy modułu, bo:
- Wraca w v1.0 z prawdziwym backendem.
- Tier-check w innych miejscach kodu (transcriber.py:1193) zostaje, ale teraz jest "miękki" (BYOK go omija — patrz PRO.1).

**Brak zmian w pliku.** Tylko nota w komentarzu na górze: `# In beta-1, license verification is intentionally a no-op. BYOK path overrides feature gates. See plan: docs/BETA-1-PLAN.md`.

### Task PRO.5 — Komunikacja w README + onboarding doc

**Plik**: [docs/BETA-ONBOARDING.md](docs/BETA-ONBOARDING.md) (nowy z P0.1) — sekcja "Co z PRO?":
> Beta jest BYOK only — używasz własnego klucza Anthropic. Wszystkie funkcje AI (podsumowania, tagi, wersjonowanie markdown) działają. Płatny tier („Malinche PRO") planowany w v1.0 — będzie to wygoda hostowanego API, nie blokada feature'ów. Twój feedback z bety pomoże ustalić cenę i scope.

**Plik**: [README.md](README.md) (P1.2) — sekcja "🧪 Closed Beta": jednolinijkowy disclaimer linkujący do BETA-ONBOARDING.md.

---

## Status funkcjonalności (snapshot dla bety)

| Feature | Stan w kodzie | W becie dla BYOK |
|---|---|---|
| Whisper transkrypcja | ✅ działa | ✅ |
| Markdown export | ✅ działa | ✅ |
| AI summary (Claude) | ✅ działa via BYOK | ✅ |
| AI smart tags (Claude) | ✅ działa via BYOK | ✅ |
| AI naming (filename z tytułu) | ✅ działa via BYOK | ✅ |
| Markdown versioning (v2/v3) | ⚠️ FREE-locked, kod działa | ✅ **odblokowane (PRO.1)** |
| Retranscribe menu | ⚠️ FREE-locked, kod działa | ✅ **odblokowane (PRO.1)** |
| Speaker diarization | ❌ tylko enum, brak kodu | ❌ niedostępne |
| Cloud sync | ❌ tylko enum | ❌ niedostępne |
| Shared speaker DB | ❌ tylko enum | ❌ niedostępne |
| Domain lexicon | ❌ tylko enum | ❌ niedostępne |
| Knowledge base | ❌ tylko enum, plan w docs/future/ | ❌ niedostępne |
| Ollama summarizer | ❌ placeholder | ❌ niedostępne |
| License activation UI | ⚠️ stub UI + dead backend | 🚫 **ukryte (PRO.2)** |

---

## Roadmap po becie (informacyjnie, nie scope dla v2.0.0-beta.1)

1. **beta-1 → beta-2** (4-6 tyg) — fixy z feedbacku testerów, stabilność. Brak nowych feature'ów PRO.
2. **beta-2 survey** — krótki survey w menu "Daj feedback" walidujący pricing dla Opcji A (multiple choice: $5/mc / $10/mc / $20/mc / nie zapłacę). Survey **NIE wchodzi do beta-1** — beta-1 = stabilność, survey = osobny cykl.
3. **v1.0 implementation** — Opcja A (decyzja zatwierdzona):
   - Backend proxy do Anthropic API (FastAPI lub Cloudflare Worker).
   - Stripe checkout + webhook → wystawia license key.
   - `LicenseManager.activate_license()` weryfikuje key przeciw backendowi (kod już istnieje w stub-formie).
   - Estymacja: ~2-3 tyg pracy + setup infrastruktury.
4. **v1.1+** (opcjonalnie) — PRO_ORG (Opcja C) jako oddzielny tier, koegzystujący z PRO indywidualnym.

---

## Krytyczne pliki (delta vs główny plan)

| Task | Plik | Zmiana |
|---|---|---|
| PRO.1 | [src/config/__init__.py](src/config/__init__.py) | nowy helper `is_byok_configured()` (extract z summarizer/tagger) |
| PRO.1 | [src/transcriber.py:1193](src/transcriber.py#L1193) | `can_version` uwzględnia BYOK |
| PRO.1 | [src/menu_app.py:505-515](src/menu_app.py#L505) | retranscribe odblokowane dla BYOK |
| PRO.1 | [tests/test_transcriber.py](tests/test_transcriber.py) | nowy test versioning+BYOK |
| PRO.2 | [src/config/config.py](src/config/config.py) | flag `BETA_HIDE_PRO_UI = True` |
| PRO.2 | [src/menu_app.py:111-116, 382-387](src/menu_app.py#L111) | conditional render PRO UI |
| PRO.3 | [src/setup/wizard.py](src/setup/wizard.py) | extended privacy + beta disclaimer w AI_CONFIG |
| PRO.3 | [src/ui/constants.py](src/ui/constants.py) | `TEXTS["beta_disclaimer"]` |
| PRO.4 | [src/config/license.py](src/config/license.py) | tylko komentarz na górze (no-op w becie) |
| PRO.5 | [docs/BETA-ONBOARDING.md](docs/BETA-ONBOARDING.md) | sekcja "Co z PRO?" |

---

## Verification dla PRO.1-PRO.5

1. ✅ `pytest tests/ -q` — 335+ pass + 2 nowe.
2. ✅ Świeża instalacja DMG → wizard pokazuje beta disclaimer w AI_CONFIG.
3. ✅ Po finish wizard, BYOK skonfigurowane → menu **nie ma** "Aktywuj PRO...".
4. ✅ Status label w menu bar → normalny status (idle/transcribing), bez "Aktywuj PRO".
5. ✅ Retranscribe menu — items dostępne (nie "(PRO)").
6. ✅ Re-transcribe pliku → markdown ma `version: 2` w frontmatter (versioning działa).
7. ✅ Bez BYOK (puste pole API key) → AI features fallback (markdown ma fallback summary, brak tagów). To samo zachowanie co dziś.
8. ✅ `grep -r "Aktywuj PRO\|💎 Malinche PRO" dist/Malinche.app/Contents/Resources/lib/python3.12/src/` → brak hits (poza wyłączonym kodem za flagą).

---

## Decyzje wykonawcze (zatwierdzone)

Wszystkie poniższe są ustalone i wcielone w taski PRO.1–PRO.5 lub roadmap. Bez dalszych pytań przed implementacją:

1. **Kierunek strategiczny** → **Opcja A** (PRO = hosted convenience). BYOK = pełen produkt; PRO w v1.0 = wygoda hostowanego API.
2. **Waitlist email signup w becie** → **NIE w beta-1**. Bez konkretnego pricingu = niska wartość. Wraca w beta-2 razem z survey.
3. **Survey "jakbyś chciał zapłacić"** → **beta-2**. Beta-1 = walidacja stabilności, nie pricingu. Pytanie z konkretnymi cenami ($5/$10/$20/nie zapłacę).
4. **`OllamaSummarizer`** → **P2 (nice-to-have, post-beta-1)**. Kod stub w [src/summarizer.py:425](src/summarizer.py#L425) zostaje. Dokończenie = oddzielny task po becie, alternatywa do PRO dla użytkowników bez budżetu na Anthropic.
5. **Kolejność implementacji** → PRO.1 → PRO.2 → PRO.3 → PRO.4 → PRO.5, **przed P0.7** z głównego planu (bump beta.1).
6. **Format zatwierdzonych testów** → standard repo: `pytest tests/ -q` musi pass; każdy task = osobny commit z `[tests: pass]`.

---

## Alternatywy rozważane (appendix — kontekst decyzji)

### Opcja B: PRO = feature gate (advanced features) — ODRZUCONA dla v1.0

**Definicja**: FREE+BYOK ma `summary` + `tags`. PRO odblokowuje `versioning`, `diarization`, `domain lexicon`, `knowledge base`.

**Dlaczego odrzucona**: wymaga 3-6 miesięcy kodu (`diarization`, `domain_lexicon`, `knowledge_base` to obecnie tylko enum, brak implementacji) **zanim** cokolwiek pójdzie do bety. Beta to *teraz*. Dodatkowo: BYOK użytkownicy mogą porzucić Malinche na rzecz konkurencji która daje wszystko w BYOK.

### Opcja C: PRO_ORG = team/enterprise only — ODŁOŻONA do v1.1+

**Definicja**: indywidualne użycie zostaje na zawsze BYOK. PRO_ORG = team features (cloud sync, shared speaker DB, admin panel, SSO).

**Dlaczego odłożona, nie odrzucona**: jasny segment B2B z wyższym ARPU, **niezależny** od decyzji indywidualnej (może koegzystować z A). Wymaga zaimplementowania PRO_ORG features (~6+ mies). Nie blokuje v1.0 — wraca jako osobny tier w v1.1+.

---

## Integracja z głównym planem

- Ten suplement **zastępuje P1.3** w [`BETA-1-PLAN.md`](BETA-1-PLAN.md).
- Sekcja P0.6 (privacy disclaimer) **rozszerza się** o tekst beta-disclaimer (PRO.3).
- Sekcja P1.2 (README) zyskuje subsekcję "Co z PRO?" (PRO.5).
- Reszta P0.1-P0.7 + P1.1, P1.4, P2 **bez zmian**.
- Kolejność wykonania: PRO.1-PRO.5 wykonać **przed P0.7** (bump beta.1), żeby DMG od razu miało clean UX bez PRO śmietnika.
- `BETA-1-PLAN.md` ma sekcję "Decyzje wykonawcze (zatwierdzone)" z 6 odpowiadającymi decyzjami dla głównego scope (update checker thread model, diagnostic line limit, install_for_beta.sh skip, README publiczny, repo URL, PRO UI strategia).
