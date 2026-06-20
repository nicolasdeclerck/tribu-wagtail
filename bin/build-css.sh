#!/usr/bin/env bash
# Build (and optionally watch) the Tailwind stylesheet.
#   ./bin/build-css.sh          # one-off minified build
#   ./bin/build-css.sh --watch  # rebuild on change (dev)
set -euo pipefail

CLI="tools/tailwindcss"
[ -x "$CLI" ] || { echo "Tailwind CLI missing — run ./bin/get-tailwind.sh first."; exit 1; }

IN="theme/static_src/input.css"
OUT="core/static/css/app.css"

if [ "${1:-}" = "--watch" ]; then
    exec "$CLI" -c tailwind.config.js -i "$IN" -o "$OUT" --watch
else
    "$CLI" -c tailwind.config.js -i "$IN" -o "$OUT" --minify
fi
