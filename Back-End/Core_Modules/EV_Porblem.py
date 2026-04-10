import sys
import os

# This adds the folder ABOVE your current folder to the search path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from networkx import MultiDiGraph
from Core_Modules.EVGraph import get_edge_distance_km , get_node_coords , haversine_km
from Core_Modules.Node import Node


# INFO : state is a node_id in the the city Graph.
# Current Heuristic Used: Haversine Distance.

class EV_Problem:
    def __init__(self, initial_state, goal_state,BATTERY_LEVEL, graph:MultiDiGraph):

        self.initial_state = initial_state
        self.goal_state = goal_state
        self.Graph = graph
        
        self.BATTERY_LEVEL = BATTERY_LEVEL

    
    def is_goal(self,state):
        return state==self.goal_state
    
    
    def get_valid_actions(self,state):
        moves=[]
        for action in self.Graph.successors(state):
            moves.append((action,get_edge_distance_km(self.Graph,state,action)))
        return moves
    
    def get_total_cost(self,g,coordinates,use_cost,use_heuristic):
        goal_coordinates = get_node_coords(self.Graph,self.goal_state)
        
        return ((g if use_cost else 0 ) + (haversine_km(coordinates[0],coordinates[1],goal_coordinates[0],goal_coordinates[1]) if use_heuristic else 0))
    
    
    def expand_node(self,node_to_expand:Node,use_cost=True,use_heuristic=False)->list[Node]:
        
        
        current_cost=node_to_expand.g
    
        children=[]
        
        for(child_id , step_cost) in self.get_valid_actions(state= node_to_expand.state_id):
        
            child_coordinates = get_node_coords(self.Graph,child_id)
        
            cumulative_cost= current_cost + step_cost
        
            f_score = self.get_total_cost(cumulative_cost,child_coordinates,use_cost,use_heuristic)
        
            children.append(Node(child_id,self.BATTERY_LEVEL,node_to_expand,child_id,cumulative_cost,f_score))
    
    
        return children

        
        
        
