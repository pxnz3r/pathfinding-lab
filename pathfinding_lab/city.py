"""
city.py - shortest walking routes on a real street map of Westminster,
London, built from OpenStreetMap.

The map is a graph: a node is a point on a street (a junction or a bend),
an edge is the stretch of street between two nodes, and its cost is its
length in metres. Streets are walked both ways.

maps/westminster.json is built once by scripts/build_city_map.py from an
OpenStreetMap download and committed, so nothing is downloaded at run time.
Map data © OpenStreetMap contributors, ODbL.
"""

import json
import math
from collections import defaultdict

import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection

MAP_FILE = "maps/westminster.json"

# Street types kept from OpenStreetMap: anything a person can walk along
# that is a real street, not a footpath through a building or park.
STREET_TYPES = {
    "trunk",
    "trunk_link",
    "primary",
    "primary_link",
    "secondary",
    "secondary_link",
    "tertiary",
    "tertiary_link",
    "unclassified",
    "residential",
    "living_street",
    "pedestrian",
    "service",
}

# Places to start and end a route, snapped to the nearest street node.
LANDMARKS = {
    "Trafalgar Square": (51.5080, -0.1281),
    "Piccadilly Circus": (51.5100, -0.1347),
    "Leicester Square": (51.5103, -0.1302),
    "Covent Garden": (51.5117, -0.1240),
    "Charing Cross station": (51.5081, -0.1248),
    "Horse Guards Parade": (51.5049, -0.1287),
    "Downing Street": (51.5033, -0.1276),
    "Big Ben": (51.5007, -0.1246),
    "St James's Park station": (51.4995, -0.1335),
    "Pall Mall": (51.5065, -0.1330),
}

EARTH_RADIUS_METRES = 6_371_000


def distance_metres(point_a, point_b):
    """
    Straight-line (great-circle) distance between two (latitude, longitude)
    points, with the haversine formula.

    Inputs:
        point_a, point_b: (latitude, longitude) in degrees.
    Returns:
        The distance in metres.
    """
    lat_a, lon_a = map(math.radians, point_a)
    lat_b, lon_b = map(math.radians, point_b)
    half = math.sin((lat_b - lat_a) / 2) ** 2 + math.cos(lat_a) * math.cos(lat_b) * math.sin((lon_b - lon_a) / 2) ** 2
    return 2 * EARTH_RADIUS_METRES * math.asin(math.sqrt(half))


def build_city_map(osm_path, map_path, bbox):
    """
    Turn an OpenStreetMap JSON download into the compact street graph used
    here, keeping only the largest connected part.

    Inputs:
        osm_path: the OpenStreetMap API JSON file.
        map_path: where to write the graph.
        bbox: (min_lon, min_lat, max_lon, max_lat) of the download.
    Returns:
        (number of nodes, number of edges).
    """
    with open(osm_path, encoding="utf-8") as file:
        elements = json.load(file)["elements"]
    points = {e["id"]: (e["lat"], e["lon"]) for e in elements if e["type"] == "node" and "lat" in e}
    min_lon, min_lat, max_lon, max_lat = bbox
    inside = {i for i, (lat, lon) in points.items() if min_lat <= lat <= max_lat and min_lon <= lon <= max_lon}

    edges = {}
    for element in elements:
        if element["type"] != "way" or element.get("tags", {}).get("highway") not in STREET_TYPES:
            continue
        nodes = element["nodes"]
        for a, b in zip(nodes, nodes[1:]):
            if a in inside and b in inside and a != b:
                edges[tuple(sorted((a, b)))] = round(distance_metres(points[a], points[b]), 1)

    # Keep the largest connected part, so every pair of nodes has a route.
    links = defaultdict(list)
    for a, b in edges:
        links[a].append(b)
        links[b].append(a)
    best, seen = set(), set()
    for node in links:
        if node in seen:
            continue
        part, stack = set(), [node]
        while stack:
            current = stack.pop()
            if current not in part:
                part.add(current)
                stack.extend(links[current])
        seen |= part
        best = max(best, part, key=len)

    graph = {
        "source": "OpenStreetMap contributors, ODbL 1.0 (openstreetmap.org/copyright)",
        "bbox": list(bbox),
        "nodes": {str(i): [round(points[i][0], 6), round(points[i][1], 6)] for i in sorted(best)},
        "edges": [[str(a), str(b), length] for (a, b), length in sorted(edges.items()) if a in best],
    }
    with open(map_path, "w", encoding="utf-8") as file:
        json.dump(graph, file, separators=(",", ":"))
    return len(graph["nodes"]), len(graph["edges"])


class CityMap:
    """The street graph: node positions and, per node, its street links."""

    def __init__(self, path=MAP_FILE):
        """
        Input:
            path: the graph file written by build_city_map().
        """
        with open(path, encoding="utf-8") as file:
            data = json.load(file)
        self.positions = {node: tuple(point) for node, point in data["nodes"].items()}
        self.links = defaultdict(list)
        for a, b, length in data["edges"]:
            self.links[a].append((b, length))
            self.links[b].append((a, length))
        self.segments = [(self.positions[a], self.positions[b]) for a, b, _ in data["edges"]]

    def nearest_node(self, point):
        """
        The street node closest to a (latitude, longitude) point.

        Input:
            point: (latitude, longitude).
        Returns:
            The node id.
        """
        return min(self.positions, key=lambda node: distance_metres(point, self.positions[node]))


class CityProblem:
    """
    Walk from one street node to another. Follows the problem interface of
    pxlab.search.algorithms.
    """

    def __init__(self, city, start, goal):
        """
        Inputs:
            city: a CityMap.
            start, goal: node ids.
        """
        self.city = city
        self.start = start
        self.goal = goal
        self.goal_position = city.positions[goal]

    def is_goal(self, node):
        """True at the goal node."""
        return node == self.goal

    def neighbours(self, node):
        """The nodes one street segment away, with the segment length in metres."""
        return self.city.links[node]

    def heuristic(self, node):
        """
        Straight-line distance to the goal. No walk can be shorter than the
        straight line, so it never overestimates and A* stays optimal.
        """
        return distance_metres(self.city.positions[node], self.goal_position)


def plot_city(axis, city, result, title):
    """
    Draw the streets, the nodes a search explored and the route it found.

    Inputs:
        axis: a matplotlib axis.
        city: a CityMap.
        result: a SearchResult on a CityProblem.
        title: the axis title.
    Returns:
        Nothing.
    """
    # Longitude across, latitude up; squash longitude so distances look right.
    squash = math.cos(math.radians(51.5))
    lines = [[(a[1] * squash, a[0]), (b[1] * squash, b[0])] for a, b in city.segments]
    axis.add_collection(LineCollection(lines, colors="#BFC5CC", linewidths=0.7))
    explored = [city.positions[node] for node in result.explored]
    axis.scatter([p[1] * squash for p in explored], [p[0] for p in explored], s=3, color="#4C8BD6", alpha=0.5)
    route = [city.positions[node] for node in result.path]
    axis.plot([p[1] * squash for p in route], [p[0] for p in route], color="#E8590C", linewidth=2.6)
    for point, marker in [(route[0], "o"), (route[-1], "*")]:
        axis.plot(point[1] * squash, point[0], marker=marker, color="#2B8A3E", markersize=11)
    axis.set_title(title, fontsize=10)
    axis.set_aspect("equal")
    axis.autoscale()
    axis.set_xticks([])
    axis.set_yticks([])
    axis.grid(False)


def city_figure(city, results, titles):
    """
    Side-by-side maps, one per search result.

    Inputs:
        city: a CityMap.
        results: SearchResults on the same route.
        titles: one title per result.
    Returns:
        The matplotlib figure.
    """
    figure, axes = plt.subplots(1, len(results), figsize=(5.4 * len(results), 5.6))
    for axis, result, title in zip(axes, results, titles):
        plot_city(axis, city, result, title)
    return figure
