"""
main.py - run every search comparison with one command:

    python main.py

It:
    1. maze (brief 1): BFS against DFS on random mazes of four sizes,
       comparing path length, explored cells and time,
    2. 8-puzzle (brief 2): A* with Manhattan distance, against A* with
       misplaced tiles and breadth-first search, on scrambles of growing
       difficulty,
    3. robot (brief 3): greedy best-first against A* on obstacle grids of
       three densities,
    4. city map (brief 17): BFS, uniform cost and A* on every route between
       ten Westminster landmarks,
    5. draws one example of each and writes docs/results.md.
Figures and tables go to outputs/search/.
"""

import matplotlib.pyplot as plt
import pandas as pd

from pathfinding_lab.city import LANDMARKS, CityMap, CityProblem, city_figure
from pathfinding_lab.grids import GridProblem, grid_figure, make_maze, make_obstacle_grid
from pathfinding_lab.puzzle import HEURISTICS, PuzzleProblem, scramble
from pathfinding_lab.report import FOLDER, results_sections
from pxlab.common import save_figure, save_table, set_plot_style, write_results_doc
from pxlab.search.algorithms import ALGORITHMS, a_star_search, breadth_first_search

MAZE_SIZES = [15, 25, 35, 45]
ROBOT_DENSITIES = [0.1, 0.2, 0.3]
PUZZLE_SCRAMBLES = [5, 10, 15, 20, 25, 30, 40]
SEEDS = range(10)


def result_row(result, **labels):
    """
    One table row for a search result.

    Inputs:
        result: a SearchResult.
        labels: extra columns, e.g. size=15.
    Returns:
        A dictionary.
    """
    return {
        **labels,
        "Algorithm": result.algorithm,
        "Path steps": result.steps,
        "Path cost": result.cost,
        "Explored": len(result.explored),
        "Largest frontier": result.max_frontier,
        "Milliseconds": result.seconds * 1000,
    }


def maze_study():
    """
    BFS against DFS on 10 mazes of each size.

    Returns:
        The per-run table.
    """
    rows = []
    for size in MAZE_SIZES:
        for seed in SEEDS:
            grid, start, goal = make_maze(size, seed)
            problem = GridProblem(grid, start, goal)
            for name in ["Breadth-first", "Depth-first"]:
                rows.append(result_row(ALGORITHMS[name](problem), Size=f"{size}x{size}", Seed=seed))
    runs = pd.DataFrame(rows)
    summary = runs.groupby(["Size", "Algorithm"], sort=False)[
        ["Path steps", "Explored", "Largest frontier", "Milliseconds"]
    ].mean()
    save_table(summary.round(2), f"{FOLDER}/maze_benchmark.csv", index=True)
    print(summary.round(1).to_string())

    grid, start, goal = make_maze(35, 3)
    problem = GridProblem(grid, start, goal)
    results = [breadth_first_search(problem), ALGORITHMS["Depth-first"](problem)]
    titles = [f"{r.algorithm}: {r.steps} steps, {len(r.explored)} cells explored" for r in results]
    save_figure(grid_figure(problem, results, titles), f"{FOLDER}/maze_example.png")
    return runs


def puzzle_study():
    """
    A* (two heuristics) against breadth-first on 10 scrambles per length.

    Returns:
        The per-run table.
    """
    rows = []
    for moves in PUZZLE_SCRAMBLES:
        for seed in SEEDS:
            board = scramble(moves, seed)
            optimal = None
            for heuristic_name, heuristic in HEURISTICS.items():
                result = a_star_search(PuzzleProblem(board, heuristic))
                optimal = result.steps
                row = result_row(result, Scramble=moves, Seed=seed)
                row["Algorithm"] = f"A* ({heuristic_name.lower()})"
                rows.append(row)
            rows.append(result_row(breadth_first_search(PuzzleProblem(board)), Scramble=moves, Seed=seed))
            for row in rows[-3:]:
                row["Optimal moves"] = optimal
    runs = pd.DataFrame(rows)
    summary = runs.groupby(["Optimal moves", "Algorithm"])[["Explored", "Largest frontier", "Milliseconds"]].mean()
    summary["Boards"] = runs.groupby(["Optimal moves", "Algorithm"]).size()
    save_table(summary.round(1), f"{FOLDER}/puzzle_benchmark.csv", index=True)
    print(summary.round(1).to_string())

    figure, axis = plt.subplots(figsize=(8, 4.6))
    for algorithm, part in runs.groupby("Algorithm"):
        means = part.groupby("Optimal moves")["Explored"].mean()
        axis.plot(means.index, means.values, marker="o", label=algorithm)
    axis.set_yscale("log")
    axis.set_xlabel("Moves in the shortest solution")
    axis.set_ylabel("Boards explored (log scale)")
    axis.set_title("8-puzzle: boards explored before finding the solution")
    axis.legend()
    save_figure(figure, f"{FOLDER}/puzzle_explored.png")
    return runs


def robot_study():
    """
    Greedy best-first against A* on 40x40 grids at three obstacle densities.

    Returns:
        The per-run table.
    """
    rows = []
    worst = None
    for density in ROBOT_DENSITIES:
        for seed in range(20):
            grid, start, goal = make_obstacle_grid(40, 40, density, seed)
            problem = GridProblem(grid, start, goal)
            greedy, star = ALGORITHMS["Greedy best-first"](problem), a_star_search(problem)
            if not star.found:
                continue  # obstacles cut the goal off; neither search can help
            extra = greedy.steps - star.steps
            rows.append(result_row(greedy, Density=density, Seed=seed, **{"Extra steps": extra}))
            rows.append(result_row(star, Density=density, Seed=seed, **{"Extra steps": 0}))
            if worst is None or extra > worst[0]:
                worst = (extra, problem, greedy, star)
    runs = pd.DataFrame(rows)
    grouped = runs.groupby(["Density", "Algorithm"])
    summary = grouped[["Path steps", "Explored", "Milliseconds"]].mean()
    summary["Grids"] = grouped.size()
    summary["Grids with a longer path"] = grouped["Extra steps"].apply(lambda extra: int((extra > 0).sum()))
    save_table(summary.round(2), f"{FOLDER}/robot_benchmark.csv", index=True)
    print(summary.round(1).to_string())

    _, problem, greedy, star = worst
    titles = [f"{r.algorithm}: {r.steps} steps, {len(r.explored)} cells explored" for r in [greedy, star]]
    save_figure(grid_figure(problem, [greedy, star], titles), f"{FOLDER}/robot_example.png")
    return runs


def city_study():
    """
    BFS, uniform cost and A* on every route between two landmarks.

    Returns:
        The per-run table.
    """
    city = CityMap()
    nodes = {name: city.nearest_node(point) for name, point in LANDMARKS.items()}
    names = list(LANDMARKS)
    rows = []
    for index, origin in enumerate(names):
        for destination in names[index + 1 :]:
            problem = CityProblem(city, nodes[origin], nodes[destination])
            for name in ["Breadth-first", "Uniform cost", "A*"]:
                rows.append(result_row(ALGORITHMS[name](problem), From=origin, To=destination))
    runs = pd.DataFrame(rows).rename(columns={"Path cost": "Metres", "Path steps": "Street segments"})
    shortest = runs[runs["Algorithm"] == "Uniform cost"].set_index(["From", "To"])["Metres"]
    runs["Metres over shortest"] = runs["Metres"] - runs.set_index(["From", "To"]).index.map(shortest)
    summary = runs.groupby("Algorithm", sort=False)[
        ["Metres", "Metres over shortest", "Street segments", "Explored", "Milliseconds"]
    ].mean()
    summary["Routes"] = runs.groupby("Algorithm", sort=False).size()
    save_table(summary.round(1), f"{FOLDER}/city_benchmark.csv", index=True)
    print(summary.round(1).to_string())

    problem = CityProblem(city, nodes["Piccadilly Circus"], nodes["Big Ben"])
    results = [ALGORITHMS[name](problem) for name in ["Breadth-first", "Uniform cost", "A*"]]
    titles = [f"{r.algorithm}: {r.cost:,.0f} m, {len(r.explored)} nodes explored" for r in results]
    save_figure(city_figure(city, results, titles), f"{FOLDER}/city_example.png")
    return runs


def main():
    """
    Every study, then the results document.

    Returns:
        Nothing.
    """
    set_plot_style()
    print("Maze: breadth-first against depth-first")
    maze_study()
    print("8-puzzle: A* against breadth-first")
    puzzle_study()
    print("Robot: greedy best-first against A*")
    robot_study()
    print("City map: breadth-first, uniform cost and A*")
    city_study()
    write_results_doc(
        "Results",
        "Produced by `python main.py`. Times are from one laptop run in plain Python and only comparable "
        "with each other; the counts of explored states don't depend on the machine.",
        results_sections(),
    )
    print("  Done. Run: streamlit run app.py")


if __name__ == "__main__":
    main()
