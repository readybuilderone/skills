---
name: chess-tactics
description: 国际象棋战术习题练习教练。从 horse-puzzle.pgn 中选题，渲染棋盘图片，用 Stockfish 分析走法，多轮讨论讲解。Use when user wants to practice chess tactics, mentions 战术/习题/chess puzzle, or says /chess-tactics.
---

# Chess Tactics Coach

## Quick Start

用户调用 `/chess-tactics <自然语言描述>` 开始练习。

示例：
- `/chess-tactics 来道入门题`
- `/chess-tactics 给我第42题`
- `/chess-tactics 来道难的`
- `/chess-tactics 上一题的配对题`

## Workflow

### 1. 选题

根据用户请求从 PGN 中选题。参考 [PUZZLE-DB.md](PUZZLE-DB.md) 了解数据结构。

**智能推荐**：如果用户未指定主题/难度（如"来道题"），先读取练习日志 `practice-log.jsonl`，按主题×难度交叉分析正确率，倾向推荐薄弱组合。样本 < 3 的组合不算薄弱。

### 2. 出题

1. 从 `boards/` 目录读取预生成的棋盘 PNG 图片，文件名格式为 `{puzzle_id}_{side}.png`（如 `42_w.png`、`739_b.png`）
2. 用 Read 工具展示图片 + 基本信息（题号、谁先走、难度星级）
3. **默认不透露战术主题**，用户问了才告知

如果预生成图片缺失，用 [render-board.py](scripts/render-board.py) 临时生成。

### 3. 用户作答（逐步考察）

关键着数（Black 字段）表示这道题有几步非显然决策。**必须逐步考察每一个关键步骤**，不能只问第一步就揭晓答案。

流程：
1. 用户给出第一步走法 → 验证是否正确
2. 如果正确，回复对手的应着（强制着法），然后问用户"接下来呢？"
3. 继续直到所有关键步骤都考察完毕
4. 只有用户答出所有关键步骤才算 `correct`；答出部分算 `partial`

例如 Black=3 的题（3 步关键着）：
- 用户答对第 1 步 → 给出对手应着 → 问第 2 步
- 用户答对第 2 步 → 给出对手应着 → 问第 3 步
- 用户答对第 3 步 → 全部正确

如果用户某一步答错，可以提示后让用户再想，或直接进入讲解。

### 4. 分析反馈

用 Stockfish 验证用户走法，对比 PGN 标准答案：

- **PGN 答案**：展示出题者意图（战术主题的教学目标）
- **Stockfish 评估**：客观最优解，补充引擎视角

调用方法见 [STOCKFISH.md](STOCKFISH.md)。

### 5. 多轮讨论

保持教练角色。用户可以追问：
- "为什么不能走 Nf3？"
- "如果对手不吃呢？"
- "还有别的解法吗？"

每次用 Stockfish 分析用户提出的变体。

### 6. 记录日志

**每做完一道题（给出反馈后）立即记录日志**，不要等到对话结束。如果用户接着做了配对题，配对题做完后也立即记录。

追加记录到 `practice-log.jsonl`：

```json
{"timestamp":"...","puzzle_id":"42","side":"w","theme":"引离","difficulty":3,"result":"correct|partial|incorrect","user_moves":["Rxh7+","Kxf5"],"notes":"一句话总结"}
```

时机：
- 单题：反馈讲解完成后立即写入
- 配对题：主题做完记录一条，配对题做完再记录一条

### 7. 配对题推荐

如果当前题有配对题（同题号、不同 side-to-move），反馈结束时提示：
> "这道题有配对题（同局面，换对方先走），要试试吗？"

## 练习报告

用户说"分析我的练习情况"或"推荐复习"时：
1. 读取 `practice-log.jsonl`
2. 按主题×难度交叉统计正确率
3. 找出明显低于整体平均的薄弱组合
4. 给出具体建议和推荐题目

## Language

- 讲解、反馈、对话：中文
- 棋谱记号：英文标准代数记号（Rxh7+, Nf3, O-O）
