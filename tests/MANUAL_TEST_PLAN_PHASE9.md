# Manual Test Plan - Phase 9 + Multi-device

## UI (A1-A4)
- Verify app icon in Finder and mounted DMG volume icon.
- Verify menu bar icon switches for idle/scanning/transcribing/error.
- Build DMG and verify custom background appears.
- Open wizard and settings; verify unified text style and save flow.

## Multi-device dedup
- Device A transcribes sample audio in iCloud Vault.
- Wait for iCloud sync, on Device B run scan of same audio.
- Verify file is skipped (no second transcript in FREE tier).

## PRO versioning
- Enable PRO tier in test environment.
- Re-transcribe existing fingerprint with changed model/language.
- Verify `.v2.md` (then `.v3.md`) appears and includes `previous_version`.

## Migration
- Start with legacy markdown files without fingerprint.
- Run app first start migration.
- Verify `.malinche/index.json` is created and entries populated.

## Deferred (wymaga manualnie lub 2 Macow)
- UI-1..UI-9: app icon, DMG background, menu bar status icons, wizard/settings dialogs.
- Smoke bundla i instalacji: otwarcie `.dmg`, kopiowanie do `/Applications`, uruchomienie appki.
- Realny iCloud multi-device: M-1 i M-5 (synchronizacja i zachowanie offline na drugim Macu).
- Edge cases E-1..E-6: corrupted index, iCloud conflict copy, lock contention, very large files, missing metadata fallback, readonly vault.
