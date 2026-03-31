class Node:
    def __init__(self, state,Battery_Level, parent=None, action=None, g=0, f=0):
        self.state = state
        self.parent = parent
        self.action = action
        self.Battery_level=Battery_Level
        self.g = g  # Cumulative cost from start to this node
        self.f = f  # Evaluation cost (g + heuristic if applicable)
        
        if parent is None:
            self.depth = 0
        else:
            self.depth = parent.depth + 1
            
    def __hash__(self):
        if isinstance(self.state, list):
            state_tuple = tuple([tuple(row) for row in self.state])
            return hash(state_tuple)
    def __eq__(self,other):
        return isinstance(other, Node) and self.state==other.state
    def __gt__(self,other):
        return isinstance(other,Node) and self.f > other.f