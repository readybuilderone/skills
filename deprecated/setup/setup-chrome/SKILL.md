---
name: setup-chrome
description: |
  [首次部署/恢复] 安装 Chrome/Chromium 并配置 Agent 的浏览器自动化能力（CDP）。
  当浏览器操作失败且检测到 Chrome 未安装或 CDP 不可用时自动建议。
version: 1.0.0
platforms: [linux]
depends_on: [setup-base]
target: aws-ec2
frequency: once
estimated_time: 10min
metadata:
  openclaw:
    emoji: "🌐"
    requires: { bins: ["curl", "sudo", "python3"] }
  hermes:
    category: setup
    tags: [infrastructure, browser, cdp]
---

# Setup Chrome — 浏览器自动化环境

## When to Use

- 首次部署 AWS EC2 环境
- 浏览器操作失败，检测到 Chrome 未安装
- CDP 端口（9222/18800）无响应
- Agent browser 配置丢失或损坏

## Prerequisites

- Ubuntu 20.04/22.04/24.04 LTS (amd64 或 arm64)
- sudo 权限
- setup-base 已执行
- 如需 headed 模式：setup-dcv 已执行

## Procedure

### Phase 1: 环境检测

```bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AGENT=$(bash "$SCRIPT_DIR/shared/detect-agent.sh")
echo "当前 Agent: $AGENT"

ENV_JSON=$(bash "$SCRIPT_DIR/shared/detect-display-env.sh")
echo "$ENV_JSON" | python3 -m json.tool

CHROME_INSTALLED=$(echo "$ENV_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin)['chrome_installed'])")
RECOMMENDED_MODE=$(echo "$ENV_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin)['recommended_mode'])")

echo "Chrome 已安装: $CHROME_INSTALLED"
echo "推荐模式: $RECOMMENDED_MODE"
```

#### Checkpoint（首次暂停）

汇报：
1. Agent 环境（openclaw / hermes）
2. Chrome 是否已安装
3. 推荐运行模式（headed / headless / arm64-snap）

如果 Chrome 已安装且 CDP 端口正常，可直接跳到 Phase 4 验证。

### Phase 2: 安装 Chrome/Chromium

```bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
bash "$SCRIPT_DIR/shared/install-chrome.sh"
```

#### Checkpoint

```bash
google-chrome-stable --version 2>/dev/null || chromium-browser --version
```

期望输出版本号。失败则检查网络和 APT 源。

### Phase 3: 配置 Agent Browser

```bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AGENT=$(bash "$SCRIPT_DIR/shared/detect-agent.sh")
RECOMMENDED_MODE=$(bash "$SCRIPT_DIR/shared/detect-display-env.sh" | python3 -c "import sys,json; print(json.load(sys.stdin)['recommended_mode'])")

bash "$SCRIPT_DIR/adapters/${AGENT}/configure-browser.sh" --mode "$RECOMMENDED_MODE"
```

对于 ARM64 Snap Chromium (arm64-snap 模式)，额外创建 systemd 服务：

```bash
if [ "$RECOMMENDED_MODE" = "arm64-snap" ]; then
  mkdir -p ~/.config/systemd/user/
  cat > ~/.config/systemd/user/chromium-headless.service << 'EOF'
[Unit]
Description=Chromium Headless CDP
After=default.target

[Service]
ExecStart=/snap/bin/chromium --headless --no-sandbox --remote-debugging-port=18800 --remote-allow-origins=*
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
EOF
  systemctl --user daemon-reload
  systemctl --user enable --now chromium-headless
  echo "✅ ARM64 Snap Chromium systemd 服务已启动"
fi
```

#### Checkpoint

```bash
AGENT=$(bash "$SCRIPT_DIR/shared/detect-agent.sh")
if [ "$AGENT" = "openclaw" ]; then
  python3 -c "
import json, os
cfg = json.load(open(os.path.expanduser('~/.openclaw/openclaw.json')))
b = cfg.get('browser', {})
assert b.get('enabled', True), 'browser not enabled'
print('✅ OpenClaw browser 配置正常')
print('   headless:', b.get('headless'))
print('   profiles:', list(b.get('profiles', {}).keys()) or 'default')
"
elif [ "$AGENT" = "hermes" ]; then
  hermes config get browser 2>/dev/null && echo "✅ Hermes browser 配置正常"
fi
```

### Phase 4: 验证

#### 4.1 CDP 端口

```bash
curl -s http://127.0.0.1:9222/json/version 2>/dev/null | python3 -m json.tool && echo "✅ CDP 9222 正常" || \
curl -s http://127.0.0.1:18800/json/version 2>/dev/null | python3 -m json.tool && echo "✅ CDP 18800 正常" || \
echo "❌ CDP 端口均无响应"
```

#### 4.2 截图功能测试

通过当前 Agent 对话测试：
> "打开 https://www.google.com 并截图"

期望：返回截图图片。

## Verification

- [ ] Chrome/Chromium 已安装且可运行
- [ ] CDP 端口（9222 或 18800）响应正常
- [ ] Agent 的 browser 配置已正确写入
- [ ] 截图测试通过

## Pitfalls

| 问题 | 原因 | 解决 |
|------|------|------|
| CDP 端口在监听但连接被拒 | 缺少 `--remote-allow-origins=*` | 写入 chrome-flags 后重启浏览器 |
| Snap Chromium 启动失败 | AppArmor 限制 | 用 systemd 服务方式运行（Phase 3 已处理） |
| Gateway 重启后 browser 未生效 | enabled 变更需完整重启 | `openclaw gateway restart` |
| ARM64 无法安装 Chrome | 官方不支持 ARM64 | 自动切换到 Chromium |
| 截图空白 | GPU 渲染问题 | 在 browser.extraArgs 加 `--disable-gpu` |

## Fallback

重试 2 次后仍失败：
1. 收集诊断：`journalctl --user -u chromium-headless --since '5min ago'`
2. 检查配置：`cat ~/.openclaw/openclaw.json` 或 `hermes config get browser`
3. 停止并告知用户
4. 参考详细文档：`2. Chrome_DevTool/README.md`
