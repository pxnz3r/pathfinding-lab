"""
puzzle.py - the 8-puzzle: eight numbered tiles and a gap on a 3x3 board.
Slide tiles into the gap until the board reads 1 to 8 with the gap last.

A state is a tuple of 9 numbers read row by row, 0 for the gap. A move
slides a neighbouring tile into the gap and costs 1. Half of all
arrangements can't reach the goal, so scrambles are made by sliding from
the goal, which always gives a solvable board.
"""

import numpy as np

GOAL = (1, 2, 3, 4, 5, 6, 7, 8, 0)


def manhattan(state):
    """
    Sum over tiles of how many rows plus columns each is from its place.
    Every move shifts one tile by one square, so this never overestimates.

    Input:
        state: a board tuple.
    Returns:
        The distance.
    """
    total = 0
    for index, tile in enumerate(state):
        if tile:
            target = tile - 1
            total += abs(index // 3 - target // 3) + abs(index % 3 - target % 3)
    return total


def misplaced(state):
    """
    Number of tiles out of place. Also never overestimates, but it is a
    weaker hint than Manhattan distance (always less or equal).

    Input:
        state: a board tuple.
    Returns:
        The count.
    """
    return sum(1 for index, tile in enumerate(state) if tile and tile != GOAL[index])


HEURISTICS = {"Manhattan distance": manhattan, "Misplaced tiles": misplaced}


class PuzzleProblem:
    """
    Solve one 8-puzzle board. Follows the problem interface of
    pxlab.search.algorithms.
    """

    def __init__(self, start, heuristic=manhattan):
        """
        Inputs:
            start: the scrambled board tuple.
            heuristic: a function board -> estimated moves left.
        """
        self.start = tuple(start)
        self.heuristic = heuristic

    def is_goal(self, state):
        """True when the board is solved."""
        return state == GOAL

    def neighbours(self, state):
        """
        Every board one slide away, each costing 1.

        Input:
            state: a board tuple.
        Returns:
            A list of (board, 1).
        """
        gap = state.index(0)
        row, column = divmod(gap, 3)
        result = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            r, c = row + dr, column + dc
            if 0 <= r < 3 and 0 <= c < 3:
                board = list(state)
                board[gap], board[r * 3 + c] = board[r * 3 + c], 0
                result.append((tuple(board), 1))
        return result


def scramble(moves, seed):
    """
    A solvable board made by sliding random tiles from the goal, never
    undoing the previous slide.

    Inputs:
        moves: how many slides.
        seed: random seed.
    Returns:
        A board tuple.
    """
    generator = np.random.default_rng(seed)
    problem = PuzzleProblem(GOAL)
    state, previous = GOAL, None
    for _ in range(moves):
        options = [board for board, _ in problem.neighbours(state) if board != previous]
        previous, state = state, options[generator.integers(len(options))]
    return state


def board_text(state):
    """
    The board as three lines of text, with a dot for the gap.

    Input:
        state: a board tuple.
    Returns:
        A string.
    """
    cells = [str(tile) if tile else "·" for tile in state]
    return "\n".join(" ".join(cells[row * 3 : row * 3 + 3]) for row in range(3))
