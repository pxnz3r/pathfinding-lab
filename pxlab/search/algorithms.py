"""
search/algorithms.py - uninformed and informed search on any problem.

A problem is any object with:
    start                the starting state (any hashable value)
    is_goal(state)       True when the state is a goal
    neighbours(state)    a list of (next_state, step_cost)
    heuristic(state)     an estimate of the cost left to the goal
                         (only the informed searches use it)

Every search returns a SearchResult with the path it found, its cost, the
states it expanded in order (to draw and count them), the largest the
frontier got (memory) and the time it took.

Uninformed searches know nothing about where the goal is:
    breadth-first   expands states in order of distance in steps, so it
                    finds the path with the fewest steps.
    depth-first     follows one branch as deep as it goes before backing
                    up. Little memory, but the path it finds can be long.
    uniform cost    expands the cheapest path so far, so it finds the
                    cheapest path when steps cost different amounts.
Informed searches use the heuristic:
    greedy          expands whatever looks closest to the goal. Fast, but
                    not guaranteed to find the best path.
    A*              expands the lowest (cost so far + estimate left). With
                    a heuristic that never overestimates, the first path
                    it finds is the cheapest.
"""

import heapq
import itertools
import time
from collections import deque
from dataclasses import dataclass


@dataclass
class SearchResult:
    """What one search run found and what it cost to find it."""

    algorithm: str
    path: list  # states from the start to the goal; empty if no path
    cost: float  # total step cost of the path
    explored: list  # states in the order they were expanded
    max_frontier: int  # the most states waiting in the frontier at once
    seconds: float

    @property
    def found(self):
        """True when a path to the goal was found."""
        return bool(self.path)

    @property
    def steps(self):
        """Number of moves in the path."""
        return max(len(self.path) - 1, 0)


def rebuild_path(parents, goal):
    """
    Follow the parent links back from the goal to the start.

    Inputs:
        parents: dictionary state -> the state it was reached from (None
            for the start).
        goal: the goal state.
    Returns:
        The list of states from the start to the goal.
    """
    path = [goal]
    while parents[path[-1]] is not None:
        path.append(parents[path[-1]])
    return path[::-1]


def finish(name, parents, costs, explored, max_frontier, started, goal=None):
    """
    Package a search's outcome as a SearchResult.

    Inputs:
        name: the algorithm's name.
        parents, costs: dictionaries filled during the search.
        explored: the expanded states in order.
        max_frontier: the largest frontier size.
        started: time.perf_counter() at the start.
        goal: the goal state reached, or None if there was none.
    Returns:
        A SearchResult.
    """
    path = rebuild_path(parents, goal) if goal is not None else []
    cost = costs[goal] if goal is not None else float("inf")
    return SearchResult(name, path, cost, explored, max_frontier, time.perf_counter() - started)


def breadth_first_search(problem):
    """
    Breadth-first search: a first-in-first-out queue, so all states one
    step away are expanded before any state two steps away.

    Input:
        problem: see the module docstring.
    Returns:
        A SearchResult; the path has the fewest steps.
    """
    started = time.perf_counter()
    queue = deque([problem.start])
    parents = {problem.start: None}  # also the set of states already seen
    costs = {problem.start: 0}
    explored = []
    max_frontier = 1
    while queue:
        state = queue.popleft()
        explored.append(state)
        if problem.is_goal(state):
            return finish("Breadth-first", parents, costs, explored, max_frontier, started, state)
        for next_state, step_cost in problem.neighbours(state):
            if next_state not in parents:
                parents[next_state] = state
                costs[next_state] = costs[state] + step_cost
                queue.append(next_state)
        max_frontier = max(max_frontier, len(queue))
    return finish("Breadth-first", parents, costs, explored, max_frontier, started)


def depth_first_search(problem):
    """
    Depth-first search: a last-in-first-out stack, so the newest state is
    expanded next and the search dives down one branch at a time.

    Input:
        problem: see the module docstring.
    Returns:
        A SearchResult; the path is whatever branch reached the goal first.
    """
    started = time.perf_counter()
    stack = [problem.start]
    parents = {problem.start: None}
    costs = {problem.start: 0}
    visited = set()
    explored = []
    max_frontier = 1
    while stack:
        state = stack.pop()
        if state in visited:
            continue  # pushed twice; the copy popped first already handled it
        visited.add(state)
        explored.append(state)
        if problem.is_goal(state):
            return finish("Depth-first", parents, costs, explored, max_frontier, started, state)
        # Push in reverse so the first neighbour is expanded first.
        for next_state, step_cost in reversed(problem.neighbours(state)):
            if next_state not in visited:
                # The latest push is popped first, so the latest parent is
                # the one the search really uses.
                parents[next_state] = state
                costs[next_state] = costs[state] + step_cost
                stack.append(next_state)
        max_frontier = max(max_frontier, len(stack))
    return finish("Depth-first", parents, costs, explored, max_frontier, started)


def best_first_search(problem, name, priority, improve_paths=True):
    """
    The shared loop of uniform cost, greedy and A*: a priority queue that
    always expands the state with the lowest priority value.

    Inputs:
        problem: see the module docstring.
        name: the algorithm's name for the result.
        priority: function (cost so far, state) -> number; lower is
            expanded first.
        improve_paths: True to update a waiting state when a cheaper way to
            it turns up (needed for uniform cost and A* to be optimal).
    Returns:
        A SearchResult.
    """
    started = time.perf_counter()
    order = itertools.count()  # breaks ties in arrival order
    frontier = [(priority(0, problem.start), next(order), problem.start)]
    parents = {problem.start: None}
    costs = {problem.start: 0}
    closed = set()
    explored = []
    max_frontier = 1
    while frontier:
        _, _, state = heapq.heappop(frontier)
        if state in closed:
            continue  # an older, worse copy of a state already expanded
        closed.add(state)
        explored.append(state)
        if problem.is_goal(state):
            return finish(name, parents, costs, explored, max_frontier, started, state)
        for next_state, step_cost in problem.neighbours(state):
            if next_state in closed:
                continue
            new_cost = costs[state] + step_cost
            seen = next_state in costs
            if not seen or (improve_paths and new_cost < costs[next_state]):
                parents[next_state] = state
                costs[next_state] = new_cost
                heapq.heappush(frontier, (priority(new_cost, next_state), next(order), next_state))
        max_frontier = max(max_frontier, len(frontier))
    return finish(name, parents, costs, explored, max_frontier, started)


def uniform_cost_search(problem):
    """
    Uniform cost search: expand the cheapest path so far (Dijkstra's
    algorithm with an early stop at the goal).

    Input:
        problem: see the module docstring.
    Returns:
        A SearchResult; the path is the cheapest.
    """
    return best_first_search(problem, "Uniform cost", lambda cost, state: cost)


def greedy_best_first_search(problem):
    """
    Greedy best-first search: expand whatever the heuristic says is
    closest to the goal, ignoring the cost so far.

    Input:
        problem: see the module docstring.
    Returns:
        A SearchResult; often quick, but the path can be longer than needed.
    """
    return best_first_search(
        problem, "Greedy best-first", lambda cost, state: problem.heuristic(state), improve_paths=False
    )


def a_star_search(problem):
    """
    A* search: expand the lowest cost so far + heuristic estimate left.

    Input:
        problem: see the module docstring.
    Returns:
        A SearchResult; the path is the cheapest when the heuristic never
        overestimates.
    """

    def priority(cost, state):
        # Many states can share the same total (on an open grid every
        # direct route does). Among those, expand the one estimated closest
        # to the goal first, so A* follows one route instead of all of them.
        estimate = problem.heuristic(state)
        return (cost + estimate, estimate)

    return best_first_search(problem, "A*", priority)


ALGORITHMS = {
    "Breadth-first": breadth_first_search,
    "Depth-first": depth_first_search,
    "Uniform cost": uniform_cost_search,
    "Greedy best-first": greedy_best_first_search,
    "A*": a_star_search,
}
