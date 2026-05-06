#!/usr/bin/env python3
"""Render a chess position from FEN to PNG image."""

import sys
import subprocess
import tempfile
import os

import chess
import chess.svg


def render(fen: str, output_path: str, size: int = 400, last_move: str = None):
    board = chess.Board(fen)

    kwargs = {"size": size}
    if last_move:
        move = chess.Move.from_uci(last_move)
        kwargs["lastmove"] = move

    svg = chess.svg.board(board, **kwargs)

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

    print(output_path)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: render-board.py <FEN> <output.png> [size] [last_move_uci]")
        sys.exit(1)

    fen = sys.argv[1]
    output = sys.argv[2]
    size = int(sys.argv[3]) if len(sys.argv) > 3 else 400
    last_move = sys.argv[4] if len(sys.argv) > 4 else None

    render(fen, output, size, last_move)
