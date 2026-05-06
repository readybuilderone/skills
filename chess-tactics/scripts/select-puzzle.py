#!/usr/bin/env python3
"""Select a puzzle from horse-puzzle.pgn based on criteria."""

import json
import os
import random
import re
import sys

PGN_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "horse-puzzle.pgn")

DIFFICULTY_MAP = {
    "入门": [1],
    "初级": [2, 3],
    "中级": [4, 5],
    "高级": [6, 7, 8, 9],
    "大师级": [10, 11, 12, 13, 14],
}

THEMES = [
    "消除保护", "引离", "引入", "闪击", "开线", "腾挪",
    "穿透攻击", "拦截", "阻塞", "破坏兵型", "升变",
    "过渡", "逼和", "理论和", "长将/重复局面和", "战术组合",
]


def load_puzzles():
    pgn_path = os.path.normpath(PGN_PATH)
    with open(pgn_path, "rb") as f:
        content = f.read().decode("gb2312").replace("\r\n", "\n")

    puzzles = []
    current = {}
    for line in content.split("\n"):
        line = line.strip()
        if not line:
            continue
        m = re.match(r'\[(\w+)\s+"(.*?)"\]', line)
        if m:
            tag, value = m.group(1), m.group(2)
            if tag == "Event":
                if current and "event" in current:
                    puzzles.append(current)
                current = {"event": value}
            else:
                current[tag.lower()] = value
        elif not line.startswith("["):
            current["moves"] = current.get("moves", "") + line + " "

    if current and "event" in current:
        puzzles.append(current)

    return puzzles


def find_paired(puzzles, puzzle):
    """Find the paired puzzle (same White number, different side-to-move)."""
    pid = puzzle.get("white")
    side = puzzle.get("fen", "").split(" ")[1] if " " in puzzle.get("fen", "") else None
    for p in puzzles:
        if p.get("white") == pid and p is not puzzle:
            p_side = p.get("fen", "").split(" ")[1] if " " in p.get("fen", "") else None
            if p_side != side:
                return p
    return None


def select(puzzles, puzzle_id=None, theme=None, difficulty=None):
    """Select a puzzle matching criteria."""
    candidates = puzzles

    if puzzle_id:
        candidates = [p for p in candidates if p.get("white") == str(puzzle_id)]
        if not candidates:
            return None
        # If multiple (paired), return first (white-to-move) by default
        return candidates[0]

    if theme:
        candidates = [p for p in candidates if p.get("event") == theme]

    if difficulty:
        levels = DIFFICULTY_MAP.get(difficulty, [])
        if levels:
            candidates = [p for p in candidates if p.get("black", "0").isdigit() and int(p["black"]) in levels]

    if not candidates:
        return None

    return random.choice(candidates)


def format_puzzle(puzzle):
    """Format puzzle for JSON output."""
    fen = puzzle.get("fen", "")
    side = fen.split(" ")[1] if " " in fen else "w"
    black_val = puzzle.get("black", "?")

    try:
        diff_num = int(black_val)
    except ValueError:
        diff_num = 0

    if diff_num == 1:
        diff_label = "入门"
    elif diff_num <= 3:
        diff_label = "初级"
    elif diff_num <= 5:
        diff_label = "中级"
    elif diff_num <= 9:
        diff_label = "高级"
    else:
        diff_label = "大师级"

    return {
        "puzzle_id": puzzle.get("white", "?"),
        "theme": puzzle.get("event", "?"),
        "difficulty": diff_num,
        "difficulty_label": diff_label,
        "side_to_move": "白" if side == "w" else "黑",
        "fen": fen,
        "moves": puzzle.get("moves", "").strip(),
        "result": puzzle.get("result", ""),
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--id", type=int, help="Puzzle number")
    parser.add_argument("--theme", help="Tactical theme")
    parser.add_argument("--difficulty", help="Difficulty: 入门/初级/中级/高级/大师级")
    parser.add_argument("--paired", type=int, help="Find paired puzzle for this ID")
    parser.add_argument("--side", choices=["w", "b"], help="Side to move filter")
    args = parser.parse_args()

    puzzles = load_puzzles()

    if args.paired:
        candidates = [p for p in puzzles if p.get("white") == str(args.paired)]
        if len(candidates) > 1:
            # Return the one with opposite side
            for p in candidates:
                side = p.get("fen", "").split(" ")[1] if " " in p.get("fen", "") else None
                if args.side and side == args.side:
                    print(json.dumps(format_puzzle(p), ensure_ascii=False, indent=2))
                    sys.exit(0)
            # Default: return second one
            print(json.dumps(format_puzzle(candidates[1]), ensure_ascii=False, indent=2))
        else:
            print(json.dumps({"error": "No paired puzzle found"}, ensure_ascii=False))
        sys.exit(0)

    puzzle = select(puzzles, puzzle_id=args.id, theme=args.theme, difficulty=args.difficulty)

    if puzzle:
        result = format_puzzle(puzzle)
        # Check for paired puzzle
        paired = find_paired(puzzles, puzzle)
        result["has_paired"] = paired is not None
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(json.dumps({"error": "No matching puzzle found"}, ensure_ascii=False))
