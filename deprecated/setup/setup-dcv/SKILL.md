---
name: setup-dcv
description: |
  [首次部署/恢复] 安装 Amazon DCV Server 远程桌面，通过 SSM 安全访问。
  当需要 headed 模式浏览器但无图形环境时自动建议。
version: 1.0.0
platforms: [linux]
depends_on: [setup-base]
target: aws-ec2
frequency: once
estimated_time: 15min
metadata:
  openclaw:
    emoji: "🖥️"
    requires: { bins: ["sudo", "curl", "systemctl"] }
  hermes:
    category: setup
    tags: [infrastructure, desktop, dcv]
---

# Setup DCV — 远程桌面

## When to Use

- 首次部署 AWS EC2 环境，需要图形桌面
- 模块 2 (Chrome) 需要 headed 模式但无显示环境
- 模块 F7 (视频号发布) 或 F3 (发票下载) 需要可视化操作
- `detect-display-env.sh` 输出 `has_display: false`

## Prerequisites

- AWS EC2 实例（t3.medium 或更大）
- Ubuntu 20.04/22.04/24.04 LTS
- sudo 权限
- setup-base 已执行

## Procedure

### Phase 1: 环境检测

```bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# 检查是否已安装
if systemctl is-active --quiet dcvserver 2>/dev/null; then
  echo "✅ DCV Server 已运行"
  dcvgldiag 2>/dev/null || true
  echo "⏭ 跳过安装，进入验证"
  exit 0
fi

# 检查实例类型
ARCH=$(dpkg --print-architecture)
echo "架构: $ARCH"

# 检查是否在 EC2 上
TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600" 2>/dev/null)
if [ -z "$TOKEN" ]; then
  echo "⚠ 无法获取 EC2 metadata，可能不在 EC2 环境"
  echo "DCV 仅在 EC2 上免费使用，是否继续？"
fi

INSTANCE_TYPE=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/instance-type 2>/dev/null || echo "unknown")
echo "实例类型: $INSTANCE_TYPE"
```

#### Checkpoint（首次暂停）

汇报：实例类型、架构、DCV 是否已安装。确认是否继续。

### Phase 2: 安装桌面环境

```bash
echo "安装 GNOME 桌面环境..."
sudo apt-get update -qq
sudo apt-get install -y ubuntu-desktop-minimal gdm3

# 禁用 Wayland（DCV 不兼容）
sudo sed -i 's/#WaylandEnable=false/WaylandEnable=false/' /etc/gdm3/custom.conf 2>/dev/null || true

echo "✅ 桌面环境安装完成"
```

### Phase 3: 安装 DCV Server

```bash
ARCH=$(dpkg --print-architecture)

# 添加 DCV GPG key 和 repo
wget -q https://d1uj6qtbmh3dt5.cloudfront.net/NICE-GPG-KEY -O /tmp/NICE-GPG-KEY
gpg --import /tmp/NICE-GPG-KEY 2>/dev/null
sudo cp /tmp/NICE-GPG-KEY /etc/apt/trusted.gpg.d/dcv.asc

# 添加 DCV apt 源
echo "deb [signed-by=/etc/apt/trusted.gpg.d/dcv.asc] https://d1uj6qtbmh3dt5.cloudfront.net/ubuntu2404/$ARCH stable main" | \
  sudo tee /etc/apt/sources.list.d/nice-dcv.list

sudo apt-get update -qq
sudo apt-get install -y nice-dcv-server nice-dcv-web-viewer

# GPU 实例可选安装 GL 支持
if lspci | grep -qi nvidia; then
  sudo apt-get install -y nice-dcv-gl
  echo "✅ GPU GL 支持已安装"
fi

echo "✅ DCV Server 安装完成"
```

### Phase 4: 配置并启动 DCV

```bash
# 启动 DCV 服务
sudo systemctl enable dcvserver
sudo systemctl start dcvserver

# 创建控制台会话
CURRENT_USER=$(whoami)
dcv create-session --type=console --owner "$CURRENT_USER" my-session 2>/dev/null || \
  echo "⏭ Session 已存在"

# 验证
dcv list-sessions
systemctl status dcvserver --no-pager
```

#### Checkpoint

验证 DCV 运行状态：
```bash
systemctl is-active dcvserver && echo "✅ DCV 运行中"
dcv list-sessions | grep -q "my-session" && echo "✅ 会话已创建"
```

### Phase 5: SSM 端口转发说明

DCV 通过 SSM 安全访问，无需开放安全组端口：

```bash
# 在本地机器执行（非 EC2 上）：
# aws ssm start-session \
#   --target <instance-id> \
#   --document-name AWS-StartPortForwardingSession \
#   --parameters '{"portNumber":["8443"],"localPortNumber":["8443"]}'
#
# 然后浏览器访问 https://localhost:8443
```

向用户说明 SSM 连接方式。

## Verification

- [ ] `systemctl is-active dcvserver` 返回 "active"
- [ ] `dcv list-sessions` 显示 "my-session"
- [ ] `detect-display-env.sh` 输出 `has_display: true, display_type: dcv`

## Pitfalls

| 问题 | 解决 |
|------|------|
| Wayland 导致 DCV 黑屏 | 确认 `/etc/gdm3/custom.conf` 中 `WaylandEnable=false` |
| 非 GPU 实例显示问题 | DCV 自动使用软件渲染，无需操作 |
| Session 创建失败 | 确认当前用户已登录桌面环境：`loginctl list-sessions` |
| apt 源无法访问 | 检查 VPC 是否有 Internet 访问或 S3 endpoint |
