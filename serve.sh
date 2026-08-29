#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-8765}"
HOST="${HOST:-127.0.0.1}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$ROOT"

# The multilingual site is generated; serve the build output so the locale
# folders, hreflang tags and per-locale partials behave exactly as deployed.
rm -rf _site
python3 scripts/build-i18n.py _site

echo
echo "Fixbyte designs — preview locale"
echo "  http://${HOST}:${PORT}/                    (fr)"
echo "  http://${HOST}:${PORT}/restaurant.html"
echo "  http://${HOST}:${PORT}/nl/                 (nl)"
echo "  http://${HOST}:${PORT}/en/restaurant.html  (en)"
echo "  http://${HOST}:${PORT}/ar/                 (rtl)"
echo "Ctrl+C pour arrêter."
echo

exec python3 -m http.server "$PORT" --bind "$HOST" --directory _site
