"""
================================================================================
SlopeShield: Intelligent Landslide Risk & Safe Route System
OOP Risk Scorer Hierarchy (Member 3 Architecture integrating Member 1 Logic)
Author: Anshika Gaur (Member 3)
================================================================================

This module encapsulates Member 1's scientific risk formulas in an OOP class hierarchy:
- BaseRiskScorer: Abstract Base Class defining the scoring contract.
- WeightedRiskScorer: Concrete implementation fulfilling the 60% static / 40% dynamic formula.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple
from core.models import Location, WeatherReading, RiskProfile


class BaseRiskScorer(ABC):
    """Abstract Base Class for risk calculation models."""

    @abstractmethod
    def score_location(self, location: Location, weather: WeatherReading, weights: Dict[str, Any]) -> RiskProfile:
        """Calculate and return an encapsulated RiskProfile for the given location and weather."""
        pass

    @abstractmethod
    def classify(self, total_score: float, thresholds: Dict[str, float]) -> str:
        """Classify numeric score into categorical hazard level."""
        pass


class WeightedRiskScorer(BaseRiskScorer):
    """
    Standard SlopeShield Weighted Risk Scorer.
    Implements Member 1's formula: 60% Static Terrain Susceptibility + 40% Dynamic Weather Trigger.
    """

    def classify(self, total_score: float, thresholds: Dict[str, float]) -> str:
        if total_score < thresholds.get("low_max", 25.0):
            return "Low"
        if total_score < thresholds.get("moderate_max", 50.0):
            return "Moderate"
        if total_score < thresholds.get("high_max", 75.0):
            return "High"
        return "Critical"

    def compute_static(self, location: Location, weights: Dict[str, Any]) -> Tuple[float, Dict[str, float]]:
        """
        Compute static terrain susceptibility (0-100).
        Slope (0.30), History (0.20), Soil (0.15), Landuse (0.12), Lithology (0.13), Road (0.10).
        """
        norm = weights.get("norm", {})
        lk = weights.get("lookup", {})
        s_w = weights.get("static", {})

        slope_norm = min(max(location.slope_deg / norm.get("slope_max_deg", 70.0), 0.0), 1.0)
        history_norm = min(max(location.historical_count / norm.get("history_cap", 50.0), 0.0), 1.0)

        soil_factor = lk.get("soil", {}).get(location.soil_type, 0.70)
        landuse_factor = lk.get("landuse", {}).get(location.landuse, 0.99)
        lith_factor = min(max(location.lithology_factor, 0.0), 1.0)
        road_factor = lk.get("road", {}).get(location.road_condition, 0.50)

        total_static = (
            s_w.get("slope", 0.30) * slope_norm +
            s_w.get("history", 0.20) * history_norm +
            s_w.get("soil", 0.15) * soil_factor +
            s_w.get("landuse", 0.12) * landuse_factor +
            s_w.get("lithology", 0.13) * lith_factor +
            s_w.get("road", 0.10) * road_factor
        )

        return round(total_static * 100.0, 2), {
            "slope_norm": slope_norm,
            "history_norm": history_norm,
            "soil_factor": soil_factor,
            "landuse_factor": landuse_factor,
            "lith_factor": lith_factor,
            "road_factor": road_factor
        }

    def compute_dynamic(self, weather: WeatherReading, weights: Dict[str, Any]) -> Tuple[float, Dict[str, float]]:
        """
        Compute dynamic meteorological trigger (0-100).
        Current rain (0.45), 24h forecast (0.35), soil moisture proxy (0.20).
        """
        cap = weights.get("norm", {}).get("rain_cap_mm", 100.0)
        d_w = weights.get("dynamic", {})

        cur_norm = min(max(weather.current_rain_mm / cap, 0.0), 1.0)
        fc_norm = min(max(weather.forecast_24h_mm / cap, 0.0), 1.0)
        ant_norm = min(max(weather.antecedent_3d_mm / cap, 0.0), 1.0)
        hum_norm = min(max(weather.humidity_pct / 100.0, 0.0), 1.0)

        moisture_proxy = 0.6 * ant_norm + 0.4 * hum_norm

        total_dynamic = (
            d_w.get("current_rain", 0.45) * cur_norm +
            d_w.get("forecast_24h", 0.35) * fc_norm +
            d_w.get("moisture", 0.20) * moisture_proxy
        )

        return round(total_dynamic * 100.0, 2), {
            "cur_norm": cur_norm,
            "fc_norm": fc_norm,
            "moisture_proxy": moisture_proxy
        }

    def score_location(self, location: Location, weather: WeatherReading, weights: Dict[str, Any]) -> RiskProfile:
        """Combine static and dynamic scores using configured percentages (default 60/40)."""
        static_score, _ = self.compute_static(location, weights)
        dynamic_score, _ = self.compute_dynamic(weather, weights)

        w_static = weights.get("static_weight", 0.6)
        w_dynamic = weights.get("dynamic_weight", 0.4)

        total_score = round(w_static * static_score + w_dynamic * dynamic_score, 2)
        risk_level = self.classify(total_score, weights.get("thresholds", {}))

        profile = RiskProfile(static_score, dynamic_score, total_score, risk_level)
        return profile
