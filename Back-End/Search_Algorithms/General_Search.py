import sys
import os

# This adds the folder ABOVE your current folder to the search path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import queue
from Core_Modules.Node import Node
from Core_Modules.EV_Porblem import EV_Problem
from Core_Modules.EVGraph import get_node_coords


class General_Serach:

    def __init__(self, problem: EV_Problem):
        self.use_cost = None
        self.use_heuristic = None
        self.problem = problem
        



    def set_frontier(self, serach_strategy: str):

        frontier = None
        match serach_strategy:
            case "BFS":
                frontier = queue.Queue()
                self.use_cost = True
                self.use_heuristic = False

            case "Greedy":
                frontier = queue.PriorityQueue()
                self.use_cost = False
                self.use_heuristic = True

            case "A*":
                frontier = queue.PriorityQueue()
                self.use_cost = True
                self.use_heuristic = True
            case _:
                raise ValueError("Unsupported search strategy: " + serach_strategy)

        return frontier

    
    
    def search(self, search_strategy):
        frontier = self.set_frontier(search_strategy)
        explored = set()
        initial_node =  Node(self.problem.initial_state,self.problem.BATTERY_LEVEL)
        frontier.put(initial_node)

        while not frontier.empty():
            current: Node = frontier.get()

            if self.problem.is_goal(current.state_id):
                return current  # reconstruct path via parent pointers

            if current in explored:
                continue
            explored.add(current)

            for neighbour in self.problem.expand_node(current, self.use_cost, self.use_heuristic):
                
                if neighbour in explored:
                    continue
                else:
                    frontier.put(neighbour)

        return None  # no path found

    def get_solution_path(self,solution_node: Node) -> list[list[str,str]]:
        """
        returns the constructed path in list of lists [[lat,lon]].
        """
        path = []
        current = solution_node
        while current is not None:
            lat, lon = get_node_coords(self.problem.Graph, current.state_id)
            path.append([lat, lon])
            current = current.parent
        return list(reversed(path))
