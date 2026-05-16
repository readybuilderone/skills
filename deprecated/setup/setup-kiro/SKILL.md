---
name: setup-kiro
description: |
  [首次部署/恢复] 安装 Kiro CLI 并配置 ACP 协议集成和 MCP 扩展（Exa Search + AWS Docs）。
  当编码任务需要降本路由或 Exa 搜索不可用时自动建议。
version: 1.0.0
platforms: [linux]
depends_on: [setup-base]
target: aws-ec2
frequency: once
estimated_time: 10min
metadata:
  openclaw:
    emoji: "⚡"
    requires: { bins: ["curl", "node"] }
  hermes:
    category: setup
    tags: [infrastructure, acp, mcp, cost-optimization]
---

# Setup Kiro — ACP 降本引擎 + MCP 扩展

## When to Use

- 首次部署环境，需要 Kiro CLI 作为编码执行层
- Exa 搜索功能不可用（F1 采集依赖）
- 需要降低 Claude API Token 消耗
- `kiro-cli --version` 报错或未安装

## Prerequisites

- Ubuntu 20.04/22.04/24.04 LTS
- Node.js ≥ v20（`node --version`）
- setup-base 已执行
- Kiro 账号（免费 License 即可）

## Procedure

### Phase 1: 环境检测

```bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AGENT=$(bash "$SCRIPT_DIR/shared/detect-agent.sh")
echo "当前 Agent: $AGENT"

# Node.js
node --version 2>/dev/null || echo "❌ Node.js 未安装"

# Kiro CLI
if command -v kiro-cli &>/dev/null; then
  echo "✅ Kiro CLI 已安装: $(kiro-cli --version 2>/dev/null)"
  # 验证登录状态
  echo "ok" | kiro-cli chat --message "hello" --max-turns 1 2>/dev/null && \
    echo "✅ Kiro CLI 已登录" || echo "⚠ Kiro CLI 未登录或 session 过期"
else
  echo "❌ Kiro CLI 未安装"
fi
```

#### Checkpoint（首次暂停）

汇报 Node.js 版本、Kiro CLI 安装状态、登录状态。确认是否继续。

### Phase 2: 安装 Kiro CLI

如果 Node.js 版本不足：

```bash
if ! node --version 2>/dev/null | grep -qP 'v2[0-9]|v[3-9]'; then
  echo "安装 Node.js LTS..."
  curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash
  export NVM_DIR="$HOME/.nvm"
  [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
  nvm install --lts
  nvm use --lts
fi
```

安装 Kiro CLI：

```bash
if ! command -v kiro-cli &>/dev/null; then
  npm install -g @anthropic-ai/kiro-cli
  echo "✅ Kiro CLI 安装完成: $(kiro-cli --version)"
else
  echo "⏭ Kiro CLI 已安装"
fi
```

### Phase 3: 登录 Kiro CLI

```bash
# Device Flow 登录（需要用户在浏览器中确认）
kiro-cli login --license free --use-device-flow
```

向用户说明：
1. 终端会输出一个 URL 和验证码
2. 在浏览器中打开该 URL
3. 输入验证码完成登录
4. 验证码有效期约 10 分钟

#### Checkpoint

```bash
echo "ok" | kiro-cli chat --message "hello" --max-turns 1 2>/dev/null && \
  echo "✅ 登录成功" || echo "❌ 登录失败"
```

### Phase 4: 配置 MCP 扩展

```bash
# Kiro CLI 设置默认模型
mkdir -p ~/.kiro/settings
cat > ~/.kiro/settings/settings.json << 'EOF'
{
  "ai.chat.defaultModel": "claude-sonnet-4-6-20250514"
}
EOF

# Exa MCP（高级搜索，F1 采集依赖）
# 需要 Exa API Key，提示用户配置
if [ -z "${EXA_API_KEY:-}" ]; then
  echo "⚠ 需要配置 EXA_API_KEY 环境变量"
  echo "  获取: https://exa.ai → Settings → API Keys"
  echo "  设置: export EXA_API_KEY=your-key-here"
fi
```

### Phase 5: 配置 Agent ACP/MCP 集成

```bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AGENT=$(bash "$SCRIPT_DIR/shared/detect-agent.sh")

if [ "$AGENT" = "openclaw" ]; then
  # 将 Kiro CLI 注册为 ACP peer
  python3 -c "
import json, os
path = os.path.expanduser('~/.openclaw/openclaw.json')
try:
    cfg = json.load(open(path))
except:
    cfg = {}

# 注册 Exa MCP
if 'mcpServers' not in cfg:
    cfg['mcpServers'] = {}

cfg['mcpServers']['exa'] = {
    'type': 'remote',
    'url': 'https://mcp.exa.ai',
    'headers': {
        'x-api-key': '\${EXA_API_KEY}'
    }
}

json.dump(cfg, open(path, 'w'), indent=2, ensure_ascii=False)
print('✅ OpenClaw MCP 配置已写入')
"
  openclaw gateway restart 2>/dev/null || echo "⚠ Gateway 重启失败"

elif [ "$AGENT" = "hermes" ]; then
  # Hermes MCP 配置
  hermes mcp add exa --url "https://mcp.exa.ai" --header "x-api-key:\${EXA_API_KEY}" 2>/dev/null || \
    echo "⚠ Hermes MCP 配置需手动添加"
fi
```

## Verification

- [ ] `kiro-cli --version` 输出版本号
- [ ] Kiro CLI 登录状态正常（chat 命令可执行）
- [ ] Agent 的 MCP 配置包含 Exa
- [ ] `EXA_API_KEY` 环境变量已设置（F1 采集需要）

## Pitfalls

| 问题 | 解决 |
|------|------|
| Device Flow 验证码过期 | 重新执行 `kiro-cli login` |
| npm install 权限问题 | 使用 nvm 管理 Node.js，不用 sudo |
| Kiro CLI 版本不兼容 | `npm update -g @anthropic-ai/kiro-cli` |
| Exa API Key 无效 | 在 exa.ai 控制台重新生成 |
| MCP 连接超时 | 检查网络，确认 VPC 可访问外网 |

## Fallback

登录失败时：
1. 确认网络可达 `curl -s https://api.kiro.dev`
2. 清除缓存 `rm -rf ~/.kiro/auth`
3. 重试登录
4. 如仍失败，可暂时跳过（其他模块可降级运行，仅失去降本能力）
