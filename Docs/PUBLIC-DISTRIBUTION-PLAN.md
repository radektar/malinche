# 📦 Plan Dystrybucji Publicznej - Malinche

**Wersja:** 1.1 (Freemium)  
**Data utworzenia:** 2025-12-17  
**Ostatnia aktualizacja:** 2025-12-17  
**Status:** DRAFT - Do zatwierdzenia  
**Model:** Freemium (FREE open-source + PRO płatne)

---

## 📋 Spis treści

1. [Podsumowanie wykonawcze](#1-podsumowanie-wykonawcze)
2. [Decyzje strategiczne](#2-decyzje-strategiczne)
3. [Architektura docelowa](#3-architektura-docelowa)
4. [Plan implementacji - Fazy](#4-plan-implementacji---fazy)
5. [Strategia testowania](#5-strategia-testowania)
6. [Szczegóły techniczne](#6-szczegóły-techniczne)
7. [Harmonogram i kamienie milowe](#7-harmonogram-i-kamienie-milowe)
8. [Ryzyka i mitygacja](#8-ryzyka-i-mitygacja)
9. [Koszty](#9-koszty)
10. [Kryteria sukcesu](#10-kryteria-sukcesu)
11. [Strategia Git i repozytoria](#11-strategia-git-i-repozytoria)
12. [Następne kroki](#12-następne-kroki)
13. [Podsumowanie modelu Freemium](#13-podsumowanie-modelu-freemium)

---

## 1. Podsumowanie wykonawcze

### Cel projektu

Przekształcenie Malinche z narzędzia developerskiego w aplikację gotową do publicznej dystrybucji, z:
- Prostą instalacją (drag & drop do Applications)
- Wsparciem dla dowolnego recordera/karty SD
- Profesjonalnym UX (code signing, notaryzacja)
- Automatycznym pobieraniem zależności (whisper.cpp)
- **Modelem Freemium** (FREE + PRO)

### Model biznesowy

| Wersja | Cena | Funkcje |
|--------|------|---------|
| **FREE** | $0 (open source) | Transkrypcja lokalna, eksport MD, dowolne recordery |
| **PRO** | $79 lifetime | FREE + AI summaries, AI tags, cloud sync |

### Kluczowe decyzje techniczne

| Aspekt | Decyzja | Uzasadnienie |
|--------|---------|--------------|
| **Narzędzie pakowania** | py2app + rumps | Dedykowane dla menu bar apps, lepsze niż PyInstaller |
| **Architektura CPU** | Tylko Apple Silicon (M1/M2/M3) | Uproszczenie buildu, 80%+ nowych Mac'ów |
| **Whisper.cpp** | Download on first run | Mniejsza paczka początkowa (~15MB vs 550MB) |
| **FFmpeg** | Bundlowany statycznie | Bez dependency na Homebrew |
| **Code signing** | Tak ($99/rok) | Profesjonalne UX bez ostrzeżeń Gatekeeper |
| **Backend PRO** | Cloudflare Workers | Serverless, niskie koszty, wysoka dostępność |
| **Płatności** | LemonSqueezy | Prostota, tax compliance, license keys API |

### Szacowany czas realizacji

| Faza | Czas |
|------|------|
| **v2.0.0 FREE** | 4-5 tygodni |
| **v2.1.0 PRO** | 2-3 tygodnie (po FREE) |
| **RAZEM** | ~7-8 tygodni |

---

## 2. Decyzje strategiczne

### 2.1. Docelowa platforma

```
✅ WYBÓR: Apple Silicon (ARM64) only

Uzasadnienie:
- 80%+ nowych Mac'ów to Apple Silicon (od 2020)
- Upraszcza proces budowania (jeden build)
- Core ML acceleration działa tylko na Apple Silicon
- Intel Mac'i mogą używać wersji developerskiej (źródła)
```

### 2.2. Docelowy użytkownik

```
✅ WYBÓR: Użytkownik nietechniczny

Konsekwencje:
- Wszystkie zależności pobierane automatycznie
- Brak wymagania Homebrew
- Wizard prowadzący przez konfigurację
- Jasne instrukcje dla Full Disk Access
```

### 2.3. Model dystrybucji

```
✅ WYBÓR: Freemium (FREE + PRO)

┌─────────────────────────────────────────────────────────────────────────┐
│                         TRANSREC FREE                                    │
│                     (Open Source - GitHub)                               │
├─────────────────────────────────────────────────────────────────────────┤
│  ✅ Automatyczne wykrywanie recorderów/kart SD                          │
│  ✅ Transkrypcja lokalna (whisper.cpp)                                  │
│  ✅ Podstawowe tagi (#transcription, #audio)                            │
│  ✅ Export do Markdown                                                   │
│  ✅ Menu bar app                                                        │
│  ✅ First-run wizard                                                    │
│                                                                         │
│  ❌ AI Podsumowania                                                     │
│  ❌ Inteligentne tagi AI                                                │
│  ❌ Cloud sync                                                          │
│  ❌ Web dashboard                                                        │
│  ❌ Multi-device sync                                                    │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                         TRANSREC PRO                                     │
│                    ($79 lifetime / subskrypcja)                          │
├─────────────────────────────────────────────────────────────────────────┤
│  ✅ Wszystko z FREE +                                                   │
│                                                                         │
│  ⭐ AI Podsumowania (przez serwer z Claude/GPT)                         │
│  ⭐ Inteligentne tagi AI                                                │
│  ⭐ Automatyczne nazewnictwo plików z AI                                │
│  ⭐ Cloud sync (iCloud, Dropbox, S3)                                    │
│  ⭐ Dashboard web (historia, statystyki)                                │
│  ⭐ Multi-device sync                                                   │
│  ⭐ Priorytetowe wsparcie                                               │
└─────────────────────────────────────────────────────────────────────────┘

Kanały dystrybucji:
1. GitHub Releases - FREE (open source)
2. transrec.app - PRO (płatności przez LemonSqueezy)
3. Mac App Store - NIE (wymaga sandboxing, niekompatybilne z FDA)
```

### 2.4. Wersjonowanie

```
Obecna wersja: 1.10.0 (development)

Planowane wersje:
  v2.0.0 - FREE release (transkrypcja lokalna)
  v2.1.0 - PRO release (AI features przez backend)
  v2.2.0 - Cloud sync (PRO)

Schemat: MAJOR.MINOR.PATCH
- MAJOR: Zmiany łamiące kompatybilność
- MINOR: Nowe funkcje / PRO features
- PATCH: Bugfixy
```

---

## 3. Architektura docelowa

### 3.1. Struktura aplikacji

```
~/Applications/
└── Malinche.app/                        (~15MB download)
    └── Contents/
        ├── Info.plist
        ├── MacOS/
        │   └── Malinche                 (main executable)
        ├── Resources/
        │   ├── icon.icns
        │   ├── lib/                     (Python runtime + packages)
        │   └── ffmpeg                   (statycznie zlinkowany, ~15MB)
        └── Frameworks/

~/Library/Application Support/Malinche/  (pobierane przy pierwszym uruchomieniu)
├── whisper.cpp/
│   └── whisper-cli                      (~10MB)
├── models/
│   └── ggml-small.bin                   (~466MB)
├── config.json                          (ustawienia użytkownika)
└── cache/                               (pliki tymczasowe)

~/.transrec/                             (dane użytkownika)
├── state.json                           (historia przetworzonych plików)
└── logs/
    └── transrec.log
```

### 3.2. Przepływ pierwszego uruchomienia

```
┌─────────────────────────────────────────────────────────────────┐
│                    FIRST RUN WIZARD                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  KROK 1: Powitanie                                              │
│  ┌────────────────────────────────────────────────────────┐     │
│  │  🎙️ Witaj w Malinche!                                  │     │
│  │                                                        │     │
│  │  Malinche automatycznie transkrybuje nagrania          │     │
│  │  z Twojego dyktafonu lub karty SD.                     │     │
│  │                                                        │     │
│  │  Przeprowadzimy Cię przez szybką konfigurację.         │     │
│  │                                                        │     │
│  │  [Rozpocznij →]                                        │     │
│  └────────────────────────────────────────────────────────┘     │
│                                                                  │
│  KROK 2: Pobieranie silnika transkrypcji                        │
│  ┌────────────────────────────────────────────────────────┐     │
│  │  📥 Pobieranie silnika transkrypcji...                 │     │
│  │                                                        │     │
│  │  ████████████████░░░░░░░░░░░░░░  45%                   │     │
│  │                                                        │     │
│  │  Pobieranie: whisper-cli (10 MB)        ✓ Gotowe      │     │
│  │  Pobieranie: model small (466 MB)       W toku...      │     │
│  │                                                        │     │
│  │  Szacowany czas: ~3 minuty                             │     │
│  └────────────────────────────────────────────────────────┘     │
│                                                                  │
│  KROK 3: Uprawnienia dostępu do dysków                          │
│  ┌────────────────────────────────────────────────────────┐     │
│  │  🔐 Malinche potrzebuje dostępu do dysków              │     │
│  │                                                        │     │
│  │  Aby automatycznie wykrywać dyktafon, Malinche         │     │
│  │  potrzebuje uprawnień "Full Disk Access".              │     │
│  │                                                        │     │
│  │  1. Kliknij "Otwórz Ustawienia"                        │     │
│  │  2. Odblokuj kłódkę 🔒 (hasło administratora)          │     │
│  │  3. Znajdź "Malinche" i zaznacz ☑                      │     │
│  │  4. Wróć tutaj                                         │     │
│  │                                                        │     │
│  │  [📖 Pokaż instrukcję]  [Otwórz Ustawienia →]          │     │
│  │                                                        │     │
│  │  ○ Pomiń (będę wybierać pliki ręcznie)                 │     │
│  └────────────────────────────────────────────────────────┘     │
│                                                                  │
│  KROK 4: Wybór źródła nagrań                                    │
│  ┌────────────────────────────────────────────────────────┐     │
│  │  📁 Skąd pobierać nagrania?                            │     │
│  │                                                        │     │
│  │  ○ Automatycznie wykryj każdy nowy dysk                │     │
│  │    (zalecane dla większości użytkowników)              │     │
│  │                                                        │     │
│  │  ○ Tylko określone dyski:                              │     │
│  │    ☑ LS-P1 (Olympus)                                   │     │
│  │    ☑ SD Card                                           │     │
│  │    ☐ ZOOM-H6                                           │     │
│  │    [+ Dodaj inny...]                                   │     │
│  │                                                        │     │
│  │  [Dalej →]                                             │     │
│  └────────────────────────────────────────────────────────┘     │
│                                                                  │
│  KROK 5: Folder na transkrypcje                                 │
│  ┌────────────────────────────────────────────────────────┐     │
│  │  📂 Gdzie zapisywać transkrypcje?                      │     │
│  │                                                        │     │
│  │  [~/Documents/Transcriptions           ] [Zmień...]    │     │
│  │                                                        │     │
│  │  ☑ Użyj formatu Obsidian (YAML frontmatter)            │     │
│  │                                                        │     │
│  │  [Dalej →]                                             │     │
│  └────────────────────────────────────────────────────────┘     │
│                                                                  │
│  KROK 6: Język transkrypcji                                     │
│  ┌────────────────────────────────────────────────────────┐     │
│  │  🗣️ W jakim języku są Twoje nagrania?                  │     │
│  │                                                        │     │
│  │  [Polski                              ▼]               │     │
│  │                                                        │     │
│  │  ☐ Automatyczne wykrywanie języka                      │     │
│  │                                                        │     │
│  │  [Dalej →]                                             │     │
│  └────────────────────────────────────────────────────────┘     │
│                                                                  │
│  KROK 7: AI Podsumowania (opcjonalne)                           │
│  ┌────────────────────────────────────────────────────────┐     │
│  │  🤖 Chcesz automatyczne podsumowania AI?               │     │
│  │                                                        │     │
│  │  Malinche może generować inteligentne podsumowania     │     │
│  │  i tytuły używając Claude AI (wymaga klucza API).      │     │
│  │                                                        │     │
│  │  ○ Włącz podsumowania AI                               │     │
│  │    API Key: [sk-ant-...                    ]           │     │
│  │    [Jak uzyskać klucz?]                                │     │
│  │                                                        │     │
│  │  ○ Pomiń (proste tytuły z nazwy pliku)                 │     │
│  │                                                        │     │
│  │  [Dalej →]                                             │     │
│  └────────────────────────────────────────────────────────┘     │
│                                                                  │
│  KROK 8: Gotowe!                                                │
│  ┌────────────────────────────────────────────────────────┐     │
│  │  ✅ Malinche jest gotowy do pracy!                     │     │
│  │                                                        │     │
│  │  Podłącz dyktafon, a Malinche automatycznie            │     │
│  │  przetworzy Twoje nagrania.                            │     │
│  │                                                        │     │
│  │  Ikona Malinche pojawi się w pasku menu (góra ekranu). │     │
│  │                                                        │     │
│  │  [🎉 Rozpocznij!]                                      │     │
│  └────────────────────────────────────────────────────────┘     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.3. Architektura modułów

```
src/
├── __init__.py
├── main.py                    # Entry point (bez zmian)
├── menu_app.py               # Menu bar UI (rozbudowa)
│
├── config/                    # NOWY: Konfiguracja
│   ├── __init__.py
│   ├── settings.py           # UserSettings dataclass
│   ├── defaults.py           # Domyślne wartości
│   ├── features.py           # 🆕 FREEMIUM: Feature flags & tiers
│   ├── license.py            # 🆕 FREEMIUM: License management
│   └── migration.py          # Migracja ze starej konfiguracji
│
├── setup/                     # NOWY: First-run wizard
│   ├── __init__.py
│   ├── wizard.py             # Główna logika wizarda
│   ├── downloader.py         # Pobieranie whisper.cpp/modeli
│   ├── permissions.py        # Sprawdzanie FDA
│   └── views/                # Widoki wizarda (rumps alerts)
│       ├── welcome.py
│       ├── download.py
│       ├── permissions.py
│       ├── source_config.py
│       └── finish.py
│
├── core/                      # Istniejąca logika (reorganizacja)
│   ├── __init__.py
│   ├── transcriber.py        # (przeniesiony)
│   ├── file_monitor.py       # (przeniesiony + rozbudowa)
│   ├── summarizer.py         # Modified: PRO check dla AI
│   ├── markdown_generator.py # (przeniesiony)
│   ├── tagger.py             # Modified: PRO check dla AI tags
│   └── state_manager.py      # (przeniesiony)
│
├── services/                  # 🆕 FREEMIUM: PRO services
│   ├── __init__.py
│   ├── api_client.py         # Malinche API client
│   ├── cloud_sync.py         # Cloud sync service (PRO)
│   └── analytics.py          # Usage analytics (opt-in)
│
├── utils/                     # NOWY: Narzędzia pomocnicze
│   ├── __init__.py
│   ├── logger.py             # (przeniesiony)
│   ├── paths.py              # Zarządzanie ścieżkami
│   ├── platform.py           # Wykrywanie platformy
│   └── notifications.py      # macOS notifications
│
└── ui/                        # NOWY: Komponenty UI
    ├── __init__.py
    ├── settings_window.py    # Okno ustawień
    ├── pro_activation.py     # 🆕 FREEMIUM: PRO activation UI
    └── about_window.py       # Okno "O aplikacji"
```

### 3.4. Architektura Freemium

```
┌─────────────────────────────────────────────────────────────────┐
│                      TRANSREC APP (CLIENT)                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐     ┌──────────────────┐                  │
│  │  Feature Flags   │────▶│  License Manager │                  │
│  │  (features.py)   │     │  (license.py)    │                  │
│  └────────┬─────────┘     └────────┬─────────┘                  │
│           │                        │                             │
│           ▼                        ▼                             │
│  ┌──────────────────────────────────────────────┐               │
│  │              Feature Check                    │               │
│  │  if features.ai_summaries:                   │               │
│  │      # Call PRO API                          │               │
│  │  else:                                       │               │
│  │      # Use FREE fallback                     │               │
│  └──────────────────────────────────────────────┘               │
│                                                                  │
└──────────────────────────────┬──────────────────────────────────┘
                               │ HTTPS (tylko PRO)
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    TRANSREC BACKEND (SERVER)                     │
│                 (Cloudflare Workers / Vercel)                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  /v1/license/verify     POST    Weryfikacja klucza licencji     │
│  /v1/summarize          POST    AI podsumowanie (PRO)           │
│  /v1/tags               POST    AI tagi (PRO)                   │
│  /v1/title              POST    AI tytuł (PRO)                  │
│  /v1/sync/upload        POST    Upload transkrypcji (PRO)       │
│  /v1/sync/download      GET     Download transkrypcji (PRO)     │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│                      EXTERNAL SERVICES                           │
├─────────────────────────────────────────────────────────────────┤
│  • LemonSqueezy         - Płatności & license keys              │
│  • Claude API           - AI summaries/tags                     │
│  • Cloudflare R2        - Storage dla sync                      │
│  • PostgreSQL (Neon)    - Database                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Plan implementacji - Fazy

### FAZA 1: Uniwersalne źródła nagrań (3-4 dni)

**Cel:** Aplikacja wykrywa dowolny dysk/kartę SD, nie tylko Olympus LS-P1.

#### 1.1. Nowy system konfiguracji użytkownika

**Plik:** `src/config/settings.py`

```python
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional
import json

@dataclass
class UserSettings:
    """Ustawienia użytkownika (persystentne)."""
    
    # Źródła nagrań
    watch_mode: str = "auto"  # "auto" | "manual" | "specific"
    watched_volumes: List[str] = field(default_factory=list)
    
    # Ścieżki
    output_dir: Path = None
    
    # Transkrypcja
    language: str = "pl"
    whisper_model: str = "small"
    
    # AI
    enable_ai_summaries: bool = False
    ai_api_key: Optional[str] = None
    
    # UI
    show_notifications: bool = True
    start_at_login: bool = False
    
    # Stan wizarda
    setup_completed: bool = False
    
    @classmethod
    def load(cls) -> "UserSettings":
        """Wczytaj ustawienia z pliku."""
        config_path = cls._config_path()
        if config_path.exists():
            with open(config_path, "r") as f:
                data = json.load(f)
            return cls(**data)
        return cls()
    
    def save(self) -> None:
        """Zapisz ustawienia do pliku."""
        config_path = self._config_path()
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w") as f:
            json.dump(self.__dict__, f, indent=2, default=str)
    
    @staticmethod
    def _config_path() -> Path:
        return Path.home() / "Library" / "Application Support" / "Malinche" / "config.json"
```

#### 1.2. Rozbudowa FileMonitor

**Plik:** `src/core/file_monitor.py` - zmiany

```python
# Nowa logika wykrywania źródeł
def _should_process_volume(self, volume_path: Path) -> bool:
    """Sprawdź czy volumen powinien być przetwarzany."""
    settings = UserSettings.load()
    volume_name = volume_path.name
    
    # Ignoruj systemowe volumeny
    SYSTEM_VOLUMES = {"Macintosh HD", "Recovery", "Preboot", "VM", "Data"}
    if volume_name in SYSTEM_VOLUMES:
        return False
    
    match settings.watch_mode:
        case "auto":
            # Sprawdź czy zawiera pliki audio
            return self._has_audio_files(volume_path)
        case "specific":
            return volume_name in settings.watched_volumes
        case "manual":
            return False  # Użytkownik wybiera ręcznie
    
    return False

def _has_audio_files(self, path: Path, max_depth: int = 3) -> bool:
    """Sprawdź czy folder zawiera pliki audio."""
    audio_extensions = {".mp3", ".wav", ".m4a", ".wma", ".flac", ".aac"}
    try:
        for item in path.rglob("*"):
            if item.suffix.lower() in audio_extensions:
                return True
            # Ogranicz głębokość skanowania
            if len(item.relative_to(path).parts) > max_depth:
                continue
    except PermissionError:
        return False
    return False
```

#### 1.3. Zadania

- [ ] Utworzyć `src/config/settings.py` z klasą `UserSettings`
- [ ] Utworzyć `src/config/defaults.py` z domyślnymi wartościami
- [ ] Zrefaktorować `config.py` do użycia `UserSettings`
- [ ] Rozbudować `file_monitor.py` o logikę `watch_mode`
- [ ] Dodać testy jednostkowe dla nowej konfiguracji
- [ ] Dodać migrację ze starej konfiguracji (`~/.olympus_transcriber_state.json`)

---

### FAZA 2: System pobierania zależności (4-5 dni)

**Cel:** Automatyczne pobieranie whisper.cpp i modeli przy pierwszym uruchomieniu.

#### 2.1. Moduł Downloader

**Plik:** `src/setup/downloader.py`

```python
import urllib.request
import hashlib
from pathlib import Path
from typing import Callable, Optional
import subprocess
import platform

class DependencyDownloader:
    """Pobieranie i weryfikacja zależności."""
    
    # URLs dla plików binarnych
    WHISPER_URLS = {
        "arm64": "https://github.com/YOUR_REPO/releases/download/v1.0/whisper-cli-arm64",
    }
    
    MODEL_URLS = {
        "small": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin",
        "medium": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-medium.bin",
    }
    
    # Checksums SHA256
    CHECKSUMS = {
        "whisper-cli-arm64": "abc123...",
        "ggml-small.bin": "def456...",
    }
    
    def __init__(self, progress_callback: Optional[Callable[[str, float], None]] = None):
        self.progress_callback = progress_callback
        self.support_dir = Path.home() / "Library" / "Application Support" / "Malinche"
    
    def is_whisper_installed(self) -> bool:
        """Sprawdź czy whisper.cpp jest zainstalowany."""
        whisper_path = self.support_dir / "whisper.cpp" / "whisper-cli"
        return whisper_path.exists() and whisper_path.stat().st_size > 0
    
    def is_model_installed(self, model: str = "small") -> bool:
        """Sprawdź czy model jest pobrany."""
        model_path = self.support_dir / "models" / f"ggml-{model}.bin"
        return model_path.exists()
    
    async def download_whisper(self) -> bool:
        """Pobierz whisper.cpp binary."""
        arch = platform.machine()
        if arch != "arm64":
            raise RuntimeError(f"Unsupported architecture: {arch}")
        
        url = self.WHISPER_URLS["arm64"]
        dest = self.support_dir / "whisper.cpp" / "whisper-cli"
        dest.parent.mkdir(parents=True, exist_ok=True)
        
        await self._download_file(url, dest, "whisper-cli")
        
        # Nadaj uprawnienia wykonywania
        dest.chmod(0o755)
        
        return True
    
    async def download_model(self, model: str = "small") -> bool:
        """Pobierz model whisper."""
        url = self.MODEL_URLS.get(model)
        if not url:
            raise ValueError(f"Unknown model: {model}")
        
        dest = self.support_dir / "models" / f"ggml-{model}.bin"
        dest.parent.mkdir(parents=True, exist_ok=True)
        
        await self._download_file(url, dest, f"model-{model}")
        
        return True
    
    async def _download_file(self, url: str, dest: Path, name: str) -> None:
        """Pobierz plik z progress callback."""
        # Implementacja z urllib + progress reporting
        ...
    
    def verify_checksum(self, file_path: Path, expected: str) -> bool:
        """Zweryfikuj SHA256 checksum."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest() == expected
```

#### 2.2. Hosting plików binarnych

**Opcje:**

1. **GitHub Releases** (zalecane)
   - Darmowe
   - Niezawodne
   - Łatwa integracja z CI/CD

2. **Hugging Face** (dla modeli)
   - Oficjalne źródło modeli whisper.cpp
   - Wysoka dostępność

#### 2.3. Budowanie whisper.cpp dla dystrybucji

```bash
# Skrypt budowania (CI/CD)
#!/bin/bash
set -e

# Klonuj whisper.cpp
git clone https://github.com/ggerganov/whisper.cpp.git
cd whisper.cpp

# Kompiluj dla ARM64 z Core ML
cmake -B build \
    -DWHISPER_COREML=ON \
    -DCMAKE_OSX_ARCHITECTURES=arm64 \
    -DCMAKE_BUILD_TYPE=Release

cmake --build build --config Release

# Kopiuj binary
cp build/bin/whisper-cli ../whisper-cli-arm64

# Generuj checksum
shasum -a 256 ../whisper-cli-arm64 > ../whisper-cli-arm64.sha256
```

#### 2.4. Zadania

- [ ] Utworzyć `src/setup/downloader.py`
- [ ] Skonfigurować GitHub Actions do budowania whisper.cpp
- [ ] Utworzyć GitHub Release z binaries
- [ ] Zaimplementować progress callback dla UI
- [ ] Dodać weryfikację checksum
- [ ] Obsłużyć błędy pobierania (retry, offline mode)
- [ ] Testy integracyjne pobierania

---

### FAZA 3: First-Run Wizard (4-5 dni)

**Cel:** Przyjazny wizard prowadzący użytkownika przez konfigurację.

#### 3.1. Główna klasa wizarda

**Plik:** `src/setup/wizard.py`

```python
import rumps
from enum import Enum, auto
from typing import Optional
from src.config.settings import UserSettings
from src.setup.downloader import DependencyDownloader
from src.setup.permissions import check_full_disk_access

class WizardStep(Enum):
    WELCOME = auto()
    DOWNLOAD = auto()
    PERMISSIONS = auto()
    SOURCE_CONFIG = auto()
    OUTPUT_CONFIG = auto()
    LANGUAGE = auto()
    AI_CONFIG = auto()
    FINISH = auto()

class SetupWizard:
    """First-run setup wizard."""
    
    def __init__(self):
        self.current_step = WizardStep.WELCOME
        self.settings = UserSettings()
        self.downloader = DependencyDownloader(progress_callback=self._on_progress)
    
    def needs_setup(self) -> bool:
        """Sprawdź czy wizard jest potrzebny."""
        settings = UserSettings.load()
        return not settings.setup_completed
    
    def run(self) -> bool:
        """Uruchom wizard. Zwraca True jeśli ukończony."""
        while self.current_step != WizardStep.FINISH:
            result = self._run_step()
            if result == "cancel":
                return False
            elif result == "back":
                self._previous_step()
            else:
                self._next_step()
        
        self.settings.setup_completed = True
        self.settings.save()
        return True
    
    def _run_step(self) -> str:
        """Wykonaj aktualny krok. Zwraca 'next', 'back' lub 'cancel'."""
        match self.current_step:
            case WizardStep.WELCOME:
                return self._show_welcome()
            case WizardStep.DOWNLOAD:
                return self._show_download()
            case WizardStep.PERMISSIONS:
                return self._show_permissions()
            case WizardStep.SOURCE_CONFIG:
                return self._show_source_config()
            case WizardStep.OUTPUT_CONFIG:
                return self._show_output_config()
            case WizardStep.LANGUAGE:
                return self._show_language()
            case WizardStep.AI_CONFIG:
                return self._show_ai_config()
        return "next"
    
    def _show_welcome(self) -> str:
        """Ekran powitalny."""
        response = rumps.alert(
            title="🎙️ Witaj w Malinche!",
            message=(
                "Malinche automatycznie transkrybuje nagrania "
                "z Twojego dyktafonu lub karty SD.\n\n"
                "Przeprowadzimy Cię przez szybką konfigurację."
            ),
            ok="Rozpocznij →",
            cancel="Anuluj"
        )
        return "next" if response == 1 else "cancel"
    
    def _show_download(self) -> str:
        """Pobieranie zależności."""
        if self.downloader.is_whisper_installed() and self.downloader.is_model_installed():
            return "next"  # Skip jeśli już pobrane
        
        # Pokaż dialog pobierania
        # TODO: Implementacja async download z progress
        ...
    
    def _show_permissions(self) -> str:
        """Instrukcje Full Disk Access."""
        if check_full_disk_access():
            return "next"  # Skip jeśli już ma uprawnienia
        
        response = rumps.alert(
            title="🔐 Uprawnienia dostępu",
            message=(
                "Aby automatycznie wykrywać dyktafon, Malinche "
                "potrzebuje uprawnień 'Full Disk Access'.\n\n"
                "1. Kliknij 'Otwórz Ustawienia'\n"
                "2. Odblokuj kłódkę 🔒\n"
                "3. Znajdź 'Malinche' i zaznacz ☑\n"
                "4. Wróć tutaj"
            ),
            ok="Otwórz Ustawienia",
            cancel="Pomiń"
        )
        
        if response == 1:
            import subprocess
            subprocess.run([
                "open",
                "x-apple.systempreferences:com.apple.preference.security?Privacy_AllFiles"
            ])
            # Poczekaj na powrót użytkownika
            rumps.alert("Gotowe?", "Kliknij OK gdy nadasz uprawnienia.", ok="OK")
        
        return "next"
    
    # ... pozostałe metody
```

#### 3.2. Sprawdzanie Full Disk Access

**Plik:** `src/setup/permissions.py`

```python
import subprocess
from pathlib import Path

def check_full_disk_access() -> bool:
    """Sprawdź czy aplikacja ma Full Disk Access."""
    # Próba dostępu do chronionego katalogu
    test_paths = [
        Path.home() / "Library" / "Mail",
        Path.home() / "Library" / "Safari",
        Path("/Volumes"),
    ]
    
    for path in test_paths:
        try:
            list(path.iterdir())
        except PermissionError:
            return False
    
    return True

def open_fda_preferences() -> None:
    """Otwórz preferencje Full Disk Access."""
    subprocess.run([
        "open",
        "x-apple.systempreferences:com.apple.preference.security?Privacy_AllFiles"
    ])
```

#### 3.3. Zadania

- [ ] Utworzyć strukturę `src/setup/`
- [ ] Zaimplementować `SetupWizard` z wszystkimi krokami
- [ ] Zaimplementować `check_full_disk_access()`
- [ ] Dodać async download z progress bar
- [ ] Dodać obsługę cofania (back button)
- [ ] Testy manualne przepływu wizarda
- [ ] Instrukcja z obrazkami dla FDA (opcjonalnie jako HTML)

---

### FAZA 4: Pakowanie z py2app (3-4 dni)

**Cel:** Tworzenie .app bundle gotowego do dystrybucji.

#### 4.1. Konfiguracja py2app

**Plik:** `setup_app.py`

```python
from setuptools import setup
import py2app
from pathlib import Path

APP = ['src/menu_app.py']

DATA_FILES = [
    ('', ['assets/icon.icns']),
    ('ffmpeg', ['vendor/ffmpeg']),  # Statycznie zlinkowany ffmpeg
]

OPTIONS = {
    'argv_emulation': False,
    'iconfile': 'assets/icon.icns',
    'plist': {
        'CFBundleName': 'Malinche',
        'CFBundleDisplayName': 'Malinche',
        'CFBundleIdentifier': 'com.yourname.transrec',
        'CFBundleVersion': '2.0.0',
        'CFBundleShortVersionString': '2.0.0',
        'LSUIElement': True,  # Menu bar only, no dock icon
        'LSMinimumSystemVersion': '12.0',  # macOS Monterey+
        'NSRequiresAquaSystemAppearance': False,  # Dark mode support
        'NSHighResolutionCapable': True,
        'NSAppleEventsUsageDescription': 'Malinche needs to control system events.',
        'NSMicrophoneUsageDescription': 'Malinche does not use the microphone.',
    },
    'packages': [
        'rumps',
        'anthropic',
        'mutagen',
        'httpx',
        'pydantic',
    ],
    'excludes': [
        'tkinter',
        'matplotlib',
        'PIL',
        'numpy',
        'scipy',
    ],
    'arch': 'arm64',  # Apple Silicon only
}

setup(
    name='Malinche',
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
```

#### 4.2. Skrypt budowania

**Plik:** `scripts/build_app.sh`

```bash
#!/bin/bash
set -e

echo "🔨 Building Malinche.app..."

# Wyczyść poprzednie buildy
rm -rf build dist

# Aktywuj venv
source venv/bin/activate

# Zainstaluj py2app
pip install py2app

# Zbuduj aplikację
python setup_app.py py2app

# Skopiuj dodatkowe zasoby
cp -r assets/instructions dist/Malinche.app/Contents/Resources/

echo "✅ Build complete: dist/Malinche.app"
echo "📦 Size: $(du -sh dist/Malinche.app | cut -f1)"
```

#### 4.3. Zadania

- [ ] Utworzyć `setup_app.py` z konfiguracją py2app
- [ ] Przygotować ikony (`icon.icns` w różnych rozmiarach)
- [ ] Pobrać/zbudować statyczny ffmpeg
- [ ] Utworzyć skrypt `scripts/build_app.sh`
- [ ] Przetestować build na czystym systemie
- [ ] Zoptymalizować rozmiar (excludes)

---

### FAZA 5: Code Signing & Notaryzacja (2-3 dni)

**Cel:** Podpisana i notaryzowana aplikacja bez ostrzeżeń Gatekeeper.

#### 5.1. Wymagania

- [ ] Konto Apple Developer ($99/rok)
- [ ] Developer ID Application certificate
- [ ] App-specific password dla notaryzacji

#### 5.2. Skrypt podpisywania

**Plik:** `scripts/sign_and_notarize.sh`

```bash
#!/bin/bash
set -e

APP_PATH="dist/Malinche.app"
BUNDLE_ID="com.yourname.transrec"
DEVELOPER_ID="Developer ID Application: Your Name (TEAM_ID)"
APPLE_ID="your@email.com"
TEAM_ID="YOUR_TEAM_ID"
APP_PASSWORD="xxxx-xxxx-xxxx-xxxx"  # App-specific password

echo "🔏 Signing application..."

# Podpisz wszystkie frameworks i binaries
codesign --deep --force --options runtime \
    --sign "$DEVELOPER_ID" \
    --entitlements entitlements.plist \
    "$APP_PATH"

# Zweryfikuj podpis
codesign --verify --deep --strict "$APP_PATH"
echo "✅ Signature verified"

echo "📦 Creating DMG..."
# Utwórz DMG
create-dmg \
    --volname "Malinche" \
    --window-pos 200 120 \
    --window-size 600 400 \
    --icon-size 100 \
    --icon "Malinche.app" 175 190 \
    --app-drop-link 425 190 \
    "dist/Malinche-2.0.0.dmg" \
    "$APP_PATH"

echo "🔏 Signing DMG..."
codesign --sign "$DEVELOPER_ID" "dist/Malinche-2.0.0.dmg"

echo "📤 Submitting for notarization..."
xcrun notarytool submit "dist/Malinche-2.0.0.dmg" \
    --apple-id "$APPLE_ID" \
    --password "$APP_PASSWORD" \
    --team-id "$TEAM_ID" \
    --wait

echo "📎 Stapling notarization ticket..."
xcrun stapler staple "dist/Malinche-2.0.0.dmg"

echo "✅ Done! Ready for distribution: dist/Malinche-2.0.0.dmg"
```

#### 5.3. Entitlements

**Plik:** `entitlements.plist`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>com.apple.security.cs.allow-jit</key>
    <true/>
    <key>com.apple.security.cs.allow-unsigned-executable-memory</key>
    <true/>
    <key>com.apple.security.cs.disable-library-validation</key>
    <true/>
    <key>com.apple.security.automation.apple-events</key>
    <true/>
</dict>
</plist>
```

#### 5.4. Zadania

- [ ] Zarejestrować się w Apple Developer Program ($99)
- [ ] Utworzyć Developer ID Application certificate
- [ ] Wygenerować app-specific password
- [ ] Utworzyć `entitlements.plist`
- [ ] Utworzyć skrypt `scripts/sign_and_notarize.sh`
- [ ] Przetestować na maszynie bez certyfikatu dewelopera
- [ ] Zautomatyzować w GitHub Actions (secrets)

---

### FAZA 6: Tworzenie DMG & Release (2 dni)

**Cel:** Profesjonalny DMG do pobrania.

#### 6.1. Instalacja create-dmg

```bash
brew install create-dmg
```

#### 6.2. Tło DMG

**Plik:** `assets/dmg-background.png` (600x400px)

```
┌────────────────────────────────────────────────────────────────┐
│                                                                │
│                                                                │
│     🎙️                                    📁                   │
│   [Malinche]  ─────────────────────────→  Applications        │
│                                                                │
│                                                                │
│          Przeciągnij Malinche do Applications                  │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

#### 6.3. GitHub Release

**Workflow:** `.github/workflows/release.yml`

```yaml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: macos-14  # Apple Silicon runner
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install py2app
      
      - name: Build app
        run: python setup_app.py py2app
      
      - name: Import certificates
        env:
          CERTIFICATE_BASE64: ${{ secrets.APPLE_CERTIFICATE }}
          CERTIFICATE_PASSWORD: ${{ secrets.CERTIFICATE_PASSWORD }}
        run: |
          # Import certificate...
      
      - name: Sign and notarize
        env:
          APPLE_ID: ${{ secrets.APPLE_ID }}
          APPLE_PASSWORD: ${{ secrets.APPLE_PASSWORD }}
          TEAM_ID: ${{ secrets.TEAM_ID }}
        run: bash scripts/sign_and_notarize.sh
      
      - name: Create Release
        uses: softprops/action-gh-release@v1
        with:
          files: dist/Malinche-*.dmg
          generate_release_notes: true
```

#### 6.4. Zadania

- [ ] Zaprojektować tło DMG
- [ ] Skonfigurować create-dmg
- [ ] Utworzyć workflow GitHub Actions
- [ ] Skonfigurować secrets (certificates, passwords)
- [ ] Przetestować cały pipeline release

---

### FAZA 7: GUI Settings & Polish (MVP) ✅ COMPLETED

**Cel:** Minimalne poprawki UX istniejącego interfejsu z architekturą przygotowaną na przyszły redesign.

**Status:** ✅ Zakończona (testy automatyczne: 18/18 pass, coverage 94%, testy manualne wymagane)

#### 7.1. Moduł UI

**Utworzone pliki:**
- `src/ui/__init__.py` - eksporty modułu
- `src/ui/constants.py` - stałe UI (APP_VERSION, APP_NAME, TEXTS) - łatwe do wymiany przy redesignie
- `src/ui/dialogs.py` - reusable funkcje dialogów

#### 7.2. Date picker dla "Resetuj pamięć"

**Zmodyfikowany plik:** `src/menu_app.py`

- Dialog z opcjami: 7 dni / 30 dni / Inna data
- Input daty w formacie YYYY-MM-DD z walidacją
- Zastępuje prosty dialog z tylko opcją "7 dni"

#### 7.3. Graficzny wybór folderu w wizardzie

**Zmodyfikowany plik:** `src/setup/wizard.py`

- NSOpenPanel dla natywnego dialogu wyboru folderu
- Fallback na tekstowy input gdy AppKit niedostępne
- Dialog z opcjami: Wybierz folder / Użyj domyślnego / Wstecz

#### 7.4. Dialog "O aplikacji"

**Zmodyfikowany plik:** `src/menu_app.py`

- Nowy MenuItem "O aplikacji..." w menu
- Wyświetla wersję, linki do strony i GitHub, informacje o licencji

#### 7.5. Testy

- ✅ Testy automatyczne: `tests/test_ui_constants.py`, `tests/test_ui_dialogs.py`
- ✅ Coverage: 94% dla modułu `src/ui/`
- [ ] Testy manualne: `tests/MANUAL_TESTING_PHASE_7.md` (9 scenariuszy)

**Uwaga:** Pełne okno Settings i sprawdzanie aktualizacji zostały odłożone na Fazę 9 (pełny redesign UI).

---

### FAZA 9: Pełny redesign UI (przed dystrybucją) 🆕

**Cel:** Całkowity redesign interfejsu użytkownika przed dystrybucją publiczną.

**Szacowany czas:** 1-2 tygodnie

#### 9.1. Nowy instalator/wizard

- Wizualny redesign wizarda instalacyjnego
- Lepsze UX z nowymi komponentami
- Natywne komponenty macOS (date picker, dropdown języka)

#### 9.2. Nowe menu aplikacji

- Rozbudowane menu z dodatkowymi opcjami
- Pełne okno Settings (zamiast prostych dialogów)
- Sprawdzanie aktualizacji z auto-update

#### 9.3. Nowe ikony i kolory

- Branding i identyfikacja wizualna
- Nowe ikony aplikacji
- Dark mode support
- Spójny design system

#### 9.4. Decyzje do podjęcia przed Fazą 9

- Technologia: rumps + PyObjC vs Swift UI vs Electron
- Styl wizualny: minimalistyczny vs bogaty
- System ikon: SF Symbols vs custom

#### 9.5. Zadania

- [ ] Wybór technologii UI
- [ ] Projekt wizualny (mockupy)
- [ ] Implementacja nowego instalatora
- [ ] Implementacja nowego menu
- [ ] Nowe ikony i kolory
- [ ] Dark mode support
- [ ] Testy UI (automatyczne + manualne)

---

### FAZA 8: Infrastruktura Freemium (3-4 dni)

**Cel:** System feature flags i licencji (przygotowanie na PRO).

#### 8.1. Feature Flags

**Plik:** `src/config/features.py`

```python
from enum import Enum
from dataclasses import dataclass
from typing import Optional

class FeatureTier(Enum):
    FREE = "free"
    PRO = "pro"

@dataclass
class FeatureFlags:
    """Feature flags based on license tier."""
    
    # FREE features (always enabled)
    recorder_detection: bool = True
    local_transcription: bool = True
    markdown_export: bool = True
    basic_tags: bool = True
    
    # PRO features (requires license)
    ai_summaries: bool = False
    ai_smart_tags: bool = False
    ai_naming: bool = False
    cloud_sync: bool = False
    web_dashboard: bool = False
    
    @classmethod
    def for_tier(cls, tier: FeatureTier) -> "FeatureFlags":
        """Get feature flags for a specific tier."""
        if tier == FeatureTier.PRO:
            return cls(
                ai_summaries=True,
                ai_smart_tags=True,
                ai_naming=True,
                cloud_sync=True,
                web_dashboard=True,
            )
        return cls()  # FREE defaults
```

#### 8.2. License Manager

**Plik:** `src/config/license.py`

```python
import httpx
from pathlib import Path
from typing import Optional
import json
from datetime import datetime, timedelta

class LicenseManager:
    """Manages license verification and feature access."""
    
    LICENSE_API = "https://api.transrec.app/v1/license"
    CACHE_VALIDITY_DAYS = 7
    
    def __init__(self):
        self._cached_tier: Optional[FeatureTier] = None
        self._license_key: Optional[str] = None
        self._load_stored_license()
    
    def get_current_tier(self) -> FeatureTier:
        """Get current license tier (cached)."""
        if self._cached_tier is None:
            self._cached_tier = self._verify_license()
        return self._cached_tier
    
    def get_features(self) -> FeatureFlags:
        """Get enabled features based on license."""
        return FeatureFlags.for_tier(self.get_current_tier())
    
    def activate_license(self, key: str) -> tuple[bool, str]:
        """Activate a license key. Returns (success, message)."""
        try:
            response = httpx.post(
                f"{self.LICENSE_API}/activate",
                json={"license_key": key},
                timeout=10.0
            )
            data = response.json()
            
            if response.status_code == 200 and data.get("valid"):
                self._license_key = key
                self._cached_tier = FeatureTier.PRO
                self._save_license()
                return True, "Licencja PRO aktywowana! 🎉"
            
            return False, data.get("error", "Nieprawidłowy klucz")
        except Exception as e:
            return False, f"Błąd połączenia: {e}"
    
    def _verify_license(self) -> FeatureTier:
        """Verify license with server (with offline fallback)."""
        # Check cache first
        cached = self._load_cache()
        if cached and cached["expires"] > datetime.now().isoformat():
            return FeatureTier(cached["tier"])
        
        if not self._license_key:
            return FeatureTier.FREE
        
        try:
            response = httpx.post(
                f"{self.LICENSE_API}/verify",
                json={"license_key": self._license_key},
                timeout=5.0
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("valid"):
                    tier = FeatureTier.PRO
                    self._save_cache(tier)
                    return tier
        except Exception:
            # Offline fallback - use cache even if expired (grace period)
            if cached:
                return FeatureTier(cached["tier"])
        
        return FeatureTier.FREE
    
    def _load_stored_license(self) -> None:
        """Load license key from secure storage."""
        license_file = self._license_path()
        if license_file.exists():
            data = json.loads(license_file.read_text())
            self._license_key = data.get("key")
    
    def _save_license(self) -> None:
        """Save license key to secure storage."""
        license_file = self._license_path()
        license_file.parent.mkdir(parents=True, exist_ok=True)
        license_file.write_text(json.dumps({"key": self._license_key}))
    
    def _license_path(self) -> Path:
        return Path.home() / "Library" / "Application Support" / "Malinche" / "license.json"
    
    def _cache_path(self) -> Path:
        return Path.home() / "Library" / "Application Support" / "Malinche" / "license_cache.json"
    
    def _load_cache(self) -> Optional[dict]:
        cache_file = self._cache_path()
        if cache_file.exists():
            return json.loads(cache_file.read_text())
        return None
    
    def _save_cache(self, tier: FeatureTier) -> None:
        cache_file = self._cache_path()
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        expires = datetime.now() + timedelta(days=self.CACHE_VALIDITY_DAYS)
        cache_file.write_text(json.dumps({
            "tier": tier.value,
            "expires": expires.isoformat()
        }))

# Global instance
license_manager = LicenseManager()
```

#### 8.3. UI aktywacji PRO

**Plik:** `src/ui/pro_activation.py`

```python
import rumps
from src.config.license import license_manager

def show_pro_activation():
    """Show PRO activation dialog."""
    features = license_manager.get_features()
    
    if features.ai_summaries:
        rumps.alert(
            title="✅ Malinche PRO",
            message="Masz już aktywną licencję PRO!"
        )
        return
    
    # Show upgrade prompt
    response = rumps.alert(
        title="🚀 Malinche PRO",
        message=(
            "Odblokuj pełne możliwości Malinche:\n\n"
            "⭐ AI Podsumowania\n"
            "⭐ Inteligentne tagi\n"
            "⭐ Cloud sync\n"
            "⭐ Web dashboard\n\n"
            "Cena: $79 (lifetime)"
        ),
        ok="Kup PRO",
        cancel="Mam już klucz"
    )
    
    if response == 1:
        # Open purchase page
        import webbrowser
        webbrowser.open("https://transrec.app/pro")
    elif response == 0:
        # Show key input
        key_response = rumps.Window(
            title="Aktywacja PRO",
            message="Wklej klucz licencyjny:",
            ok="Aktywuj",
            cancel="Anuluj",
            dimensions=(300, 24)
        ).run()
        
        if key_response.clicked == 1 and key_response.text:
            success, message = license_manager.activate_license(key_response.text.strip())
            rumps.alert(
                title="✅ Sukces" if success else "❌ Błąd",
                message=message
            )
```

#### 8.4. Modyfikacja istniejących modułów

**Przykład:** `src/core/summarizer.py`

```python
from src.config.license import license_manager
from src.logger import logger

class Summarizer:
    def summarize(self, transcript: str) -> Optional[str]:
        """Generate AI summary."""
        features = license_manager.get_features()
        
        if not features.ai_summaries:
            logger.info("AI summaries require PRO license - skipping")
            return None
        
        # PRO: Call server API
        return self._call_api(transcript)
    
    def _call_api(self, transcript: str) -> str:
        """Call Malinche API for AI summary."""
        response = httpx.post(
            "https://api.transrec.app/v1/summarize",
            json={
                "transcript": transcript[:5000],  # Limit size
                "language": "pl",
            },
            headers={"Authorization": f"Bearer {license_manager._license_key}"},
            timeout=30.0
        )
        response.raise_for_status()
        return response.json()["summary"]
```

#### 8.5. Zadania

- [ ] Utworzyć `src/config/features.py` z FeatureFlags
- [ ] Utworzyć `src/config/license.py` z LicenseManager
- [ ] Utworzyć `src/ui/pro_activation.py`
- [ ] Zmodyfikować `summarizer.py` - PRO check
- [ ] Zmodyfikować `tagger.py` - PRO check dla AI tags
- [ ] Dodać "Uaktywnij PRO..." do menu app
- [ ] Testy feature flags
- [ ] Dokumentacja dla użytkowników (FREE vs PRO)

---

### FAZA 10: Backend PRO (5-7 dni) - OPCJONALNA

**Cel:** Serwer API dla funkcji PRO.

> ⚠️ **UWAGA:** Ta faza może być realizowana RÓWNOLEGLE lub PO wydaniu wersji FREE.

#### 9.1. Architektura backendu

```
transrec-backend/
├── src/
│   ├── index.ts              # Entry point (Cloudflare Workers)
│   ├── routes/
│   │   ├── license.ts        # /v1/license/*
│   │   ├── summarize.ts      # /v1/summarize
│   │   ├── tags.ts           # /v1/tags
│   │   └── sync.ts           # /v1/sync/*
│   ├── services/
│   │   ├── lemonsqueezy.ts   # Payment provider
│   │   ├── anthropic.ts      # Claude API
│   │   └── storage.ts        # R2/S3
│   └── middleware/
│       └── auth.ts           # License verification
├── wrangler.toml             # Cloudflare config
└── package.json
```

#### 9.2. Integracja LemonSqueezy

```typescript
// src/services/lemonsqueezy.ts
import crypto from 'crypto';

interface LicenseValidation {
  valid: boolean;
  tier: 'free' | 'pro';
  email?: string;
  expiresAt?: string;
}

export async function validateLicense(key: string): Promise<LicenseValidation> {
  const response = await fetch(
    `https://api.lemonsqueezy.com/v1/licenses/validate`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ license_key: key }),
    }
  );
  
  const data = await response.json();
  
  if (data.valid) {
    return {
      valid: true,
      tier: 'pro',
      email: data.meta?.customer_email,
    };
  }
  
  return { valid: false, tier: 'free' };
}
```

#### 9.3. Endpoint AI Summary

```typescript
// src/routes/summarize.ts
import Anthropic from '@anthropic-ai/sdk';

export async function handleSummarize(request: Request, env: Env) {
  // Verify PRO license (middleware)
  const license = request.headers.get('Authorization')?.replace('Bearer ', '');
  if (!await isProLicense(license)) {
    return new Response(JSON.stringify({ error: 'PRO license required' }), { 
      status: 403 
    });
  }
  
  const { transcript, language } = await request.json();
  
  const client = new Anthropic({ apiKey: env.ANTHROPIC_API_KEY });
  
  const message = await client.messages.create({
    model: 'claude-3-haiku-20240307',
    max_tokens: 500,
    messages: [{
      role: 'user',
      content: `Podsumuj poniższą transkrypcję w 2-3 zdaniach po polsku:\n\n${transcript.slice(0, 3000)}`
    }]
  });
  
  return new Response(JSON.stringify({
    summary: message.content[0].text
  }));
}
```

#### 9.4. Koszty backendu

| Serwis | Darmowy tier | Szacowany koszt przy 100 PRO users |
|--------|--------------|-----------------------------------|
| Cloudflare Workers | 100k req/dzień | $0 |
| Cloudflare R2 | 10GB storage | $0 |
| Claude API (Haiku) | - | ~$5-10/mies |
| LemonSqueezy | 5% + $0.50/transakcja | ~$4/transakcja |
| Neon PostgreSQL | 0.5GB | $0 |
| **RAZEM** | | **~$10-20/mies** |

#### 9.5. Zadania

- [ ] Setup projektu Cloudflare Workers
- [ ] Konto LemonSqueezy + produkt
- [ ] Implementacja `/v1/license/verify`
- [ ] Implementacja `/v1/license/activate`
- [ ] Implementacja `/v1/summarize`
- [ ] Implementacja `/v1/tags`
- [ ] Webhook LemonSqueezy dla nowych licencji
- [ ] Testy end-to-end
- [ ] Dokumentacja API
- [ ] Setup CI/CD dla backendu

---

## 5. Strategia testowania

### 5.1. Poziomy testów

```
┌─────────────────────────────────────────────────────────────────┐
│                    PIRAMIDA TESTÓW                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│                         ▲                                        │
│                        /█\     E2E Tests (Manual)                │
│                       /███\    - Pełny flow użytkownika          │
│                      /█████\   - Beta testing                    │
│                     ─────────                                    │
│                    /█████████\  Integration Tests                │
│                   /███████████\ - Workflow między modułami       │
│                  /█████████████\ - API endpoints                 │
│                 ───────────────                                  │
│                /█████████████████\  Unit Tests (pytest)          │
│               /███████████████████\ - Każda funkcja/klasa        │
│              /█████████████████████\ - Mockowanie zależności     │
│             ─────────────────────────                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2. Testy per faza

#### FAZA 1: Uniwersalne źródła nagrań

| Typ testu | Zakres | Plik testowy | Kryteria akceptacji |
|-----------|--------|--------------|---------------------|
| **Unit** | `UserSettings` dataclass | `tests/test_settings.py` | Load/save działa, migracja ze starej konfiguracji |
| **Unit** | `_should_process_volume()` | `tests/test_file_monitor.py` | Poprawne wykrywanie audio na różnych volumenach |
| **Unit** | `_has_audio_files()` | `tests/test_file_monitor.py` | Wykrywa .mp3, .wav, .m4a, .flac; ignoruje systemowe |
| **Integration** | Watch mode "auto" | `tests/test_integration.py` | Automatyczne wykrycie USB z audio |
| **Integration** | Watch mode "specific" | `tests/test_integration.py` | Tylko wybrane volumeny |
| **Manual** | Różne recordery | - | Test z Olympus, Zoom, SD card, pendrive |

**Checklist przed zakończeniem Fazy 1:**
- [x] `pytest tests/test_settings.py` - 100% pass ✅
- [x] `pytest tests/test_file_monitor.py` - 100% pass ✅
- [x] `pytest tests/test_file_monitor_integration.py` - 100% pass (11/11) ✅
- [ ] Test manualny: wykrycie 3 różnych urządzeń USB z audio ⚠️ *Wymagane przed produkcją*
- [ ] Test manualny: ignorowanie pendrive bez plików audio ⚠️ *Wymagane przed produkcją*

**Status:** Testy automatyczne zakończone. Testy manualne na fizycznych urządzeniach są niezbędne przed wydaniem v2.0.0 FREE, aby zweryfikować rzeczywiste zachowanie FSEvents i kompatybilność z różnymi systemami plików.

---

#### FAZA 2: System pobierania zależności

| Typ testu | Zakres | Plik testowy | Kryteria akceptacji |
|-----------|--------|--------------|---------------------|
| **Unit** | `DependencyDownloader` | `tests/test_downloader.py` | Poprawne URL-e, checksum verification |
| **Unit** | `is_whisper_installed()` | `tests/test_downloader.py` | Poprawne wykrywanie zainstalowanego whisper |
| **Unit** | `is_model_installed()` | `tests/test_downloader.py` | Poprawne wykrywanie modelu |
| **Integration** | Download whisper.cpp | `tests/test_downloader_integration.py` | Pobiera z GitHub, weryfikuje checksum |
| **Integration** | Download model | `tests/test_downloader_integration.py` | Pobiera z HuggingFace, ~466MB |
| **Manual** | Progress callback | - | UI pokazuje postęp pobierania |
| **Manual** | Offline mode | - | Graceful error gdy brak internetu |

**Checklist przed zakończeniem Fazy 2:**
- [ ] `pytest tests/test_downloader.py` - 100% pass
- [ ] Test integracyjny pobierania (może być slow, ~5min)
- [ ] Test manualny: przerwanie pobierania i wznowienie
- [ ] Test manualny: brak internetu → komunikat błędu

---

#### FAZA 3: First-Run Wizard

| Typ testu | Zakres | Plik testowy | Kryteria akceptacji |
|-----------|--------|--------------|---------------------|
| **Unit** | `SetupWizard` flow | `tests/test_wizard.py` | Poprawna kolejność kroków |
| **Unit** | `check_full_disk_access()` | `tests/test_permissions.py` | Wykrywa brak/obecność FDA |
| **Unit** | `WizardStep` enum | `tests/test_wizard.py` | Wszystkie kroki zdefiniowane |
| **Integration** | Wizard + Downloader | `tests/test_wizard_integration.py` | Wizard triggeruje pobieranie |
| **Manual** | Kompletny przepływ | - | Od Welcome do Finish bez błędów |
| **Manual** | Cancel/Back | - | Można cofać i anulować |
| **Manual** | FDA instrukcje | - | Link do System Preferences działa |

**Checklist przed zakończeniem Fazy 3:**
- [ ] `pytest tests/test_wizard.py` - 100% pass
- [ ] `pytest tests/test_permissions.py` - 100% pass
- [ ] Test manualny: pełny wizard na czystym systemie (<5 min)
- [ ] Test manualny: wizard z już pobranym whisper (skip download)

---

#### FAZA 4: Pakowanie py2app

| Typ testu | Zakres | Plik testowy | Kryteria akceptacji |
|-----------|--------|--------------|---------------------|
| **Build** | py2app build | `scripts/build_app.sh` | Build kończy się bez błędów |
| **Build** | App size | - | <20MB (bez modeli) |
| **Manual** | Launch .app | - | Aplikacja uruchamia się |
| **Manual** | Menu bar | - | Ikona pojawia się w pasku menu |
| **Manual** | All features | - | Transkrypcja działa z .app |
| **Manual** | Clean system | - | Działa na macOS bez Python |

**Checklist przed zakończeniem Fazy 4:**
- [ ] Build script kończy się sukcesem
- [ ] `.app` uruchamia się bez błędów
- [ ] `.app` rozmiar <20MB
- [ ] Test na czystym macOS (VM lub inny Mac)
- [ ] Wszystkie funkcje działają z bundled app

---

#### FAZA 5: Code Signing & Notaryzacja

| Typ testu | Zakres | Plik testowy | Kryteria akceptacji |
|-----------|--------|--------------|---------------------|
| **Script** | Sign script | `scripts/sign_and_notarize.sh` | Podpisuje bez błędów |
| **Verify** | Signature | `codesign --verify` | Valid signature |
| **Verify** | Notarization | `xcrun stapler validate` | Stapled ticket valid |
| **Manual** | Gatekeeper | - | Brak ostrzeżeń przy uruchomieniu |
| **Manual** | Other Mac | - | Działa na Macu bez dev tools |

**Checklist przed zakończeniem Fazy 5:**
- [ ] `codesign --verify --deep --strict dist/Malinche.app` → valid
- [ ] `spctl --assess --type exec dist/Malinche.app` → accepted
- [ ] Test na innym Macu: brak "unidentified developer"
- [ ] Test pierwszego uruchomienia: brak bloków Gatekeeper

---

#### FAZA 6: DMG & Release

| Typ testu | Zakres | Plik testowy | Kryteria akceptacji |
|-----------|--------|--------------|---------------------|
| **Build** | DMG creation | `scripts/create_dmg.sh` | DMG tworzy się poprawnie |
| **Verify** | DMG signature | `codesign --verify` | DMG podpisany |
| **Manual** | Drag & drop | - | Instalacja przez przeciągnięcie |
| **Manual** | GitHub Release | - | Release widoczny, download działa |
| **E2E** | Fresh install | - | Od pobrania do działającej transkrypcji |

**Checklist przed zakończeniem Fazy 6:**
- [ ] DMG tworzy się bez błędów
- [ ] DMG otwiera się i pokazuje app + Applications link
- [ ] Drag & drop do Applications działa
- [ ] GitHub Release utworzony z release notes
- [ ] Download link działa

---

#### FAZA 7: GUI Settings & Polish

| Typ testu | Zakres | Plik testowy | Kryteria akceptacji |
|-----------|--------|--------------|---------------------|
| **Unit** | `SettingsWindow` | `tests/test_settings_ui.py` | Okno otwiera się, zapisuje |
| **Manual** | Wszystkie opcje | - | Każda opcja działa |
| **Manual** | Update check | - | Sprawdza GitHub API |
| **Manual** | About window | - | Pokazuje wersję, linki |
| **UX** | Użytkownik nietechniczny | - | Zrozumiałe bez dokumentacji |

**Checklist przed zakończeniem Fazy 7:**
- [ ] Wszystkie opcje Settings działają
- [ ] Zmiany persistują po restarcie
- [ ] "Check for updates" wykrywa nową wersję
- [ ] UX review: test z osobą nietechniczną

---

#### FAZA 8: Infrastruktura Freemium

| Typ testu | Zakres | Plik testowy | Kryteria akceptacji |
|-----------|--------|--------------|---------------------|
| **Unit** | `FeatureFlags` | `tests/test_features.py` | FREE vs PRO flags poprawne |
| **Unit** | `LicenseManager` | `tests/test_license.py` | Verify, activate, cache |
| **Unit** | PRO gate w summarizer | `tests/test_summarizer.py` | Blokuje bez licencji |
| **Unit** | PRO gate w tagger | `tests/test_tagger.py` | Blokuje bez licencji |
| **Integration** | Offline mode | `tests/test_license_offline.py` | Cache działa 7 dni |
| **Manual** | PRO activation UI | - | Dialog aktywacji |
| **Manual** | "Upgrade to PRO" | - | Link do zakupu |

**Checklist przed zakończeniem Fazy 8:**
- [ ] `pytest tests/test_features.py` - 100% pass
- [ ] `pytest tests/test_license.py` - 100% pass
- [ ] FREE: transkrypcja działa, AI disabled
- [ ] Symulacja: aktywacja PRO → AI enabled
- [ ] Symulacja: offline → cache działa

---

#### FAZA 9: Backend PRO (opcjonalna)

| Typ testu | Zakres | Plik testowy | Kryteria akceptacji |
|-----------|--------|--------------|---------------------|
| **Unit** | License validation | `backend/tests/license.test.ts` | LemonSqueezy integration |
| **Unit** | Summarize endpoint | `backend/tests/summarize.test.ts` | Claude API call |
| **Unit** | Tags endpoint | `backend/tests/tags.test.ts` | Generuje tagi |
| **Integration** | App → Backend | `tests/test_pro_integration.py` | End-to-end PRO flow |
| **Load** | Rate limiting | - | 100 req/min per user |
| **Security** | Auth | - | Invalid key → 403 |

**Checklist przed zakończeniem Fazy 9:**
- [ ] Backend unit tests pass
- [ ] App → Backend integration działa
- [ ] Płatność LemonSqueezy → licencja aktywna
- [ ] Rate limiting działa
- [ ] Security audit: brak wycieku kluczy

---

### 5.3. Strategia beta testingu

```
┌─────────────────────────────────────────────────────────────────┐
│                    BETA TESTING TIMELINE                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  TYDZIEŃ 4                                                       │
│  ├─ Alpha (internal)                                             │
│  │  └─ 1-2 osoby z zespołu                                       │
│  │  └─ Focus: critical bugs, crashes                             │
│  │                                                               │
│  TYDZIEŃ 5                                                       │
│  ├─ Beta (external)                                              │
│  │  └─ 5-10 osób (znajomi, early adopters)                       │
│  │  └─ Focus: UX, edge cases, różne recordery                    │
│  │  └─ Feedback form (Google Forms)                              │
│  │                                                               │
│  ├─ RC (Release Candidate)                                       │
│  │  └─ Ostatnie poprawki                                         │
│  │  └─ Freeze features                                           │
│  │  └─ Only critical bugfixes                                    │
│  │                                                               │
│  RELEASE v2.0.0                                                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### Beta feedback form

Pytania dla beta testerów:
1. Na jakim macOS testujesz? (wersja)
2. Jaki recorder/kartę SD używasz?
3. Czy instalacja przebiegła bez problemów? (1-5)
4. Czy wizard był zrozumiały? (1-5)
5. Czy transkrypcja działa poprawnie? (Tak/Nie)
6. Ile czasu zajęła transkrypcja 5-min nagrania?
7. Czy wystąpiły jakieś błędy? (opisz)
8. Co byś zmienił/poprawił?

### 5.4. Test environment matrix

| macOS | Status | Priorytet | Uwagi |
|-------|--------|-----------|-------|
| 15 (Sequoia) | ✅ Required | P0 | Primary target |
| 14 (Sonoma) | ✅ Required | P0 | Most common |
| 13 (Ventura) | ✅ Required | P1 | Still supported |
| 12 (Monterey) | ⚠️ Optional | P2 | Minimum supported |
| <12 | ❌ Not supported | - | Too old |

| Architektura | Status | Uwagi |
|--------------|--------|-------|
| Apple Silicon (M1/M2/M3/M4) | ✅ Required | Primary target |
| Intel x86_64 | ❌ Not supported | Use source code |

| Urządzenia do testów |
|---------------------|
| Olympus LS-P1 |
| Zoom H1/H6 |
| Generic SD card |
| USB flash drive z audio |
| iPhone (jako recorder) |

### 5.5. Automatyzacja testów (CI/CD)

```yaml
# .github/workflows/tests.yml
name: Tests

on:
  push:
    branches: [main, develop, feature/*]
  pull_request:
    branches: [develop]

jobs:
  unit-tests:
    runs-on: macos-14  # Apple Silicon
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      
      - name: Run unit tests
        run: pytest tests/ -v --cov=src --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  build-test:
    runs-on: macos-14
    needs: unit-tests
    steps:
      - uses: actions/checkout@v4
      
      - name: Build app
        run: |
          pip install py2app
          python setup_app.py py2app
      
      - name: Verify build
        run: |
          test -d dist/Malinche.app
          du -sh dist/Malinche.app
```

### 5.6. Kryteria akceptacji release

#### v2.0.0 FREE - Definition of Done

| Kategoria | Kryterium | Status |
|-----------|-----------|--------|
| **Unit Tests** | 100% pass, >80% coverage | [ ] |
| **Integration** | Wszystkie scenariusze pass | [ ] |
| **Build** | .app buduje się bez błędów | [ ] |
| **Signing** | Notaryzacja przeszła | [ ] |
| **Beta** | <5 critical bugs, all fixed | [ ] |
| **Performance** | <3s startup, <30s/min transcription | [ ] |
| **UX** | 5/5 beta testerów: "łatwa instalacja" | [ ] |
| **Docs** | README, QUICKSTART aktualne | [ ] |

#### v2.1.0 PRO - Definition of Done

| Kategoria | Kryterium | Status |
|-----------|-----------|--------|
| **Backend** | All endpoints working | [ ] |
| **Payments** | LemonSqueezy integration | [ ] |
| **License** | Activation works | [ ] |
| **AI Features** | Summaries, tags working | [ ] |
| **Security** | No API key leaks | [ ] |

### 5.7. Bug tracking

**GitHub Issues labels:**
- `bug` - Błąd do naprawy
- `bug-critical` - Blokuje release
- `bug-minor` - Można wydać z tym bugiem
- `phase-X` - Dotyczy konkretnej fazy
- `beta-feedback` - Z beta testingu

**Bug triage:**
- **P0 (Critical)**: Fix przed release, blokuje użytkownika
- **P1 (High)**: Fix przed release jeśli możliwe
- **P2 (Medium)**: Może być w następnej wersji
- **P3 (Low)**: Nice to have

---

## 6. Szczegóły techniczne

### 5.1. Statyczny FFmpeg

**Źródło:** https://evermeet.cx/ffmpeg/ (trusted builds dla macOS)

Lub build własny:
```bash
# Minimalna kompilacja ffmpeg
./configure \
    --disable-everything \
    --enable-decoder=mp3,wav,aac,flac,pcm_s16le \
    --enable-demuxer=mp3,wav,aac,flac \
    --enable-protocol=file \
    --enable-filter=aresample \
    --disable-network \
    --disable-doc \
    --arch=arm64

make -j8
```

### 5.2. Whisper.cpp pre-built

**Hosting:** GitHub Releases w osobnym repo lub tym samym.

**Pliki:**
- `whisper-cli-arm64` (~10MB) - skompilowany z Core ML
- `ggml-small.bin` - hosted na Hugging Face (szybszy CDN)

### 5.3. Auto-update mechanism

**Opcja 1: Sparkle** (standardowy dla macOS apps)
- https://sparkle-project.org/
- Wymaga dodatkowej integracji

**Opcja 2: Manual check** (prostsza)
- GitHub API sprawdza najnowszy release
- Powiadomienie z linkiem do pobrania

**Rekomendacja:** Opcja 2 na start, Sparkle w przyszłości.

---

## 7. Harmonogram i kamienie milowe

### 6.1. Faza FREE (v2.0.0) - 4-5 tygodni

```
┌─────────────────────────────────────────────────────────────────┐
│ TYDZIEŃ 1                                                       │
├─────────────────────────────────────────────────────────────────┤
│ Pn-Śr: FAZA 1 - Uniwersalne źródła nagrań                       │
│        - Nowy system konfiguracji                               │
│        - Rozbudowa FileMonitor                                  │
│        - Testy                                                  │
│                                                                 │
│ Cz-Pt: FAZA 2 - System pobierania (start)                       │
│        - Klasa DependencyDownloader                             │
│        - GitHub Release setup                                   │
├─────────────────────────────────────────────────────────────────┤
│ TYDZIEŃ 2                                                       │
├─────────────────────────────────────────────────────────────────┤
│ Pn-Śr: FAZA 2 - System pobierania (koniec)                      │
│        - Build whisper.cpp w CI                                 │
│        - Testy pobierania                                       │
│                                                                 │
│ Cz-Pt: FAZA 3 - First-Run Wizard (start)                        │
│        - Struktura wizarda                                      │
│        - Ekrany powitania, pobierania                           │
├─────────────────────────────────────────────────────────────────┤
│ TYDZIEŃ 3                                                       │
├─────────────────────────────────────────────────────────────────┤
│ Pn-Wt: FAZA 3 - First-Run Wizard (koniec)                       │
│        - Pozostałe ekrany                                       │
│        - Testy przepływu                                        │
│                                                                 │
│ Śr-Pt: FAZA 4 - Pakowanie py2app                                │
│        - Konfiguracja py2app                                    │
│        - Build i optymalizacja                                  │
├─────────────────────────────────────────────────────────────────┤
│ TYDZIEŃ 4                                                       │
├─────────────────────────────────────────────────────────────────┤
│ Pn-Wt: FAZA 5 - Code Signing                                    │
│        - Setup certyfikatów                                     │
│        - Skrypty podpisywania                                   │
│                                                                 │
│ Śr:    FAZA 6 - DMG & Release                                   │
│        - Create-dmg                                             │
│        - GitHub Actions workflow                                │
│                                                                 │
│ Cz-Pt: FAZA 7 - GUI Settings & Polish (MVP)                     │
│        - Date picker, folder picker, About dialog              │
│        - Moduł UI przygotowany na redesign                     │
│        - Testy automatyczne                                     │
├─────────────────────────────────────────────────────────────────┤
│ TYDZIEŃ 5                                                       │
├─────────────────────────────────────────────────────────────────┤
│ Pn-Śr: FAZA 8 - Infrastruktura Freemium                         │
│        - Feature flags                                          │
│        - License manager (placeholder)                          │
│        - UI "Uaktywnij PRO"                                     │
│                                                                 │
│ Cz-Pt: FAZA 9 - Pełny redesign UI                              │
│        - Nowy instalator/wizard                                │
│        - Nowe menu aplikacji                                   │
│        - Nowe ikony i kolory                                    │
│        - Dark mode support                                      │
├─────────────────────────────────────────────────────────────────┤
│ TYDZIEŃ 6                                                       │
├─────────────────────────────────────────────────────────────────┤
│ Pn-Pt: Testy końcowe & Release FREE                             │
│        - Beta testing                                           │
│        - GitHub Release v2.0.0                                  │
│        - Ogłoszenie                                             │
└─────────────────────────────────────────────────────────────────┘

KAMIENIE MILOWE FREE:
  🏁 M1 (Koniec T1): Działająca konfiguracja użytkownika
  🏁 M2 (Koniec T2): Działający wizard z pobieraniem
  🏁 M3 (Koniec T3): Działający .app bundle
  🏁 M4 (Koniec T4): Podpisany DMG
  🏁 M5 (Koniec T5): GUI Settings & Polish (MVP)
  🏁 M6 (Koniec T5): Infrastruktura Freemium
  🏁 M7 (Koniec T6): Pełny redesign UI
  🏁 M8 (Koniec T6): 🎉 RELEASE v2.0.0 FREE
```

### 6.2. Faza PRO (v2.1.0) - 2-3 tygodnie (po FREE)

```
┌─────────────────────────────────────────────────────────────────┐
│ TYDZIEŃ 6-7 (po release FREE)                                   │
├─────────────────────────────────────────────────────────────────┤
│ FAZA 10 - Backend PRO                                           │
│        - Setup Cloudflare Workers                               │
│        - Integracja LemonSqueezy                                │
│        - API: /v1/license, /v1/summarize, /v1/tags              │
│        - Testowanie end-to-end                                  │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│ TYDZIEŃ 8                                                       │
├─────────────────────────────────────────────────────────────────┤
│ Aktywacja funkcji PRO w aplikacji                               │
│        - Podłączenie do backendu                                │
│        - Testy z prawdziwymi licencjami                         │
│        - Strona transrec.app                                    │
│        - Release v2.1.0 PRO                                     │
└─────────────────────────────────────────────────────────────────┘

KAMIENIE MILOWE PRO:
  🏁 M6 (Koniec T7): Backend działa
  🏁 M7 (Koniec T8): 🎉 RELEASE v2.1.0 PRO
```

### 6.3. Wizualizacja roadmap

```
         FREE                              PRO
    ┌─────────────┐                  ┌─────────────┐
    │   v2.0.0    │                  │   v2.1.0    │
    │             │                  │             │
T1  │ ▓▓▓ F1-F2   │                  │             │
T2  │ ▓▓▓ F2-F3   │                  │             │
T3  │ ▓▓▓ F3-F4   │                  │             │
T4  │ ▓▓▓ F5-F7   │                  │             │
T5  │ ▓▓▓ F8-F9   │                  │             │
T6  │ ▓▓▓ Testing │ ← RELEASE FREE   │             │
    │             │                  │             │
T7  │             │                  │ ▓▓▓ F10     │
T8  │             │                  │ ▓▓▓ Launch  │ ← RELEASE PRO
    └─────────────┘                  └─────────────┘
```

---

## 8. Ryzyka i mitygacja

### 7.1. Ryzyka techniczne (FREE)

| Ryzyko | Prawdopodobieństwo | Impact | Mitygacja |
|--------|-------------------|--------|-----------|
| py2app nie działa z rumps | Niskie | Wysoki | Przetestować wcześnie, alternatywa: PyInstaller z workarounds |
| Code signing błędy | Średnie | Średni | Dokładna dokumentacja, testy na wielu maszynach |
| Whisper.cpp build fail w CI | Średnie | Średni | Pre-built binaries jako backup |
| Rozmiar app > 100MB | Niskie | Niski | Agresywne excludes, download-on-demand |
| Apple odrzuci notaryzację | Niskie | Wysoki | Przestrzegać guidelines, testować przed release |
| Użytkownicy nie nadadzą FDA | Średnie | Wysoki | Tryb "manual" jako fallback |

### 7.2. Ryzyka biznesowe (PRO)

| Ryzyko | Prawdopodobieństwo | Impact | Mitygacja |
|--------|-------------------|--------|-----------|
| Niska konwersja FREE→PRO | Średnie | Średni | Jasna wartość PRO, demo AI w FREE (limited) |
| Wysokie koszty Claude API | Niskie | Średni | Limity per user, cache responses |
| Problemy z LemonSqueezy | Niskie | Wysoki | Plan B: Stripe + własny license server |
| Konkurencja (MacWhisper, etc.) | Średnie | Średni | Fokus na niszę (recordery), integracja Obsidian |
| Refundy | Niskie | Niski | Jasna dokumentacja, 30-day refund policy |
| Fraud (fake licenses) | Niskie | Niski | Server-side validation, rate limiting |

---

## 9. Koszty

### 8.1. Koszty wersji FREE

| Element | Koszt | Notatki |
|---------|-------|---------|
| Apple Developer Program | $99/rok | Wymagane dla notaryzacji |
| GitHub Actions (macOS) | ~$0-50/mies | Zależy od częstotliwości buildów |
| Domena | ~$15/rok | transrec.app |
| Hosting strony | $0 | GitHub Pages |
| **RAZEM FREE (pierwszy rok)** | **~$114-164** | |
| **RAZEM FREE (kolejne lata)** | **~$114/rok** | |

### 8.2. Dodatkowe koszty PRO (po uruchomieniu backendu)

| Element | Darmowy tier | Szacowany koszt (100 PRO users) |
|---------|--------------|----------------------------------|
| Cloudflare Workers | 100k req/dzień | $0 |
| Cloudflare R2 | 10GB | $0 |
| Claude API (Haiku) | - | ~$10-20/mies |
| PostgreSQL (Neon) | 0.5GB | $0 |
| LemonSqueezy | - | 5% + $0.50/transakcja |
| **RAZEM PRO infrastruktura** | | **~$10-30/mies** |

### 8.3. Projekcja przychodów PRO

| Scenariusz | Użytkownicy PRO | Przychód (lifetime $79) | Przychód netto (po prowizji) |
|------------|-----------------|-------------------------|------------------------------|
| Pesymistyczny | 10 | $790 | ~$700 |
| Realistyczny | 50 | $3,950 | ~$3,500 |
| Optymistyczny | 200 | $15,800 | ~$14,000 |

> **Break-even:** ~15-20 użytkowników PRO pokrywa roczne koszty infrastruktury

---

## 10. Kryteria sukcesu

### 9.1. Techniczne (FREE)

- [ ] .app uruchamia się na czystym macOS 12+ bez dodatkowych instalacji
- [ ] First-run wizard kończy się w <5 minut (z pobieraniem modelu)
- [ ] Transkrypcja działa z dowolnym USB/SD card
- [ ] Brak ostrzeżeń Gatekeeper
- [ ] Rozmiar DMG <20MB (bez modeli)
- [ ] Feature flags działają (PRO features zablokowane w FREE)

### 9.2. Techniczne (PRO)

- [ ] Licencja aktywuje się poprawnie
- [ ] AI summaries działają przez API
- [ ] Offline fallback (cache licencji 7 dni)
- [ ] Płatności przez LemonSqueezy działają

### 9.3. UX

- [ ] Użytkownik nietechniczny może zainstalować i skonfigurować bez pomocy
- [ ] Jasne komunikaty błędów
- [ ] Profesjonalny wygląd (ikona, DMG, menu)
- [ ] Jasna komunikacja FREE vs PRO (bez dark patterns)

### 9.4. Biznes (po 3 miesiącach od launch)

- [ ] >500 pobrań wersji FREE
- [ ] >10 użytkowników PRO
- [ ] <5% refund rate
- [ ] Feedback użytkowników zebrany

---

## 11. Strategia Git i repozytoria

### 10.1. Struktura repozytoriów

```
┌─────────────────────────────────────────────────────────────────┐
│                        REPOZYTORIA                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. transrec (PUBLIC) - GitHub                                  │
│     ├── Główna aplikacja (FREE + PRO client)                    │
│     ├── Open source (MIT license)                               │
│     └── Releases: DMG dla użytkowników                          │
│                                                                  │
│  2. transrec-backend (PRIVATE) - GitHub                         │
│     ├── API dla funkcji PRO                                     │
│     ├── Cloudflare Workers / Vercel                             │
│     └── Prywatne (zawiera API keys, logikę biznesową)           │
│                                                                  │
│  3. transrec.app (PUBLIC/PRIVATE) - GitHub                      │
│     ├── Strona marketingowa                                     │
│     └── Landing page, dokumentacja, pricing                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 10.2. Git Flow

```
main (produkcja)
│
├── v1.10.0 (obecny stan)
│
├── v2.0.0 (release FREE) ──────────────────────┐
│                                               │
├── v2.1.0 (release PRO)                        │
│                                               │
develop ◄───────────────────────────────────────┘
│
├── feature/faza-1-universal-sources
├── feature/faza-2-dependency-downloader
├── feature/faza-3-first-run-wizard
├── feature/faza-4-py2app
├── feature/faza-5-code-signing
├── feature/faza-6-dmg-release
├── feature/faza-7-settings-ui
├── feature/faza-8-freemium-infrastructure
│
└── hotfix/xxx (bugfixy na produkcji)
```

### 10.3. Strategia tagowania

```
v1.10.0          ← Obecna wersja (development)
v2.0.0-alpha.1   ← Pierwsza wersja do testów
v2.0.0-beta.1    ← Beta dla testerów
v2.0.0-rc.1      ← Release Candidate
v2.0.0           ← 🎉 Release FREE
v2.0.1           ← Bugfix
v2.1.0           ← 🎉 Release PRO
```

### 10.4. Workflow dla każdej fazy

```bash
# 1. Rozpocznij pracę nad fazą
git checkout develop
git checkout -b feature/faza-X-nazwa

# 2. Pracuj, commituj
git add .
git commit -m "v2.0.0: Opis zmiany"

# 3. Po zakończeniu fazy - merge do develop
git checkout develop
git merge feature/faza-X-nazwa
git push origin develop

# 4. Release - merge develop do main + tag
git checkout main
git merge develop
git tag -a v2.0.0 -m "Release v2.0.0 FREE"
git push origin main --tags
```

### 10.5. Zarządzanie kodem FREE vs PRO

```
✅ WYBÓR: Feature Flags (jeden codebase)

Uzasadnienie:
- Jeden codebase do utrzymania
- Łatwe testowanie obu wersji
- Użytkownicy FREE widzą co mogą odblokować
- Brak duplikacji kodu

NIE: Oddzielne branche dla FREE/PRO
- Trudne utrzymanie (merge conflicts)
- Duplikacja kodu
- Łatwo zapomnieć o backport bugfixów
```

---

## 12. Następne kroki

### Przed startem
1. **TERAZ:** Zatwierdzenie planu
2. **TERAZ:** Decyzja o modelu cenowym PRO (lifetime vs subscription)
3. **TERAZ:** Utworzenie brancha `develop`
4. **RÓWNOLEGLE:** Rejestracja Apple Developer Program ($99)

### Po zatwierdzeniu
5. **START:** Utworzenie `feature/faza-1-universal-sources`
6. **TYDZIEŃ 1-5:** Implementacja FREE (Fazy 1-8)
7. **RELEASE:** v2.0.0 FREE na GitHub
8. **TYDZIEŃ 6-8:** Implementacja PRO (Faza 10) + utworzenie `transrec-backend`
9. **RELEASE:** v2.1.0 PRO

### Decyzje do podjęcia

| Decyzja | Opcje | Rekomendacja |
|---------|-------|--------------|
| Model cenowy PRO | Lifetime $79 / Subskrypcja $8/mies | **Lifetime** (prostsze na start) |
| "Bring your own API key" | Tak / Nie | **Nie** (unikamy kanibalizacji PRO) |
| Open source license | MIT / GPL / BSL | **MIT** (zachęca do adopcji) |
| Git workflow | Git Flow / Trunk-based | **Git Flow** (main + develop + feature branches) |

---

## 13. Podsumowanie modelu Freemium

```
┌─────────────────────────────────────────────────────────────────┐
│                    STRATEGIA FREEMIUM                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  FREE (GitHub, open source MIT)                                 │
│  ├─ Pełna funkcjonalność transkrypcji                           │
│  ├─ Wszystkie formaty audio                                     │
│  ├─ Dowolne recordery/karty SD                                  │
│  └─ Eksport do Markdown/Obsidian                                │
│                                                                  │
│  PRO ($79 lifetime przez transrec.app)                          │
│  ├─ Wszystko z FREE +                                           │
│  ├─ AI Podsumowania (przez serwer)                              │
│  ├─ AI Tagi                                                     │
│  ├─ Cloud sync (przyszłość)                                     │
│  └─ Web dashboard (przyszłość)                                  │
│                                                                  │
│  STRATEGIA MONETYZACJI:                                         │
│  ├─ FREE buduje bazę użytkowników i reputację                   │
│  ├─ PRO dla power users którzy chcą AI features                 │
│  └─ Niski próg wejścia (lifetime, nie subscription)             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

**Autor:** Cursor AI  
**Wersja planu:** 1.1 (z modelem Freemium)  
**Zatwierdzenie:** [ ] Oczekuje na zatwierdzenie  
**Data zatwierdzenia:** ___________

