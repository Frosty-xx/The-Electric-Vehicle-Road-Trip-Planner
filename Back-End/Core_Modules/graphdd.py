from pyrosm import OSM
import os
from dotenv import load_dotenv
import math
import logging
import requests
import osmnx as ox
import networkx as nx
from networkx import MultiDiGraph
import pandas as pd
pd.options.mode.chained_assignment = None

# Standard OSMnx settings
ox.settings.requests_timeout = 800

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# DATA LOADING (GLOBAL)
# ---------------------------------------------------------------------------
# PBF_PATH = "graphs/tunisia_osm.pbf"

# if os.path.exists(PBF_PATH):
#     log.info(f"Loading Tunisia PBF data from {PBF_PATH}...")
#     osm = OSM(PBF_PATH)
    
#     # Capture the output regardless of how many values are returned
#     network_data = osm.get_network(network_type="driving")

#     # Robust unpacking
#     if isinstance(network_data, tuple):
#         # Handle 2-tuple (nodes, edges) or 3-tuple (nodes, edges, coords)
#         nodes_pyrosm = network_data[0]
#         edges_pyrosm = network_data[1]
#     else:
#         # Handle case where only edges are returned
#         edges_pyrosm = network_data
#         nodes_pyrosm = None

#     # CRITICAL FIX: If nodes are None, we must extract them from the edges
#     if nodes_pyrosm is None:
#         log.info("Nodes not returned by pyrosm; generating from edges...")
#         # This creates the necessary node GeoDataFrame from the edge geometries
#         # Note: In some versions, this helper is required to avoid the NoneType error
#         # Alternatively, ensure nodes exist by using a broader filter
#         nodes_pyrosm, edges_pyrosm = osm.get_network(network_type="driving", nodes=True)

#     # Convert to NetworkX MultiDiGraph
#     try:
#         TUNISIA_G = osm.to_graph(nodes_pyrosm, edges_pyrosm, graph_type="networkx")
#         log.info("Full Tunisia graph loaded into memory.")
#     except Exception as e:
#         log.error(f"Failed to convert to graph: {e}")
#         TUNISIA_G = None

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DEFAULT_KWH_PER_KM = 0.16125 
OPEN_CHARGE_MAP_URL = "https://api.openchargemap.io/v3/poi/"
load_dotenv()
OCM_API_KEY = os.getenv("OCM_API_KEY")
COUNTRY_CODE = "TN" # Fixed to TN for Tunisia

# ---------------------------------------------------------------------------
# Core Logic
# ---------------------------------------------------------------------------

def _resolve_location(location: str | tuple[float, float]) -> tuple[float, float]:
    if isinstance(location, str):
        return ox.geocode(location)
    return location

def build_graph(
    origin: str | tuple[float, float],
    destination: str | tuple[float, float],
    simplify: bool = True,
    add_speeds: bool = True,
    add_travel_times: bool = True,
) -> tuple[nx.MultiDiGraph, int, int]:
    """
    Uses the pre-loaded Tunisia graph to calculate the trip.
    """
    # if TUNISIA_G is None:
    #     raise FileNotFoundError("Global Tunisia graph not loaded. check PBF path.")

    loc1 = _resolve_location(origin)
    loc2 = _resolve_location(destination)

    distance_km = haversine_km(loc1[0], loc1[1], loc2[0], loc2[1])
    log.info(f"Route: {origin} -> {destination} ({distance_km:.1f} km)")

    # We use the full graph now, but you could sub-graph it for speed if desired.
    # For Tunisia, using the full graph (TUNISIA_G) is fine.
    G = ox.graph_from_xml("graphs/tunisia_osm_01.osm")
    
    if simplify:
        # Pyrosm graphs are usually already simplified, but ox can clean it further
        G = ox.simplify_graph(G)

    if add_speeds:
        G = ox.add_edge_speeds(G)

    if add_travel_times:
        G = ox.add_edge_travel_times(G)

    _add_energy_cost(G)

    # Initialize charging station attributes
    nx.set_node_attributes(G, False, "is_charging_station")
    nx.set_node_attributes(G, 0, "charger_kw")

    # Tag charging stations based on the bounding box of the route
    bbox = _build_bbox(loc1, loc2, distance_km)
    _tag_charging_stations(G, bbox)

    # Snap nodes (Note: OSMnx expects lat, lon usually, but Pyrosm nodes use x/y)
    orig_node = ox.distance.nearest_nodes(G, loc1[1], loc1[0]) 
    dest_node = ox.distance.nearest_nodes(G, loc2[1], loc2[0])

    return G, orig_node, dest_node

# [Keep your _add_energy_cost, _tag_charging_stations, _fetch_charging_stations, 
# _build_bbox, and haversine_km functions exactly as they were here...]

def _add_energy_cost(G, kwh_per_km=DEFAULT_KWH_PER_KM):
    for u, v, k, d in G.edges(keys=True, data=True):
        dist_km = d.get("length", 0) / 1000.0
        G[u][v][k]["kwh_cost"] = round(dist_km * kwh_per_km, 4)

def _build_bbox(loc1, loc2, distance_km):
    padding = max(0.05, distance_km * 0.01) # Slightly larger padding for stations
    north = max(loc1[0], loc2[0]) + padding
    south = min(loc1[0], loc2[0]) - padding
    east  = max(loc1[1], loc2[1]) + padding
    west  = min(loc1[1], loc2[1]) - padding
    return north, south, east, west

def _tag_charging_stations(G, bbox):
    stations = _fetch_charging_stations(bbox)
    if not stations: return
    
    lons = [s["lon"] for s in stations]
    lats = [s["lat"] for s in stations]
    node_ids = ox.distance.nearest_nodes(G, lons, lats)

    for node_id, station in zip(node_ids, stations):
        G.nodes[node_id]["is_charging_station"] = True
        G.nodes[node_id]["charger_kw"] = max(G.nodes[node_id].get("charger_kw", 0), station.get("max_kw", 50))

def _fetch_charging_stations(bbox):
    north, south, east, west = bbox
    params = {
        "output": "json", "maxresults": 500, "compact": True,
        "countrycode": "TN", "latitude": (north+south)/2, "longitude": (east+west)/2,
        "distance": _bbox_radius_km(north, south, east, west), "distanceunit": "KM", "levelid": 3,
    }
    try:
        resp = requests.get(OPEN_CHARGE_MAP_URL, params=params, timeout=10)
        raw = resp.json()
        stations = []
        for poi in raw:
            addr = poi.get("AddressInfo", {})
            stations.append({
                "lat": addr.get("Latitude"), 
                "lon": addr.get("Longitude"), 
                "max_kw": max([c.get("PowerKW", 0) or 0 for c in poi.get("Connections", [])] + [50])
            })
        return stations
    except: return []

def _bbox_radius_km(north, south, east, west):
    lat_km = (north - south) * 111
    lon_km = (east - west) * 111 * math.cos(math.radians((north + south) / 2))
    return round(math.sqrt((lat_km / 2) ** 2 + (lon_km / 2) ** 2), 1)

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi, dlam = math.radians(lat2-lat1), math.radians(lon2-lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlam/2)**2
    return R * 2 * math.asin(math.sqrt(a))

# ---------------------------------------------------------------------------
# Test Execution
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=== Test 1: Intra-city (Tunis) ===")
    try:
        G, orig, dest = build_graph(
            origin="Tunis, Tunisia",
            destination="La Marsa, Tunisia"
        )
        cs_nodes = [n for n, d in G.nodes(data=True) if d.get("is_charging_station")]
        print(f"Nodes: {len(G.nodes)}, Charging stations: {len(cs_nodes)}")
        print(f"Origin Node: {orig}, Destination Node: {dest}")
    except Exception as e:
        print(f"Test 1 Failed: {e}")

    print("\n=== Test 2: Distance Check ===")
    d = haversine_km(36.8065, 10.1616, 34.7406, 10.7603)
    print(f"Haversine Tunis→Sfax: {d:.1f} km (Target ~250km)")