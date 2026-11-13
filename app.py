"""
app.py - the search algorithms demo. Run it with:

    streamlit run app.py

Tabs:
    Overview   what each algorithm does and what was found,
    Maze       breadth-first against depth-first on a maze you generate,
    8-puzzle   A* with a heuristic you pick, against breadth-first, step by step,
    Robot      greedy best-first against A* on an obstacle grid,
    City map   breadth-first, uniform cost and A* between Westminster landmarks,
    Results    the saved benchmark tables and figures from main.py.
Every search runs live; nothing needs to be trained first.
"""

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from pathfinding_lab.city import LANDMARKS, CityMap, CityProblem, city_figure
from pathfinding_lab.grids import GridProblem, grid_figure, make_maze, make_obstacle_grid
from pathfinding_lab.puzzle import HEURISTICS, PuzzleProblem, board_text, scramble
from pathfinding_lab.report import results_sections
from pxlab.app import setup_page, show_markdown_file, show_results_tabs
from pxlab.search.algorithms import ALGORITHMS, a_star_search, breadth_first_search


def stats_table(results):
    """
    The comparison table shown under each search.

    Input:
        results: SearchResults.
    Returns:
        A DataFrame indexed by algorithm.
    """
    return pd.DataFrame(
        {
            "Path steps": [r.steps for r in results],
            "Explored": [len(r.explored) for r in results],
            "Largest frontier": [r.max_frontier for r in results],
            "Milliseconds": [round(r.seconds * 1000, 1) for r in results],
        },
        index=[r.algorithm for r in results],
    )


def show_figure_live(figure):
    """
    Show a matplotlib figure and free its memory.

    Input:
        figure: a matplotlib figure.
    Returns:
        Nothing.
    """
    st.pyplot(figure, width="stretch")
    plt.close(figure)


def show_maze_page():
    """
    The Maze tab: BFS and DFS side by side on a generated maze.

    Returns:
        Nothing.
    """
    size_box, seed_box, loops_box = st.columns(3)
    size = size_box.select_slider("Maze size", [15, 25, 35, 45, 55], value=35)
    seed = seed_box.number_input("Maze number", 0, 999, 3, help="The same number always gives the same maze.")
    loops = loops_box.slider(
        "Extra openings", 0.0, 0.3, 0.08, 0.02, help="Share of inner walls removed, so more than one route exists."
    )
    grid, start, goal = make_maze(size, int(seed), loops)
    problem = GridProblem(grid, start, goal)
    results = [breadth_first_search(problem), ALGORITHMS["Depth-first"](problem)]
    titles = [f"{r.algorithm}: {r.steps} steps" for r in results]
    show_figure_live(grid_figure(problem, results, titles))
    st.caption("Light blue: cells explored. Orange: the path found. Green circle: start. Green star: goal.")
    st.dataframe(stats_table(results), width="stretch")
    st.markdown(
        "Breadth-first explores in rings around the start, so its path has the fewest steps. "
        "Depth-first follows one corridor to its end before backing up: it keeps less in memory but "
        "usually comes back with a much longer path. Set **Extra openings** to 0 for a maze with only one "
        "route: then both find the same path."
    )


def show_puzzle_page():
    """
    The 8-puzzle tab: solve a scrambled board and step through the solution.

    Returns:
        Nothing.
    """
    moves_box, seed_box, heuristic_box = st.columns(3)
    moves = moves_box.slider("Scramble moves", 2, 60, 20, help="Random slides away from the solved board.")
    seed = seed_box.number_input("Puzzle number", 0, 999, 0)
    heuristic_name = heuristic_box.selectbox("A* heuristic", list(HEURISTICS))
    board = scramble(moves, int(seed))
    star = a_star_search(PuzzleProblem(board, HEURISTICS[heuristic_name]))
    bfs = breadth_first_search(PuzzleProblem(board))
    star.algorithm = f"A* ({heuristic_name.lower()})"

    left, right = st.columns([1, 2], gap="large")
    with left:
        step = st.slider("Move", 0, star.steps, 0) if star.steps else 0
        st.code(board_text(star.path[step]), language=None)
        st.caption(f"Board after {step} of {star.steps} moves.")
    with right:
        st.dataframe(stats_table([star, bfs]), width="stretch")
        st.markdown(
            "Both find a shortest solution. Breadth-first tries every board 1 move away, then every board "
            "2 moves away, and so on. A* tries first the boards whose moves so far plus estimated moves left "
            "are lowest. Manhattan distance (how far each tile is from its place) is a closer estimate than "
            "misplaced tiles, so A* with it explores fewer boards."
        )


def show_robot_page():
    """
    The Robot tab: greedy best-first against A* on an obstacle grid.

    Returns:
        Nothing.
    """
    size_box, density_box, seed_box = st.columns(3)
    size = size_box.select_slider("Grid size", [20, 30, 40, 50], value=40)
    density = density_box.slider("Obstacles", 0.0, 0.4, 0.3, 0.05, help="Share of cells that are blocked.")
    seed = seed_box.number_input("Grid number", 0, 999, 7)
    grid, start, goal = make_obstacle_grid(size, size, density, int(seed))
    problem = GridProblem(grid, start, goal)
    results = [ALGORITHMS["Greedy best-first"](problem), a_star_search(problem)]
    if not results[1].found:
        st.warning("The obstacles cut the goal off from the start. Try another grid number or fewer obstacles.")
        return
    titles = [f"{r.algorithm}: {r.steps} steps" for r in results]
    show_figure_live(grid_figure(problem, results, titles))
    st.caption("Light blue: cells explored. Orange: the path found. Green circle: start. Green star: goal.")
    st.dataframe(stats_table(results), width="stretch")
    st.markdown(
        "Greedy best-first always moves to whatever cell looks closest to the goal, so it explores few cells, "
        "but it walks into dead ends and keeps the detour. A* also counts the steps already taken, so it "
        "explores more but always returns a shortest path."
    )


@st.cache_resource
def load_city():
    """
    Load the Westminster street graph (cached, so this happens once).

    Returns:
        A CityMap.
    """
    return CityMap()


def show_city_page():
    """
    The City map tab: three searches on one walking route.

    Returns:
        Nothing.
    """
    city = load_city()
    names = list(LANDMARKS)
    from_box, to_box = st.columns(2)
    origin = from_box.selectbox("From", names, index=names.index("Piccadilly Circus"))
    destination = to_box.selectbox("To", names, index=names.index("Big Ben"))
    if origin == destination:
        st.info("Pick two different places.")
        return
    problem = CityProblem(city, city.nearest_node(LANDMARKS[origin]), city.nearest_node(LANDMARKS[destination]))
    results = [ALGORITHMS[name](problem) for name in ["Breadth-first", "Uniform cost", "A*"]]
    titles = [f"{r.algorithm}: {r.cost:,.0f} m" for r in results]
    show_figure_live(city_figure(city, results, titles))
    st.caption("Blue dots: street points explored. Orange: the route found.")
    table = stats_table(results).rename(columns={"Path steps": "Street segments"})
    table.insert(0, "Metres", [round(r.cost) for r in results])
    st.dataframe(table, width="stretch")
    st.markdown(
        "Breadth-first counts street segments, not metres, so its route has the fewest segments but is often "
        "longer to walk. Uniform cost expands the shortest walk so far and finds the shortest route. A* finds "
        "the same route but, guided by the straight-line distance to the goal, explores far fewer points."
    )
    st.caption("Map data © OpenStreetMap contributors, ODbL.")


def main():
    """
    Build the page.

    Returns:
        Nothing.
    """
    setup_page("Pathfinding lab")
    tabs = st.tabs(["Overview", "Maze", "8-puzzle", "Robot", "City map", "Results"])
    with tabs[0]:
        show_markdown_file("app_overview.md")
    with tabs[1]:
        show_maze_page()
    with tabs[2]:
        show_puzzle_page()
    with tabs[3]:
        show_robot_page()
    with tabs[4]:
        show_city_page()
    with tabs[5]:
        show_results_tabs(results_sections())


main()
