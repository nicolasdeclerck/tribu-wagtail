#!/usr/bin/env bash
# Download the Tailwind CSS v3 standalone CLI (no Node required).
set -euo pipefail

VERSION="v3.4.17"
DEST="tools/tailwindcss"

case "$(uname -s)-$(uname -m)" in
    Darwin-arm64)  ASSET="tailwindcss-macos-arm64" ;;
    Darwin-x86_64) ASSET="tailwindcss-macos-x64" ;;
    Linux-x86_64)  ASSET="tailwindcss-linux-x64" ;;
    Linux-aarch64) ASSET="tailwindcss-linux-arm64" ;;
    *) echo "Unsupported platform: $(uname -s)-$(uname -m)"; exit 1 ;;
esac

mkdir -p tools
echo "Downloading Tailwind ${VERSION} (${ASSET})…"
curl -sL -o "${DEST}" \
    "https://github.com/tailwindlabs/tailwindcss/releases/download/${VERSION}/${ASSET}"
chmod +x "${DEST}"
echo "Done -> ${DEST}"
