# TEST M4.3: Menu Functionality - Checklist

## Status przygotowania ✅
- ✅ Aplikacja działa (PID: 52940)
- ✅ Log file istnieje (~/Library/Logs/olympus_transcriber.log)
- ✅ Staging directory istnieje z 7 plikami audio
- ✅ State file istnieje

---

## Testy do wykonania

### 1. ✅ Status (wyświetlanie)
**Sprawdź:**
- [ ] Kliknij ikonę w menu bar
- [ ] Sprawdź czy pierwsza linia to "Status: Oczekiwanie na recorder..." (lub podobny status)
- [ ] Status powinien być nieklikalny (tylko wyświetlanie)

**Oczekiwany wynik:** Status wyświetla aktualny stan aplikacji

---

### 2. ✅ Otwórz logi
**Sprawdź:**
- [ ] Kliknij "Otwórz logi" w menu
- [ ] Sprawdź czy otwiera się plik logów w domyślnym edytorze (TextEdit lub inny)
- [ ] Sprawdź czy plik zawiera logi aplikacji

**Oczekiwany wynik:** Plik logów otwiera się w edytorze

---

### 3. ✅ Resetuj pamięć od...
**Sprawdź:**
- [ ] Kliknij "Resetuj pamięć od..." w menu
- [ ] Sprawdź czy pojawia się dialog z pytaniem o reset do daty sprzed 7 dni
- [ ] Kliknij "Anuluj" (nie resetuj teraz)
- [ ] Sprawdź czy dialog się zamyka bez zmian

**Oczekiwany wynik:** Dialog się pojawia i działa poprawnie

---

### 4. ✅ Retranskrybuj plik...
**Sprawdź:**
- [ ] Kliknij "Retranskrybuj plik..." w menu (powinno być strzałka > wskazująca submenu)
- [ ] Sprawdź czy submenu się otwiera
- [ ] Sprawdź czy widzisz listę plików audio (powinno być 7 plików z datami)
- [ ] Sprawdź format: "📁 nazwa_pliku (DD.MM.YYYY HH:MM)"

**Oczekiwany wynik:** Submenu pokazuje listę plików z staging directory

**Uwaga:** Nie klikaj jeszcze żadnego pliku - to będzie test retranskrypcji

---

### 5. ✅ Zakończ / Quit
**UWAGA:** Ten test na końcu - zamknie aplikację!

**Sprawdź:**
- [ ] Kliknij "Zakończ" w menu
- [ ] Sprawdź czy pojawia się dialog potwierdzenia
- [ ] Kliknij "Anuluj" (nie zamykaj jeszcze)
- [ ] Sprawdź czy aplikacja nadal działa

**Oczekiwany wynik:** Dialog potwierdzenia działa, aplikacja nie zamyka się po anulowaniu

---

## Wyniki testów

Po wykonaniu wszystkich testów, zaznacz co działa:

- [ ] Status wyświetla się poprawnie
- [ ] Otwórz logi działa
- [ ] Resetuj pamięć pokazuje dialog
- [ ] Retranskrybuj plik pokazuje submenu z plikami
- [ ] Zakończ pokazuje dialog potwierdzenia

### Znalezione problemy:
- 

---

## Następne kroki

Po zakończeniu testów M4.3:
- TEST M4.4: Wizard w bundle
- TEST M4.5: Dependency download w bundle


