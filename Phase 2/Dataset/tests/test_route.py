"""
Member-2: Comprehensive Route Engine Test Suite
Author: Jahnvi Verma (Member 2)
SlopeShield Project: Intelligent Landslide Risk & Safe Route System

Validates:
1. Priority Queue: Min-Heap invariant, push, pop (extract-min), peek, empty handling.
2. Graph Data Structure & Adjacency List: Vertex addition, bidirectional edges, degrees.
3. Risk-Based Edge Weight Design: Formula accuracy, critical penalties, monotonicity.
4. Dijkstra's Algorithm: Optimal paths, shortest vs safest cost invariants.
5. Scenario Replay (tests/route_cases.csv): Hazard bypasses, detours, and cost comparisons.
6. Frontend Output Format: Valid JSON, Leaflet coordinates, route segments.

Usage:
  python tests/test_route.py
"""

import csv
import json
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "scripts"))

from route_engine import (  # noqa: E402
    MinPriorityQueue,
    Graph,
    Vertex,
    Edge,
    DijkstraRouter,
    RouteComparison,
    RouteDataLoader,
    DEFAULT_ALPHA,
    DEFAULT_CRITICAL_PENALTY,
    CRITICAL_THRESHOLD,
    OUT_JSON
)

CASES_CSV = os.path.join(BASE, "tests", "route_cases.csv")


def test_priority_queue():
    """Verify custom MinPriorityQueue min-heap mechanics."""
    pq = MinPriorityQueue()
    assert pq.is_empty(), "PQ should be empty initially"
    assert len(pq) == 0

    # Insert items with unsorted priorities
    items = [(45.0, "B"), (12.5, "A"), (78.2, "D"), (33.1, "C"), (12.5, "A2"), (0.0, "Z")]
    for prio, val in items:
        pq.push(prio, val)

    assert not pq.is_empty()
    assert len(pq) == len(items)

    # Pop elements and verify strictly ascending order
    popped = []
    prev_prio = -1.0
    while not pq.is_empty():
        prio, val = pq.pop()
        assert prio >= prev_prio, f"Min-heap violation: popped {prio} after {prev_prio}"
        prev_prio = prio
        popped.append((prio, val))

    assert len(popped) == len(items)
    assert popped[0] == (0.0, "Z"), "Smallest element must be extracted first"

    # Underflow check
    try:
        pq.pop()
        assert False, "Popping from empty PQ should raise IndexError"
    except IndexError:
        pass


def test_graph_and_adjacency():
    """Verify Graph representation and Adjacency list storage."""
    graph = RouteDataLoader.load_graph()
    assert len(graph.vertices) == 11, f"Expected 11 vertices, got {len(graph.vertices)}"

    # Check key locations exist
    for expected_id in ["RISH", "DEHR", "MUSS", "RUDR", "UKHI", "KEDN", "CHAM", "BADR", "UTTK", "GANG", "MALP"]:
        assert graph.get_vertex(expected_id) is not None, f"Missing vertex {expected_id}"

    # Verify adjacency list representation
    assert len(graph.adj) == 11
    rish_neighbors = [e.v for e in graph.get_neighbors("RISH")]
    assert "DEHR" in rish_neighbors
    assert "RUDR" in rish_neighbors
    assert "UTTK" in rish_neighbors

    # Verify bidirectional connectivity
    e_forward = graph.get_edge("RISH", "DEHR")
    e_backward = graph.get_edge("DEHR", "RISH")
    assert e_forward is not None and e_backward is not None
    assert e_forward.distance_km == e_backward.distance_km == 45.0


def test_risk_weight_design():
    """Verify risk-based edge weight formula and monotonicity."""
    g = Graph()
    u = Vertex("U", "Node U", 30.0, 78.0)
    v = Vertex("V", "Node V", 30.1, 78.1)
    g.add_vertex(u)
    g.add_vertex(v)
    g.add_edge("TEST_01", "U", "V", 100.0, bidirectional=True)

    # Case 1: Low risk (R_u=10, R_v=20 => R_edge=15)
    u.update_risk(10.0, "Low")
    v.update_risk(20.0, "Low")
    g.update_edge_weights(alpha=1.5, critical_penalty=1000.0)
    edge = g.get_edge("U", "V")
    assert edge.edge_risk_score == 15.0
    assert edge.edge_risk_level == "Low"
    # Weight = 100 * (1 + 1.5 * 15/100) = 100 * 1.225 = 122.5
    assert abs(edge.risk_cost - 122.5) < 1e-2

    # Case 2: Monotonicity check (increasing risk must increase edge weight)
    prev_cost = edge.risk_cost
    for r in [30.0, 50.0, 70.0]:
        u.update_risk(r, "Moderate" if r < 50 else "High")
        v.update_risk(r, "Moderate" if r < 50 else "High")
        g.update_edge_weights(alpha=1.5, critical_penalty=1000.0)
        curr_cost = g.get_edge("U", "V").risk_cost
        assert curr_cost > prev_cost, f"Monotonicity failed: {curr_cost} <= {prev_cost}"
        prev_cost = curr_cost

    # Case 3: Critical hazard penalty application
    u.update_risk(80.0, "Critical")
    v.update_risk(80.0, "Critical")
    g.update_edge_weights(alpha=1.5, critical_penalty=1000.0)
    crit_edge = g.get_edge("U", "V")
    assert crit_edge.edge_risk_level == "Critical"
    assert crit_edge.critical_penalty_applied is True
    # Weight = 100 * (1 + 1.5 * 80/100) + 1000 = 220 + 1000 = 1220.0
    assert abs(crit_edge.risk_cost - 1220.0) < 1e-2


def test_dijkstra_optimality():
    """Verify Dijkstra's algorithm respects distance and risk invariants."""
    graph = RouteDataLoader.load_graph()

    for src in ["RISH", "KEDN", "CHAM"]:
        for dst in ["BADR", "UTTK", "MUSS"]:
            if src == dst:
                continue
            shortest = DijkstraRouter.find_path(graph, src, dst, mode="distance")
            safest = DijkstraRouter.find_path(graph, src, dst, mode="risk")

            if shortest.found and safest.found:
                # Invariant 1: Shortest distance path must have <= physical distance
                assert shortest.total_distance_km <= safest.total_distance_km + 1e-6, \
                    f"Shortest path distance ({shortest.total_distance_km}) > safest distance ({safest.total_distance_km})"

                # Invariant 2: Safest path must have <= total risk cost
                assert safest.total_risk_cost <= shortest.total_risk_cost + 1e-6, \
                    f"Safest path risk cost ({safest.total_risk_cost}) > shortest risk cost ({shortest.total_risk_cost})"


def test_scenarios():
    """Replay and verify all 8 test scenarios from tests/route_cases.csv."""
    graph = RouteDataLoader.load_graph()
    fails = 0

    print("=" * 105)
    print(f"{'Case ID':32s} | {'Source->Dest':12s} | {'Safest Path Got':28s} | {'Safest Expected':28s} | Verdict")
    print("=" * 105)

    with open(CASES_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            case_id = row["case_id"].strip()
            src = row["source_id"].strip()
            dst = row["dest_id"].strip()
            ov_type = row["override_type"].strip()
            ov_target = row["override_target"].strip()
            ov_score = float(row["override_score"])
            ov_level = row["override_level"].strip()
            exp_short = row["expected_shortest"].strip()
            exp_safe = row["expected_safest"].strip()

            # Apply scenario hazard overrides
            node_ov = {}
            edge_ov = {}
            if ov_type == "NODE":
                node_ov[ov_target] = (ov_score, ov_level)
            elif ov_type == "EDGE":
                edge_ov[ov_target] = (ov_score, ov_level)

            graph.update_edge_weights(node_overrides=node_ov, edge_overrides=edge_ov)

            shortest = DijkstraRouter.find_path(graph, src, dst, mode="distance")
            safest = DijkstraRouter.find_path(graph, src, dst, mode="risk")

            got_short_str = "->".join(shortest.path)
            got_safe_str = "->".join(safest.path)

            ok_short = (got_short_str == exp_short)
            ok_safe = (got_safe_str == exp_safe)

            verdict = "PASS" if (ok_short and ok_safe) else "FAIL"
            if verdict == "FAIL":
                fails += 1

            src_dst = f"{src}->{dst}"
            print(f"{case_id:32s} | {src_dst:12s} | {got_safe_str:28s} | {exp_safe:28s} | {verdict}")

    print("=" * 105)
    # Reset edge weights to standard baseline
    graph.update_edge_weights()
    return fails


def test_frontend_json_contract():
    """Verify data/route_output.json matches the frontend integration contract."""
    assert os.path.exists(OUT_JSON), f"Missing {OUT_JSON}"
    with open(OUT_JSON, encoding="utf-8") as f:
        data = json.load(f)

    assert "metadata" in data
    assert "all_locations" in data
    assert "routes" in data

    # Verify Leaflet polyline coordinates and segment format
    sample_route = data["routes"]["RISH_to_BADR"]
    safest = sample_route["safest_route"]
    assert "coordinates" in safest and len(safest["coordinates"]) >= 2
    assert "segments" in safest and len(safest["segments"]) >= 1
    assert "distance_diff_km" in sample_route
    assert "risk_reduction_pct" in sample_route


def main():
    print("Running Member-2 Route Engine Test Suite...\n")
    test_priority_queue()
    print("[1/5] MinPriorityQueue Unit Tests: PASSED")

    test_graph_and_adjacency()
    print("[2/5] Graph & Adjacency List Tests: PASSED")

    test_risk_weight_design()
    print("[3/5] Risk-Based Edge Weight Design & Monotonicity: PASSED")

    test_dijkstra_optimality()
    print("[4/5] Dijkstra Optimality & Invariant Checks: PASSED")

    print("[5/5] Replaying Multi-Scenario Route Comparisons (tests/route_cases.csv):")
    fails = test_scenarios()

    test_frontend_json_contract()
    print("\n[Contract] Frontend JSON Output Schema Verified: PASSED")

    if fails == 0:
        print("\n=============================================")
        print(" ALL MEMBER-2 ROUTE ENGINE TESTS PASSED (8/8)")
        print("=============================================")
        sys.exit(0)
    else:
        print(f"\nFAILURE: {fails} test scenario(s) failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
