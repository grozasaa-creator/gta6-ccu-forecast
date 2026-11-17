import itertools, json, math, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import main as m
import eval_loo as e
d = json.load(open(sys.argv[1], encoding="utf-8"))
comps = d["comparables"]
built = []
for i, c in enumerate(comps):
    b = e.build_case(c, [x for j, x in enumerate(comps) if j != i])
    if b: built.append(b)
def run():
    tot = n = 0
    for case, ans in built:
        l = e.score(m.predict(case)["hours"], ans)
        tot += sum(l); n += len(l)
    return tot / n
res = []
for bwr, bws, s0, s1, wd in itertools.product([0.4, 0.6, 1.0], [1.0, 2.0, 4.0], [0.08, 0.12], [0.15, 0.25], [0.9, 1.0, 1.15]):
    m.BW_RATIO, m.BW_SIZE, m.SPREAD0, m.SPREAD1, m.WIDEN = bwr, bws, s0, s1, wd
    res.append((run(), bwr, bws, s0, s1, wd))
res.sort()
for r in res[:8]: print("%.4f bwr=%s bws=%s s0=%s s1=%s widen=%s" % r)
print("worst", res[-1])
