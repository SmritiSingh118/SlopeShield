"""
================================================================================
SlopeShield: Intelligent Landslide Risk & Safe Route System
Core OOP Domain Models (Member 3: Architecture & Data Modeling)
Author: Anshika Gaur (Member 3)
================================================================================

This module encapsulates all core domain entities for SlopeShield:
1. Location: Encapsulated geographical node with static terrain features and risk state.
2. RoadSegment: Encapsulated highway edge with physical distance, risk weights, and geometry.
3. RiskProfile: Encapsulated risk evaluation state (static, dynamic, total, level).
4. WeatherReading: Encapsulated dynamic meteorological observation.
5. RouteResult: Encapsulated single-path traversal computation from Dijkstra with full geometry.
6. RouteComparison: Encapsulated comparison between shortest and safest paths.
"""

from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timezone
from abc import ABC, abstractmethod


class BaseEntity(ABC):
    """Abstract base entity providing standardized serialization contract."""
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Serialize entity state into a JSON-compatible dictionary."""
        pass


class RiskProfile(BaseEntity):
    """
    Encapsulates risk scores and categorical risk level for a location or road segment.
    Enforces score clamping to [0.0, 100.0] and validates categorical risk labels.
    """
    VALID_LEVELS = {"Low", "Moderate", "High", "Critical"}

    def __init__(self, static_score: float = 0.0, dynamic_score: float = 0.0, total_score: float = 0.0, risk_level: str = "Low"):
        self._static_score: float = max(0.0, min(100.0, float(static_score)))
        self._dynamic_score: float = max(0.0, min(100.0, float(dynamic_score)))
        self._total_score: float = max(0.0, min(100.0, float(total_score)))
        lvl = str(risk_level).strip()
        self._risk_level: str = lvl if lvl in self.VALID_LEVELS else "Low"

    @property
    def static_score(self) -> float:
        return self._static_score

    @property
    def dynamic_score(self) -> float:
        return self._dynamic_score

    @property
    def total_score(self) -> float:
        return self._total_score

    @property
    def risk_level(self) -> str:
        return self._risk_level

    def update_scores(self, static_score: float, dynamic_score: float, total_score: float, risk_level: Optional[str] = None):
        """Update scores and enforce risk level categorization and [0, 100] bounds."""
        self._static_score = round(max(0.0, min(100.0, float(static_score))), 2)
        self._dynamic_score = round(max(0.0, min(100.0, float(dynamic_score))), 2)
        self._total_score = round(max(0.0, min(100.0, float(total_score))), 2)

        if risk_level and str(risk_level).strip() in self.VALID_LEVELS:
            self._risk_level = str(risk_level).strip()
        else:
            # Enforce standard SlopeShield threshold cutoffs
            if self._total_score < 25.0:
                self._risk_level = "Low"
            elif self._total_score < 50.0:
                self._risk_level = "Moderate"
            elif self._total_score < 75.0:
                self._risk_level = "High"
            else:
                self._risk_level = "Critical"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "static_score": self._static_score,
            "dynamic_score": self._dynamic_score,
            "total_score": self._total_score,
            "risk_level": self._risk_level
        }

    def __repr__(self) -> str:
        return f"<RiskProfile total={self._total_score:.1f} level={self._risk_level}>"


class WeatherReading(BaseEntity):
    """Encapsulates weather observations and forecast metrics for a location."""
    def __init__(self, current_rain_mm: float = 0.0, forecast_24h_mm: float = 0.0,
                 humidity_pct: int = 50, antecedent_3d_mm: float = 0.0,
                 temp_c: float = 20.0, weather_desc: str = ""):
        self._current_rain_mm = max(0.0, float(current_rain_mm))
        self._forecast_24h_mm = max(0.0, float(forecast_24h_mm))
        self._humidity_pct = min(100, max(0, int(humidity_pct)))
        self._antecedent_3d_mm = max(0.0, float(antecedent_3d_mm))
        self._temp_c = float(temp_c)
        self._weather_desc = str(weather_desc)

    @property
    def current_rain_mm(self) -> float:
        return self._current_rain_mm

    @property
    def forecast_24h_mm(self) -> float:
        return self._forecast_24h_mm

    @property
    def humidity_pct(self) -> int:
        return self._humidity_pct

    @property
    def antecedent_3d_mm(self) -> float:
        return self._antecedent_3d_mm

    @property
    def temp_c(self) -> float:
        return self._temp_c

    @property
    def weather_desc(self) -> str:
        return self._weather_desc

    def to_dict(self) -> Dict[str, Any]:
        return {
            "current_rain_mm": self._current_rain_mm,
            "forecast_24h_mm": self._forecast_24h_mm,
            "humidity_pct": self._humidity_pct,
            "antecedent_3d_mm": self._antecedent_3d_mm,
            "temp_c": self._temp_c,
            "weather_desc": self._weather_desc
        }


class Location(BaseEntity):
    """
    Encapsulates a geographical pilgrimage/hub location in Uttarakhand.
    Encapsulates static terrain characteristics, weather observations, and risk evaluation.
    """
    def __init__(self, location_id: str, name: str, lat: float, lon: float, elevation_m: float = 0.0,
                 slope_deg: float = 0.0, soil_type: str = "loamy", landuse: str = "non-forest",
                 lithology_factor: float = 0.5, historical_count: int = 0, road_condition: str = "moderate",
                 static_notes: str = ""):
        lid = location_id.strip()
        if not lid:
            raise ValueError("[Location] location_id cannot be empty.")
        self._id = lid
        self._name = name.strip() if name else lid
        
        lat_f = float(lat)
        lon_f = float(lon)
        if not (-90.0 <= lat_f <= 90.0) or not (-180.0 <= lon_f <= 180.0):
            raise ValueError(f"[Location {lid}] Invalid GPS coordinates: lat={lat_f}, lon={lon_f}")
        self._lat = lat_f
        self._lon = lon_f

        self._elevation_m = max(-500.0, float(elevation_m))
        self._slope_deg = max(0.0, min(90.0, float(slope_deg)))
        self._soil_type = soil_type.strip().lower()
        self._landuse = landuse.strip().lower()
        self._lithology_factor = max(0.0, min(1.0, float(lithology_factor)))
        self._historical_count = max(0, int(historical_count))
        self._road_condition = road_condition.strip().lower()
        self._static_notes = static_notes.strip()

        # Encapsulated state objects
        self._risk = RiskProfile()
        self._weather = WeatherReading()

    @property
    def id(self) -> str:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @property
    def lat(self) -> float:
        return self._lat

    @property
    def lon(self) -> float:
        return self._lon

    @property
    def elevation_m(self) -> float:
        return self._elevation_m

    @property
    def slope_deg(self) -> float:
        return self._slope_deg

    @property
    def soil_type(self) -> str:
        return self._soil_type

    @property
    def landuse(self) -> str:
        return self._landuse

    @property
    def lithology_factor(self) -> float:
        return self._lithology_factor

    @property
    def historical_count(self) -> int:
        return self._historical_count

    @property
    def road_condition(self) -> str:
        return self._road_condition

    @property
    def static_notes(self) -> str:
        return self._static_notes

    @property
    def risk(self) -> RiskProfile:
        return self._risk

    @property
    def weather(self) -> WeatherReading:
        return self._weather

    def set_risk(self, static_score: float, dynamic_score: float, total_score: float, risk_level: Optional[str] = None):
        self._risk.update_scores(static_score, dynamic_score, total_score, risk_level)

    def set_weather(self, weather: WeatherReading):
        self._weather = weather

    def to_dict(self) -> Dict[str, Any]:
        return {
            "location_id": self._id,
            "name": self._name,
            "lat": self._lat,
            "lon": self._lon,
            "elevation_m": self._elevation_m,
            "slope_deg": self._slope_deg,
            "soil_type": self._soil_type,
            "landuse": self._landuse,
            "lithology_factor": self._lithology_factor,
            "historical_count": self._historical_count,
            "road_condition": self._road_condition,
            "risk_score": self._risk.total_score,
            "risk_level": self._risk.risk_level,
            "static_score": self._risk.static_score,
            "dynamic_score": self._risk.dynamic_score,
            "weather": self._weather.to_dict()
        }

    def __repr__(self) -> str:
        return f"<Location {self._id} '{self._name}' Risk={self._risk.risk_level}>"


class RoadSegment(BaseEntity):
    """
    Encapsulates a highway segment connecting two locations.
    Contains both physical route details, dynamically calculated risk costs,
    and verified OpenStreetMap road geometry.
    """
    def __init__(self, road_id: str, u: str, v: str, distance_km: float,
                 highway: str = "", road_type: str = "", description: str = "",
                 geometry: Optional[List[List[float]]] = None,
                 has_verified_geometry: bool = False):
        rid = road_id.strip()
        if not rid:
            raise ValueError("[RoadSegment] road_id cannot be empty.")
        self._road_id = rid

        u_id = u.strip()
        v_id = v.strip()
        if not u_id or not v_id:
            raise ValueError(f"[RoadSegment {rid}] Endpoint location IDs cannot be empty.")
        self._u = u_id
        self._v = v_id

        dist = float(distance_km)
        if dist <= 0.0:
            raise ValueError(f"[RoadSegment {rid}] distance_km must be strictly positive, got {dist}")
        self._distance_km = dist

        self._highway = highway.strip()
        self._road_type = road_type.strip()
        self._description = description.strip()

        # Road geometry: ordered list of [lat, lon] points
        self._geometry: List[List[float]] = geometry if geometry is not None else []
        self._has_verified_geometry: bool = has_verified_geometry

        # Dynamic risk-weighted routing attributes
        self._edge_risk_score: float = 0.0
        self._edge_risk_level: str = "Low"
        self._risk_multiplier: float = 1.0
        self._risk_cost: float = float(dist)
        self._critical_penalty_applied: bool = False

    @property
    def road_id(self) -> str:
        return self._road_id

    @property
    def u(self) -> str:
        return self._u

    @property
    def v(self) -> str:
        return self._v

    @property
    def distance_km(self) -> float:
        return self._distance_km

    @property
    def highway(self) -> str:
        return self._highway

    @property
    def road_type(self) -> str:
        return self._road_type

    @property
    def description(self) -> str:
        return self._description

    @property
    def geometry(self) -> List[List[float]]:
        return self._geometry

    @property
    def has_verified_geometry(self) -> bool:
        return self._has_verified_geometry

    def set_geometry(self, geometry: List[List[float]], has_verified: bool = True):
        self._geometry = geometry
        self._has_verified_geometry = has_verified

    def get_traversal_coordinates(self, forward: bool = True) -> List[List[float]]:
        """Returns ordered [lat, lon] coordinates in the direction of traversal."""
        if not self._geometry:
            return []
        if forward:
            return [list(pt) for pt in self._geometry]
        else:
            return [list(pt) for pt in reversed(self._geometry)]

    @property
    def edge_risk_score(self) -> float:
        return self._edge_risk_score

    @property
    def edge_risk_level(self) -> str:
        return self._edge_risk_level

    @property
    def risk_multiplier(self) -> float:
        return self._risk_multiplier

    @property
    def risk_cost(self) -> float:
        return self._risk_cost

    @property
    def critical_penalty_applied(self) -> bool:
        return self._critical_penalty_applied

    def calculate_weight(self, u_loc: Location, v_loc: Location, alpha: float = 1.5,
                         critical_penalty: float = 1000.0,
                         custom_override: Optional[Tuple[float, str]] = None) -> float:
        """
        Calculates risk-based edge weight integrating Member 1's scientific risk scores.
        Formula:
          R_edge = (R_u + R_v) / 2
          multiplier = 1.0 + alpha * (R_edge / 100.0)
          cost = distance_km * multiplier + (critical_penalty if Critical else 0.0)
        """
        if custom_override:
            r_edge, r_level = custom_override
            self._edge_risk_score = round(float(r_edge), 2)
            self._edge_risk_level = str(r_level)
        else:
            u_risk = u_loc.risk.total_score
            v_risk = v_loc.risk.total_score
            u_level = u_loc.risk.risk_level
            v_level = v_loc.risk.risk_level

            r_edge = round((u_risk + v_risk) / 2.0, 2)
            self._edge_risk_score = r_edge

            if u_level == "Critical" or v_level == "Critical" or r_edge >= 75.0:
                self._edge_risk_level = "Critical"
            elif u_level == "High" or v_level == "High" or r_edge >= 50.0:
                self._edge_risk_level = "High"
            elif r_edge >= 25.0:
                self._edge_risk_level = "Moderate"
            else:
                self._edge_risk_level = "Low"

        self._risk_multiplier = round(1.0 + alpha * (self._edge_risk_score / 100.0), 3)

        if self._edge_risk_level == "Critical":
            self._critical_penalty_applied = True
            self._risk_cost = round(self._distance_km * self._risk_multiplier + critical_penalty, 2)
        else:
            self._critical_penalty_applied = False
            self._risk_cost = round(self._distance_km * self._risk_multiplier, 2)

        return self._risk_cost

    def to_dict(self) -> Dict[str, Any]:
        return {
            "road_id": self._road_id,
            "from_id": self._u,
            "to_id": self._v,
            "distance_km": self._distance_km,
            "highway": self._highway,
            "road_type": self._road_type,
            "edge_risk_score": self._edge_risk_score,
            "edge_risk_level": self._edge_risk_level,
            "risk_multiplier": self._risk_multiplier,
            "risk_cost": self._risk_cost,
            "critical_penalty_applied": self._critical_penalty_applied,
            "has_verified_geometry": self._has_verified_geometry,
            "geometry": self._geometry
        }

    def __repr__(self) -> str:
        return f"<RoadSegment {self._road_id}: {self._u}->{self._v} ({self._distance_km}km, Risk={self._edge_risk_level})>"


class RouteResult(BaseEntity):
    """Encapsulates the complete result of a Dijkstra route computation."""
    def __init__(self, source_id: str, dest_id: str, mode: str):
        self.source_id = source_id
        self.dest_id = dest_id
        self.mode = mode
        self.found = False
        self.path: List[str] = []
        self.path_names: List[str] = []
        self.coordinates: List[List[float]] = []
        self.has_verified_geometry: bool = False
        self.is_schematic: bool = True
        self.total_distance_km: float = 0.0
        self.total_risk_cost: float = 0.0
        self.average_risk_score: float = 0.0
        self.max_risk_level: str = "Low"
        self.segments: List[Dict[str, Any]] = []
        self.error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        res = {
            "source_id": self.source_id,
            "dest_id": self.dest_id,
            "mode": self.mode,
            "found": self.found,
            "path": self.path,
            "path_names": self.path_names,
            "coordinates": self.coordinates,
            "has_verified_geometry": self.has_verified_geometry,
            "is_schematic": self.is_schematic,
            "total_distance_km": round(self.total_distance_km, 2),
            "total_risk_cost": round(self.total_risk_cost, 2),
            "average_risk_score": round(self.average_risk_score, 2),
            "max_risk_level": self.max_risk_level,
            "segments": self.segments
        }
        if self.error_message:
            res["error_message"] = self.error_message
        return res


class RouteComparison(BaseEntity):
    """Encapsulates comparison between Shortest Distance and Safest Risk paths."""
    def __init__(self, shortest: RouteResult, safest: RouteResult):
        self.shortest = shortest
        self.safest = safest
        self.is_identical = (shortest.path == safest.path) and shortest.found and safest.found
        self.distance_diff_km = round(safest.total_distance_km - shortest.total_distance_km, 2)
        self.cost_diff = round(safest.total_risk_cost - shortest.total_risk_cost, 2)

        if shortest.total_risk_cost > 0:
            reduction = (shortest.total_risk_cost - safest.total_risk_cost) / shortest.total_risk_cost * 100.0
            self.risk_reduction_pct = round(max(reduction, 0.0), 2)
        else:
            self.risk_reduction_pct = 0.0

        if not shortest.found or not safest.found:
            self.recommendation = "No route found between the specified locations."
        elif self.is_identical:
            self.recommendation = (f"The shortest path is already the safest path "
                                   f"({safest.total_distance_km} km, risk cost: {safest.total_risk_cost}).")
        else:
            self.recommendation = (f"Safest route takes {self.distance_diff_km:+.1f} km detour "
                                   f"to reduce risk cost by {self.risk_reduction_pct:.1f}% "
                                   f"(avoids active landslide hazards).")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.safest.source_id,
            "dest_id": self.safest.dest_id,
            "is_identical": self.is_identical,
            "distance_diff_km": self.distance_diff_km,
            "cost_diff": self.cost_diff,
            "risk_reduction_pct": self.risk_reduction_pct,
            "recommendation": self.recommendation,
            "has_verified_geometry": self.safest.has_verified_geometry,
            "shortest_route": self.shortest.to_dict(),
            "safest_route": self.safest.to_dict()
        }
