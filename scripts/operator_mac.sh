#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LEGAL_SCRIPTS_DIR="$ROOT_DIR/Legal/scripts"
WEBSITE_ENV_FILE="$ROOT_DIR/simple-reporting-site/.env"
RUNLOG_DIR="$ROOT_DIR/.runlogs"

usage() {
  cat <<'EOF'
Usage: ./scripts/operator_mac.sh <command>

Commands:
  status         Show quick project health checks
  refresh-legal  Regenerate Legal CSVs, import into Postgres, build reporting views
  start          Start website launcher
  stop           Stop website launcher
  full-refresh   Run refresh-legal, then start website
EOF
}

load_env_if_present() {
  if [[ -f "$WEBSITE_ENV_FILE" ]]; then
    set -a
    # shellcheck disable=SC1090
    source "$WEBSITE_ENV_FILE"
    set +a
  fi
}

require_cmd() {
  local cmd="$1"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "Missing required command: $cmd"
    exit 1
  fi
}

status() {
  echo "Project root: $ROOT_DIR"
  echo ""
  echo "Tooling"
  if command -v node >/dev/null 2>&1; then
    echo "  node: $(node -v)"
  else
    echo "  node: missing"
  fi
  if command -v npm >/dev/null 2>&1; then
    echo "  npm:  $(npm -v)"
  else
    echo "  npm:  missing"
  fi
  if command -v python3 >/dev/null 2>&1; then
    echo "  python3: $(python3 --version 2>&1)"
  else
    echo "  python3: missing"
  fi
  echo ""
  echo "Runtime"
  if lsof -iTCP:8080 -sTCP:LISTEN -n -P >/dev/null 2>&1; then
    echo "  simple-reporting-site: listening on 8080"
  else
    echo "  simple-reporting-site: not listening on 8080"
  fi

  if [[ -f "$RUNLOG_DIR/website.log" ]]; then
    echo ""
    echo "Recent simple-reporting-site log lines:"
    tail -n 8 "$RUNLOG_DIR/website.log" || true
  else
    echo ""
    echo "No simple-reporting-site log found yet at $RUNLOG_DIR/website.log"
  fi
}

refresh_legal() {
  require_cmd python3
  load_env_if_present

  echo "Step 1/3: Generate Legal CSV dataset"
  python3 "$LEGAL_SCRIPTS_DIR/build_legal_reporting_dataset.py"

  echo "Step 2/3: Import Legal dataset into PostgreSQL"
  python3 "$LEGAL_SCRIPTS_DIR/importLegaldb.py"

  echo "Step 3/3: Build Legal reporting views"
  python3 "$LEGAL_SCRIPTS_DIR/build_legal_models.py"

  echo ""
  echo "Legal refresh complete."
}

start_site() {
  "$ROOT_DIR/run_project_mac.sh"
}

stop_site() {
  "$ROOT_DIR/stop_project_mac.sh"
}

full_refresh() {
  refresh_legal
  echo ""
  echo "Starting simple-reporting-site after refresh"
  start_site
}

main() {
  local cmd="${1:-}"
  case "$cmd" in
    status)
      status
      ;;
    refresh-legal)
      refresh_legal
      ;;
    start)
      start_site
      ;;
    stop)
      stop_site
      ;;
    full-refresh)
      full_refresh
      ;;
    *)
      usage
      exit 1
      ;;
  esac
}

main "$@"
