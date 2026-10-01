# Study script (2026-10-01): run from umeh3/calc as python3 studies/<name>.py <variant> ...

import sys, time, json; sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.dirname(__import__('os').path.abspath(__file__))))
import umeh3
from umeh3 import geom, loads
var=sys.argv[1]; geom.apply(var); D=int(sys.argv[3]) if len(sys.argv)>3 else 60; mp = loads.mass_props(D)
for v in json.loads(sys.argv[2]):
    st=loads.static(mp, v)['m']
    out=[f"{var} D{D} {v} M={mp[0]*1e3:.1f} static root {st['root_p']:.0f} pinna {st['pinna_p']:.0f} sulc {st['sulcus_p']:.0f} npad {st['n_pad']}"]
    for cat in ("treadmill",):
        s = loads.sweep(mp, v, cat, n_dir=12, n_cable=2, n_grav=3)
        w=s['worst']; out.append(f"  {cat}: n={s['n']} rel={s['released']} ({100*s['released']/s['n']:.1f}%) lost={s['clamp_lost']} root={w['root_p']:.0f} pinna={w['pinna_p']:.0f} lobe={w['lobe_p']:.0f} disp={w['disp']:.2f}")
    print("\n".join(out), flush=True)
