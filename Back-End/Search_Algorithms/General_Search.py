"""Search algorithms for Electric Vehicle route planning.

This module implements various graph search strategies (BFS, Greedy, A*) to find
optimal paths for electric vehicles considering battery constraints and charging stations.
"""

import sys
import os

# This adds the folder ABOVE your current folder to the search path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import queue
from Core_Modules.Node import Node
from Core_Modules.EV_Porblem import EV_Problem





class GeneralSearch:
    """Implements general graph search algorithms for EV route planning.
    
    Supports multiple search strategies (BFS, Greedy, A*) to find paths
    from a starting location to a destination while respecting battery constraints.
    
    Attributes:
        use_cost (bool): Whether to use path cost in the search algorithm.
        use_heuristic (bool): Whether to use heuristic (estimated cost to goal).
        problem (EV_Problem): The EV routing problem to solve.
    """

    def __init__(self, problem: EV_Problem):
        """Initialize the search algorithm with an EV problem.
        
        Args:
            problem (EV_Problem): The electric vehicle routing problem instance.
        """
        self.use_cost = None
        self.use_heuristic = None
        self.problem = problem
        



    def set_frontier(self, search_strategy: str):
        """Initialize the search frontier based on the selected strategy.
        
        Args:
            search_strategy (str): The search algorithm to use.
                - "BFS": Breadth-First Search (explores nodes level by level)
                - "Greedy": Greedy Best-First (uses heuristic to estimate proximity to goal)
                - "A*": A* Search (combines actual cost and heuristic estimate)
        
        Returns:
            queue.Queue or queue.PriorityQueue: The appropriate frontier data structure.
        
        Raises:
            ValueError: If an unsupported search strategy is provided.
        """
        frontier = None
        match search_strategy:
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
                raise ValueError("Unsupported search strategy: " + search_strategy)

        return frontier

    
    
    def search(self, search_strategy) -> tuple[Node,set[Node]]:
        """Execute the search algorithm to find a path from start to goal.
        
        This method expands nodes from the frontier, tracking explored nodes to avoid
        revisiting them. The search terminates when the goal is found or the frontier
        is exhausted.
        
        Args:
            search_strategy (str): The search algorithm to use ("BFS", "Greedy", or "A*").
        
        Returns:
            Node: The goal node with parent pointers reconstructing the path, or None if no path exists.
        """
        frontier = self.set_frontier(search_strategy)
        explored = set()
        
        # Calculate initial battery level in kWh
        initial_battery_kwh = self.problem.initial_batery_percentage * self.problem.battery_capacity / 100
        initial_node = Node(self.problem.initial_state, initial_battery_kwh)
        frontier.put(initial_node)

        while not frontier.empty():
            current: Node = frontier.get()

            # Check if goal state is reached
            if self.problem.is_goal(current.state_id):
                return current , explored  # Goal found; reconstruct path via parent pointers + explored set for showcasing

            # Skip if already explored
            if current in explored:
                continue
            explored.add(current)

            # Expand current node and add unvisited neighbors to frontier
            for neighbour in self.problem.expand_node(current, self.use_cost, self.use_heuristic):
                if neighbour not in explored:
                    frontier.put(neighbour)

        return None,explored  # No path found

    def get_solution_path(self, solution_node: Node) -> list[list[float, float]]:
        # Collect nodes from goal to start
        nodes = []
        current = solution_node
        while current is not None:
            nodes.append(current.state_id)
            current = current.parent
        nodes.reverse()  # now start → goal

        # Build coordinate list using edge geometry
        G = self.problem.Graph
        coords = []

        for i in range(len(nodes) - 1):
            u, v = nodes[i], nodes[i + 1]
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

            # Avoid duplicate junction points
            if coords and points[0] == coords[-1]:
                points = points[1:]

            coords.extend(points)

        return coords





