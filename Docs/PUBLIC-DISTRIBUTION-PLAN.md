# 📦 Plan Dystrybucji Publicznej - Malinche

**Wersja:** 1.2 (Freemium - Subscription Model)  
**Data utworzenia:** 2025-12-17  
**Ostatnia aktualizacja:** 2026-02-08  
**Status:** DRAFT - Do zatwierdzenia  
**Model:** Freemium (FREE open-source + PRO subskrypcja)

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
- **Modelem Freemium** (FREE + PRO Individual + PRO Org)

### Model biznesowy

| Wersja | Cena | Funkcje | Limity |
|--------|------|---------|--------|
| **FREE** | $0 (open source) | Transkrypcja lokalna, eksport MD, dowolne recordery | Brak |
| **PRO Individual** | Miesięczna subskrypcja | FREE + AI summaries, AI tags, Diarization | 300 min/mies |
| **PRO Organization** | Miesięczna subskrypcja | PRO + Knowledge Base, Shared Lexicon, Cloud Sync | 1000+ min/mies |

### Kluczowe decyzje techniczne

| Aspekt | Decyzja | Uzasadnienie |
|--------|---------|--------------|
| **Narzędzie pakowania** | py2app + rumps | Dedykowane dla menu bar apps, lepsze niż PyInstaller |
| **Architektura CPU** | Tylko Apple Silicon (M1/M2/M3/M4) | Uproszczenie buildu, 80%+ nowych Mac'ów |
| **Whisper.cpp** | Download on first run | Mniejsza paczka początkowa (~15MB vs 550MB) |
| **FFmpeg** | Bundlowany statycznie | Bez dependency na Homebrew |
| **Code signing** | Tak ($99/rok) | Profesjonalne UX bez ostrzeżeń Gatekeeper |
| **Backend PRO** | FastAPI (Python) | Współdzielona logika z klientem, łatwa integracja AI |
| **Płatności** | LemonSqueezy / Stripe | Tax compliance, obsługa subskrypcji i kluczy API |

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
│                         MALINCHE FREE                                   │
│                     (Open Source - GitHub)                               │
│ ├─────────────────────────────────────────────────────────────────────────┤
│ ✅ Automatyczne wykrywanie recorderów/kart SD                          │
│ ✅ Transkrypcja lokalna (whisper.cpp)                                  │
│ ✅ Podstawowe tagi (#transcription, #audio)                            │
│ ✅ Export do Markdown                                                   │
│ ✅ Menu bar app                                                        │
│ ✅ First-run wizard                                                    │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                         MALINCHE PRO INDIVIDUAL                         │
│                    (Miesięczna subskrypcja)                             │
│ ├─────────────────────────────────────────────────────────────────────────┤
│ ⭐ AI Podsumowania (przez serwer z Claude/GPT)                         │
│ ⭐ Inteligentne tagi AI                                                │
│ ⭐ Automatyczne nazewnictwo plików z AI                                │
│ ⭐ Diaryzacja rozmówców (lokalna/serwerowa)                            │
│ 📊 Limit: 300 minut przetwarzania miesięcznie                          │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                         MALINCHE PRO ORGANIZATION                       │
│                    (Miesięczna subskrypcja)                             │
│ ├─────────────────────────────────────────────────────────────────────────┤
│ 🏢 Współdzielona baza rozmówców                                        │
│ 🏢 Słownik dziedzinowy (Custom Lexicon)                                 │
│ 🏢 Baza Wiedzy (Knowledge Base extraction)                              │
│ 🏢 Cloud sync (Obsidian, S3, Azure)                                     │
│ 📊 Limit: 1000+ minut przetwarzania miesięcznie                        │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Architektura docelowa

### 3.1. Struktura aplikacji (v2.0.0)

```
~/Applications/
└── Malinche.app/                        (~15MB download)
    └── Contents/
        ├── MacOS/
        │   └── Malinche                 (główny plik wykonywalny)
        ├── Resources/
        │   ├── icon.icns
        │   └── ffmpeg                   (statyczny, ~15MB)

~/Library/Application Support/Malinche/
├── whisper.cpp/                         (pobierane przy 1. uruchomieniu)
├── models/                              (modele GGML)
├── config.json                          (ustawienia użytkownika)
├── license.json                         (klucz licencyjny)
└── license_cache.json                   (cache weryfikacji offline)
```

---

## 4. Plan implementacji - Fazy

### FAZA 1: Uniwersalne źródła nagrań (ZAKOŃCZONA ✅)
Aplikacja wykrywa dowolny dysk/kartę SD. Nowy system `UserSettings`.

### FAZA 2: System pobierania zależności (ZAKOŃCZONA ✅)
Automatyczne pobieranie whisper.cpp i modeli z GitHub/HuggingFace.

### FAZA 3: First-Run Wizard (ZAKOŃCZONA ✅)
Przyjazny tutorial i konfiguracja wstępna.

### FAZA 4: Pakowanie py2app (ZAKOŃCZONA ✅)
Tworzenie .app bundle.

### FAZA 5: Code Signing & Notaryzacja (W TOKU)
Podpisywanie aplikacji certyfikatem Apple Developer.

### FAZA 6: Profesjonalny DMG (ZAKOŃCZONA ✅ - wersja testowa)
Skrypty budowania DMG i instrukcje dla testerów.

### FAZA 7: GUI Settings & Polish (ZAKOŃCZONA ✅)
Menu ustawień, wybór folderów, języka i modeli.

### FAZA 8: Infrastruktura Freemium (ZAKOŃCZONA ✅)
- System Feature Flags (FREE/PRO/PRO_ORG).
- License Manager z obsługą offline cache (7 dni).
- PRO Gates w summarizerze i taggerze.
- UI aktywacji PRO w menu paska stanu.

---

## 5. Strategia testowania

### 5.1. Wymagania Coverage
- **Minimum 80% coverage** dla wszystkich nowych modułów.
- **100% coverage** dla krytycznych modułów: `src/config/settings.py`, `src/config/license.py`, `src/core/file_monitor.py`.

### 5.2. Testy manualne (Faza 8)
- [ ] Aktywacja nieprawidłowego klucza → błąd UI.
- [ ] Symulacja braku internetu → użycie cache'u licencji.
- [ ] Wygaśnięcie cache'u (7 dni) → powrót do FREE.
- [ ] Próba użycia AI w wersji FREE → log "Require PRO" i brak akcji.

---

## 9. Koszty

### 8.1. Koszty infrastruktury (PRO)

| Serwis | Darmowy tier | Szacowany koszt (100 PRO users) |
|--------|--------------|----------------------------------|
| Claude API (Haiku) | - | ~$10-20/mies |
| Diarization (VAD/Embeddings) | Lokalnie | $0 (koszt CPU użytkownika) |
| Hosting API | CF Workers / Fly.io | $0-5/mies |
| **RAZEM** | | **~$15-25/mies** |

### 8.2. Projekcja przychodów

- Model: Subskrypcja (np. $8/mies Individual, $25/mies Organization).
- Próg rentowności (break-even): ~5-10 aktywnych subskrypcji PRO.

---

## 13. Podsumowanie modelu Freemium

```
┌─────────────────────────────────────────────────────────────────┐
│                    STRATEGIA FREEMIUM                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  FREE (GitHub, MIT)                                              │
│  ├─ Lokalna transkrypcja bez limitów                             │
│  └─ Eksport do Markdown                                          │
│                                                                  │
│  PRO INDIVIDUAL (Subskrypcja miesięczna)                         │
│  ├─ AI Summaries & Smart Tags                                    │
│  ├─ Diaryzacja rozmówców (Speaker ID)                            │
│  └─ Limit: 300 minut przetwarzania/mies                          │
│                                                                  │
│  PRO ORGANIZATION (Subskrypcja miesięczna)                       │
│  ├─ Baza Wiedzy (Knowledge Base)                                 │
│  ├─ Słownik dziedzinowy (Lexicon)                                │
│  └─ Cloud Sync & Shared Speaker DB                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

**Autor:** Cursor AI  
**Wersja planu:** 1.2 (Subscription Model)  
**Zatwierdzenie:** [ ] Oczekuje na zatwierdzenie  
**Data zatwierdzenia:** 2026-02-08
