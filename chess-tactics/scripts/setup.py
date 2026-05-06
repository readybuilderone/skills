#!/usr/bin/env python3
"""Check and install dependencies for chess-tactics skill."""

import os
import subprocess
import shutil
import sys

PROJECT_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
BOARDS_DIR = os.path.join(PROJECT_ROOT, "boards")
PGN_PATH = os.path.join(PROJECT_ROOT, "horse-puzzle.pgn")


def check_command(name):
    return shutil.which(name) is not None


def check_python_package(name):
    try:
        __import__(name)
        return True
    except ImportError:
        return False


def run(cmd, desc):
    print(f"  Installing: {desc}...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ERROR: {result.stderr.strip()}", file=sys.stderr)
        return False
    return True


def main():
    print("=== Chess Tactics Skill Setup ===\n")
    all_ok = True

    # 1. Check stockfish
    print("[1/4] Stockfish")
    if check_command("stockfish"):
        print("  ✓ stockfish found")
    else:
        print("  ✗ stockfish not found")
        if not run(["brew", "install", "stockfish"], "stockfish via Homebrew"):
            all_ok = False

    # 2. Check rsvg-convert
    print("[2/4] rsvg-convert (librsvg)")
    if check_command("rsvg-convert"):
        print("  ✓ rsvg-convert found")
    else:
        print("  ✗ rsvg-convert not found")
        if not run(["brew", "install", "librsvg"], "librsvg via Homebrew"):
            all_ok = False

    # 3. Check python-chess
    print("[3/4] python-chess")
    if check_python_package("chess"):
        print("  ✓ python-chess found")
    else:
        print("  ✗ python-chess not found")
        if not run([sys.executable, "-m", "pip", "install", "python-chess"], "python-chess via pip"):
            all_ok = False

    # 4. Check PGN + boards
    print("[4/4] Puzzle data & board images")
    if not os.path.exists(PGN_PATH):
        print(f"  ✗ horse-puzzle.pgn not found at {PGN_PATH}")
        print("  Please place horse-puzzle.pgn in the project root.")
        all_ok = False
    else:
        print("  ✓ horse-puzzle.pgn found")

        # Count expected boards
        existing = len([f for f in os.listdir(BOARDS_DIR) if f.endswith(".png")]) if os.path.exists(BOARDS_DIR) else 0

        if existing >= 1400:
            print(f"  ✓ board images found ({existing} files)")
        else:
            if existing > 0:
                print(f"  △ only {existing} board images found, regenerating missing ones...")
            else:
                print("  ✗ board images not found, generating...")

            generate_script = os.path.join(os.path.dirname(__file__), "generate-all-boards.py")
            result = subprocess.run(
                [sys.executable, generate_script],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                new_count = len([f for f in os.listdir(BOARDS_DIR) if f.endswith(".png")])
                print(f"  ✓ board images generated ({new_count} files)")
            else:
                print(f"  ERROR: {result.stderr.strip()}", file=sys.stderr)
                all_ok = False

    print()
    if all_ok:
        print("✓ All dependencies satisfied. Ready to use /chess-tactics!")
    else:
        print("✗ Some dependencies could not be installed. See errors above.")

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
