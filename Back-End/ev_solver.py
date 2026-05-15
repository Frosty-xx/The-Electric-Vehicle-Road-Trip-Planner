import osmnx as ox
from Core_Modules.EVGraph import get_nearest_node_from_address, _add_energy_cost,get_node_coords,is_charging_station
from Core_Modules.EV_Porblem import EV_Problem
from Search_Algorithms.General_Search import GeneralSearch 

DEFAULT_BATTERY_CAPACITY_KWH = 77.4  # Adjust based on the EV model you want to simulate
DEFAULT_SPEED = 30  # km/h for travel time estimation on edges without speed data
DEFAULT_KWH_PER_KM =  0.16125 # Average energy consumption in kWh per km (tune to your use case)

MAXIMUM_EXPLORED_PATHES_VISUAL=100


def solve(start_address, goal_address, strategy, battery_info,Graph,kwh_per_km):
    
    G = Graph
    print(f"Adding Energy costs : kwh_per_km = {kwh_per_km} ")
    _add_energy_cost(G,kwh_per_km)

    print(f"Resolving start: {start_address}")
    initial_state = get_nearest_node_from_address(G,start_address)
    
    print(f"Resolved to node: {initial_state}")
    
    print(f"Resolving goal: {goal_address}")
    goal_state = get_nearest_node_from_address(G,goal_address)
    print(f"Resolved to node: {goal_state}")
    

    problem = EV_Problem(initial_state,goal_state,battery_info,DEFAULT_BATTERY_CAPACITY_KWH,G)
    search_engine = GeneralSearch(problem)
    print(f"Starting {strategy} search...")
    solution_node, explored_nodes= search_engine.search(strategy)
    
    if solution_node is None:
        print("ERROR: No path found!")
        return None
    
    print(f"Path found! Nodes explored: {len(explored_nodes)}")
    #================= Path reconstruction and data gathering for visualization==================
    data = search_engine.get_solution_path_data(solution_node)
    explored_paths =  get_explored_paths(G,explored_nodes,MAXIMUM_EXPLORED_PATHES_VISUAL)
    battery_time_graph = data.get("battery_time_graph", [])
    battery_distance_graph = data.get("battery_distance_graph", [])

    formatted_battery_time_graph =  [{"battery_level": item[1], "time": item[0]} for item in battery_time_graph]
    formatted_battery_distance_graph = [{"battery_level": item[1], "distance_km": item[0]} for item in battery_distance_graph]
    total_battery_consumed_kwh = data.get("total_battery_consumed_kwh", 0.0)
    return{
        
        'path': data.get("solution_path", []),
        'explored_paths':explored_paths,
<<<<<<< Updated upstream
        'total_travel_time_h': solution_node.g,
        'total_distance_km': solution_node.distance_km,
        'total_kwh_used': battery_used_kwh,
        'Battery_Distance_Graph':formatted_battery_distance_graph,
        'Charging_stations' :[],
        'Battery_percentage':battery_info - battery_used_kwh *100 / DEFAULT_BATTERY_CAPACITY_KWH
=======
        'total_ditance_km': data.get("distance_traveled_km", 0.0),
        'Battery_Time_Graph':formatted_battery_time_graph,
        'Battery_Distance_Graph': formatted_battery_distance_graph,
        'Charging_stations' :data.get("chargers_in_path", []),
        'total_kwh_used': total_battery_consumed_kwh,

>>>>>>> Stashed changes
        } # for now


def get_explored_paths(G,explored_nodes,max_paths) -> list[list[list[float, float]]]:
    explored_paths: list[list[list[float, float]]] = []
    i = 0

    for node in explored_nodes:
        nodes = []
        current = node
        while current is not None:
            nodes.append(current.state_id)
            current = current.parent
        nodes.reverse()

        coords = []
        for j in range(len(nodes) - 1):
            u, v = nodes[j], nodes[j + 1]
            edge_data = G.get_edge_data(u, v)
            if edge_data is None:
                continue
            data = edge_data[min(edge_data)]

            if "geometry" in data:
                points = [[lat, lon] for lon, lat in data["geometry"].coords]
            else:
                u_data = G.nodes[u]
                v_data = G.nodes[v]
                points = [[u_data["y"], u_data["x"]], [v_data["y"], v_data["x"]]]

            if coords and points[0] == coords[-1]:
                points = points[1:]

            coords.extend(points)

        if not coords:
            continue

        parent_found = False
        for p in explored_paths:
            if coords[0] == p[-1]:
                p.extend(coords[1:])
                parent_found = True
                break

        if not parent_found:
            explored_paths.append(coords)
            i += 1
            if i >= max_paths:
                break

    return explored_paths
if __name__ == "__main__":
<<<<<<< Updated upstream
    G= ox.load_graphml("Data/tunisia_major.graphml")
    result = solve("Avenue Habib Bourguiba, Tunis, Tunisia","Sidi Mansour, Sfax, Tunisia","A*",100,G,0.16125)
=======
    print("Loading graph...")
    G= ox.load_graphml("Data/algeria_roads.graphml")
    print("Graph loaded.")
    result = solve("Algiers, Sidi M'Hamed District, Algiers, 16000, Algeria","Annaba, Annaba District, Annaba, 23000, Algeria","A*",100,G,DEFAULT_KWH_PER_KM)
>>>>>>> Stashed changes
    if result:
        print(f"Path: {len(result['path'])} nodes")
        print(f"Travel Time: {result['total_travel_time_h']:.2f} h")
        print(f"Distance: {result['total_distance_km']:.2f} km")
        print(f"Energy: {result['total_kwh_used']:.2f} kWh")
        print(f"Battery: {result['Battery_percentage']:.1f}%")
        print(f"trip duration (s): {result['Battery_Time_Graph'][-1]['time'] / 3600:.2f} hours")
        print(f"Charging Stations in Path: {result['Charging_stations']}")
    else:
        print("No path found")
        
        

    
        