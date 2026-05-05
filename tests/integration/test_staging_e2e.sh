#!/bin/bash
# End-to-end test script for staging workflow
# Run this script when recorder is connected

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/../.."

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "=========================================="
echo "  Olympus Transcriber - E2E Staging Test"
echo "=========================================="
echo ""

# Step 1: Check recorder
echo -e "${YELLOW}[1/7] Checking recorder connection...${NC}"
if [ ! -d "/Volumes/LS-P1" ]; then
    echo -e "${RED}✗ Recorder not found at /Volumes/LS-P1${NC}"
    echo "  Please connect the recorder and try again"
    exit 1
fi
echo -e "${GREEN}✓ Recorder found at /Volumes/LS-P1${NC}"

# Count audio files
AUDIO_FILES=$(find /Volumes/LS-P1 -name "*.MP3" -o -name "*.mp3" 2>/dev/null | wc -l | tr -d ' ')
echo "  Found $AUDIO_FILES audio file(s) on recorder"
if [ "$AUDIO_FILES" -gt 0 ]; then
    echo "  Sample files:"
    find /Volumes/LS-P1 -name "*.MP3" -o -name "*.mp3" 2>/dev/null | head -3 | sed 's/^/    /'
fi
echo ""

# Step 2: Stop any running daemon
echo -e "${YELLOW}[2/7] Stopping any running daemon...${NC}"
launchctl unload ~/Library/LaunchAgents/com.user.olympus-transcriber.plist 2>/dev/null || true
pkill -f "python.*src/main.py" 2>/dev/null || true
sleep 2
echo -e "${GREEN}✓ Daemon stopped${NC}"
echo ""

# Step 3: Cleanup test environment
echo -e "${YELLOW}[3/7] Cleaning up test environment...${NC}"
# Backup log
if [ -f ~/Library/Logs/olympus_transcriber.log ]; then
    cp ~/Library/Logs/olympus_transcriber.log ~/Library/Logs/olympus_transcriber.log.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || true
fi
# Clear log
> ~/Library/Logs/olympus_transcriber.log 2>/dev/null || true

# Clear state file
rm -f ~/.olympus_transcriber_state.json

# Clear staging directory (but keep the directory itself)
rm -rf ~/.olympus_transcriber/recordings/* 2>/dev/null || true

echo -e "${GREEN}✓ Cleanup complete${NC}"
echo "  - Log cleared"
echo "  - State file removed"
echo "  - Staging directory cleared"
echo ""

# Step 4: Verify configuration
echo -e "${YELLOW}[4/7] Verifying configuration...${NC}"
python3 << 'EOF'
from src.config import config
print(f"TRANSCRIBE_DIR: {config.TRANSCRIBE_DIR}")
print(f"LOCAL_RECORDINGS_DIR: {config.LOCAL_RECORDINGS_DIR}")
print(f"STATE_FILE: {config.STATE_FILE}")
print(f"LOG_FILE: {config.LOG_FILE}")
assert config.LOCAL_RECORDINGS_DIR is not None, "LOCAL_RECORDINGS_DIR not configured!"
print("✓ Configuration OK")
EOF
echo ""

# Step 5: Start application in background
echo -e "${YELLOW}[5/7] Starting application (will run for 120 seconds)...${NC}"
source venv/bin/activate
export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"
python src/main.py &
APP_PID=$!
echo "  Application PID: $APP_PID"
echo "  Monitoring logs in real-time..."
echo ""

# Wait a bit for startup
sleep 5

# Monitor logs
echo -e "${BLUE}=== Recent log entries ===${NC}"
tail -30 ~/Library/Logs/olympus_transcriber.log | grep -E "(Staging|Staged|stage|batch|Recorder|Processing|Complete)" || echo "  (waiting for activity...)"
echo ""

# Let it run
echo "  Application running... (will stop after 120 seconds)"
echo "  Watch logs in another terminal: tail -f ~/Library/Logs/olympus_transcriber.log"
sleep 115

# Stop application
echo ""
echo "  Stopping application..."
kill $APP_PID 2>/dev/null || true
wait $APP_PID 2>/dev/null || true
sleep 2
echo -e "${GREEN}✓ Application stopped${NC}"
echo ""

# Step 6: Verify results
echo -e "${YELLOW}[6/7] Verifying test results...${NC}"
echo ""

# Check staging directory
STAGED_COUNT=$(ls ~/.olympus_transcriber/recordings/*.MP3 ~/.olympus_transcriber/recordings/*.mp3 2>/dev/null | wc -l | tr -d ' ')
if [ "$STAGED_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✓ Staging directory contains $STAGED_COUNT file(s)${NC}"
    echo "  Files:"
    ls -lh ~/.olympus_transcriber/recordings/ | grep -E "\.(MP3|mp3)$" | head -5 | awk '{print "    " $9 " (" $5 ")"}'
else
    echo -e "${YELLOW}⚠ No files in staging directory${NC}"
fi
echo ""

# Check state file
if [ -f ~/.olympus_transcriber_state.json ]; then
    echo -e "${GREEN}✓ State file exists${NC}"
    echo "  Content:"
    cat ~/.olympus_transcriber_state.json | python3 -m json.tool | sed 's/^/    /'
else
    echo -e "${YELLOW}⚠ State file not created (may be OK if batch had failures)${NC}"
fi
echo ""

# Check transcription directory
TRANSCRIPT_COUNT=$(ls ~/Library/Mobile\ Documents/iCloud~md~obsidian/Documents/Obsidian/11-Transcripts/*.md 2>/dev/null | wc -l | tr -d ' ')
if [ "$TRANSCRIPT_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✓ Found $TRANSCRIPT_COUNT markdown file(s) in transcription directory${NC}"
    echo "  Recent files:"
    ls -lt ~/Library/Mobile\ Documents/iCloud~md~obsidian/Documents/Obsidian/11-Transcripts/*.md 2>/dev/null | head -3 | awk '{print "    " $9}' | xargs -I {} basename {}
else
    echo -e "${YELLOW}⚠ No markdown files found in transcription directory${NC}"
fi
echo ""

# Step 7: Analyze logs
echo -e "${YELLOW}[7/7] Analyzing logs...${NC}"
echo ""

# Staging activity
STAGING_LOGS=$(grep -i "stage\|staged" ~/Library/Logs/olympus_transcriber.log | wc -l | tr -d ' ')
if [ "$STAGING_LOGS" -gt 0 ]; then
    echo -e "${GREEN}✓ Found $STAGING_LOGS staging-related log entries${NC}"
    echo ""
    echo "  Sample staging logs:"
    grep -i "stage\|staged" ~/Library/Logs/olympus_transcriber.log | tail -5 | sed 's/^/    /'
else
    echo -e "${YELLOW}⚠ No staging activity in logs${NC}"
fi
echo ""

# Batch results
BATCH_LOGS=$(grep -i "batch complete" ~/Library/Logs/olympus_transcriber.log | tail -1)
if [ -n "$BATCH_LOGS" ]; then
    echo -e "${GREEN}✓ Batch processing completed${NC}"
    echo "  $BATCH_LOGS" | sed 's/^/    /'
else
    echo -e "${YELLOW}⚠ No batch completion log found${NC}"
fi
echo ""

# Errors (excluding expected staging failures)
ERROR_COUNT=$(grep -i "error\|failed\|✗" ~/Library/Logs/olympus_transcriber.log | grep -v "Could not stage" | grep -v "WARNING" | wc -l | tr -d ' ')
if [ "$ERROR_COUNT" -gt 0 ]; then
    echo -e "${YELLOW}⚠ Found $ERROR_COUNT error(s) in logs (excluding staging warnings)${NC}"
    echo "  Sample errors:"
    grep -i "error\|failed\|✗" ~/Library/Logs/olympus_transcriber.log | grep -v "Could not stage" | grep -v "WARNING" | tail -3 | sed 's/^/    /'
else
    echo -e "${GREEN}✓ No critical errors found${NC}"
fi
echo ""

# Summary
echo "=========================================="
echo -e "${GREEN}Test Summary${NC}"
echo "=========================================="
echo "  Staged files: $STAGED_COUNT"
echo "  Markdown files: $TRANSCRIPT_COUNT"
echo "  Staging log entries: $STAGING_LOGS"
echo "  Errors: $ERROR_COUNT"
echo ""
echo "To view full logs:"
echo "  tail -f ~/Library/Logs/olympus_transcriber.log"
echo ""
echo "To check staging directory:"
echo "  ls -lah ~/.olympus_transcriber/recordings/"
echo ""
echo "To check state:"
echo "  cat ~/.olympus_transcriber_state.json"
echo ""

