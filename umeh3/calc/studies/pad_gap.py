# Study (2026-10-01): how far the pad lifts off the skin while running (closed-back leak). Treadmill set (5400
# cases), donned state: for every case the gap at each pad sector that lost contact (-dn of its spring) and the
# share of the pad ring open. Gives the leak geometry for the acoustic check (light_checks.py).
# python3 studies/pad_gap.py <D>
import sys, os, json, numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import umeh3
from umeh3 import geom, loads, contacts as ct, neckband as nb, RESULTS
D = int(sys.argv[1]); geom.apply("AF"); V = {"P": 0.5, "neck": 2.0}
mp = nb.with_band(loads.mass_props(D), V["neck"])
C, link, info = ct.contact_set(V); model = nb.ModelN(C, link)
model.set_base(loads.static_wrench(mp))
gmax, frac, rel = [], [], 0
for tag, W in loads.cases(mp, "treadmill", n_grav=3, n_cable=2):
    r = model.solve(W)
    if not r["ok"]:
        rel += 1; continue
    g = np.array([max(-x["dn"], 0.0) for x in r["contacts"] if x["name"] in ct.PADS]) * 1e3
    gmax.append(g.max()); frac.append(float((g > 1e-4).mean()))
gmax, frac = np.array(gmax), np.array(frac)
res = dict(D=D, n=len(gmax), released=rel, open_share_of_cases=float((gmax > 1e-4).mean()),
           gap_mm_p50=float(np.percentile(gmax, 50)), gap_mm_p90=float(np.percentile(gmax, 90)), gap_mm_max=float(gmax.max()),
           ring_open_p50=float(np.percentile(frac, 50)), ring_open_p90=float(np.percentile(frac, 90)), ring_open_max=float(frac.max()),
           gap_mm_p90_when_open=float(np.percentile(gmax[gmax > 1e-4], 90)) if (gmax > 1e-4).any() else 0.0,
           ring_open_p90_when_open=float(np.percentile(frac[gmax > 1e-4], 90)) if (gmax > 1e-4).any() else 0.0)
json.dump(res, open(os.path.join(RESULTS, f"pad_gap_AF_{D}.json"), "w"), indent=1)
print(res)
