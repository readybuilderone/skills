---
name: article-to-podcast
description: |
  文章转多人对话播客音频。AI 生成对话脚本 + 多角色 TTS + 音频拼接 + RSS Feed。
  触发词：转播客、生成播客、article to podcast、做成音频。
  每篇文章执行一次，约 15-20 分钟。
version: 1.0.0
platforms: [linux]
depends_on: [setup-kiro]
frequency: per-article
estimated_time: 15-20min
metadata:
  openclaw:
    emoji: "🎙️"
    requires:
      bins: [python3, ffmpeg]
  hermes:
    category: workflow
    tags: [content-pipeline, audio, podcast]
---

# Article to Podcast — 文章转播客

## When to Use

- F2 写作完成后，将文章转为播客音频
- 用户指定某篇文章
- 触发词："把这篇做成播客"、"生成音频"

## Input

- 文章来源：URL 或本地 `.md` 文件
- 可选：角色配置（主持人/嘉宾声音选择）

## Output

- `output/podcast-YYYYMMDD-title/`
  - `episode.mp3`：最终音频（响度标准化 -16 LUFS）
  - `script.json`：对话脚本
  - `cover.jpg`：播客封面
  - `metadata.json`：标题、描述、章节标记
  - `feed.xml`：RSS Feed（可选更新）

## Procedure

### Phase 1: 生成对话脚本

```
输入：文章全文
输出：35-40 轮多人对话脚本

角色：
- Host（主持人）：引导话题、提问、总结
- Guest（嘉宾）：深度分析、举例、提供观点

脚本要求：
- 自然对话风格（不是朗读文章）
- 有互动感（追问、回应、补充）
- 总时长 25-35 分钟
- 每轮 2-5 句话

输出格式：
[
  {"role": "host", "text": "...", "emotion": "curious"},
  {"role": "guest", "text": "...", "emotion": "excited"},
  ...
]
```

### Phase 2: 多角色 TTS 合成

TTS 后端选择（按优先级）：

```
1. MiniMax（中文最优，参考音频方式指定音色）
2. ElevenLabs（英文最优）
3. Edge TTS（免费降级方案）
```

```bash
# 对每轮对话：
for turn in script:
    if turn.role == "host":
        voice = HOST_VOICE  # 随机轮换增加多样性
    else:
        voice = GUEST_VOICE  # 固定嘉宾声音

    tts_synthesize(turn.text, voice, output=f"segment_{i}.mp3")
```

角色音色配置：
| 角色 | MiniMax 音色 | Edge TTS 备选 |
|------|-------------|---------------|
| Host | 参考音频 A | zh-CN-YunyangNeural |
| Guest | 参考音频 B | zh-CN-YunxiNeural |

### Phase 3: 音频拼接 + 后处理

```bash
# 拼接所有片段
ffmpeg -f concat -safe 0 -i segments.txt -c copy raw_episode.mp3

# 响度标准化（播客标准 -16 LUFS）
ffmpeg -i raw_episode.mp3 \
  -af loudnorm=I=-16:TP=-1.5:LRA=11 \
  episode.mp3

# 可选：添加背景音乐（0.08 音量）
ffmpeg -i episode.mp3 -i bgm.mp3 \
  -filter_complex "[1]volume=0.08[bg];[0][bg]amix=inputs=2:duration=shortest" \
  episode_with_bgm.mp3
```

### Phase 4: 元数据 + 封面

```
1. AI 生成播客标题和描述
2. 生成章节标记（基于对话脚本的话题转换点）
3. AI 生成封面（Bedrock SD3.5 Large）
4. 写入 metadata.json
```

### Phase 5: RSS Feed 更新（可选）

```xml
<!-- 追加新 episode 到 feed.xml -->
<item>
  <title>Episode 标题</title>
  <enclosure url="https://your-host/episode.mp3" type="audio/mpeg"/>
  <pubDate>发布日期</pubDate>
  <itunes:duration>时长</itunes:duration>
  <description>描述</description>
</item>
```

支持分发：Apple Podcasts / Spotify / 小宇宙 / 喜马拉雅

## Verification

- [ ] `episode.mp3` 存在，时长 25-35 分钟
- [ ] 音频无异常（无静音段、无爆音）
- [ ] 两个角色声音可区分
- [ ] 响度符合 -16 LUFS 标准
- [ ] metadata.json 完整

## Pitfalls

| 问题 | 解决 |
|------|------|
| MiniMax API 限流 | 降级到 Edge TTS |
| 对话脚本不自然 | 重新生成，强调"像真人聊天" |
| 音频片段间有跳变 | 加 crossfade：`-af acrossfade=d=0.3` |
| 总时长过短 | 增加对话轮数（40→50 轮） |
| Edge TTS 中文发音错误 | 对专有名词加拼音标注 |
| RSS Feed 格式错误 | 用 feedvalidator.org 验证 |
