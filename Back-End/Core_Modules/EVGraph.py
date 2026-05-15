"""
Helper Function To manupulate the Graph
"""
import math
import osmnx as ox
import networkx as nx

# ---------------------------------------------------------------------------
# 2. Energy cost on edges
# ---------------------------------------------------------------------------
def _add_energy_cost(
    G: nx.MultiDiGraph, kwh_per_km
) -> None:
    """
    Add `kwh_cost` attribute to every edge.
    kwh_cost = distance_km * kwh_per_km
    """
    for u, v, key, data in G.edges(keys=True, data=True):
        dist_km = data.get("length", 0) / 1000.0  # OSMnx stores length in metres
        G[u][v][key]["kwh_cost"] = round(dist_km * kwh_per_km, 4)



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

def get_edge_trvel_time(G:nx.MultiDiGraph,u:int,v:int)->float:
    """Shortest edge travel time in seconds between u and v (min over parallel edges).
    """
    return min(d.get("travel_time", 0) for d in G[u][v].values()) 


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



