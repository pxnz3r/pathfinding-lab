# Methodology

## Question

How do uninformed searches (breadth-first, depth-first, uniform cost) and informed searches (greedy best-first, A*) differ in the paths they find and the work they do, on problems of different shapes?

## One engine, four problems

`pxlab/search/algorithms.py` implements the five searches once. A problem only has to say where it starts, when it has reached the goal, which states are one move away and at what cost, and (for the informed searches) an estimate of the cost left. Each search returns the path, its cost, every state it expanded in order, the largest its frontier grew and the time taken.

All five are graph searches: a state is expanded at most once. Breadth-first and depth-first stop when they expand the goal. Uniform cost, greedy and A* share one priority-queue loop and differ only in the priority: cost so far, estimate left, or their sum. A* breaks ties between equal sums by the smaller estimate, so on open ground it follows one route instead of fanning out across all equally good ones.

| Problem | States | Moves and cost | Estimate (heuristic) |
| --- | --- | --- | --- |
| Maze | free cells of a grid | up, down, left, right; 1 each | not used |
| 8-puzzle | the 9! / 2 = 181,440 solvable boards | slide a tile into the gap; 1 each | Manhattan distance, or tiles out of place |
| Robot | free cells of an obstacle grid | up, down, left, right; 1 each | Manhattan distance |
| City map | 3,257 street points in Westminster | walk a street segment; its length in metres | straight-line distance |

Every estimate here never overestimates (a tile needs at least its Manhattan distance in moves; no walk is shorter than the straight line), so A* returns optimal paths.

## Setups

1. **Maze**: grids of 15, 25, 35 and 45 cells per side, carved with randomised depth-first backtracking from fixed seeds, then 8% of the inner walls removed so several routes exist. Start top-left, goal bottom-right. 10 mazes per size.
2. **8-puzzle**: boards made by 5 to 40 random slides from the solved board (never undoing the last slide), 10 per length, so every board is solvable. Results are grouped by the length of the shortest solution, which A* finds.
3. **Robot**: 40x40 grids with 10%, 20% and 30% of cells blocked at random, 20 per density. Grids where the obstacles cut off the goal are skipped (both searches fail on them).
4. **City map**: walkable streets (roads, pedestrian streets, service roads; not footpaths through parks) from an OpenStreetMap download of about 1.1 km by 1.5 km around Whitehall, kept as the largest connected network and walked in both directions. Ten landmarks are snapped to their nearest street point; all 45 pairs are routed.

Counts of explored states don't depend on the machine; times are from one run in plain Python and only comparable with each other.

## Limits

- **Times are small and noisy.** Most searches take a few milliseconds, where Python overhead matters as much as the algorithm. The explored counts are the fairer comparison.
- **Depth-first depends on move order.** It tries up, down, left, right in that order; another order gives different paths.
- **One heuristic per problem.** The robot and city searches use the simplest admissible estimates; better ones (precomputed landmark distances, for example) would shrink A* further.
- **A small map.** 3,257 points is enough to show the differences; on a whole city, uniform cost and breadth-first explore far more, and the gap to A* widens.
- **Walking only.** One-way streets and turn restrictions are ignored.
