#!/bin/bash
# Register Kiro CLI and Exa MCP in OpenClaw configuration.

set -euo pipefail

CONFIG="$HOME/.openclaw/openclaw.json"

echo "=== 配置 OpenClaw Kiro/MCP 集成 ==="

cp "$CONFIG" "${CONFIG}.bak.$(date +%s)" 2>/dev/null || true

python3 -c "
import json, os

path = os.path.expanduser('$CONFIG')
try:
    cfg = json.load(open(path))
except:
    cfg = {}

if 'mcpServers' not in cfg:
    cfg['mcpServers'] = {}

# Exa Search MCP
cfg['mcpServers']['exa'] = {
    'type': 'remote',
    'url': 'https://mcp.exa.ai',
    'headers': {
        'x-api-key': '\${EXA_API_KEY}'
    }
}

json.dump(cfg, open(path, 'w'), indent=2, ensure_ascii=False)
print('✅ Exa MCP 已注册到 openclaw.json')
"

openclaw gateway restart 2>/dev/null || echo "⚠ Gateway 重启失败"
