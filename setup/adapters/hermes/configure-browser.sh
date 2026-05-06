#!/bin/bash
# Configure Hermes browser toolset.
# Usage: configure-browser.sh --mode <headed|headless|arm64-snap>

set -euo pipefail

MODE="${1#--mode=}"
[ "${1:-}" = "--mode" ] && MODE="${2:-headless}"

echo "=== 配置 Hermes Browser (mode=$MODE) ==="

case "$MODE" in
  headless)
    hermes config set browser.enabled true 2>/dev/null || true
    hermes config set browser.headless true 2>/dev/null || true
    hermes config set browser.cdp_url "http://127.0.0.1:9222" 2>/dev/null || true
    echo "✅ headless 配置已写入"
    ;;
  headed)
    hermes config set browser.enabled true 2>/dev/null || true
    hermes config set browser.headless false 2>/dev/null || true
    hermes config set browser.cdp_url "http://127.0.0.1:9222" 2>/dev/null || true
    echo "✅ headed 配置已写入"
    ;;
  arm64-snap)
    hermes config set browser.enabled true 2>/dev/null || true
    hermes config set browser.headless true 2>/dev/null || true
    hermes config set browser.cdp_url "http://127.0.0.1:18800" 2>/dev/null || true
    echo "✅ ARM64 Snap 配置已写入"
    ;;
  *)
    echo "❌ 未知模式: $MODE"
    exit 1
    ;;
esac

echo "✔ Hermes browser 配置完成"
