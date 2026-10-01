# Study (2026-10-01): sustained state after repeated treadmill strides (frictional shakedown), neckband designs.
# python3 studies/neckband_shakedown.py <variant> <D> '<design-variable dict>'
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import umeh3
from umeh3 import geom, loads, neckband as nb
var, D = sys.argv[1], int(sys.argv[2]); geom.apply(var)
v = json.loads(sys.argv[3])
mp = nb.with_band(loads.mass_props(D), v["neck"])
sd = loads.shakedown(mp, v, cat="treadmill", n_cyc=8, n_grav=1, n_cable=1)
m = sd.get("m") or {}
print(f"{var} D{D} {v}: cycles={sd.get('cycles')} converged={sd.get('converged')} released={sd.get('n_rel')} "
      f"sustained root={m.get('root_p', float('nan')):.0f} Pa pad={m.get('pad_p', float('nan')):.0f} "
      f"pinna={m.get('pinna_p', float('nan')):.0f} npad={m.get('n_pad')}", flush=True)
