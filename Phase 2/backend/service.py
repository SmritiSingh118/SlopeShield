"""
================================================================================
SlopeShield: Intelligent Landslide Risk & Safe Route System
Backend Service Controller (Member 3: Integration & Backend Architecture)
Author: Anshika Gaur (Member 3)
================================================================================

This module acts as the Facade and Central Controller for SlopeShield.
It unites:
- Member 1's Environmental Risk Science & Dynamic Weather Ingestion
- Member 2's DSA Safe Route Engine (Adjacency Graph, Min-Heap, Dijkstra)
- Member 3's Central DataManager, OOP Pipeline, and REST Integration
- Member 4's Leaflet Map Presentation Contract
"""

import os
import sys
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timezone

from core.models import Location, RoadSegment, RouteResult, RouteComparison, WeatherReading
from core.data_handlers import DataManager
from core.weather_service import WeatherService
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
    Enforces strict pipeline order:
      input data -> dynamic weather/risk assessment -> graph weight updates -> route calculation -> response/export.
    """

    def __init__(self, base_dir: Optional[str] = None):
        self.data_manager = DataManager(base_dir)
        self.weather_service = WeatherService(base_dir)
        self.scorer = WeightedRiskScorer()
        self.router = DijkstraRoutePlanner()
        self.graph = RoadGraph()

        self._weights_config: Dict[str, Any] = {}
        self._locations: Dict[str, Location] = {}
        self._roads: List[RoadSegment] = []
        self._active_node_overrides: Dict[str, Tuple[float, str]] = {}
        self._active_edge_overrides: Dict[str, Tuple[float, str]] = {}
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
        Loads configuration, static locations, and the road network with OSM geometry.
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

    def get_weather_status(self) -> Dict[str, Any]:
        """Returns current weather pipeline status and verification metadata."""
        return self.weather_service.last_status

    def refresh_weather_and_scores(self, mode: str = "mock", api_key: Optional[str] = None,
                                   use_mock: Optional[bool] = None) -> Dict[str, Any]:
        """
        Executes the Environmental Risk Pipeline:
        1. Ingests dynamic weather (Live OpenWeatherMap or Mock).
        2. Scores all 11 locations using WeightedRiskScorer.
        3. Updates Location states and persists data/risk_scores.csv & data/risk_output.json.
        4. Re-weights graph edges with fresh risk assessments.
        5. Recomputes standard routes and persists data/route_output.json.
        """
        if not self._initialized:
            self.initialize()

        # Backwards compatibility with use_mock flag
        if use_mock is not None:
            mode = "mock" if use_mock else "live"

        locs_list = [
            {"location_id": loc.id, "name": loc.name, "lat": loc.lat, "lon": loc.lon}
            for loc in self._locations.values()
        ]

        # Fetch weather (live with graceful fallback, or calibrated mock)
        readings, weather_meta = self.weather_service.fetch_weather(locs_list, mode=mode, api_key=api_key)

        # Score each location with fresh readings
        for lid, loc in self._locations.items():
            reading = readings.get(lid, WeatherReading())
            loc.set_weather(reading)
            profile = self.scorer.score_location(loc, reading, self._weights_config)
            loc.set_risk(profile.static_score, profile.dynamic_score, profile.total_score, profile.risk_level)

        # Persist scores to disk
        self.data_manager.save_risk_scores(self._locations, self._weights_config)

        # Update RoadGraph edge weights with new scores
        self.graph.update_edge_weights(
            alpha=self._weights_config.get("alpha", 1.5),
            critical_penalty=self._weights_config.get("critical_penalty", 1000.0),
            node_overrides=self._active_node_overrides,
            edge_overrides=self._active_edge_overrides
        )

        # Refresh exported standard corridors in data/route_output.json
        self.plan_all_standard_corridors()

        return {
            "status": "success",
            "scored_count": len(self._locations),
            "weather_mode": weather_meta.get("weather_mode", mode),
            "is_live_verified": weather_meta.get("is_live_verified", False),
            "weather_source": weather_meta.get("source", "unknown"),
            "weather_message": weather_meta.get("message", ""),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "locations": [loc.to_dict() for loc in self._locations.values()]
        }

    def plan_route(self, source_id: str, dest_id: str, mode: str = "safest") -> RouteResult:
        """Find the optimal route between source and destination using Dijkstra's algorithm."""
        if not self._initialized:
            self.initialize()

        src = source_id.strip().upper()
        dst = dest_id.strip().upper()

        if src not in self._locations or dst not in self._locations:
            res = RouteResult(src, dst, mode)
            res.error_message = f"Invalid location: source '{src}' or destination '{dst}' not found in network."
            return res

        return self.router.find_path(self.graph, src, dst, mode=mode)

    def compare_route(self, source_id: str, dest_id: str) -> RouteComparison:
        """Compare Shortest Distance vs Safest Risk-Weighted route."""
        if not self._initialized:
            self.initialize()

        src = source_id.strip().upper()
        dst = dest_id.strip().upper()

        if src not in self._locations or dst not in self._locations:
            shortest = RouteResult(src, dst, "shortest")
            shortest.error_message = f"Invalid location: source '{src}' or destination '{dst}' not found in network."
            safest = RouteResult(src, dst, "safest")
            safest.error_message = shortest.error_message
            return RouteComparison(shortest, safest)

        return self.router.compare_routes(self.graph, src, dst)

    def plan_all_standard_corridors(self) -> Dict[str, Any]:
        """
        Calculates all 7 standard Char Dham corridors, constructs the frontend payload,
        and saves it atomically to data/route_output.json.
        """
        if not self._initialized:
            self.initialize()

        routes_data = {}
        for src, dst in STANDARD_CORRIDORS:
            key = f"{src}_to_{dst}"
            comp = self.router.compare_routes(self.graph, src, dst)
            routes_data[key] = comp.to_dict()

        weather_status = self.weather_service.last_status

        payload = {
            "metadata": {
                "system": "SlopeShield Intelligent Safe Route Engine",
                "author": "The Debug Divas (Integration Lead: Anshika Gaur - Member 3)",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "algorithm": "Dijkstra with custom Min-Heap Priority Queue (CLRS)",
                "weight_formula": "distance * (1 + 1.5 * edge_risk/100) + critical_penalty",
                "weather_integration": {
                    "mode": weather_status.get("weather_mode", "mock"),
                    "is_live_verified": weather_status.get("is_live_verified", False),
                    "source": weather_status.get("source", "calibrated_mock"),
                    "status": weather_status.get("message", "")
                },
                "road_geometry": {
                    "source": "OpenStreetMap / OSRM",
                    "status": "Verified continuous highway polylines"
                },
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
        Does not permanently alter baseline data.
        """
        if not self._initialized:
            self.initialize()

        t_type = override_type.upper().strip()
        tgt = target.strip().upper()

        if t_type == "NODE":
            self._active_node_overrides[tgt] = (float(score), level.strip())
        elif t_type == "EDGE":
            self._active_edge_overrides[tgt] = (float(score), level.strip())

        self.graph.update_edge_weights(
            alpha=self._weights_config.get("alpha", 1.5),
            critical_penalty=self._weights_config.get("critical_penalty", 1000.0),
            node_overrides=self._active_node_overrides,
            edge_overrides=self._active_edge_overrides
        )

        return {
            "status": "simulation_applied",
            "override_type": t_type,
            "target": tgt,
            "score": score,
            "level": level,
            "active_node_overrides": self._active_node_overrides,
            "active_edge_overrides": self._active_edge_overrides
        }

    def reset_hazards(self) -> None:
        """Reset all simulated hazard overrides and restore exact baseline weights."""
        if not self._initialized:
            self.initialize()

        self._active_node_overrides.clear()
        self._active_edge_overrides.clear()

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
        """Return all unique road segments with current traversal costs and road geometries."""
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
