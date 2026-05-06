---
name: setup-base
description: |
  [首次部署/恢复] 安装安全基座：配置防护规则、skill-vetter 审查框架、skill-registry。
  当其他 setup Skill 检测到 setup-base 未完成时自动建议执行。
version: 1.0.0
platforms: [linux]
depends_on: []
target: aws-ec2
frequency: once
estimated_time: 5min
metadata:
  openclaw:
    emoji: "🛡️"
    requires: { bins: ["python3", "git"] }
  hermes:
    category: setup
    tags: [infrastructure, security, foundation]
---

# Setup Base — 安全基座

## When to Use

- 首次部署 AWS EC2 环境（所有其他 setup Skill 的前置）
- Agent 配置文件被意外修改或损坏
- 需要重新初始化安全防护规则

## Prerequisites

- Ubuntu 20.04/22.04/24.04 LTS
- sudo 权限
- Agent（OpenClaw 或 Hermes）已安装并可运行

## Procedure

### Phase 1: 检测当前状态

```bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AGENT=$(bash "$SCRIPT_DIR/shared/detect-agent.sh")
echo "当前 Agent: $AGENT"

# 检查 setup-base 是否已执行
if [ -f "$SCRIPT_DIR/shared/.base-installed" ]; then
  echo "✅ setup-base 已完成，进入验证模式"
fi
```

#### Checkpoint（首次暂停）

汇报当前 Agent 环境，确认是否继续。

### Phase 2: 部署共用脚本

确保 `shared/` 目录下所有脚本可执行且就位：

```bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
chmod +x "$SCRIPT_DIR/shared/"*.sh
chmod +x "$SCRIPT_DIR/adapters/openclaw/"*.sh 2>/dev/null || true
chmod +x "$SCRIPT_DIR/adapters/hermes/"*.sh 2>/dev/null || true
echo "✅ 脚本权限设置完成"
```

### Phase 3: 配置安全防护规则

```bash
AGENT=$(bash "$SCRIPT_DIR/shared/detect-agent.sh")

if [ "$AGENT" = "openclaw" ]; then
  # 写入 MEMORY.md 硬规则
  MEMORY_DIR="$HOME/.openclaw/workspace"
  mkdir -p "$MEMORY_DIR"
  if ! grep -q "配置修改安全协议" "$MEMORY_DIR/MEMORY.md" 2>/dev/null; then
    cat >> "$MEMORY_DIR/MEMORY.md" << 'RULES'

## 配置修改安全协议

修改 openclaw.json 前必须：
1. 查阅官方文档确认字段含义
2. 备份当前配置 (`cp openclaw.json openclaw.json.bak.$(date +%s)`)
3. 修改后验证 JSON 格式合法 (`python3 -m json.tool openclaw.json`)
4. 告知用户所做的修改
RULES
    echo "✅ OpenClaw 安全规则已写入 MEMORY.md"
  else
    echo "⏭ 安全规则已存在，跳过"
  fi

elif [ "$AGENT" = "hermes" ]; then
  # 写入 AGENTS.md
  AGENTS_FILE="$HOME/.hermes/AGENTS.md"
  mkdir -p "$(dirname "$AGENTS_FILE")"
  if ! grep -q "配置修改安全协议" "$AGENTS_FILE" 2>/dev/null; then
    cat >> "$AGENTS_FILE" << 'RULES'

## 配置修改安全协议

修改配置文件前必须：
1. 查阅文档确认字段含义
2. 备份当前配置
3. 修改后验证格式合法
4. 告知用户所做的修改
RULES
    echo "✅ Hermes 安全规则已写入 AGENTS.md"
  else
    echo "⏭ 安全规则已存在，跳过"
  fi
fi
```

### Phase 4: 初始化 skill-registry

```bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REGISTRY="$SCRIPT_DIR/shared/skill-registry.json"

if [ ! -f "$REGISTRY" ]; then
  cat > "$REGISTRY" << 'EOF'
{
  "version": "1.0.0",
  "skills": {},
  "last_check": null
}
EOF
  echo "✅ skill-registry.json 已创建"
else
  echo "⏭ skill-registry.json 已存在"
fi

# 标记完成
touch "$SCRIPT_DIR/shared/.base-installed"
```

## Verification

- [ ] `detect-agent.sh` 输出 "openclaw" 或 "hermes"
- [ ] 安全规则已写入对应的配置文件（MEMORY.md 或 AGENTS.md）
- [ ] `skill-registry.json` 存在且 JSON 合法
- [ ] `shared/` 下所有脚本有执行权限

## Pitfalls

| 问题 | 解决 |
|------|------|
| Agent 未安装 | 先安装 OpenClaw 或 Hermes |
| MEMORY.md 不存在 | 脚本会自动创建 |
| 权限不足 | 确认当前用户是 Agent 的运行用户 |
