#!/bin/bash
# scripts/build_release.sh
# Orchestrates the full build and release pipeline for Malinche

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

APP_NAME="Malinche"
PLATFORM="$(uname -s)"

echo "🚀 Starting release build for ${APP_NAME}..."

case "${PLATFORM}" in
    Darwin)
        echo "🍎 Platform: macOS (Darwin)"
        
        # 1. Build .app bundle
        echo "--- Step 1: Building .app bundle ---"
        bash scripts/build_app.sh
        
        # 2. Create DMG
        echo "--- Step 2: Creating DMG installer ---"
        bash scripts/create_dmg.sh
        
        # 3. Generate checksums
        echo "--- Step 3: Generating checksums ---"
        VERSION=$(python3 -c "import setup_app; print(setup_app.APP_VERSION)" 2>/dev/null || echo "2.0.0-alpha.6")
        DMG_FILE="dist/${APP_NAME}-${VERSION}-ARM64-UNSIGNED.dmg"
        
        if [ -f "${DMG_FILE}" ]; then
            shasum -a 256 "${DMG_FILE}" > "${DMG_FILE}.sha256"
            echo "✅ Checksum generated: ${DMG_FILE}.sha256"
            echo "   $(cat "${DMG_FILE}.sha256")"
        fi
        
        echo ""
        echo "🎉 Release build complete!"
        echo "📂 Location: dist/"
        ;;
    
    MINGW*|MSYS*|CYGWIN*)
        echo "🪟 Platform: Windows"
        echo "❌ Error: Windows build pipeline is not yet implemented."
        echo "   Planned: PyInstaller + NSIS/Inno Setup. See BACKLOG.md"
        exit 1
        ;;
        
    *)
        echo "❓ Platform: ${PLATFORM} (Unknown)"
        echo "❌ Error: Unsupported platform for release build."
        exit 1
        ;;
esac
