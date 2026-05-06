#!/bin/bash
# Detect display environment on AWS EC2 Ubuntu.
# Outputs JSON with arch, display, chrome, and recommended mode.

set -euo pipefail

ARCH=$(dpkg --print-architecture 2>/dev/null || echo "unknown")

# Detect display
HAS_DISPLAY=false
DISPLAY_TYPE="none"

if pgrep -x dcvserver &>/dev/null || systemctl is-active --quiet dcvserver 2>/dev/null; then
  HAS_DISPLAY=true
  DISPLAY_TYPE="dcv"
elif [ -n "${DISPLAY:-}" ] || [ -n "${WAYLAND_DISPLAY:-}" ]; then
  HAS_DISPLAY=true
  if [ -n "${WAYLAND_DISPLAY:-}" ]; then
    DISPLAY_TYPE="wayland"
  else
    DISPLAY_TYPE="x11"
  fi
elif pgrep -x Xvnc &>/dev/null; then
  HAS_DISPLAY=true
  DISPLAY_TYPE="vnc"
fi

# Detect Chrome/Chromium
CHROME_INSTALLED=false
CHROME_BINARY=""
CHROME_VERSION=""

if command -v google-chrome-stable &>/dev/null; then
  CHROME_INSTALLED=true
  CHROME_BINARY="google-chrome-stable"
  CHROME_VERSION=$(google-chrome-stable --version 2>/dev/null | grep -oP '[\d.]+' | head -1)
elif command -v chromium-browser &>/dev/null; then
  CHROME_INSTALLED=true
  CHROME_BINARY="chromium-browser"
  CHROME_VERSION=$(chromium-browser --version 2>/dev/null | grep -oP '[\d.]+' | head -1)
fi

# Detect Node.js
NODE_INSTALLED=false
NODE_VERSION=""
if command -v node &>/dev/null; then
  NODE_INSTALLED=true
  NODE_VERSION=$(node --version 2>/dev/null)
fi

# Determine recommended mode
if [ "$HAS_DISPLAY" = "true" ]; then
  if [ "$ARCH" = "arm64" ] && [ "$CHROME_BINARY" = "chromium-browser" ] && snap list chromium 2>/dev/null | grep -q chromium; then
    RECOMMENDED_MODE="arm64-snap"
  else
    RECOMMENDED_MODE="headed"
  fi
else
  RECOMMENDED_MODE="headless"
fi

cat <<EOF
{
  "arch": "$ARCH",
  "has_display": $HAS_DISPLAY,
  "display_type": "$DISPLAY_TYPE",
  "chrome_installed": $CHROME_INSTALLED,
  "chrome_binary": "$CHROME_BINARY",
  "chrome_version": "$CHROME_VERSION",
  "node_installed": $NODE_INSTALLED,
  "node_version": "$NODE_VERSION",
  "recommended_mode": "$RECOMMENDED_MODE"
}
EOF
