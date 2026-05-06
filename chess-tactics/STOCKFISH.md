# Stockfish Integration

## Location

```
/opt/homebrew/bin/stockfish
```

## UCI Command Templates

### Analyze a position (get best move + evaluation)

```bash
echo "position fen <FEN>
go depth 20" | /opt/homebrew/bin/stockfish 2>/dev/null | grep -E "^(bestmove|info depth 20)"
```

### Analyze after specific moves

```bash
echo "position fen <FEN> moves <move1> <move2> ...
go depth 20" | /opt/homebrew/bin/stockfish 2>/dev/null | grep -E "^(bestmove|info depth 20)"
```

### Evaluate a specific user move (check if it's good)

1. Get evaluation of position BEFORE the move
2. Apply the move, get evaluation AFTER
3. Compare: if eval drops significantly, the move is suboptimal

```bash
# Before move
echo "position fen <FEN>
go depth 20" | /opt/homebrew/bin/stockfish 2>/dev/null | grep "info depth 20"

# After user's move
echo "position fen <FEN> moves <user_move>
go depth 20" | /opt/homebrew/bin/stockfish 2>/dev/null | grep "info depth 20"
```

## Move Format

Stockfish uses UCI long algebraic notation:
- `e2e4` (not `e4`)
- `e7e8q` (promotion)
- `e1g1` (castling kingside)

To convert from standard algebraic (PGN) to UCI, use python-chess:

```python
import chess
board = chess.Board(fen)
move = board.parse_san("Rxh7+")  # Parse standard algebraic
uci = move.uci()  # Get UCI format: "h4h7"
```

## Interpreting Output

Key fields in `info depth 20` line:
- `score cp <N>`: centipawn evaluation (positive = white advantage)
- `score mate <N>`: forced mate in N moves
- `pv <moves>`: principal variation (best line)

## Depth

Always use depth 20. Sufficient for tactical puzzles up to 14 moves.

## Full Analysis Script

For convenience, use [scripts/analyze.py](scripts/analyze.py) which handles:
- FEN input
- Move validation
- Evaluation comparison
- Output formatting
