#!/usr/bin/env bash
# Deterministic reboot-notice script (no_agent mode)
# Runs every 2 minutes. Detects gateway reboot via timestamp gaps.
# On reboot detection, also checks Paperclip org health.
# Non-empty stdout = delivered to user as a notification.
#
# Install as a no_agent=true cron job with script=reboot-notice.sh
# and schedule=every 2m

HEARTBEAT_FILE="$HOME/.hermes/heartbeat.last"
NOTICE_FILE="$HOME/.hermes/reboot-notice-sent"
NOW=$(date +%s)

# First run ever — create files silently, no notification needed
if [ ! -f "$HEARTBEAT_FILE" ]; then
    echo "$NOW" > "$HEARTBEAT_FILE"
    echo "$NOW" > "$NOTICE_FILE"
    exit 0
fi

LAST=$(cat "$HEARTBEAT_FILE")
GAP=$(( NOW - LAST ))

# Update timestamp
echo "$NOW" > "$HEARTBEAT_FILE"

# If gap > 3 minutes, a reboot happened
if [ "$GAP" -gt 180 ]; then
    LAST_NOTICE=$(cat "$NOTICE_FILE" 2>/dev/null || echo "0")
    NOTICE_GAP=$(( NOW - LAST_NOTICE ))

    # Only send notice if we haven't sent one in the last 10 minutes
    if [ "$NOTICE_GAP" -gt 600 ]; then
        echo "$NOW" > "$NOTICE_FILE"

        echo "╔═══════════════════════════════════════════════╗"
        echo "║     Hermes Online — Post-Reboot Status        ║"
        echo "╚═══════════════════════════════════════════════╝"
        echo ""

        # Check Paperclip
        PAPERCLIP=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:3100/api/health 2>/dev/null)
        if [ "$PAPERCLIP" = "200" ]; then
            echo "✅ Paperclip Server — OK (port 3100)"
            AGENTS_JSON=$(curl -s http://127.0.0.1:3100/api/companies/811b098e-04c0-4567-96ee-cda484b8f951/agents 2>/dev/null)
            TOTAL=$(echo "$AGENTS_JSON" | python3 -c "import sys,json; data=json.load(sys.stdin); print(len(data))" 2>/dev/null)
            ERRORS=$(echo "$AGENTS_JSON" | python3 -c "import sys,json; data=json.load(sys.stdin); errs=[a for a in data if a.get('errorReason')]; print(len(errs))" 2>/dev/null)
            echo "   Agents: $TOTAL total, $ERRORS with errors"
        else
            echo "❌ Paperclip Server — DOWN (HTTP $PAPERCLIP)"
        fi

        echo ""
        FLY_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://{business-domain-1}/api/v1/health 2>/dev/null)
        if [ "$FLY_STATUS" = "200" ]; then
            echo "✅ Web App — OK ({business-domain-1})"
        else
            echo "❌ Web App — DOWN (HTTP $FLY_STATUS)"
        fi

        echo ""
        echo "---"
        echo "Reboot: $(date -d @${NOW} '+%Y-%m-%d %H:%M:%S ET')"
    fi
fi

exit 0
