# Study (2026-10-01): models A and B with the neckband on the treadmill load set.
# python3 studies/neckband_treadmill.py <variant> <D> '<json list of design-variable dicts>'
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import umeh3
from umeh3 import geom, loads, neckband as nb
var, D = sys.argv[1], int(sys.argv[2]); geom.apply(var)
mp0 = loads.mass_props(D)
for v in json.loads(sys.argv[3]):
    nb.EYE_XY[:] = v.pop("eye", [0.0, 0.0])
    mp = nb.with_band(mp0, v["neck"])
    dz = nb.design(v["neck"])
    sr = loads.static(mp, v)
    if not sr["ok"]:
        print(var, v, "static FAILED", sr.get("why")); continue
    st = sr["m"]
    s = loads.sweep(mp, v, "treadmill", n_grav=3, n_cable=2)
    w = s["worst"]
    t = loads.tug_limits(mp, v)
    print(f"{var} D{D} {v} eye {nb.EYE_XY} M={mp[0]*1e3:.1f} band d={dz['d_mm']} coils={dz['n_coil']} k_side={dz['k_side']:.0f} "
          f"Pmin/max={dz['P_min']:.2f}/{dz['P_max']:.2f} SFy={dz['SF_yield']:.2f} mass={dz['mass_g']:.1f}g\n"
          f"  static: root {st['root_p']:.0f} pad {st['pad_p']:.0f} pinna {st['pinna_p']:.0f} npad {st['n_pad']}\n"
          f"  treadmill: rel={s['released']}/{s['n']} ({100*s['released']/s['n']:.1f}%) root={w['root_p']:.0f} pad={w['pad_p']:.0f} "
          f"pinna={w['pinna_p']:.0f} disp={w['disp']:.2f} npadmin={w['n_pad']} lost={s['clamp_lost']}\n"
          f"  tug min {min(x['F'] for x in t):.2f} N", flush=True)
