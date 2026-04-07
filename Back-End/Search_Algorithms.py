
from EVGraph import build_graph,get_or_build_graph, nearest_node,get_node_coords,get_node_id_from_address,haversine_km,get_edge_distance_km
import queue
from Node import Node
from networkx import MultiDiGraph



G = get_or_build_graph(cache_path="lyon_test_cache.graphml",place="Lyon,France")

BATTERY_LEVEL=80

initial_address="Rue Vauban Lyon"
goal_address = "Jardin Botanique de Lyon"


initial_node_id = get_node_id_from_address(initial_address,G)
goal_node_id=get_node_id_from_address(goal_address,G)

initial_node:Node = Node(initial_node_id,80)


def goal_test(state_id):
    return state_id == goal_node_id


def get_total_cost(g:float,coordinates,use_cost,use_heuristic):
    
    goal_coordinates = get_node_coords(G,goal_node_id)

    
    return ((g if use_cost else 0 ) + (haversine_km(coordinates[0],coordinates[1],goal_coordinates[0],goal_coordinates[1]) if use_heuristic else 0))
    
    
def expand_Node(node_to_expand:Node,use_cost:bool=True,use_heuristic:bool=True)-> list[Node]:
    
    current_cost=node_to_expand.g
    
    children=[]
    for(child_id , step_cost) in get_available_moves(Graph=G,node_id = node_to_expand.state_id):
        
        child_coordinates = get_node_coords(G,child_id)
        
        cumulative_cost= current_cost + step_cost
        
        f_score = get_total_cost(cumulative_cost,child_coordinates,use_cost,use_heuristic)
        
        children.append(Node(child_id,BATTERY_LEVEL,node_to_expand,child_id,cumulative_cost,f_score))
    
    
    return children
    
    
    

def get_available_moves(Graph:MultiDiGraph,node_id):

    moves=[]
    for n_id in Graph.successors(node_id):
        moves.append((n_id,get_edge_distance_km(G,node_id,n_id)))
    return moves;
        

def get_solution_path(node:Node)->list[tuple]:
    """
        returns the constructed path in list of [(lat,lon)].
    """
    
    path=[]
    current=node
    while current is not None:
        lat,lon = get_node_coords(G,current.state_id)
        path.append((lat, lon))
        current= current.parent
    return list(reversed(path))



def Greedy_Search():
    frontier = queue.PriorityQueue()
    visited = set()

    frontier.put(initial_node)

    while not frontier.empty():
        current:Node = frontier.get()

        if goal_test(current.state_id):
            return current  # reconstruct path via parent pointers

        if current in visited:
            continue
        visited.add(current)

        for neighbour in expand_Node(current,False,True):
            if neighbour in visited:
                continue
            else:
                frontier.put(neighbour)

    return None  # no path found  




if __name__ == "__main__":
    #initial Greedy Test (Road only no battery or optimization).
    
    goal_node = Greedy_Search()
    path=get_solution_path(goal_node)
    
    print(f"\n========================= path from {initial_address} to {goal_address}:=========================")
    print(path)

    


    