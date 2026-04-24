"""EV routing problem definition for graph search algorithms.

Defines the EV_Problem class that represents the routing problem,
including state validation, action expansion, and cost calculations.
"""

import sys
import os

# This adds the folder ABOVE your current folder to the search path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from networkx import MultiDiGraph
from Core_Modules.EVGraph import get_edge_distance_km, get_node_coords, haversine_km, get_edge_kwh_cost
from Core_Modules.Node import Node

# State is a node_id in the city graph
# Heuristic used: Haversine distance (straight-line distance to goal)

class EV_Problem:
    """Represents an electric vehicle routing problem.
    
    Defines the problem space including initial state, goal state, battery capacity,
    and the road network graph. Provides methods to check goal state, get valid actions,
    and expand nodes for search algorithms.
    
    Attributes:
        initial_state: Starting node ID in the graph.
        goal_state: Target node ID.
        battery_capacity: Max battery capacity in kWh.
        initial_batery_percentage: Battery level at start (0-100).
        Graph: The road network as a MultiDiGraph.
    """
    
    def __init__(self, initial_state, goal_state, initial_batery_percentage, battery_capacity, graph: MultiDiGraph):
        """Initialize the EV routing problem."""
        self.initial_state = initial_state
        self.goal_state = goal_state
        self.battery_capacity = battery_capacity
        self.Graph = graph
        self.initial_batery_percentage = initial_batery_percentage

    
    def is_goal(self,state):
        return state==self.goal_state
    
    
    def get_valid_actions(self, state):
        """Get all valid next moves from the current state.
        
        Returns list of tuples: (next_node_id, distance_km)
        """
        moves = []
        for action in self.Graph.successors(state):
            moves.append((action, get_edge_distance_km(self.Graph, state, action)))
        return moves
    
    
    def get_total_cost(self, g, coordinates, use_cost, use_heuristic):
        """Calculate f-score for a node.
        
        f = g + h, where:
        - g: actual cost from start to current node
        - h: estimated cost from current node to goal (heuristic)
        """
        goal_coordinates = get_node_coords(self.Graph, self.goal_state)
        
        return ((g if use_cost else 0) + 
                (haversine_km(coordinates[0], coordinates[1], goal_coordinates[0], goal_coordinates[1]) 
                 if use_heuristic else 0))
    
    
    def expand_node(self, node_to_expand: Node, use_cost=True, use_heuristic=False) -> list[Node]:
        """Expand a node by generating all valid child nodes.
        
        For each valid action from the current node, creates a child node with:
        - Updated position and battery level
        - Path cost from start
        - f-score for search algorithm
        
        Returns list of child Node objects.
        """
        current_cost = node_to_expand.g
        children = []
        
        # Generate child nodes for each valid action
        for (child_id, step_cost) in self.get_valid_actions(state=node_to_expand.state_id):
            
            # Get coordinates and costs for the child node
            child_coordinates = get_node_coords(self.Graph, child_id)
            cumulative_cost = current_cost + step_cost
            f_score = self.get_total_cost(cumulative_cost, child_coordinates, use_cost, use_heuristic)

            # Calculate battery remaining after traveling to child node
            battery_consumed_kwh = get_edge_kwh_cost(self.Graph, node_to_expand.state_id, child_id)
            new_battery_level = node_to_expand.battery_kwh - battery_consumed_kwh

            # Create and add the child node
            children.append(Node(child_id, new_battery_level, node_to_expand, child_id, cumulative_cost, f_score))
    
        return children

        
        
        
