#!/usr/bin/env bash
# Gateway Reboot Detection (no_agent mode)
# Detects Hermes gateway restart via cron ticker heartbeat timestamp gaps.
# Silent when no reboot detected. Non-empty stdout = notification delivered.
# Install as a no_agent=true cron job with schedule=every 2m.
# Dedup: only sends one notification per 10 minutes (crash-loop guard).

set -u

HEARTBEAT_FILE="${HERMES_HOME:-$HOME/.hermes}/cron/ticker_heartbeat"
NOTICE_FILE="${HERMES_HOME:-$HOME/.hermes}/gateway-reboot-notice-sent"
NOW=$(date +%s)

# First run ever — create files silently
if [ ! -f "$HEARTBEAT_FILE" ]; then
    echo "$NOW" > "$HEARTBEAT_FILE"
    echo "$NOW" > "$NOTICE_FILE"
    exit 0
fi

# Parse heartbeat timestamp (may contain fractional seconds)
LAST=$(cat "$HEARTBEAT_FILE" 2>/dev/null | cut -d. -f1 || echo "0")
GAP=$(( NOW - LAST ))
echo "$NOW" > "$HEARTBEAT_FILE"

# If gap > 3 minutes, a reboot happened
if [ "$GAP" -gt 180 ]; then
    LAST_NOTICE=$(cat "$NOTICE_FILE" 2>/dev/null || echo "0")
    NOTICE_GAP=$(( NOW - LAST_NOTICE ))

    if [ "$NOTICE_GAP" -gt 600 ]; then
        echo "$NOW" > "$NOTICE_FILE"

        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "  Hermes Online — Post-Reboot Status"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        echo "🕐 Start: $(date -d "@${NOW}" '+%Y-%m-%d %H:%M:%S ET')"

        # Paperclip
        if curl -sf -o /dev/null http://127.0.0.1:3100/api/health 2>/dev/null; then
            echo "✅ Paperclip Server — OK (port 3100)"
            AGENTS=$(curl -s http://127.0.0.1:3100/api/companies/811b098e-04c0-4567-96ee-cda484b8f951/agents 2>/dev/null)
            if [ -n "$AGENTS" ]; then
                TOTAL=$(echo "$AGENTS" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d))" 2>/dev/null || echo "?")
                ERRORS=$(echo "$AGENTS" | python3 -c "import sys,json; d=json.load(sys.stdin); print(sum(1 for a in d if a.get('errorReason')))" 2>/dev/null || echo "?")
                echo "   Agents: $TOTAL total, $ERRORS with errors"
            fi
        else
            echo "❌ Paperclip Server — DOWN"
        fi

        # Web App
        if curl -sf -o /dev/null https://{business-domain-1}/api/v1/health 2>/dev/null; then
            echo "🌐 Web App: OK ({business-domain-1})"
        else
            echo "🌐 Web App: DOWN"
        fi
        echo ""
        echo "Checking on any issues now."
    fi
fi
exit 0
