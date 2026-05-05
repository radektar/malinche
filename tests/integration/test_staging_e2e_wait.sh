#!/bin/bash
# End-to-end test script for staging workflow
# This version waits for recorder to be connected

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/../.."

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "=========================================="
echo "  Olympus Transcriber - E2E Staging Test"
echo "  (Waiting for recorder)"
echo "=========================================="
echo ""

# Wait for recorder
echo -e "${YELLOW}Waiting for recorder to be connected...${NC}"
echo "  Please connect your Olympus LS-P1 recorder"
echo ""

while [ ! -d "/Volumes/LS-P1" ]; do
    echo -n "."
    sleep 2
done

echo ""
echo -e "${GREEN}✓ Recorder detected!${NC}"
echo ""

# Run the main test script
exec "$SCRIPT_DIR/test_staging_e2e.sh"

