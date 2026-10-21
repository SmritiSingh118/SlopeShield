"""
================================================================================
SlopeShield: Intelligent Landslide Risk & Safe Route System
Central CSV & JSON File Handling Layer (Member 3: File Handling & Data Pipeline)
Author: Anshika Gaur (Member 3)
================================================================================

This module provides an object-oriented file handling layer:
1. BaseDataHandler: Abstract Base Class defining read/write contracts.
2. CsvHandler: Robust CSV reader and writer with atomic file safety, header validation, and error reporting.
3. JsonHandler: Robust JSON parser and serializer with atomic file safety and schema checks.
4. DataManager: High-level central coordinator managing all project datasets and road geometries.
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
    Provides automatic whitespace trimming, header validation, atomic write safety,
    and helpful error reporting on malformed inputs.
    """

    def read(self, file_path: str, required_headers: Optional[List[str]] = None) -> List[Dict[str, str]]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"[CsvHandler] Missing required CSV file: {file_path}")

        if os.path.getsize(file_path) == 0:
            raise ValueError(f"[CsvHandler] CSV file is empty (0 bytes): {file_path}")

        records: List[Dict[str, str]] = []
        try:
            with open(file_path, mode="r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                if reader.fieldnames is None:
                    raise ValueError(f"[CsvHandler] CSV file contains no header row: {file_path}")

                # Clean and check fieldnames
                cleaned_fieldnames = [k.strip() if k else "" for k in reader.fieldnames]

                if required_headers:
                    missing = [h for h in required_headers if h not in cleaned_fieldnames]
                    if missing:
                        raise ValueError(f"[CsvHandler] CSV '{file_path}' is missing required column(s): {', '.join(missing)}")

                for line_idx, row in enumerate(reader, start=2):
                    cleaned_row = {}
                    for k, v in row.items():
                        if k is not None:
                            cleaned_row[k.strip()] = v.strip() if isinstance(v, str) else v
                    records.append(cleaned_row)
        except (ValueError, FileNotFoundError):
            raise
        except Exception as e:
            raise IOError(f"[CsvHandler] Error reading CSV file '{file_path}': {str(e)}") from e

        return records

    def write(self, file_path: str, data: List[Dict[str, Any]], fieldnames: Optional[List[str]] = None) -> bool:
        """
        Writes data to file atomically via a temporary file, ensuring partial or corrupted
        files are never left on disk if interrupted.
        """
        if not data and not fieldnames:
            return False

        try:
            abs_path = os.path.abspath(file_path)
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            if not fieldnames and data:
                fieldnames = list(data[0].keys())

            temp_path = f"{abs_path}.tmp"
            with open(temp_path, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for row in data:
                    writer.writerow(row)

            # Atomic replace
            if os.path.exists(abs_path):
                os.replace(temp_path, abs_path)
            else:
                os.rename(temp_path, abs_path)
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

        if os.path.getsize(file_path) == 0:
            raise ValueError(f"[JsonHandler] JSON file is empty (0 bytes): {file_path}")

        try:
            with open(file_path, mode="r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as jde:
            raise ValueError(f"[JsonHandler] Malformed JSON in '{file_path}' (line {jde.lineno}, col {jde.colno}): {jde.msg}") from jde
        except Exception as e:
            raise IOError(f"[JsonHandler] Error reading JSON file '{file_path}': {str(e)}") from e

    def write(self, file_path: str, data: Any, indent: int = 2) -> bool:
        """Writes JSON payload atomically to avoid corrupting destinations."""
        try:
            abs_path = os.path.abspath(file_path)
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            temp_path = f"{abs_path}.tmp"
            with open(temp_path, mode="w", encoding="utf-8") as f:
                json.dump(data, f, indent=indent, ensure_ascii=False)

            # Atomic replace
            if os.path.exists(abs_path):
                os.replace(temp_path, abs_path)
            else:
                os.rename(temp_path, abs_path)
            return True
        except Exception as e:
            raise IOError(f"[JsonHandler] Error writing JSON file '{file_path}': {str(e)}") from e


class DataManager:
    """
    Central Data Coordinator encapsulating all dataset paths, file operations,
    model hydration, road geometry ingestion, and persistence for SlopeShield.
    """

    REQUIRED_LOCATION_HEADERS = ["location_id", "name", "lat", "lon", "elevation_m", "slope_deg"]
    REQUIRED_ROAD_HEADERS = ["road_id", "from_id", "to_id", "distance_km"]

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
        self._road_geometries_path = os.path.join(self._base_dir, "data", "road_geometries.json")
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
        cfg = self._json_handler.read(self._weights_config_path)
        if not isinstance(cfg, dict):
            raise ValueError(f"[DataManager] Invalid configuration format in {self._weights_config_path}")
        return cfg

    def load_road_geometries(self) -> Dict[str, Any]:
        """Loads cached OpenStreetMap road geometries from data/road_geometries.json if present."""
        if not os.path.exists(self._road_geometries_path):
            return {}
        try:
            return self._json_handler.read(self._road_geometries_path)
        except Exception:
            return {}

    def load_locations(self) -> Dict[str, Location]:
        """
        Load static location features and instantiate encapsulated Location objects.
        Validates columns: location_id, name, lat, lon, elevation_m, slope_deg, etc.
        """
        rows = self._csv_handler.read(self._static_locations_path, required_headers=self.REQUIRED_LOCATION_HEADERS)
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
        Validates columns: road_id, from_id, to_id, distance_km.
        Attaches verified OpenStreetMap road geometry from road_geometries.json if available.
        """
        rows = self._csv_handler.read(self._road_network_path, required_headers=self.REQUIRED_ROAD_HEADERS)
        geometries = self.load_road_geometries()
        segments: List[RoadSegment] = []

        for row in rows:
            rid = row.get("road_id", "").strip()
            u = row.get("from_id", "").strip()
            v = row.get("to_id", "").strip()
            if not rid or not u or not v:
                continue

            # Check if verified geometry exists in cache
            geom_entry = geometries.get(rid)
            geom_coords = None
            has_verified = False
            if geom_entry and isinstance(geom_entry, dict):
                geom_coords = geom_entry.get("coordinates")
                has_verified = bool(geom_entry.get("has_verified_geometry", True) and geom_coords and len(geom_coords) > 2)

            seg = RoadSegment(
                road_id=rid,
                u=u,
                v=v,
                distance_km=float(row.get("distance_km", 0.0)),
                highway=row.get("highway", ""),
                road_type=row.get("road_type", ""),
                description=row.get("description", ""),
                geometry=geom_coords,
                has_verified_geometry=has_verified
            )
            segments.append(seg)

        return segments

    def load_dynamic_features(self) -> Dict[str, WeatherReading]:
        """Load meteorological readings from dynamic_features.csv."""
        if not os.path.exists(self._dynamic_features_path):
            return {}

        try:
            rows = self._csv_handler.read(self._dynamic_features_path)
        except Exception:
            return {}

        weather_map: Dict[str, WeatherReading] = {}
        for row in rows:
            lid = row.get("location_id", "").strip()
            if not lid:
                continue

            reading = WeatherReading(
                current_rain_mm=float(row.get("current_rain_mm", 0.0)),
                forecast_24h_mm=float(row.get("forecast_24h_mm", 0.0)),
                humidity_pct=int(float(row.get("humidity_pct", 50))),
                antecedent_3d_mm=float(row.get("antecedent_3d_mm", 0.0)),
                temp_c=float(row.get("temp_c", 20.0)),
                weather_desc=row.get("weather_desc", "")
            )
            weather_map[lid] = reading

        return weather_map

    def save_risk_scores(self, locations: Dict[str, Location], weights: Optional[Dict[str, Any]] = None) -> bool:
        """
        Persist scored locations to both CSV and JSON formats with atomic safety.
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
            "generator": "SlopeShield DataManager (OOP Architecture - Member 3: Anshika Gaur)",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "weights": weights.get("weights", {"static": 0.6, "dynamic": 0.4}) if weights else {"static": 0.6, "dynamic": 0.4},
            "locations": json_locations
        }
        self._json_handler.write(self._risk_output_json_path, payload)
        return True

    def save_route_output(self, route_payload: Dict[str, Any]) -> bool:
        """Persist frontend-ready route results to data/route_output.json atomically."""
        return self._json_handler.write(self._route_output_json_path, route_payload)

    def validate_datasets(self) -> Tuple[bool, List[str]]:
        """Validate integrity and presence of all core input datasets."""
        issues: List[str] = []
        if not os.path.exists(self._static_locations_path):
            issues.append(f"Missing {self._static_locations_path}")
        elif os.path.getsize(self._static_locations_path) == 0:
            issues.append(f"Empty {self._static_locations_path}")

        if not os.path.exists(self._road_network_path):
            issues.append(f"Missing {self._road_network_path}")
        elif os.path.getsize(self._road_network_path) == 0:
            issues.append(f"Empty {self._road_network_path}")

        if not os.path.exists(self._weights_config_path):
            issues.append(f"Missing {self._weights_config_path}")
        elif os.path.getsize(self._weights_config_path) == 0:
            issues.append(f"Empty {self._weights_config_path}")

        return len(issues) == 0, issues
