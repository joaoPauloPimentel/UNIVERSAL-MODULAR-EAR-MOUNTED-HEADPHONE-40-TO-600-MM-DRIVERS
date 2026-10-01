# Study (2026-10-01): model A final under the UMEH-2 load categories outside running (umeh2.support.CATEGORIES):
# 1 g normal (worst-case grid, head tilt to 45 deg, cable 0.5 N), 2 g dynamic, 3 g severe, 5 g accidental (cable snag).
# python3 studies/categories.py <D> [cat ...]
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import umeh3
from umeh3 import geom, loads, neckband as nb, RESULTS
from umeh2 import support as sp
D = int(sys.argv[1]); cats = sys.argv[2:] or list(sp.CATEGORIES)
geom.apply("AF"); V = {"P": 0.5, "neck": 2.0}
mp = nb.with_band(loads.mass_props(D), V["neck"])
out = {}
for cat in cats:
    t0 = time.time()
    r = loads.sweep(mp, V, cat)
    r.pop("info", None)
    out[cat] = r
    w = r.get("worst", {})
    print(f"AF D{D} {cat}: cases {r.get('n')}, released {r.get('released')} ({100 * r.get('released', 0) / max(r.get('n', 1), 1):.1f} %), "
          f"pad open {r.get('pad_open')}, root {w.get('root_p', 0) / 1e3:.1f} kPa, pad {w.get('pad_p', 0) / 1e3:.1f}, "
          f"pinna {w.get('pinna_p', 0) / 1e3:.1f}, helix {w.get('helix_p', 0) / 1e3:.1f}, lobe {w.get('lobe_p', 0) / 1e3:.1f}, "
          f"sulcus {w.get('sulcus_p', 0) / 1e3:.1f}, disp {w.get('disp', 0):.2f} mm, rot {w.get('rot', 0):.2f} deg, "
          f"p_lim {sp.CATEGORIES[cat]['p_lim'] / 1e3:.0f} kPa  [{time.time() - t0:.0f} s]", flush=True)
    json.dump(out, open(os.path.join(RESULTS, f"categories_AF_{D}.json"), "w"), indent=1, default=str)
