"""
statistics.py - turns the benchmark runs into evidence.

    Paired comparisons: two algorithms run on the very same instances, so
        each instance is a pair. The sign test asks: if neither algorithm
        were really better, how likely is it that one wins this many pairs
        by luck (like a fair coin landing heads that often)?
    Effective branching factor: the b* for which a tree of the solution's
        depth d with b* children per node would hold the number of nodes
        explored, N + 1 = 1 + b* + b*^2 + ... + b*^d. A better heuristic
        gives a b* closer to 1; it hardly changes with the puzzle's depth,
        so heuristics can be compared at any difficulty.
"""

from math import comb

import pandas as pd

SIGNIFICANCE_LEVEL = 0.05


def sign_test(wins, losses):
    """
    Two-sided exact sign test (ties are left out).

    Inputs:
        wins, losses: pairs won by each side.
    Returns:
        The p-value.
    """
    total = wins + losses
    if total == 0:
        return 1.0
    smaller = min(wins, losses)
    tail = sum(comb(total, count) for count in range(smaller + 1)) / 2**total
    return min(1.0, 2 * tail)


def paired_comparison(study, runs, keys, first, second, column="Explored"):
    """
    Compare two algorithms instance by instance.

    Inputs:
        study: the study's name for the table.
        runs: the per-run table.
        keys: the columns that identify an instance (e.g. Size and Seed).
        first, second: the two algorithm names.
        column: what is compared (smaller is better).
    Returns:
        A dictionary (one table row).
    """
    table = runs.pivot_table(index=keys, columns="Algorithm", values=column)[[first, second]].dropna()
    wins = int((table[first] < table[second]).sum())
    losses = int((table[first] > table[second]).sum())
    p_value = sign_test(wins, losses)
    return {
        "Study": study,
        "Compared": f"{first} vs {second}",
        "On": column,
        "Instances": len(table),
        "Median, first": float(table[first].median()),
        "Median, second": float(table[second].median()),
        "First is smaller on": wins,
        "Second is smaller on": losses,
        "p-value (sign test)": round(p_value, 6),
        "Verdict": "real difference" if p_value < SIGNIFICANCE_LEVEL else "could be chance",
    }


def effective_branching_factor(explored, depth):
    """
    Solve N + 1 = 1 + b + b^2 + ... + b^depth for b by bisection.

    Inputs:
        explored: nodes explored (N).
        depth: moves in the solution (d).
    Returns:
        b*, or None when depth is 0.
    """
    if depth == 0:
        return None
    low, high = 1.0, float(explored) + 1
    for _ in range(100):
        middle = (low + high) / 2
        total = sum(middle**level for level in range(depth + 1))
        if total < explored + 1:
            low = middle
        else:
            high = middle
    return (low + high) / 2


def branching_table(puzzle_runs):
    """
    Average effective branching factor of each 8-puzzle search by solution
    depth.

    Input:
        puzzle_runs: the per-run table of the 8-puzzle study.
    Returns:
        A wide DataFrame: Optimal moves, then one column per algorithm.
    """
    runs = puzzle_runs[puzzle_runs["Optimal moves"] > 0].copy()
    runs["Branching factor"] = [
        effective_branching_factor(explored, depth) for explored, depth in zip(runs["Explored"], runs["Optimal moves"])
    ]
    table = runs.pivot_table(index="Optimal moves", columns="Algorithm", values="Branching factor", aggfunc="mean")
    return table.round(3).reset_index()


def comparisons_table(maze, puzzle, robot, city):
    """
    Every paired comparison the studies support.

    Inputs:
        maze, puzzle, robot, city: the per-run tables.
    Returns:
        A DataFrame, one row per comparison.
    """
    rows = [
        paired_comparison("Maze", maze, ["Size", "Seed"], "Breadth-first", "Depth-first"),
        paired_comparison("Maze", maze, ["Size", "Seed"], "Breadth-first", "Depth-first", "Path steps"),
        paired_comparison("8-puzzle", puzzle, ["Scramble", "Seed"], "A* (manhattan distance)", "A* (misplaced tiles)"),
        paired_comparison("8-puzzle", puzzle, ["Scramble", "Seed"], "A* (misplaced tiles)", "Breadth-first"),
        paired_comparison("Robot", robot, ["Density", "Seed"], "Greedy best-first", "A*"),
        paired_comparison("Robot", robot, ["Density", "Seed"], "A*", "Greedy best-first", "Path steps"),
        paired_comparison("City map", city, ["From", "To"], "A*", "Uniform cost"),
        paired_comparison("City map", city, ["From", "To"], "Uniform cost", "Breadth-first", "Metres"),
    ]
    return pd.DataFrame(rows)
