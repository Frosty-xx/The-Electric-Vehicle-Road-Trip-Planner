import json
import math

#Helper Function
def haversine(lat1, lon1, lat2, lon2):
    """Calculate distance in km between two GPS coordinates."""
    R = 6371  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))


def build_graph(dataset_path, max_edge_distance_km=100):
    """
    Builds a graph where:
    - Each node is a charging station (id, name, lat, lon, power_kw)
    - Each edge connects two stations within max_edge_distance_km
    - Edge weight is the distance in km
    """

    # Load dataset
    with open(dataset_path) as f:
        dataset = json.load(f)

    stations = dataset["charging_stations"]
    vehicle = dataset["vehicle"]

    # Build node list
    nodes = {}
    for i, station in enumerate(stations):
        if station["latitude"] and station["longitude"]:  # skip stations with missing coords
            nodes[i] = {
                "id": i,
                "name": station["name"],
                "lat": station["latitude"],
                "lon": station["longitude"],
                "power_kw": station["power_kw"]
            }

    # Build adjacency list
    graph = {node_id: [] for node_id in nodes}


    for i in nodes:
        for j in nodes:
            if i >= j:
                continue  # avoid duplicates and self-loops

            dist = haversine(
                nodes[i]["lat"], nodes[i]["lon"],
                nodes[j]["lat"], nodes[j]["lon"]
            )

            if dist <= max_edge_distance_km:
                # Calculate battery cost for this edge
                battery_cost = dist * vehicle["consumption_kwh_per_km"]

                graph[i].append({
                    "to": j,
                    "distance_km": round(dist, 2),
                    "battery_cost_kwh": round(battery_cost, 2)
                })
                graph[j].append({
                    "to": i,
                    "distance_km": round(dist, 2),
                    "battery_cost_kwh": round(battery_cost, 2)
                })

    return nodes, graph, vehicle


def find_nearest_station(nodes, lat, lon):
    """Find the closest station to a given GPS coordinate."""
    return min(nodes, key=lambda i: haversine(lat, lon, nodes[i]["lat"], nodes[i]["lon"]))

def near_stations(nodes,lat,lon,radius=60):
    """Retruns near stations to a given GPS coordinates."""
    stations=[]
    for i in nodes:
        if haversine(lat, lon,nodes[i]["lat"],nodes[i]["lon"]) < radius:
            stations.append(nodes[i]["id"])
    return stations

def print_node(node_id:int):
    print(f"Name: {nodes[node_id]["name"]}")
    print(f"lat: {nodes[node_id]["lat"]}")
    print(f"lon: {nodes[node_id]["lon"]}")
    print(f"distance: {haversine(lat,lon,nodes[node_id]["lat"],nodes[node_id]["lon"])} km")
    print(f"pwer(kwh): {nodes[node_id]["power_kw"]}")
    


# --- Example usage ---
if __name__ == "__main__":
    nodes, graph, vehicle = build_graph("./ev_dataset.json", max_edge_distance_km=300)
    
    # A GPS location in Paris
    lat=48.8566
    lon=2.3522


    print(f"Nodes: {len(nodes)} charging stations")


    #Charging Stations near a location in Paris 
    print("====================================Charging Stations near Paris:====================================")
    
    near_stations_ids= near_stations(nodes,lat,lon,radius=100)
    for station_id in near_stations_ids:
        print_node(station_id)
        print('-'*20)


    #Nearest Station:
    station_id = find_nearest_station(nodes, lat, lon)   # Algiers
    print("====================================Nearest Station:====================================")
    print_node(station_id)

    
    
    
    


