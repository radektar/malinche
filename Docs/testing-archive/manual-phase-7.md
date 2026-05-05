# Manual Testing - Faza 7: GUI Settings & Polish

**Data:** 2025-12-29  
**Wersja:** v2.0.0  
**Tester:** Manual testing completed

---

## Checklist testów manualnych

| ID | Test | Kryteria akceptacji | Status | Uwagi |
|----|------|---------------------|--------|-------|
| M7.1 | Date picker - 7 dni | Reset do 7 dni działa | [x] | PASS - Notyfikacja działa po poprawce |
| M7.2 | Date picker - 30 dni | Reset do 30 dni działa | [x] | PASS - Poprawka response=-1 dla przycisku "other" |
| M7.3 | Date picker - custom | Input YYYY-MM-DD działa | [x] | PASS |
| M7.4 | Date picker - błędna data | Pokazuje komunikat błędu | [x] | PASS |
| M7.5 | Folder picker - NSOpenPanel | Otwiera dialog systemowy | [x] | PASS |
| M7.6 | Folder picker - wybór | Zapisuje wybraną ścieżkę | [x] | PASS |
| M7.7 | Folder picker - anuluj | Wraca do poprzedniego kroku | [x] | PASS |
| M7.8 | About dialog | Pokazuje wersję i linki | [x] | PASS |
| M7.9 | About dialog - zamknięcie | OK zamyka dialog | [x] | PASS |

---

## Procedura testów

### Przygotowanie

1. Zbuduj bundle:
   ```bash
   python setup_app.py py2app
   ```

2. Uruchom aplikację:
   ```bash
   open dist/Malinche.app
   ```

---

### M7.1: Date picker - 7 dni

**Kroki:**
1. Kliknij ikonę Malinche w pasku menu
2. Wybierz "Resetuj pamięć od..."
3. W dialogu wybierz opcję "7 dni"

**Oczekiwany wynik:**
- Pamięć zostaje zresetowana do daty sprzed 7 dni
- Pojawia się notyfikacja z potwierdzeniem

**Status:** [x] PASS / [ ] FAIL

**Uwagi:** Notyfikacja działa poprawnie po zmianie z `rumps.notification()` na `send_notification()` (osascript)

---

### M7.2: Date picker - 30 dni

**Kroki:**
1. Kliknij ikonę Malinche w pasku menu
2. Wybierz "Resetuj pamięć od..."
3. W dialogu wybierz opcję "30 dni"

**Oczekiwany wynik:**
- Pamięć zostaje zresetowana do daty sprzed 30 dni
- Pojawia się notyfikacja z potwierdzeniem

**Status:** [x] PASS / [ ] FAIL

**Uwagi:** Poprawka - `rumps.alert()` zwraca `-1` dla przycisku "other", nie `2`

---

### M7.3: Date picker - custom data

**Kroki:**
1. Kliknij ikonę Malinche w pasku menu
2. Wybierz "Resetuj pamięć od..."
3. W dialogu wybierz "Inna data..."
4. Wpisz datę w formacie YYYY-MM-DD (np. 2025-12-01)
5. Kliknij OK

**Oczekiwany wynik:**
- Pamięć zostaje zresetowana do podanej daty
- Pojawia się notyfikacja z potwierdzeniem

**Status:** [x] PASS / [ ] FAIL

---

### M7.4: Date picker - błędna data

**Kroki:**
1. Kliknij ikonę Malinche w pasku menu
2. Wybierz "Resetuj pamięć od..."
3. W dialogu wybierz "Inna data..."
4. Wpisz nieprawidłową datę (np. "invalid-date" lub "2025-13-45")
5. Kliknij OK

**Oczekiwany wynik:**
- Pojawia się komunikat błędu o nieprawidłowym formacie daty
- Pamięć nie zostaje zresetowana

**Status:** [x] PASS / [ ] FAIL

---

### M7.5: Folder picker - NSOpenPanel

**Kroki:**
1. Uruchom wizard (jeśli nie był uruchomiony, usuń `~/Library/Application Support/Malinche/config.json`)
2. Przejdź do kroku "Folder na transkrypcje"
3. Kliknij "Wybierz folder..."

**Oczekiwany wynik:**
- Otwiera się natywny dialog macOS do wyboru folderu
- Dialog pozwala na przeglądanie folderów

**Status:** [x] PASS / [ ] FAIL

---

### M7.6: Folder picker - wybór

**Kroki:**
1. W dialogu wyboru folderu (M7.5) wybierz dowolny folder
2. Kliknij "Wybierz"

**Oczekiwany wynik:**
- Wybrana ścieżka zostaje zapisana w ustawieniach
- Wizard przechodzi do następnego kroku

**Status:** [x] PASS / [ ] FAIL

---

### M7.7: Folder picker - anuluj

**Kroki:**
1. W dialogu wyboru folderu (M7.5) kliknij "Anuluj" lub zamknij dialog
2. Następnie kliknij "Wstecz" w głównym dialogu

**Oczekiwany wynik:**
- Wizard wraca do poprzedniego kroku
- Ustawienia nie zostają zmienione

**Status:** [x] PASS / [ ] FAIL

---

### M7.8: About dialog

**Kroki:**
1. Kliknij ikonę Malinche w pasku menu
2. Wybierz "O aplikacji..."

**Oczekiwany wynik:**
- Dialog pokazuje:
  - Nazwę aplikacji: "Malinche"
  - Wersję: "v2.0.0"
  - Link do strony: https://transrec.app
  - Link do GitHub: https://github.com/radektar/transrec
  - Informację o licencji: "Open Source (MIT)"

**Status:** [x] PASS / [ ] FAIL

---

### M7.9: About dialog - zamknięcie

**Kroki:**
1. Otwórz dialog "O aplikacji" (M7.8)
2. Kliknij "OK"

**Oczekiwany wynik:**
- Dialog zamyka się
- Aplikacja działa normalnie

**Status:** [x] PASS / [ ] FAIL

---

## Podsumowanie

- **Testy wykonane:** 9/9
- **Testy przechodzące:** 9/9
- **Testy nieprzechodzące:** 0/9

## Uwagi ogólne

[Dodaj tutaj wszelkie uwagi dotyczące UX, błędów, sugestii poprawy]

---

## Następne kroki

- [x] Wszystkie testy przechodzą ✅
- [x] Zgłoszone błędy naprawione ✅
  - Naprawiono notyfikacje (zmiana z rumps.notification na send_notification)
  - Naprawiono obsługę przycisku "other" w date picker (response=-1 zamiast 2)
- [ ] Dokumentacja zaktualizowana

## Dodatkowe poprawki zaimplementowane podczas testów

- ✅ Dodano opcję "Anuluj" w każdym kroku wizarda (oprócz download)
- ✅ Zaimplementowano dropdown wyboru języka z NSPopUpButton zamiast tekstowego inputu

