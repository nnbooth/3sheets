#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SITE_DIR="$ROOT_DIR/simple-reporting-site"
LOG_DIR="$ROOT_DIR/.runlogs"
SITE_PORT="${PORT:-8080}"
SITE_PID_FILE="$LOG_DIR/website.pid"
SITE_LOG="$LOG_DIR/website.log"

mkdir -p "$LOG_DIR"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required but not found in PATH."
  exit 1
fi

if [ ! -f "$SITE_DIR/index.html" ]; then
  echo "simple-reporting-site not found at $SITE_DIR"
  exit 1
fi

if lsof -iTCP:"$SITE_PORT" -sTCP:LISTEN -n -P >/dev/null 2>&1; then
  echo "Port $SITE_PORT is already in use; skipping simple-reporting-site start."
else
  echo "Starting simple-reporting-site on http://127.0.0.1:$SITE_PORT ..."
  (
    cd "$SITE_DIR"
    nohup python3 -m http.server "$SITE_PORT" --bind 127.0.0.1 >"$SITE_LOG" 2>&1 &
    echo $! >"$SITE_PID_FILE"
  )
fi

sleep 2

if ! lsof -iTCP:"$SITE_PORT" -sTCP:LISTEN -n -P >/dev/null 2>&1; then
  echo ""
  echo "simple-reporting-site failed to start on port $SITE_PORT."
  echo "Recent log output:"
  if [ -f "$SITE_LOG" ]; then
    tail -n 40 "$SITE_LOG" || true
  else
    echo "  (no log file found at $SITE_LOG)"
  fi
  exit 1
fi

open "http://127.0.0.1:$SITE_PORT" >/dev/null 2>&1 || true

echo ""
echo "Started."
echo "simple-reporting-site:  http://127.0.0.1:$SITE_PORT"
echo "Logs:"
echo "  $SITE_LOG"
echo "Use ./stop_project_mac.sh to stop processes started by this script."
