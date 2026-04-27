#!/bin/bash
# Build script for Malinche.app using py2app
# This script builds a macOS application bundle ready for distribution

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${PROJECT_ROOT}"

echo "🔨 Building Malinche.app..."
echo "Project root: ${PROJECT_ROOT}"

# Check if we're on macOS
if [[ "$(uname)" != "Darwin" ]]; then
    echo "❌ Error: This script must be run on macOS"
    exit 1
fi

# Check if we're on Apple Silicon
ARCH=$(uname -m)
if [[ "${ARCH}" != "arm64" ]]; then
    echo "⚠️  Warning: Building on ${ARCH}, but bundle will be for arm64 only"
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
else
    echo "⚠️  Warning: venv not found, using system Python"
fi

# Check if py2app is installed
if ! python3 -c "import py2app" 2>/dev/null; then
    echo "📥 Installing py2app..."
    pip install py2app
else
    echo "✅ py2app already installed"
fi

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build dist

# Check if icon exists
if [ ! -f "assets/icon.icns" ]; then
    echo "⚠️  Warning: assets/icon.icns not found, building without icon"
fi

# Build the application
echo "🔨 Running py2app..."
# Note: py2app may segfault during import checking, but bundle is usually complete
# We check for bundle existence after build regardless of exit code
set +e  # Temporarily disable exit on error
python3 setup_app.py py2app
BUILD_EXIT_CODE=$?
set -e  # Re-enable exit on error

# Verify build - bundle should exist even if build ended with segfault
if [ ! -d "dist/Malinche.app" ]; then
    echo "❌ Error: Build failed - Malinche.app not found"
    exit 1
fi

# Warn if build ended with segfault but bundle exists
if [ $BUILD_EXIT_CODE -ne 0 ]; then
    echo "⚠️  Warning: Build ended with exit code $BUILD_EXIT_CODE (may be segfault during import checking)"
    echo "   Bundle exists and will be verified..."
fi

# Check bundle size
BUNDLE_SIZE=$(du -sh dist/Malinche.app | cut -f1)
BUNDLE_SIZE_BYTES=$(du -sk dist/Malinche.app | cut -f1)
BUNDLE_SIZE_MB=$((BUNDLE_SIZE_BYTES / 1024))

echo "✅ Build complete!"
echo "📦 Bundle location: dist/Malinche.app"
echo "📏 Bundle size: ${BUNDLE_SIZE} (${BUNDLE_SIZE_MB} MB)"

# Check if size is reasonable (<20MB without models)
if [ "${BUNDLE_SIZE_MB}" -gt 20 ]; then
    echo "⚠️  Warning: Bundle size (${BUNDLE_SIZE_MB} MB) exceeds 20MB target"
    echo "   Consider optimizing excludes in setup_app.py"
else
    echo "✅ Bundle size is within target (<20MB)"
fi

# Verify bundle structure
echo "🔍 Verifying bundle structure..."
if [ ! -f "dist/Malinche.app/Contents/Info.plist" ]; then
    echo "❌ Error: Info.plist not found"
    exit 1
fi

if [ ! -f "dist/Malinche.app/Contents/MacOS/Malinche" ]; then
    echo "❌ Error: Main executable not found"
    exit 1
fi

# Verify critical Python packages are bundled
REQUIRED_PKGS=("anthropic" "rumps" "mutagen" "httpx" "click" "dotenv")
BUNDLE_SITE="dist/Malinche.app/Contents/Resources/lib/python3.12"
for pkg in "${REQUIRED_PKGS[@]}"; do
    if [ ! -d "${BUNDLE_SITE}/${pkg}" ]; then
        echo "❌ Error: required package '${pkg}' not found in bundle"
        exit 1
    fi
done
echo "✅ All required Python packages verified in bundle"

# Make executable
chmod +x dist/Malinche.app/Contents/MacOS/Malinche

# Sign bundle (Developer ID if available, otherwise ad-hoc for local installs)
if [ -n "${APPLE_DEVELOPER_ID:-}" ]; then
    echo "🔏 Signing app with Developer ID: ${APPLE_DEVELOPER_ID}"
    codesign --force --deep --sign "${APPLE_DEVELOPER_ID}" dist/Malinche.app
else
    echo "🔏 Signing app with ad-hoc certificate (local install mode)"
    codesign --force --deep --sign - dist/Malinche.app
fi

echo ""
echo "✅ Build verification complete!"
echo ""
echo "To test the app:"
echo "  open dist/Malinche.app"
echo ""
echo "To check bundle info:"
echo "  plutil -p dist/Malinche.app/Contents/Info.plist"

