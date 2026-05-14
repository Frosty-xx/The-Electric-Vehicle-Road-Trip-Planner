class Node:
    def __init__(self, state_id,battery_kwh, parent=None, action=None, g=0, f=0, distance_km=0):
        self.state_id = state_id
        self.battery_kwh=battery_kwh 

        self.parent = parent
        self.action = action
        self.g = g  # Cumulative cost from start to this node (now in hours)
        self.f = f  # Evaluation cost (g + heuristic if applicable)
        self.distance_km = distance_km  # Cumulative distance in km (for display)
        
        if parent is None:
            self.depth = 0
        else:
            self.depth = parent.depth + 1
            
    def __hash__(self):
        # Bucket battery into 5 kWh bands so nearby states are still merged
        battery_bucket = round(self.battery_kwh / 5)
        return hash((self.state_id, battery_bucket))

    def __eq__(self, other):
        return  (isinstance(other, Node) and
                self.state_id == other.state_id and
                round(self.battery_kwh / 5) == round(other.battery_kwh / 5))
    def __gt__(self,other):
        return isinstance(other,Node) and self.f > other.f

    
    def print_node(self):
        print("Action:", self.action, "| Depth:", self.depth)
        
