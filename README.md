# Minesweeper

A pygame Minesweeper with a no-guessing generator and a deterministic auto-solver.

Python 3.11+ recommended.

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Run

From the repo root:

```bash
.venv/bin/python main.py
```

Classic sizes if `--mines` is omitted: beginner 9×9/10, intermediate 16×16/40, expert 16×30/99. Other sizes use expert density.

```bash
.venv/bin/python main.py --rows 9 --cols 9
.venv/bin/python main.py --rows 10 --cols 10 --mines 15
.venv/bin/python main.py --debug
```

The highlighted square is a first click that solves the board without guessing. **R** or the face button generates a new board. The solve button runs the auto-solver. On win the face becomes `win.png`.

## Tests

```bash
SDL_VIDEODRIVER=dummy .venv/bin/python -m pytest src/tests -q
```
