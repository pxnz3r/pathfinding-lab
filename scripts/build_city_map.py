"""
build_city_map.py - build maps/westminster.json from OpenStreetMap. Run
once from the project folder:

    python scripts/build_city_map.py

It downloads one small area (about 1.1 km by 1.5 km around Whitehall) from
the OpenStreetMap API into data/, keeps the walkable streets and writes the
compact street graph. The graph is committed, so main.py and the app never
download anything. Map data © OpenStreetMap contributors, ODbL.
"""

import os
import sys

sys.path.insert(0, os.getcwd())

from pathfinding_lab.city import MAP_FILE, build_city_map  # noqa: E402
from pxlab.common import DATA_FOLDER, download_once  # noqa: E402

BBOX = (-0.138, 51.499, -0.122, 51.513)  # min longitude, min latitude, max longitude, max latitude
URL = "https://api.openstreetmap.org/api/0.6/map.json?bbox=" + ",".join(str(value) for value in BBOX)


def main():
    """
    Download the area (once) and write the street graph.

    Returns:
        Nothing.
    """
    osm_path = download_once(URL, os.path.join(DATA_FOLDER, "osm_westminster.json"), timeout_seconds=180)
    os.makedirs(os.path.dirname(MAP_FILE), exist_ok=True)
    nodes, edges = build_city_map(osm_path, MAP_FILE, BBOX)
    print(f"  Wrote {MAP_FILE}: {nodes} street nodes, {edges} street segments")


if __name__ == "__main__":
    main()
