# Raport testów manualnych - TEST M1: Pierwsze uruchomienie

**Data:** 2025-12-26  
**Tester:** Automated Test Script  
**Wersja:** feature/faza-2-dependency-downloader  
**macOS:** macOS 25.1.0 (darwin)  
**Architektura:** arm64

## Prerequisites

- [x] GitHub Release utworzony: TAK (deps-v1.0.0)
- [x] Checksums zaktualizowane: TAK
- [x] URLs zaktualizowane: TAK
- [x] Unit tests: PASS (100%)

## Wyniki testów

### TEST M1: Pierwsze uruchomienie

| Element | Status | Uwagi |
|---------|--------|-------|
| Dialog pobierania | N/A | Test automatyczny - bez GUI |
| Postęp w status | PASS | Progress callback działał poprawnie |
| whisper-cli pobrany | PASS | 824,360 bajtów (805 KB) |
| ffmpeg pobrany | PASS | 80,083,328 bajtów (76.4 MB) |
| Model pobrany | PASS | 487,601,967 bajtów (465 MB) |
| Checksum verification | PASS | Model checksum się zgadza |
| Uprawnienia wykonywania | PASS | Wszystkie pliki mają chmod 755 |
| Aplikacja działa | PASS | check_all() zwraca True |

**Czas pobierania:**
- whisper-cli: ~1 sekunda
- ffmpeg: ~36 sekund
- Model: ~46 sekund (łącznie ~83 sekundy)

**Szczegóły:**
- whisper-cli: ✓ Pobrano w pierwszej próbie
- ffmpeg: ✓ Pobrano w pierwszej próbie
- Model: ✓ Pobrano w pierwszej próbie
- Checksum modelu: `1be3a9b2063867b937e64e2ec7483364a79917e17fa98c5d94b5c1fffea987b` ✓

**Uwagi:**
- Test wykonany automatycznie przez skrypt (bez GUI)
- Wszystkie pliki zostały pobrane poprawnie
- Checksum weryfikacja działa poprawnie
- Uprawnienia wykonywania ustawione poprawnie
- Logi pokazują sukces dla wszystkich operacji

## Podsumowanie

- **Testy przeszły:** 1/1 (TEST M1)
- **Krytyczne problemy:** 0
- **Wysokie problemy:** 0
- **Średnie problemy:** 0
- **Niskie problemy:** 0

**Gotowe do merge:** TAK (dla części automatycznej)

**Uwagi końcowe:**
TEST M1 przeszedł pomyślnie w trybie automatycznym. Wszystkie zależności zostały pobrane poprawnie z GitHub Releases i HuggingFace. Checksum weryfikacja działa poprawnie. 

**Następne kroki:**
- TEST M2: Brak internetu (wymaga manualnego wyłączenia WiFi)
- TEST M3: Resume download (wymaga przerwania pobierania)
- TEST M4-M6: Opcjonalne testy zaawansowane



