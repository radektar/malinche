# Manual Test Checklist — v2.0.0-alpha.8

## 0. Preconditions
- [ ] macOS z uprawnieniami do uruchamiania aplikacji menu bar.
- [ ] Folder `~/Library/Application Support/Malinche/` istnieje.
- [ ] Masz stabilne połączenie internetowe (do scenariuszy download).
- [ ] Aplikacja uruchamiana z nowym buildem alpha.8.

## 1. Wizard — kolejność i wybór modelu
- [ ] Wymuś pierwszy start (usuń `~/Library/Application Support/Malinche/config.json`).
- [ ] Uruchom app i potwierdź kolejność kroków: `WELCOME -> SOURCE_CONFIG -> BASIC_CONFIG -> DOWNLOAD`.
- [ ] W kroku `BASIC_CONFIG` zmień model na `medium`.
- [ ] Przejdź do `DOWNLOAD` i potwierdź, że ekran pokazuje wybrany model `medium`.
- [ ] Kliknij `Zmień model` i potwierdź powrót do `BASIC_CONFIG`.
- [ ] Ustaw model z powrotem na `small`, przejdź dalej.

## 2. Wizard — pobieranie w tle i responsywność UI
- [ ] W `DOWNLOAD` kliknij `Pobierz teraz`.
- [ ] Potwierdź, że pojawia się okno postępu (progress window), a nie pętla modalnych alertów.
- [ ] Potwierdź, że UI nie zamraża się (menu bar i kliknięcia działają).
- [ ] Zamknij okno postępu i potwierdź, że wizard może iść dalej.
- [ ] Dokończ wizard i zamknij app.

## 3. Resume wizarda po przerwaniu
- [ ] Ponownie wymuś pierwszy start.
- [ ] Przejdź do `BASIC_CONFIG` i przerwij app (Force Quit / kill procesu).
- [ ] Uruchom app ponownie.
- [ ] Potwierdź, że wizard wraca od zapisanego etapu (`setup_stage`), a nie od początku.

## 4. Menu app — async dependency download
- [ ] Ustaw w `config.json` model na `medium`, usuń lokalny model medium jeśli istnieje.
- [ ] Uruchom app, zaakceptuj pobieranie zależności.
- [ ] Potwierdź status `Pobieranie...` oraz brak freeze UI.
- [ ] Potwierdź, że ikona/status po zakończeniu wraca do stanu gotowości.

## 5. Zmiana modelu w Settings po setupie
- [ ] Przy działającej aplikacji otwórz `Ustawienia`.
- [ ] Zmień model `small -> medium` i zapisz.
- [ ] Potwierdź komunikat o brakujących danych i starcie pobierania w tle.
- [ ] Bez restartu app sprawdź, że pobieranie się rozpoczęło.

## 6. Ścieżki błędów download
- [ ] Wyłącz internet i spróbuj pobrania -> oczekiwany komunikat `Brak połączenia`.
- [ ] Zasymuluj brak miejsca na dysku -> oczekiwany komunikat `Brak miejsca`.
- [ ] Przywróć internet i ponów -> pobieranie powinno wystartować poprawnie.

## 7. Smoke test transkrypcji po pobraniu
- [ ] Podłącz recorder/kartę SD z 1-2 plikami audio.
- [ ] Potwierdź wykrycie wolumenu i rozpoczęcie przetwarzania.
- [ ] Potwierdź utworzenie pliku `.md` w folderze docelowym.
- [ ] Potwierdź brak crashy/freeze podczas transkrypcji.

## 8. Artefakty do zebrania po teście
- [ ] `~/Library/Application Support/Malinche/config.json`
- [ ] `~/Library/Application Support/Malinche/logs/malinche.log`
- [ ] Krótki raport: PASS/FAIL per sekcja 1-7.

