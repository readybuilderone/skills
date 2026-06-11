---
name: chess-tactics-setup
description: 安装和配置 chess-tactics skill 的依赖。检查 Stockfish、python-chess、librsvg 是否就绪，缺失则自动安装；检查棋盘图片是否已预生成，未生成则批量生成。Use when user says "setup chess" or before first use of /chess-tactics if dependencies are missing.
---

# Chess Tactics Setup

## What It Does

检查并安装 `/chess-tactics` skill 所需的全部依赖：

| 依赖 | 用途 | 安装方式 |
|------|------|----------|
| stockfish | 国际象棋引擎，分析局面 | `brew install stockfish` |
| librsvg (rsvg-convert) | SVG → PNG 转换 | `brew install librsvg` |
| python-chess | 棋盘渲染 + 走法解析 | `pip install python-chess` |
| board images | 1416 张预生成棋盘图 | 运行 generate-all-boards.py |

## Usage

```bash
python3 .claude/skills/chess-tactics/scripts/setup.py
```

## Workflow

运行 setup 脚本：

```bash
python3 .claude/skills/chess-tactics/scripts/setup.py
```

脚本会：
1. 检查 `stockfish` 是否在 PATH 中，没有则 `brew install`
2. 检查 `rsvg-convert` 是否在 PATH 中，没有则 `brew install librsvg`
3. 检查 `python-chess` 是否可导入，没有则 `pip install`
4. 检查 `horse-puzzle.pgn` 是否存在
5. 检查 `boards/` 目录是否有 >= 1400 张图片，不足则运行预生成

全部通过后输出 `✓ All dependencies satisfied.`
