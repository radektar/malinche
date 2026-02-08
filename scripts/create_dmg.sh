#!/bin/bash
# scripts/create_dmg.sh
# Creates a professional DMG for Malinche

set -e

APP_NAME="Malinche"
VERSION=$(python3 -c "import setup_app; print('2.0.0')" 2>/dev/null || echo "2.0.0")
DMG_FILENAME="${APP_NAME}-${VERSION}-ARM64-UNSIGNED.dmg"
DIST_DIR="dist"
APP_PATH="${DIST_DIR}/${APP_NAME}.app"

echo "📦 Creating DMG for ${APP_NAME} v${VERSION}..."

# Check if .app exists
if [ ! -d "${APP_PATH}" ]; then
    echo "❌ Error: ${APP_PATH} not found. Build the app first using scripts/build_app.sh"
    exit 1
fi

# Remove old DMG if exists
rm -f "${DIST_DIR}/${DMG_FILENAME}"

# Create DMG
# Settings:
# - Window position: 200, 120
# - Window size: 600, 400
# - Icon size: 100
# - App icon position: 175, 190
# - Applications link position: 425, 190
create-dmg \
  --volname "${APP_NAME} Installer" \
  --window-pos 200 120 \
  --window-size 600 400 \
  --icon-size 100 \
  --icon "${APP_NAME}.app" 175 190 \
  --hide-extension "${APP_NAME}.app" \
  --app-drop-link 425 190 \
  --no-internet-enable \
  "${DIST_DIR}/${DMG_FILENAME}" \
  "${APP_PATH}"

echo "✅ DMG created: ${DIST_DIR}/${DMG_FILENAME}"
echo "📏 Size: $(du -sh "${DIST_DIR}/${DMG_FILENAME}" | cut -f1)"
