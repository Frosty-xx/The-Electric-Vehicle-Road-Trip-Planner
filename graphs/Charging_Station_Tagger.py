import logging
import networkx as nx
import osmnx as ox
import os
import json

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(
    BASE_DIR, "..", "Back-End", "Data", "Algeria_charging_stations.json"
)
Graph_Path = os.path.join(BASE_DIR, "algeria_roads.graphml")

# ---------------------------------------------------------------------------
# tag charging stations
# ---------------------------------------------------------------------------


def _tag_charging_stations(G: nx.MultiDiGraph, stations) -> None:
    """Snap OpenChargeMap stations to their nearest graph node."""
    if not stations:
        log.warning("No charging stations provided– graph will have none tagged.")
        return

    lons = [s["lon"] for s in stations]
    lats = [s["lat"] for s in stations]

    log.info(f"Snapping {len(stations)} charging stations to graph nodes ...")
    node_ids = ox.distance.nearest_nodes(G, lons, lats)

    for node_id, station in zip(node_ids, stations):
        G.nodes[node_id]["is_charging_station"] = True
        existing_kw = G.nodes[node_id].get("charger_kw", 0)
        G.nodes[node_id]["charger_kw"] = max(existing_kw, station.get("max_kw", 50))


if __name__ == "__main__":

    with open(DATA_PATH, encoding="utf-8") as f:
        data = json.load(f)

    stations = [
        {
            "lat": s["latitude"],
            "lon": s["longitude"],
            "max_kw": s["power_kw"],
            "name": s["name"],
        }
        for s in data["charging_stations"]
    ]
    # Default all nodes to False
    G = ox.load_graphml(Graph_Path)
    for node_id in G.nodes:
        G.nodes[node_id]["is_charging_station"] = False
        G.nodes[node_id]["charger_kw"] = 0
    _tag_charging_stations(G, stations)
    ox.save_graphml(G, Graph_Path)
