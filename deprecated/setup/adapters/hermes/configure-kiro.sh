#!/bin/bash
# Register Kiro CLI and Exa MCP in Hermes configuration.

set -euo pipefail

echo "=== 配置 Hermes Kiro/MCP 集成 ==="

# Exa MCP
hermes mcp add exa --url "https://mcp.exa.ai" --header "x-api-key:\${EXA_API_KEY}" 2>/dev/null && \
  echo "✅ Exa MCP 已注册到 Hermes" || \
  echo "⚠ 需手动配置 Exa MCP"
