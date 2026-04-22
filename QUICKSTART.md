# Malinche - Quick Start Guide

Szybki przewodnik uruchomienia w 5 minut.

## 📦 Wymagania

- macOS (Silicon zalecane dla Core ML)
- Python 3.8+
- ffmpeg (instalowany automatycznie)
- whisper.cpp (instalowany automatycznie)
- Olympus LS-P1 recorder
- **Opcjonalnie:** Anthropic API key dla podsumowań AI

## 🚀 Instalacja (6 kroków)

### 1. Przejdź do folderu projektu

```bash
cd ~/CODE/Olympus_transcription
```

### 2. Utwórz virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Zainstaluj zależności

```bash
make install
```

lub ręcznie:

```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 4. Zainstaluj whisper.cpp

```bash
bash scripts/install_whisper_cpp.sh
```

To pobierze, skompiluje i skonfiguruje whisper.cpp z Core ML (jeśli Apple Silicon).
Proces trwa 2-5 minut.

### 4.5. (Opcjonalnie) Skonfiguruj Claude API dla podsumowań

**Najprostszy sposób - plik .env:**

```bash
# Skopiuj przykładowy plik
cp .env.example .env

# Edytuj .env i dodaj swój klucz API
nano .env  # lub vim, code, etc.
```

W pliku `.env` dodaj:
```bash
ANTHROPIC_API_KEY=sk-ant-...
```

**Alternatywnie - zmienne środowiskowe:**

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

Lub dodaj do `~/.zshrc`:
```bash
echo 'export ANTHROPIC_API_KEY="sk-ant-..."' >> ~/.zshrc
source ~/.zshrc
```

**Bez API key:** System będzie działał, ale bez podsumowań AI (użyje prostych tytułów z nazwy pliku).

**Gdzie zdobyć klucz:** https://console.anthropic.com/

### 5. Test lokalny

**Opcja A: Tray App (Zalecane - z interfejsem graficznym)**

```bash
python src/menu_app.py
```

Aplikacja pojawi się w pasku menu macOS. Kliknij ikonę, aby zobaczyć status i opcje.

**Opcja B: Tryb daemon (CLI)**

```bash
make run
```

lub:

```bash
python src/main.py
```

**Oczekiwany output:**
```
🚀 Malinche starting...
✓ Found whisper.cpp at: /Users/username/whisper.cpp/main
✓ Found ffmpeg at: /opt/homebrew/bin/ffmpeg
✓ Core ML model found - GPU acceleration enabled
✓ FSEvents monitor started
✓ Periodic checker started
✓ All monitors running
⏳ Waiting for recorder connection...
```

Podłącz recorder - powinno pokazać:
```
📢 Detected recorder activity: /Volumes/LS-P1
✓ Recorder detected: /Volumes/LS-P1
📁 Found X new audio file(s)
🎙️  Starting transcription: recording.mp3
🔄 Attempting transcription with Core ML acceleration
✓ Transcription complete: recording.mp3
```

### 6. Skonfiguruj Full Disk Access (Wymagane dla daemona)

**⚠️ WAŻNE:** Daemon uruchomiony przez `launchd` lub jako aplikacja `.app` wymaga **Full Disk Access** aby móc odczytywać pliki z zewnętrznych dysków (rekorder Olympus).

**Szybka konfiguracja:**

1. Otwórz System Settings → Privacy & Security → **Full Disk Access**
2. Kliknij przycisk **"+"** (plus)
3. Naciśnij **Cmd + Shift + G** (Go to Folder)
4. Wklej: `~/Applications`
5. Wybierz **Malinche.app**
6. Kliknij **Open**
7. Upewnij się, że checkbox obok aplikacji jest **zaznaczony**

**Alternatywa:** Jeśli używasz ręcznego uruchomienia z Terminala, nie jest to wymagane (Terminal ma już pełny dostęp).

📖 **Szczegółowa instrukcja:** Zobacz [`Docs/FULL_DISK_ACCESS_SETUP.md`](Docs/FULL_DISK_ACCESS_SETUP.md)

### 7. Zainstaluj jako daemon

**Opcja A: Użyj aplikacji .app (Zalecane)**

Aplikacja `Malinche.app` została już utworzona w `~/Applications/`. 

**Automatyczne uruchamianie przy logowaniu:**
- System Settings → General → **Login Items**
- Upewnij się, że `Malinche.app` jest na liście

**Lub użyj LaunchAgent:**
```bash
make setup-daemon
```

**Opcja B: Ręczne uruchomienie**

```bash
open ~/Applications/Malinche.app
```

**Gotowe!** Aplikacja działa w tle i automatycznie uruchomi się przy następnym logowaniu.

---

## ✅ Weryfikacja

### Sprawdź status

```bash
make status
```

### Zobacz logi

```bash
make logs
```

### Testuj działanie

1. Podłącz Olympus LS-P1
2. Sprawdź logi:
   ```bash
   tail -f ~/Library/Logs/olympus_transcriber.log
   ```
3. Sprawdź transkrypcje:
   ```bash
   ls -la ~/Library/Mobile\ Documents/iCloud~md~obsidian/Documents/Obsidian/11-Transcripts/
   ```

---

## 📝 Format Wyjściowy

Transkrypcje są zapisywane jako pliki `.md` (markdown) w folderze Obsidian:
```
~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Obsidian/11-Transcripts/
```

**Nazwa pliku:** `YYYY-MM-DD_Tytul.md` (generowana z podsumowania AI)

**Struktura pliku:**
```markdown
---
title: "Rozmowa o projekcie"
date: 2025-11-19
recording_date: 2025-11-19T14:30:00
source: REC001.mp3
duration: 00:15:32
tags: [transcription]
---

## Podsumowanie

[Długie podsumowanie wygenerowane przez Claude AI...]

## Transkrypcja

[Pełna transkrypcja nagrania...]
```

Pliki są gotowe do użycia w Obsidian z pełnym frontmatter YAML.

**Uwaga:** Jeśli nie masz skonfigurowanego `ANTHROPIC_API_KEY`, system użyje prostych tytułów z nazwy pliku.

---

## 🔧 Przydatne komendy

```bash
# Makefile commands
make help           # Pokaż wszystkie komendy
make test           # Uruchom testy
make lint           # Sprawdź kod
make format         # Formatuj kod
make stop-daemon    # Zatrzymaj daemon
make reload-daemon  # Przeładuj daemon
make logs           # Zobacz logi
make clean          # Wyczyść cache

# Bezpośrednie komendy
python src/main.py  # Uruchom lokalnie
pytest tests/ -v    # Uruchom testy
```

---

## 📂 Kluczowe lokalizacje

| Co | Gdzie |
|----|-------|
| Transkrypcje | Obsidian vault `11-Transcripts` |
| Logi aplikacji | `~/Library/Logs/olympus_transcriber.log` |
| Plik stanu | `~/.olympus_transcriber_state.json` |
| LaunchAgent plist | `~/Library/LaunchAgents/com.user.olympus-transcriber.plist` |
| Logi LaunchAgent | `/tmp/olympus-transcriber-out.log` |

---

## 🐛 Troubleshooting

### whisper.cpp nie znaleziony

```bash
# Zainstaluj whisper.cpp
bash scripts/install_whisper_cpp.sh

# Sprawdź instalację
~/whisper.cpp/main -h

# Jeśli nie działa, sprawdź ścieżkę w config.py
ls ~/whisper.cpp/main
```

### Recorder nie wykrywa się

```bash
# Sprawdź czy zamontowany
ls /Volumes/

# Uruchom lokalnie z logami debug
python src/main.py
```

### Daemon nie startuje

```bash
# Sprawdź błędy
cat /tmp/olympus-transcriber-err.log

# Przeładuj
make reload-daemon

# Sprawdź status
launchctl list | grep olympus
```

### Whisper zgłasza błąd Metal (-6)

Od wersji 1.7.1 aplikacja automatycznie wykrywa komunikaty typu
`ggml_metal_device_init: tensor API disabled` i uruchamia ponownie
transkrypcję w trybie CPU. Jeśli chcesz całkowicie wyłączyć Core ML:

```bash
export WHISPER_COREML=0
python -m src.main
```

### Proces zablokowany przez lock file

Jeżeli w logach pojawia się komunikat
`Skipping process_recorder because another instance holds lock`, oznacza to,
że inna instancja wciąż działa lub zostawiła plik blokady.

```bash
ls ~/.olympus_transcriber/transcriber.lock
rm ~/.olympus_transcriber/transcriber.lock  # tylko gdy masz pewność, że daemon nie działa
```

### Testy nie przechodzą

```bash
# Zainstaluj dev dependencies
pip install -r requirements-dev.txt

# Uruchom z verbose
pytest tests/ -v -s
```

---

## 📚 Dodatkowa dokumentacja

- `README.md` - Pełna dokumentacja projektu
- `Docs/ARCHITECTURE.md` - Architektura systemu
- `Docs/DEVELOPMENT.md` - Guide dla developerów
- `Docs/TESTING-GUIDE.md` - Szczegółowy guide testowania
- `Docs/API.md` - Dokumentacja API
- `CHANGELOG.md` - Historia zmian

---

## 🎯 Następne kroki

1. ✅ Zainstaluj i przetestuj lokalnie
2. ✅ Zainstaluj jako daemon
3. ✅ Podłącz recorder i zweryfikuj
4. 📖 Przeczytaj `DEVELOPMENT.md` dla advanced usage
5. 🔧 Dostosuj konfigurację w `src/config.py` jeśli potrzeba
6. 🧪 Uruchom testy: `make test`

---

## 💡 Wskazówki

- **Pierwsze uruchomienie**: Wszystkie pliki z ostatnich 7 dni będą transkrybowane
- **Kolejne podłączenia**: Tylko nowe pliki od ostatniego podłączenia
- **Timeout**: Transkrypcja ma 30 minut timeout
- **State file**: Usuń `~/.olympus_transcriber_state.json` aby zresetować historię
- **Logi**: Zawsze sprawdzaj logi przy problemach

---

## ✨ Gotowe do użycia!

Podłącz swój Olympus LS-P1 i ciesz się automatycznymi transkrypcjami! 🎉

---

## Multi-Mac (iCloud Vault)

- Umieść `TRANSCRIBE_DIR` w iCloud (`~/Library/Mobile Documents/...`).
- Malinche zapisuje dedup index w `.malinche/index.json` wewnątrz Vault.
- Gdy drugi Mac zobaczy ten sam plik audio, fingerprint zostanie wykryty i plik zostanie pominięty.
- W FREE działa dedup/skip. W PRO dostępna jest wersjonowana retranskrypcja (`.v2.md`, `.v3.md`).

