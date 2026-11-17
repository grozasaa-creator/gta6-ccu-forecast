import json, math, sys
from datetime import datetime, timedelta, timezone
d = json.load(open(sys.argv[1]))
def parse(s): return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
for c in d["comparables"]:
    ds = parse(c["day_start"] if "T" in c["day_start"] else c["day_start"] + "T00:00:00Z")
    pts = {parse(r["from"]): r["viewers"] for r in c["hourly"]}
    row = []
    for h in range(1, 25):
        v = pts.get(ds + timedelta(hours=h - 1))
        row.append(v)
    n = sum(v is not None for v in row)
    p1 = row[0]
    rel = [round(v / p1, 2) if (v and p1) else None for v in row]
    print(c["name"][:28].ljust(28), c["day_start"][:10], "n=%d" % n, "p1=%s" % p1, "max=", max([v for v in row if v] or [0]))
    print("   ", rel)
