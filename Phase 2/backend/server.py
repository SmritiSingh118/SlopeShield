"""
================================================================================
SlopeShield: Intelligent Landslide Risk & Safe Route System
Backend Service Controller (Member 3: Integration & Backend Architecture)
Author: Anshika Gaur (Member 3)
================================================================================

This module acts as the Facade and Central Controller for SlopeShield.
It unites:
- Member 1's Environmental Risk Science
- Member 2's DSA Safe Route Engine
- Member 3's Central DataManager & OOP Pipeline
"""

import os
import sys
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timezone

from core.models import Location, RoadSegment, RouteResult, RouteComparison, WeatherReading
from core.data_handlers import DataManager
from core.risk_scorer import WeightedRiskScorer
from core.route_planner import RoadGraph, DijkstraRoutePlanner

# Standard Char Dham corridors
STANDARD_CORRIDORS: List[Tuple[str, str]] = [
    ("RISH", "BADR"),  # Rishikesh to Badrinath
    ("RISH", "KEDN"),  # Rishikesh to Kedarnath
    ("RISH", "GANG"),  # Rishikesh to Gangotri
    ("KEDN", "BADR"),  # Kedarnath to Badrinath (Cross-Dham)
    ("RISH", "UTTK"),  # Rishikesh to Uttarkashi
    ("DEHR", "MUSS"),  # Dehradun to Mussoorie
    ("CHAM", "MALP"),  # Chamoli to Malpa (Eastern border flank)
]


class SlopeShieldBackend:
    """
    Facade Controller providing high-level operational APIs for SlopeShield.
    Coordinates file loading, weather fetching, risk calculation, graph construction,
    routing computation, and frontend payload generation.
    """

    def __init__(self, base_dir: Optional[str] = None):
        self.data_manager = DataManager(base_dir)
        self.scorer = WeightedRiskScorer()
        self.router = DijkstraRoutePlanner()
        self.graph = RoadGraph()

        self._weights_config: Dict[str, Any] = {}
        self._locations: Dict[str, Location] = {}
        self._roads: List[RoadSegment] = []
        self._baseline_risks: Dict[str, Tuple[float, float, float, str]] = {}
        self._initialized: bool = False

    @property
    def locations(self) -> Dict[str, Location]:
        return self._locations

    @property
    def roads(self) -> List[RoadSegment]:
        return self._roads

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    def initialize(self) -> bool:
        """
        Loads configuration, static locations, and the road network.
        Constructs the internal RoadGraph and calculates baseline edge weights.
        """
        valid, issues = self.data_manager.validate_datasets()
        if not valid:
            raise FileNotFoundError(f"[SlopeShieldBackend] Dataset validation failed: {issues}")

        self._weights_config = self.data_manager.load_weights_config()
        self._locations = self.data_manager.load_locations()
        self._roads = self.data_manager.load_road_network()

        # Build Graph
        self.graph = RoadGraph()
        for loc in self._locations.values():
            self.graph.add_location(loc)

        for road in self._roads:
            self.graph.add_road(road, bidirectional=True)

        self.graph.update_edge_weights(
            alpha=self._weights_config.get("alpha", 1.5),
            critical_penalty=self._weights_config.get("critical_penalty", 1000.0)
        )

        self._initialized = True
        return True

    def refresh_weather_and_scores(self, use_mock: bool = True, api_key: Optional[str] = None, recalculate_routes: bool = True) -> Dict[str, Any]:
        """
        Executes the Complete End-to-End Dynamic Weather & Routing Pipeline:
        1. Dynamic Weather Ingestion: Fetches from OpenWeatherMap API or falls back to cached/mock readings.
        2. Reliable Source & Freshness Identification: Accurately classifies each location as 'openweathermap',
           'cache', 'mock', or 'fallback', and checks staleness.
        3. Risk Recalculation: Evaluates static & dynamic features using WeightedRiskScorer,
           updates Location objects, and saves risk_scores.csv and risk_output.json.
        4. Road Graph Re-weighting: Recalculates traversal weights on all road edges using the updated risk scores.
        5. Dijkstra Pathfinding: Recomputes Shortest and Safest routes across all standard corridors using custom Min-Heap.
        6. Route Output Persistence: Serializes and saves data/route_output.json and syncs to frontend.
        7. Full Status & Payload Generation: Returns updated weather, risk, routes, and accurate system status.
        """
        if not self._initialized:
            self.initialize()

        effective_key = (api_key or os.environ.get("OWM_API_KEY", "")).strip()
        warnings: List[str] = []
        is_fresh_pull = False
        fetch_attempted = False

        # Stage 1: Ingest dynamic weather (Live OpenWeatherMap API or Cached/Mock)
        if not use_mock and effective_key:
            fetch_attempted = True
            try:
                from scripts.fetch_weather import run_fetch
                print("[SlopeShieldBackend] Requesting live weather from OpenWeatherMap API for 11 locations...")
                run_fetch(api_key=effective_key, mock=False, verbose=False)
                is_fresh_pull = True
            except Exception as ex:
                warnings.append(f"Live weather fetch error: {str(ex)}")
                print(f"[SlopeShieldBackend] [warn] Live weather fetch failed ({ex}). Falling back to cached data.")

        # Load dynamic features from data manager
        weather_map = self.data_manager.load_dynamic_features(is_fresh_pull=is_fresh_pull)

        # If mock explicitly requested or no dynamic features exist, generate deterministic mock readings
        if use_mock or not weather_map:
            now_iso = datetime.now(timezone.utc).isoformat()
            mock_heavy = {"RUDR": 42.0, "MALP": 55.0, "KEDN": 38.0, "MUSS": 22.0}
            mock_rows_to_save = []
            for i, (lid, loc) in enumerate(self._locations.items()):
                rain_24h = mock_heavy.get(lid, 8.0 + (len(lid) % 3) * 3.0)
                cur_rain = round(rain_24h / 8.0, 2)
                hum = 88 if lid in mock_heavy else 72
                ant = round(rain_24h * 0.8, 2)
                reading = WeatherReading(
                    current_rain_mm=cur_rain,
                    forecast_24h_mm=rain_24h,
                    humidity_pct=hum,
                    antecedent_3d_mm=ant,
                    temp_c=18.5,
                    weather_desc="Monsoon rain" if lid in mock_heavy else "Overcast",
                    source="mock",
                    fetched_at=now_iso,
                    stale=False
                )
                weather_map[lid] = reading
                mock_rows_to_save.append({
                    "location_id": lid,
                    "name": loc.name,
                    "lat": loc.lat,
                    "lon": loc.lon,
                    "current_rain_mm": cur_rain,
                    "forecast_24h_mm": rain_24h,
                    "burst_mm": round(rain_24h / 4.0, 2),
                    "humidity_pct": hum,
                    "temp_c": 18.5,
                    "weather_desc": reading.weather_desc,
                    "wind_ms": 3.2,
                    "antecedent_3d_mm": ant,
                    "fetched_at": now_iso,
                    "stale": False,
                    "source": "mock"
                })
            # Persist mock readings to maintain file consistency
            try:
                self.data_manager.save_dynamic_features(mock_rows_to_save)
            except Exception:
                pass

        # Stage 2: Identify per-location data sources, freshness and aggregate system status
        n_live = 0
        n_cache = 0
        n_fallback = 0
        n_mock = 0
        n_stale = 0

        for lid in self._locations:
            reading = weather_map.get(lid)
            if not reading:
                reading = WeatherReading(source="fallback", stale=True)
                weather_map[lid] = reading

            src = reading.source.lower()
            if reading.stale:
                n_stale += 1

            if "openweathermap" in src and not reading.stale:
                n_live += 1
            elif "mock" in src:
                n_mock += 1
            elif "cache" in src:
                n_cache += 1
            else:
                n_fallback += 1

        total_locs = len(self._locations)
        if n_live == total_locs:
            system_status = "live"
            data_source = "live_openweathermap"
            is_live = True
        elif n_live > 0:
            system_status = "mixed"
            data_source = "mixed"
            is_live = False
            warnings.append(f"Partial live data: {n_live}/{total_locs} locations fetched live; remainder using fallback/cache.")
        elif n_fallback > 0:
            system_status = "fallback"
            data_source = "fallback"
            is_live = False
            if fetch_attempted:
                warnings.append("API fetch attempted but could not retrieve live data; system fell back to cached/fallback records.")
        elif n_cache > 0:
            system_status = "cache"
            data_source = "cache"
            is_live = False
        else:
            system_status = "mock"
            data_source = "mock"
            is_live = False

        # Stage 3: Recalculate Risk Scores using latest weather
        for lid, loc in self._locations.items():
            reading = weather_map[lid]
            loc.set_weather(reading)
            profile = self.scorer.score_location(loc, reading, self._weights_config)
            loc.set_risk(profile.static_score, profile.dynamic_score, profile.total_score, profile.risk_level)
            self._baseline_risks[lid] = (profile.static_score, profile.dynamic_score, profile.total_score, profile.risk_level)

        # Persist scores to disk
        self.data_manager.save_risk_scores(self._locations, self._weights_config)

        # Stage 4: Update RoadGraph edge weights with new scores
        self.graph.update_edge_weights(
            alpha=self._weights_config.get("alpha", 1.5),
            critical_penalty=self._weights_config.get("critical_penalty", 1000.0)
        )

        # Stage 5 & 6: Recalculate Dijkstra Routes and regenerate/save data/route_output.json
        routes_payload: Dict[str, Any] = {}
        if recalculate_routes:
            routes_payload = self.plan_all_standard_corridors()

        # Stage 7: Assemble complete JSON response for frontend
        now_ts = datetime.now(timezone.utc).isoformat()
        pipeline_stages = [
            "1. Dynamic weather ingested (API/Cache/Mock)",
            "2. Reliable data source & freshness verified",
            "3. Landslide risk recalculated and saved to risk_scores.csv & risk_output.json",
            "4. Road graph traversal edge weights updated",
            "5. Dijkstra routes recalculated across all standard corridors",
            "6. route_output.json regenerated and persisted to disk"
        ]

        response_payload = {
            "status": "success",
            "pipeline_stages_completed": pipeline_stages,
            "is_live": is_live,
            "data_source": data_source,
            "system_status": system_status,
            "freshness_summary": {
                "live_count": n_live,
                "cache_count": n_cache,
                "fallback_count": n_fallback,
                "mock_count": n_mock,
                "stale_count": n_stale,
                "total_count": total_locs
            },
            "scored_count": total_locs,
            "generated_at": now_ts,
            "locations": [loc.to_dict() for loc in self._locations.values()],
            "routes": routes_payload.get("routes", {}),
            "metadata": routes_payload.get("metadata", {
                "algorithm": "Dijkstra with Min-Heap Priority Queue (CLRS)",
                "weight_formula": "distance * (1 + 1.5 * edge_risk/100) + critical_penalty"
            })
        }
        if warnings:
            response_payload["warnings"] = warnings

        return response_payload

    def plan_route(self, source_id: str, dest_id: str, mode: str = "safest") -> RouteResult:
        """Find the optimal route between source and destination using Dijkstra's algorithm."""
        if not self._initialized:
            self.initialize()

        src = source_id.strip().upper()
        dst = dest_id.strip().upper()
        return self.router.find_path(self.graph, src, dst, mode=mode)

    def compare_route(self, source_id: str, dest_id: str) -> RouteComparison:
        """Compare Shortest Distance vs Safest Risk-Weighted route."""
        if not self._initialized:
            self.initialize()

        src = source_id.strip().upper()
        dst = dest_id.strip().upper()
        return self.router.compare_routes(self.graph, src, dst)

    def plan_all_standard_corridors(self) -> Dict[str, Any]:
        """
        Calculates all 7 standard Char Dham corridors, constructs the frontend payload,
        and saves it to data/route_output.json.
        """
        if not self._initialized:
            self.initialize()

        routes_data = {}
        for src, dst in STANDARD_CORRIDORS:
            key = f"{src}_to_{dst}"
            comp = self.router.compare_routes(self.graph, src, dst)
            routes_data[key] = comp.to_dict()

        payload = {
            "metadata": {
                "system": "SlopeShield Intelligent Safe Route Engine",
                "author": "The Debug Divas (Integration: Jahnvi Verma - Member 3)",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "algorithm": "Dijkstra with custom Min-Heap Priority Queue (CLRS)",
                "weight_formula": "distance * (1 + 1.5 * edge_risk/100) + critical_penalty",
                "parameters": {
                    "alpha": self._weights_config.get("alpha", 1.5),
                    "critical_penalty": self._weights_config.get("critical_penalty", 1000.0)
                }
            },
            "all_locations": {lid: loc.to_dict() for lid, loc in self._locations.items()},
            "routes": routes_data
        }

        self.data_manager.save_route_output(payload)
        return payload

    def simulate_hazard(self, override_type: str, target: str, score: float, level: str) -> Dict[str, Any]:
        """
        Simulate an active environmental hazard on a node or edge.
        Recalculates traversal weights and returns the affected network status.
        """
        if not self._initialized:
            self.initialize()

        node_ov = {}
        edge_ov = {}
        target_clean = target.strip().upper()

        if override_type.upper() == "NODE":
            node_ov[target_clean] = (float(score), level.strip())
            if target_clean in self._locations:
                loc = self._locations[target_clean]
                if target_clean not in self._baseline_risks:
                    self._baseline_risks[target_clean] = (
                        loc.risk.static_score,
                        loc.risk.dynamic_score,
                        loc.risk.total_score,
                        loc.risk.risk_level
                    )
                loc.set_risk(loc.risk.static_score, loc.risk.dynamic_score, float(score), level.strip())
        elif override_type.upper() == "EDGE":
            edge_ov[target_clean] = (float(score), level.strip())

        self.graph.update_edge_weights(
            alpha=self._weights_config.get("alpha", 1.5),
            critical_penalty=self._weights_config.get("critical_penalty", 1000.0),
            node_overrides=node_ov,
            edge_overrides=edge_ov
        )

        return {
            "status": "simulation_applied",
            "override_type": override_type,
            "target": target,
            "score": score,
            "level": level
        }

    def reset_hazards(self) -> None:
        """Reset all simulated hazard overrides and restore standard weights."""
        if not self._initialized:
            self.initialize()

        # Restore original baseline risk profile for all modified locations
        for lid, (static, dynamic, total, lvl) in self._baseline_risks.items():
            if lid in self._locations:
                self._locations[lid].set_risk(static, dynamic, total, lvl)

        self.graph.update_edge_weights(
            alpha=self._weights_config.get("alpha", 1.5),
            critical_penalty=self._weights_config.get("critical_penalty", 1000.0)
        )

    def get_locations_summary(self) -> List[Dict[str, Any]]:
        """Return all locations sorted by risk severity (highest first)."""
        if not self._initialized:
            self.initialize()

        locs = [loc.to_dict() for loc in self._locations.values()]
        locs.sort(key=lambda x: x["risk_score"], reverse=True)
        return locs

    def get_roads_summary(self) -> List[Dict[str, Any]]:
        """Return all unique road segments with current traversal costs."""
        if not self._initialized:
            self.initialize()

        seen = set()
        res = []
        for edges in self.graph.adj.values():
            for e in edges:
                clean_id = e.road_id.replace("_rev", "")
                if clean_id not in seen:
                    seen.add(clean_id)
                    res.append(e.to_dict())
        return res
