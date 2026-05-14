"""EV routing problem definition for graph search algorithms.

Defines the EV_Problem class that represents the routing problem,
including state validation, action expansion, and cost calculations.
"""

import sys
import os

# This adds the folder ABOVE your current folder to the search path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from networkx import MultiDiGraph
from Core_Modules.EVGraph import get_edge_distance_km, get_node_coords, haversine_km, get_edge_kwh_cost,is_charging_station
from Core_Modules.Node import Node

LOW_BATTERY_THRESHOLD_KWH = 10.0
# State is a node_id in the city graph
# Heuristic used: Haversine distance (straight-line distance to goal)


class EV_Problem:

    def __init__(self, initial_state, goal_state, initial_batery_percentage,
                 battery_capacity, graph: MultiDiGraph):
        self.initial_state = initial_state
        self.goal_state = goal_state
        self.battery_capacity = battery_capacity
        self.Graph = graph
        self.initial_batery_percentage = initial_batery_percentage
        self._charger_cache = {}  # (from_node, battery_bucket) → charger_node | None
        self._charger_nodes_sorted = None  # built lazily on first call

        # Pre-compute charger list ONCE — avoids O(n) scan on every expansion
        self._charger_nodes = [
            node_id
            for node_id, data in graph.nodes(data=True)
            if self._parse_bool(data.get("is_charging_station", False))
        ]
        print(f"[EV_Problem] Found {len(self._charger_nodes)} charging stations in graph.")

    # ------------------------------------------------------------------

    @staticmethod
    def _parse_bool(val) -> bool:
        """GraphML loads booleans as strings — handle both."""
        if isinstance(val, str):
            return val.strip().lower() == "true"
        return bool(val)

    
    def _node_float(self,G, node_id, key, default=0.0) -> float:
        """GraphML loads all attributes as strings — safely cast to float."""
        val = G.nodes[node_id].get(key, default)
        try:
            return float(val)
        except (TypeError, ValueError):
            return float(default)

    # ------------------------------------------------------------------

    def is_goal(self, state):
        return state == self.goal_state

    def get_valid_actions(self, state):
        moves = []
        for action in self.Graph.successors(state):
            moves.append((action, get_edge_distance_km(self.Graph, state, action)))
        return moves

    def get_total_cost(self, g, coordinates, use_cost, use_heuristic,
                       override_target=None):
        if override_target:
            goal_coords = override_target
        else:
            goal_coords = get_node_coords(self.Graph, self.goal_state)
        return (
            (g if use_cost else 0) +
            (haversine_km(coordinates[0], coordinates[1],
                          goal_coords[0], goal_coords[1])
             if use_heuristic else 0)
        )

    # ------------------------------------------------------------------

    LOW_BATTERY_KWH = 5.0   # tune to your use case


    def _nearest_reachable_charger(self, from_node, battery_kwh):
        """Return best charger reachable within remaining battery.
        
        For Greedy search, prefer fast chargers even if slightly farther.
        """
        bucket = int(battery_kwh // 1)
        cache_key = (from_node, bucket)
        if cache_key in self._charger_cache:
            return self._charger_cache[cache_key]

        # Max range in km given current battery
        max_range_km = battery_kwh / 0.16125
        from_coords = get_node_coords(self.Graph, from_node)

        # Find ALL reachable chargers within battery range
        candidate_chargers = []
        for nid in self._charger_nodes:
            # Check if reachable within battery (using straight-line estimate)
            coords = get_node_coords(self.Graph, nid)
            h_dist = haversine_km(from_coords[0], from_coords[1], coords[0], coords[1])
            if h_dist <= max_range_km:
                charger_kw = self._node_float(self.Graph, nid, "charger_kw", default=7.0)
                candidate_chargers.append((nid, h_dist, charger_kw))

        if not candidate_chargers:
            self._charger_cache[cache_key] = None
            return None

        # Score chargers: prefer fast chargers (lower score = better)
        # Formula: score = distance_km * (1 / charger_kw_factor)
        # Fast chargers (>=50 kW) get 0.5x multiplier, slow chargers get 1x
        best_charger = None
        best_score = float('inf')
        
        for nid, dist, kw in candidate_chargers:
            # Fast charger bonus: reduce effective distance for fast chargers
            if kw >= 50:
                effective_dist = dist * 0.5  # Fast chargers appear twice as close
            else:
                effective_dist = dist * 1.0  # Slow chargers at actual distance
            
            if effective_dist < best_score:
                best_score = effective_dist
                best_charger = nid

        self._charger_cache[cache_key] = best_charger
        return best_charger

    def expand_node(self, node_to_expand: Node,
                    use_cost=True, use_heuristic=False) -> list[Node]:
        current_cost = node_to_expand.g
        children = []

        for (child_id, step_cost) in self.get_valid_actions(
                state=node_to_expand.state_id):

            battery_consumed = get_edge_kwh_cost(
                self.Graph, node_to_expand.state_id, child_id)
            new_battery = node_to_expand.battery_kwh - battery_consumed

            # Hard constraint — prune dead-battery moves
            if new_battery <= 0:
                continue

            child_coords = get_node_coords(self.Graph, child_id)
            cumulative_cost = current_cost + step_cost

            if node_to_expand.battery_kwh < self.LOW_BATTERY_KWH:
                target_node = self._nearest_reachable_charger(child_id, new_battery)
                if target_node is None:
                    continue  # truly stranded — prune this branch
                target_coords = get_node_coords(self.Graph, target_node)
            else:
                target_coords = None  # get_total_cost will use goal

            f_score = self.get_total_cost(
                cumulative_cost, child_coords,
                use_cost, use_heuristic,
                override_target=target_coords)

            # If child IS a charger — recharge and apply soft constraint
            if self._parse_bool(
                    self.Graph.nodes[child_id].get("is_charging_station", False)):
                charger_kw = self._node_float(
                    self.Graph, child_id, "charger_kw", default=7.0)
                energy_needed = self.battery_capacity - new_battery
                new_battery = self.battery_capacity  # fully charged

                # Soft constraint: slow charger adds a time penalty to f-score
                if use_heuristic and charger_kw < 50:
                    charging_time_h = energy_needed / max(charger_kw, 0.1)
                    f_score += charging_time_h * 30  # 30 km-equivalent per hour

            children.append(Node(child_id, new_battery, node_to_expand,
                                 child_id, cumulative_cost, f_score))

        return children