

class Node:
    def __init__(self, state_id,battery_kwh, parent=None, action=None, g=0, f=0):
        self.state_id = state_id
        self.battery_kwh=battery_kwh 

        self.parent = parent
        self.action = action
        self.g = g  # Cumulative cost from start to this node
        self.f = f  # Evaluation cost (g + heuristic if applicable)
        
        if parent is None:
            self.depth = 0
        else:
            self.depth = parent.depth + 1
            
    def __hash__(self):
        return hash((self.state_id))
    
    def __eq__(self,other):
        #Add Battery !important
        return isinstance(other, Node) and self.state_id==other.state_id 
    
    def __gt__(self,other):
        return isinstance(other,Node) and self.f > other.f

    
    def print_node(self):
        print("Action:", self.action, "| Depth:", self.depth)
        
