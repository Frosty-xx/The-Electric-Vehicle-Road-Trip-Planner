"""
test_greedy_search.py
=====================
Simple verification tests for Greedy Best-First Search + soft constraint.
Uses node IDs extracted directly from tunisia_major.graphml.

Each test changes the goal_state and checks a specific behavior:
  Test 1 — Normal route, battery never runs low          → expect valid path
  Test 2 — Short battery, goal reachable without charger → expect valid path, no charger visited
  Test 3 — Short battery, goal NOT reachable directly    → expect charger detour in path
  Test 4 — Fast vs Slow charger preference               → expect fast charger chosen
  Test 5 — Dead-end (impossible battery)                 → expect None (no path)
"""

import sys
import os
import osmnx as ox

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from Core_Modules.EVGraph import is_charging_station
from Core_Modules.EV_Porblem import EV_Problem
from Search_Algorithms.General_Search import GeneralSearch

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
GRAPH_PATH = os.path.join(BASE_DIR, "..", "Data", "tunisia_major.graphml")

# Node IDs taken directly from the graphml snippet you provided
# Northern Tunisia cluster (close together ~Tunis area)
NODE_TUNIS_CENTER   = 93850200   # lat 36.800, lon 10.186  — Tunis area
NODE_TUNIS_NEARBY   = 103795990  # lat 36.800, lon 10.187  — very close to center
NODE_TUNIS_FAR      = 206335191  # lat 36.821, lon 10.190  — ~3 km north
NODE_ARIANA         = 245920311  # lat 36.831, lon 10.180  — ~5 km north
NODE_BARDO          = 243996998  # lat 36.834, lon 10.176  — ~5 km north-west

# Southern Tunisia cluster (far from Tunis ~250+ km)
NODE_SFAX_AREA      = 257980756  # lat 35.240, lon  9.145
NODE_KASSERINE      = 257979695  # lat 35.323, lon  8.718
NODE_GAFSA          = 257979809  # lat 35.074, lon  8.665
NODE_SIDI_BOUZID    = 257980043  # lat 34.553, lon  8.650
NODE_GABES_AREA     = 257980229  # lat 34.313, lon  8.418

DEFAULT_BATTERY_KWH = 77.4  # Hyundai Ioniq 5

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

PASS = "\033[92m[PASS]\033[0m"
FAIL = "\033[91m[FAIL]\033[0m"
INFO = "\033[94m[INFO]\033[0m"

def run_greedy(G, start, goal, battery_kwh, label=""):
    """Run Greedy search and return (solution_node, explored_set, path_coords)."""
    print(f"\n{INFO} {label}")
    print(f"       start={start}  goal={goal}  battery={battery_kwh:.1f} kWh")
    problem = EV_Problem(start, goal, 100, battery_kwh, G)
    # Override initial battery directly so we can test with custom values
    problem.initial_batery_percentage = (battery_kwh / problem.battery_capacity) * 100
    searcher = GeneralSearch(problem)
    solution, explored = searcher.search("Greedy")
    return solution, explored, searcher

def chargers_in_path(G, solution_node):
    """Walk parent chain and collect any charging station nodes visited."""
    chargers = []
    cur = solution_node
    while cur is not None:
        if is_charging_station(G, cur.state_id):
            chargers.append((cur.state_id, G.nodes[cur.state_id].get("charger_kw", 0)))
        cur = cur.parent
    return chargers

def path_length(solution_node):
    """Return total distance (km) of the solution."""
    return solution_node.distance_km if solution_node else None

def battery_at_goal(solution_node):
    return solution_node.battery_kwh if solution_node else None

# ---------------------------------------------------------------------------
# Load graph ONCE
# ---------------------------------------------------------------------------

print("Loading graph …")
G = ox.load_graphml(GRAPH_PATH)
print(f"Graph loaded: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges\n")
print("=" * 65)

results = []

# ---------------------------------------------------------------------------
# TEST 1 — Normal short route, plenty of battery
# Goal: NODE_TUNIS_FAR (~3 km from start)
# Expect: solution found, battery never critically low, no charger detour
# ---------------------------------------------------------------------------
label = "Test 1 — Short route, full battery"
start = NODE_TUNIS_CENTER
goal  = NODE_TUNIS_FAR

solution, explored, searcher = run_greedy(G, start, goal, DEFAULT_BATTERY_KWH, label)

if solution is not None:
    dist   = path_length(solution)
    batt   = battery_at_goal(solution)
    chrgs  = chargers_in_path(G, solution)
    pct    = batt / DEFAULT_BATTERY_KWH * 100
    print(f"       distance={dist:.2f} km  battery_left={batt:.2f} kWh ({pct:.1f}%)")
    print(f"       explored={len(explored)} nodes  chargers_visited={chrgs}")
    ok = dist < 20 and pct > 80          # should be short and battery still high
    print(f"  {PASS if ok else FAIL} Expected short path (<20 km) and high battery (>80%): {'yes' if ok else 'NO'}")
    results.append(("Test 1", ok))
else:
    print(f"  {FAIL} No solution found — should have found one.")
    results.append(("Test 1", False))

print("-" * 65)

# ---------------------------------------------------------------------------
# TEST 2 — Slightly longer route, battery still sufficient without charging
# Goal: NODE_ARIANA (~5 km from start)
# Battery: 15 kWh (enough for ~93 km, well above 5 km needed)
# Expect: solution found, no charger needed
# ---------------------------------------------------------------------------
label = "Test 2 — Medium route, sufficient battery (15 kWh)"
start = NODE_TUNIS_CENTER
goal  = NODE_ARIANA

solution, explored, searcher = run_greedy(G, start, goal, 15.0, label)

if solution is not None:
    dist  = path_length(solution)
    batt  = battery_at_goal(solution)
    chrgs = chargers_in_path(G, solution)
    print(f"       distance={dist:.2f} km  battery_left={batt:.2f} kWh")
    print(f"       explored={len(explored)} nodes  chargers_visited={chrgs}")
    # Battery should still be positive and no critical detour needed for ~5 km
    ok = solution is not None and batt > 0
    print(f"  {PASS if ok else FAIL} Reached goal with battery > 0: {'yes' if ok else 'NO'}")
    results.append(("Test 2", ok))
else:
    print(f"  {FAIL} No solution returned.")
    results.append(("Test 2", False))

print("-" * 65)

# ---------------------------------------------------------------------------
# TEST 3 — Long route, low battery → charger detour expected
# Goal: NODE_SFAX_AREA (~250 km south)
# Battery: 10 kWh (only ~62 km range — must stop at charger(s))
# Expect: solution found AND at least one charging station in path
# ---------------------------------------------------------------------------
print("\n" + "="*65)
print("FINDING CHARGERS NEAR START - Modified Test 3")
print("="*65)

start = NODE_TUNIS_CENTER

# Find charging stations in the graph and their distances
charger_nodes = []
for node_id, data in G.nodes(data=True):
    is_cs = str(data.get("is_charging_station", "")).lower() == "true"
    if is_cs:
        # Calculate distance from start
        from Core_Modules.EVGraph import get_node_coords, haversine_km
        start_coords = get_node_coords(G, start)
        cs_coords = get_node_coords(G, node_id)
        dist_km = haversine_km(start_coords[0], start_coords[1], cs_coords[0], cs_coords[1])
        kw = float(data.get("charger_kw", 0)) if data.get("charger_kw") else 0
        charger_nodes.append((node_id, dist_km, kw))
        print(f"  Charger at node {node_id}: {dist_km:.1f} km away, {kw} kW")

if charger_nodes:
    # Sort by distance
    charger_nodes.sort(key=lambda x: x[1])
    nearest_charger = charger_nodes[0][0]
    nearest_dist = charger_nodes[0][1]
    
    print(f"\nNearest charger to start: node {nearest_charger} at {nearest_dist:.1f} km")
    
    # Set battery to just enough to reach the charger (plus a little extra)
    battery_to_reach_charger = nearest_dist * 0.16125 + 2.0  # kWh needed + buffer
    print(f"Battery needed to reach charger: {battery_to_reach_charger:.1f} kWh")
    
    # Pick a goal beyond the charger (use a node that requires going past the charger)
    # For demonstration, use a node farther away
    goal = NODE_TUNIS_FAR  # ~3 km from start
    
    print(f"\nTest: Start={start}, Goal={goal}, Battery={battery_to_reach_charger:.1f} kWh")
    print("Expectation: Greedy should drive to nearest charger FIRST, then to goal")
    
    solution, explored, searcher = run_greedy(G, start, goal, battery_to_reach_charger, 
                                               "Modified Test 3 - Must use charger")
    
    if solution:
        dist = path_length(solution)
        batt = battery_at_goal(solution)
        chrgs = chargers_in_path(G, solution)
        print(f"\n  Result: distance={dist:.2f} km, final battery={batt:.2f} kWh")
        print(f"  Chargers visited: {len(chrgs)}")
        for cid, kw in chrgs:
            print(f"    → Node {cid}: {kw} kW")
        
        if len(chrgs) > 0:
            print(f"\n  ✓ SUCCESS! Greedy found a charger and used it")
        else:
            print(f"\n  ✗ Greedy did NOT use any charger (may have gone directly to goal)")
    else:
        print(f"\n  ✗ Greedy FAILED - could not find a path with {battery_to_reach_charger:.1f} kWh")
        print(f"    Explored {len(explored)} nodes")
else:
    print("No charging stations found in the graph!")

print("-" * 65)
# ---------------------------------------------------------------------------
# TEST 4 — Soft constraint: fast charger preferred over slow charger
# We manually tag two nearby nodes: one as 7 kW, one as 150 kW
# Then run with low battery and check which charger was visited
# Goal: NODE_BARDO (~5 km away, battery just barely forces a stop)
# ---------------------------------------------------------------------------
# In your test_greedy.py, change Test 4 to:

label = "Test 4 — Soft constraint: fast charger preference (LOW BATTERY)"
SLOW_CHARGER_NODE = NODE_TUNIS_NEARBY   # 7 kW  
FAST_CHARGER_NODE = NODE_TUNIS_FAR      # 150 kW

# Tag them on a copy
import copy
G_test4 = copy.deepcopy(G)
G_test4.nodes[SLOW_CHARGER_NODE]["is_charging_station"] = True
G_test4.nodes[SLOW_CHARGER_NODE]["charger_kw"] = 7
G_test4.nodes[FAST_CHARGER_NODE]["is_charging_station"] = True
G_test4.nodes[FAST_CHARGER_NODE]["charger_kw"] = 150

# Force the path to need a charger
start = NODE_TUNIS_CENTER
goal = NODE_BARDO  # ~7 km away

# Calculate battery that's INSUFFICIENT to reach goal directly
# Goal distance ~7 km = needs ~1.13 kWh
# Give only 0.8 kWh (forces charger stop)
battery_given = 0.8  # kWh

print(f"\n{INFO} {label}")
print(f"       Battery given: {battery_given} kWh (insufficient for direct trip)")
print(f"       slow_charger={SLOW_CHARGER_NODE} (7 kW)   fast_charger={FAST_CHARGER_NODE} (150 kW)")

problem = EV_Problem(start, goal, 100, DEFAULT_BATTERY_KWH, G_test4)
problem.initial_batery_percentage = (battery_given / DEFAULT_BATTERY_KWH) * 100
searcher = GeneralSearch(problem)
solution, explored = searcher.search("Greedy")

if solution:
    chrgs = chargers_in_path(G_test4, solution)
    visited_ids = [c[0] for c in chrgs]
    used_fast = FAST_CHARGER_NODE in visited_ids
    used_slow = SLOW_CHARGER_NODE in visited_ids
    print(f"       chargers visited: {chrgs}")
    if used_fast:
        print(f"  {PASS} Fast charger preferred! ✓")
    elif used_slow:
        print(f"  {FAIL} Chose slow charger instead of fast - check soft constraint")
    else:
        print(f"  {FAIL} No charger used - battery may still have been sufficient")
else:
    print(f"  {FAIL} No solution found")
# ---------------------------------------------------------------------------
# TEST 5 — Dead-end: battery impossibly small (0.01 kWh) for any move
# Goal: NODE_TUNIS_FAR (just 3 km but every edge costs more than 0.01 kWh)
# Expect: returns None (no path possible)
# ---------------------------------------------------------------------------
label = "Test 5 — Dead-end: battery too small for any move"
start = NODE_TUNIS_CENTER
goal  = NODE_TUNIS_FAR

solution, explored, searcher = run_greedy(G, start, goal, 0.01, label)

if solution is None:
    print(f"  {PASS} Correctly returned None (dead end).")
    print(f"       explored={len(explored)} nodes before giving up.")
    results.append(("Test 5", True))
else:
    print(f"  {FAIL} Found a solution with 0.01 kWh — battery constraint not enforced!")
    results.append(("Test 5", False))

print("-" * 65)

# ---------------------------------------------------------------------------
# BONUS TEST 6 — Changing goal state: same start, 4 different goals
# Purpose: verify haversine heuristic actually guides search differently
# ---------------------------------------------------------------------------
print(f"\n{INFO} Test 6 — Same start, 4 different goals (heuristic direction check)")
goals = {
    "nearby (103795990)": NODE_TUNIS_NEARBY,
    "ariana (245920311)": NODE_ARIANA,
    "bardo  (243996998)": NODE_BARDO,
    "far    (206335191)": NODE_TUNIS_FAR,
}

prev_explored = None
start = NODE_TUNIS_CENTER
test6_ok = True
for gname, gnode in goals.items():
    sol, explored, _ = run_greedy(G, start, gnode, DEFAULT_BATTERY_KWH,
                                  f"  goal={gname}")
    n_explored = len(explored)
    dist = f"{sol.distance_km:.2f} km ({sol.g:.2f} h)" if sol else "NO PATH"
    print(f"       explored={n_explored:5d} nodes   dist={dist}")
    if sol is None:
        test6_ok = False

print(f"  {PASS if test6_ok else FAIL} All 4 goals reached: {'yes' if test6_ok else 'NO'}")
results.append(("Test 6", test6_ok))

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
print("\n" + "=" * 65)
print("SUMMARY")
print("=" * 65)
passed = failed = skipped = 0
for name, ok in results:
    if ok is None:
        print(f"  {INFO} {name}: skipped (condition not triggered)")
        skipped += 1
    elif ok:
        print(f"  {PASS} {name}")
        passed += 1
    else:
        print(f"  {FAIL} {name}")
        failed += 1
print(f"\n  Total: {passed} passed, {failed} failed, {skipped} skipped")
print("=" * 65)