#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PORT="${1:-8555}"
export CSV_EDITOR_PORT="$PORT"

echo "Serving CSV editor at: http://localhost:${PORT}/"
if command -v python3 >/dev/null 2>&1; then
  python3 "$SCRIPT_DIR/../ProductMgmt/server.py"
else
  echo "python3 not found. Install it or update the script to point at your Python."
  exit 1
fi
