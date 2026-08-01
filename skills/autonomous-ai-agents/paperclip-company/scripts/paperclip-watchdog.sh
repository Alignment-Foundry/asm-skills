#!/usr/bin/env bash
# Paperclip Watchdog — deterministic health check + auto-restart
# no_agent=true: script-only cron job, stdout = notification payload
# Silent when Paperclip is healthy; only outputs when action is taken.

set -euo pipefail

PAPERCLIP_URL="http://127.0.0.1:3100"
PAPERCLIP_DATA_DIR="$HOME/.paperclip/instances/default"
LOG_FILE="$PAPERCLIP_DATA_DIR/logs/server.log"
TIMESTAMP="$(date '+%Y-%m-%d %H:%M:%S')"

# 1) Check if the HTTP server is responding
if curl -sf -o /dev/null "$PAPERCLIP_URL/" 2>/dev/null; then
  # Paperclip is up — stay silent (watchdog pattern)
  exit 0
fi

# 2) Server is down — check if the process is orphaned
PID="$(pgrep -f 'node.*@paperclipai/server' 2>/dev/null || true)"
if [ -n "$PID" ]; then
  echo "[$TIMESTAMP] Paperclip HTTP down ($PAPERCLIP_URL) but process PID=$PID still exists — killing stale process"
  kill "$PID" 2>/dev/null || true
  sleep 2
fi

# 3) Start Paperclip via npx
echo "[$TIMESTAMP] Paperclip is DOWN — starting server..."
npx --yes paperclipai run --no-repair &
NPX_PID=$!

# Wait for server to be ready (up to 30s)
for i in $(seq 1 30); do
  if curl -sf -o /dev/null "$PAPERCLIP_URL/" 2>/dev/null; then
    echo "[$TIMESTAMP] Paperclip started successfully (PID=$NPX_PID, took ${i}s)"
    exit 0
  fi
  sleep 1
done

# Timed out
echo "[$TIMESTAMP] ERROR: Paperclip failed to start within 30s (npx PID=$NPX_PID)"
exit 1