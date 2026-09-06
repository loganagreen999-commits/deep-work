#!/usr/bin/env bash
# Copies the extension to the Windows Desktop and opens Chrome's extensions page.
set -e
SRC="$(cd "$(dirname "$0")" && pwd)/youtube-blinders"
DEST="/mnt/c/Users/$(powershell.exe -NoProfile -Command '$env:USERNAME' | tr -d '\r')/Desktop/youtube-blinders"
rm -rf "$DEST"; cp -r "$SRC" "$DEST"
echo "Extension copied to your Desktop: youtube-blinders"
echo "Opening chrome://extensions — turn on Developer mode, click Load unpacked, pick that folder."
powershell.exe -NoProfile -Command 'Start-Process chrome "chrome://extensions"' 2>/dev/null || true
