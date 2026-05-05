# TEST M4.6: Clean System Test - Instrukcje

> **Data:** 2025-12-29  
> **Test:** M4.6 - Clean system test  
> **Cel:** Sprawdzenie czy bundle działa na czystym macOS bez Python

---

## 📋 Przygotowanie

### 1. Skopiuj bundle na innego Maca

**Opcja A: Przez AirDrop**
```bash
# Na Macu źródłowym (gdzie zbudowano bundle)
open -a AirDrop dist/Transrec.app
```

**Opcja B: Przez USB/External Drive**
```bash
# Skopiuj folder dist/Transrec.app na zewnętrzny dysk
cp -R dist/Transrec.app /Volumes/[NAZWA_DYSKU]/
```

**Opcja C: Przez sieć (scp)**
```bash
# Jeśli masz dostęp SSH do drugiego Maca
scp -r dist/Transrec.app user@other-mac.local:~/Desktop/
```

### 2. Sprawdź czy Python nie jest zainstalowany na docelowym Macu

```bash
# Na docelowym Macu sprawdź:
which python3
python3 --version

# Jeśli Python jest zainstalowany, sprawdź czy to systemowy:
/usr/bin/python3 --version  # Systemowy Python (może być)
# Lub sprawdź czy to Homebrew:
brew list python3  # Jeśli zwraca błąd, Python nie jest z Homebrew
```

**UWAGA:** Obecność systemowego Pythona (np. `/usr/bin/python3`) jest OK - bundle powinien używać własnego Pythona z bundle.

---

## 🧪 Scenariusz testowy

### Krok 1: Uruchomienie aplikacji

1. **Na docelowym Macu**, znajdź `Transrec.app` (na Desktop lub w Downloads)
2. **Kliknij dwukrotnie** lub użyj:
   ```bash
   open ~/Desktop/Transrec.app
   # lub
   open ~/Downloads/Transrec.app
   ```

3. **OBSERWUJ:**
   - Czy aplikacja się uruchamia (ikona w menu bar)
   - Czy pojawiają się błędy w Console.app
   - Czy logi są tworzone: `~/Library/Logs/olympus_transcriber.log`

### Krok 2: Test wizarda (pierwsze uruchomienie)

1. **Jeśli to pierwsze uruchomienie**, powinien pojawić się wizard
2. **Przejdź przez wizard:**
   - ✅ Krok 1: Powitanie
   - ✅ Krok 2: Pobieranie zależności (jeśli nie są pobrane)
   - ✅ Krok 3: Full Disk Access (jeśli nie nadane)
   - ✅ Krok 4: Źródła nagrań
   - ✅ Krok 5: Folder docelowy
   - ✅ Krok 6: Język
   - ✅ Krok 7: AI config (opcjonalnie)
   - ✅ Krok 8: Zakończenie

3. **SPRAWDŹ** czy konfiguracja została zapisana:
   ```bash
   cat ~/Library/Application\ Support/Transrec/config.json
   ```

### Krok 3: Test pobierania zależności

**Jeśli zależności nie są pobrane:**

1. Usuń zależności (jeśli istnieją):
   ```bash
   rm -rf ~/Library/Application\ Support/Transrec/bin/
   rm -rf ~/Library/Application\ Support/Transrec/models/
   rm -f ~/Library/Application\ Support/Transrec/config.json
   ```

2. Uruchom aplikację ponownie
3. **SPRAWDŹ:**
   - Czy wizard wykrywa brak zależności
   - Czy krok pobierania się uruchamia
   - Czy okno dialogowe pokazuje postęp
   - Czy pobieranie kończy się sukcesem
   - Czy zależności są pobierane:
     ```bash
     ls -la ~/Library/Application\ Support/Transrec/bin/
     ls -la ~/Library/Application\ Support/Transrec/models/
     ```

### Krok 4: Test menu bar

1. **Kliknij ikonę** Transrec w menu bar
2. **SPRAWDŹ** wszystkie opcje menu:
   - Status
   - Ostatnie transkrypcje
   - Resetuj pamięć od...
   - Retranskrybuj plik...
   - Ustawienia...
   - Wyjście

3. **SPRAWDŹ** czy każda opcja działa poprawnie

### Krok 5: Test transkrypcji (jeśli masz recorder)

**UWAGA:** Ten krok wymaga podłączenia dyktafonu/karty SD

1. **Podłącz** dyktafon lub kartę SD z nagraniami
2. **SPRAWDŹ** czy aplikacja wykrywa nowe pliki
3. **SPRAWDŹ** czy transkrypcja działa:
   - Czy pliki są przetwarzane
   - Czy transkrypty są tworzone w folderze docelowym
   - Czy notyfikacje są wyświetlane

### Krok 6: Sprawdzenie logów

```bash
# Sprawdź logi aplikacji
tail -50 ~/Library/Logs/olympus_transcriber.log

# Sprawdź Console.app dla błędów systemowych
# Otwórz Console.app i wyszukaj "Transrec" lub "olympus_transcriber"
```

---

## ✅ Checklist wyników

### Podstawowe funkcje
- [ ] Aplikacja uruchamia się bez błędów
- [ ] Ikona pojawia się w menu bar
- [ ] Brak błędów w Console.app
- [ ] Logi są tworzone poprawnie

### Wizard
- [ ] Wizard uruchamia się przy pierwszym uruchomieniu
- [ ] Wszystkie kroki wizarda działają
- [ ] Konfiguracja jest zapisywana poprawnie

### Pobieranie zależności
- [ ] Wizard wykrywa brak zależności
- [ ] Pobieranie działa poprawnie
- [ ] Okno dialogowe pokazuje postęp
- [ ] Zależności są pobierane do poprawnej lokalizacji
- [ ] Po pobraniu aplikacja działa normalnie

### Menu bar
- [ ] Wszystkie opcje menu działają
- [ ] Status jest wyświetlany poprawnie
- [ ] Ustawienia działają

### Transkrypcja (jeśli testowane)
- [ ] Aplikacja wykrywa podłączenie dysku/karty SD
- [ ] Pliki są skanowane
- [ ] Transkrypcja działa
- [ ] Transkrypty są zapisywane poprawnie

---

## 📝 Notatki z testów

### Środowisko docelowe:
- macOS wersja: _______________
- Architektura: _______________ (arm64 / x86_64)
- Python zainstalowany: TAK / NIE
- Python wersja (jeśli zainstalowany): _______________

### Wyniki:
- [ ] ✅ Wszystkie testy przechodzą
- [ ] ⚠️ Częściowe problemy (opisz poniżej)
- [ ] ❌ Krytyczne problemy (opisz poniżej)

### Znalezione problemy:

1. **Problem:** _______________
   - **Opis:** _______________
   - **Krytyczność:** Wysoka / Średnia / Niska

2. **Problem:** _______________
   - **Opis:** _______________
   - **Krytyczność:** Wysoka / Średnia / Niska

### Dodatkowe uwagi:

_______________

---

## 🔍 Troubleshooting

### Problem: Aplikacja nie uruchamia się

**Sprawdź:**
1. Console.app - czy są błędy systemowe?
2. Logi: `~/Library/Logs/olympus_transcriber.log`
3. Czy bundle ma uprawnienia do wykonania:
   ```bash
   chmod +x Transrec.app/Contents/MacOS/Transrec
   ```

### Problem: "App is damaged" lub "Cannot be opened"

**Rozwiązanie:**
```bash
# Usuń kwarantannę
xattr -cr Transrec.app
```

### Problem: Wizard nie działa

**Sprawdź:**
- Czy `config.json` istnieje i jest poprawny
- Czy logi pokazują błędy
- Czy Full Disk Access jest nadane (jeśli wymagane)

---

**Po zakończeniu testów, zaktualizuj `tests/MANUAL_TESTING_PHASE_4.md` z wynikami.**


