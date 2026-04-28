"""
graph_builder.py
================
Builds and manages the road network graph for the EV route planner.

Uses a locally saved OSM PBF file (tunisia_osm.pbf) via pyrosm.
The full network is loaded once, then filtered to the bounding box of the
origin–destination pair. Road type is also filtered based on distance.

NOTE: pyrosm's bounding_box constructor parameter is broken in current versions
(KeyError on 'id' in pbfreader). We work around this by filtering the returned
GeoDataFrames manually after get_network().

Usage:
    from graph_builder import build_graph

    G, orig_node, dest_node = build_graph("Tunis, Tunisia", "Sfax, Tunisia")
    # or with raw coordinates:
    G, orig_node, dest_node = build_graph((36.80, 10.18), (34.74, 10.76))
"""

import os
from dotenv import load_dotenv
import math
import logging
import requests
import osmnx as ox
import networkx as nx

import pandas as pd
pd.options.mode.chained_assignment = None

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PBF_PATH = "graphs/tunisia_osm.pbf"

# Average EV energy consumption in kWh/km (Hyundai Ioniq 5: 77.4 kWh / 480 km WLTP)
DEFAULT_KWH_PER_KM = 0.16125

OPEN_CHARGE_MAP_URL = "https://api.openchargemap.io/v3/poi/"
load_dotenv()
OCM_API_KEY = os.getenv("OCM_API_KEY")
COUNTRY_CODE = "TN"  # Tunisia

# ---------------------------------------------------------------------------
# Type alias
# ---------------------------------------------------------------------------

Location = str | tuple[float, float]  # address string OR (lat, lon) tuple

# ---------------------------------------------------------------------------
# 1. Build the road-network graph
# ---------------------------------------------------------------------------




def build_and_save_graph(
    add_speeds: bool = True,
    add_travel_times: bool = True,
):
    # Load the XML file locally
    print("Processing XML... this may take 1-2 minutes.")
    G = ox.graph_from_xml("graphs/tunisia_refined.osm")
    # log.info("Loading Graph...")
    # G = ox.load_graphml("graphs/tunisia.graphml")
    for u, v, k, data in G.edges(data=True, keys=True):
        if "length" in data:
            data["length"] = float(data["length"])
        
        # Ensure any existing speed tags are also numbers
        if "speed_kph" in data and data["speed_kph"] is not None:
            data["speed_kph"] = float(data["speed_kph"])


    if add_speeds:
        log.info("Adding speed data with fallbacks...")
        G = ox.add_edge_speeds(G)

    # Remove edges without length or speed, and add default speed to any remaining edges
    edges_to_remove = []
    for u, v, k, data in G.edges(data=True, keys=True):
        if data.get("length") is None:
            edges_to_remove.append((u, v, k))
        elif data.get("speed_kph") is None:
            # Set a default speed for edges missing speed_kph
            G[u][v][k]["speed_kph"] = 50.0
    
    for u, v, k in edges_to_remove:
        G.remove_edge(u, v, k)
    
    if edges_to_remove:
        log.warning(f"Removed {len(edges_to_remove)} edges without length attribute")

    if add_travel_times:
        log.info("Adding travel times ...")
        G = ox.add_edge_travel_times(G)

    _add_energy_cost(G)

    nx.set_node_attributes(G, False, "is_charging_station")
    nx.set_node_attributes(G, 0, "charger_kw")
    _tag_charging_stations(G)

    log.info(
        f"Graph ready: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges."
    )
    ox.save_graphml(G, "graphs/tunisia.graphml")
    print("Done! You now have a .graphml file.")


# ---------------------------------------------------------------------------
# 2. Energy cost on edges
# ---------------------------------------------------------------------------


def _add_energy_cost(
    G: nx.MultiDiGraph, kwh_per_km: float = DEFAULT_KWH_PER_KM
) -> None:
    """
    Add `kwh_cost` attribute to every edge.
    kwh_cost = distance_km * kwh_per_km
    """
    for u, v, key, data in G.edges(keys=True, data=True):
        dist_km = data.get("length", 0) / 1000.0  # OSMnx stores length in metres
        G[u][v][key]["kwh_cost"] = round(dist_km * kwh_per_km, 4)


# ---------------------------------------------------------------------------
# 3. Fetch & tag charging stations
# ---------------------------------------------------------------------------


def _tag_charging_stations(G: nx.MultiDiGraph)-> None:
    """Snap OpenChargeMap stations to their nearest graph node."""
    stations = _fetch_charging_stations()
    if not stations:
        log.warning("No charging stations fetched – graph will have none tagged.")
        return

    lons = [s["lon"] for s in stations]
    lats = [s["lat"] for s in stations]

    log.info(f"Snapping {len(stations)} charging stations to graph nodes ...")
    node_ids = ox.distance.nearest_nodes(G, lons, lats)

    for node_id, station in zip(node_ids, stations):
        G.nodes[node_id]["is_charging_station"] = True
        existing_kw = G.nodes[node_id].get("charger_kw", 0)
        G.nodes[node_id]["charger_kw"] = max(existing_kw, station.get("max_kw", 50))


def _fetch_charging_stations()-> list[dict]:

    params = {
        "output": "json",
        "maxresults": 2000,
        "compact": True,
        "verbose": False,
        "countrycode": COUNTRY_CODE,
        "distanceunit": "KM",
    }
    headers = {"X-API-Key": OCM_API_KEY} if OCM_API_KEY else {}

    try:
        log.info("Fetching charging stations from OpenChargeMap ...")
        resp = requests.get(OPEN_CHARGE_MAP_URL, params=params, headers=headers, timeout=15)
        resp.raise_for_status()
        raw = resp.json()
    except Exception as e:
        log.warning(f"OpenChargeMap request failed: {e}")
        return []

    stations = []
    for poi in raw:
        addr = poi.get("AddressInfo", {})
        lat, lon = addr.get("Latitude"), addr.get("Longitude")
        if lat is None or lon is None:
            continue
        max_kw = max((c.get("PowerKW") or 0 for c in poi.get("Connections", [])), default=0)
        stations.append({"lat": lat, "lon": lon, "max_kw": max_kw or 50})

    log.info(f"Found {len(stations)} charging stations.")
    return stations



# ---------------------------------------------------------------------------
# 4. Helper functions for the search algorithms
# ---------------------------------------------------------------------------

def get_nearest_node_from_address(G, address):
    """
    Get the nearest graph node ID from either:
      - a string address (geocoded automatically)

    Parameters
    ----------
    G       : nx.MultiDiGraph  — your OSMnx road network
    address : str              — e.g. "10 Rue de Rivoli, Lyon, France"

    Returns
    -------
    node_id : int
    """
    if address is not None:
        # Geocode the address → (lat, lon)
        lat, lon = ox.geocode(address)

    node_id = ox.distance.nearest_nodes(G, X=lon, Y=lat)  # note: X=lon, Y=lat
    return node_id

def nearest_node(G: nx.MultiDiGraph, lat: float, lon: float) -> int:
    """
    Return the graph node ID closest to (lat, lon).
    Use this to convert user-supplied coordinates into node IDs.
    """
    return ox.distance.nearest_nodes(G, lon, lat)


def get_edge_distance_km(G: nx.MultiDiGraph, u: int, v: int) -> float:
    """Shortest edge distance in km between u and v (min over parallel edges)."""
    return min(d.get("length", 0) for d in G[u][v].values()) / 1000.0


def get_edge_kwh_cost(G: nx.MultiDiGraph, u: int, v: int) -> float:
    """Energy cost (kWh) of the cheapest parallel edge u→v."""
    return float(min(d.get("kwh_cost", 0) for d in G[u][v].values()))


def get_node_coords(G: nx.MultiDiGraph, node_id: int) -> tuple[float, float]:
    """Return (lat, lon) of a node."""
    data = G.nodes[node_id]
    return data["y"], data["x"]  # 'y'=lat, 'x'=lon — set during build


def is_charging_station(G, node_id):
    val = G.nodes[node_id].get("is_charging_station", False)
    # GraphML returns the string "True" or "False", not a bool
    if isinstance(val, str):
        return val.strip().lower() == "true"
    return bool(val)


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Straight-line distance in km between two (lat, lon) points.
    Used as the heuristic h(n) in A*.
    """
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    a = (
        math.sin(math.radians(lat2 - lat1) / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    )
    return R * 2 * math.asin(math.sqrt(a))




# ---------------------------------------------------------------------------
# 5. Quick smoke-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=== Test 1 (Tunis) ===")
    # build_and_save_graph()
    G=ox.load_graphml("graphs/tunisia.graphml")
    G=ox.add_edge_travel_times(G)
    ox.save_graphml(G, "graphs/tunisia_final.graphml")


    d = haversine_km(36.8065, 10.1616, 34.7406, 10.7603)
    print(f"\nHaversine Tunis→Sfax: {d:.1f} km  (expect ~250 km)")