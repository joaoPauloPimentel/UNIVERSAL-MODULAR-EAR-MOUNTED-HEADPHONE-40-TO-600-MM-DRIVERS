# Study (2026-10-01): heaviest driver each size can carry on the treadmill with no release (5400 cases), found by
# bisection on an extra point mass at the driver's centre of mass. Also reports the per-stride root pressure there.
# python3 studies/max_driver_mass.py <D>
import sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import umeh3
from umeh3 import geom, loads, neckband as nb, RESULTS
D = int(sys.argv[1]); geom.apply(os.environ.get("UMEH_VAR", "AF")); V = {"P": 0.5, "neck": 2.0}
M, com, I, p_c, rows = loads.mass_props(D)
c_d = np.array(next(r["c_mm"] for r in rows if r["part"] == "driver")) * 1e-3
m_d0 = next(r["m_g"] for r in rows if r["part"] == "driver")


def with_extra(dm):
    M2 = M + dm; com2 = (M * com + dm * c_d) / M2
    d1, d2 = com - com2, c_d - com2
    I2 = I + M * (d1 @ d1 * np.eye(3) - np.outer(d1, d1)) + dm * (d2 @ d2 * np.eye(3) - np.outer(d2, d2))
    return nb.with_band((M2, com2, I2, p_c, rows), V["neck"])


def run(dm):
    r = loads.sweep(with_extra(dm), V, "treadmill", n_grav=3, n_cable=2)
    return r


lo, hi = 0.0, 0.080
r_lo = run(lo); hist = [(lo, r_lo["released"], r_lo["worst"]["root_p"])]
if r_lo["released"] > 0:
    print(f"D{D}: releases already with the typical driver"); sys.exit()
r_hi = run(hi); hist.append((hi, r_hi["released"], r_hi["worst"]["root_p"]))
if r_hi["released"] == 0:
    lo = hi
else:
    for _ in range(4):
        mid = 0.5 * (lo + hi); r = run(mid); hist.append((mid, r["released"], r["worst"]["root_p"]))
        if r["released"] == 0:
            lo, r_lo = mid, r
        else:
            hi = mid
        print(f"  D{D} +{mid * 1e3:.0f} g: released {r['released']}, root {r['worst']['root_p'] / 1e3:.1f} kPa", flush=True)
res = dict(D=D, driver_typical_g=m_d0, max_driver_g=m_d0 + lo * 1e3, bracket_g=[m_d0 + lo * 1e3, m_d0 + hi * 1e3],
           root_at_max_kPa=r_lo["worst"]["root_p"] / 1e3, hist=[(m_d0 + a * 1e3, n, p / 1e3) for a, n, p in hist])
json.dump(res, open(os.path.join(RESULTS, f"max_driver_{geom.VARIANT}_{D}.json"), "w"), indent=1)
print(f"D{D}: max driver {res['max_driver_g']:.0f} g (typical {m_d0:.0f} g), bracket {res['bracket_g'][0]:.0f}-{res['bracket_g'][1]:.0f} g, root there {res['root_at_max_kPa']:.1f} kPa", flush=True)
