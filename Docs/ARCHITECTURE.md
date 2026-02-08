# System Architecture

> **Wersja:** v2.0.0 (w przygotowaniu)
> 
> **Powiązane dokumenty:**
> - [README.md](../README.md) - Przegląd projektu
> - [API.md](API.md) - Dokumentacja API modułów
> - [DEVELOPMENT.md](DEVELOPMENT.md) - Przewodnik deweloperski
> - [PUBLIC-DISTRIBUTION-PLAN.md](PUBLIC-DISTRIBUTION-PLAN.md) - Plan dystrybucji

## Overview

Malinche to system automatycznie transkrybujący pliki audio z dowolnego dysku zewnętrznego (rekorder, karta SD, pendrive).

```
┌─────────────────────────────────────────────────────────────────┐
│                        macOS System                              │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Menu Bar App (src/menu_app.py)                            │ │
│  │  - rumps-based native macOS interface                      │ │
│  │  - Status display & user actions                           │ │
│  └───────────────────┬────────────────────────────────────────┘ │
│                      │                                           │
│  ┌───────────────────┴────────────────────────────────────────┐ │
│  │  App Core (src/app_core.py)                                │ │
│  │  - Thread-safe state management                            │ │
│  │  - Orchestrates monitoring & transcription                 │ │
│  └───────────────────┬────────────────────────────────────────┘ │
│                      │                                           │
│  ┌───────────────────┴────────────────────────────────────────┐ │
│  │  FSEvents Monitor (src/file_monitor.py)                    │ │
│  │  - Watches /Volumes for mount events                       │ │
│  │  - Detects ANY external volume with audio files            │ │
│  └───────────────────┬────────────────────────────────────────┘ │
│                      │ (onChange callback)                       │
│  ┌───────────────────┴────────────────────────────────────────┐ │
│  │  Transcriber Engine (src/transcriber.py)                   │ │
│  │  - Scans for new audio files                               │ │
│  │  - Stages files locally before processing                  │ │
│  │  - Manages transcription queue                             │ │
│  └───────────────────┬────────────────────────────────────────┘ │
│                      │                                           │
│  ┌───────────────────┴────────────────────────────────────────┐ │
│  │  whisper.cpp Engine                                        │ │
│  │  - Native binary with Core ML acceleration                 │ │
│  │  - Runs as subprocess with timeout protection              │ │
│  └───────────────────┬────────────────────────────────────────┘ │
│                      │                                           │
│  ┌───────────────────┴────────────────────────────────────────┐ │
│  │  Markdown Generator (src/markdown_generator.py)            │ │
│  │  - Creates .md files with YAML frontmatter                 │ │
│  │  - Formats transcription output                            │ │
│  └───────────────────┬────────────────────────────────────────┘ │
│                      │                                           │
│                      ▼                                           │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Output: TRANSCRIBE_DIR (configurable)                     │ │
│  │  - YYYY-MM-DD_Title.md files                               │ │
│  │  - Ready for Obsidian/other markdown editors               │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  State Management (src/state_manager.py)                   │ │
│  │  - ~/.transrec_state.json                                  │ │
│  │  - Tracks processed files per volume                       │ │
│  │  - Prevents duplicate transcriptions                       │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Logging (~/Library/Logs/transrec.log)                     │ │
│  │  - All events logged with timestamps                       │ │
│  │  - Configurable log level                                  │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Component Breakdown

### 1. Menu Bar App (`src/menu_app.py`)

**Odpowiedzialność:** Interfejs użytkownika w pasku menu macOS

```python
OlympusMenuApp (rumps.App)
├── title              # Status icon/text
├── menu               # Dropdown menu items
├── status_item()      # Current status display
├── open_logs()        # Open log file
├── reset_memory()     # Reset state
├── settings()         # Open settings window
└── quit()             # Clean shutdown
```

**Technologia:** `rumps` - Python library for macOS menu bar apps

### 2. App Core (`src/app_core.py`)

**Odpowiedzialność:** Koordynacja wszystkich komponentów

```python
OlympusTranscriber
├── state: AppState           # Thread-safe state container
├── transcriber: Transcriber  # Transcription engine
├── monitor: FileMonitor      # FSEvents monitor
├── start()                   # Start all components
├── stop()                    # Clean shutdown
└── get_status()              # Current status for UI
```

**AppState:**
- `IDLE` - Oczekiwanie na dysk
- `SCANNING` - Skanowanie plików
- `TRANSCRIBING` - Transkrypcja w toku
- `ERROR` - Błąd

### 3. FSEvents Monitor (`src/file_monitor.py`)

**Odpowiedzialność:** Wykrywanie podłączenia dysków zewnętrznych

```python
FileMonitor
├── start()           # Start monitoring /Volumes
├── stop()            # Stop monitoring
├── on_change()       # Callback on volume change
└── _should_process_volume()  # Check if volume has audio
```

**Mechanizm (v2.0.0):**
- Monitoruje `/Volumes` przez FSEvents
- Wykrywa KAŻDY nowy dysk zewnętrzny
- Sprawdza czy zawiera pliki audio
- Czeka 2 sekundy na pełny mount
- Uruchamia callback jeśli znaleziono audio

**Ignorowane katalogi:**
- `.Spotlight-V100`, `.fseventsd`, `.Trashes`
- Wewnętrzne dyski systemowe

### 4. Transcriber Engine (`src/transcriber.py`)

**Odpowiedzialność:** Proces transkrypcji

```python
Transcriber
├── find_audio_files()        # Scan volume for audio
├── _stage_audio_file()       # Copy to local staging
├── transcribe_file()         # Run whisper.cpp
├── process_volume()          # Main workflow
└── on_status_change          # Callback for UI updates
```

**Staging Workflow:**
1. Kopiuj plik z dysku do `~/.transrec/recordings/`
2. Transkrypuj lokalną kopię (bezpieczne odmontowanie)
3. Generuj markdown output
4. Aktualizuj state

### 5. Markdown Generator (`src/markdown_generator.py`)

**Odpowiedzialność:** Tworzenie plików .md

```python
MarkdownGenerator
├── generate()                # Create markdown file
├── _format_frontmatter()     # YAML frontmatter
└── _format_content()         # Transcription content
```

**Output format:**
```markdown
---
source: recording.mp3
date: 2025-01-15
duration: 5:32
tags: []
---

# Transkrypcja

[treść transkrypcji]
```

### 6. State Manager (`src/state_manager.py`)

**Odpowiedzialność:** Persystencja stanu (przetworzone pliki)

### 7. License Manager (`src/config/license.py`)

**Odpowiedzialność:** Zarządzanie licencją i dostępem do funkcji PRO

```python
LicenseManager
├── get_current_tier()        # FREE / PRO / PRO_ORG
├── get_features()            # Zwraca FeatureFlags
├── activate_license()        # Aktywacja klucza
└── get_usage_limits()        # Limity minut (PRO Individual)
```

---

## v2.0.0 Architecture Changes

### Universal Volume Detection

**Przed (v1.x):**
```python
# Hardcoded recorder names
RECORDER_NAMES = ["LS-P1", "OLYMPUS"]
if volume_name in RECORDER_NAMES:
    process()
```

**Po (v2.0.0):**
```python
# Any external volume with audio files
def _should_process_volume(volume_path: Path) -> bool:
    if _is_internal_volume(volume_path):
        return False
    return _has_audio_files(volume_path)
```

### Feature Flags (Freemium)

**Struktura (v2.0.0):**
```python
from src.config.features import FeatureTier, FeatureFlags

# Tiery: FREE, PRO (Individual), PRO_ORG (Organization)
# Flagi: ai_summaries, ai_smart_tags, speaker_diarization, domain_lexicon, knowledge_base
```

**Użycie:**
```python
from src.config.license import license_manager

features = license_manager.get_features()
if features.ai_summaries:
    # Użyj funkcji PRO
```

### PRO Features Architecture (v2.1.0+)

Aplikacja kliencka Malinche integruje się z backendem dla funkcji wymagających dużych modeli AI (Claude) oraz zarządzania licencjami i limitami użycia.

1.  **PRO Individual (Monthly Subscription):** AI Summaries, AI Tags, Diarization (z miesięcznymi limitami minut).
2.  **PRO Organization (Monthly Subscription):** Współdzielona baza rozmówców, słownik dziedzinowy, baza wiedzy.

```
┌─────────────────────────────────────────────────────────────────┐
│                     PRO Features (v2.1.0)                        │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  License Manager (src/config/license.py)                   │ │
│  │  - Verify license with backend                             │ │
│  │  - Cache locally (7 days offline)                          │ │
│  │  - Feature gate checking                                   │ │
│  └───────────────────┬────────────────────────────────────────┘ │
│                      │                                           │
│  ┌───────────────────┴────────────────────────────────────────┐ │
│  │  Summarizer (src/summarizer.py)                            │ │
│  │  - Generate AI summaries via backend API                   │ │
│  │  - Feature flag: ai_summaries                              │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Tagger (src/tagger.py)                                    │ │
│  │  - Auto-generate tags via backend API                      │ │
│  │  - Feature flag: ai_smart_tags                             │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  transrec-backend (private repo)                 │
│                                                                  │
│  FastAPI Server                                                  │
│  ├── POST /api/v1/summarize      # AI summaries                 │
│  ├── POST /api/v1/tags           # Auto-tagging                 │
│  ├── POST /api/v1/license/verify # License check                │
│  └── POST /api/v1/license/activate # Activation                 │
└─────────────────────────────────────────────────────────────────┘
```

## Configuration (`src/config/config.py`)

Centralized configuration with environment variable support (only during migration):

```python
@dataclass
class Config:
    # Paths
    TRANSCRIBE_DIR: Path          # Output directory
    LOCAL_RECORDINGS_DIR: Path    # Staging directory
    STATE_FILE: Path              # State persistence
    LOG_FILE: Path                # Log file
    
    # whisper.cpp
    WHISPER_CPP_PATH: Path        # Binary path
    WHISPER_CPP_MODELS_DIR: Path  # Models directory
    WHISPER_MODEL: str            # Model size (tiny/base/small/medium/large)
    WHISPER_LANGUAGE: str         # Transcription language
    
    # Timeouts
    TRANSCRIPTION_TIMEOUT: int    # Max transcription time (seconds)
    MOUNT_MONITOR_DELAY: int      # Wait after mount (seconds)
    
    # Audio
    AUDIO_EXTENSIONS: set         # Supported formats
```

**Note:** Configuration has been refactored for better determinism and testability:
- Migration is executed only once during application startup (`src/main.py`)
- `Config` does not perform side effects during initialization
- `Transcriber` uses dependency injection for config (better testability)

Details: **[API.md](API.md#configpy)**

## Error Handling

### Graceful Degradation

1. **whisper.cpp nie znaleziony** → Pobierz przy pierwszym uruchomieniu
2. **Timeout transkrypcji** → Log error, pomiń plik, kontynuuj
3. **State file corrupted** → Reset to 7 days ago
4. **FSEvents fails** → Fallback na periodic checking
5. **PRO license invalid** → Continue with FREE features only

### Retry Strategy

- Każde podłączenie dysku = nowa próba dla nieprzetłumaczonych plików
- `last_sync` aktualizowany tylko jeśli WSZYSTKIE pliki succeeded
- Failed files pozostają w kolejce do następnej synchronizacji

## Performance

### Resource Usage
- **RAM:** ~50-100 MB (idle) + whisper.cpp (~500MB-2GB during transcription)
- **CPU:** Minimal during idle, ~80-100% during transcription
- **Disk:** Staging + output (temporary + permanent)

### Optimizations
- FSEvents = zero-polling overhead
- Core ML acceleration on Apple Silicon
- Sequential processing (one file at a time)
- State file prevents re-processing

## Security

- No credentials in code
- API keys via environment variables only
- Local state file (no cloud sync in FREE)
- whisper.cpp runs locally (no cloud)
- License verification cached locally

---

> **Powiązane dokumenty:**
> - [README.md](../README.md) - Przegląd projektu
> - [API.md](API.md) - Dokumentacja API modułów
> - [DEVELOPMENT.md](DEVELOPMENT.md) - Przewodnik deweloperski
> - [PUBLIC-DISTRIBUTION-PLAN.md](PUBLIC-DISTRIBUTION-PLAN.md) - Plan dystrybucji v2.0.0
