"""
Member-1: Dynamic weather fetcher (OpenWeatherMap -> CSV/JSON)
Reads:  data/locations_static.csv
Writes: data/dynamic_features.csv, data/live_weather.json, data/weather_cache/<id>.json

Usage:
  python scripts/fetch_weather.py --mock              # demo without API key (viva-safe)
  python scripts/fetch_weather.py --api-key <KEY>     # live pull
  set OWM_API_KEY env var instead of --api-key

Free tier endpoints used:
  https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={KEY}&units=metric
  https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={KEY}&units=metric
"""
import argparse
import csv
import json
import os
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_CSV = os.path.join(BASE_DIR, "data", "locations_static.csv")
DYN_CSV = os.path.join(BASE_DIR, "data", "dynamic_features.csv")
LIVE_JSON = os.path.join(BASE_DIR, "data", "live_weather.json")
CACHE_DIR = os.path.join(BASE_DIR, "data", "weather_cache")

CURRENT_URL = "https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={key}&units=metric"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={key}&units=metric"


def read_locations():
    locs = []
    with open(STATIC_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            locs.append({
                "location_id": row["location_id"],
                "name": row["name"],
                "lat": float(row["lat"]),
                "lon": float(row["lon"]),
            })
    return locs


def http_get_json(url, timeout=15):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def parse_current(data):
    """Extract dynamic fields. Missing rain => 0.0 (OWM omits rain key when dry)."""
    rain = data.get("rain", {}) or {}
    current_rain = float(rain.get("1h", rain.get("3h", 0.0) or 0.0))
    main = data.get("main", {}) or {}
    wind = data.get("wind", {}) or {}
    weather = (data.get("weather") or [{}])[0]
    return {
        "current_rain_mm": round(current_rain, 2),
        "humidity_pct": int(main.get("humidity", 50)),
        "temp_c": round(float(main.get("temp", 20.0)), 1),
        "weather_main": weather.get("main", "Unknown"),
        "weather_desc": weather.get("description", ""),
        "wind_ms": round(float(wind.get("speed", 0.0)), 2),
    }


def parse_forecast(data, slots=8):
    """Sum next `slots` x 3h blocks (=24h) and take max 3h burst."""
    items = (data.get("list") or [])[:slots]
    total, burst = 0.0, 0.0
    for it in items:
        r = ((it.get("rain") or {}).get("3h", 0.0)) or 0.0
        total += float(r)
        burst = max(burst, float(r))
    return round(total, 2), round(burst, 2)


def load_prev_antecedent(loc_id):
    path = os.path.join(CACHE_DIR, f"{loc_id}.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return float(json.load(f).get("antecedent_3d_mm", 0.0))
    except Exception:
        return None


def save_cache(loc_id, payload):
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(os.path.join(CACHE_DIR, f"{loc_id}.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def mock_row(loc, i):
    """Deterministic demo values so viva works without internet/key.
    High-static sites (RUDR/MALP/KEDN) get heavier mock rain."""
    heavy = {"RUDR": 42.0, "MALP": 55.0, "KEDN": 38.0, "MUSS": 22.0}
    base = heavy.get(loc["location_id"], 8.0 + (i * 2.5) % 12)
    return {
        "location_id": loc["location_id"],
        "name": loc["name"],
        "lat": loc["lat"],
        "lon": loc["lon"],
        "current_rain_mm": round(base / 8, 2),
        "forecast_24h_mm": round(base, 2),
        "burst_mm": round(base / 4, 2),
        "humidity_pct": 88 if base > 20 else 72,
        "temp_c": 18.5,
        "weather_main": "Rain" if base > 15 else "Clouds",
        "weather_desc": "mock monsoon demo data (no API key)",
        "wind_ms": 3.2,
        "antecedent_3d_mm": round(base * 0.8, 2),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "stale": False,
        "source": "mock",
    }


def fetch_live(loc, api_key):
    cur = http_get_json(CURRENT_URL.format(lat=loc["lat"], lon=loc["lon"], key=api_key))
    time.sleep(1.1)  # respect free-tier rate limit
    try:
        fc = http_get_json(FORECAST_URL.format(lat=loc["lat"], lon=loc["lon"], key=api_key))
        f24, burst = parse_forecast(fc)
    except Exception as e:
        print(f"  [warn] {loc['location_id']} forecast failed ({e}); using 0")
        f24, burst = 0.0, 0.0
    p = parse_current(cur)
    prev = load_prev_antecedent(loc["location_id"])
    # Antecedent proxy: decay previous + add today's rain (simple, explainable)
    if prev is None:
        antecedent = round(p["current_rain_mm"] + f24 * 0.3, 2)
    else:
        antecedent = round(prev * 0.7 + p["current_rain_mm"] + f24 * 0.1, 2)
    row = {
        "location_id": loc["location_id"], "name": loc["name"],
        "lat": loc["lat"], "lon": loc["lon"],
        "current_rain_mm": p["current_rain_mm"],
        "forecast_24h_mm": f24, "burst_mm": burst,
        "humidity_pct": p["humidity_pct"], "temp_c": p["temp_c"],
        "weather_main": p["weather_main"], "weather_desc": p["weather_desc"],
        "wind_ms": p["wind_ms"], "antecedent_3d_mm": antecedent,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "stale": False, "source": "openweathermap",
    }
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mock", action="store_true", help="generate demo data without API key")
    ap.add_argument("--api-key", default=os.environ.get("OWM_API_KEY", ""), help="OWM API key")
    args = ap.parse_args()

    locs = read_locations()
    print(f"Locations: {len(locs)} from locations_static.csv")
    rows = []

    if args.mock or not args.api_key:
        if not args.api_key:
            print("No API key -> mock mode (use --api-key <KEY> for live).")
        for i, loc in enumerate(locs):
            rows.append(mock_row(loc, i))
    else:
        for loc in locs:
            try:
                print(f"Fetching {loc['location_id']} ({loc['name']}) ...")
                rows.append(fetch_live(loc, args.api_key))
            except urllib.error.HTTPError as e:
                print(f"  [ERROR] {loc['location_id']} HTTP {e.code}: check API key / quota. Using cache.")
                prev = load_prev_antecedent(loc["location_id"])
                rows.append(mock_row(loc, 0) | {"stale": True, "source": f"cache-fallback(http-{e.code})",
                                                "antecedent_3d_mm": prev or 0.0})
            except Exception as e:
                print(f"  [ERROR] {loc['location_id']} {e}. Using cache/mock.")
                prev = load_prev_antecedent(loc["location_id"])
                rows.append(mock_row(loc, 0) | {"stale": True, "source": "cache-fallback(error)",
                                                "antecedent_3d_mm": prev or 0.0})

    for r in rows:
        save_cache(r["location_id"], {"antecedent_3d_mm": r["antecedent_3d_mm"],
                                      "fetched_at": r["fetched_at"]})

    with open(DYN_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["location_id", "current_rain_mm", "forecast_24h_mm",
                                          "burst_mm", "humidity_pct", "antecedent_3d_mm", "fetched_at"])
        w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in w.fieldnames})

    with open(LIVE_JSON, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2)

    print(f"Wrote {DYN_CSV} ({len(rows)} rows)")
    print(f"Wrote {LIVE_JSON}")


if __name__ == "__main__":
    main()
