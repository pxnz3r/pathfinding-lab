### What this is

Five search algorithms on four problems. Each problem is a set of **states** (a cell, a board, a street corner), **moves** between them with a cost, a **start** and a **goal**. One search engine solves all four, so the algorithms are compared on equal terms.

| Problem | Compared | The question |
| --- | --- | --- |
| Maze | breadth-first, depth-first | path length, explored cells and time |
| 8-puzzle | A* (Manhattan distance), A* (misplaced tiles), breadth-first | how much a good estimate saves |
| Robot on an obstacle grid | greedy best-first, A* | speed against path quality |
| Walking in Westminster, London | breadth-first, uniform cost, A* | shortest route on a real street map |

### The algorithms

- **Breadth-first**: explores everything 1 step away, then 2 steps, and so on. Finds the path with the fewest steps.
- **Depth-first**: follows one branch to its end, then backs up. Little memory, no guarantee of a short path.
- **Uniform cost**: explores the cheapest path so far. Finds the cheapest path when moves cost different amounts (metres of street).
- **Greedy best-first**: goes wherever an estimate says is closest to the goal. Fast, but the path can be poor.
- **A***: goes where cost so far plus estimated cost left is lowest. If the estimate never overestimates, the path is the cheapest, and the search is much smaller than uniform cost's.

### What was found

- **Maze**: depth-first explores about as many cells as breadth-first, but its path is 1.4 to 3.1 times longer, worse in bigger mazes.
- **8-puzzle**: for boards 20 moves from solved, breadth-first explores about 48,000 boards; A* with misplaced tiles about 3,400; A* with Manhattan distance about 250.
- **Robot**: greedy explores about half as many cells as A*, but returned a longer path on every grid tested: 8% longer on average with 10% obstacles, 27% with 30%.
- **City map**: A* finds the same shortest walks as uniform cost while exploring 3.4 times fewer street points. Breadth-first's fewest-segment routes are 15% longer to walk.

Every tab runs the searches live: change the maze, scramble, obstacles or route and compare.

Code and every figure: [github.com/pxnz3r/pathfinding-lab](https://github.com/pxnz3r/pathfinding-lab).
