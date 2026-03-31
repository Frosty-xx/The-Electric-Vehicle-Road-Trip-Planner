class Node:
    def __init__(self, state,battery_level, parent=None, action=None, g=0, f=0):
        self.state = state
        self.battery_level=battery_level
        self.parent = parent
        self.action = action
        self.g = g  # Cumulative cost from start to this node
        self.f = f  # Evaluation cost (g + heuristic if applicable)
        
        if parent is None:
            self.depth = 0
        else:
            self.depth = parent.depth + 1
            
    def __hash__(self):
        return hash((self.state, round(self.battery_level, 2)))
    
    def __eq__(self,other):
        return isinstance(other, Node) and self.state==other.state and self.battery_level==other.battery_level
    
    def __gt__(self,other):
        return isinstance(other,Node) and self.f > other.f