# Instrukcja dla testerów - Malinche

Dziękujemy za testowanie aplikacji **Malinche** (dawniej Transrec)!

Ponieważ jest to wersja testowa i nie posiada jeszcze certyfikatu Apple Developer, proces instalacji wymaga kilku dodatkowych kroków.

## 📥 Instalacja

1. Pobierz plik `Malinche-2.0.0-ARM64-UNSIGNED.dmg`.
2. Otwórz plik DMG (dwukrotne kliknięcie).
3. Przeciągnij ikonę **Malinche** do folderu **Applications**.

## 🚀 Pierwsze uruchomienie (Omijanie Gatekeepera)

Przy pierwszej próbie otwarcia zobaczysz komunikat: *"Malinche" cannot be opened because the developer cannot be verified.*

**Aby uruchomić aplikację:**
1. Otwórz folder **Applications** w Finderze.
2. Kliknij na ikonę **Malinche** PRAWYM PRZYCISKIEM MYSZY (lub Ctrl + kliknięcie).
3. Wybierz opcję **Otwórz** (Open).
4. W oknie dialogowym, które się pojawi, ponownie kliknij **Otwórz** (Open).
5. Aplikacja zostanie dodana do wyjątków bezpieczeństwa i od teraz będzie uruchamiać się normalnie.

## 🔐 Uprawnienia (Full Disk Access)

Aby Malinche mogło automatycznie wykrywać podłączone dyktafony i karty SD, potrzebuje uprawnień do odczytu dysków zewnętrznych.

1. Po uruchomieniu, Wizard przeprowadzi Cię przez proces.
2. Wejdź w **Ustawienia Systemowe** -> **Prywatność i bezpieczeństwo** -> **Pełny dostęp do dysku**.
3. Dodaj/zaznacz **Malinche** na liście.

## 🧪 Co testować?

1. **Wizard**: Czy pobieranie silnika Whisper i modelu przebiega poprawnie?
2. **Wykrywanie**: Czy po podłączeniu dyktafonu/karty SD aplikacja reaguje?
3. **Transkrypcja**: Czy pliki Markdown są generowane poprawnie?
4. **Ustawienia**: Czy zmiana folderu docelowego lub języka działa?

## 📝 Feedback

Zgłoś wszelkie błędy lub sugestie do zespołu deweloperskiego. Zwróć szczególną uwagę na:
- Czy aplikacja się zawiesza?
- Czy komunikaty są zrozumiałe?
- Czy interfejs w pasku menu działa płynnie?
