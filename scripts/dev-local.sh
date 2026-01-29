#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_DIR="$ROOT_DIR/.pids"
LOG_DIR="$ROOT_DIR/.logs"

BACKEND_PID="$PID_DIR/backend.pid"
FRONTEND_PID="$PID_DIR/frontend.pid"

mkdir -p "$PID_DIR" "$LOG_DIR"

is_running() {
  local pid_file="$1"
  if [[ -f "$pid_file" ]]; then
    local pid
    pid="$(cat "$pid_file")"
    if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
      return 0
    fi
  fi
  return 1
}

http_ok() {
  local url="$1"
  if ! command -v curl >/dev/null 2>&1; then
    return 1
  fi
  local code
  code="$(curl -s -o /dev/null -w "%{http_code}" "$url" || true)"
  [[ "$code" =~ ^2|3 ]]
}

frontend_port_from_log() {
  if [[ ! -f "$LOG_DIR/frontend.log" ]]; then
    return 1
  fi
  local match
  match="$(grep -Eo 'http://localhost:[0-9]+' "$LOG_DIR/frontend.log" | tail -n 1 || true)"
  if [[ -n "$match" ]]; then
    echo "${match##http://localhost:}"
    return 0
  fi
  return 1
}

start_backend() {
  if is_running "$BACKEND_PID"; then
    echo "Backend already running (pid $(cat "$BACKEND_PID"))"
    return
  fi
  local python_bin="python3"
  if [[ -x "$ROOT_DIR/.venv/bin/python" ]]; then
    python_bin="$ROOT_DIR/.venv/bin/python"
  fi
  if ! command -v "$python_bin" >/dev/null 2>&1; then
    echo "python3 not found." >&2
    exit 1
  fi
  echo "Starting backend..."
  (cd "$ROOT_DIR" && PYTHONUNBUFFERED=1 nohup "$python_bin" App/server.py > "$LOG_DIR/backend.log" 2>&1 & echo $! > "$BACKEND_PID")
}

start_frontend() {
  if is_running "$FRONTEND_PID"; then
    echo "Frontend already running (pid $(cat "$FRONTEND_PID"))"
    return
  fi
  if ! command -v npm >/dev/null 2>&1; then
    echo "npm not found." >&2
    exit 1
  fi
  echo "Starting frontend..."
  (cd "$ROOT_DIR/App/ui" && nohup npm run dev > "$LOG_DIR/frontend.log" 2>&1 & echo $! > "$FRONTEND_PID")
}

stop_backend() {
  if is_running "$BACKEND_PID"; then
    local pid
    pid="$(cat "$BACKEND_PID")"
    echo "Stopping backend (pid $pid)..."
    kill "$pid" 2>/dev/null || true
    rm -f "$BACKEND_PID"
  else
    echo "Backend not running."
  fi
}

stop_frontend() {
  if is_running "$FRONTEND_PID"; then
    local pid
    pid="$(cat "$FRONTEND_PID")"
    echo "Stopping frontend (pid $pid)..."
    kill "$pid" 2>/dev/null || true
    rm -f "$FRONTEND_PID"
  else
    echo "Frontend not running."
  fi
}

status() {
  local backend_running=false
  local frontend_running=false
  local frontend_port=""
  if is_running "$BACKEND_PID"; then
    backend_running=true
  elif http_ok "http://localhost:8555/api/session"; then
    backend_running=true
  fi
  if is_running "$FRONTEND_PID"; then
    frontend_running=true
  else
    if frontend_port="$(frontend_port_from_log)"; then
      if http_ok "http://localhost:${frontend_port}/"; then
        frontend_running=true
      fi
    elif http_ok "http://localhost:5173/"; then
      frontend_running=true
      frontend_port="5173"
    fi
  fi
  if [[ "$backend_running" == "true" ]]; then
    echo "Backend: running"
  else
    echo "Backend: stopped"
  fi
  if [[ "$frontend_running" == "true" ]]; then
    if [[ -n "$frontend_port" ]]; then
      echo "Frontend: running (port ${frontend_port})"
    else
      echo "Frontend: running"
    fi
  else
    echo "Frontend: stopped"
  fi
}

case "${1:-}" in
  start)
    start_backend
    start_frontend
    ;;
  stop)
    stop_frontend
    stop_backend
    ;;
  restart)
    stop_frontend
    stop_backend
    start_backend
    start_frontend
    ;;
  status)
    status
    ;;
  *)
    echo "Usage: $(basename "$0") {start|stop|restart|status}"
    exit 1
    ;;
esac
