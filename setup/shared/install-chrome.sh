#!/bin/bash
# Install or upgrade Chrome/Chromium based on architecture.
# Idempotent: already-installed browsers are only upgraded.

set -euo pipefail

ARCH=$(dpkg --print-architecture)
echo "=== 架构: $ARCH ==="

if [ "$ARCH" = "arm64" ]; then
  if command -v chromium-browser &>/dev/null; then
    echo "Chromium 已安装，升级到最新版..."
    sudo apt-get update -qq
    sudo apt-get install -y --only-upgrade chromium-browser
  else
    echo "安装 Chromium (ARM64 不支持 Chrome)..."
    sudo apt-get update -qq
    sudo apt-get install -y chromium-browser
  fi
  echo "=== Chromium $(chromium-browser --version 2>/dev/null) ==="
else
  if command -v google-chrome-stable &>/dev/null; then
    echo "Chrome 已安装，升级到最新版..."
    sudo apt-get update -qq
    sudo apt-get install -y --only-upgrade google-chrome-stable
  else
    echo "安装 Google Chrome..."
    wget -q -O /tmp/google-chrome-stable.deb \
      "https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb"
    sudo apt-get install -y /tmp/google-chrome-stable.deb
    rm -f /tmp/google-chrome-stable.deb
  fi
  echo "=== Chrome $(google-chrome-stable --version 2>/dev/null) ==="
fi

echo "✔ 浏览器安装/升级完成"
