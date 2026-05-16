# Setup Skills — 基础设施一键部署

AWS EC2 环境的基础设施 Setup Skills，支持 OpenClaw 和 Hermes 双平台执行。

## 安装

### 方式 1：npx skills（推荐）

```bash
npx skills add your-org/enhancement4openclaw --path skills/setup
```

### 方式 2：手动复制

```bash
# OpenClaw
cp -r skills/setup/* ~/.openclaw/workspace/skills/

# Hermes
cp -r skills/setup/* ~/.hermes/skills/
```

## Skill 列表

| Skill | 用途 | 预估时间 | 依赖 |
|-------|------|----------|------|
| `setup-base` | 安全基座（防护规则 + skill-registry） | 5min | 无 |
| `setup-dcv` | Amazon DCV 远程桌面 | 15min | setup-base |
| `setup-chrome` | Chrome/Chromium + CDP 浏览器自动化 | 10min | setup-base |
| `setup-kiro` | Kiro CLI + ACP + Exa MCP | 10min | setup-base |
| `setup-autofix` | 三层自愈（OnFailure + 健康检查 + 巡检） | 10min | setup-base, setup-kiro |

## 推荐安装顺序

```
setup-base → setup-kiro → setup-chrome → setup-dcv (可选) → setup-autofix
```

`setup-dcv` 仅在需要 headed 模式浏览器时安装。

## 目录结构

```
skills/setup/
├── README.md                       # 本文件
├── shared/                         # 跨 Agent 共用脚本
│   ├── detect-agent.sh            # 检测当前 Agent（openclaw/hermes）
│   ├── detect-display-env.sh      # 检测显示环境
│   └── install-chrome.sh          # Chrome 安装（幂等）
├── adapters/                       # Agent 适配层
│   ├── openclaw/
│   │   ├── configure-browser.sh   # 写 openclaw.json browser 配置
│   │   └── configure-kiro.sh      # 写 openclaw.json MCP 配置
│   └── hermes/
│       ├── configure-browser.sh   # 配置 Hermes browser toolset
│       └── configure-kiro.sh      # 配置 Hermes MCP
├── setup-base/SKILL.md
├── setup-dcv/SKILL.md
├── setup-chrome/SKILL.md
├── setup-kiro/SKILL.md
└── setup-autofix/SKILL.md
```

## 设计原则

- **双平台兼容**：同一 SKILL.md 被 OpenClaw 或 Hermes 执行
- **Agent 自适应**：`detect-agent.sh` 运行时判断，Agent 特有逻辑在 `adapters/` 中
- **幂等**：所有操作先检测状态，重复执行安全
- **分阶段 + Checkpoint**：首次执行每阶段暂停确认，重跑全自动
- **失败不降级**：重试 2 次后停止，告知用户

## 兼容性

| Agent | 支持状态 |
|-------|---------|
| OpenClaw | ✅ 完整支持 |
| Hermes | ✅ 完整支持 |
| Claude Code | ⚠️ 可读取 SKILL.md 作为指令，但 adapters 需手动匹配 |
| Cursor / Copilot | ⚠️ 可读取通用部分，Agent 特有配置不适用 |
