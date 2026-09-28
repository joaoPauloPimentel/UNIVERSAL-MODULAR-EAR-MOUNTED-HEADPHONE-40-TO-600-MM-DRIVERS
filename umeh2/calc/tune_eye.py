#!/usr/bin/env python3
"""
Per-module link-eye position on the cup end.

The cradle (ring, arms, pads, saddle) and the occipital link are common to every
driver size; the cup - and therefore the eye boss the link is screwed to - is
part of each module. Heavier/deeper modules have a larger tipping moment
M1 = m g z_com, so the eye (the line of action of the preload) must sit
M1/P above the support-polygon centroid, and each module gets its own eye.

For every driver size:
  1. CAD mass properties of the complete side (OpenSCAD meshes + hardware),
  2. grid over (link_x, link_y) on the cup end face, limited so that the eye
     boss lies inside the cup outer wall: r <= cup_ro - eye_boss_d/2 - 0.5 mm,
  3. every candidate: static case, the 1 g worst-case grid (support.GRID_1G: upright + head tilt
     at half and all of the cone x azimuths, x 10 head-rotation cases [none, +-alpha about 3 axes,
     omega about 3 axes] x cable pulls straight down and at the edge of the cable cone, SET1) and a
     reduced 2 g set (SET2); set_counts() gives the resulting numbers of directions and cases,
  4. lexicographic max-min score: first the smallest normalised normal-use
     margin (slip, tilt <= 2 deg, seating margin = third-largest skin contact
     force - 0.1 N, static pad load, static skin pressure, static auricle-root
     pressure (donning A), static friction demand), then the fraction of 2 g combinations without gross slip
     (weight 2) and the fraction of 1 g cases without pad micro-slip (0.5),
  5. staged: (1) static + 1 g on the whole 4 mm grid, (2) the 2 g set on the
     ten best normal-use candidates of each size, (3) full evaluation on 2 mm
     and then 1 mm neighbourhoods of the best candidate, (4) the dense 1 g check
     and its local refinement (analysis.dense_1g_chunk / refine_1g_chunk: finer
     than the grid, between its points) on the best candidates in score order
     until one passes (at most MAX_VERIFY per module): the chosen eye.
  6. the link preload (common to every module) is tuned with the eyes: stage 1 runs at preload
     levels from the layout preload upwards (PRELOAD_STEP), each with the link wire sized on every
     module for that preload (analysis.size_link_on_modules, at the layout's reference eye pulled inside
     each module's eye limit, ref_eyes); the
     LOWEST level at which every module has an eye meeting every normal-use criterion (stage 1) and
     passing stage 4 is taken [design rule: the least preload keeps the pad pressures and the wire
     stress lowest]; stages 2-4 run at a level once stage 1 passes on every module. A candidate stops at its first failing 1 g case (it can no
     longer pass; the cases are taken outward-first so that failures show early).
Writes per_size and link_preload into calc/final_layout.json. The last refinement step is 1 mm,
so the eye lies on a 1 mm grid (print XY tolerance +-0.15 mm); the stored value
is rounded to 0.5 mm, which leaves grid points unchanged.
"""
import json, math, os, sys, time, multiprocessing as mpr
import concurrent.futures as cfu
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from umeh2 import design as dz, configs as cf, analysis as an, support as sp, layout as lo
from umeh2.materials import TISSUE

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAYOUT = os.path.join(ROOT, "calc", "final_layout.json")
T0 = time.time()
BASE = cf.final_design()
BASE.pop("per_size", None)
lk = json.load(open(os.path.join(ROOT, "results", "link.json")))["Final"]["chosen"]
BASE["wire_d"] = lk["d_mm"]; BASE["link_coils"] = lk["n_coil"]
MPT = {}


def log(*a):
    print(f"[{time.time() - T0:7.1f}s]", *a, flush=True)


def r_max(D):
    d = an.prepared(BASE, D)[1]
    return d["cup_ro"] - d["eye_boss_d"] / 2 - 0.5


SKIN_PADS = sp.SKIN_PADS
SET1 = dict(n_dir=1, n_cable=0, n_grav=0)     # 1 g set of every candidate: the worst-case grid support.GRID_1G
                                              # (n_grav / n_cable are not used for a grid category)
SET2 = dict(n_cable=2, n_grav=3)              # reduced 2 g set (with N_DIR2 dynamic directions)


PRELOAD_STEP = 0.4      # N [design rule], preload levels: the layout preload, then this step upwards
PRELOAD_LEVELS = 5      # levels tried at most
LEVEL = {}              # preload -> design base with the link wire sized for it (level_base), filled before forking


def ref_eyes():
    """The layout's reference eye on every module, pulled radially inside that module's eye limit r_max (the
    reference eye lies outside the limit on the small cups), so the wire is sized on eyes the tune can choose."""
    out = {}
    for D in dz.SIZES:
        x, y = float(BASE["link_x"]), float(BASE["link_y"])
        r, rm = math.hypot(x, y), r_max(D)
        s = min(1.0, rm / r) if r > 0 else 1.0
        out[str(D)] = dict(link_x=x * s, link_y=y * s)
    return out


REF_EYES = {}         # ref_eyes(), filled in main before forking


def cand_des(P, D, x, y):
    """Design of candidate eye (x, y) on module D at preload level P. The link preload of a module other than the
    reference module follows from the reference module's eye (analysis.link_preload_at), which is held at REF_EYES
    during the tune (the Final uses the tuned 50 mm eye: run_all re-scores, results/eye_check.json)."""
    des = dict(LEVEL[P], link_x=x, link_y=y)
    if D != an.LINK_REF_D and not des.get("per_size"):      # a design with its own per_size (the Final) keeps it
        des["per_size"] = {str(an.LINK_REF_D): REF_EYES[str(an.LINK_REF_D)]}
    return des


def level_base(P):
    """BASE at link preload P (on the reference module) with the link wire sized on every module for P
    (analysis.size_link_on_modules at ref_eyes()); None if no stock wire carries P."""
    des = dict(BASE, link_preload=P, link_preload_ref=P, per_size=ref_eyes())
    cands, cm = an.size_link_on_modules(des)
    if cm is None:
        return None
    des.pop("per_size")                  # the tune sets each candidate's eye itself
    des["wire_d"] = cm["d_mm"]; des["link_coils"] = cm["n_coil"]
    return des


def outward_first(tw):
    tag = tw[0]
    return -(float(tag["g_dir"][2]) + float(tag["cable_dir"][2]))


def evaluate(args):
    D, x, y, full, P, abort = args
    des, d = an.prepared(cand_des(P, D, x, y), D)
    C = sp.contact_set(d, des, mu_level=1, mu_scale=1 / lo.GAMMA_MU)
    link, L = sp.make_link(d, des)
    model = sp.Model(C, link)
    mpt = MPT[(P, D)]                  # mass properties with this level's link wire (filled before forking)
    W_st = sp.static_wrench(mpt, d, des)
    fd = sp.static_friction_demand(C, link, W_st)
    if fd is None or not model.set_base(W_st):
        return dict(D=D, x=x, y=y, P=P, score=-1e9, score1=-1e9)
    r0 = model.solve(W_st, fric=True)
    if not r0["ok"]:
        return dict(D=D, x=x, y=y, P=P, score=-1e9, score1=-1e9)
    skin = [c for c in r0["contacts"] if not c["name"].startswith("S root")]
    root = [c for c in r0["contacts"] if c["name"].startswith("S root")]
    m = {"static pads": (min(c["Fn"] for c in r0["contacts"]) - sp.F_MIN) / 0.3,
         "static p": 1 - max(c["p_mean"] for c in skin) / TISSUE["p_sustained"].v,
         "static root p": 1 - max((c["p_mean"] for c in root), default=0.0) / TISSUE["p_sustained"].v,
         "static friction": 1 - max(fd.values())}
    seat = np.inf; tilt = 0.0; rel = 0; n = 0; padslip = 0; aborted = False
    cases = list(sp.load_cases(mpt, d, des, "1 g normal", SET1["n_dir"], SET1["n_cable"], SET1["n_grav"]))
    n_all = len(cases)
    if abort:
        if min(m.values()) < 0:                    # a static criterion fails: the candidate cannot pass
            cases, aborted = [], True
        cases.sort(key=outward_first)
    for tag, W in cases:
        n += 1
        r = model.solve(W, fric=True)
        if not r["ok"]:
            rel += 1
            if abort:
                aborted = True; break
            continue
        padslip += any(c["slipping"] for c in r["contacts"] if c["name"] in SKIN_PADS)
        fs = sorted((c["Fn"] for c in r["contacts"] if c["name"][0] in "TMP" or c["name"] == "S scalp"), reverse=True)
        seat = min(seat, (fs[2] if len(fs) > 2 else 0.0) - sp.F_MIN)
        tilt = max(tilt, math.degrees(np.linalg.norm(r["q"][3:5])))
        if abort and (seat < 0 or tilt > lo.ROT_NORMAL):
            aborted = True; break
    if n:                                                  # a static abort solved no 1 g case: no 1 g margins
        m["1g slip-free"] = 1.0 if rel == 0 else -10 * rel / n
        m["1g tilt"] = 1 - tilt / lo.ROT_NORMAL
        m["1g seating margin"] = seat / 0.3 if np.isfinite(seat) else -10
    m = {k: max(float(v), -10.0) for k, v in m.items()}
    prim = min(m.values())
    out = dict(D=D, x=x, y=y, margins=m, prim=prim, P=P, P_D=des["link_preload"], seat_N=seat, tilt=tilt,
               mu_demand=fd, padslip1=padslip / n if n else None, aborted=aborted, n1=n, n1_all=n_all)
    # an aborted candidate stopped at its first failing case: its 1 g margins are partial (n1 of n1_all cases)
    out["score1"] = min(prim, 1.0) + (0.5 * (1 - out["padslip1"]) if prim >= 0 else 0.0)
    out["score"] = out["score1"] if prim < 0 else None
    if full and prim >= 0:
        w2, _ = sp.sweep(mpt, d, des, C, link, "2 g dynamic", n_dir=N_DIR2, n_grav=SET2["n_grav"], n_cable=SET2["n_cable"])
        out["slip2"] = w2["released"] / w2["n_cases"]
        out["score"] = out["score1"] + 2 * (1 - out["slip2"])
    return out


N_DIR2 = 10       # 2 g directions per candidate (the case count follows from SET2, see set_counts)
K_2G = 10         # stage-2 candidates per size (best static/1 g score among those passing normal use)
GRID_STEPS = (4.0, 2.0, 1.0)   # mm: stage-1 grid, then the refinement steps around the best candidate


def set_counts(D=50):
    """Numbers of gravity / dynamic / head-rotation / cable directions and load cases of the two tuning sets
    (enumerated from support.load_cases, so the report states what was run)."""
    des, d = an.prepared(BASE, D)
    mp = MPT.get(D) or (0.17, np.zeros(3), np.eye(3) * 1e-5)
    out = {}
    for name, cat, n_dir, s_ in (("1 g", "1 g normal", SET1["n_dir"], SET1), ("2 g", "2 g dynamic", N_DIR2, SET2)):
        g, dd, a, c, n = set(), set(), set(), set(), 0
        for tag, _ in sp.load_cases(mp, d, des, cat, n_dir, s_["n_cable"], s_["n_grav"]):
            n += 1
            g.add(tuple(np.round(tag["g_dir"], 9))); dd.add(tuple(np.round(tag["dyn_dir"], 9)))
            a.add((tag["axis"], tag["sign"], tag["phase"])); c.add(tuple(np.round(tag["cable_dir"], 9)))
        out[name] = dict(cat=cat, n_dir=n_dir, n_cable=s_["n_cable"], n_grav=s_["n_grav"], cases=n, gravity=len(g),
                         dynamic=len(dd), head_motion=len(a), cable=len(c))
    return out


def grid(D, step):
    rm = r_max(D)
    pts = []
    for x in np.arange(-27.0, 12.01, step):
        for y in np.arange(-12.0, 30.01, step):
            if math.hypot(x, y) <= rm:
                pts.append((D, float(x), float(y)))
    return pts


def run(ex, pts, what):
    out = []
    for i, r in enumerate(ex.map(evaluate, pts, chunksize=1)):
        out.append(r)
        if (i + 1) % 25 == 0 or i + 1 == len(pts):
            log(f"{what}: {i + 1}/{len(pts)}")
    return out


def ranked(rs):
    return sorted((r for r in rs if r.get("score") is not None), key=lambda r: -r["score"])


MAX_VERIFY = 4    # stage-4 candidates per module (dense check + local refinement each)


def verify_module(ex, P, D, rs_D):
    """Stage 4 for one module: the dense 1 g check and its local refinement on the best candidates meeting normal use
    (score order) until one passes. Returns dict(chosen=candidate or None, checks=[summary per candidate checked])."""
    cands = [r for r in ranked(rs_D) if r.get("prim", -1) >= 0][:MAX_VERIFY]
    checks = []
    for c in cands:
        des = cand_des(P, D, c["x"], c["y"])
        mpt = MPT[(P, D)]
        dense = an.dense_1g_merge(list(ex.map(an.dense_1g_chunk, an.dense_1g_jobs(des, D, mpt), chunksize=1)))
        ref = None
        if dense["ok"]:                   # a failed dense check fails the candidate; refine only a passing one
            rj, seeds = an.refine_1g_jobs(des, D, mpt, dense)
            ref = an.refine_1g_merge(list(ex.map(an.refine_1g_chunk, rj, chunksize=1)), seeds) if rj else None
        ok = bool(dense["ok"]) and (ref is None or bool(ref["ok"]))
        sm = lambda r_: None if r_ is None else dict(n=r_["n"], released=r_["released"], released_numerical=r_["released_numerical"],
                                                     unseated=r_["unseated"], tilt_over=r_["tilt_over"], worst_tilt=r_["worst_tilt"][0],
                                                     min_seat=r_["min_seat"][0], n_fails=len(r_["fails"]), ok=r_["ok"])
        checks.append(dict(x=c["x"], y=c["y"], score=c.get("score"), ok=ok, dense=sm(dense), refine=sm(ref)))
        log(f"stage 4, {P:g} N, D={D}: eye ({c['x']:.1f}, {c['y']:.1f}) dense {dense['n']} cases: released {dense['released']}, "
            f"tripod lost {dense['unseated']}, tilt over {dense['tilt_over']}, min seat {dense['min_seat'][0]:.3f} N"
            + (f"; refinement {ref['n']} cases, fails {len(ref['fails'])}, min seat {ref['min_seat'][0]:.3f} N" if ref else "")
            + f" -> {'PASS' if ok else 'fail'}")
        if ok:
            return dict(chosen=c, checks=checks)
    return dict(chosen=None, checks=checks)


def main():
    lay0 = json.load(open(LAYOUT))
    P0 = float(lay0.get("_link_preload_layout", lay0["link_preload"]))       # the layout search's preload
    levels = [round(P0 + i * PRELOAD_STEP, 3) for i in range(PRELOAD_LEVELS)]
    REF_EYES.update(ref_eyes())
    for P in levels:
        LEVEL[P] = level_base(P)
    if LEVEL[levels[0]] is None:
        raise SystemExit(f"no stock link wire carries the layout preload {levels[0]:g} N")
    for D in dz.SIZES:
        for P in levels:
            if LEVEL[P] is not None:
                mp = an.mass_properties(dict(LEVEL[P], per_size=REF_EYES), D, "T")   # main process only (writes the SCAD);
                                                                                           # eye boss at the pulled-in ref eye
                MPT[(P, D)] = (mp["M"], mp["com"], mp["I"])
        MPT[D] = MPT[(levels[0], D)]
        log(f"D={D}: mass {MPT[D][0] * 1e3:.1f} g (preload {levels[0]:g} N), COM {np.round(MPT[D][1] * 1e3, 2)} mm, eye r_max {r_max(D):.1f} mm")
    for P in levels:
        L_ = LEVEL[P]
        log(f"preload {P:g} N: " + (f"wire {L_['wire_d']:g} mm, {L_['link_coils']} coils" if L_ else "no stock wire carries it"))
    ctx = mpr.get_context("fork")
    res = {D: [] for D in dz.SIZES}
    level_log = []
    chosen = None
    verified = {}
    with cfu.ProcessPoolExecutor(4, mp_context=ctx) as ex:
        # preload levels upwards; at each level stage 1 (static + 1 g grid on the whole 4 mm eye grid), and when every
        # module has a passing eye, stages 2-4; the first level whose stage 4 verifies an eye on every module is taken
        for P in levels:
            if LEVEL[P] is None:
                level_log.append(dict(P=P, wire=None))
                break
            pts = [p + (False, P, True) for D in dz.SIZES for p in grid(D, GRID_STEPS[0])]
            log(f"stage 1 at preload {P:g} N (static + 1 g) on the coarse grid:", len(pts), "candidates")
            rs = run(ex, pts, f"stage 1, {P:g} N")
            npass = {D: sum(1 for r in rs if r["D"] == D and r.get("prim", -1) >= 0) for D in dz.SIZES}
            level_log.append(dict(P=P, wire=dict(d_mm=LEVEL[P]["wire_d"], n_coil=LEVEL[P]["link_coils"]),
                                  n_pass={str(D): npass[D] for D in dz.SIZES},
                                  n_eval={str(D): sum(1 for r in rs if r["D"] == D) for D in dz.SIZES},
                                  best_prim={str(D): max((r.get("prim", -1e9) for r in rs if r["D"] == D), default=None) for D in dz.SIZES}))
            log(f"preload {P:g} N: candidates passing normal use per module {npass}")
            chosen = P
            verified = {}
            res = {D: [r for r in rs if r["D"] == D] for D in dz.SIZES}
            if not all(npass[D] > 0 for D in dz.SIZES):
                continue
            for D in dz.SIZES:
                MPT[D] = MPT[(P, D)]
            # stage 2: the 2 g set for the K_2G best normal-use candidates of each size
            pts = []
            for D in dz.SIZES:
                ok = sorted((r for r in res[D] if r.get("prim", -1) >= 0), key=lambda r: -r["score1"])[:K_2G]
                pts += [(D, r["x"], r["y"], True, P, True) for r in ok]
            new = {(r["D"], r["x"], r["y"]): r for r in run(ex, pts, "stage 2 (2 g)")}
            for D in dz.SIZES:
                res[D] = [new.get((D, r["x"], r["y"]), r) for r in res[D]]
            # stage 3: full evaluation on 2 mm, then 1 mm neighbourhoods of the best candidate
            for step in GRID_STEPS[1:]:
                pts = []
                for D in dz.SIZES:
                    top = ranked(res[D])[:1]
                    seen = {(r["x"], r["y"]) for r in res[D]}
                    rm = r_max(D)
                    for t in top:
                        for dx in (-step, 0, step):
                            for dy in (-step, 0, step):
                                x, y = t["x"] + dx, t["y"] + dy
                                if (x, y) not in seen and math.hypot(x, y) <= rm:
                                    seen.add((x, y)); pts.append((D, x, y, True, P, True))
                for r in run(ex, pts, f"refine {step} mm"):
                    res[r["D"]].append(r)
            # stage 4: the dense check and its local refinement (analysis.dense_1g_chunk / refine_1g_chunk) on the best
            # candidates meeting normal use, in score order, until one passes (at most MAX_VERIFY per module)
            verified = {D: verify_module(ex, P, D, res[D]) for D in dz.SIZES}
            level_log[-1]["dense_verified"] = {str(D): verified[D]["chosen"] is not None for D in dz.SIZES}
            level_log[-1]["dense_checks"] = {str(D): verified[D]["checks"] for D in dz.SIZES}
            if all(verified[D]["chosen"] is not None for D in dz.SIZES):
                break
            log(f"preload {P:g} N: no candidate passes the dense check at "
                + ", ".join(f"{D} mm" for D in dz.SIZES if verified[D]["chosen"] is None) + "; next preload level")
    P = chosen
    for D in dz.SIZES:
        MPT[D] = MPT[(P, D)]
    per = {}
    summary = {}
    for D in dz.SIZES:
        # full score (stages 2-3) first, then the static + 1 g score of stage-1-only candidates (fallback levels)
        rs = sorted(res[D], key=lambda r: (r.get("score") is not None and r.get("prim", -1) >= 0,
                                           r["score"] if r.get("score") is not None else r["score1"]), reverse=True)
        v = verified.get(D) or {}
        best = v.get("chosen") or rs[0]
        xr, yr = round(best["x"] * 2) / 2, round(best["y"] * 2) / 2
        per[str(D)] = dict(link_x=xr, link_y=yr)
        summary[str(D)] = dict(best=best, top5=rs[:5], n_eval=len(res[D]),
                               n_pass=sum(1 for r in res[D] if r.get("prim", -1) >= 0),
                               dense_verified=v.get("chosen") is not None, dense_checks=v.get("checks", []),
                               best_score_rank=next((i for i, r in enumerate(rs) if (r["x"], r["y"]) == (best["x"], best["y"])), None))
        log(f"D={D}: eye ({best['x']:.2f}, {best['y']:.2f}) -> ({xr}, {yr}); score {best.get('score') or best.get('score1'):.3f} "
            f"(rank {summary[str(D)]['best_score_rank']}); margins {({k: round(v_, 3) for k, v_ in best.get('margins', {}).items()})}; "
            f"2 g slip {best.get('slip2')}; {summary[str(D)]['n_pass']}/{len(res[D])} candidates pass normal use; dense check "
            f"{'passed' if summary[str(D)]['dense_verified'] else 'NOT passed'}")
    # the inputs this tune assumed, so run_all/make_report can check they are the ones the Final uses
    B = LEVEL[P]
    summary["_inputs"] = dict(wire_d=B["wire_d"], link_coils=B["link_coils"], leg_t=B["leg_t"], link_preload=P,
                              saddle_liner_t=B.get("saddle_liner_t", 0.0), bar_t=B["bar_t"],
                              mass={str(D): MPT[D][0] for D in dz.SIZES}, com={str(D): MPT[D][1] for D in dz.SIZES},
                              sets=set_counts(), grid_mm=list(GRID_STEPS), k_2g=K_2G,
                              preload_layout=P0, preload_step=PRELOAD_STEP, preload_levels=level_log,
                              all_modules_pass=all(summary[str(D)]["n_pass"] > 0 and summary[str(D)]["dense_verified"] for D in dz.SIZES),
                              max_verify=MAX_VERIFY, grid_1g=sp.GRID_1G, dense_1g=sp.DENSE_1G)
    lay = json.load(open(LAYOUT))
    lay.setdefault("_link_preload_layout", P0)
    lay["link_preload"] = P
    lay["per_size"] = per
    lay["_per_size_note"] = ("link eye on each cup and the link preload, from calc/tune_eye.py (common cradle and link; "
                             "module-specific eye); _link_preload_layout = the layout search's preload")
    json.dump(lay, open(LAYOUT, "w"), indent=1)
    from umeh2.util import js
    json.dump(js(summary), open(os.path.join(ROOT, "results", "eye_tuning.json"), "w"), indent=1)
    log("written", LAYOUT)


if __name__ == "__main__":
    main()
