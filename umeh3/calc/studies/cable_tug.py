# Study script (2026-10-01): run from umeh3/calc as python3 studies/<name>.py <variant> ...

import sys, json; sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.dirname(__import__('os').path.abspath(__file__))))
import umeh3, numpy as np
from umeh3 import geom, loads
var=sys.argv[1]; geom.apply(var); D=int(sys.argv[2]); mp=loads.mass_props(D)
v=dict(P=1.2)
t=loads.tug_limits(mp, v)
out=[f"{var} D{D} M={mp[0]*1e3:.1f} tug min {min(x['F'] for x in t):.2f} N at {min(t,key=lambda x:x['F'])['dir']}; outward-ish (z>0.5): {[round(x['F'],2) for x in t if x['dir'][2]>0.5]}"]
loads.TREADMILL["cable"]=0.5
s=loads.sweep(mp, v, "treadmill", n_grav=3, n_cable=2)
w=s['worst']; out.append(f"  treadmill cable 0.5 N: rel={s['released']}/{s['n']} root={w['root_p']:.0f} pinna={w['pinna_p']:.0f} disp={w['disp']:.2f} npadmin={w['n_pad']}")
print("\n".join(out), flush=True)
