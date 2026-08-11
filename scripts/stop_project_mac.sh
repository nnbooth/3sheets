#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$ROOT_DIR/.runlogs"
SITE_PID_FILE="$LOG_DIR/website.pid"
SITE_PORT="${PORT:-8080}"

stop_from_pid_file() {
  local label="$1"
  local pid_file="$2"

  if [ ! -f "$pid_file" ]; then
    return 0
  fi

  local pid
  pid="$(cat "$pid_file")"

  if [ -z "$pid" ]; then
    echo "$label: pid file is empty."
    rm -f "$pid_file"
    return 0
  fi

  if kill -0 "$pid" >/dev/null 2>&1; then
    kill "$pid" >/dev/null 2>&1 || true
    echo "$label: stopped pid $pid"
  else
    echo "$label: process $pid is not running"
  fi

  rm -f "$pid_file"
}

stop_listener_on_port() {
  local label="$1"
  local port="$2"

  local pids
  pids="$(lsof -tiTCP:"$port" -sTCP:LISTEN -n -P 2>/dev/null || true)"

  if [ -z "$pids" ]; then
    echo "$label: no active process found on port $port."
    return 0
  fi

  for pid in $pids; do
    if kill -0 "$pid" >/dev/null 2>&1; then
      kill "$pid" >/dev/null 2>&1 || true
      echo "$label: stopped listener pid $pid"
    fi
  done

  return 0
}

stop_from_pid_file "Simple reporting site" "$SITE_PID_FILE"

if [ -f "$SITE_PID_FILE" ]; then
  echo "Simple reporting site: pid file still present after stop attempt; removed."
  rm -f "$SITE_PID_FILE"
else
  stop_listener_on_port "Simple reporting site" "$SITE_PORT"
fi
