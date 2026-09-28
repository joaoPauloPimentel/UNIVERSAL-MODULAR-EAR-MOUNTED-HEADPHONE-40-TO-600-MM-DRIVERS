#!/usr/bin/env python3
"""
Arm-leg thickness and saddle-liner thickness, chosen together (run before tune_eye.py).

Both set how the weight of the side is shared between the auricle root (normal force through the saddle) and the skin
pads (tangential springs through the arms): thinner legs make the pad arms more compliant and send weight onto the root;
a thicker liner makes the root contact more compliant and sends weight onto the pads' friction. Legs cost PETG mass; the
liner costs friction margin and softens the saddle's fore-aft location.

Pairs: legs 4.5-6.5 mm in 0.5 mm steps (4.0 fails the 10 N handling load, results/weight.json W4d) x liner 1.5-3.0 mm
in 0.5 mm casting steps. Sizes 55 and 60 mm: the heavy modules, where the auricle-root limit binds (results/root_levers.json);
every size is checked afterwards by tune_eye.py and run_all.py.
  1. CAD mass properties of every pair and size (OpenSCAD meshes, liner at its own thickness),
  2. tune_eye's static criteria (all pads loaded, skin and auricle-root pressure <= 4 kPa, static friction demand <= 1)
     on the 4 mm eye grid,
  3. liner rule, applied to every leg thickness: the thinnest liner with >= 5 % root margin and all static criteria met
     at both sizes (best eye of each size),
  4. those pairs: tune_eye's evaluation (static + the 1 g grid, stopping at the first failing case) at every eye that
     meets the static criteria with the 5 % root margin, then its full evaluation (+ the reduced 2 g set) at the
     MAX_EYES best of each size that meet normal use, at the link preload of calc/final_layout.json with the link wire
     the tune uses there (results/legs_liner.json keeps the preload, wire and 1 g set it ran with).
Choice: every normal-use criterion met at both sizes; then the highest tune score of the worse size (the eye tune's own
score: smallest normal-use margin, then 2 g held fraction x 2, then 1 g pad hold x 0.5); pairs within SCORE_TIE of the
best are ranked by mass. Writes results/legs_liner.json.
"""
import json, os, sys, time, multiprocessing as mpr
import concurrent.futures as cfu

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tune_eye as te
from umeh2 import analysis as an, support as sp, layout as lo
from umeh2.materials import TISSUE
from umeh2.util import js

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEGS = (4.5, 5.0, 5.5, 6.0, 6.5)
LINERS = (1.5, 2.0, 2.5, 3.0)
SIZES = (55, 60)
ROOT_MARGIN = 0.05     # liner rule: >= 5 % auricle-root pressure margin (tissue stiffnesses are [A]/[LIT])
MAX_EYES = 3           # full evaluations per pair and size
SCORE_TIE = 0.02       # tune-score difference below which the lighter pair is preferred
BASE0 = dict(te.BASE)
MPP = {}
T0 = time.time()


def log(*a):
    print(f"[{time.time() - T0:7.1f}s]", *a, flush=True)


def static_only(args):
    leg, t, D, x, y = args
    des, d = an.prepared(dict(BASE0, leg_t=leg, saddle_liner_t=t, link_x=x, link_y=y,
                              per_size={str(an.LINK_REF_D): te.REF_EYES[str(an.LINK_REF_D)]} if D != an.LINK_REF_D else {}), D)
    C = sp.contact_set(d, des, mu_level=1, mu_scale=1 / lo.GAMMA_MU)
    link, L = sp.make_link(d, des)
    model = sp.Model(C, link)
    W_st = sp.static_wrench(MPP[(leg, t, D)], d, des)
    fd = sp.static_friction_demand(C, link, W_st)
    if fd is None or not model.set_base(W_st):
        return dict(leg=leg, t=t, D=D, x=x, y=y, ok=False)
    r0 = model.solve(W_st, fric=True)
    if not r0["ok"]:
        return dict(leg=leg, t=t, D=D, x=x, y=y, ok=False)
    skin = [c for c in r0["contacts"] if not c["name"].startswith("S root")]
    root = [c for c in r0["contacts"] if c["name"].startswith("S root")]
    m = {"static pads": (min(c["Fn"] for c in r0["contacts"]) - sp.F_MIN) / 0.3,
         "static p": 1 - max(c["p_mean"] for c in skin) / TISSUE["p_sustained"].v,
         "static root p": 1 - max(c["p_mean"] for c in root) / TISSUE["p_sustained"].v,
         "static friction": 1 - max(fd.values())}
    return dict(leg=leg, t=t, D=D, x=x, y=y, ok=True, m=m, prim=min(m.values()))


def full_eval(args):
    leg, t, D, x, y = args[:5]
    full, abort = args[5:7] if len(args) > 5 else (True, False)
    P = BASE0["link_preload"]
    te.BASE = dict(BASE0, leg_t=leg, saddle_liner_t=t); te.LEVEL[P] = dict(te.BASE)
    te.MPT[(P, D)] = MPP[(leg, t, D)]
    r = te.evaluate((D, x, y, full, P, abort))          # the tune's evaluation at the current link preload
    return dict(r, leg=leg, t=t)


def main():
    # the link wire the tune uses at this preload (sized on every module, tune_eye.level_base): results/link.json
    # holds the wire of the last run_all, which may belong to another preload
    P = BASE0["link_preload"]
    Lb = te.level_base(P)
    if Lb is None:
        raise SystemExit(f"legs_liner: no stock link wire carries {P:g} N")
    BASE0.update(wire_d=Lb["wire_d"], link_coils=Lb["link_coils"], link_preload_ref=P)
    te.REF_EYES.update(te.ref_eyes())            # the reference module's eye during the tune (tune_eye.cand_des)
    log(f"link preload {P:g} N: wire {BASE0['wire_d']:g} mm, {BASE0['link_coils']} coils")
    for leg in LEGS:
        for t in LINERS:
            for D in SIZES:
                mp = an.mass_properties(dict(BASE0, leg_t=leg, saddle_liner_t=t), D, "LL")
                MPP[(leg, t, D)] = (mp["M"], mp["com"], mp["I"])
        log(f"legs {leg}: mass " + ", ".join(f"liner {t} {MPP[(leg, t, 60)][0] * 1e3:.2f} g" for t in LINERS) + " (60 mm)")
    ctx = mpr.get_context("fork")
    pts = [(leg, t, D, x, y) for leg in LEGS for t in LINERS for D in SIZES for (_, x, y) in te.grid(D, te.GRID_STEPS[0])]
    with cfu.ProcessPoolExecutor(4, mp_context=ctx) as ex:
        st = list(ex.map(static_only, pts, chunksize=8))
    log("static screen:", len(pts), "candidates")
    pairs = []
    for leg in LEGS:
        for t in LINERS:
            row = dict(leg_t=leg, liner_t=t, mass={str(D): MPP[(leg, t, D)][0] for D in SIZES}, sizes={})
            for D in SIZES:
                r = [a for a in st if a["leg"] == leg and a["t"] == t and a["D"] == D and a["ok"]]
                ok5 = sorted((a for a in r if a["prim"] >= 0 and a["m"]["static root p"] >= ROOT_MARGIN), key=lambda a: -a["prim"])
                best = max(r, key=lambda a: a["prim"]) if r else None
                row["sizes"][str(D)] = dict(n=len(r), n_pass=sum(1 for a in r if a["prim"] >= 0), n_pass_root5=len(ok5),
                                            best=best, eyes_root5=[(a["x"], a["y"]) for a in ok5])
            row["static_ok_root5"] = all(row["sizes"][str(D)]["n_pass_root5"] > 0 for D in SIZES)
            pairs.append(row)
    # liner rule per leg thickness
    cand = []
    for leg in LEGS:
        ok = [p for p in pairs if p["leg_t"] == leg and p["static_ok_root5"]]
        if ok:
            p = min(ok, key=lambda p: p["liner_t"])
            p["liner_rule"] = True
            cand.append(p)
    log("liner rule:", ", ".join(f"legs {p['leg_t']} -> liner {p['liner_t']}" for p in cand))
    # eye search per pair and size, as the eye tune's stages 1-2: static + the 1 g grid at every eye meeting the static
    # criteria with the root margin (a candidate stops at its first failing 1 g case), then the full evaluation (+ the
    # reduced 2 g set) of the MAX_EYES best that meet normal use
    pts = [(p["leg_t"], p["liner_t"], D, x, y, False, True) for p in cand for D in SIZES
           for (x, y) in p["sizes"][str(D)]["eyes_root5"]]
    with cfu.ProcessPoolExecutor(4, mp_context=ctx) as ex:
        s1 = list(ex.map(full_eval, pts, chunksize=1))
        log("static + 1 g at every eye meeting the static criteria:", len(pts))
        pts = []
        for p in cand:
            for D in SIZES:
                r = sorted((a for a in s1 if a["leg"] == p["leg_t"] and a["t"] == p["liner_t"] and a["D"] == D
                            and a.get("prim", -1) >= 0), key=lambda a: -a["score1"])[:MAX_EYES]
                pts += [(p["leg_t"], p["liner_t"], D, a["x"], a["y"]) for a in r]
        fr = list(ex.map(full_eval, pts, chunksize=1))
    log("full evaluations:", len(pts))
    done = {(a["leg"], a["t"], a["D"], a["x"], a["y"]) for a in fr}
    fr += [a for a in s1 if (a["leg"], a["t"], a["D"], a["x"], a["y"]) not in done]      # stage-A results of the others
    for p in cand:
        p["full"] = {}
        for D in SIZES:
            r = [a for a in fr if a["leg"] == p["leg_t"] and a["t"] == p["liner_t"] and a["D"] == D]
            passing = [a for a in r if a.get("prim", -1) >= 0 and a.get("score") is not None]
            best = max(passing, key=lambda a: a["score"]) if passing else (max(r, key=lambda a: a.get("score1", -1e9)) if r else None)
            p["full"][str(D)] = dict(evaluated=r, best=best, passes=bool(passing), n_eyes=len(r),
                                     n_pass_1g=sum(1 for a in r if a.get("prim", -1) >= 0))
        p["passes_normal_use"] = all(p["full"][str(D)]["passes"] for D in SIZES)
        p["score_worse_size"] = min((p["full"][str(D)]["best"] or {}).get("score") or -1e9 for D in SIZES)
    ok = [p for p in cand if p["passes_normal_use"]]
    choice = None
    if ok:
        top = max(p["score_worse_size"] for p in ok)
        near = [p for p in ok if p["score_worse_size"] >= top - SCORE_TIE]
        choice = min(near, key=lambda p: p["mass"]["60"])
    out = dict(note=("legs x liner study; static on the 4 mm eye grid, full tune_eye evaluation (static + 1 g set + "
                     "reduced 2 g) at the eyes meeting the static criteria with the 5 % root margin"),
               link_preload=BASE0["link_preload"], wire_d=BASE0["wire_d"], link_coils=BASE0["link_coils"], sets=te.set_counts(),
               legs=LEGS, liners=LINERS, sizes=SIZES, root_margin=ROOT_MARGIN, max_eyes=MAX_EYES, score_tie=SCORE_TIE,
               pairs=pairs, candidates=[(p["leg_t"], p["liner_t"]) for p in cand],
               choice=(choice["leg_t"], choice["liner_t"]) if choice else None)
    json.dump(js(out), open(os.path.join(ROOT, "results", "legs_liner.json"), "w"), indent=1)
    for p in cand:
        log(f"legs {p['leg_t']} liner {p['liner_t']}: mass60 {p['mass']['60'] * 1e3:.2f} g, normal use "
            f"{'PASS' if p['passes_normal_use'] else 'FAIL'}, score (worse size) {p['score_worse_size']:.3f}; " +
            "; ".join(f"D{D} eye ({(p['full'][str(D)]['best'] or {}).get('x')}, {(p['full'][str(D)]['best'] or {}).get('y')}) "
                      f"prim {(p['full'][str(D)]['best'] or {}).get('prim', float('nan')):.3f} "
                      f"2 g released {(p['full'][str(D)]['best'] or {}).get('slip2')}" for D in SIZES))
    log("choice:", out["choice"])


if __name__ == "__main__":
    main()
