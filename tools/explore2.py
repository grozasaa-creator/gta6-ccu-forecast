import json, math, sys
from datetime import datetime, timedelta, timezone
def parse(s): return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
base = "../gta6-twitch-ccu-forecast-01-kit/input/"
for pid in ["p00","p01","p02","p03"]:
    d = json.load(open(base + pid + ".in"))
    ds = parse(d["day_start"])
    pts = {parse(r["from"]): r["viewers"] for r in d["history_hourly"]}
    pre = [pts.get(ds + timedelta(hours=k)) for k in range(-14, 1)]
    print(pid, d["game"]["name"][:20], d["notes"][:0], "last15h:", pre, "p1", d["known"][0]["viewers"])
print()
d = json.load(open(base + "p00.in"))
for c in d["comparables"]:
    if c["name"].startswith("Grand Theft"): continue
    ds = parse(c["day_start"] + "T00:00:00Z") if "T" not in c["day_start"] else parse(c["day_start"])
    pts = {parse(r["from"]): r["viewers"] for r in c["hourly"]}
    pre = [pts.get(ds + timedelta(hours=k)) for k in range(-14, 1)]
    print(c["name"][:22].ljust(22), pre)
