#!/bin/bash
# Cross-platform startup script for Linux and macOS

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

# Prefer Python launcher if available
if command -v python3 &>/dev/null; then
    exec python3 launch_chrome.py "$@"
elif command -v python &>/dev/null; then
    exec python launch_chrome.py "$@"
fi

# Fallback shell logic if Python is not installed
echo "[*] Closing existing Chrome debugging processes..."
pkill -f "remote-debugging-port=9222" 2>/dev/null || killall "Google Chrome" 2>/dev/null
sleep 1

PROFILE_DIR="$DIR/chrome_profile"
mkdir -p "$PROFILE_DIR"

TARGET_URL="https://learn.better.efekta.com/gap/ui/self-study"
ARGS="--remote-debugging-port=9222 --user-data-dir=$PROFILE_DIR --no-first-run --no-default-browser-check --autoplay-policy=no-user-gesture-required $TARGET_URL"

echo "[*] Launching browser with remote debugging on port 9222..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    open -a "Google Chrome" --args $ARGS
elif command -v google-chrome &>/dev/null; then
    google-chrome $ARGS &
elif command -v google-chrome-stable &>/dev/null; then
    google-chrome-stable $ARGS &
elif command -v chromium &>/dev/null; then
    chromium $ARGS &
elif command -v chromium-browser &>/dev/null; then
    chromium-browser $ARGS &
else
    echo "[!] Error: Neither Google Chrome nor Chromium could be found."
    exit 1
fi

echo ""
echo "[✓] Browser launched with debugging port 9222 enabled."
echo "[*] Ensure you are on the Efekta dashboard or lesson, then run: python bot.py"
