# Malinche

> **Version:** v2.0.0-beta.8 (development) → v2.0.0 (in preparation)

Automatic audio transcription system for any USB recorder or SD card on macOS.

## Features

### FREE (v2.0.0)
- **Auto-detection** — recognizes any external volume containing audio files
- **Smart scanning** — finds only new audio files since the last sync
- **Automatic transcription** — uses whisper.cpp with Core ML for maximum performance
- **Markdown output** — transcripts saved as `.md` files with YAML frontmatter
- **Menu bar app** — native macOS app with menu bar interface
- **Settings UI** — graphical configuration window

### PRO (v2.1.0 — planned)
- 🔒 **AI summaries** — automatic summary generation via Claude API
- 🔒 **Auto-tagging** — intelligent transcript tagging
- 🔒 **Auto-title** — file names generated from summary
- 🔒 **Cloud sync** — synchronization with Obsidian/iCloud

## Requirements

- macOS 12+ (Apple Silicon recommended for Core ML)
- Python 3.12+
- ffmpeg (installed automatically)
- whisper.cpp (installed automatically on first launch)

## Quick Start

For full instructions see **[QUICKSTART.md](QUICKSTART.md)**.

```bash
# 1. Clone the repository
git clone https://github.com/radektar/malinche.git
cd malinche

# 2. Create a virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app (whisper.cpp + ffmpeg are downloaded by the first-run wizard)
python -m src.menu_app
```

## Project Structure

```
src/                    source code (menu bar app, transcription, AI summary, UI)
tests/                  automated tests — run with: pytest
tests/integration/      E2E shell + Python integration scripts (require recorder)
scripts/                asset generators (icon, DMG background) + release pipeline
assets/                 icons, DMG background, menu bar template PNGs
Docs/                   architecture, beta plans, public distribution plan
Docs/testing-archive/   historical manual test checklists (alpha → milestones)
Docs/test-reports/      milestone test reports (M1, M2, M5)
Docs/archive/           legacy notes (Obsidian setup, migration summary)
setup_app.py            py2app entry — produces Malinche.app + DMG
Makefile                `make release` orchestrates build_release.sh
```

## Usage

### Menu bar app (recommended)

```bash
python -m src.menu_app
```

The app appears in the macOS menu bar with:
- Real-time status
- Open logs
- Retranscribe submenu
- Settings (General / Transcription / Disks / Maintenance tabs)
- PRO activation
- Quit

### CLI mode

```bash
python -m src.main
```

## Configuration

Configuration lives in the user settings file (managed via the Settings window) or via environment variables:

| Variable | Description | Default |
|---|---|---|
| `MALINCHE_TRANSCRIBE_DIR` | Output folder for transcripts | `~/Documents/Transcriptions` |
| `WHISPER_MODEL` | Whisper model | `small` |
| `WHISPER_LANGUAGE` | Transcription language | `pl` |

User data lives at `~/Library/Application Support/Malinche/` (config, logs, models, runtime).

For details see **[Docs/API.md](Docs/API.md)**.

## Documentation

| Document | Description |
|---|---|
| **[QUICKSTART.md](QUICKSTART.md)** | Quick start for developers |
| **[CHANGELOG.md](CHANGELOG.md)** | Release history |
| **[BACKLOG.md](BACKLOG.md)** | Planned features |
| **[Docs/ARCHITECTURE.md](Docs/ARCHITECTURE.md)** | System architecture |
| **[Docs/API.md](Docs/API.md)** | Module API reference |
| **[Docs/DEVELOPMENT.md](Docs/DEVELOPMENT.md)** | Developer guide |
| **[Docs/FULL_DISK_ACCESS_SETUP.md](Docs/FULL_DISK_ACCESS_SETUP.md)** | Full Disk Access setup |
| **[Docs/PUBLIC-DISTRIBUTION-PLAN.md](Docs/PUBLIC-DISTRIBUTION-PLAN.md)** | v2.0.0 distribution plan |

## Development

```bash
# Tests
pytest tests/ -v

# Linting
ruff check src/

# Build a signed DMG
make release
```

For details see **[Docs/DEVELOPMENT.md](Docs/DEVELOPMENT.md)**.

## Roadmap

### v2.0.0 FREE
- [x] Universal recorder support
- [x] First-run wizard
- [x] py2app packaging
- [x] DMG release (unsigned beta)
- [ ] Code signing & notarization

### v2.1.0 PRO
- [ ] AI summaries
- [ ] Auto-tagging
- [ ] Cloud sync
- [ ] License management

For details see **[Docs/PUBLIC-DISTRIBUTION-PLAN.md](Docs/PUBLIC-DISTRIBUTION-PLAN.md)**.

## Troubleshooting

### App does not detect the volume

1. Check that the volume is mounted: `ls /Volumes/`
2. Check the log: `tail -f ~/Library/Application\ Support/Malinche/logs/malinche.log`
3. Confirm the app has **Full Disk Access**: see **[Docs/FULL_DISK_ACCESS_SETUP.md](Docs/FULL_DISK_ACCESS_SETUP.md)**

### whisper.cpp not found

The first-run wizard downloads whisper-cli automatically. To re-trigger downloads, open Settings → Maintenance → "Re-download dependencies".

## License

MIT License

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/name`
3. Commit with a descriptive message ending with `[tests: pass]`
4. Open a Pull Request against `main`

For workflow details see **[Docs/DEVELOPMENT.md](Docs/DEVELOPMENT.md)**.

---

> **Related documents:**
> - Architecture: [Docs/ARCHITECTURE.md](Docs/ARCHITECTURE.md)
> - API: [Docs/API.md](Docs/API.md)
> - Development: [Docs/DEVELOPMENT.md](Docs/DEVELOPMENT.md)
> - v2.0.0 plan: [Docs/PUBLIC-DISTRIBUTION-PLAN.md](Docs/PUBLIC-DISTRIBUTION-PLAN.md)
