---
name: publish-bili
description: |
  B站 API 自动投稿。分片上传视频 + AI 生成标题/标签/简介 + 封面生成。
  触发词：发B站、投稿B站、publish bilibili、上传B站。
  每个视频执行一次。
version: 1.0.0
platforms: [linux]
depends_on: [setup-kiro]
frequency: per-video
estimated_time: 5-10min
metadata:
  openclaw:
    emoji: "📡"
    requires:
      bins: [python3, bilitool]
  hermes:
    category: workflow
    tags: [content-pipeline, publishing, video, bilibili]
---

# Publish Bili — B站投稿

## When to Use

- F6/F11 视频渲染完成后
- 用户说"发到B站"、"B站投稿"
- 纯 API 方式，不需要浏览器

## Input

- 视频文件：`output-compressed.mp4`
- bilitool 已登录（cookie 有效期 ~30 天）

## Output

- 视频已投稿到 B 站（等待审核）
- AI 生成的标题/标签/简介
- AI 生成封面（可选）

## Procedure

### Phase 1: 检查登录状态

```bash
# 确认 bilitool 已安装
command -v bilitool &>/dev/null || pip3 install bilitool

# 检查登录状态
bilitool account info 2>/dev/null && echo "✅ B站已登录" || {
  echo "❌ B站未登录，请执行："
  echo "  bilitool login"
  echo "  (扫描二维码登录)"
  exit 1
}
```

### Phase 2: AI 生成元数据

```
通过 Kiro CLI 生成 B 站风格的元数据：

标题（≤80 字）：
- B站风格：有吸引力、可加括号标注重点
- 示例："【深度解析】Claude 4 为什么能碾压 GPT-5？三个核心技术突破"

标签（≤12 个，每个 ≤20 字）：
- 必含：AI、人工智能
- 相关技术标签
- 热门话题标签

简介（≤2000 字）：
- 概述视频内容
- 时间轴标记（如果视频分段明确）
- 相关链接
```

### Phase 3: 上传视频

```bash
# 分片上传（大文件自动分片）
bilitool upload \
  --video output-compressed.mp4 \
  --title "AI 生成的标题" \
  --desc "AI 生成的简介" \
  --tag "AI,人工智能,技术" \
  --tid 122 \
  --copyright 1 \
  --cover cover.jpg

# tid 122 = 科技/野生技术协会（可根据内容调整）
# copyright: 1=原创, 2=转载
```

分区参考：
| tid | 分区 |
|-----|------|
| 122 | 科技/野生技术协会 |
| 207 | 科技/计算机技术 |
| 208 | 科技/工业与商业 |
| 209 | 科技/极客DIY |

### Phase 4: 封面处理

```bash
# 方式 1：从视频中提取最佳帧（与 publish-channels 共用逻辑）
ffmpeg -i output-compressed.mp4 -ss 30 -frames:v 1 cover-candidate.jpg

# 方式 2：AI 生成竖版封面（Bedrock SD3.5 Large）
# Kiro CLI 生成 prompt → 生成 960×600 封面

# 上传封面
bilitool cover upload cover.jpg
```

### Phase 5: 确认投稿

```bash
# 查看最近投稿状态
bilitool video list --limit 1

# 输出：
# - BV号
# - 审核状态（处理中/已过审/未通过）
# - 预计审核时间：1-24 小时
```

## Verification

- [ ] `bilitool video list` 显示新投稿
- [ ] 标题/标签/简介已正确设置
- [ ] 封面已上传
- [ ] 无上传错误

## Pitfalls

| 问题 | 解决 |
|------|------|
| Cookie 过期（~30天） | `bilitool login` 重新扫码 |
| 上传限速 | 海外服务器换 CDN：`--cdn tx` 或 `--cdn bda2` |
| 审核不通过 | 检查标题是否敏感词，修改后重投 |
| 分P投稿失败 | 子账号不支持，需用主账号 |
| 文件过大上传断 | bilitool 自动断点续传 |
