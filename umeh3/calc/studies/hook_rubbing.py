# Study (2026-10-01): rubbing of the hook on the ear while running. From the settled state (after the shakedown of the
# treadmill set) every stride case is applied and removed; at each hook contact the tangential slip there and back
# (change of the slip offsets s) and the friction work mu*Fn*slip are summed per stride.
# python3 studies/hook_rubbing.py <D> '<design-variable dict>' '<SADDLE override dict>'
import sys, os, json, numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import umeh3
from umeh3 import geom, loads, contacts as ct, neckband as nb
from umeh2 import support as sp
D = int(sys.argv[1]); v = json.loads(sys.argv[2])
S = dict(geom.VARIANTS["AF"]["SADDLE"]); S.update(json.loads(sys.argv[3]) if len(sys.argv) > 3 else {})
geom.apply("AF", SADDLE=S)
mp = nb.with_band(loads.mass_props(D), v["neck"])
C, link, info = ct.contact_set(v); model = nb.ModelN(C, link)
W_st = loads.static_wrench(mp)
cs = list(loads.cases(mp, "treadmill", n_grav=1, n_cable=1))
sd = sp.shakedown(model, W_st, [w for _, w in cs], seq="A", n_cyc=8, pads=ct.PADS)
st = sd["state"]; Ws = model._pad(W_st)
names = [c["name"] for c in C]; mu = np.array([c["mu"] for c in C])
hook = [i for i, n in enumerate(names) if n.startswith("H ")]
pads = [i for i, n in enumerate(names) if n in ct.PADS]
slip = np.zeros((len(cs), len(C))); work = np.zeros((len(cs), len(C))); n_rel = 0
for j, (tag, W) in enumerate(cs):
    W = model._pad(W)
    ok1, st1, _ = model._ramp(Ws, W, st, True, 60, model.N_STEPS)
    if not ok1: n_rel += 1; continue
    ok2, st2, _ = model._ramp(W, Ws, st1, True, 60, model.N_STEPS)
    if not ok2: n_rel += 1; continue
    d = np.linalg.norm(st1["s"] - st["s"], axis=1) + np.linalg.norm(st2["s"] - st1["s"], axis=1)
    Fm = 0.5 * (np.maximum(st1["Fn"], 0) + np.maximum(st2["Fn"], 0))
    slip[j] = d; work[j] = mu * Fm * d
    st = st2
print(f"AF D{D} {v} saddle {S}  strides {len(cs)}  released {n_rel}")
print(f"{'contact':12s} {'mu':>5s} {'strides slipping %':>19s} {'mean slip um':>13s} {'p95 slip um':>12s} {'work uJ/stride':>15s}")
for i in hook + [pads[0]]:
    s = slip[:, i] * 1e6; w = work[:, i] * 1e6
    print(f"{names[i]:12s} {mu[i]:5.2f} {100 * np.mean(s > 1):19.1f} {s.mean():13.1f} {np.percentile(s, 95):12.1f} {w.mean():15.2f}")
P = slip[:, pads] * 1e6
print(f"{'pads (all)':12s} {'':5s} {100 * np.mean(P.max(1) > 1):19.1f} {P.mean():13.1f} {np.percentile(P, 95):12.1f} {work[:, pads].sum(1).mean() * 1e6:15.2f}")
