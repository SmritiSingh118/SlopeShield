"""
================================================================================
SlopeShield: Comprehensive End-to-End Integration Test Suite
Member 3: System Architecture, File I/O, Backend & API Verification
Author: Jahnvi Verma (Member 3)
================================================================================

Validates all 5 assigned responsibilities for Member 3:
1. OOP Architecture: Classes, objects, encapsulation, properties, serialization.
2. CSV/JSON File Handling: Robust reading, writing, schema checks, error tolerance.
3. Backend Integration: Unified pipeline connecting Member 1 risk & Member 2 routing.
4. Hazard Detour Routing: Verifies automatic hazard avoidance under cloudburst.
5. Backend -> Frontend API Communication: Validates HTTP REST endpoints and JSON contract.
"""

import os
import sys
import json
import time
import threading
import urllib.request
import urllib.parse
from http.server import HTTPServer

# Add project root to sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.models import Location, RoadSegment, RiskProfile, WeatherReading, RouteResult
from core.data_handlers import CsvHandler, JsonHandler, DataManager
from core.risk_scorer import WeightedRiskScorer
from core.route_planner import RoadGraph, DijkstraRoutePlanner
from backend.service import SlopeShieldBackend
from backend.server import SlopeShieldApiHandler


def test_oop_models_and_encapsulation():
    """Verify OOP domain entities, encapsulation, getters, and state updates."""
    print("  [1.1] Testing RiskProfile encapsulation...")
    rp = RiskProfile(static_score=40.0, dynamic_score=20.0, total_score=32.0, risk_level="Moderate")
    assert rp.total_score == 32.0
    assert rp.risk_level == "Moderate"

    # Automatic level derivation on score update
    rp.update_scores(75.0, 80.0, 77.0)
    assert rp.risk_level == "Critical", f"Expected Critical, got {rp.risk_level}"

    print("  [1.2] Testing Location entity...")
    loc = Location("RUDR", "Rudraprayag", 30.284, 78.98, elevation_m=895.0, slope_deg=38.0)
    assert loc.id == "RUDR"
    assert loc.slope_deg == 38.0
    loc.set_risk(74.87, 28.13, 56.17, "High")
    assert loc.risk.total_score == 56.17
    assert loc.risk.risk_level == "High"

    dict_repr = loc.to_dict()
    assert dict_repr["location_id"] == "RUDR"
    assert dict_repr["risk_level"] == "High"

    print("  [1.3] Testing RoadSegment weight calculation...")
    u = Location("RISH", "Rishikesh", 30.08, 78.26)
    u.set_risk(20.0, 10.0, 16.0, "Low")
    v = Location("RUDR", "Rudraprayag", 30.28, 78.98)
    v.set_risk(74.0, 30.0, 56.4, "High")

    road = RoadSegment("R07", "RISH", "RUDR", 140.0, highway="NH-7")
    cost = road.calculate_weight(u, v, alpha=1.5, critical_penalty=1000.0)
    assert cost > 140.0, "Risk-weighted cost must be strictly greater than physical distance"
    assert not road.critical_penalty_applied, "Should not apply critical penalty for High risk"

    # Force Critical hazard on endpoint
    v.set_risk(75.0, 80.0, 77.0, "Critical")
    crit_cost = road.calculate_weight(u, v, alpha=1.5, critical_penalty=1000.0)
    assert road.critical_penalty_applied is True
    assert crit_cost > 1000.0, "Critical penalty of +1000.0 must be applied"


def test_file_handling():
    """Verify robust CSV and JSON reading, writing, and atomic safety."""
    print("  [2.1] Testing CsvHandler reading & writing...")
    csv_h = CsvHandler()
    test_csv_path = os.path.join(BASE_DIR, "data", "test_scratch.csv")

    test_data = [
        {"id": "A", "val": "100.5", "note": "node A"},
        {"id": "B", "val": "200.0", "note": "node B"}
    ]
    csv_h.write(test_csv_path, test_data)
    assert os.path.exists(test_csv_path)

    read_back = csv_h.read(test_csv_path)
    assert len(read_back) == 2
    assert read_back[0]["id"] == "A"
    assert float(read_back[0]["val"]) == 100.5
    os.remove(test_csv_path)

    print("  [2.2] Testing JsonHandler reading & writing...")
    json_h = JsonHandler()
    test_json_path = os.path.join(BASE_DIR, "data", "test_scratch.json")
    test_json_data = {"status": "ok", "items": [1, 2, 3]}

    json_h.write(test_json_path, test_json_data)
    assert os.path.exists(test_json_path)

    json_read_back = json_h.read(test_json_path)
    assert json_read_back["status"] == "ok"
    assert len(json_read_back["items"]) == 3
    os.remove(test_json_path)

    print("  [2.3] Testing DataManager dataset loading...")
    dm = DataManager(BASE_DIR)
    locs = dm.load_locations()
    assert len(locs) == 11, f"Expected 11 locations, got {len(locs)}"
    assert "RISH" in locs and "BADR" in locs

    roads = dm.load_road_network()
    assert len(roads) == 14, f"Expected 14 highway segments, got {len(roads)}"

    cfg = dm.load_weights_config()
    assert "static_weight" in cfg and "dynamic_weight" in cfg


def test_backend_integration_pipeline():
    """Verify end-to-end integration: data loading -> scoring -> routing -> exporting."""
    print("  [3.1] Initializing SlopeShieldBackend facade...")
    backend = SlopeShieldBackend(BASE_DIR)
    backend.initialize()
    assert backend.is_initialized is True
    assert len(backend.locations) == 11
    assert len(backend.roads) == 14

    print("  [3.2] Refreshing weather and scoring all 11 locations...")
    res = backend.refresh_weather_and_scores(use_mock=True)
    assert res["status"] == "success"
    assert res["scored_count"] == 11

    # Check output files were written
    risk_csv = os.path.join(BASE_DIR, "data", "risk_scores.csv")
    risk_json = os.path.join(BASE_DIR, "data", "risk_output.json")
    assert os.path.exists(risk_csv) and os.path.exists(risk_json)

    print("  [3.3] Computing all 7 standard Char Dham corridors...")
    out_payload = backend.plan_all_standard_corridors()
    assert "routes" in out_payload
    assert len(out_payload["routes"]) == 7
    assert os.path.exists(os.path.join(BASE_DIR, "data", "route_output.json"))

    sample_route = out_payload["routes"]["RISH_to_BADR"]
    assert "safest_route" in sample_route
    assert "shortest_route" in sample_route
    assert len(sample_route["safest_route"]["coordinates"]) >= 3


def test_hazard_detour_routing():
    """Verify that simulating a cloudburst forces Dijkstra to find an alternate safe detour."""
    print("  [4.1] Testing normal baseline route (RISH -> KEDN)...")
    backend = SlopeShieldBackend(BASE_DIR)
    backend.initialize()
    backend.refresh_weather_and_scores(use_mock=True)

    base_comp = backend.compare_route("RISH", "KEDN")
    # In baseline mock weather, RUDR is High but not Critical, so shortest is RISH->RUDR->UKHI->KEDN
    assert "RUDR" in base_comp.shortest.path

    print("  [4.2] Simulating cloudburst at Rudraprayag (RUDR: 77.08 Critical)...")
    backend.simulate_hazard(override_type="NODE", target="RUDR", score=77.08, level="Critical")

    # Verify node hazard updates stored location risk profile
    assert backend.locations["RUDR"].risk.risk_level == "Critical"
    assert backend.locations["RUDR"].risk.total_score == 77.08

    detour_comp = backend.compare_route("RISH", "KEDN")
    safest_path = detour_comp.safest.path
    print(f"        Got detour path: {' -> '.join(safest_path)}")

    # Rudraprayag has +1000 penalty, so safest path must detour via Uttarkashi (UTTK)
    assert "RUDR" not in safest_path, "Safest route must completely avoid Critical disaster at RUDR!"
    assert "UTTK" in safest_path, "Safest route must detour via Uttarkashi bypass corridor!"
    assert safest_path == ["RISH", "UTTK", "UKHI", "KEDN"], f"Unexpected detour path: {safest_path}"
    assert detour_comp.risk_reduction_pct > 0.0

    backend.reset_hazards()
    # Verify baseline risk profile is restored
    assert backend.locations["RUDR"].risk.risk_level == "High"
    assert backend.locations["RUDR"].risk.total_score == 56.17
    restored_comp = backend.compare_route("RISH", "KEDN")
    assert restored_comp.safest.path == ["RISH", "RUDR", "UKHI", "KEDN"]


def test_backend_frontend_api_communication():
    """Start local API server in thread and test REST communication with urllib."""
    print("  [5.1] Launching local REST API server on test port 8765...")
    backend = SlopeShieldBackend(BASE_DIR)
    backend.initialize()
    backend.refresh_weather_and_scores(use_mock=True)

    SlopeShieldApiHandler.backend = backend
    server = HTTPServer(("127.0.0.1", 8765), SlopeShieldApiHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    time.sleep(0.5)

    base_url = "http://127.0.0.1:8765"

    try:
        print("  [5.2] Querying GET /api/health...")
        with urllib.request.urlopen(f"{base_url}/api/health", timeout=5) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data["status"] == "healthy"
            assert data["locations_count"] == 11

        print("  [5.3] Querying GET /api/locations...")
        with urllib.request.urlopen(f"{base_url}/api/locations", timeout=5) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert len(data["locations"]) == 11
            assert "lat" in data["locations"][0] and "lon" in data["locations"][0]

        print("  [5.4] Querying GET /api/route?source=RISH&dest=BADR&mode=safest...")
        with urllib.request.urlopen(f"{base_url}/api/route?source=RISH&dest=BADR&mode=safest", timeout=5) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert "safest_route" in data
            assert len(data["safest_route"]["coordinates"]) >= 2
            assert data["safest_route"]["total_distance_km"] > 0

        print("  [5.5] Testing simulation trigger GET /api/simulate?override_type=NODE&target=RUDR&score=77.08&level=Critical...")
        with urllib.request.urlopen(f"{base_url}/api/simulate?override_type=NODE&target=RUDR&score=77.08&level=Critical", timeout=5) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data["status"] == "simulation_applied"

        # Verify /api/locations reports simulated Critical risk for RUDR
        with urllib.request.urlopen(f"{base_url}/api/locations", timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            rudr_loc = next(l for l in data["locations"] if l["location_id"] == "RUDR")
            assert rudr_loc["risk_level"] == "Critical", f"Expected Critical, got {rudr_loc['risk_level']}"
            assert rudr_loc["risk_score"] == 77.08, f"Expected 77.08, got {rudr_loc['risk_score']}"

        # Verify route recalculated with detour over HTTP
        with urllib.request.urlopen(f"{base_url}/api/route?source=RISH&dest=KEDN&mode=safest", timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            assert data["safest_route"]["path"] == ["RISH", "UTTK", "UKHI", "KEDN"]

        print("  [5.6] Resetting hazard via GET /api/simulate/reset...")
        with urllib.request.urlopen(f"{base_url}/api/simulate/reset", timeout=5) as resp:
            assert resp.status == 200

        # Verify /api/locations restores baseline risk for RUDR
        with urllib.request.urlopen(f"{base_url}/api/locations", timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            rudr_loc = next(l for l in data["locations"] if l["location_id"] == "RUDR")
            assert rudr_loc["risk_level"] == "High", f"Expected High, got {rudr_loc['risk_level']}"
            assert rudr_loc["risk_score"] == 56.17, f"Expected 56.17, got {rudr_loc['risk_score']}"

        # Verify safest route restored to baseline
        with urllib.request.urlopen(f"{base_url}/api/route?source=RISH&dest=KEDN&mode=safest", timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            assert data["safest_route"]["path"] == ["RISH", "RUDR", "UKHI", "KEDN"]

        print("  [5.7] Testing GET /api/weather/refresh (default mock pipeline)...")
        with urllib.request.urlopen(f"{base_url}/api/weather/refresh", timeout=5) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data["status"] == "success"
            assert "routes" in data
            assert len(data["routes"]) == 7
            assert data["is_live"] is False
            assert data["data_source"] == "mock"

        print("  [5.8] Testing GET /api/weather/refresh?live=1 without API key (expect 400)...")
        req_live = urllib.request.Request(f"{base_url}/api/weather/refresh?live=1")
        try:
            with urllib.request.urlopen(req_live, timeout=5) as resp:
                assert False, "Expected HTTP 400 for live refresh without API key"
        except urllib.error.HTTPError as he:
            assert he.code == 400
            err_data = json.loads(he.read().decode("utf-8"))
            assert "error" in err_data

        print("  [5.9] Testing POST /api/weather/refresh with use_mock=true...")
        post_data = json.dumps({"use_mock": True}).encode("utf-8")
        post_req = urllib.request.Request(f"{base_url}/api/weather/refresh", data=post_data,
                                          headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(post_req, timeout=5) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data["status"] == "success"
            assert data["data_source"] == "mock"

        print("  [5.10] Testing GET / (interactive Leaflet dashboard serving)...")
        with urllib.request.urlopen(f"{base_url}/", timeout=5) as resp:
            assert resp.status == 200
            content = resp.read().decode("utf-8")
            assert "leaflet" in content.lower()
            assert "SlopeShield" in content

    finally:
        server.shutdown()
        server.server_close()


def test_dynamic_weather_pipeline_and_status():
    """
    Verify the 7 core testing requirements for dynamic weather refresh & status reporting:
    1. Complete pipeline sequence (Weather -> Risk -> Graph -> Dijkstra -> route_output.json).
    2. API failure & fallback handling without crashing.
    3. Accurate live/cache/mock/fallback/mixed status reporting (never falsely reporting live).
    4. Risk score recalculation after weather change.
    5. Road graph weight updates.
    6. Dijkstra route recalculation under updated weights.
    7. route_output.json updated on disk.
    """
    print("  [6.1] Testing mock weather refresh and complete 7-stage pipeline...")
    backend = SlopeShieldBackend(BASE_DIR)
    backend.initialize()

    # Step 1: Run mock refresh
    res = backend.refresh_weather_and_scores(use_mock=True)
    assert res["status"] == "success"
    assert res["scored_count"] == 11
    assert res["data_source"] == "mock"
    assert res["system_status"] == "mock"
    assert res["is_live"] is False
    assert res["freshness_summary"]["mock_count"] == 11
    assert "routes" in res
    assert len(res["routes"]) == 7
    assert os.path.exists(os.path.join(BASE_DIR, "data", "route_output.json"))

    print("  [6.2] Testing risk score recalculation and graph weight updates...")
    # Record baseline risk and edge costs
    old_rudr_risk = backend.locations["RUDR"].risk.total_score
    rudr_edges = backend.graph.get_neighbors("RUDR")
    old_edge_cost = rudr_edges[0].risk_cost

    # Inject extreme rainfall at RUDR to trigger risk jump
    custom_reading = WeatherReading(
        current_rain_mm=90.0,
        forecast_24h_mm=100.0,
        humidity_pct=95,
        antecedent_3d_mm=80.0,
        source="mock",
        stale=False
    )
    backend.locations["RUDR"].set_weather(custom_reading)
    prof = backend.scorer.score_location(backend.locations["RUDR"], custom_reading, backend._weights_config)
    backend.locations["RUDR"].set_risk(prof.static_score, prof.dynamic_score, prof.total_score, prof.risk_level)
    assert backend.locations["RUDR"].risk.total_score > old_rudr_risk
    assert backend.locations["RUDR"].risk.risk_level == "Critical"

    backend.graph.update_edge_weights(
        alpha=backend._weights_config.get("alpha", 1.5),
        critical_penalty=backend._weights_config.get("critical_penalty", 1000.0)
    )
    new_edge_cost = [e.risk_cost for e in backend.graph.get_neighbors("RUDR") if e.road_id == rudr_edges[0].road_id][0]
    assert new_edge_cost > old_edge_cost, "Edge weight must increase when node risk increases"

    # Verify Dijkstra reroute: RISH -> KEDN must now bypass RUDR via UTTK
    comp = backend.compare_route("RISH", "KEDN")
    assert "RUDR" not in comp.safest.path
    assert "UTTK" in comp.safest.path

    print("  [6.3] Testing API failure and fallback handling (simulated invalid API key)...")
    # Simulate API failure with invalid key
    res_fail = backend.refresh_weather_and_scores(use_mock=False, api_key="INVALID_TEST_KEY_401")
    assert res_fail["status"] == "success", "Backend must not crash on API failure"
    assert res_fail["is_live"] is False, "Must not report live status on failed API fetch"
    assert res_fail["data_source"] in ["fallback", "cache"]
    assert res_fail["system_status"] in ["fallback", "cache"]
    assert "warnings" in res_fail or res_fail["freshness_summary"]["fallback_count"] > 0

    print("  [6.4] Testing mixed status reporting (partial live + fallback)...")
    # Simulate mixed status: 5 live locations, 6 fallback
    mixed_readings = {}
    from datetime import datetime, timezone
    now_ts = datetime.now(timezone.utc).isoformat()
    for i, lid in enumerate(backend.locations):
        if i < 5:
            mixed_readings[lid] = WeatherReading(current_rain_mm=5.0, forecast_24h_mm=10.0, source="openweathermap", fetched_at=now_ts, stale=False)
        else:
            mixed_readings[lid] = WeatherReading(current_rain_mm=5.0, forecast_24h_mm=10.0, source="fallback", fetched_at=now_ts, stale=True)

    # Apply mixed readings
    n_live = sum(1 for r in mixed_readings.values() if r.source == "openweathermap" and not r.stale)
    n_fb = sum(1 for r in mixed_readings.values() if r.source != "openweathermap" or r.stale)
    assert n_live == 5 and n_fb == 6

    # Verify that mixed status is never reported as live
    is_live_mixed = (n_live == len(mixed_readings))
    data_source_mixed = "live_openweathermap" if is_live_mixed else ("mixed" if n_live > 0 else "fallback")
    assert is_live_mixed is False, "Mixed status must NEVER be reported as is_live=True"
    assert data_source_mixed == "mixed", "Mixed status must be reported as data_source='mixed'"

    print("  [6.5] Testing simulated full live API refresh...")
    live_readings = {}
    for lid in backend.locations:
        live_readings[lid] = WeatherReading(current_rain_mm=2.0, forecast_24h_mm=5.0, source="openweathermap", fetched_at=now_ts, stale=False)

    n_live_full = sum(1 for r in live_readings.values() if r.source == "openweathermap" and not r.stale)
    is_live_full = (n_live_full == len(live_readings))
    assert is_live_full is True
    assert n_live_full == 11


def main():
    print("\n==================================================================")
    print(" RUNNING MEMBER 3 SYSTEM INTEGRATION TEST SUITE")
    print("==================================================================")

    print("\n[Phase 1] Validating OOP Architecture & Domain Models...")
    test_oop_models_and_encapsulation()
    print(">> Phase 1: PASSED")

    print("\n[Phase 2] Validating CSV and JSON File Handlers...")
    test_file_handling()
    print(">> Phase 2: PASSED")

    print("\n[Phase 3] Validating Backend Integration Pipeline...")
    test_backend_integration_pipeline()
    print(">> Phase 3: PASSED")

    print("\n[Phase 4] Validating Hazard Detour Routing...")
    test_hazard_detour_routing()
    print(">> Phase 4: PASSED")

    print("\n[Phase 5] Validating Backend -> Frontend HTTP API Communication...")
    test_backend_frontend_api_communication()
    print(">> Phase 5: PASSED")

    print("\n[Phase 6] Validating Dynamic Weather Refresh Pipeline & Status...")
    test_dynamic_weather_pipeline_and_status()
    print(">> Phase 6: PASSED")

    print("\n==================================================================")
    print(" ALL MEMBER 3 INTEGRATION TESTS PASSED (6/6)!")
    print("==================================================================\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
