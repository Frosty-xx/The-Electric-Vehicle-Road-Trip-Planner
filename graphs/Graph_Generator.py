import osmnx as ox
import json as js
import pandas as pd

# Load from your filtered .pbf
print("Loading graph from XML....")
G = ox.graph_from_xml("algeria_roads.o5m", simplify=True, retain_all=False)

# --- NODES: only osmid, lat, lon ---
nodes, edges = ox.graph_to_gdfs(G)

nodes_minimal = nodes[["y", "x"]].rename(columns={"y": "lat", "x": "lon"})
nodes_minimal.index.name = "osmid"

# --- EDGES: osmid pair + distance + speed + geometry midpoint ---
# OSMnx adds 'length' (meters) and 'speed_kph' if you call add_edge_speeds
print("Adding edge speeds...")
G = ox.add_edge_speeds(G)     # adds 'speed_kph' from maxspeed tags + defaults
print("Adding Travel_Times..")
G = ox.add_edge_travel_times(G)

nodes, edges = ox.graph_to_gdfs(G)

edges_minimal = edges[["length", "speed_kph"]].copy()
edges_minimal["distance_m"] = edges_minimal["length"].round(2)
edges_minimal = edges_minimal.drop(columns=["length"])

# --- SAVE ---
# Option A: Parquet (fastest, smallest, keeps MultiIndex u/v/key)
nodes_minimal.to_parquet("algeria_nodes.parquet")
edges_minimal.to_parquet("algeria_edges.parquet")

# # Option B: CSV
# nodes_minimal.to_csv("algeria_nodes.csv")
# edges_minimal.to_csv("algeria_edges.csv")

# Option C: GraphML (keeps graph structure, good for NetworkX)
ox.save_graphml(G,'algeria_roads.graphml')
# Strip all attributes first for minimal size
for n, data in G.nodes(data=True):
    data.clear()
    data["lat"] = G.nodes[n].get("y")  # re-add only what you need... 
# Better: use the parquet approach and rebuild graph from it when needed

print(f"Nodes: {len(nodes_minimal):,}")
print(f"Edges: {len(edges_minimal):,}")