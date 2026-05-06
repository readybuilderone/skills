#!/usr/bin/env python3
"""Analyze chess positions using Stockfish UCI protocol."""

import subprocess
import sys
import time
import chess

STOCKFISH = "/opt/homebrew/bin/stockfish"
DEPTH = 20


def run_stockfish(fen: str, moves: list[str] = None) -> str:
    proc = subprocess.Popen(
        [STOCKFISH],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    commands = "uci\nisready\n"
    cmd = f"position fen {fen}"
    if moves:
        cmd += " moves " + " ".join(moves)
    commands += cmd + f"\ngo depth {DEPTH}\n"

    proc.stdin.write(commands)
    proc.stdin.flush()

    lines = []
    while True:
        line = proc.stdout.readline()
        if not line:
            break
        lines.append(line.strip())
        if line.startswith("bestmove"):
            break

    proc.stdin.write("quit\n")
    proc.stdin.flush()
    proc.terminate()

    return "\n".join(lines)


def parse_output(output: str) -> dict:
    result = {"bestmove": None, "score": None, "pv": None, "mate": None}

    last_info = None
    for line in output.split("\n"):
        if line.startswith("bestmove"):
            parts = line.split()
            result["bestmove"] = parts[1] if len(parts) > 1 else None
        if f"info depth {DEPTH}" in line and "seldepth" in line:
            last_info = line
        elif "info depth" in line and "seldepth" in line and "score" in line:
            last_info = line

    if last_info:
        parts = last_info.split()
        if "score" in parts:
            idx = parts.index("score")
            if parts[idx + 1] == "cp":
                result["score"] = int(parts[idx + 2])
            elif parts[idx + 1] == "mate":
                result["mate"] = int(parts[idx + 2])
        if "pv" in parts:
            pv_idx = parts.index("pv")
            result["pv"] = parts[pv_idx + 1:]

    return result


def analyze_position(fen: str, moves: list[str] = None) -> dict:
    output = run_stockfish(fen, moves)
    return parse_output(output)


def evaluate_move(fen: str, move_san: str) -> dict:
    """Evaluate whether a user's move is good."""
    board = chess.Board(fen)

    try:
        move = board.parse_san(move_san)
    except (chess.IllegalMoveError, chess.InvalidMoveError, chess.AmbiguousMoveError) as e:
        return {"error": f"Invalid move: {move_san} ({e})"}

    move_uci = move.uci()

    before = analyze_position(fen)
    after = analyze_position(fen, [move_uci])

    # Flip after score (opponent's perspective)
    after_score = -after["score"] if after["score"] is not None else None
    after_mate = -after["mate"] if after["mate"] is not None else None

    is_best = before["bestmove"] == move_uci

    best_san = None
    if before["bestmove"]:
        try:
            best_san = board.san(chess.Move.from_uci(before["bestmove"]))
        except Exception:
            best_san = before["bestmove"]

    return {
        "move_uci": move_uci,
        "move_san": move_san,
        "is_best": is_best,
        "best_move_uci": before["bestmove"],
        "best_move_san": best_san,
        "score_before": before["score"],
        "mate_before": before["mate"],
        "score_after": after_score,
        "mate_after": after_mate,
        "pv": before["pv"],
    }


if __name__ == "__main__":
    import json

    if len(sys.argv) < 2:
        print("Usage:")
        print("  analyze.py <FEN>                    # Best move analysis")
        print('  analyze.py <FEN> --move "Rxh7+"     # Evaluate a specific move')
        sys.exit(1)

    fen = sys.argv[1]

    if "--move" in sys.argv:
        move_idx = sys.argv.index("--move")
        move_san = sys.argv[move_idx + 1]
        result = evaluate_move(fen, move_san)
    else:
        result = analyze_position(fen)

    print(json.dumps(result, indent=2, ensure_ascii=False))
