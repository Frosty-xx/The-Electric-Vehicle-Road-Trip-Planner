import sys
import os
import osmnx as ox
# This adds the folder ABOVE your current folder to the search path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Core_Modules.EVGraph import get_nearest_node_from_address 
from Core_Modules.EV_Porblem import EV_Problem
from Search_Algorithms.General_Search import GeneralSearch

# Directory of the current file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GRAPH_PATH = os.path.join(BASE_DIR, "..", "Data", "tunisia.graphml")

DEFAULT_BATTERY_CAPACITY_KWH = 77.4  # Adjust based on the EV model you want to simulate
DEFAULT_SPEED = 30  # km/h for travel time estimation on edges without speed data
INIT_BATTERY_LEVEL_PERCENTAGE= 100
INITIAL_ADRESS = "Avenue Habib Bourguiba, Tunis, Tunisia"
GOAL_ADRESS = "Sidi Mansour, Sfax, Tunisia"


if __name__ == "__main__":
    

    
    
    print("loading Graph")
    G = ox.load_graphml(GRAPH_PATH)
    print("Done Loading")
    initial_state = get_nearest_node_from_address(G,INITIAL_ADRESS)
    goal_state = get_nearest_node_from_address(G,GOAL_ADRESS)
    print(goal_state)
    print(initial_state)
    strategy = "A*"
    

    problem = EV_Problem(initial_state,goal_state,INIT_BATTERY_LEVEL_PERCENTAGE,DEFAULT_BATTERY_CAPACITY_KWH,G)
    print("searching")
    serach_instance = GeneralSearch(problem)

    solution_node = serach_instance.search(search_strategy=strategy)[0]

    Path = serach_instance.get_solution_path(solution_node)
    

    print(f"\n========================= path from {INITIAL_ADRESS} to {GOAL_ADRESS} ({strategy}):=========================")
    print()
    print(f"Constructed Path: {Path}")
    print(f"Distance Traveled: {solution_node.g} KM , Batter_Level:{solution_node.battery_kwh / problem.battery_capacity * 100:.2f}%")

