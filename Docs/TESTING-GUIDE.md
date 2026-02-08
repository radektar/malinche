# Testing Guide

> **Wersja:** v2.0.0 (w przygotowaniu)
>
> **Powiązane dokumenty:**
> - [README.md](../README.md) - Przegląd projektu
> - [DEVELOPMENT.md](DEVELOPMENT.md) - Przewodnik deweloperski
> - [API.md](API.md) - Dokumentacja API modułów
> - [PUBLIC-DISTRIBUTION-PLAN.md](PUBLIC-DISTRIBUTION-PLAN.md) - Strategia testowania per faza

Comprehensive guide for testing Malinche.

## 📋 Test Types

| Typ | Narzędzie | Kiedy uruchamiać |
|-----|-----------|------------------|
| **Unit Tests** | pytest | Każdy commit |
| **Integration Tests** | pytest + fixtures | Przed merge do develop |
| **E2E Tests** | Manual / scripts | Przed release |
| **Beta Testing** | External users | Przed v2.0.0 release |

---

## 🎯 Testy v2.0.0 - Nowe moduły

### Testy dla nowych funkcji

| Moduł | Plik testowy | Status |
|-------|--------------|--------|
| `UserSettings` | `tests/test_settings.py` | 🆕 Do utworzenia |
| `DependencyDownloader` | `tests/test_downloader.py` | 🆕 Do utworzenia |
| `SetupWizard` | `tests/test_wizard.py` | 🆕 Do utworzenia |
| `FeatureFlags` | `tests/test_features.py` | 🆕 Do utworzenia |
| `LicenseManager` | `tests/test_license.py` | 🆕 Do utworzenia |
| Universal volume detection | `tests/test_file_monitor.py` | 📝 Do rozszerzenia |

### Uruchamianie testów v2.0.0

```bash
# Wszystkie nowe testy
pytest tests/test_settings.py tests/test_downloader.py tests/test_wizard.py -v

# Testy feature flags (freemium)
pytest tests/test_features.py tests/test_license.py -v

# Testy z coverage dla nowych modułów
pytest tests/ --cov=src/config --cov=src/setup --cov-report=html
```

---

## 🧪 Unit Tests

### Setup

```bash
cd ~/CODEing/transrec  # lub twoja ścieżka do projektu
source venv/bin/activate
pip install -r requirements-dev.txt
```

### Running Tests

```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/test_config.py -v

# Specific test function
pytest tests/test_transcriber.py::test_find_recorder_found -v

# With coverage
pytest tests/ --cov=src --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Test Structure

```
tests/
├── __init__.py
├── test_config.py        # Configuration tests
├── test_transcriber.py   # Transcriber logic tests
└── test_file_monitor.py  # FSEvents monitor tests
```

### Expected Results

All tests should pass:

```
========================= test session starts ==========================
tests/test_config.py::test_config_initialization PASSED          [ 16%]
tests/test_config.py::test_config_paths PASSED                   [ 33%]
tests/test_config.py::test_config_audio_extensions PASSED        [ 50%]
tests/test_transcriber.py::test_transcriber_initialization PASSED [ 66%]
tests/test_transcriber.py::test_find_audio_files PASSED          [ 83%]
tests/test_transcriber.py::test_stage_audio_file_success PASSED [ 90%]
tests/test_transcriber.py::test_process_recorder_batch_failure_handling PASSED [100%]
tests/test_file_monitor.py::test_file_monitor_start PASSED       [100%]

========================= 8 passed in 2.50s ============================
```

### Staging Tests

The staging functionality ensures files are copied to a local directory before transcription, making the process robust to recorder unmounting:

**Test: Staging Success**
```bash
pytest tests/test_transcriber.py::test_stage_audio_file_success -v
```

**Test: Staging Failure Handling**
```bash
pytest tests/test_transcriber.py::test_stage_audio_file_not_found -v
```

**Test: Batch Failure Logic**
```bash
pytest tests/test_transcriber.py::test_process_recorder_batch_failure_handling -v
```

These tests verify:
- Files are correctly copied to `LOCAL_RECORDINGS_DIR`
- Existing staged copies are reused when appropriate
- `last_sync` is not updated if any file in batch fails
- Staging failures are handled gracefully

---

## 🔄 Integration Tests

### Prerequisites

1. MacWhisper installed
2. Olympus LS-P1 recorder available
3. Test audio files on recorder

### Test Scenarios

#### Scenario 1: First Time Setup

**Steps:**
1. Remove state file if exists:
   ```bash
   rm ~/.olympus_transcriber_state.json
   ```

2. Remove old transcriptions:
   ```bash
   rm -rf ~/Documents/Transcriptions/*
   ```

3. Start application:
   ```bash
   source venv/bin/activate
   python src/main.py
   ```

4. Connect Olympus LS-P1

**Expected Behavior:**
- ✓ Application starts without errors
- ✓ Logs show "Waiting for recorder..."
- ✓ Recorder is detected when connected
- ✓ All audio files are found and transcribed
- ✓ Transcriptions appear in ~/Documents/Transcriptions/
- ✓ State file is created with current timestamp

**Verify:**
```bash
# Check logs
tail -f ~/Library/Logs/olympus_transcriber.log

# Check transcriptions
ls -la ~/Documents/Transcriptions/

# Check state
cat ~/.olympus_transcriber_state.json
```

#### Scenario 2: Subsequent Connections

**Steps:**
1. Application running from Scenario 1
2. Add new audio file to recorder
3. Connect recorder again

**Expected Behavior:**
- ✓ Only new file is transcribed
- ✓ Old files are skipped
- ✓ State file is updated

**Verify:**
```bash
# Should show "Already transcribed: old_file.txt"
tail -20 ~/Library/Logs/olympus_transcriber.log

# Should only have new transcription
ls -lt ~/Documents/Transcriptions/ | head -5
```

#### Scenario 3: Graceful Shutdown

**Steps:**
1. Application running
2. Press Ctrl+C

**Expected Behavior:**
- ✓ Logs show "Shutting down..."
- ✓ FSEvents monitor stops
- ✓ Application exits cleanly

**Verify:**
```bash
# Should show shutdown message
tail -5 ~/Library/Logs/olympus_transcriber.log
```

#### Scenario 4: Timeout Protection

**Steps:**
1. Create very large audio file (> 30 min of audio)
2. Connect recorder
3. Wait for transcription

**Expected Behavior:**
- ✓ Transcription starts
- ✓ After 30 minutes, timeout triggers
- ✓ Error logged
- ✓ Next file is processed

**Verify:**
```bash
# Should show timeout error
grep "timeout" ~/Library/Logs/olympus_transcriber.log
```

#### Scenario 5: No New Files

**Steps:**
1. Connect recorder with no new files
2. Check behavior

**Expected Behavior:**
- ✓ Recorder detected
- ✓ No files found
- ✓ State updated
- ✓ No errors

**Verify:**
```bash
# Should show "No new files"
tail -20 ~/Library/Logs/olympus_transcriber.log
```

---

## 🚀 LaunchAgent Tests

### Test 1: Installation

```bash
cd ~/CODE/Olympus_transcription
chmod +x setup.sh
./setup.sh
```

**Expected Output:**
```
================================================
  Malinche - LaunchAgent Setup
================================================

✓ Python 3 found: /usr/bin/python3
✓ Main script found
✓ Created: ~/Documents/Transcriptions
✓ Created: ~/Library/Logs
✓ Created: ~/Library/LaunchAgents
✓ Virtual environment found
✓ Created: ~/Library/LaunchAgents/com.user.olympus-transcriber.plist
✓ LaunchAgent loaded and running
✓ Installation Complete!
```

**Verify:**
```bash
launchctl list | grep olympus-transcriber
# Should show: PID  Status  Label
```

### Test 2: Auto-Start on Boot

**Steps:**
1. Restart computer
2. Wait for system to boot
3. Check if daemon is running

**Verify:**
```bash
launchctl list | grep olympus-transcriber
tail -20 ~/Library/Logs/olympus_transcriber.log
```

**Expected:**
- ✓ Daemon is running
- ✓ Logs show startup

### Test 3: Persistent Operation

**Steps:**
1. Let daemon run for 24 hours
2. Connect recorder multiple times
3. Check logs for issues

**Verify:**
```bash
# Check for errors
grep ERROR ~/Library/Logs/olympus_transcriber.log

# Check for crashes
grep -i "fatal\|crash\|exception" /tmp/olympus-transcriber-err.log

# Check memory usage
ps aux | grep olympus_transcriber
```

**Expected:**
- ✓ No errors
- ✓ No crashes
- ✓ Memory usage stable (<200MB)

### Test 4: Reload After Code Update

**Steps:**
1. Update code in src/
2. Reload LaunchAgent:
   ```bash
   launchctl unload ~/Library/LaunchAgents/com.user.olympus-transcriber.plist
   launchctl load ~/Library/LaunchAgents/com.user.olympus-transcriber.plist
   ```

**Expected:**
- ✓ Old process terminates
- ✓ New process starts
- ✓ No data loss

**Verify:**
```bash
cat ~/.olympus_transcriber_state.json
# Should still have last_sync timestamp
```

---

## 🐛 Error Scenarios

### Test 1: MacWhisper Not Installed

**Setup:**
```bash
# Temporarily rename MacWhisper
sudo mv /Applications/MacWhisper.app /Applications/MacWhisper.app.bak
```

**Run:**
```bash
python src/main.py
```

**Expected:**
- ✓ Warning logged: "MacWhisper not found"
- ✓ Application continues running
- ✓ Recorder detection works
- ✓ Transcription is skipped with error

**Restore:**
```bash
sudo mv /Applications/MacWhisper.app.bak /Applications/MacWhisper.app
```

### Test 2: Corrupted State File

**Setup:**
```bash
echo "invalid json" > ~/.olympus_transcriber_state.json
```

**Run:**
```bash
python src/main.py
```

**Expected:**
- ✓ Error reading state logged
- ✓ Falls back to 7 days ago
- ✓ Application continues

**Verify:**
```bash
# State file should be regenerated on next sync
cat ~/.olympus_transcriber_state.json
```

### Test 3: Full Disk

**Setup:**
```bash
# Create nearly full disk scenario (carefully!)
# This is advanced - skip if unsure
```

**Expected:**
- ✓ Error logged
- ✓ Application continues
- ✓ Retry on next connection

### Test 4: Recorder Disconnected During Transcription

**Steps:**
1. Start transcription of large file
2. Disconnect recorder mid-transcription

**Expected:**
- ✓ Transcription fails
- ✓ Error logged
- ✓ No partial file created
- ✓ Next connection retries

---

## 📊 Performance Tests

### Test 1: Multiple Files

**Setup:**
- 50+ audio files on recorder
- Various sizes (1MB - 100MB)

**Measure:**
```bash
# Start time
start_time=$(date +%s)

# Connect recorder and wait for completion
# Watch logs

# End time
end_time=$(date +%s)

# Calculate
echo "Duration: $((end_time - start_time)) seconds"
```

**Expected:**
- ✓ All files processed
- ✓ Reasonable time per file
- ✓ No memory leaks

### Test 2: Large File

**Setup:**
- Single 500MB audio file (3+ hours)

**Expected:**
- ✓ Transcription starts
- ✓ Progress visible in logs
- ✓ Completes within timeout

### Test 3: Rapid Connect/Disconnect

**Steps:**
1. Connect recorder
2. Wait 2 seconds
3. Disconnect
4. Repeat 10 times

**Expected:**
- ✓ No crashes
- ✓ Debouncing prevents duplicate processing
- ✓ Logs show proper detection

---

## ✅ Test Checklist

### Before Release

- [ ] All unit tests pass
- [ ] All integration scenarios pass
- [ ] LaunchAgent installs successfully
- [ ] Auto-start on boot works
- [ ] MacWhisper integration works
- [ ] State management persists
- [ ] Error handling is graceful
- [ ] Logs are comprehensive
- [ ] Performance is acceptable
- [ ] Documentation is complete

### After Each Update

- [ ] Run unit tests
- [ ] Test basic transcription
- [ ] Check logs for errors
- [ ] Verify state file integrity
- [ ] Test LaunchAgent reload

---

## 🔍 Debugging Tests

### Enable Debug Logging

```python
# In src/logger.py, temporarily change:
logger.setLevel(logging.DEBUG)
```

### Watch Logs in Real-Time

```bash
# Application log
tail -f ~/Library/Logs/olympus_transcriber.log

# LaunchAgent stdout
tail -f /tmp/olympus-transcriber-out.log

# LaunchAgent stderr
tail -f /tmp/olympus-transcriber-err.log
```

### Inspect State

```bash
# View state file
cat ~/.olympus_transcriber_state.json | python -m json.tool

# Check last modification
ls -la ~/.olympus_transcriber_state.json
```

### Check Process

```bash
# Find process
ps aux | grep olympus_transcriber

# Monitor resources
top -pid <PID>
```

---

## 📝 Test Reporting

### Create Test Report

```bash
# Run tests with output
pytest tests/ -v --tb=short > test_report.txt 2>&1

# Add system info
echo "\nSystem Info:" >> test_report.txt
sw_vers >> test_report.txt
python --version >> test_report.txt

# Add MacWhisper version
echo "\nMacWhisper:" >> test_report.txt
/Applications/MacWhisper.app/Contents/MacOS/MacWhisper --version >> test_report.txt

# View report
cat test_report.txt
```

---

## 🎯 Success Criteria

All tests pass if:

✓ Unit tests: 100% passing
✓ Integration tests: All scenarios work as expected
✓ LaunchAgent: Installs and runs reliably
✓ Performance: Acceptable transcription times
✓ Stability: No crashes during 24h test
✓ Errors: Graceful handling, good logging
✓ Documentation: Complete and accurate

---

## 🚨 Common Issues

### FSEvents Not Triggering

**Symptom:** Recorder connected but not detected

**Debug:**
```bash
# Check FSEvents
fs_usage | grep Volumes

# Check manual detection
ls /Volumes/
```

**Fix:** Periodic checker should catch it within 30s

### Transcription Never Completes

**Symptom:** Hangs indefinitely

**Debug:**
```bash
# Check MacWhisper process
ps aux | grep MacWhisper

# Check timeout setting
grep TRANSCRIPTION_TIMEOUT src/config.py
```

**Fix:** Verify timeout is set, kill hanging process

### State File Issues

**Symptom:** All files re-transcribed

**Debug:**
```bash
# Check state file
cat ~/.olympus_transcriber_state.json

# Check permissions
ls -la ~/.olympus_transcriber_state.json
```

**Fix:** Ensure state file is writable

---

For more troubleshooting, see `DEVELOPMENT.md` and application logs.

---

## 🚀 Testy v2.0.0 - E2E Scenarios

### Scenario: Fresh Install (v2.0.0)

**Cel:** Weryfikacja pełnego flow dla nowego użytkownika.

**Setup:**
- Czysty macOS (VM lub nowy użytkownik)
- Brak poprzedniej instalacji Malinche
- Brak whisper.cpp

**Kroki:**
1. Pobierz DMG z GitHub Releases
2. Otwórz DMG, przeciągnij Malinche.app do Applications
3. Uruchom Malinche.app
4. Przejdź przez First-Run Wizard
5. Poczekaj na pobranie whisper.cpp + model
6. Nadaj Full Disk Access
7. Podłącz recorder z plikami audio
8. Poczekaj na transkrypcję

**Expected:**
- [ ] DMG otwiera się bez ostrzeżeń Gatekeeper
- [ ] Wizard uruchamia się automatycznie
- [ ] Pobieranie pokazuje progress bar
- [ ] Instrukcje FDA są jasne
- [ ] Recorder wykrywany automatycznie
- [ ] Transkrypcja działa poprawnie
- [ ] Plik .md utworzony w output dir

**Czas:** ~10-15 minut (z pobieraniem modelu)

---

### Scenario: Universal Volume Detection (v2.0.0)

**Cel:** Weryfikacja wykrywania różnych urządzeń.

> 📖 **Szczegółowy przewodnik:** Zobacz [MANUAL_TESTING_PHASE_1.md](../tests/MANUAL_TESTING_PHASE_1.md) dla pełnego scenariusza testowego z krokami, komendami i checklistą.

**Urządzenia do testu:**
| Urządzenie | Status | Uwagi |
|------------|--------|-------|
| Olympus LS-P1 | [ ] | Legacy support |
| Zoom H1/H6 | [ ] | Popular recorder |
| Generic SD card | [ ] | Z plikami .mp3 |
| USB flash drive | [ ] | Z plikami .wav |
| iPhone (jako dysk) | [ ] | DCIM folder |
| Empty USB drive | [ ] | NIE powinien być wykryty |

**Quick test steps:**
1. Podłącz urządzenie
2. Sprawdź log: czy wykryte?
3. Jeśli ma audio - czy transkrypcja startuje?
4. Odłącz i podłącz ponownie

**Watch modes do przetestowania:**
- [ ] **"auto"** - automatyczne wykrywanie urządzeń z audio
- [ ] **"specific"** - tylko urządzenia z listy `watched_volumes`
- [ ] **"manual"** - brak auto-detekcji

---

### Scenario: Freemium Flow (v2.0.0)

**Cel:** Weryfikacja FREE vs PRO features.

**Test FREE:**
1. Uruchom bez licencji PRO
2. Wykonaj transkrypcję
3. Sprawdź: AI summaries = disabled
4. Sprawdź: AI tags = disabled
5. Sprawdź: podstawowe tagi działają
6. Kliknij "Upgrade to PRO"
7. Sprawdź: otwiera się strona zakupu

**Test PRO (symulacja):**
1. Aktywuj testową licencję
2. Sprawdź: AI summaries = enabled
3. Wykonaj transkrypcję
4. Sprawdź: summary w pliku .md
5. Sprawdź: AI tags w pliku .md

---

### Scenario: Offline Mode (v2.0.0)

**Cel:** Aplikacja działa bez internetu.

**Kroki:**
1. Wyłącz internet
2. Uruchom Malinche (z już pobranym whisper)
3. Podłącz recorder
4. Wykonaj transkrypcję

**Expected:**
- [ ] Transkrypcja działa (lokalna)
- [ ] AI features graceful fail (log warning)
- [ ] License check używa cache

---

## 📋 Beta Testing Checklist (v2.0.0)

### Przed wysłaniem do beta testerów:

- [ ] Wszystkie unit tests pass
- [ ] Build script działa
- [ ] Notaryzacja przeszła
- [ ] DMG testowane na czystym systemie
- [ ] README zaktualizowane
- [ ] Known issues udokumentowane

### Instrukcje dla beta testerów:

```markdown
## Beta Test Instructions

1. Download: [link do DMG]
2. Install: Drag to Applications
3. Run: Double-click Malinche.app
4. Complete wizard
5. Connect your recorder
6. Report issues: [link do GitHub Issues]

### What to test:
- [ ] Installation smooth?
- [ ] Wizard understandable?
- [ ] Your recorder detected?
- [ ] Transcription works?
- [ ] Any crashes?

### Feedback form:
[link do Google Form]
```

### Po beta testingu:

- [ ] Wszystkie critical bugs naprawione
- [ ] Feedback zebrano
- [ ] Release notes napisane
- [ ] Tag v2.0.0 utworzony

---

> **Powiązane dokumenty:**
> - [PUBLIC-DISTRIBUTION-PLAN.md](PUBLIC-DISTRIBUTION-PLAN.md) - Pełna strategia testowania per faza
> - [DEVELOPMENT.md](DEVELOPMENT.md) - Przewodnik deweloperski
> - [CHANGELOG.md](../CHANGELOG.md) - Historia zmian





