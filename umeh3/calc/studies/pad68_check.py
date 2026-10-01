# Study (2026-10-01): the round 110 mm velour pad actually sold (AliExpress listing found while sourcing in Brazil) has a
# ~68 mm opening and is ~23 mm thick, not the assumed 60 / 25 mm. Treadmill set at 60 mm with that pad.
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import umeh3
from umeh3 import geom, loads, neckband as nb
pad = dict(geom.VARIANTS.get("AF", {}).get("PAD", geom._BASE["PAD"]))
pad.update(id=68.0)
geom.apply("AF", PAD=pad)
geom.VARIANT = "AF"            # same mass file (the pad mass is the same)
v = {"P": 0.5, "neck": 2.0}
mp = nb.with_band(loads.mass_props(60), v["neck"])
sr = loads.static(mp, v); st = sr["m"]
s = loads.sweep(mp, v, "treadmill", n_grav=3, n_cable=2); w = s["worst"]
t = loads.tug_limits(mp, v)
print(f"pad id 68: static root {st['root_p']:.0f} pad {st['pad_p']:.0f} npad {st['n_pad']}; treadmill rel={s['released']}/{s['n']} "
      f"root={w['root_p']:.0f} pad={w['pad_p']:.0f} disp={w['disp']:.2f} npadmin={w['n_pad']}; tug min {min(x['F'] for x in t):.2f} N", flush=True)
