"""Forecast GTA VI's launch-day Twitch viewers, hour by hour (Python 3.13, standard library only).

For every case file in the input directory it writes five quantiles (0.05, 0.25, 0.5, 0.75, 0.95) of the hourly
count of hours 2..24. The method pools the comparables (past big launches' hourly counts) as follows:

  * each comparable gives a log-ratio curve L_c(h) = ln v_c(h) - ln v_c(1) around its own release day;
  * a comparable weighs more the more its hour 1 looks like the case's: where hour 1 sits against the highest of the
    14 hours before it (an unlock ramp that has passed its crest), and how big its hour 1 is;
  * a comparable with no unlock ramp before hour 1 (a quiet category that only starts later) weighs almost nothing;
  * the five quantiles are those of the weighted mixture of normals centred on L_c(h) with a spread that widens with h.

Deterministic, offline, no randomness.
"""

import json
import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

INPUT_DIR = Path(os.environ.get("MAKEFUN_INPUT_DIR", "/input"))
OUTPUT_DIR = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))

LEVELS = [0.05, 0.25, 0.5, 0.75, 0.95]
HOUR = 3600

# Tunables (fitted on a leave-one-out run over the comparables, tools/eval_loo.py).
BW_RATIO = 1.0      # bandwidth on ln(hour 1 / highest of the 14 hours before)
BW_SIZE = 2.0       # bandwidth on ln(hour 1)
SPREAD0 = 0.12      # log spread of each comparable's kernel at hour 2
SPREAD1 = 0.25      # extra log spread at hour 24 (grows with sqrt of the hours ahead)
WIDEN = 0.9         # widens the weighted quantiles around their median
MIN_RAMP = math.log(3.0)
TIER_WEIGHT = {"weak": 0.3, "early-access-contaminated": 0.5}


def to_epoch(s: str) -> int:
    if "T" not in s:
        s += "T00:00:00Z"
    return int(datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp())


def hourly(rows: list) -> dict[int, float]:
    return {to_epoch(r["from"]): float(r["viewers"]) for r in rows if r.get("viewers") is not None}


def features(pts: dict[int, float], start: int, p1: float):
    """(ln(p1 / crest), ln p1, ramp) from the 14 hours before the day's second hour, or None without them."""
    pre = [pts[start + k * HOUR] for k in range(-14, 0) if (start + k * HOUR) in pts]
    if len(pre) < 6:
        return None
    crest = max(pre)
    low = min(pre[:4]) if len(pre) >= 4 else min(pre)
    ramp = math.log(max(crest, 1.0) / max(low, 1.0))
    return (math.log(max(p1, 1.0) / max(crest, 1.0)), math.log(max(p1, 1.0)), ramp)


def tier_of(c: dict) -> float:
    unlock = c.get("unlock", "") or ""
    for key, w in TIER_WEIGHT.items():
        if f"Tier: {key}" in unlock:
            return w
    return 1.0


def norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def mixture_quantile(tau: float, centres: list, weights: list, spread: float) -> float:
    lo = min(centres) - 6 * spread - 1.0
    hi = max(centres) + 6 * spread + 1.0
    total = sum(weights)
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        cdf = sum(w * norm_cdf((mid - c) / spread) for c, w in zip(centres, weights)) / total
        if cdf < tau:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def predict(case: dict) -> dict:
    """The forecast object {"hours": [...]} of one case."""
    start = to_epoch(case["day_start"])
    first = next(k for k in case["known"] if k["hour"] == 1)
    p1 = max(1.0, float(first["viewers"]))
    target = features(hourly(case["history_hourly"]), start, p1)
    hours = [row["hour"] for row in case["forecast"]]

    pool = []
    for c in case["comparables"]:
        if c.get("name", "").startswith("Grand Theft Auto VI category"):
            continue
        pts = hourly(c["hourly"])
        cstart = to_epoch(c["day_start"])
        cp1 = pts.get(cstart)
        if cp1 is None or cp1 <= 0:
            continue
        f = features(pts, cstart, cp1)
        if f is None:
            continue
        w = tier_of(c)
        w *= 1.0 / (1.0 + math.exp(-4.0 * (f[2] - MIN_RAMP)))
        if target is not None:
            w *= math.exp(-0.5 * (((f[0] - target[0]) / BW_RATIO) ** 2 + ((f[1] - target[1]) / BW_SIZE) ** 2))
        if w < 1e-9:
            continue
        pool.append((pts, cstart, cp1, w))

    rows = []
    for h in hours:
        centres, weights = [], []
        for pts, cstart, cp1, w in pool:
            v = pts.get(cstart + (h - 1) * HOUR)
            if v is None or v <= 0:
                continue
            centres.append(math.log(v / cp1))
            weights.append(w)
        spread = math.sqrt(SPREAD0 ** 2 + (SPREAD1 ** 2) * (h - 1) / 23.0)
        if sum(weights) < 0.05 or len(centres) < 2:
            sigma = 0.15 * math.sqrt(h - 1)
            qs = [p1 * math.exp(z * sigma) for z in (-1.645, -0.674, 0.0, 0.674, 1.645)]
        else:
            raw = [mixture_quantile(t, centres, weights, spread) for t in LEVELS]
            med = raw[2]
            qs = [p1 * math.exp(med + WIDEN * (r - med)) for r in raw]
        qs = [min(max(q, 1e-6), 1e9) for q in qs]
        for i in range(1, 5):
            qs[i] = max(qs[i], qs[i - 1])
        rows.append({"hour": h, "q": [round(q, 2) for q in qs]})
    return {"hours": rows}


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for path in sorted(INPUT_DIR.glob("*.in")):
        case = json.loads(path.read_text(encoding="utf-8"))
        (OUTPUT_DIR / f"{path.stem}.out").write_text(json.dumps(predict(case), separators=(",", ":")) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
