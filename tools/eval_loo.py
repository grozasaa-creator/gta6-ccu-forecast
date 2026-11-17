"""Leave-one-out check of main.py: every analogue comparable becomes a pseudo-case, forecast from the others.

    python tools/eval_loo.py <a kit input .in file>      (e.g. input/p00.in: only its comparables are read)

Scores with the contest's pinball loss on the log scale (mean over hours 2..24 and the five levels) and prints the
persistence baseline's loss on the same pseudo-cases. A pseudo-case is an analogue when its hour 1 follows an unlock
ramp (the same rule main.py uses to weigh a comparable), so the quiet-category launches that only start later are not
scored: they are not what GTA VI's hour 1 looks like.
"""

import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import main as m  # noqa: E402

LEVELS = m.LEVELS
Z = [-1.645, -0.674, 0.0, 0.674, 1.645]


def hour_iso(epoch: int) -> str:
    from datetime import datetime, timezone
    return datetime.fromtimestamp(epoch, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def pinball(y: float, q: float, tau: float) -> float:
    d = math.log(max(y, 1.0)) - math.log(q)
    return 2 * max(tau * d, (tau - 1) * d)


def build_case(c: dict, others: list) -> tuple:
    pts = m.hourly(c["hourly"])
    start = m.to_epoch(c["day_start"])
    p1 = pts.get(start)
    if p1 is None:
        return None
    f = m.features(pts, start, p1)
    if f is None or f[2] < m.MIN_RAMP or p1 < 5000:
        return None
    answers = {h: pts[start + (h - 1) * 3600] for h in range(2, 25) if (start + (h - 1) * 3600) in pts}
    if len(answers) < 20:
        return None
    hist = [{"from": hour_iso(t), "viewers": v, "channels": None, "reads": 1} for t, v in sorted(pts.items()) if t < start + 3600]
    case = {
        "day_start": hour_iso(start),
        "known": [{"hour": 1, "viewers": p1}],
        "forecast": [{"hour": h} for h in range(2, 25)],
        "history_hourly": hist,
        "comparables": others,
    }
    return case, answers


def score(rows: list, answers: dict) -> list:
    losses = []
    for r in rows:
        y = answers.get(r["hour"])
        if y is None:
            continue
        losses += [pinball(y, q, t) for q, t in zip(r["q"], LEVELS)]
    return losses


def main() -> None:
    d = json.load(open(sys.argv[1], encoding="utf-8"))
    comps = d["comparables"]
    total, base_total, n_items = 0.0, 0.0, 0
    rows_out = []
    cover = [0, 0]
    for i, c in enumerate(comps):
        built = build_case(c, [x for j, x in enumerate(comps) if j != i])
        if built is None:
            continue
        case, answers = built
        pred = m.predict(case)["hours"]
        p1 = case["known"][0]["viewers"]
        base = [{"hour": h, "q": [p1 * math.exp(z * 0.15 * math.sqrt(h - 1)) for z in Z]} for h in range(2, 25)]
        a, b = score(pred, answers), score(base, answers)
        for r in pred:
            y = answers.get(r["hour"])
            if y is not None:
                cover[1] += 1
                cover[0] += r["q"][0] <= y <= r["q"][4]
        total += sum(a)
        base_total += sum(b)
        n_items += len(a)
        rows_out.append((c["name"][:30], sum(a) / len(a), sum(b) / len(b)))
    for name, a, b in rows_out:
        print(f"{name:30s} model {a:.3f}  baseline {b:.3f}")
    print(f"cases {len(rows_out)}  model loss {total / n_items:.4f}  baseline loss {base_total / n_items:.4f}  coverage90 {cover[0] / cover[1]:.3f}")


if __name__ == "__main__":
    main()
