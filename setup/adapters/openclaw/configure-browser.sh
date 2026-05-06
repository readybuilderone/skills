#!/bin/bash
# Configure OpenClaw browser settings in openclaw.json.
# Usage: configure-browser.sh --mode <headed|headless|arm64-snap>

set -euo pipefail

MODE="${1#--mode=}"
[ "${1:-}" = "--mode" ] && MODE="${2:-headless}"
CONFIG="$HOME/.openclaw/openclaw.json"

echo "=== 配置 OpenClaw Browser (mode=$MODE) ==="

# Backup
cp "$CONFIG" "${CONFIG}.bak.$(date +%s)" 2>/dev/null || true

case "$MODE" in
  headless)
    python3 -c "
import json, os
path = os.path.expanduser('$CONFIG')
try:
    cfg = json.load(open(path))
except:
    cfg = {}
cfg['browser'] = {
    'enabled': True,
    'headless': True,
    'noSandbox': True,
    'evaluateEnabled': True
}
cfg.pop('mcpServers', None)
json.dump(cfg, open(path, 'w'), indent=2, ensure_ascii=False)
print('✅ headless 配置已写入')
"
    ;;
  headed)
    python3 -c "
import json, os
path = os.path.expanduser('$CONFIG')
try:
    cfg = json.load(open(path))
except:
    cfg = {}
cfg['browser'] = {
    'enabled': True,
    'headless': False,
    'noSandbox': False,
    'evaluateEnabled': True,
    'defaultProfile': 'openclaw',
    'profiles': {
        'user': {
            'cdpUrl': 'http://127.0.0.1:9222',
            'driver': 'existing-session',
            'attachOnly': True,
            'color': '#00AA00'
        },
        'openclaw': {
            'color': '#FF4500'
        }
    }
}
cfg.pop('mcpServers', None)
json.dump(cfg, open(path, 'w'), indent=2, ensure_ascii=False)
print('✅ headed 双 Profile 配置已写入')
"
    ;;
  arm64-snap)
    python3 -c "
import json, os
path = os.path.expanduser('$CONFIG')
try:
    cfg = json.load(open(path))
except:
    cfg = {}
cfg['browser'] = {
    'enabled': True,
    'headless': True,
    'attachOnly': True,
    'evaluateEnabled': True,
    'defaultProfile': 'user',
    'profiles': {
        'user': {
            'cdpUrl': 'http://127.0.0.1:18800',
            'driver': 'existing-session',
            'attachOnly': True,
            'color': '#FF4500'
        }
    }
}
cfg.pop('mcpServers', None)
json.dump(cfg, open(path, 'w'), indent=2, ensure_ascii=False)
print('✅ ARM64 Snap attachOnly 配置已写入')
"
    ;;
  *)
    echo "❌ 未知模式: $MODE"
    exit 1
    ;;
esac

# Restart gateway
echo "重启 Gateway..."
openclaw gateway restart 2>/dev/null || echo "⚠ Gateway 重启失败，可能需要手动重启"
