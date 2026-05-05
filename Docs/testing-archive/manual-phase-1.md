# Manual Testing Guide - Faza 1: Uniwersalne źródła nagrań

> **Wersja:** v2.0.0  
> **Faza:** 1 - Universal Volume Detection  
> **Data:** 2025-12-17  
> **Status:** ⚠️ Testy integracyjne zakończone, testy manualne wymagane przed produkcją

---

## 📊 Status testów

### ✅ Testy automatyczne (ZAKOŃCZONE)

**Testy integracyjne:** `tests/test_file_monitor_integration.py`
- ✅ 11 testów przechodzi (100% pass rate)
- ✅ Pokrycie scenariuszy: auto/specific/manual modes, różne formaty audio, volumeny systemowe, debouncing, zagnieżdżone katalogi
- ✅ Symulowane volumeny bez potrzeby fizycznych urządzeń

**Testy jednostkowe:** `tests/test_settings.py`, `tests/test_file_monitor.py`
- ✅ Wszystkie testy przechodzą
- ✅ Pokrycie logiki `UserSettings` i `FileMonitor`

### ⚠️ Testy manualne (WYMAGANE PRZED PRODUKCJĄ)

**Status:** Oczekujące na dostępność fizycznych urządzeń

**Uwaga:** Testy integracyjne pokrywają logikę aplikacji, ale **testy manualne na rzeczywistych urządzeniach są niezbędne** przed wydaniem v2.0.0 FREE, aby zweryfikować:
- Rzeczywiste zachowanie FSEvents na różnych urządzeniach
- Kompatybilność z różnymi systemami plików (FAT32, exFAT, HFS+)
- Wydajność skanowania na dużych volumenach
- Obsługę edge cases specyficznych dla fizycznych urządzeń

---

## 📋 Cel testów manualnych

Weryfikacja wykrywania i przetwarzania różnych urządzeń USB/SD card z plikami audio, zgodnie z nowym systemem `watch_mode` (auto, specific, manual).

---

## ✅ Prerequisites

### Wymagane urządzenia

| Urządzenie | Status | Uwagi |
|------------|--------|-------|
| Olympus LS-P1 | [ ] | Legacy recorder (backward compatibility) |
| Zoom H1/H6 | [ ] | Popularny recorder |
| Generic SD card | [ ] | Z plikami .mp3, .wav |
| USB flash drive | [ ] | Z plikami audio |
| iPhone (jako dysk) | [ ] | Opcjonalnie - DCIM folder |
| Empty USB drive | [ ] | **NIE powinien być wykryty** |

### Wymagane pliki testowe

- **Pliki audio na urządzeniach:**
  - `.mp3` - minimum 1 plik
  - `.wav` - minimum 1 plik
  - `.m4a` - opcjonalnie
  - `.flac` - opcjonalnie

- **Pliki nie-audio (do weryfikacji ignorowania):**
  - `.txt`, `.jpg`, `.pdf` - nie powinny być wykryte

### Środowisko testowe

- macOS 12+ (Monterey lub nowszy)
- Python 3.12+ z venv aktywowanym
- Transrec uruchomiony z brancha `feature/faza-1-universal-sources`
- Logi włączone: `tail -f ~/Library/Logs/olympus_transcriber.log`

---

## 🧪 Scenariusze testowe

### SCENARIUSZ 1: Watch Mode "auto" - Automatyczne wykrywanie

**Cel:** Weryfikacja automatycznego wykrywania urządzeń z plikami audio.

#### Setup

```bash
# 1. Uruchom aplikację
cd ~/CODEing/transrec
source venv/bin/activate
python -m src.menu_app

# 2. Ustaw watch_mode na "auto" (jeśli nie jest domyślny)
# W terminalu lub przez modyfikację config.json:
python3 << EOF
from src.config.settings import UserSettings
settings = UserSettings.load()
settings.watch_mode = "auto"
settings.save()
print("Watch mode set to: auto")
EOF

# 3. Otwórz logi w osobnym terminalu
tail -f ~/Library/Logs/olympus_transcriber.log
```

#### Test Steps

Dla każdego urządzenia z plikami audio:

1. **Podłącz urządzenie** (USB/SD card)
2. **Obserwuj logi** - powinno pojawić się:
   ```
   📢 Detected volume activity: /Volumes/[DEVICE_NAME]/...
   ```
3. **Sprawdź czy transkrypcja startuje** - powinien pojawić się proces transkrypcji
4. **Odłącz urządzenie**
5. **Podłącz ponownie** - sprawdź czy nie duplikuje przetwarzania (debouncing)

#### Expected Results

| Urządzenie | Wykryte? | Transkrypcja startuje? | Uwagi |
|------------|----------|------------------------|-------|
| Olympus LS-P1 z audio | ✅ | ✅ | Legacy support |
| Zoom H1/H6 z audio | ✅ | ✅ | Nowy recorder |
| SD card z .mp3 | ✅ | ✅ | Generic device |
| USB drive z .wav | ✅ | ✅ | Generic device |
| USB drive BEZ audio | ❌ | ❌ | Powinien być ignorowany |
| iPhone (DCIM) | ⚠️ | ⚠️ | Zależy od zawartości |

#### Verification Commands

```bash
# Sprawdź logi wykrywania
grep "Detected volume activity" ~/Library/Logs/olympus_transcriber.log | tail -10

# Sprawdź czy pliki zostały przetworzone
ls -la ~/Documents/Transcriptions/  # lub inny output_dir

# Sprawdź konfigurację
cat ~/Library/Application\ Support/Transrec/config.json | python3 -m json.tool
```

---

### SCENARIUSZ 2: Watch Mode "specific" - Tylko wybrane volumeny

**Cel:** Weryfikacja przetwarzania tylko określonych urządzeń z listy.

#### Setup

```bash
# Ustaw watch_mode na "specific" i dodaj urządzenia do listy
python3 << EOF
from src.config.settings import UserSettings
settings = UserSettings.load()
settings.watch_mode = "specific"
settings.watched_volumes = ["SD_CARD", "USB_DRIVE"]  # Zastąp rzeczywistymi nazwami
settings.save()
print(f"Watch mode: {settings.watch_mode}")
print(f"Watched volumes: {settings.watched_volumes}")
EOF
```

#### Test Steps

1. **Podłącz urządzenie Z LISTY** (np. "SD_CARD")
   - ✅ Powinno być wykryte i przetworzone
   
2. **Podłącz urządzenie POZA LISTĄ** (np. "OTHER_DEVICE")
   - ❌ Powinno być zignorowane (brak logów wykrywania)

3. **Dodaj nowe urządzenie do listy** (bez restartu aplikacji)
   ```bash
   # Zmień config i podłącz urządzenie
   # Aplikacja powinna załadować nową konfigurację przy następnym wykryciu
   ```

#### Expected Results

| Urządzenie | Na liście? | Wykryte? | Przetworzone? |
|------------|------------|----------|---------------|
| SD_CARD | ✅ | ✅ | ✅ |
| USB_DRIVE | ✅ | ✅ | ✅ |
| OTHER_DEVICE | ❌ | ❌ | ❌ |

---

### SCENARIUSZ 3: Watch Mode "manual" - Brak auto-detekcji

**Cel:** Weryfikacja że tryb manual nie przetwarza automatycznie.

#### Setup

```bash
python3 << EOF
from src.config.settings import UserSettings
settings = UserSettings.load()
settings.watch_mode = "manual"
settings.save()
print("Watch mode set to: manual")
EOF
```

#### Test Steps

1. **Podłącz urządzenie z plikami audio**
2. **Obserwuj logi** - NIE powinno być żadnych logów wykrywania
3. **Sprawdź czy transkrypcja NIE startuje automatycznie**

#### Expected Results

- ❌ Brak logów "Detected volume activity"
- ❌ Brak automatycznej transkrypcji
- ✅ Aplikacja działa normalnie (menu bar visible)

---

### SCENARIUSZ 4: Wykrywanie różnych formatów audio

**Cel:** Weryfikacja wykrywania wszystkich obsługiwanych formatów.

#### Setup

Przygotuj USB drive z plikami:
- `test.mp3`
- `test.wav`
- `test.m4a`
- `test.flac`
- `test.aac`
- `test.ogg`
- `test.txt` (nie-audio, powinien być ignorowany)

#### Test Steps

1. **Podłącz USB drive** (watch_mode = "auto")
2. **Sprawdź logi** - powinny być wykryte wszystkie formaty audio
3. **Sprawdź czy .txt jest ignorowany**

#### Expected Results

| Format | Wykryty? | Przetworzony? |
|--------|----------|---------------|
| .mp3 | ✅ | ✅ |
| .wav | ✅ | ✅ |
| .m4a | ✅ | ✅ |
| .flac | ✅ | ✅ |
| .aac | ✅ | ✅ |
| .ogg | ✅ | ✅ |
| .txt | ❌ | ❌ |

---

### SCENARIUSZ 5: Ignorowanie system volumes

**Cel:** Weryfikacja że systemowe volumeny są ignorowane.

#### Test Steps

1. **Sprawdź czy "Macintosh HD" jest ignorowany**
   - Nawet jeśli zawiera pliki audio, nie powinien być przetwarzany

2. **Sprawdź inne system volumes:**
   - Recovery
   - Preboot
   - VM
   - Data

#### Expected Results

- ❌ System volumes NIE są wykrywane
- ✅ Logi nie pokazują aktywności dla system volumes

---

### SCENARIUSZ 6: Migracja ze starej konfiguracji

**Cel:** Weryfikacja migracji z `~/.olympus_transcriber_state.json`.

#### Setup

```bash
# 1. Utwórz stary state file
cat > ~/.olympus_transcriber_state.json << EOF
{
  "last_sync": "2024-01-01T12:00:00",
  "transcribe_dir": "$HOME/Documents/OldTranscriptions",
  "language": "en",
  "whisper_model": "medium",
  "recorder_names": ["LS-P1", "OLYMPUS"]
}
EOF

# 2. Usuń nowy config (jeśli istnieje)
rm -f ~/Library/Application\ Support/Transrec/config.json

# 3. Uruchom aplikację - powinna wykonać migrację
```

#### Test Steps

1. **Uruchom aplikację**
2. **Sprawdź logi** - powinna być informacja o migracji:
   ```
   INFO - Old configuration detected, performing migration...
   INFO - Migrated output_dir from old config: ...
   INFO - Migrated watched volumes: ['LS-P1', 'OLYMPUS']
   INFO - ✓ Migration completed successfully
   ```

3. **Sprawdź nowy config:**
   ```bash
   cat ~/Library/Application\ Support/Transrec/config.json | python3 -m json.tool
   ```

#### Expected Results

- ✅ Migracja wykonana automatycznie
- ✅ `watch_mode` = "specific" (z migrated volumes)
- ✅ `watched_volumes` = ["LS-P1", "OLYMPUS"]
- ✅ `output_dir` = migrated path
- ✅ `setup_completed` = true
- ✅ Nowy config.json utworzony

---

### SCENARIUSZ 7: Głębokość skanowania (max_depth)

**Cel:** Weryfikacja że skanowanie jest ograniczone do rozsądnej głębokości.

#### Setup

Utwórz strukturę katalogów na USB drive:
```
USB_DRIVE/
├── level1/
│   ├── level2/
│   │   ├── level3/
│   │   │   └── audio.mp3  ✅ Powinien być wykryty (depth 3)
│   │   └── level4/
│   │       └── audio.mp3  ❌ Powinien być ignorowany (depth 4)
```

#### Test Steps

1. **Podłącz USB drive**
2. **Sprawdź logi** - tylko pliki do depth 3 powinny być wykryte

#### Expected Results

- ✅ Pliki na głębokości ≤ 3 są wykryte
- ❌ Pliki na głębokości > 3 są ignorowane

---

## 📊 Checklist testów manualnych

### Przed rozpoczęciem

- [ ] Wszystkie urządzenia przygotowane z plikami audio
- [ ] Logi włączone (`tail -f`)
- [ ] Konfiguracja zapisana (watch_mode ustawiony)
- [ ] Backup starej konfiguracji (jeśli istnieje)

### Testy podstawowe

- [ ] **SCENARIUSZ 1:** Watch mode "auto" - wykrywa urządzenia z audio
- [ ] **SCENARIUSZ 1:** Watch mode "auto" - ignoruje urządzenia bez audio
- [ ] **SCENARIUSZ 2:** Watch mode "specific" - przetwarza tylko z listy
- [ ] **SCENARIUSZ 2:** Watch mode "specific" - ignoruje poza listą
- [ ] **SCENARIUSZ 3:** Watch mode "manual" - brak auto-detekcji

### Testy formatów

- [ ] **SCENARIUSZ 4:** Wykrywa .mp3
- [ ] **SCENARIUSZ 4:** Wykrywa .wav
- [ ] **SCENARIUSZ 4:** Wykrywa .m4a
- [ ] **SCENARIUSZ 4:** Wykrywa .flac
- [ ] **SCENARIUSZ 4:** Wykrywa .aac
- [ ] **SCENARIUSZ 4:** Wykrywa .ogg
- [ ] **SCENARIUSZ 4:** Ignoruje .txt

### Testy zaawansowane

- [ ] **SCENARIUSZ 5:** Ignoruje system volumes
- [ ] **SCENARIUSZ 6:** Migracja ze starej konfiguracji działa
- [ ] **SCENARIUSZ 7:** Max depth działa poprawnie

### Po testach

- [ ] Wszystkie logi zapisane
- [ ] Screenshots problemów (jeśli były)
- [ ] Raport błędów utworzony (jeśli były)
- [ ] Konfiguracja przywrócona do stanu początkowego

---

## 🐛 Troubleshooting

### Problem: Urządzenie nie jest wykrywane

**Debug:**
```bash
# Sprawdź czy volumen jest zamontowany
ls /Volumes/

# Sprawdź logi
grep -i "volume\|detect" ~/Library/Logs/olympus_transcriber.log

# Sprawdź konfigurację
cat ~/Library/Application\ Support/Transrec/config.json | python3 -m json.tool | grep watch_mode
```

**Możliwe przyczyny:**
- Watch mode = "manual" (nie wykrywa automatycznie)
- Urządzenie nie ma plików audio (watch mode = "auto")
- Urządzenie nie jest na liście (watch mode = "specific")
- System volume (zawsze ignorowany)

### Problem: Wszystkie urządzenia są wykrywane (nawet bez audio)

**Debug:**
```bash
# Sprawdź czy _has_audio_files działa
python3 << EOF
from pathlib import Path
from src.file_monitor import FileMonitor
monitor = FileMonitor(lambda: None)
volume = Path("/Volumes/YOUR_DEVICE")
print(f"Has audio: {monitor._has_audio_files(volume)}")
EOF
```

**Możliwe przyczyny:**
- Błąd w logice `_has_audio_files()`
- Pliki audio są na głębokości > max_depth

### Problem: Migracja nie działa

**Debug:**
```bash
# Sprawdź czy stary state file istnieje
ls -la ~/.olympus_transcriber_state.json

# Sprawdź logi migracji
grep -i "migration\|migrate" ~/Library/Logs/olympus_transcriber.log

# Sprawdź czy nowy config został utworzony
ls -la ~/Library/Application\ Support/Transrec/config.json
```

---

## 📝 Template raportu testowego

```markdown
# Raport testów manualnych - Faza 1

**Data:** YYYY-MM-DD
**Tester:** [Imię]
**Wersja:** v2.0.0 (feature/faza-1-universal-sources)
**macOS:** [wersja]

## Wyniki testów

### SCENARIUSZ 1: Watch Mode "auto"
- ✅/❌ Wykrywa urządzenia z audio
- ✅/❌ Ignoruje urządzenia bez audio
- **Uwagi:** [opcjonalne]

### SCENARIUSZ 2: Watch Mode "specific"
- ✅/❌ Przetwarza tylko z listy
- ✅/❌ Ignoruje poza listą
- **Uwagi:** [opcjonalne]

### SCENARIUSZ 3: Watch Mode "manual"
- ✅/❌ Brak auto-detekcji
- **Uwagi:** [opcjonalne]

### SCENARIUSZ 4: Formaty audio
- ✅/❌ .mp3, .wav, .m4a, .flac, .aac, .ogg
- **Uwagi:** [opcjonalne]

### SCENARIUSZ 5: System volumes
- ✅/❌ Ignorowane poprawnie
- **Uwagi:** [opcjonalne]

### SCENARIUSZ 6: Migracja
- ✅/❌ Migracja działa
- **Uwagi:** [opcjonalne]

### SCENARIUSZ 7: Max depth
- ✅/❌ Działa poprawnie
- **Uwagi:** [opcjonalne]

## Znalezione problemy

1. [Opis problemu]
   - **Severity:** Critical/High/Medium/Low
   - **Steps to reproduce:** [kroki]
   - **Expected:** [oczekiwane zachowanie]
   - **Actual:** [rzeczywiste zachowanie]

## Podsumowanie

- **Testy przeszły:** X/Y
- **Krytyczne problemy:** 0
- **Gotowe do commita:** ✅/❌
```

---

## ✅ Kryteria akceptacji

Testy manualne są **PASS** jeśli:

- ✅ Wszystkie scenariusze 1-3 przechodzą (watch modes)
- ✅ Wszystkie formaty audio są wykrywane (scenariusz 4)
- ✅ System volumes są ignorowane (scenariusz 5)
- ✅ Migracja działa poprawnie (scenariusz 6)
- ✅ Max depth działa (scenariusz 7)
- ✅ Brak crashy podczas testów
- ✅ Logi są czytelne i informatywne

---

**Powiązane dokumenty:**
- [PUBLIC-DISTRIBUTION-PLAN.md](../Docs/PUBLIC-DISTRIBUTION-PLAN.md) - Sekcja 5.2 (FAZA 1)
- [TESTING-GUIDE.md](../Docs/TESTING-GUIDE.md) - Ogólny przewodnik testowania

