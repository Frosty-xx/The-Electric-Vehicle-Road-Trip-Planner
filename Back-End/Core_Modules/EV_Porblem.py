"""EV routing problem definition for graph search algorithms.

Defines the EV_Problem class that represents the routing problem,
including state validation, action expansion, and cost calculations.
"""

import sys
import os
import math

# This adds the folder ABOVE your current folder to the search path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


from networkx import MultiDiGraph
from Core_Modules.EVGraph import get_node_coords, get_edge_kwh_cost, get_edge_trvel_time
from Core_Modules.Node import Node

LOW_BATTERY_THRESHOLD_KWH = 14.8  # tune to your use case (for 20% of 74 kWh capacity)
AVG_SPEED = 90  # average speed in haighways and routes
# State is a node_id in the city graph


# haversine distance.
def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Straight-line distance in km between two (lat, lon) points.
    """
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    a = (
        math.sin(math.radians(lat2 - lat1) / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    )
    return R * 2 * math.asin(math.sqrt(a))


class EV_Problem:

    def __init__(
        self,
        initial_state,
        goal_state,
        initial_batery_percentage,
        battery_capacity,
        graph: MultiDiGraph,
    ):
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
        print(
            f"[EV_Problem] Found {len(self._charger_nodes)} charging stations in graph."
        )

    # ------------------------------------------------------------------

    @staticmethod
    def _parse_bool(val) -> bool:
        """GraphML loads booleans as strings — handle both."""
        if isinstance(val, str):
            return val.strip().lower() == "true"
        return bool(val)

    def _node_float(self, G, node_id, key, default=0.0) -> float:
        """GraphML loads all attributes as strings — safely cast to float."""
        val = G.nodes[node_id].get(key, default)
        try:
            return float(val)
        except (TypeError, ValueError):
            return float(default)

    def _edge_speed_kph(self, u, v) -> float:
        """Get speed_kph for the edge u->v, using min over parallel edges."""
        speeds = [d.get("speed_kph", 50.0) for d in self.Graph[u][v].values()]
        return min(speeds)  # Conservative: use slowest speed on parallel edges

    # ------------------------------------------------------------------

    def is_goal(self, state):
        return state == self.goal_state

    def get_valid_actions(self, state):
        moves = []
        for action in self.Graph.successors(state):
            travel_time = get_edge_trvel_time(self.Graph, state, action)
            kws_cost = get_edge_kwh_cost(self.Graph, state, action)
            moves.append((action, travel_time, kws_cost))
        return moves

    def heuristic(
        slef, lat1: float, lon1: float, lat2: float, lon2: float, speed=AVG_SPEED
    ):
        return (
            haversine_km(lat1, lon1, lat2, lon2) / speed * 3600
        )  # convert hours to seconds for consistent cost units

    def get_total_cost(
        self, g, coordinates, use_cost, use_heuristic, override_target=None
    ):
        if override_target:
            goal_coords = override_target
        else:
            goal_coords = get_node_coords(self.Graph, self.goal_state)
        return (g if use_cost else 0) + (
            self.heuristic(
                coordinates[0], coordinates[1], goal_coords[0], goal_coords[1]
            )
            if use_heuristic
            else 0
        )

    # ------------------------------------------------------------------

    def _nearest_reachable_charger(self, from_node, battery_kwh):
        """Return best charger reachable within remaining battery.

        For Greedy search, prefer fast chargers even if slightly farther.
        """
        bucket = int(battery_kwh // 5)  # 5 kWh buckets for caching
        cache_key = (from_node, bucket)
        if cache_key in self._charger_cache:
            return self._charger_cache[cache_key]

        # Max range in km given current battery
        max_range_km = (
            battery_kwh / 0.16125
        ) * 0.75  # use 75% to be conservative  Convert kWh to km using average consumption
        from_coords = get_node_coords(self.Graph, from_node)

        # Find ALL reachable chargers within battery range
        candidate_chargers = []
        for nid in self._charger_nodes:
            # Check if reachable within battery (using straight-line estimate)
            coords = get_node_coords(self.Graph, nid)
            h_dist = haversine_km(from_coords[0], from_coords[1], coords[0], coords[1])
            if h_dist <= max_range_km:
                charger_kw = self._node_float(
                    self.Graph, nid, "charger_kw", default=7.0
                )
                candidate_chargers.append((nid, h_dist, charger_kw))

        if not candidate_chargers:
            self._charger_cache[cache_key] = None
            return None

        # Score chargers: prefer fast chargers (lower score = better)
        # Formula: score = distance_km * (1 / charger_kw_factor)
        # Fast chargers (>=50 kW) get 0.5x multiplier, slow chargers get 1x
        best_charger = None
        best_score = float("inf")

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

    def expand_node(
    self,
    node_to_expand: Node,
    use_cost=True,
    use_heuristic=False,
    use_constraints=True,
    is_greedy=False,
) -> list[Node]:
    
        current_cost = node_to_expand.g
        current_distance = node_to_expand.distance_km
        children = []

        for child_id, step_cost, battery_consumed in self.get_valid_actions(
            state=node_to_expand.state_id
        ):
            # 1. Calculate battery after travel
            new_battery = node_to_expand.battery_kwh - battery_consumed

            # Hard constraint — prune dead-battery moves
            if new_battery <= 0:
                continue

            cumulative_cost = current_cost + step_cost
            
            # 2. Handle Charging Logic BEFORE final f_score
            # This ensures the heuristic knows we are at full capacity
            is_charger = self._parse_bool(
                self.Graph.nodes[child_id].get("is_charging_station", False)
            )
            threshold = LOW_BATTERY_THRESHOLD_KWH if not is_greedy else 3.7

            # Apply charging if at a station and battery is low (or constraints off)
            if is_charger and (new_battery < threshold or not use_constraints):
                charger_kw = self._node_float(
                    self.Graph, child_id, "charger_kw", default=7.0
                )
                energy_needed = self.battery_capacity - new_battery
                
                # Update state to full battery
                new_battery = self.battery_capacity
                
                # Update cost to include charging time
                charging_time_h = energy_needed / max(charger_kw, 0.1)
                cumulative_cost += charging_time_h * 3600
                
                # Optional: penalty for slow chargers in heuristic
                # Note: This is now applied to cumulative_cost or f_score accurately
                if use_heuristic and charger_kw < 50:
                    cumulative_cost += (charging_time_h * 0.5) # Soft constraint penalty

            # 3. Calculate Heuristic Target
            child_coords = get_node_coords(self.Graph, child_id)
            if (
                new_battery < threshold
                and use_heuristic
                and use_constraints
            ):
                target_node = self._nearest_reachable_charger(child_id, new_battery)
                if target_node is None:
                    continue  # Prune stranded branch
                target_coords = get_node_coords(self.Graph, target_node)
            else:
                target_coords = None  # get_total_cost will default to goal

            # 4. Final Score Calculation
            f_score = self.get_total_cost(
                cumulative_cost,
                child_coords,
                use_cost,
                use_heuristic,
                override_target=target_coords,
            )

            # 5. Create Node
            # Args: state_id, battery, parent_node, action, g_score, f_score
            children.append(
                Node(
                    child_id,           # Current State
                    new_battery,        # Current Battery (potentially recharged)
                    node_to_expand,     # Correct Parent Assignment
                    f"move_to_{child_id}", # Descriptive Action (instead of just ID)
                    cumulative_cost,    # G-score
                    f_score,            # F-score
                )
            )

        return children
