"""Setup configuration for py2app to build Transrec.app bundle."""

from setuptools import setup
import py2app
from pathlib import Path

# Entry point - menu bar application
APP = ['src/menu_app.py']

# Data files (icons, etc.)
DATA_FILES = []

# Add icon if it exists
icon_path = Path('assets/icon.icns')
if icon_path.exists():
    DATA_FILES.append(('', [str(icon_path)]))

# py2app options
OPTIONS = {
    'argv_emulation': False,  # Menu bar app doesn't need command line args
    'iconfile': 'assets/icon.icns' if icon_path.exists() else None,
    'plist': {
        'CFBundleName': 'Malinche',
        'CFBundleDisplayName': 'Malinche',
        'CFBundleIdentifier': 'com.malinche.app',
        'CFBundleVersion': '2.0.0',
        'CFBundleShortVersionString': '2.0.0',
        'LSUIElement': True,  # Menu bar only, no dock icon
        'LSMinimumSystemVersion': '12.0',  # macOS Monterey+
        'NSRequiresAquaSystemAppearance': False,  # Dark mode support
        'NSHighResolutionCapable': True,
        'NSAppleEventsUsageDescription': (
            'Malinche needs to control system events for file monitoring.'
        ),
        'NSFullDiskAccessUsageDescription': (
            'Malinche needs Full Disk Access to automatically detect '
            'external recorders and SD cards for transcription.'
        ),
    },
    'packages': [
        'rumps',
        'anthropic',
        'mutagen',
        'httpx',
        'dotenv',
        'click',
        'src',  # Include entire src package
    ],
    'includes': [
        'MacFSEvents',  # FSEvents wrapper
        'src.config',
        'src.config.settings',
        'src.config.defaults',
        'src.logger',
        'src.app_core',
        'src.app_status',
        'src.state_manager',
        'src.transcriber',
        'src.file_monitor',
        'src.markdown_generator',
        'src.summarizer',
        'src.tagger',
        'src.tag_index',
        'src.setup',
        'src.setup.downloader',
        'src.setup.wizard',
        'src.setup.permissions',
        'src.setup.errors',
        'src.setup.checksums',
        'src.env_loader',
    ],
    'excludes': [
        'tkinter',  # GUI not used
        'matplotlib',  # Graphics not used
        'PIL',  # Image processing not used
        'numpy',  # Scientific computing not used
        'scipy',  # Scientific computing not used
        'pandas',  # Data analysis not used
        'IPython',  # Interactive shell not used
        'jupyter',  # Notebooks not used
        'test',  # Test modules
        'tests',  # Test modules
        'pytest',  # Test framework
        'unittest',  # Test framework
    ],
    'arch': 'arm64',  # Apple Silicon only
    'optimize': 1,  # Bytecode optimization (reduced from 2 to avoid segfault)
    'strip': False,  # Don't strip symbols - avoids segfault during import checking
}

setup(
    name='Malinche',
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)

