#!/bin/bash
# Reset Malinche memory state (last_sync timestamp)
#
# Użycie:
#   bash scripts/reset_recorder_memory.sh            # domyślna data 2025-11-18
#   bash scripts/reset_recorder_memory.sh YYYY-MM-DD # własna data
#
# Skrypt:
# - robi backup istniejącego pliku stanu do *.backup
# - ustawia last_sync na podaną datę o 00:00:00
# - NIE uruchamia daemona ani aplikacji – to robisz osobno

set -e

TARGET_DATE="${1:-2025-11-18}"
STATE_FILE="$HOME/.olympus_transcriber_state.json"
BACKUP_FILE="$HOME/.olympus_transcriber_state.json.backup"

echo "Resetting Malinche memory..."
echo ""

# Backup existing state
if [ -f "$STATE_FILE" ]; then
    echo "Backing up current state..."
    cp "$STATE_FILE" "$BACKUP_FILE"
    echo "Backup saved: $BACKUP_FILE"
    echo ""
fi

# Create new state with target date
echo "Setting last_sync to: ${TARGET_DATE}T00:00:00"
cat > "$STATE_FILE" << EOF
{
  "last_sync": "${TARGET_DATE}T00:00:00"
}
EOF

echo ""
echo "Memory reset complete!"
echo ""
echo "Current state:"
cat "$STATE_FILE"
echo ""
echo "Next recorder connection will process files after ${TARGET_DATE}"
echo ""


