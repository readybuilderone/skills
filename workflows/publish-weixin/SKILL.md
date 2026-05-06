---
name: publish-weixin
description: |
  博客文章自动发布微信公众号。两阶段发布：快速草稿 + AI 封面/引言增强。
  触发词：发微信、发公众号、publish weixin、推送文章。
  每篇文章执行一次。
version: 1.0.0
platforms: [linux]
depends_on: [setup-kiro, setup-chrome]
frequency: per-article
estimated_time: 2-3min
metadata:
  openclaw:
    emoji: "💬"
    requires:
      bins: [python3, kiro-cli]
      env: [WEIXIN_APP_ID, WEIXIN_APP_SECRET]
  hermes:
    category: workflow
    tags: [content-pipeline, publishing, weixin]
---

# Publish Weixin — 微信公众号发布

## When to Use

- F2 写作完成后，将文章发布到微信公众号
- 用户指定某篇博客 URL 或本地 Markdown 发布
- 触发词："发到公众号"、"推送微信"

## Input

- 文章来源：博客 URL 或本地 `.md` 文件
- 微信公众号 API 凭证（WEIXIN_APP_ID, WEIXIN_APP_SECRET）
- `articles_index.json`：历史文章索引（扩展阅读匹配用）

## Output

- 微信公众号草稿（可在后台确认发布）
- AI 生成封面图（5 种风格可选）
- AI 生成引言（100 字内）
- 扩展阅读推荐（5+ 篇历史文章）

## Procedure

### Phase 1: 快速草稿（~10 秒）

```
1. 获取文章内容：
   - URL → readability + html2text → Markdown
   - 本地文件 → 直接读取

2. Markdown → 微信 HTML（内联样式）

3. 上传文章内图片到微信 CDN（去重，已上传跳过）

4. 通过微信 API 创建草稿：
   POST https://api.weixin.qq.com/cgi-bin/draft/add
   {
     "articles": [{
       "title": "文章标题",
       "content": "微信 HTML",
       "digest": "摘要",
       "thumb_media_id": "默认封面"
     }]
   }

5. 汇报：草稿已创建，media_id = xxx
```

### Phase 2: AI 增强（~2 分钟）

```
1. AI 引言生成（Kiro CLI）：
   - 输入：文章标题 + 前 500 字
   - 输出：100 字内吸引读者的摘要

2. AI 封面生成：
   - Kiro CLI 生成文生图 prompt（基于文章主题）
   - Bedrock SD3.5 Large 出图
   - 5 种风格：赛博朋克/科幻/像素/漫画/浮世绘
   - 上传封面到微信 CDN

3. 扩展阅读推荐：
   - 从 articles_index.json 语义匹配 5+ 篇相关历史文章
   - 生成"相关阅读"HTML 块，追加到文章末尾

4. 更新草稿：
   POST https://api.weixin.qq.com/cgi-bin/draft/update
   - 更新封面、引言、扩展阅读

5. 汇报：草稿已更新，封面风格 = xxx
```

### 资源去重

```python
registry = load_registry()
# 跳过已上传的图片
if image_hash in registry['uploaded_images']:
    media_id = registry['uploaded_images'][image_hash]
else:
    media_id = upload_to_weixin(image)
    registry['uploaded_images'][image_hash] = media_id
```

## Verification

- [ ] 微信后台可见新草稿
- [ ] 封面图已生成并上传
- [ ] 引言字数 ≤ 100
- [ ] 扩展阅读链接有效
- [ ] 图片在手机端正常显示

## Pitfalls

| 问题 | 解决 |
|------|------|
| Access Token 过期 | 重新获取：`/cgi-bin/token` |
| 图片上传失败 | 检查图片格式（仅支持 jpg/png），大小 < 10MB |
| Markdown 有序列表渲染异常 | 已知 bug：`nl2br` + 空行导致 `<li><p>` 嵌套 |
| 封面生成失败 | 降级使用默认封面，Phase 2 不阻塞 Phase 1 |
| 文章超 20K 字符 | 警告用户，微信可能截断 |
