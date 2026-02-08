#!/bin/bash
# Restart Malinche daemon

PLIST_PATH="$HOME/Library/LaunchAgents/com.user.olympus-transcriber.plist"

echo "🔄 Restarting Malinche daemon..."
echo ""

# Unload if loaded
if launchctl list | grep -q "olympus-transcriber"; then
    echo "⏹  Stopping daemon..."
    launchctl unload "$PLIST_PATH" 2>/dev/null || true
    sleep 1
fi

# Load daemon
echo "▶️  Starting daemon..."
launchctl load "$PLIST_PATH"
sleep 2

# Check status
if launchctl list | grep -q "olympus-transcriber"; then
    echo ""
    echo "✅ Daemon is running!"
    echo ""
    echo "Status:"
    launchctl list | grep olympus-transcriber
    echo ""
    echo "📋 Logs:"
    echo "  Application: ~/Library/Logs/olympus_transcriber.log"
    echo "  LaunchAgent: /tmp/olympus-transcriber-out.log"
    echo "  Errors:      /tmp/olympus-transcriber-err.log"
    echo ""
    echo "💡 Watch logs: tail -f ~/Library/Logs/olympus_transcriber.log"
else
    echo ""
    echo "❌ Failed to start daemon!"
    echo ""
    echo "Check errors:"
    tail -20 /tmp/olympus-transcriber-err.log
fi

