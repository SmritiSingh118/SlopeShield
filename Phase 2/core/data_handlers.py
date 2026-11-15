"""
================================================================================
SlopeShield: Intelligent Landslide Risk & Safe Route System
Central CSV & JSON File Handling Layer (Member 3: File Handling & Data Pipeline)
Author: Anshika Gaur (Member 3)
================================================================================

This module provides an object-oriented file handling layer:
1. BaseDataHandler: Abstract Base Class defining read/write contracts.
2. CsvHandler: Robust CSV reader and writer with schema cleaning and validation.
3. JsonHandler: Robust JSON parser and serializer with schema checks.
4. DataManager: High-level central coordinator managing all project datasets.
"""

import os
import csv
import json
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timezone

from core.models import Location, RoadSegment, RiskProfile, WeatherReading


class BaseDataHandler(ABC):
    """Abstract base class defining the contract for data serialization and deserialization."""

    @abstractmethod
    def read(self, file_path: str) -> Any:
        """Read data from the specified path."""
        pass

    @abstractmethod
    def write(self, file_path: str, data: Any) -> bool:
        """Write data to the specified path."""
        pass


class CsvHandler(BaseDataHandler):
    """
    Polymorphic CSV Handler responsible for reading and writing tabular records.
    Provides automatic whitespace trimming, header validation, and error reporting.
    """

    def read(self, file_path: str) -> List[Dict[str, str]]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"[CsvHandler] Missing required CSV file: {file_path}")

        records: List[Dict[str, str]] = []
        try:
            with open(file_path, mode="r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                if reader.fieldnames is None:
                    return records

                # Clean fieldnames
                cleaned_fieldnames = [k.strip() if k else "" for k in reader.fieldnames]

                for line_idx, row in enumerate(reader, start=2):
                    cleaned_row = {}
                    for k, v in row.items():
                        if k is not None:
                            cleaned_row[k.strip()] = v.strip() if isinstance(v, str) else v
                    records.append(cleaned_row)
        except Exception as e:
            raise IOError(f"[CsvHandler] Error reading CSV file '{file_path}': {str(e)}") from e

        return records

    def write(self, file_path: str, data: List[Dict[str, Any]], fieldnames: Optional[List[str]] = None) -> bool:
        if not data and not fieldnames:
            return False

        try:
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
            if not fieldnames and data:
                fieldnames = list(data[0].keys())

            with open(file_path, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for row in data:
                    writer.writerow(row)
            return True
        except Exception as e:
            raise IOError(f"[CsvHandler] Error writing CSV file '{file_path}': {str(e)}") from e


class JsonHandler(BaseDataHandler):
    """
    Polymorphic JSON Handler responsible for parsing and writing nested JSON structures.
    Provides UTF-8 support, clean formatting, and atomic file safety.
    """

    def read(self, file_path: str) -> Any:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"[JsonHandler] Missing required JSON file: {file_path}")

        try:
            with open(file_path, mode="r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as jde:
            raise ValueError(f"[JsonHandler] Malformed JSON in '{file_path}': {str(jde)}") from jde
        except Exception as e:
            raise IOError(f"[JsonHandler] Error reading JSON file '{file_path}': {str(e)}") from e

    def write(self, file_path: str, data: Any, indent: int = 2) -> bool:
        try:
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
            temp_path = f"{file_path}.tmp"
            with open(temp_path, mode="w", encoding="utf-8") as f:
                json.dump(data, f, indent=indent, ensure_ascii=False)
            
            # Atomic replace
            if os.path.exists(file_path):
                os.replace(temp_path, file_path)
            else:
                os.rename(temp_path, file_path)
            return True
        except Exception as e:
            raise IOError(f"[JsonHandler] Error writing JSON file '{file_path}': {str(e)}") from e


class DataManager:
    """
    Central Data Coordinator encapsulating all dataset paths, file operations,
    model hydration, and persistence for the SlopeShield system.
    """

    def __init__(self, base_dir: Optional[str] = None):
        if base_dir is None:
            # Locate project root directory
            self._base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        else:
            self._base_dir = os.path.abspath(base_dir)

        self._csv_handler = CsvHandler()
        self._json_handler = JsonHandler()

        # Standard file paths
        self._static_locations_path = os.path.join(self._base_dir, "data", "locations_static.csv")
        self._road_network_path = os.path.join(self._base_dir, "data", "road_network.csv")
        self._weights_config_path = os.path.join(self._base_dir, "config", "risk_weights.json")
        self._dynamic_features_path = os.path.join(self._base_dir, "data", "dynamic_features.csv")
        self._live_weather_path = os.path.join(self._base_dir, "data", "live_weather.json")
        self._risk_scores_csv_path = os.path.join(self._base_dir, "data", "risk_scores.csv")
        self._risk_output_json_path = os.path.join(self._base_dir, "data", "risk_output.json")
        self._route_output_json_path = os.path.join(self._base_dir, "data", "route_output.json")

    @property
    def base_dir(self) -> str:
        return self._base_dir

    def load_weights_config(self) -> Dict[str, Any]:
        """Load mathematical weights and normalization parameters."""
        return self._json_handler.read(self._weights_config_path)

    def load_locations(self) -> Dict[str, Location]:
        """
        Load static location features and instantiate encapsulated Location objects.
        Validates columns: location_id, name, lat, lon, elevation_m, slope_deg, etc.
        """
        rows = self._csv_handler.read(self._static_locations_path)
        locations: Dict[str, Location] = {}

        for row in rows:
            lid = row.get("location_id", "").strip()
            if not lid:
                continue

            loc = Location(
                location_id=lid,
                name=row.get("name", lid),
                lat=float(row.get("lat", 0.0)),
                lon=float(row.get("lon", 0.0)),
                elevation_m=float(row.get("elevation_m", 0.0)),
                slope_deg=float(row.get("slope_deg", 0.0)),
                soil_type=row.get("soil_type", "loamy"),
                landuse=row.get("landuse", "non-forest"),
                lithology_factor=float(row.get("lithology_factor", 0.5)),
                historical_count=int(float(row.get("historical_count", 0))),
                road_condition=row.get("road_condition", "moderate"),
                static_notes=row.get("static_notes", "")
            )
            locations[lid] = loc

        # Hydrate existing risk scores if available
        self.hydrate_risk_scores(locations)
        return locations

    def hydrate_risk_scores(self, locations: Dict[str, Location]) -> None:
        """Attach calculated risk scores if risk_scores.csv or risk_output.json exists."""
        if os.path.exists(self._risk_scores_csv_path):
            try:
                rows = self._csv_handler.read(self._risk_scores_csv_path)
                for r in rows:
                    lid = r.get("location_id", "")
                    if lid in locations:
                        locations[lid].set_risk(
                            static_score=float(r.get("static_score", 0.0)),
                            dynamic_score=float(r.get("dynamic_score", 0.0)),
                            total_score=float(r.get("total_score", 0.0)),
                            risk_level=r.get("risk_level", "Low")
                        )
                        # Also attach basic dynamic weather
                        weather = WeatherReading(
                            current_rain_mm=float(r.get("current_rain_mm", 0.0)),
                            forecast_24h_mm=float(r.get("forecast_24h_mm", 0.0)),
                            humidity_pct=int(float(r.get("humidity_pct", 50)))
                        )
                        locations[lid].set_weather(weather)
            except Exception:
                pass

    def load_road_network(self) -> List[RoadSegment]:
        """
        Load highway network and instantiate encapsulated RoadSegment objects.
        Validates columns: road_id, from_id, to_id, distance_km, highway, road_type.
        """
        rows = self._csv_handler.read(self._road_network_path)
        segments: List[RoadSegment] = []

        for row in rows:
            rid = row.get("road_id", "").strip()
            u = row.get("from_id", "").strip()
            v = row.get("to_id", "").strip()
            if not rid or not u or not v:
                continue

            seg = RoadSegment(
                road_id=rid,
                u=u,
                v=v,
                distance_km=float(row.get("distance_km", 0.0)),
                highway=row.get("highway", ""),
                road_type=row.get("road_type", ""),
                description=row.get("description", "")
            )
            segments.append(seg)

        return segments

    def load_dynamic_features(self, is_fresh_pull: bool = False, max_age_seconds: int = 3600) -> Dict[str, WeatherReading]:
        """
        Load meteorological readings from dynamic_features.csv and enrich with live_weather.json if available.
        Accurately attributes data source ('openweathermap', 'cache', 'mock', 'fallback') and staleness.
        When is_fresh_pull is False, previously saved API records on disk are identified as 'cache'.
        """
        if not os.path.exists(self._dynamic_features_path):
            return {}

        rows = self._csv_handler.read(self._dynamic_features_path)
        weather_map: Dict[str, WeatherReading] = {}

        # Load rich live metadata if available
        live_meta = {}
        if os.path.exists(self._live_weather_path):
            try:
                live_list = self._json_handler.read(self._live_weather_path)
                if isinstance(live_list, list):
                    for item in live_list:
                        lid = item.get("location_id", "")
                        if lid:
                            live_meta[lid] = item
            except Exception:
                pass

        now_utc = datetime.now(timezone.utc)

        for row in rows:
            lid = row.get("location_id", "").strip()
            if not lid:
                continue

            meta = live_meta.get(lid, {})
            temp_val = float(row.get("temp_c", meta.get("temp_c", 20.0)) or 20.0)
            desc_val = str(row.get("weather_desc", meta.get("weather_desc", "")) or "")
            raw_source = str(meta.get("source", row.get("source", "cache"))).strip()
            fetched_at_str = str(row.get("fetched_at", meta.get("fetched_at", "")) or now_utc.isoformat()).strip()
            stale_val = bool(meta.get("stale", False))

            # Determine reliable source categorization
            if is_fresh_pull:
                if "openweathermap" in raw_source.lower() and not stale_val:
                    source_val = "openweathermap"
                elif "mock" in raw_source.lower():
                    source_val = "mock"
                elif "fallback" in raw_source.lower() or "error" in raw_source.lower() or "cache" in raw_source.lower():
                    source_val = "fallback"
                else:
                    source_val = "openweathermap" if not stale_val else "fallback"
            else:
                # Previously saved file on disk without current live pull is cached or mock
                if "mock" in raw_source.lower():
                    source_val = "mock"
                else:
                    source_val = "cache"

            # Check staleness based on timestamp age
            if fetched_at_str:
                try:
                    clean_ts = fetched_at_str.replace("Z", "+00:00")
                    dt = datetime.fromisoformat(clean_ts)
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    age_seconds = (now_utc - dt).total_seconds()
                    if age_seconds > max_age_seconds:
                        stale_val = True
                except Exception:
                    pass

            reading = WeatherReading(
                current_rain_mm=float(row.get("current_rain_mm", 0.0)),
                forecast_24h_mm=float(row.get("forecast_24h_mm", 0.0)),
                humidity_pct=int(float(row.get("humidity_pct", 50))),
                antecedent_3d_mm=float(row.get("antecedent_3d_mm", 0.0)),
                temp_c=temp_val,
                weather_desc=desc_val,
                source=source_val,
                fetched_at=fetched_at_str,
                stale=stale_val
            )
            weather_map[lid] = reading

        return weather_map

    def save_dynamic_features(self, rows: List[Dict[str, Any]]) -> bool:
        """Persist weather readings to dynamic_features.csv and live_weather.json."""
        if not rows:
            return False

        csv_fieldnames = ["location_id", "current_rain_mm", "forecast_24h_mm",
                          "burst_mm", "humidity_pct", "antecedent_3d_mm",
                          "temp_c", "weather_desc", "fetched_at"]
        clean_rows = []
        for r in rows:
            clean_rows.append({k: r.get(k, "") for k in csv_fieldnames})

        self._csv_handler.write(self._dynamic_features_path, clean_rows, csv_fieldnames)
        self._json_handler.write(self._live_weather_path, rows)
        return True

    def save_risk_scores(self, locations: Dict[str, Location], weights: Optional[Dict[str, Any]] = None) -> bool:
        """
        Persist scored locations to both CSV and JSON formats.
        Satisfies the contract required by Member 2 and Member 4.
        """
        csv_rows = []
        json_locations = []

        for loc in locations.values():
            csv_rows.append({
                "location_id": loc.id,
                "name": loc.name,
                "lat": loc.lat,
                "lon": loc.lon,
                "static_score": loc.risk.static_score,
                "dynamic_score": loc.risk.dynamic_score,
                "total_score": loc.risk.total_score,
                "risk_level": loc.risk.risk_level,
                "current_rain_mm": loc.weather.current_rain_mm,
                "forecast_24h_mm": loc.weather.forecast_24h_mm,
                "humidity_pct": loc.weather.humidity_pct
            })

            json_locations.append({
                "location_id": loc.id,
                "name": loc.name,
                "lat": loc.lat,
                "lon": loc.lon,
                "static_score": loc.risk.static_score,
                "dynamic_score": loc.risk.dynamic_score,
                "total_score": loc.risk.total_score,
                "risk_level": loc.risk.risk_level,
                "current_rain_mm": loc.weather.current_rain_mm,
                "forecast_24h_mm": loc.weather.forecast_24h_mm,
                "humidity_pct": loc.weather.humidity_pct
            })

        fieldnames = ["location_id", "name", "lat", "lon", "static_score", "dynamic_score",
                      "total_score", "risk_level", "current_rain_mm", "forecast_24h_mm", "humidity_pct"]

        # Write CSV
        self._csv_handler.write(self._risk_scores_csv_path, csv_rows, fieldnames)

        # Write JSON
        payload = {
            "generator": "SlopeShield DataManager (OOP Architecture - Member 3)",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "weights": weights.get("weights", {"static": 0.6, "dynamic": 0.4}) if weights else {"static": 0.6, "dynamic": 0.4},
            "locations": json_locations
        }
        self._json_handler.write(self._risk_output_json_path, payload)
        return True

    def save_route_output(self, route_payload: Dict[str, Any]) -> bool:
        """Persist frontend-ready route results to data/route_output.json and sync to frontend folder."""
        res = self._json_handler.write(self._route_output_json_path, route_payload)
        # Sync to SlopeShield_frontend fallback data folder if present
        try:
            frontend_dir = os.path.join(os.path.dirname(os.path.dirname(self._base_dir)), "SlopeShield_frontend", "frontend", "data")
            if os.path.exists(frontend_dir):
                self._json_handler.write(os.path.join(frontend_dir, "route_output.json"), route_payload)
        except Exception:
            pass
        return res

    def validate_datasets(self) -> Tuple[bool, List[str]]:
        """Validate integrity and presence of all core input datasets."""
        issues: List[str] = []
        if not os.path.exists(self._static_locations_path):
            issues.append(f"Missing {self._static_locations_path}")
        if not os.path.exists(self._road_network_path):
            issues.append(f"Missing {self._road_network_path}")
        if not os.path.exists(self._weights_config_path):
            issues.append(f"Missing {self._weights_config_path}")

        return len(issues) == 0, issues
