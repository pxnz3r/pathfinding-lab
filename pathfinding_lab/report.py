"""
report.py - which saved tables and figures make up the results. The app's
Results tab and docs/results.md both read this list, so they always match.
"""

FOLDER = "search"


def results_sections():
    """
    The results, grouped into sections.

    Returns:
        A list of (section name, items) for pxlab's show_results_tabs() and
        write_results_doc().
    """
    return [
        (
            "Maze",
            [
                ("text", "Breadth-first against depth-first, averaged over 10 random mazes per size."),
                ("table", "Maze benchmark", f"{FOLDER}/maze_benchmark.csv"),
                ("figure", f"{FOLDER}/maze_example.png"),
            ],
        ),
        (
            "8-puzzle",
            [
                (
                    "text",
                    "A* with two heuristics against breadth-first, averaged over the scrambled boards "
                    "whose shortest solution has the same number of moves.",
                ),
                ("figure", f"{FOLDER}/puzzle_explored.png"),
                ("table", "8-puzzle benchmark", f"{FOLDER}/puzzle_benchmark.csv"),
            ],
        ),
        (
            "Robot",
            [
                (
                    "text",
                    "Greedy best-first against A* on 40x40 grids, 20 per obstacle density "
                    "(grids where obstacles cut off the goal are skipped).",
                ),
                ("table", "Robot benchmark", f"{FOLDER}/robot_benchmark.csv"),
                ("figure", f"{FOLDER}/robot_example.png"),
            ],
        ),
        (
            "City map",
            [
                ("text", "Every route between ten Westminster landmarks (45 routes), walking distance in metres."),
                ("table", "City map benchmark", f"{FOLDER}/city_benchmark.csv"),
                ("figure", f"{FOLDER}/city_example.png"),
            ],
        ),
    ]
