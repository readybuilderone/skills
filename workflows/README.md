# Workflow Skills — 内容生产流水线

日常重复执行的内容生产与分发 Skills，支持 OpenClaw 和 Hermes 双平台。

## 流水线全景

```
collect-tech-news (每日6次)
        │
        ▼
write-articles (每日1次, ~80min)
        │
        ├──→ publish-weixin (每篇, ~3min)
        │         │
        │         ▼
        │    archive-weixin (每周)
        │
        ├──→ article-to-video (每篇, ~40min)
        │         │
        │         ├──→ publish-channels (每个视频, ~5min)
        │         └──→ publish-bili (每个视频, ~5min)
        │
        ├──→ article-to-podcast (每篇, ~20min)
        │
        └──→ vimax-multi-platform (每篇, ~90min, 整合上述)

独立：download-expenses (每月)
```

## Skill 列表

| Skill | 频率 | 时长 | 输入 | 输出 |
|-------|------|------|------|------|
| `collect-tech-news` | 6次/天 | 5-10min | Exa API | 日报 Markdown |
| `write-articles` | 1次/天 | 70-80min | 日报 | 博客文章 (GitHub Pages) |
| `publish-weixin` | 每篇 | 2-3min | 文章 URL/MD | 公众号草稿 |
| `archive-weixin` | 每周 | 10-30min | 微信 Session | 文章索引 + 本地备份 |
| `article-to-video` | 每篇 | ~40min | 文章 | MP4 视频 |
| `publish-channels` | 每视频 | 5-10min | MP4 | 视频号已发布 |
| `publish-bili` | 每视频 | 5-10min | MP4 | B站已投稿 |
| `article-to-podcast` | 每篇 | 15-20min | 文章 | 播客 MP3 + RSS |
| `vimax-multi-platform` | 每篇 | 60-90min | 文章 | 三平台视频 |
| `download-expenses` | 每月 | 15-30min | 邮箱会话 | 发票 PDF |

## 依赖关系

```
setup-base ←── 所有 workflow 的基础
setup-kiro ←── collect-tech-news, write-articles, publish-weixin,
               publish-bili, article-to-podcast, vimax-multi-platform
setup-chrome ←── download-expenses, archive-weixin, publish-channels,
                 article-to-video, vimax-multi-platform
setup-dcv ←── publish-channels（需要 headed 模式）
```

## 安装

```bash
# npx skills
npx skills add readybuilderone/skills

# 或手动
cp -r workflows/* ~/.openclaw/workspace/skills/   # OpenClaw
cp -r workflows/* ~/.hermes/skills/               # Hermes
```

## 典型使用场景

### 每日内容生产

```
用户: "采集今日资讯"
→ collect-tech-news 执行

用户: "开始写作"
→ write-articles 执行 (80min, SubAgent)

用户: "把今天的文章发公众号"
→ publish-weixin × N 篇

用户: "做成视频发全平台"
→ vimax-multi-platform 执行 (90min, SubAgent)
```

### 每周维护

```
用户: "同步公众号文章"
→ archive-weixin 执行
```

### 每月报销

```
用户: "下载这个月的发票"
→ download-expenses 执行
```
