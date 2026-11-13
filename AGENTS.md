# pathfinding-lab

AI Lab coursework: Search algorithms compared on mazes, the 8-puzzle, robot grids and a real city map: BFS, DFS, UCS, greedy best-first and A*

## Layout

- `pathfinding_lab/` the problems: `grids.py` (maze, robot), `puzzle.py` (8-puzzle), `city.py` (street map), `report.py`
- `pxlab/` vendored copy of the shared engine (see `pxlab/VERSION`). Don't edit it here; it is replaced on the next sync.
- `main.py` runs the full study and rewrites `docs/results.md`; `app.py` is the Streamlit demo; `app_overview.md` the demo's Overview text
- `outputs/` figures and CSV tables (committed)
- `maps/westminster.json` the street graph, built once by `scripts/build_city_map.py` from OpenStreetMap (ODbL) and committed
- `docs/` methodology, results, deploy

## Commands

- Full study: `uv run python main.py`
- Demo: `uv run streamlit run app.py`
- Lint: `uv run ruff check . && uv run ruff format --check .`

## Conventions

- Beginner-student style on purpose: plain functions, docstrings on every function, comments explaining the AI concepts.
- Every problem is a small class with `start`, `is_goal`, `neighbours` and `heuristic`, so `pxlab.search` runs any algorithm on it. Random mazes, grids and scrambles take a seed.
- After changing the study, re-run `main.py` and refresh the README results and `app_overview.md`.
