---
name: vimax-multi-platform
description: |
  一条命令将文章转为三平台差异化视频（视频号/B站/小红书）。多智能体架构，断点恢复。
  触发词：三平台视频、vimax、全平台发布、一键视频。
  每篇文章执行一次，约 60-90 分钟。
version: 1.0.0
platforms: [linux]
depends_on: [setup-kiro, setup-chrome]
frequency: per-article
estimated_time: 60-90min
metadata:
  openclaw:
    emoji: "🚀"
    requires:
      bins: [node, ffmpeg, python3, kiro-cli]
  hermes:
    category: workflow
    tags: [content-pipeline, video, multi-platform, long-running]
---

# ViMax Multi-Platform — 三平台视频流水线

## When to Use

- 需要将一篇文章同时发布到视频号、B站、小红书
- 用户说"全平台发视频"、"一键三平台"
- 替代手动分别执行 article-to-video + publish-channels + publish-bili

## Input

- 文章来源：URL 或本地 `.md` 文件
- 可选：`--resume` 从断点恢复

## Output

```
output/vimax-YYYYMMDD-title/
├── style-a/          # 横屏 1920×1080（通用）
│   └── output-compressed.mp4
├── style-b/          # 竖屏 720×1280（视频号/小红书）
│   └── output-compressed.mp4
├── style-c/          # Claude 信息图竖屏
│   └── output-compressed.mp4
├── bili/             # B站专属版本
│   └── output-compressed.mp4
├── checkpoint.json   # 断点恢复状态
└── manifest.json     # 各版本元数据
```

## Procedure

### Phase 1: ScriptWriter Agent

```
输入：文章全文
输出：演讲稿（适配多种视频风格）

ScriptWriter 生成：
- 核心叙事线（story arc）
- 10-12 段内容块
- 每段标注：适合的视觉风格、情感基调
- B站版额外内容：梗、互动引导（"一键三连"）
```

Checkpoint: `checkpoint.json` 写入 `phase: "script_done"`

### Phase 2: IllustrationWriter Agent

```
输入：演讲稿 + 风格指定
输出：每段的配图描述（image prompt）

对 4 种风格分别生成：
- Style A: 专业、科技感、横屏构图
- Style B: 社交媒体风、竖屏构图、大字标题
- Style C: 信息图风格、数据可视化
- Bili: 动漫/二次元风格
```

Checkpoint: `phase: "illustration_done"`

### Phase 3: 资源生成

```bash
# 并发控制：Nova Reel 滑动窗口（最多 3 并发）
# 或 Unsplash + Bedrock Nova Canvas

for style in style-a style-b style-c bili; do
  generate_images "$style" &
  # 滑动窗口：等待空位后再启动下一个
  wait_for_slot 3
done
wait
```

Checkpoint: `phase: "assets_done"`

### Phase 4: TTS 合成

```bash
# 4 个版本共用同一段语音（内容相同）
# 仅 B 站版可能有额外口播内容

edge-tts --voice zh-CN-YunyangNeural \
  --text script.txt \
  --write-media speech.mp3 \
  --write-subtitles speech.vtt
```

Checkpoint: `phase: "tts_done"`

### Phase 5: 渲染（最耗时）

```bash
# 顺序渲染 4 个版本（Remotion 单实例锁）
for style in style-a style-b style-c bili; do
  npx remotion render \
    --composition="${style}Composition" \
    --props="{...}" \
    --output="$style/output-raw.mp4"

  # 压缩
  ffmpeg -i "$style/output-raw.mp4" -crf 23 "$style/output-compressed.mp4"

  # 每个版本渲染完更新 checkpoint
  update_checkpoint "render_${style}_done"
done
```

Checkpoint: `phase: "render_done"`

### Phase 6: 多平台发布

```bash
# 视频号（需要 headed + DCV）
if check_channels_available; then
  invoke_skill "publish-channels" --video style-b/output-compressed.mp4
fi

# B站（API）
invoke_skill "publish-bili" --video bili/output-compressed.mp4

# 小红书（如果有集成）
# invoke_skill "publish-xiaohongshu" --video style-b/output-compressed.mp4
```

Checkpoint: `phase: "publish_done"`

### 断点恢复

```bash
# 启动时检查 checkpoint
if [ -f "checkpoint.json" ] && [ "${1:-}" = "--resume" ]; then
  LAST_PHASE=$(python3 -c "import json; print(json.load(open('checkpoint.json'))['phase'])")
  echo "从 $LAST_PHASE 之后恢复..."
  # 跳过已完成的 phase
fi
```

## Verification

- [ ] 4 个版本的视频均已生成
- [ ] 每个视频 ≤ 20MB 且时长 3-5 分钟
- [ ] B站投稿成功
- [ ] 视频号发布成功（如环境支持）
- [ ] `manifest.json` 记录各版本元数据

## Pitfalls

| 问题 | 解决 |
|------|------|
| 渲染中途 OOM | 用 `--resume` 从断点恢复 |
| Nova Reel 并发限制 | 滑动窗口控制（最多 3 并发） |
| 全流程 90 分钟超时 | SubAgent 委托执行，不阻塞主 Agent |
| 某平台发布失败 | 不影响其他平台，标记失败后继续 |
| 磁盘空间不足 | 渲染完一个版本后删除原始帧 |
| B站和视频号内容相同 | 标题/描述差异化，视觉风格不同 |
