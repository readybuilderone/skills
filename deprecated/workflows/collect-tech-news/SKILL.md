---
name: collect-tech-news
description: |
  每日 AI 资讯采集。通过 Exa 搜索 7 个维度，分类为 6 大主题，增量去重输出结构化日报。
  触发词：采集资讯、今日新闻、tech update、AI 动态。
  定时触发：每日 07/10/13/16/19/22:00 (北京时间)。
version: 1.0.0
platforms: [linux]
depends_on: [setup-kiro]
frequency: daily-6x
estimated_time: 5-10min
metadata:
  openclaw:
    emoji: "📰"
    requires:
      bins: [kiro-cli]
      env: [EXA_API_KEY]
  hermes:
    category: workflow
    tags: [content-pipeline, data-collection, daily]
---

# Collect Tech News — AI 资讯采集

## When to Use

- 每日定时触发（6 次/天）
- 用户说"采集今日资讯"、"有什么新闻"
- F2 写作系统启动前，需要当日素材
- 宕机恢复后，补采缺失时段的资讯

## Input

- `EXA_API_KEY` 环境变量
- `state.json`：上次采集时间（增量窗口）
- `topics-definition.md`：6 大主题关键词定义

## Output

- `output/YYYY-MM-DD.md`：结构化日报（追加模式，多批次去重）
- `state.json`：更新 `lastCollectorCheck` 时间戳

## Procedure

### Phase 1: 确定搜索窗口

```bash
OUTPUT_DIR="output"
STATE_FILE="state.json"
TODAY=$(date +%Y-%m-%d)
mkdir -p "$OUTPUT_DIR"

# 读取上次采集时间
if [ -f "$STATE_FILE" ]; then
  LAST_CHECK=$(python3 -c "import json; print(json.load(open('$STATE_FILE')).get('lastCollectorCheck',''))")
  echo "上次采集: $LAST_CHECK"
else
  LAST_CHECK=""
fi

# 计算搜索窗口
if [ -z "$LAST_CHECK" ]; then
  # 首次/恢复：兜底 24h
  START_DATE=$(date -d "24 hours ago" +%Y-%m-%dT%H:%M:%S 2>/dev/null || date -v-24H +%Y-%m-%dT%H:%M:%S)
  echo "首次采集，搜索窗口: 过去 24 小时"
else
  START_DATE="$LAST_CHECK"
  echo "增量采集，从 $START_DATE 开始"
fi

END_DATE=$(date +%Y-%m-%dT%H:%M:%S)
echo "搜索窗口: $START_DATE → $END_DATE"
```

### Phase 2: 7 维度 Exa 搜索

通过 Kiro CLI 调用 Exa MCP 的 `web_search_advanced_exa`，7 个维度依次搜索：

| 维度 | 关键词方向 | 来源偏好 |
|------|-----------|---------|
| A | General AI news | 官方博客、主流媒体 |
| B | AI Leaders (Sam Altman, Dario Amodei...) | Twitter/X, 个人博客 |
| C | Enterprise AI adoption | 企业博客、案例报告 |
| D | AI Critics (Gary Marcus...) | 学术、评论 |
| E | AI Startups / Fundraising | TechCrunch, VentureBeat |
| F | AWS AI updates | AWS 官方博客 |
| G | Anthropic / Claude updates | Anthropic 博客 |

对每个维度：

```
kiro-cli chat --message "
使用 web_search_advanced_exa 工具搜索：
- query: [维度关键词]
- start_published_date: $START_DATE
- end_published_date: $END_DATE
- num_results: 10
- type: auto

返回 JSON 格式结果：[{title, url, published_date, source, summary}]
" --max-turns 3
```

零结果的维度静默跳过，不报错。

### Phase 3: 去重与分类

```python
# 伪代码逻辑
existing_urls = extract_urls_from(f"output/{TODAY}.md")
new_items = [item for item in all_results if item.url not in existing_urls]

# 按 6 大主题分类
topics = {
    "Agent": [],        # Agentic AI 动态
    "OrgStructure": [], # AI 组织架构变化
    "UseCases": [],     # Agentic 实践案例
    "Commerce": [],     # Agentic 商业模式
    "Enterprise": [],   # 企业 AI 战略
    "DevLifecycle": []  # AI 开发生命周期
}

for item in new_items:
    topic = classify_by_keywords(item, topics_definition)
    topics[topic].append(item)
```

### Phase 4: 追加写入日报

```bash
# 追加到今日日报（不覆盖已有内容）
cat >> "output/$TODAY.md" << EOF

---
## Batch $(date +%H:%M) — 新增 ${#new_items[@]} 条

### Agent
...

### Enterprise
...
EOF
```

### Phase 5: 更新状态

```bash
python3 -c "
import json
from datetime import datetime
state = json.load(open('$STATE_FILE')) if os.path.exists('$STATE_FILE') else {}
state['lastCollectorCheck'] = datetime.now().isoformat()
state['todayBatchCount'] = state.get('todayBatchCount', 0) + 1
state['totalItems'] = state.get('totalItems', 0) + len(new_items)
json.dump(state, open('$STATE_FILE', 'w'), indent=2)
"
echo "✅ 采集完成，新增 X 条，今日第 N 批"
```

## Verification

- [ ] `output/YYYY-MM-DD.md` 文件已更新
- [ ] 新条目无重复 URL
- [ ] `state.json` 的 `lastCollectorCheck` 已更新
- [ ] 各主题至少有部分覆盖（允许部分维度零结果）

## Pitfalls

| 问题 | 解决 |
|------|------|
| Exa API 限流 | 降低单次 num_results，增加请求间隔 |
| Kiro CLI session 过期 | `kiro-cli login` 重新登录 |
| 某维度零结果 | 正常现象，静默跳过 |
| 时区问题 | 统一使用 UTC，显示时转北京时间 |
