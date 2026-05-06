# Puzzle Database

## File Location

`horse-puzzle.pgn` in project root.

## Encoding

GB2312 with CRLF line terminators. Always read with:

```python
with open('horse-puzzle.pgn', 'rb') as f:
    content = f.read().decode('gb2312').replace('\r\n', '\n')
```

## PGN Structure

Each puzzle is a PGN game entry:

```
[Event "战术主题"]
[White "题号"]
[Black "关键着数"]
[Result "1-0|0-1|1/2-1/2"]
[FEN "..."]

1. e4 e5 2. Nf3 1-0
```

- **Event**: 战术主题（16 种）
- **White**: 题号（1-1182）
- **Black**: 关键着数 = 难度（需要非显然决策的步数）
- **FEN**: 起始局面
- **Moves**: 标准答案（含变体，用括号嵌套）

## Difficulty Mapping

| Black 值 | 星级 | 标签 |
|----------|------|------|
| 1 | ⭐ | 入门 |
| 2-3 | ⭐⭐ | 初级 |
| 4-5 | ⭐⭐⭐ | 中级 |
| 6-9 | ⭐⭐⭐⭐ | 高级 |
| 10-14 | ⭐⭐⭐⭐⭐ | 大师级 |

## 16 Themes

消除保护, 引离, 引入, 闪击, 开线, 腾挪, 穿透攻击, 拦截, 阻塞, 破坏兵型, 升变, 过渡, 逼和, 理论和, 长将/重复局面和, 战术组合

## Paired Puzzles

234 puzzles have a paired version — same FEN position, different side-to-move. They share the same `[White]` (puzzle number). Distinguish by `w` or `b` in the FEN's side-to-move field.

## Variations in Moves

760 puzzles (54%) contain parenthetical variations showing alternative lines:

```
1. Bxe5 Bxe5 (1... Qxb5 2. Bxg7+ Kxg7 3. Nxb5) 2. Rxf8+ ...
```

Nested parentheses indicate sub-variations.

## Parsing Example

```python
import re

with open('horse-puzzle.pgn', 'rb') as f:
    content = f.read().decode('gb2312').replace('\r\n', '\n')

puzzles = []
current = {}
for line in content.split('\n'):
    line = line.strip()
    if not line:
        continue
    m = re.match(r'\[(\w+)\s+"(.*?)"\]', line)
    if m:
        tag, value = m.group(1), m.group(2)
        if tag == 'Event':
            if current and 'event' in current:
                puzzles.append(current)
            current = {'event': value}
        else:
            current[tag.lower()] = value
    elif not line.startswith('['):
        current['moves'] = current.get('moves', '') + line + ' '

if current and 'event' in current:
    puzzles.append(current)
```
