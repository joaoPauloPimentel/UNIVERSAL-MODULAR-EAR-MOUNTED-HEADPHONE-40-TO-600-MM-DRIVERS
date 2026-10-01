# Study (2026-10-01): closed-back seal of the pad while running. Static: pad sectors touching and their pressure;
# treadmill (5400 cases): share of cases in which every one of the 16 pad sectors stays in contact (seal intact),
# and the smallest number touching.
# python3 studies/pad_seal.py <D> '<design-variable dict>'
import sys, os, json, numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import umeh3
from umeh3 import geom, loads, contacts as ct, neckband as nb
D = int(sys.argv[1]); v = json.loads(sys.argv[2]); geom.apply("AF")
mp = nb.with_band(loads.mass_props(D), v["neck"])
s = loads.static(mp, v)
r = s["r"]; pads = [x for x in r["contacts"] if x["name"] in ct.PADS]
p = np.array([x["p_mean"] for x in pads])
print(f"AF D{D} static: sectors touching {int((p > 0).sum())}/16, pad pressure min {p.min():.0f} mean {p.mean():.0f} max {p.max():.0f} Pa, pad force {sum(x['Fn'] for x in pads):.2f} N")
w = loads.sweep(mp, v, "treadmill", n_grav=3, n_cable=2)
print(f"treadmill: cases {w['n']}, released {w['released']}, seal opened (<16 sectors) {w['pad_open']} ({100 * w['pad_open'] / w['n']:.1f} %), min sectors {w['worst']['n_pad']}")
