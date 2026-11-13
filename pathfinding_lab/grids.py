"""
grids.py - grid worlds for the maze (BFS vs DFS) and the robot (greedy vs
A*): making them, searching them and drawing them.

A grid is a 2D numpy array of booleans: True is a wall or obstacle, False
is free. A state is a (row, column) cell. Moves go up, down, left or right
and cost 1 each.
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap

# Up, down, left, right.
MOVES = [(-1, 0), (1, 0), (0, -1), (0, 1)]


class GridProblem:
    """
    Get from start to goal on a grid. Follows the problem interface of
    pxlab.search.algorithms.
    """

    def __init__(self, grid, start, goal):
        """
        Inputs:
            grid: 2D boolean array, True for walls.
            start, goal: (row, column) cells.
        """
        self.grid = grid
        self.start = start
        self.goal = goal

    def is_goal(self, cell):
        """True at the goal cell."""
        return cell == self.goal

    def neighbours(self, cell):
        """
        The free cells one move away, each costing 1.

        Input:
            cell: (row, column).
        Returns:
            A list of ((row, column), 1).
        """
        rows, columns = self.grid.shape
        result = []
        for row_step, column_step in MOVES:
            row, column = cell[0] + row_step, cell[1] + column_step
            if 0 <= row < rows and 0 <= column < columns and not self.grid[row, column]:
                result.append(((row, column), 1))
        return result

    def heuristic(self, cell):
        """
        Manhattan distance to the goal: the moves needed if there were no
        walls. It never overestimates, so A* stays optimal.
        """
        return abs(cell[0] - self.goal[0]) + abs(cell[1] - self.goal[1])


def make_maze(size, seed, loops=0.08):
    """
    A random maze carved with depth-first backtracking, then a share of
    inner walls knocked out so there is more than one route (otherwise BFS
    and DFS would have to find the same, only path).

    Inputs:
        size: cells per side (made odd so walls and corridors alternate).
        seed: random seed, so the same seed gives the same maze.
        loops: share of the remaining inner walls removed.
    Returns:
        (grid, start, goal) with the start top-left and the goal bottom-right.
    """
    size = size if size % 2 == 1 else size + 1
    generator = np.random.default_rng(seed)
    grid = np.ones((size, size), dtype=bool)
    grid[1, 1] = False
    stack = [(1, 1)]
    while stack:
        row, column = stack[-1]
        unvisited = [
            (row + 2 * dr, column + 2 * dc)
            for dr, dc in MOVES
            if 0 < row + 2 * dr < size - 1 and 0 < column + 2 * dc < size - 1 and grid[row + 2 * dr, column + 2 * dc]
        ]
        if not unvisited:
            stack.pop()
            continue
        next_row, next_column = unvisited[generator.integers(len(unvisited))]
        grid[(row + next_row) // 2, (column + next_column) // 2] = False  # knock down the wall between
        grid[next_row, next_column] = False
        stack.append((next_row, next_column))

    # Inner walls that separate two corridors, horizontally or vertically.
    inner = [
        (row, column)
        for row in range(1, size - 1)
        for column in range(1, size - 1)
        if grid[row, column]
        and (
            (not grid[row - 1, column] and not grid[row + 1, column])
            or (not grid[row, column - 1] and not grid[row, column + 1])
        )
    ]
    for index in generator.permutation(len(inner))[: int(loops * len(inner))]:
        grid[inner[index]] = False
    return grid, (1, 1), (size - 2, size - 2)


def make_obstacle_grid(rows, columns, density, seed):
    """
    An open floor with randomly placed obstacles, for the robot.

    Inputs:
        rows, columns: grid size.
        density: share of cells that are obstacles.
        seed: random seed.
    Returns:
        (grid, start, goal) with the start top-left and the goal bottom-right.
    """
    generator = np.random.default_rng(seed)
    grid = generator.random((rows, columns)) < density
    start, goal = (0, 0), (rows - 1, columns - 1)
    grid[start] = grid[goal] = False
    return grid, start, goal


# Free, wall, explored, path.
GRID_COLOURS = ListedColormap(["#FFFFFF", "#2F3542", "#C9DDF2", "#E8590C"])


def plot_grid(axis, problem, result, title):
    """
    Draw a grid with the cells a search explored (light blue) and the path
    it found (orange).

    Inputs:
        axis: a matplotlib axis.
        problem: a GridProblem.
        result: a SearchResult from pxlab.search.
        title: the axis title.
    Returns:
        Nothing.
    """
    picture = problem.grid.astype(int)
    for cell in result.explored:
        picture[cell] = 2
    for cell in result.path:
        picture[cell] = 3
    axis.imshow(picture, cmap=GRID_COLOURS, vmin=0, vmax=3, interpolation="nearest")
    for cell, marker in [(problem.start, "o"), (problem.goal, "*")]:
        axis.plot(cell[1], cell[0], marker=marker, color="#2B8A3E", markersize=9)
    axis.set_title(title, fontsize=10)
    axis.set_xticks([])
    axis.set_yticks([])
    axis.grid(False)


def grid_figure(problem, results, titles):
    """
    Side-by-side grids, one per search result.

    Inputs:
        problem: a GridProblem.
        results: SearchResults on that problem.
        titles: one title per result.
    Returns:
        The matplotlib figure.
    """
    figure, axes = plt.subplots(1, len(results), figsize=(5 * len(results), 5.2))
    for axis, result, title in zip(np.atleast_1d(axes), results, titles):
        plot_grid(axis, problem, result, title)
    return figure
