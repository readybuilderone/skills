---
name: write-articles
description: |
  多 Agent 协作写作流水线。从 F1 日报中选题，11 Phase 生产高质量中文博客文章，发布到 GitHub Pages。
  触发词：写文章、开始写作、启动 Orchestrator、今日创作。
  通常在 F1 采集完成后自动触发。
version: 1.0.0
platforms: [linux]
depends_on: [collect-tech-news]
frequency: daily
estimated_time: 70-80min
metadata:
  openclaw:
    emoji: "✍️"
    requires:
      bins: [git, kiro-cli]
  hermes:
    category: workflow
    tags: [content-pipeline, writing, long-running]
---

# Write Articles — 多 Agent 协作写作

## When to Use

- F1 采集完成后，当日日报已生成
- 用户说"写文章"、"启动写作"
- 定时触发（通常在最后一批 F1 采集后）

## Input

- `output/YYYY-MM-DD.md`：当日 F1 日报（必须存在）
- `articles_index.json`：已发布文章索引（F5 提供，用于避免重复话题）
- `publish-config.json`：GitHub Pages 发布配置

## Output

- 7-10 篇高质量中文博客文章（3000-5000 字/篇）
- 发布到 GitHub Pages 博客
- `state.json`：写作流程状态和质量报告

## Procedure

### Phase 0: 话题池构建

从当日 F1 日报中提取候选话题：

```
读取 output/YYYY-MM-DD.md
提取所有新闻条目
按以下标准筛选候选话题：
- 时效性（过去 24h 内）
- 深度潜力（不是简单事实，有分析空间）
- 读者兴趣（技术从业者关注度）
- 与已发文章不重复（查 articles_index.json）

输出：15-20 个候选话题
```

### Phase 1: 选题（编辑决策）

从候选话题中选出 7 个最佳话题：

```
评估维度：
- 时效性权重 30%
- 深度潜力权重 25%
- 读者兴趣权重 25%
- 独特性权重 20%（同类文章少）

输出：7 个确认话题 + 每个话题的写作方向摘要
```

### Phase 2-4: 创作 + 评审 + 修正（并行）

7 批 × 3 篇初稿，最多 2 批并行：

```
每篇文章：
Phase 2: 创作（3000-5000 字，中文）
Phase 3: 质量评审（打分 0-100）
Phase 4: 修正（评分 < 75 重写，否则微调）

质量门禁：
- < 60 分：丢弃
- 60-75 分：重写一次（v2），v2 仍 < 75 则丢弃
- ≥ 75 分：通过
```

### Phase 5: 最终选择

从通过质量门禁的文章中选出最终发布集（7-10 篇）：

```
排序标准：
- 质量评分
- 话题多样性（避免同类扎堆）
- 时效性

输出：最终 7-10 篇文章 + 发布顺序
```

### Phase 6-7: 发布评估 + GitHub Pages 发布

```bash
# 生成 Jekyll 格式 markdown
# 添加 frontmatter (title, date, categories, tags)
# git add + commit + push 到 GitHub Pages repo
```

### Phase 8-10: 总结 + 质量检查

```
Phase 8: 生成本次写作总结（话题覆盖、质量分布、耗时）
Phase 9: 质量回顾（对比历史平均分）
Phase 10: 完成，更新 state.json
```

### Checkpoint 机制

每个 Phase 完成后写入 checkpoint：

```json
{
  "currentPhase": 5,
  "status": "completed",
  "checkpoint": {
    "phase5": {
      "selected_articles": 8,
      "avg_score": 82,
      "timestamp": "2026-05-06T15:30:00Z"
    }
  }
}
```

失败时最多重试 3 次，3 次仍失败暂停等待人工。

### 断点恢复

```bash
# 检查是否有未完成的写作流程
if [ -f "state.json" ] && python3 -c "
import json
s = json.load(open('state.json'))
run = s.get('currentRun', {})
if run.get('status') == 'in_progress':
    print(f'恢复: Phase {run[\"currentPhase\"]}')
    exit(0)
exit(1)
"; then
  echo "从断点恢复..."
  # 从 currentPhase 继续执行
fi
```

## Verification

- [ ] 至少 7 篇文章通过质量门禁（≥ 75 分）
- [ ] 文章已发布到 GitHub Pages
- [ ] `state.json` 标记 status=completed
- [ ] 无重复话题（与 articles_index.json 对比）

## Pitfalls

| 问题 | 解决 |
|------|------|
| F1 日报为空 | 跳过当天写作，通知用户 |
| 全部文章 < 75 分 | 降低门禁到 65 或暂停等人工 |
| Orchestrator 超 3h 无响应 | 看门狗判定僵死，kill 后从 checkpoint 恢复 |
| GitHub push 失败 | 检查 SSH key / PAT，重试 |
| Token 消耗超预算 | 减少并行批次数（从 2 降到 1） |
