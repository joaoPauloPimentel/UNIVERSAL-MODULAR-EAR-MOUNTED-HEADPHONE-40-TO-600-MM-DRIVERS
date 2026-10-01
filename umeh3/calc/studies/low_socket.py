# Study script (2026-10-01): run from umeh3/calc as python3 studies/<name>.py <variant> ...

import sys; sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.dirname(__import__('os').path.abspath(__file__))))
import umeh3, numpy as np
from umeh3 import geom, loads
var=sys.argv[1]; geom.apply(var); mp=list(loads.mass_props(60))
print(var, 'socket now', np.round(mp[3]*1e3,1), 'Z_F', geom.Z_F)
mp[3]=np.array([-14.0, -38.0, geom.Z_F+3.0])*1e-3
v=dict(P=1.2)
t=loads.tug_limits(mp, v)
print(f"  low socket tug min {min(x['F'] for x in t):.2f} N")
loads.TREADMILL["cable"]=0.5
s=loads.sweep(mp, v, "treadmill", n_grav=3, n_cable=2); w=s['worst']
print(f"  treadmill cable 0.5 N low socket: rel={s['released']}/{s['n']} root={w['root_p']:.0f} disp={w['disp']:.2f}", flush=True)
loads.TREADMILL["cable"]=1.0
s=loads.sweep(mp, v, "treadmill", n_grav=3, n_cable=2); w=s['worst']
print(f"  treadmill cable 1.0 N low socket: rel={s['released']}/{s['n']} root={w['root_p']:.0f} disp={w['disp']:.2f}", flush=True)
