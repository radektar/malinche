# Obsidian Integration

## ✅ Konfiguracja Wykonana

Olympus Transcriber został skonfigurowany do zapisywania transkrypcji **bezpośrednio w Obsidian vault**.

### 📂 Lokalizacja Transkrypcji

Wszystkie transkrypcje będą zapisywane w:

```
~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Obsidian/11-Transcripts/
```

Czyli w folderze **`11-Transcripts`** w Twoim Obsidian vault.

### 🎯 Jak To Działa

1. **Podłączasz** Olympus LS-P1 do Mac
2. System **automatycznie wykrywa** nowe pliki audio
3. MacWhisper **transkrybuje** nagrania
4. Transkrypcje **pojawiają się bezpośrednio w Obsidian** jako pliki `.txt`

### 📝 Format Plików

Dla każdego pliku audio:
- `recording001.mp3` → `11-Transcripts/recording001.txt`
- `interview.wav` → `11-Transcripts/interview.txt`
- `notes.m4a` → `11-Transcripts/notes.txt`

### 🔄 Workflow w Obsidian

**Po transkrypcji możesz:**

1. **Otworzyć transkrypcję** w Obsidian
2. **Edytować i formatować** tekst
3. **Dodać tagi i linki** do innych notatek
4. **Utworzyć połączenia** między transkrypcjami
5. **Użyć w Daily Notes** lub innych systemach

### 📊 Przykładowy Workflow

```markdown
# Meeting Notes 2025-11-19

## Audio Transcription
![[recording001.txt]]

## Key Points
- [[Project Alpha]] deadline discussion
- [[Team]] assignments
- [[Budget]] review

## Action Items
- [ ] Follow up with @john
- [ ] Send report by Friday

#meeting #project-alpha #2025-11
```

### ⚙️ Zmiana Lokalizacji (Opcjonalnie)

Jeśli chcesz zmienić folder docelowy, edytuj `src/config.py`:

```python
# Linia 53-57 w src/config.py
if self.TRANSCRIBE_DIR is None:
    # Obsidian vault path for transcriptions
    self.TRANSCRIBE_DIR = Path(
        "/Users/radoslawtaraszka/Library/Mobile Documents/"
        "iCloud~md~obsidian/Documents/Obsidian/11-Transcripts"
    )
```

Możesz zmienić na inny folder w Obsidian, np:
- `10-Inbox` - dla nowych transkrypcji do przetworzenia
- `20-Projects/Audio` - dla transkrypcji projektowych
- `30-Archive/Transcripts` - dla archiwalnych nagrań

### 🔍 Weryfikacja

Sprawdź czy folder istnieje i jest dostępny:

```bash
ls -la ~/Library/Mobile\ Documents/iCloud~md~obsidian/Documents/Obsidian/11-Transcripts/
```

### ✨ Korzyści Integracji z Obsidian

✅ **Zero friction** - transkrypcje od razu w vault  
✅ **Natychmiastowy dostęp** - od razu widoczne w Obsidian  
✅ **Linkowanie** - łatwe tworzenie połączeń  
✅ **Tagowanie** - organizacja przez tagi  
✅ **Wyszukiwanie** - Obsidian search works  
✅ **Backup** - automatycznie w iCloud  
✅ **Edycja** - natychmiastowa możliwość edycji  

### 🚀 Ready to Use!

Konfiguracja jest kompletna. Po uruchomieniu aplikacji:

```bash
cd ~/CODE/Olympus_transcription
source venv/bin/activate
export PYTHONPATH=$PWD
python src/main.py
```

Lub zainstaluj jako daemon:

```bash
./setup.sh
```

I podłącz recorder - transkrypcje pojawią się w Obsidian! 🎉

---

**Utworzono:** 2025-11-19  
**Lokalizacja:** `11-Transcripts` folder w Obsidian vault  
**Status:** ✅ Gotowe do użycia






