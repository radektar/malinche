# Instrukcje testów manualnych - Faza 3

## Status środowiska

✅ **Testy automatyczne:** 20/20 przechodzi  
✅ **Branch:** `feature/faza-3-first-run-wizard`  
✅ **macOS:** 26.1 (Sequoia)  
✅ **Python:** 3.12.12  
✅ **rumps:** zainstalowane  
✅ **Zależności:** zainstalowane (whisper-cli, ffmpeg, model)  
❌ **Config:** nie istnieje (gotowe do testów)

---

## Testy wymagające interakcji GUI

Następujące testy wymagają Twojej pomocy przy klikaniu w okna dialogowe:

### TEST M3.1-M3.2: Pierwsze uruchomienie i powitanie
**Co zrobić:**
1. Uruchom aplikację: `python -m src.menu_app`
2. **OBSERWUJ:** Czy wizard się uruchomił automatycznie?
3. **SPRAWDŹ:** Czy widzisz ekran powitalny z tytułem "🎙️ Witaj w Transrec!"?
4. **KLIKNIJ:** "Rozpocznij →"
5. **POWIEDZ:** Co się stało po kliknięciu?

### TEST M3.3: Pobieranie - skip
**Co zrobić:**
1. Przejdź przez krok powitania (kliknij "Rozpocznij →")
2. **OBSERWUJ:** Czy krok pobierania został pominięty automatycznie?
3. **POWIEDZ:** Czy pojawił się dialog pobierania, czy przeszło od razu do FDA?

### TEST M3.4: Pobieranie - pełne (OPCJONALNE)
**UWAGA:** Ten test wymaga usunięcia zależności (~500MB pobierania)
**Jeśli chcesz przetestować:**
```bash
rm -rf ~/Library/Application\ Support/Transrec/bin/
rm -rf ~/Library/Application\ Support/Transrec/models/
```
Następnie uruchom aplikację i przejdź przez wizard.

### TEST M3.5-M3.6: FDA
**Co zrobić:**
1. Przejdź przez kroki: powitanie, pobieranie
2. **OBSERWUJ:** Czy pojawił się dialog FDA?
3. **SPRAWDŹ:** Czy masz FDA nadane w System Preferences?
   - Jeśli TAK: czy krok został pominięty?
   - Jeśli NIE: kliknij "Otwórz Ustawienia" i sprawdź czy się otworzyło

### TEST M3.7-M3.8: Źródła nagrań
**Co zrobić:**
1. Przejdź do kroku źródeł nagrań
2. **TEST M3.7:** Kliknij "Automatycznie"
3. **POWIEDZ:** Czy przeszło dalej?
4. **TEST M3.8:** Wróć i kliknij "Określone dyski"
5. **WPISZ:** "LS-P1, ZOOM-H6"
6. **KLIKNIJ:** "OK"
7. **POWIEDZ:** Czy przeszło dalej?

### TEST M3.9: Folder docelowy
**Co zrobić:**
1. Przejdź do kroku folderu docelowego
2. **SPRAWDŹ:** Czy widzisz domyślną ścieżkę?
3. **ZMIEŃ:** Na `/tmp/test_transcriptions`
4. **KLIKNIJ:** "OK"
5. **POWIEDZ:** Czy przeszło dalej?

### TEST M3.10: Język
**Co zrobić:**
1. Przejdź do kroku języka
2. **SPRAWDŹ:** Czy widzisz domyślny język "pl"?
3. **ZMIEŃ:** Na "en"
4. **KLIKNIJ:** "OK"
5. **POWIEDZ:** Czy przeszło dalej?

### TEST M3.11-M3.12: AI
**Co zrobić:**
1. Przejdź do kroku AI
2. **TEST M3.11:** Kliknij "Pomiń"
3. **POWIEDZ:** Czy przeszło dalej?
4. **TEST M3.12:** Wróć i kliknij "Skonfiguruj API"
5. **WPISZ:** "sk-test-123"
6. **KLIKNIJ:** "Zapisz"
7. **POWIEDZ:** Czy przeszło dalej?

### TEST M3.13: Zakończenie
**Co zrobić:**
1. Przejdź przez wszystkie kroki
2. **OBSERWUJ:** Czy pojawił się ekran zakończenia?
3. **SPRAWDŹ:** Czy daemon się uruchomił (status w menu bar)?
4. **POWIEDZ:** Co widzisz w menu bar?

### TEST M3.14: Anulowanie
**Co zrobić:**
1. Usuń config: `rm -f ~/Library/Application\ Support/Transrec/config.json`
2. Uruchom aplikację ponownie
3. Przejdź przez kilka kroków
4. **ANULUJ:** Zamknij aplikację lub kliknij "Anuluj" (jeśli dostępne)
5. **SPRAWDŹ:** Czy config.json nie ma `setup_completed: true`?

### TEST M3.15: Back navigation
**Co zrobić:**
1. Uruchom wizard od nowa
2. Przejdź do kroku 5 (Folder docelowy)
3. **KLIKNIJ:** "Wstecz"
4. **POWIEDZ:** Czy wróciło do poprzedniego kroku?
5. **SPRAWDŹ:** Czy dane z poprzednich kroków są zachowane?

### TEST M3.16: Restart po wizardzie
**Co zrobić:**
1. Po zakończeniu wizarda (z M3.13)
2. **ZAMKNIJ:** Aplikację
3. **URUCHOM:** Ponownie `python -m src.menu_app`
4. **OBSERWUJ:** Czy wizard się NIE uruchomił?
5. **SPRAWDŹ:** Czy daemon działa normalnie?

---

## Sprawdzanie wyników

Po każdym teście możesz sprawdzić wyniki:

```bash
# Sprawdź config.json
python scripts/test_wizard_helper.py M3.X

# Sprawdź logi
tail -20 ~/Library/Logs/olympus_transcriber.log | grep -i wizard
```

---

## Raportowanie

Dla każdego testu powiedz:
1. ✅ Czy przeszedł? (TAK/NIE)
2. 📝 Co zaobserwowałeś?
3. 🐛 Czy były jakieś problemy?



