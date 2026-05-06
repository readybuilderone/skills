---
name: archive-weixin
description: |
  微信公众号文章索引与内容备份。拉取全量已发布文章，下载正文为 Markdown，维护可搜索索引。
  触发词：归档公众号、同步文章、备份微信。
  建议每周执行一次或新文章发布后执行。
version: 1.0.0
platforms: [linux]
depends_on: [setup-chrome]
frequency: weekly
estimated_time: 10-30min
metadata:
  openclaw:
    emoji: "📦"
    requires:
      bins: [python3, curl]
  hermes:
    category: workflow
    tags: [content-pipeline, archival, weixin]
---

# Archive Weixin — 微信公众号归档

## When to Use

- 每周定期同步（增量备份新文章）
- F4 发布后同步最新文章到索引
- 用户说"备份公众号"、"同步文章索引"
- 需要为 F4 扩展阅读或 F6/F11 视频选题提供数据源

## Input

- 微信后台 Session（cookie + token，通过 CDP 自动提取或手动提供）
- 已有的 `articles_index.json`（增量更新）

## Output

- `articles_index.json`：全量文章索引（标题、URL、日期、分类、摘要）
- `articles/YYYY-MM-DD_title.md`：正文 Markdown 备份
- `articles/images/`：文章内图片本地备份

## Procedure

### Phase 1: 获取 Session

```bash
# 方式 1：CDP 自动提取（推荐）
# 需要用户在浏览器中已登录微信公众号后台
CDP_URL="http://127.0.0.1:9222"

# 通过 CDP 执行 JS 提取 cookie 和 token
# Runtime.evaluate: document.cookie
# 解析出 token 参数

# 方式 2：手动提供
# 用户提供 cookie 和 token
```

Session 有效期约 2 小时，过期需重新提取。

### Phase 2: 拉取文章列表

三源合并（按优先级）：

```
1. 发布管理 API（freepublish/batchget）— 最新文章
2. 素材管理 API（material/batchget）— 历史文章
3. 后台管理接口 — 最完整（需 admin session）

合并去重：以 URL 为唯一键
增量模式：只处理 articles_index.json 中不存在的文章
```

### Phase 3: 下载正文

```
对每篇新文章：
1. 请求文章 URL
2. readability 提取正文
3. html2text 转 Markdown
4. 下载文中图片到本地
5. 替换图片引用为本地路径
6. 限速：每篇间隔 2-3 秒
```

### Phase 4: 更新索引

```python
# 更新 articles_index.json
for article in new_articles:
    index.append({
        "title": article.title,
        "url": article.url,
        "date": article.publish_date,
        "category": classify(article),
        "summary": extract_summary(article, max_chars=200),
        "golden_quotes": extract_quotes(article),
        "local_path": f"articles/{filename}.md"
    })

# 按日期倒序排列
index.sort(key=lambda x: x['date'], reverse=True)
save_json(index)
```

## Verification

- [ ] `articles_index.json` 已更新（条目数 ≥ 之前）
- [ ] 新文章 Markdown 文件已保存
- [ ] 图片已下载到本地
- [ ] 无 404 或空内容文章

## Pitfalls

| 问题 | 解决 |
|------|------|
| Session 过期（2h） | 重新通过 CDP 提取或提示用户刷新后台页面 |
| API 返回 48001 无权限 | 订阅号不支持 freepublish API，改用后台接口 |
| 文章正文 JS 渲染失败 | 降级用 CDP 在浏览器中打开后抓取 |
| 限速被封 | 增加间隔到 5 秒，减少并发 |
| 图片防盗链 | 在浏览器上下文中 fetch（设置 Referer） |
