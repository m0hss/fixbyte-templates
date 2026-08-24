#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-8765}"
HOST="${HOST:-127.0.0.1}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$ROOT"

echo "Fixbyte designs — preview locale"
echo "  http://${HOST}:${PORT}/"
echo "  http://${HOST}:${PORT}/restaurant.html"
echo "  http://${HOST}:${PORT}/barbiers.html"
echo "  http://${HOST}:${PORT}/instituts.html"
echo "  http://${HOST}:${PORT}/cafes.html"
echo "Ctrl+C pour arrêter."
echo

exec python3 -m http.server "$PORT" --bind "$HOST"
