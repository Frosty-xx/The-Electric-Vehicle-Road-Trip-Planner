import sys
import os

# This adds the folder ABOVE your current folder to the search path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Core_Modules.EVGraph import get_node_id_from_address, get_or_build_graph
from Core_Modules.EV_Porblem import EV_Problem
from Search_Algorithms.General_Search import General_Serach
from Core_Modules.Node import Node

# Directory of the current file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GRAPH_PATH = os.path.join(BASE_DIR, "..", "Data", "graph.graphml")

BATTERY_LEVL= 80
INITIAL_ADRESS = "Culture Indoor Lyon"
GOAL_ADRESS = "terrain de Sports Anatole France Lyon"


if __name__ == "__main__":

    G = get_or_build_graph(cache_path=GRAPH_PATH, place="Lyon,France")

    initial_state = get_node_id_from_address(INITIAL_ADRESS, G)
    goal_state = get_node_id_from_address(GOAL_ADRESS,G)
    strategy = "A*"
    
    test_node= Node(goal_state,80)
    problem = EV_Problem(initial_state,goal_state,BATTERY_LEVL,G)

    serach_instance = General_Serach(problem)

    solution_node = serach_instance.search(search_strategy=strategy)

    Path = serach_instance.get_solution_path(solution_node)
    

    print(f"\n========================= path from {INITIAL_ADRESS} to {GOAL_ADRESS} ({strategy}):=========================")
    print()
    print(f"Constructed Path: {Path}")
    print(f"Distance Traveled{solution_node.g} KM")
