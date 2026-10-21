"""
================================================================================
SlopeShield: Intelligent Landslide Risk & Safe Route System
Live Weather Ingestion & Dynamic Pipeline (Member 3 Integration & Member 1 API)
Authors: Anshika Gaur (Member 3) & Smriti singh(Member 1)
================================================================================

This module connects live meteorological APIs to SlopeShield's risk pipeline:
1. Supports explicit selection between LIVE weather and MOCK/DEMO modes.
2. Ingests OpenWeatherMap current readings and 24h forecasts when configured.
3. Gracefully handles missing API keys, rate limits, timeouts, and network failures.
4. Returns rich status metadata (live, cached, mock, unverified status).
5. Converts raw weather data into encapsulated WeatherReading domain models.
"""

import os
import csv
import json
import time
import urllib.request
import urllib.error
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timezone

from core.models import WeatherReading


class WeatherService:
    """
    Central Weather Ingestion Service managing both Live OpenWeatherMap data
    and scientifically calibrated Mock/Demo scenarios.
    """

    CURRENT_URL_TEMPLATE = "https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={key}&units=metric"
    FORECAST_URL_TEMPLATE = "https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={key}&units=metric"

    # Deterministic high-precipitation centers for mock monsoon demonstration
    MOCK_PRECIPITATION_MAP = {
        "RUDR": 42.0,  # Rudraprayag cloudburst / landslide zone
        "MALP": 55.0,  # Malpa high-intensity rainfall
        "KEDN": 38.0,  # Kedarnath upper-valley storm
        "MUSS": 22.0,  # Mussoorie hillside rain
    }

    def __init__(self, base_dir: Optional[str] = None):
        if base_dir is None:
            self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        else:
            self.base_dir = os.path.abspath(base_dir)

        self.cache_dir = os.path.join(self.base_dir, "data", "weather_cache")
        self.dyn_csv_path = os.path.join(self.base_dir, "data", "dynamic_features.csv")
        self.live_json_path = os.path.join(self.base_dir, "data", "live_weather.json")

        self._last_status: Dict[str, Any] = {
            "mode": "mock",
            "is_live_verified": False,
            "source": "uninitialized",
            "last_updated": None,
            "message": "Weather service initialized"
        }

        # Try loading .env if available
        self._load_dotenv_safe()

    def _load_dotenv_safe(self) -> None:
        """Loads environment variables from .env file if python-dotenv is present."""
        env_path = os.path.join(self.base_dir, ".env")
        if os.path.exists(env_path):
            try:
                import dotenv
                dotenv.load_dotenv(env_path)
            except ImportError:
                # Basic manual .env parser fallback
                try:
                    with open(env_path, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith("#") and "=" in line:
                                k, v = line.split("=", 1)
                                k = k.strip()
                                v = v.strip().strip("'\"")
                                if k and k not in os.environ:
                                    os.environ[k] = v
                except Exception:
                    pass

    def get_api_key(self, explicit_key: Optional[str] = None) -> Optional[str]:
        """Resolves OpenWeatherMap API key from arguments or environment."""
        if explicit_key and explicit_key.strip():
            return explicit_key.strip()
        key = os.environ.get("OWM_API_KEY", "").strip()
        return key if key else None

    @property
    def last_status(self) -> Dict[str, Any]:
        return self._last_status

    def fetch_weather(self, locations: List[Dict[str, Any]], mode: str = "mock",
                      api_key: Optional[str] = None, timeout: int = 10) -> Tuple[Dict[str, WeatherReading], Dict[str, Any]]:
        """
        Executes the dynamic weather retrieval pipeline.
        
        Parameters:
            locations: List of location dicts with location_id, name, lat, lon
            mode: 'live' or 'mock'
            api_key: Optional explicit API key
            timeout: HTTP request timeout in seconds
            
        Returns:
            Tuple of (weather_readings_map, status_metadata)
        """
        mode = mode.lower().strip()
        resolved_key = self.get_api_key(api_key)

        if mode == "live":
            if not resolved_key:
                metadata = {
                    "weather_mode": "mock_fallback",
                    "is_live_verified": False,
                    "source": "mock_no_api_key",
                    "status": "warning",
                    "message": "Live weather requested but OWM_API_KEY is not configured. Falling back to calibrated mock data.",
                    "last_updated": datetime.now(timezone.utc).isoformat()
                }
                readings, raw_rows = self._generate_mock_readings(locations)
                self._persist_weather(raw_rows)
                self._last_status = metadata
                return readings, metadata

            # Live API retrieval
            return self._fetch_live_with_fallback(locations, resolved_key, timeout=timeout)

        # Explicit Mock Mode
        metadata = {
            "weather_mode": "mock",
            "is_live_verified": False,
            "source": "calibrated_mock",
            "status": "success",
            "message": "Using deterministic mock monsoon data for presentation/viva.",
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
        readings, raw_rows = self._generate_mock_readings(locations)
        self._persist_weather(raw_rows)
        self._last_status = metadata
        return readings, metadata

    def _fetch_live_with_fallback(self, locations: List[Dict[str, Any]], api_key: str, timeout: int) -> Tuple[Dict[str, WeatherReading], Dict[str, Any]]:
        """Fetches live weather from OpenWeatherMap, with per-location caching and graceful fallback."""
        readings: Dict[str, WeatherReading] = {}
        raw_rows: List[Dict[str, Any]] = []
        failures: List[str] = []
        success_count = 0

        for i, loc in enumerate(locations):
            lid = loc["location_id"]
            lat = loc["lat"]
            lon = loc["lon"]

            try:
                # 1. Fetch current weather
                cur_url = self.CURRENT_URL_TEMPLATE.format(lat=lat, lon=lon, key=api_key)
                req_cur = urllib.request.Request(cur_url, headers={"User-Agent": "SlopeShield/1.0"})
                with urllib.request.urlopen(req_cur, timeout=timeout) as resp:
                    cur_data = json.loads(resp.read().decode("utf-8"))

                # 2. Fetch 24h forecast (next 8 blocks of 3h = 24h)
                fc_url = self.FORECAST_URL_TEMPLATE.format(lat=lat, lon=lon, key=api_key)
                req_fc = urllib.request.Request(fc_url, headers={"User-Agent": "SlopeShield/1.0"})
                with urllib.request.urlopen(req_fc, timeout=timeout) as resp:
                    fc_data = json.loads(resp.read().decode("utf-8"))

                # Parse readings
                rain_1h = float((cur_data.get("rain") or {}).get("1h", 0.0) or 0.0)
                rain_3h = float((cur_data.get("rain") or {}).get("3h", 0.0) or 0.0)
                cur_rain = round(max(rain_1h, rain_3h), 2)
                
                main = cur_data.get("main") or {}
                hum = int(main.get("humidity", 50))
                temp = round(float(main.get("temp", 20.0)), 1)
                desc = (cur_data.get("weather") or [{}])[0].get("description", "clear")

                # Sum next 24h forecast
                forecast_items = (fc_data.get("list") or [])[:8]
                f24_sum = 0.0
                for item in forecast_items:
                    r_val = float((item.get("rain") or {}).get("3h", 0.0) or 0.0)
                    f24_sum += r_val
                f24_rain = round(f24_sum, 2)

                # Antecedent proxy: load previous cache or approximate
                prev_ant = self._load_cache_antecedent(lid)
                if prev_ant is not None:
                    ant_rain = round(prev_ant * 0.7 + cur_rain + f24_rain * 0.1, 2)
                else:
                    ant_rain = round(cur_rain + f24_rain * 0.3, 2)

                reading = WeatherReading(
                    current_rain_mm=cur_rain,
                    forecast_24h_mm=f24_rain,
                    humidity_pct=hum,
                    antecedent_3d_mm=ant_rain,
                    temp_c=temp,
                    weather_desc=desc
                )
                readings[lid] = reading

                row_payload = {
                    "location_id": lid,
                    "name": loc.get("name", lid),
                    "lat": lat,
                    "lon": lon,
                    "current_rain_mm": cur_rain,
                    "forecast_24h_mm": f24_rain,
                    "burst_mm": round(cur_rain, 2),
                    "humidity_pct": hum,
                    "temp_c": temp,
                    "weather_desc": desc,
                    "antecedent_3d_mm": ant_rain,
                    "fetched_at": datetime.now(timezone.utc).isoformat(),
                    "stale": False,
                    "source": "openweathermap"
                }
                raw_rows.append(row_payload)
                self._save_cache(lid, row_payload)
                success_count += 1

                # Polite delay between API calls
                if i < len(locations) - 1:
                    time.sleep(0.3)

            except urllib.error.HTTPError as he:
                error_msg = f"HTTP {he.code}: {he.reason}"
                failures.append(f"{lid} ({error_msg})")
                fallback_reading, fallback_row = self._fallback_single(loc, error_source=f"api_fallback_http_{he.code}")
                readings[lid] = fallback_reading
                raw_rows.append(fallback_row)

            except Exception as ex:
                error_msg = f"{type(ex).__name__}: {str(ex)}"
                failures.append(f"{lid} ({error_msg})")
                fallback_reading, fallback_row = self._fallback_single(loc, error_source="api_fallback_error")
                readings[lid] = fallback_reading
                raw_rows.append(fallback_row)

        self._persist_weather(raw_rows)

        if success_count == len(locations):
            metadata = {
                "weather_mode": "live",
                "is_live_verified": True,
                "source": "openweathermap",
                "status": "success",
                "message": f"Successfully pulled live weather for all {success_count} locations from OpenWeatherMap.",
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
        elif success_count > 0:
            metadata = {
                "weather_mode": "partial_live",
                "is_live_verified": True,
                "source": "hybrid_live_cache",
                "status": "warning",
                "message": f"Live weather fetched for {success_count}/{len(locations)} locations. {len(failures)} fell back to cache.",
                "failures": failures,
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
        else:
            first_err = failures[0] if failures else "Connection error"
            metadata = {
                "weather_mode": "cached_fallback",
                "is_live_verified": False,
                "source": "fallback_after_api_error",
                "status": "error",
                "message": f"OpenWeatherMap API request failed ({first_err}). System safely transitioned to cached/mock weather.",
                "failures": failures,
                "last_updated": datetime.now(timezone.utc).isoformat()
            }

        self._last_status = metadata
        return readings, metadata

    def _fallback_single(self, loc: Dict[str, Any], error_source: str) -> Tuple[WeatherReading, Dict[str, Any]]:
        """Provides a cached or calibrated mock reading when live fetch fails for a single location."""
        lid = loc["location_id"]
        cached = self._load_cache_payload(lid)
        if cached:
            reading = WeatherReading(
                current_rain_mm=float(cached.get("current_rain_mm", 0.0)),
                forecast_24h_mm=float(cached.get("forecast_24h_mm", 0.0)),
                humidity_pct=int(cached.get("humidity_pct", 50)),
                antecedent_3d_mm=float(cached.get("antecedent_3d_mm", 0.0)),
                temp_c=float(cached.get("temp_c", 20.0)),
                weather_desc=str(cached.get("weather_desc", "cached fallback"))
            )
            row = dict(cached)
            row["stale"] = True
            row["source"] = error_source
            return reading, row

        # Use mock row
        mock_rain = self.MOCK_PRECIPITATION_MAP.get(lid, 8.0)
        reading = WeatherReading(
            current_rain_mm=round(mock_rain / 8.0, 2),
            forecast_24h_mm=round(mock_rain, 2),
            humidity_pct=88 if mock_rain > 20 else 72,
            antecedent_3d_mm=round(mock_rain * 0.8, 2),
            temp_c=18.5,
            weather_desc="Mock monsoon fallback (API failed)"
        )
        row = {
            "location_id": lid,
            "name": loc.get("name", lid),
            "lat": loc["lat"],
            "lon": loc["lon"],
            "current_rain_mm": reading.current_rain_mm,
            "forecast_24h_mm": reading.forecast_24h_mm,
            "burst_mm": round(reading.current_rain_mm, 2),
            "humidity_pct": reading.humidity_pct,
            "temp_c": 18.5,
            "weather_desc": reading.weather_desc,
            "antecedent_3d_mm": reading.antecedent_3d_mm,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "stale": True,
            "source": error_source
        }
        return reading, row

    def _generate_mock_readings(self, locations: List[Dict[str, Any]]) -> Tuple[Dict[str, WeatherReading], List[Dict[str, Any]]]:
        """Generates calibrated mock weather readings suitable for viva/offline demonstrations."""
        readings = {}
        raw_rows = []

        for i, loc in enumerate(locations):
            lid = loc["location_id"]
            rain_24h = self.MOCK_PRECIPITATION_MAP.get(lid, round(8.0 + (i * 2.5) % 12, 1))
            cur_rain = round(rain_24h / 8.0, 2)
            hum = 88 if rain_24h > 20 else 72
            ant = round(rain_24h * 0.8, 2)
            desc = "Monsoon downpour (demo)" if rain_24h > 20 else "Overcast (demo)"

            reading = WeatherReading(
                current_rain_mm=cur_rain,
                forecast_24h_mm=rain_24h,
                humidity_pct=hum,
                antecedent_3d_mm=ant,
                temp_c=18.5,
                weather_desc=desc
            )
            readings[lid] = reading

            raw_rows.append({
                "location_id": lid,
                "name": loc.get("name", lid),
                "lat": loc["lat"],
                "lon": loc["lon"],
                "current_rain_mm": cur_rain,
                "forecast_24h_mm": rain_24h,
                "burst_mm": round(cur_rain, 2),
                "humidity_pct": hum,
                "temp_c": 18.5,
                "weather_desc": desc,
                "antecedent_3d_mm": ant,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "stale": False,
                "source": "calibrated_mock"
            })

        return readings, raw_rows

    def _persist_weather(self, rows: List[Dict[str, Any]]) -> None:
        """Persists weather data to dynamic_features.csv and live_weather.json with atomic safety."""
        os.makedirs(os.path.dirname(self.dyn_csv_path), exist_ok=True)

        # 1. Write dynamic_features.csv atomically
        tmp_csv = self.dyn_csv_path + ".tmp"
        fieldnames = ["location_id", "current_rain_mm", "forecast_24h_mm", "burst_mm", "humidity_pct", "antecedent_3d_mm", "fetched_at"]
        with open(tmp_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in rows:
                writer.writerow({k: r.get(k, "") for k in fieldnames})

        if os.path.exists(self.dyn_csv_path):
            os.replace(tmp_csv, self.dyn_csv_path)
        else:
            os.rename(tmp_csv, self.dyn_csv_path)

        # 2. Write live_weather.json atomically
        tmp_json = self.live_json_path + ".tmp"
        with open(tmp_json, "w", encoding="utf-8") as f:
            json.dump(rows, f, indent=2)

        if os.path.exists(self.live_json_path):
            os.replace(tmp_json, self.live_json_path)
        else:
            os.rename(tmp_json, self.live_json_path)

    def _save_cache(self, loc_id: str, payload: Dict[str, Any]) -> None:
        try:
            os.makedirs(self.cache_dir, exist_ok=True)
            path = os.path.join(self.cache_dir, f"{loc_id}.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
        except Exception:
            pass

    def _load_cache_payload(self, loc_id: str) -> Optional[Dict[str, Any]]:
        path = os.path.join(self.cache_dir, f"{loc_id}.json")
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def _load_cache_antecedent(self, loc_id: str) -> Optional[float]:
        payload = self._load_cache_payload(loc_id)
        if payload and "antecedent_3d_mm" in payload:
            try:
                return float(payload["antecedent_3d_mm"])
            except (ValueError, TypeError):
                return None
        return None
