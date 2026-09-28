"""
Layout optimisation of the ear cradle (Design B -> Final).

Design variables (BOUNDS): temporal/mastoid/posterior-superior pad angles and radii, the link eye on the cup end
(link_x, link_y; re-tuned per module afterwards by calc/tune_eye.py), link preload P and the pad scale.
Every candidate is evaluated with the contact model (support.py) over the normal-use load set and, optionally,
the dynamic load set; the score is the smallest normalised margin, so the optimum is the layout whose WORST
criterion is best (max-min design), not a weighted average. random_search samples BOUNDS, refine is a coordinate
pattern search on that score. The search ran during the design iterations (calc/final_layout.json holds its
result rounded to 0.5 deg / 0.5 mm / 0.1 N / 0.1); run_all.py re-checks that layout with the current model.

Geometric constraints [A] (geometric_ok, pad_edge_clearance): pad inner edges at least PINNA_EDGE_R from the
canal axis (p95 pinna half-length + clearance); pads, saddle and cable clip at least MIN_SEP_DEG apart on the
ring (tab width + screw access).
"""
import math
import numpy as np
from . import support as sp, design as dz
from .materials import TISSUE

ROT_NORMAL = 2.0      # deg [A] max seating rotation in normal use (1 mm at the driver)
ROT_DYN = 5.0         # deg [A] max rotation in the dynamic set (small-rotation model limit)


GAMMA_MU = 1.25      # [A] partial factor on the nominal friction coefficient for the design cases
PAD_KEYS = ("pad_t_a", "pad_t_b", "pad_m_a", "pad_m_b", "pad_p_a", "pad_p_b")


PINNA_HALF_P95 = 36.0  # mm [A] p95 pinna half-length (canal axis to the helix rim)
PINNA_EDGE_CLR = 2.0   # mm [A] clearance of a pad's inner edge beyond it
PINNA_EDGE_R = PINNA_HALF_P95 + PINNA_EDGE_CLR   # no pad edge closer to the canal axis than this
MIN_SEP_DEG = 30.0     # deg [A] pads, saddle and cable clip apart on the ring (tab width + screw access)
EYE_R_SEARCH = 25.0    # mm [A] largest eye radius on the cup end in the layout search (the per-module limit is tune_eye.r_max)


def apply_pad_scale(des):
    """Pad footprints = Base pads x pad_scale; the temporal pad can be stretched further on its own
    (pad_t_stretch = (radial a, tangential b) factors): it is the pad whose tangential stiffness takes the
    weight off the auricle root (results/root_levers.json)."""
    s = des.get("pad_scale", 1.0)
    base = dz.BASE
    for k in PAD_KEYS:
        des[k] = base[k] * s
    fa, fb = des.get("pad_t_stretch") or (1.0, 1.0)
    des["pad_t_a"] *= fa
    des["pad_t_b"] *= fb
    return des


def pad_edge_clearance(des):
    """Radial distance of each pad's inner edge from the canal axis (pad centre radius - a/2), mm."""
    des = apply_pad_scale(dict(des))
    out = {"temporal": des["temporal_r"] - des["pad_t_a"] / 2, "mastoid": des["mastoid_r"] - des["pad_m_a"] / 2}
    if des.get("post_a") is not None:
        out["post"] = des["post_r"] - des["pad_p_a"] / 2
    return out


def evaluate(mp, des, D=50, n_dyn=20, dyn=True, mu_level=1):
    """Lexicographic max-min score: first every normal-use margin (1 g set + static), then the
    slip-free fraction of the 2 g set."""
    des = apply_pad_scale(dict(des))
    p = dz.derived(des, D)
    C = sp.contact_set(p, des, mu_level=mu_level, mu_scale=1 / GAMMA_MU)
    link, L = sp.make_link(p, des)
    out = dict(des=des, link=L)
    r0 = sp.solve(C, sp.static_wrench(mp, p, des), link, fric=True)
    if not r0["ok"]:
        out["score"] = -1e9; return out
    skin = [x for x in r0["contacts"] if not x["name"].startswith("S root")]
    out["static"] = dict(sp.metrics(r0, C), contacts=r0["contacts"], p_skin=max(x["p_mean"] for x in skin))
    wn, _ = sp.sweep(mp, p, des, C, link, "1 g normal", n_dir=20, n_grav=7, n_cable=3)
    out["normal"] = wn
    m = {
        "1g slip-free": 1.0 if wn["released"] == 0 else -10 * wn["released"] / wn["n_cases"],
        "1g tilt": 1 - wn["rot_xy"][0] / ROT_NORMAL,
        "1g seated": 1.0 if wn["unseated"] == 0 else -10 * wn["unseated"] / wn["n_cases"],
        "static all pads loaded": (min(x["Fn"] for x in r0["contacts"]) - sp.F_MIN) / 0.3,
        "static skin pressure": 1 - out["static"]["p_skin"] / TISSUE["p_sustained"].v,
    }
    m = {k: max(float(v), -10.0) for k, v in m.items()}
    prim = min(m.values())
    out["margins"] = m
    score = min(prim, 1.0)
    if dyn:
        wd, _ = sp.sweep(mp, p, des, C, link, "2 g dynamic", n_dir=n_dyn, n_grav=3, n_cable=2)
        out["dynamic"] = wd
        rel2 = wd["released"] / wd["n_cases"]
        m["2g slip fraction"] = rel2
        if prim >= 0:
            score = min(prim, 1.0) + (1 - rel2) * 2
    out["score"] = score
    return out


BOUNDS = dict(temporal_a=(10, 60), temporal_r=(40, 58), mastoid_a=(205, 250), mastoid_r=(42, 60),
              post_a=(130, 175), post_r=(42, 60), link_x=(-25, 5), link_y=(-5, 30), link_preload=(2.5, 5.0),
              pad_scale=(1.1, 1.6))


def geometric_ok(des):
    angs = [des["temporal_a"], des["saddle_a"], des["post_a"], des["mastoid_a"], des["cable_a"]]
    for i in range(len(angs)):
        for j in range(i + 1, len(angs)):
            dd = abs((angs[i] - angs[j] + 180) % 360 - 180)
            if dd < MIN_SEP_DEG:
                return False
    if des.get("link_mode") == "ring":
        for a in angs:
            if abs((a - des["link_a"] + 180) % 360 - 180) < 20:
                return False
    if des.get("link_mode") == "cup" and math.hypot(des["link_x"], des["link_y"]) > EYE_R_SEARCH:
        return False          # eye boss must sit on the cup end
    return all(des[k] >= PINNA_EDGE_R for k in ("temporal_r", "mastoid_r", "post_r"))


def random_search(mp, base, n=300, seed=1, dyn=False, center=None, spread=1.0):
    rng = np.random.default_rng(seed)
    best = []
    for i in range(n):
        des = dict(base)
        for k, (lo, hi) in BOUNDS.items():
            if center is None:
                des[k] = float(rng.uniform(lo, hi))
            else:
                des[k] = float(np.clip(center[k] + rng.normal(0, spread * (hi - lo) / 6), lo, hi))
        if not geometric_ok(des):
            continue
        ev = evaluate(mp, des, dyn=dyn)
        best.append((ev["score"], des, ev.get("margins")))
    best.sort(key=lambda x: -x[0])
    return best


def refine(mp, des, steps=(4.0, 2.0, 1.0), dyn=True):
    """Coordinate pattern search on the max-min score."""
    cur = evaluate(mp, des, dyn=dyn)
    scale = {k: (hi - lo) / 20 for k, (lo, hi) in BOUNDS.items()}
    for s in steps:
        improved = True
        while improved:
            improved = False
            for k in BOUNDS:
                for sgn in (+1, -1):
                    cand = dict(cur["des"]); cand[k] = float(np.clip(cand[k] + sgn * s * scale[k] / 4, *BOUNDS[k]))
                    if not geometric_ok(cand):
                        continue
                    ev = evaluate(mp, cand, dyn=dyn)
                    if ev["score"] > cur["score"] + 1e-4:
                        cur = ev; improved = True
    return cur
