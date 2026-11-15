"""
================================================================================
SlopeShield: Intelligent Landslide Risk & Safe Route System
Master Entry Point & Orchestration CLI (Member 3: System Integration)
Author: Anshika Gaur (Member 3)
Team: The Debug Divas
================================================================================

Usage:
  python main.py                     # Run complete end-to-end pipeline & export outputs
  python main.py --serve             # Launch REST API server & interactive frontend on port 8000
  python main.py --serve --port 8080 # Launch on custom port
  python main.py --route --source RISH --dest BADR   # Query on-demand route
  python main.py --simulate --target RUDR --score 77.08 --level Critical # What-If analysis
  python main.py --test              # Run full test suite across all modules
"""

import sys
import os
import argparse
from typing import Optional

# Ensure project root is on PYTHONPATH
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.service import SlopeShieldBackend, STANDARD_CORRIDORS
from backend.server import run_server


def print_banner():
    banner = """
====================================================================================
  SlopeShield: Intelligent Landslide Risk & Safe Route System
  Team: The Debug Divas | Uttarakhand Char Dham Pilgrimage & Emergency Corridors
====================================================================================
"""
    print(banner)


def run_pipeline(backend: SlopeShieldBackend, use_mock: bool = True, api_key: str = ""):
    """Executes the complete integration pipeline from raw inputs to frontend JSON."""
    print("[1/4] Initializing OOP System & Data Handlers...")
    backend.initialize()
    print(f"      Loaded {len(backend.locations)} locations and {len(backend.roads)} road corridors.")

    print("\n[2/4] Executing Environmental Risk Pipeline (Member 1)...")
    res = backend.refresh_weather_and_scores(use_mock=use_mock, api_key=api_key)
    ds = res.get("data_source", "mock")
    if ds == "live_openweathermap":
        mode_desc = "Live OpenWeatherMap API (All 11 locations live)"
    elif ds == "mixed":
        fs = res.get("freshness_summary", {})
        mode_desc = f"Mixed (Live: {fs.get('live_count', 0)}, Cache/Fallback: {fs.get('fallback_count', 0) + fs.get('cache_count', 0)})"
    elif ds == "cache":
        mode_desc = "Previously Saved Cache Data"
    elif ds == "fallback":
        mode_desc = "Fallback Weather Data (API unavailable)"
    else:
        mode_desc = "Mock Environmental Data (Viva Safe)"
    print(f"      Source: {mode_desc}")
    print(f"      Status: is_live={res.get('is_live', False)}, system_status={res.get('system_status', ds)}")
    print(f"      Successfully scored {res['scored_count']} locations -> data/risk_scores.csv, data/risk_output.json")
    print(f"      {'ID':5s} | {'Static':7s} | {'Dynamic':7s} | {'Total':6s} | {'Hazard Level'}")
    print("      " + "-" * 48)
    for loc in backend.get_locations_summary():
        print(f"      {loc['location_id']:5s} | {loc['static_score']:7.1f} | {loc['dynamic_score']:7.1f} | {loc['risk_score']:6.1f} | {loc['risk_level']}")

    print("\n[3/4] Rebuilding Road Graph with Risk-Weighted Edges (Member 2)...")
    print("      Applied alpha multiplier (1.5) and Critical danger barrier penalty (1000.0).")

    print("\n[4/4] Executing Dijkstra Route Engine & Generating Frontend JSON...")
    routes_payload = backend.plan_all_standard_corridors()
    print(f"      Successfully generated: data/route_output.json ({len(routes_payload['routes'])} standard corridors)")

    print("\n" + "=" * 90)
    print(f"{'Corridor':14s} | {'Mode':8s} | {'Distance':9s} | {'Risk Cost':10s} | {'Max Hazard':10s} | Path")
    print("=" * 90)

    for src, dst in STANDARD_CORRIDORS:
        comp = backend.compare_route(src, dst)
        s_route = comp.shortest
        r_route = comp.safest

        s_path = " -> ".join(s_route.path)
        r_path = " -> ".join(r_route.path)

        title = f"{src} -> {dst}"
        print(f"{title:14s} | Shortest | {s_route.total_distance_km:6.1f} km | {s_route.total_risk_cost:10.1f} | {s_route.max_risk_level:10s} | {s_path}")
        print(f"{'':14s} | Safest   | {r_route.total_distance_km:6.1f} km | {r_route.total_risk_cost:10.1f} | {r_route.max_risk_level:10s} | {r_path}")
        if not comp.is_identical:
            print(f"   >>> [DETOUR ADVICE] {comp.recommendation}")
        print("-" * 90)

    print("\n>> PIPELINE EXECUTION COMPLETED SUCCESSFULLY!\n")


def query_route(backend: SlopeShieldBackend, source: str, dest: str, mode: str = "safest", use_mock: bool = True, api_key: str = ""):
    """Query a specific on-demand route."""
    if not backend.is_initialized:
        backend.initialize()
        backend.refresh_weather_and_scores(use_mock=use_mock, api_key=api_key)

    comp = backend.compare_route(source, dest)
    target_route = comp.safest if mode == "safest" else comp.shortest

    print(f"\n=======================================================")
    print(f" ROUTE QUERY: {source} -> {dest} (Mode: {mode.upper()})")
    print(f"=======================================================")
    print(f"Selected Path    : {' -> '.join(target_route.path)}")
    print(f"Total Distance   : {target_route.total_distance_km:.1f} km")
    print(f"Total Risk Cost  : {target_route.total_risk_cost:.1f}")
    print(f"Max Hazard Level : {target_route.max_risk_level}")
    print(f"Recommendation   : {comp.recommendation}")
    print(f"=======================================================\n")


def run_tests():
    """Run all verification suites across all modules."""
    print("\n==================================================================")
    print(" EXECUTING SLOPESHIELD COMPLETE MULTI-MEMBER TEST SUITE")
    print("==================================================================")

    import subprocess
    py = sys.executable

    print("\n[Phase 1/3] Running Member 1 Risk Tests (tests/test_risk.py)...")
    res1 = subprocess.run([py, os.path.join(BASE_DIR, "tests", "test_risk.py")])

    print("\n[Phase 2/3] Running Member 2 Route Engine Tests (tests/test_route.py)...")
    res2 = subprocess.run([py, os.path.join(BASE_DIR, "tests", "test_route.py")])

    print("\n[Phase 3/3] Running Member 3 Integration Tests (tests/test_integration.py)...")
    res3 = subprocess.run([py, os.path.join(BASE_DIR, "tests", "test_integration.py")])

    if res1.returncode == 0 and res2.returncode == 0 and res3.returncode == 0:
        print("\n==================================================================")
        print(" >> ALL PROJECT TESTS PASSED ACROSS ALL MODULES!")
        print("==================================================================\n")
        return 0
    else:
        print("\n>> ONE OR MORE TEST SUITES FAILED!")
        return 1


def main():
    parser = argparse.ArgumentParser(description="SlopeShield Intelligent Landslide Risk & Safe Route System")
    parser.add_argument("--live", action="store_true", help="Fetch and run with live OpenWeatherMap weather readings")
    parser.add_argument("--api-key", type=str, default=os.environ.get("OWM_API_KEY", ""), help="OpenWeatherMap API key (defaults to OWM_API_KEY env var)")
    parser.add_argument("--serve", action="store_true", help="Launch the REST API server and interactive map dashboard")
    parser.add_argument("--port", type=int, default=8000, help="Port to run the REST API server on (default: 8000)")
    parser.add_argument("--route", action="store_true", help="Query route between two points")
    parser.add_argument("--source", type=str, default="RISH", help="Source location ID (e.g., RISH)")
    parser.add_argument("--dest", type=str, default="BADR", help="Destination location ID (e.g., BADR)")
    parser.add_argument("--mode", type=str, choices=["safest", "shortest"], default="safest", help="Routing mode")
    parser.add_argument("--simulate", action="store_true", help="Simulate a disaster hazard scenario")
    parser.add_argument("--target", type=str, default="RUDR", help="Target node or edge ID for simulation")
    parser.add_argument("--type", type=str, choices=["NODE", "EDGE"], default="NODE", help="Simulation target type")
    parser.add_argument("--score", type=float, default=77.08, help="Simulated risk score (0-100)")
    parser.add_argument("--level", type=str, default="Critical", help="Simulated risk level")
    parser.add_argument("--test", action="store_true", help="Execute the complete test suite")

    args = parser.parse_args()
    print_banner()

    if args.test:
        sys.exit(run_tests())

    api_key = args.api_key.strip()
    use_mock = not (args.live or bool(api_key))

    backend = SlopeShieldBackend(BASE_DIR)

    if args.serve:
        run_server(port=args.port, base_dir=BASE_DIR, use_mock=use_mock, api_key=api_key)
        return

    if args.route:
        query_route(backend, args.source, args.dest, args.mode, use_mock=use_mock, api_key=api_key)
        return

    if args.simulate:
        backend.initialize()
        backend.refresh_weather_and_scores(use_mock=use_mock, api_key=api_key)
        print(f"Simulating hazard on {args.type} {args.target} (Score: {args.score}, Level: {args.level})...")
        backend.simulate_hazard(args.type, args.target, args.score, args.level)
        query_route(backend, "RISH", "KEDN", "safest", use_mock=use_mock, api_key=api_key)
        return

    # Default action: run full pipeline end-to-end
    run_pipeline(backend, use_mock=use_mock, api_key=api_key)


if __name__ == "__main__":
    main()
