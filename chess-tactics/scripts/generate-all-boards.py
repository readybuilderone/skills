#!/usr/bin/env python3
"""Pre-generate board PNG images for all puzzles."""

import os
import re
import subprocess
import sys
import tempfile

import chess
import chess.svg

PGN_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "horse-puzzle.pgn")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "boards")


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


def render_board(fen, output_path, size=400):
    board = chess.Board(fen)
    svg = chess.svg.board(board, size=size)

    with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as f:
        f.write(svg.encode())
        svg_path = f.name

    try:
        subprocess.run(
            ["rsvg-convert", svg_path, "-o", output_path],
            check=True,
            capture_output=True,
        )
    finally:
        os.unlink(svg_path)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    puzzles = load_puzzles()
    total = len(puzzles)
    print(f"Generating boards for {total} puzzles...")

    for i, puzzle in enumerate(puzzles):
        fen = puzzle.get("fen", "")
        pid = puzzle.get("white", "unknown")
        side = fen.split(" ")[1] if " " in fen else "w"

        filename = f"{pid}_{side}.png"
        output_path = os.path.join(OUTPUT_DIR, filename)

        if os.path.exists(output_path):
            continue

        try:
            render_board(fen, output_path)
        except Exception as e:
            print(f"  ERROR #{pid}_{side}: {e}", file=sys.stderr)
            continue

        if (i + 1) % 100 == 0:
            print(f"  {i + 1}/{total} done")

    print(f"Done. Images saved to {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
