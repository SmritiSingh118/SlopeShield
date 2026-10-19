"""
Member-1: Risk scorer (Python prototype — mirrors src/risk_scorer.cpp)
Reads:  data/locations_static.csv, data/dynamic_features.csv, config/risk_weights.json
Writes: data/risk_scores.csv, data/risk_output.json

Run after: python scripts/fetch_weather.py --mock
Usage:     python scripts/risk_scorer.py
"""
import csv
import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_CSV = os.path.join(BASE, "data", "locations_static.csv")
DYN_CSV = os.path.join(BASE, "data", "dynamic_features.csv")
WEIGHTS = os.path.join(BASE, "config", "risk_weights.json")
OUT_CSV = os.path.join(BASE, "data", "risk_scores.csv")
OUT_JSON = os.path.join(BASE, "data", "risk_output.json")


def load_weights():
    with open(WEIGHTS, encoding="utf-8") as f:
        return json.load(f)


def classify(total, th):
    if total < th["low_max"]:
        return "Low"
    if total < th["moderate_max"]:
        return "Moderate"
    if total < th["high_max"]:
        return "High"
    return "Critical"


def score_static(row, w):
    n = w["norm"]
    lk = w["lookup"]
    slope_norm = min(max(float(row["slope_deg"]) / n["slope_max_deg"], 0), 1)
    history_norm = min(max(float(row["historical_count"]) / n["history_cap"], 0), 1)
    soil = lk["soil"].get(row["soil_type"].strip().lower(), 0.6)
    landuse = lk["landuse"].get(row["landuse"].strip().lower(), 0.5)
    lith = min(max(float(row["lithology_factor"]), 0), 1)
    road = lk["road"].get(row["road_condition"].strip().lower(), 0.5)
    s = w["static"]
    total = (s["slope"] * slope_norm + s["history"] * history_norm +
             s["soil"] * soil + s["landuse"] * landuse +
             s["lithology"] * lith + s["road"] * road)
    return round(total * 100, 2), {
        "slope_norm": round(slope_norm, 3), "history_norm": round(history_norm, 3),
        "soil": soil, "landuse": landuse, "lithology": lith, "road": road}


def score_dynamic(dyn, w):
    cap = w["norm"]["rain_cap_mm"]
    cur = min(max(float(dyn["current_rain_mm"]) / cap, 0), 1)
    fc = min(max(float(dyn["forecast_24h_mm"]) / cap, 0), 1)
    ant = min(max(float(dyn["antecedent_3d_mm"]) / cap, 0), 1)
    hum = min(max(float(dyn["humidity_pct"]) / 100.0, 0), 1)
    moisture = 0.6 * ant + 0.4 * hum
    d = w["dynamic"]
    total = d["current_rain"] * cur + d["forecast_24h"] * fc + d["moisture"] * moisture
    return round(total * 100, 2), {"cur_norm": round(cur, 3),
                                   "fc_norm": round(fc, 3),
                                   "moisture": round(moisture, 3)}


def main():
    w = load_weights()
    if not os.path.exists(DYN_CSV):
        raise SystemExit("Missing data/dynamic_features.csv. Run: python scripts/fetch_weather.py --mock first.")

    dyn = {}
    with open(DYN_CSV, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            dyn[r["location_id"]] = r

    results = []
    with open(STATIC_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            lid = row["location_id"]
            if lid not in dyn:
                print(f"[warn] {lid} has no dynamic row -> skipped")
                continue
            s_score, _ = score_static(row, w)
            d_score, _ = score_dynamic(dyn[lid], w)
            total = round(w["static_weight"] * s_score + w["dynamic_weight"] * d_score, 2)
            results.append({
                "location_id": lid, "name": row["name"],
                "lat": float(row["lat"]), "lon": float(row["lon"]),
                "static_score": s_score,
                "dynamic_score": d_score,
                "total_score": total,
                "risk_level": classify(total, w["thresholds"]),
                "current_rain_mm": float(dyn[lid]["current_rain_mm"]),
                "forecast_24h_mm": float(dyn[lid]["forecast_24h_mm"]),
                "humidity_pct": int(float(dyn[lid]["humidity_pct"])),
            })

    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        wri = csv.DictWriter(f, fieldnames=["location_id", "name", "lat", "lon",
                                            "static_score", "dynamic_score", "total_score",
                                            "risk_level", "current_rain_mm",
                                            "forecast_24h_mm", "humidity_pct"])
        wri.writeheader()
        wri.writerows(results)

    from datetime import datetime, timezone
    payload = {"generated_at": datetime.now(timezone.utc).isoformat(),
               "weights": {"static": w["static_weight"], "dynamic": w["dynamic_weight"]},
               "locations": results}
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    print(f"Scored {len(results)} locations -> {OUT_CSV}, {OUT_JSON}")
    for r in sorted(results, key=lambda x: -x["total_score"]):
        print(f"  {r['location_id']:4s} static={r['static_score']:5.1f} "
              f"dynamic={r['dynamic_score']:5.1f} total={r['total_score']:5.1f} {r['risk_level']}")


if __name__ == "__main__":
    main()
