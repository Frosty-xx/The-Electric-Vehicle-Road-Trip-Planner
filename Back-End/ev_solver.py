import osmnx as ox
from Core_Modules.EVGraph import get_nearest_node_from_address , _add_energy_cost
from Core_Modules.EV_Porblem import EV_Problem
from Search_Algorithms.General_Search import GeneralSearch 

DEFAULT_BATTERY_CAPACITY_KWH = 77.4  # Adjust based on the EV model you want to simulate
DEFAULT_SPEED = 30  # km/h for travel time estimation on edges without speed data


MAXIMUM_EXPLORED_PATHES_VISUAL=500


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
    successful_path,battery_distance_graph = search_engine.get_solution_path_battery_graph(solution_node)
    explored_paths =  get_explored_paths(G,explored_nodes,MAXIMUM_EXPLORED_PATHES_VISUAL)
    battery_used_kwh = DEFAULT_BATTERY_CAPACITY_KWH - solution_node.battery_kwh
    
    formatted_battery_distance_graph =  [{"battery_level": item[1], "distance": item[0]} for item in battery_distance_graph]
    
    return{
        
        'path': successful_path,
        'explored_paths':explored_paths,
        'total_ditance_km': solution_node.g,
        'total_kwh_used': battery_used_kwh,
        'Battery_Distance_Graph':formatted_battery_distance_graph,
        'Charging_stations' :[],
        'Battery_percentage':battery_info - battery_used_kwh *100 / DEFAULT_BATTERY_CAPACITY_KWH
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
    G= ox.load_graphml("Data/tunisia_major.graphml")
    result = solve("Avenue Habib Bourguiba, Tunis, Tunisia","Sidi Mansour, Sfax, Tunisia","A*",100,)
    if result:
        print(f"Path: {len(result['path'])} nodes")
        print(f"Distance: {result['total_ditance_km']:.2f} km")
        print(f"Energy: {result['total_kwh_used']:.2f} kWh")
        print(f"Battery: {result['Battery_percentage']:.1f}%")
    else:
        print("No path found")
        
        

    
        