---
name: setup-autofix
description: |
  [首次部署/恢复] 配置三层自愈机制：systemd OnFailure 被动修复 + 依赖健康检查 + HEARTBEAT 主动巡检。
  当 Agent Gateway 频繁崩溃或依赖服务异常时自动建议。
version: 1.0.0
platforms: [linux]
depends_on: [setup-base, setup-kiro]
target: aws-ec2
frequency: once
estimated_time: 10min
metadata:
  openclaw:
    emoji: "🔄"
    requires: { bins: ["systemctl", "bash", "kiro-cli"] }
  hermes:
    category: setup
    tags: [infrastructure, self-healing, monitoring]
---

# Setup AutoFix — 三层自愈机制

## When to Use

- 首次部署环境，启用自动修复能力
- Agent Gateway 连续崩溃（60 秒内 5 次）
- 依赖服务（LiteLLM、Chromium）频繁不可用
- 需要 7×24 无人值守运维

## Prerequisites

- Ubuntu 20.04/22.04/24.04 LTS
- systemd 可用
- setup-base 已执行
- setup-kiro 已执行（自愈分析使用 Kiro CLI）
- Agent（OpenClaw 或 Hermes）以 systemd 服务方式运行

## Procedure

### Phase 1: 环境检测

```bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AGENT=$(bash "$SCRIPT_DIR/shared/detect-agent.sh")
echo "当前 Agent: $AGENT"

# 检查 Agent 是否以 systemd 运行
if [ "$AGENT" = "openclaw" ]; then
  SERVICE_NAME="openclaw-gateway"
elif [ "$AGENT" = "hermes" ]; then
  SERVICE_NAME="hermes"
fi

systemctl --user is-active "$SERVICE_NAME" 2>/dev/null && \
  echo "✅ $SERVICE_NAME 以 systemd 服务运行" || \
  echo "⚠ $SERVICE_NAME 未检测到 systemd 服务（可能以前台模式运行）"

# Kiro CLI 状态
command -v kiro-cli &>/dev/null && echo "✅ Kiro CLI 可用" || echo "❌ Kiro CLI 未安装"
```

#### Checkpoint（首次暂停）

汇报 Agent 服务状态和 Kiro CLI 可用性。如果 Agent 不以 systemd 运行，建议先迁移到服务模式。

### Phase 2: 创建修复脚本

```bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AGENT=$(bash "$SCRIPT_DIR/shared/detect-agent.sh")
FIX_DIR="$HOME/.local/bin"
mkdir -p "$FIX_DIR"

# 通用修复脚本
cat > "$FIX_DIR/agent-fix.sh" << 'FIXSCRIPT'
#!/bin/bash
# Agent 自愈修复脚本（由 systemd OnFailure 触发）
set -euo pipefail

LOG_FILE="/tmp/agent-fix-$(date +%Y%m%d-%H%M%S).log"
exec > >(tee "$LOG_FILE") 2>&1

echo "=== Agent 自愈修复启动 $(date) ==="

# 收集错误日志
AGENT_SERVICE="${1:-openclaw-gateway}"
echo "--- 最近日志 ---"
journalctl --user -u "$AGENT_SERVICE" --since "5 min ago" --no-pager 2>/dev/null | tail -50

# 检查依赖服务
echo "--- 依赖服务检查 ---"
bash "$HOME/.local/bin/agent-deps-check.sh" 2>/dev/null || true

# 调用 Kiro CLI 分析
if command -v kiro-cli &>/dev/null; then
  echo "--- Kiro CLI 分析 ---"
  CONTEXT=$(journalctl --user -u "$AGENT_SERVICE" --since "5 min ago" --no-pager 2>/dev/null | tail -30)
  echo "$CONTEXT" | kiro-cli chat --message "分析以下服务崩溃日志，给出修复建议（简短）：" --max-turns 1 2>/dev/null || \
    echo "⚠ Kiro CLI 分析失败"
fi

echo "=== 修复脚本执行完成，日志: $LOG_FILE ==="
FIXSCRIPT
chmod +x "$FIX_DIR/agent-fix.sh"

echo "✅ 修复脚本已创建: $FIX_DIR/agent-fix.sh"
```

### Phase 3: 创建依赖健康检查脚本

```bash
FIX_DIR="$HOME/.local/bin"
AGENT=$(bash "$SCRIPT_DIR/shared/detect-agent.sh")

cat > "$FIX_DIR/agent-deps-check.sh" << 'DEPSSCRIPT'
#!/bin/bash
# 依赖服务健康检查

ERRORS=0

# Chrome CDP
if curl -s http://127.0.0.1:9222/json/version >/dev/null 2>&1 || \
   curl -s http://127.0.0.1:18800/json/version >/dev/null 2>&1; then
  echo "✅ Chrome CDP 正常"
else
  echo "❌ Chrome CDP 不可用"
  # 尝试重启
  systemctl --user restart chromium-headless 2>/dev/null || true
  ERRORS=$((ERRORS + 1))
fi

# LiteLLM (如果配置了)
if curl -s http://127.0.0.1:4000/health >/dev/null 2>&1; then
  echo "✅ LiteLLM Proxy 正常"
elif systemctl --user is-enabled litellm 2>/dev/null; then
  echo "❌ LiteLLM Proxy 不可用，尝试重启..."
  systemctl --user restart litellm 2>/dev/null || true
  ERRORS=$((ERRORS + 1))
fi

# Agent Gateway
AGENT_PORT=18789
if curl -s "http://127.0.0.1:$AGENT_PORT/healthz" >/dev/null 2>&1; then
  echo "✅ Agent Gateway 正常"
else
  echo "❌ Agent Gateway 不可用"
  ERRORS=$((ERRORS + 1))
fi

if [ $ERRORS -gt 0 ]; then
  echo "⚠ 发现 $ERRORS 个异常服务"
  exit 1
fi
echo "✅ 所有依赖服务正常"
DEPSSCRIPT
chmod +x "$FIX_DIR/agent-deps-check.sh"

echo "✅ 依赖检查脚本已创建: $FIX_DIR/agent-deps-check.sh"
```

### Phase 4: 配置 systemd OnFailure

```bash
AGENT=$(bash "$SCRIPT_DIR/shared/detect-agent.sh")

if [ "$AGENT" = "openclaw" ]; then
  SERVICE_NAME="openclaw-gateway"
elif [ "$AGENT" = "hermes" ]; then
  SERVICE_NAME="hermes"
fi

mkdir -p ~/.config/systemd/user/

# OnFailure 修复服务
cat > ~/.config/systemd/user/agent-autofix.service << EOF
[Unit]
Description=Agent AutoFix (triggered on gateway failure)

[Service]
Type=oneshot
ExecStart=$HOME/.local/bin/agent-fix.sh $SERVICE_NAME
EOF

# 为主服务添加 OnFailure 触发
OVERRIDE_DIR="$HOME/.config/systemd/user/${SERVICE_NAME}.service.d"
mkdir -p "$OVERRIDE_DIR"
cat > "$OVERRIDE_DIR/autofix.conf" << EOF
[Unit]
OnFailure=agent-autofix.service

[Service]
StartLimitBurst=5
StartLimitIntervalSec=60
EOF

systemctl --user daemon-reload
echo "✅ systemd OnFailure 已配置"
```

### Phase 5: 配置 HEARTBEAT 定时巡检

```bash
# 每 30 分钟执行健康检查
cat > ~/.config/systemd/user/agent-heartbeat.service << EOF
[Unit]
Description=Agent HEARTBEAT health check

[Service]
Type=oneshot
ExecStart=$HOME/.local/bin/agent-deps-check.sh
EOF

cat > ~/.config/systemd/user/agent-heartbeat.timer << EOF
[Unit]
Description=Run agent health check every 30 minutes

[Timer]
OnBootSec=5min
OnUnitActiveSec=30min

[Install]
WantedBy=timers.target
EOF

systemctl --user daemon-reload
systemctl --user enable --now agent-heartbeat.timer
echo "✅ HEARTBEAT 定时巡检已启动（每 30 分钟）"
```

#### Checkpoint

```bash
systemctl --user is-active agent-heartbeat.timer && echo "✅ Timer 运行中"
systemctl --user list-timers | grep heartbeat
```

## Verification

- [ ] `agent-fix.sh` 可执行且路径正确
- [ ] `agent-deps-check.sh` 可执行且手动运行无报错
- [ ] systemd OnFailure 已关联到 Agent 服务
- [ ] `agent-heartbeat.timer` 已启动（`systemctl --user is-active agent-heartbeat.timer`）
- [ ] 手动触发一次健康检查：`bash ~/.local/bin/agent-deps-check.sh`

## Pitfalls

| 问题 | 解决 |
|------|------|
| Agent 非 systemd 运行 | 先将 Agent 迁移为 systemd user service |
| user lingering 未启用 | `loginctl enable-linger $(whoami)` |
| OnFailure 未触发 | 确认 `StartLimitBurst` 和 `StartLimitIntervalSec` 设置正确 |
| Kiro CLI 修复分析失败 | 不影响健康检查，降级为只收集日志 |
| Timer 开机不自动启动 | `loginctl enable-linger` 确保 user session 持久化 |

## Fallback

自愈机制本身故障时：
1. 手动检查：`systemctl --user status agent-autofix`
2. 查看日志：`ls /tmp/agent-fix-*.log`
3. 手动执行修复：`bash ~/.local/bin/agent-fix.sh`
4. 如 systemd 层面异常：`systemctl --user daemon-reload && systemctl --user restart agent-heartbeat.timer`
