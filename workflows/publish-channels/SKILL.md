---
name: publish-channels
description: |
  CDP 自动化发布视频到微信视频号创作者中心。上传视频、填写元数据、AI 封面、发布。
  触发词：发视频号、publish channels、视频号发布。
  每个视频执行一次。
version: 1.0.0
platforms: [linux]
depends_on: [setup-chrome, setup-dcv]
frequency: per-video
estimated_time: 5-10min
metadata:
  openclaw:
    emoji: "📺"
    requires:
      bins: [python3, ffmpeg]
  hermes:
    category: workflow
    tags: [content-pipeline, publishing, video, browser]
---

# Publish Channels — 视频号发布

## When to Use

- F6/F11 视频渲染完成后
- 用户说"发到视频号"、"上传视频号"
- 需要 headed 模式 Chrome + DCV 远程桌面

## Input

- 视频文件：`output-compressed.mp4`（≤30min, ≤4GB）
- 用户已登录视频号创作者中心（channels.weixin.qq.com）

## Output

- 视频已发布到微信视频号
- 封面已设置（AI 从视频中提取最佳帧）

## Procedure

### Phase 1: 环境检查

```bash
# 必须有桌面环境（headed 模式）
ENV_JSON=$(bash ~/agent-skills/setup/shared/detect-display-env.sh 2>/dev/null || echo '{}')
MODE=$(echo "$ENV_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin).get('recommended_mode','unknown'))")

if [ "$MODE" = "headless" ]; then
  echo "❌ 视频号发布需要桌面环境（headed 模式）"
  echo "请先执行 setup-dcv 安装远程桌面"
  exit 1
fi

# 确认 CDP 可用
curl -s http://127.0.0.1:9222/json/version >/dev/null 2>&1 || \
  { echo "❌ CDP 不可用"; exit 1; }

# 确认视频号后台已登录
# 检查是否有 channels.weixin.qq.com 标签页
```

### Phase 2: AI 封面提取

```bash
# 从视频中提取候选帧（跳过片头片尾）
DURATION=$(ffprobe -v error -show_entries format=duration -of csv=p=0 input.mp4)
START=$(echo "$DURATION * 0.15" | bc)
END=$(echo "$DURATION * 0.85" | bc)

# 均匀采样 10 帧
ffmpeg -i input.mp4 -ss $START -to $END -vf "fps=10/$DURATION" -q:v 2 frame_%03d.jpg

# AI 评分选最佳帧
# 标准：信息密度 + 视觉吸引力 + 无字幕遮挡
# 裁切为 16:9 或 1:1
```

### Phase 3: CDP 自动发布

```
1. 导航到 channels.weixin.qq.com 发布页
2. DOM.setFileInputFiles 注入视频文件路径
3. 等待上传完成（轮询进度条）
4. 填写标题（AI 生成，≤30 字）
5. 填写描述 + hashtag
6. 设置封面（上传 Phase 2 选出的帧）
7. 点击"发表"
8. 确认发布成功
```

AI 元数据生成：
```
Kiro CLI 生成：
- 标题：≤30 字，吸引点击，含关键词
- 描述：1-2 句话概括内容
- Hashtag：3-5 个相关话题标签
```

### Phase 4: 验证

```
确认发布成功：
- 页面显示"发布成功"或跳转到作品管理页
- 作品列表中可见新视频
```

## Verification

- [ ] 视频已出现在视频号作品列表
- [ ] 封面正确显示
- [ ] 标题和描述已填写

## Pitfalls

| 问题 | 解决 |
|------|------|
| 视频号检测 headless | 必须用 headed 模式 + DCV |
| 页面结构变更 | CDP selector 失效，需更新 |
| 上传超时 | 视频过大，检查文件大小限制 |
| 登录态过期 | 提示用户在 DCV 桌面重新登录 |
| 审核不通过 | 检查内容是否违规，修改后重新发布 |
