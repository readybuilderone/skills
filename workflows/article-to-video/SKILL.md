---
name: article-to-video
description: |
  文章转 3-5 分钟短视频。AI 演讲稿 + TTS 语音 + Remotion 视觉渲染 + FFmpeg 合成。
  触发词：转视频、生成视频、article to video、文章做成视频。
  每篇文章执行一次，约 40 分钟。
version: 1.0.0
platforms: [linux]
depends_on: [setup-chrome]
frequency: per-article
estimated_time: 40min
metadata:
  openclaw:
    emoji: "🎬"
    requires:
      bins: [node, ffmpeg, python3]
  hermes:
    category: workflow
    tags: [content-pipeline, video, long-running]
---

# Article to Video — 文章转短视频

## When to Use

- F2 写作完成后，将文章转为短视频
- 用户指定某篇文章 URL 或 Markdown
- 触发词："把这篇文章做成视频"

## Input

- 文章来源：URL 或本地 `.md` 文件
- 模板选择：横屏（1920×1080）或 竖屏（720×1280）

## Output

- `output/video-YYYYMMDD-title/`
  - `output-compressed.mp4`：最终视频（≤20MB）
  - `speech.json`：演讲稿 + 时间戳
  - `subtitles.srt`：字幕文件
  - `thumbnail.jpg`：封面帧

## Procedure

### Phase 1: 生成演讲稿

```
输入：文章全文
输出：10 段演讲稿 + key_facts

每段包含：
- text: 演讲内容（口语化）
- key_facts: 结构化数据（用于视觉布局选择）
  - type: stats | list | comparison | quote | grid
  - data: 对应的结构化数据

约束：
- 总时长 3-5 分钟（按 TTS 语速预估）
- 口语化，不是读文章
- 开场有固定格式引入
```

### Phase 2A: TTS 语音合成

```bash
# Edge TTS（默认，免费）
edge-tts --voice zh-CN-YunyangNeural --text "演讲稿" --write-media speech.mp3 --write-subtitles speech.vtt

# 或 MiniMax（更高质量，收费）
# 通过参考音频方式指定音色
```

关键：使用 WordBoundary 事件获取精确时间戳（零误差字幕）。

### Phase 2B: 配图获取

```
对每段：
1. 根据 key_facts 类型选择视觉布局
2. 从 Unsplash 搜索相关图片（免费高质量）
3. 或调用 Bedrock Nova Canvas 生成 AI 图片
4. 下载并缓存
```

### Phase 3: 字幕生成

```
从 TTS WordBoundary 时间戳直接生成 SRT：
- 每句一条字幕
- 时间精确到毫秒
- 无需 Whisper（避免同音字错误）
```

### Phase 4: Remotion 渲染

```bash
# 单实例保护（PID 锁）
LOCK_FILE="/tmp/remotion-render.lock"
if [ -f "$LOCK_FILE" ] && kill -0 $(cat "$LOCK_FILE") 2>/dev/null; then
  echo "❌ 另一个渲染任务正在运行"
  exit 1
fi
echo $$ > "$LOCK_FILE"

# 渲染
npx remotion render \
  --composition=ArticleVideo \
  --props="{\"speechData\":\"speech.json\",\"template\":\"landscape\"}" \
  --output=output-raw.mp4 \
  --concurrency=50%

rm -f "$LOCK_FILE"
```

视觉元素：
- 背景图 + Ken Burns 缩放/平移动效
- 字幕条（底部，半透明背景）
- 虚拟人物半身像（727×1290，右下角）
- 结构化数据布局（根据 key_facts.type 选择）
- 片头白板（虚拟白板 880×560）

### Phase 5: FFmpeg 压缩

```bash
ffmpeg -i output-raw.mp4 \
  -c:v libx264 -crf 23 -preset medium \
  -c:a aac -b:a 128k \
  -movflags +faststart \
  output-compressed.mp4

# 确保 ≤ 20MB（视频号/B站限制）
SIZE=$(stat -f%z output-compressed.mp4 2>/dev/null || stat -c%s output-compressed.mp4)
if [ "$SIZE" -gt 20971520 ]; then
  ffmpeg -i output-raw.mp4 -crf 28 -preset slow output-compressed.mp4
fi
```

## Verification

- [ ] `output-compressed.mp4` 存在且 ≤ 20MB
- [ ] 视频时长 3-5 分钟
- [ ] 字幕与语音同步（抽检 3 个时间点）
- [ ] 无黑屏/花屏帧

## Pitfalls

| 问题 | 解决 |
|------|------|
| Edge TTS 超时 | 重试 3 次，间隔 5 秒 |
| Remotion 渲染 OOM | 降低 concurrency 到 25% |
| ARM64 渲染慢（~27min） | 正常现象，不要中断 |
| PID 锁残留 | 检查进程是否存在，不存在则删除锁文件 |
| 生成图片有文字乱码 | prompt 加 "NO TEXT, no words, no letters" |
| 视频超 20MB | 提高 CRF 值或缩短时长 |
