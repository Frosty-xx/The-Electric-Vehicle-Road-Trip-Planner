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
DEFAULT_KWH_PER_KM= 0.16125
FAST_CHARGER_KW_THRESHOLD = 50
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


# --- 4b. EV_Problem Class ---

class EV_Problem:
    """
    Formal EV routing problem for graph search.

    Answers three questions the search engine asks on every iteration:
      - get_valid_actions()  : where can I go from here?
      - expand_node()        : what does each move cost and produce?
      - is_goal()            : am I there?

    Extra complexity vs standard shortest-path: battery constraints, charging stops,
    and heuristic redirection toward chargers when range is low.
    """

    def __init__(
        self,
        initial_state: int,
        goal_state: int,
        initial_battery_percentage: float,
        battery_capacity: float,
        graph: MultiDiGraph,
    ):
        self.initial_state  = initial_state
        self.goal_state     = goal_state
        self.battery_capacity = battery_capacity
        self.Graph          = graph
        self.initial_batery_percentage = initial_battery_percentage  # kept for compatibility

        self._charger_cache = {}   # (node, battery_bucket) → nearest charger node

        # Build charger list once — avoids O(n) graph scan on every expansion
        self._charger_nodes = [
            node_id
            for node_id, data in graph.nodes(data=True)
            if self._parse_bool(data.get("is_charging_station", False))
        ]
        print(f"[EV_Problem] Found {len(self._charger_nodes)} charging stations in graph.")

        # Cache goal coordinates for use in expand_node range checks
        goal_data = graph.nodes[goal_state]
        self._goal_coords = (float(goal_data["y"]), float(goal_data["x"]))

    # GraphML saves all attributes as strings; these helpers centralise the casting.

    @staticmethod
    def _parse_bool(val) -> bool:
        """Handle GraphML bool attributes that may come back as the string 'True'."""
        if isinstance(val, str):
            return val.strip().lower() == "true"
        return bool(val)

    def _node_float(self, G: MultiDiGraph, node_id: int, key: str, default: float = 0.0) -> float:
        """Read a node attribute as float, falling back to default on failure."""
        val = G.nodes[node_id].get(key, default)
        try:
            return float(val)
        except (TypeError, ValueError):
            return float(default)

    # ------------------------------------------------------------------
    # Core Problem Interface
    # ------------------------------------------------------------------

    def is_goal(self, state: int) -> bool:
        return state == self.goal_state

    def get_valid_actions(self, state: int) -> list[tuple]:
        """Return (neighbour_id, travel_time_s, energy_kwh) for each reachable neighbour."""
        moves = []
        for neighbour in self.Graph.successors(state):
            travel_time = get_edge_trvel_time(self.Graph, state, neighbour)
            energy_cost = get_edge_kwh_cost(self.Graph, state, neighbour)
            moves.append((neighbour, travel_time, energy_cost))
        return moves

    # ------------------------------------------------------------------
    # Heuristic & f-score
    # ------------------------------------------------------------------

    def heuristic(
        self,
        lat1: float, lon1: float,
        lat2: float, lon2: float,
        speed: float = AVG_SPEED,
    ) -> float:
        """Estimate remaining travel time (seconds) via Haversine + average speed."""
        dist_km = haversine_km(lat1, lon1, lat2, lon2)
        return dist_km / speed * 3600

    def get_total_cost(
        self,
        g: float,
        coordinates: tuple[float, float],
        use_cost: bool,
        use_heuristic: bool,
        override_target: tuple[float, float] = None,
    ) -> float:
        """
        Compute f = g + h.

        override_target lets the heuristic aim at an intermediate charger instead
        of the goal — used when battery is too low to reach the destination directly.
        """
        goal_coords = override_target if override_target else get_node_coords(self.Graph, self.goal_state)

        cost_term      = g if use_cost else 0
        heuristic_term = (
            self.heuristic(coordinates[0], coordinates[1], goal_coords[0], goal_coords[1])
            if use_heuristic else 0
        )
        return cost_term + heuristic_term

    # ------------------------------------------------------------------
    # Charging Station Lookup
    # ------------------------------------------------------------------

    def _nearest_reachable_charger(self, from_node: int, battery_kwh: float) -> int | None:
        """
        Find the best reachable charger given current battery.

        Reachability uses 75% of theoretical max range as a safety margin.
        Fast chargers (≥50 kW) get a 0.5× distance multiplier in scoring —
        a slightly longer detour to a fast charger is almost always worth it.
        Results are cached by (node, 5 kWh battery bucket).
        """
        bucket    = int(battery_kwh // 5)
        cache_key = (from_node, bucket)
        if cache_key in self._charger_cache:
            return self._charger_cache[cache_key]

        max_range_km = (battery_kwh / DEFAULT_KWH_PER_KM) * 0.75
        from_coords  = get_node_coords(self.Graph, from_node)

        candidate_chargers = []
        for nid in self._charger_nodes:
            coords = get_node_coords(self.Graph, nid)
            h_dist = haversine_km(from_coords[0], from_coords[1], coords[0], coords[1])
            if h_dist <= max_range_km:
                charger_kw = self._node_float(self.Graph, nid, "charger_kw", default=7.0)
                candidate_chargers.append((nid, h_dist, charger_kw))

        if not candidate_chargers:
            self._charger_cache[cache_key] = None
            return None

        best_charger, best_score = None, float("inf")
        for nid, dist, kw in candidate_chargers:
            effective_dist = dist * 0.5 if kw >= FAST_CHARGER_KW_THRESHOLD else dist
            if effective_dist < best_score:
                best_score   = effective_dist
                best_charger = nid

        self._charger_cache[cache_key] = best_charger
        return best_charger

    # ------------------------------------------------------------------
    # Node Expansion
    # ------------------------------------------------------------------

    def expand_node(
        self,
        node_to_expand: Node,
        use_cost: bool = True,
        use_heuristic: bool = False,
        use_constraints: bool = True,
        is_greedy: bool = False,
    ) -> list[Node]:
        """
        Generate valid child nodes from the current node.

        For each neighbour, four steps run in order:
          1. Battery feasibility  — prune moves the EV can't afford.
          2. Charging logic       — recharge only if battery can't reach the goal directly.
          3. Heuristic targeting  — redirect toward nearest charger when battery is still low.
          4. f-score computation  — combine g and h per the active strategy.
        """
        current_cost = node_to_expand.g
        children     = []

        # Greedy uses a lower threshold (3.7 kWh) — no cost term means it doesn't penalise
        # detours, so it only charges when nearly empty unlike A*/BFS (14.8 kWh).
        threshold = LOW_BATTERY_THRESHOLD_KWH if not is_greedy else 3.7

        # Straight-line distance from current node to goal — used to decide if charging is needed
        current_coords  = get_node_coords(self.Graph, node_to_expand.state_id)
        dist_to_goal_km = haversine_km(
            current_coords[0], current_coords[1],
            self._goal_coords[0], self._goal_coords[1]
        )
        # Estimate energy needed to reach goal (with 20% road overhead factor)
        energy_to_goal = dist_to_goal_km * 1.2 * DEFAULT_KWH_PER_KM

        for child_id, step_cost, battery_consumed in self.get_valid_actions(node_to_expand.state_id):
            did_charge = False

            # Step 1: prune if this edge would kill the battery
            new_battery = node_to_expand.battery_kwh - battery_consumed
            if new_battery <= 0:
                continue

            cumulative_cost = current_cost + step_cost

            # Step 2: charge only if at a station AND battery is low AND can't reach goal directly.
            # Skipping the goal-reachability check was causing unnecessary stops on short trips.
            is_charger = self._parse_bool(
                self.Graph.nodes[child_id].get("is_charging_station", False)
            )

            needs_charge = (
                use_constraints
                and new_battery < threshold
                and new_battery < energy_to_goal   # can't make it to goal on current charge
            )

            if is_charger and (needs_charge or not use_constraints):
                charger_kw    = self._node_float(self.Graph, child_id, "charger_kw", default=7.0)
                energy_needed = self.battery_capacity - new_battery

                new_battery = self.battery_capacity
                did_charge  = True

                charging_time_h  = energy_needed / max(charger_kw, 0.1)
                cumulative_cost += charging_time_h * 3600

                # Soft penalty for slow chargers so the planner weakly prefers fast ones
                if use_heuristic and charger_kw < FAST_CHARGER_KW_THRESHOLD:
                    cumulative_cost += charging_time_h * 0.5

            # Step 3: if battery is still low, redirect heuristic toward nearest charger
            child_coords  = get_node_coords(self.Graph, child_id)
            target_coords = None   # None → aim at goal

            if new_battery < threshold and use_heuristic and use_constraints:
                # Only redirect if we genuinely can't reach the goal on current charge
                child_to_goal_km = haversine_km(
                    child_coords[0], child_coords[1],
                    self._goal_coords[0], self._goal_coords[1]
                )
                if new_battery < child_to_goal_km * 1.2 * DEFAULT_KWH_PER_KM:
                    target_node = self._nearest_reachable_charger(child_id, new_battery)
                    if target_node is None:
                        continue   # No reachable charger → prune (EV would strand)
                    target_coords = get_node_coords(self.Graph, target_node)

            # Step 4: compute f-score
            f_score = self.get_total_cost(
                cumulative_cost,
                child_coords,
                use_cost,
                use_heuristic,
                override_target=target_coords,
            )

            child_node = Node(
                    child_id,
                    new_battery,
                    node_to_expand,
                    f"move_to_{child_id}",
                    cumulative_cost,
                    f_score,
                )
            child_node.charged_here = did_charge
            children.append(child_node)

        return children
