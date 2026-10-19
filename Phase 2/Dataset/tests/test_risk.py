"""Member-1: verify risk formula on tests/risk_cases.csv.
Checks: (1) expected level matches, (2) monotonicity — more rain never lowers score.
Usage: python tests/test_risk.py (run after scripts/risk_scorer.py works)
"""
import csv
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "scripts"))
from risk_scorer import load_weights, score_static, score_dynamic, classify  # noqa: E402

STATIC_CSV = os.path.join(BASE, "data", "locations_static.csv")
CASES_CSV = os.path.join(BASE, "tests", "risk_cases.csv")


def main():
    w = load_weights()
    static = {}
    with open(STATIC_CSV, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            static[r["location_id"]] = r

    fails, totals_by_loc = 0, {}
    print(f"{'case':22s} {'static':>6s} {'dynamic':>7s} {'total':>6s} {'got':>8s} {'expected':>8s}  verdict")
    with open(CASES_CSV, newline="", encoding="utf-8") as f:
        for c in csv.DictReader(f):
            lid = c["location_id"]
            s, _ = score_static(static[lid], w)
            d, _ = score_dynamic({"current_rain_mm": c["current_rain_mm"],
                                  "forecast_24h_mm": c["forecast_24h_mm"],
                                  "humidity_pct": c["humidity_pct"],
                                  "antecedent_3d_mm": c["antecedent_3d_mm"]}, w)
            total = round(w["static_weight"] * s + w["dynamic_weight"] * d, 2)
            got = classify(total, w["thresholds"])
            ok = "PASS" if got == c["expected_level"] else "FAIL"
            if ok == "FAIL":
                fails += 1
            print(f"{c['case_id']:22s} {s:6.1f} {d:7.1f} {total:6.1f} {got:>8s} {c['expected_level']:>8s}  {ok}")
            totals_by_loc.setdefault(lid, []).append((float(c["current_rain_mm"]) +
                                                      float(c["forecast_24h_mm"]), total, c["case_id"]))

    # monotonicity: same location, larger rain sum => total must not decrease
    for lid, vals in totals_by_loc.items():
        vals.sort()
        for (r1, t1, c1), (r2, t2, c2) in zip(vals, vals[1:]):
            if t2 < t1 - 1e-9:
                print(f"MONOTONICITY FAIL {lid}: {c1}({t1}) > {c2}({t2}) despite more rain")
                fails += 1

    print("ALL TESTS PASSED" if fails == 0 else f"{fails} FAILURE(S) — retune weights or expectations")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
