#!/usr/bin/env python3
"""
UMEH-2 — the sustained state in use: frictional shakedown of the worn cradle (support.shakedown).

The donned state (sequence A: clamp, then let go; or B: hung on the ear first) is only where friction starts.
Worn, the head moves: every load of the 1 g normal set of the eye tune (tune_eye.SET1 — gravity directions in the
head-tilt cone, the head-rotation phases, the cable directions; support.load_cases) is applied from the current
state and removed again, cycle after cycle, with the path-dependent friction of support.Model. Where a pad reaches
its friction limit during a case it slips a little and keeps the offset when the load is removed; repeated, this
ratchets the side's weight from pad friction onto the saddle's root zones until the contact forces repeat from cycle to
cycle (the pads may go on slipping back and forth, but the load no longer moves). The auricle-root pressure of that end
state is the SUSTAINED root pressure in use.

Runs for every module (Final design with its tuned eye and the Final CAD mass properties of results/final_sizes.json)
and both donning sequences. At 60 mm (the heaviest module) also: the levers that could keep weight on the pads
(pad friction, preload, root bearing area, root friction, liner stiffness, the eye tune's best eyes) and the side
mass at which the shakedown root pressure equals the sustained limit (mass and inertia scaled, COM kept).
Writes results/shakedown.json. Run after run_all.py (it reads results/link.json and results/final_sizes.json).
"""
import json, math, os, sys, time
import concurrent.futures as cfu, multiprocessing as mpr
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from umeh2 import configs as cf, analysis as an, support as sp, design as dz, layout as lo   # noqa: E402
from umeh2.materials import TISSUE, G, FRICTION                                               # noqa: E402
from umeh2.util import js                                                     # noqa: E402
import tune_eye as te                                                         # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
CAT = "1 g normal"
N_CYC = 25          # cycles at most
TOL = 0.002         # converged: no contact normal force changes by more than TOL x |weight| over a cycle
T0 = time.time()

FINAL = cf.final_design()
_lk = json.load(open(os.path.join(RES, "link.json")))["Final"]["chosen"]
FINAL["wire_d"] = _lk["d_mm"]; FINAL["link_coils"] = _lk["n_coil"]          # as run_all.py
_F = json.load(open(os.path.join(RES, "final_sizes.json")))
MPT = {D: (_F[str(D)]["mass"], np.asarray(_F[str(D)]["com"]), np.asarray(_F[str(D)]["I"])) for D in dz.SIZES}
P_SUS = TISSUE["p_sustained"].v


def log(*a):
    print(f"[{time.time() - T0:8.1f}s]", *a, flush=True)


def cases_for(mpt, d, des):
    s = te.SET1
    return [W for _, W in sp.load_cases(mpt, d, des, CAT, s["n_dir"], s["n_cable"], s["n_grav"])]


def run_case(des_, D, seq="A", cmod=None, mscale=1.0, zero=False):
    """Shakedown of one configuration; cmod edits the contact list (lever), mscale scales mass and inertia;
    zero=True cycles the static load itself (procedure check: nothing may move)."""
    M, com, I = MPT[D]
    mpt = (M * mscale, com, I * mscale)
    des, d, C, link, L = an.support_model(des_, D)
    if cmod:
        C = [cmod(dict(c)) for c in C]
    model = sp.Model(C, link)
    W_st = sp.static_wrench(mpt, d, des)
    cs = [W_st] * len(cases_for(mpt, d, des)) if zero else cases_for(mpt, d, des)
    r = sp.shakedown(model, W_st, cs, seq, N_CYC, TOL)
    if not r["ok"]:
        return dict(ok=False, why=r.get("why"))
    area = {c["name"]: c["area"] for c in C}
    nrm = {c["name"]: np.asarray(c["n"]) for c in C}
    roots = [n for n in area if n.startswith("S root")]
    pads = [n for n in area if n[0] in "TMP"]
    st = r["state"]
    Fn = dict(zip(area, map(float, st["Fn"])))
    Ft = dict(zip(area, (float(np.linalg.norm(x)) for x in st["Ft"])))
    mu = {c["name"]: c["mu"] for c in C}
    rp = lambda h: max(h[n] / area[n] for n in roots)
    weight = mpt[0] * G
    return dict(ok=True, cycles=r["cycles"], converged=r["converged"], n_rel=r["n_rel"], n_cases=len(cases_for(mpt, d, des)),
                n_slip=r["n_slip"],
                root_p_donned=rp(r["hist"][0]), root_p=rp(r["hist"][-1]), root_p_hist=[rp(h) for h in r["hist"]],
                root_share_y=float(sum(Fn[n] * nrm[n][1] for n in roots) / weight),
                pad_p_max=max(Fn[n] / area[n] for n in pads), weight=weight, mass=mpt[0],
                contacts={n: dict(Fn=Fn[n], p_mean=Fn[n] / area[n], Ft=Ft[n],
                                  mu_use=(Ft[n] / (mu[n] * Fn[n]) if mu[n] > 0 and Fn[n] > 1e-9 else None)) for n in area})


# ------------------------------------------------------------------------------------------------ levers (60 mm)
def pads_mu(f):
    return lambda c: dict(c, mu=c["mu"] * f) if c["name"][0] in "TMP" else c


def root_area(f):
    return lambda c: dict(c, area=c["area"] * f, k=c["k"] * f) if c["name"].startswith("S root") else c


def both(*fs):
    def g(c):
        for f_ in fs:
            c = f_(c)
        return c
    return g


def lever_list():
    P0 = FINAL["link_preload"]; Pr = FINAL.get("link_preload_ref") or P0
    mu_face = next(c["mu"] for c in an.support_model(FINAL, 60)[2] if c["name"] == "T temporal")
    out = [("Final", FINAL, None)]
    mu_hi = FRICTION["silicone/dry skin"][0][2]
    for f in (lo.GAMMA_MU, 2.0):
        note = (" (the nominal μ: no γμ)" if abs(f - lo.GAMMA_MU) < 1e-9 else
                f" (faced pads μ {mu_face * f:.2f}, above the {mu_hi:.2f} upper literature value for silicone on dry skin)" if mu_face * f > mu_hi else "")
        out.append((f"pad friction × {f:g}{note}", FINAL, pads_mu(f)))
    out.append((f"post-sup pad faced too (μ {mu_face:.2f})", FINAL, lambda c: dict(c, mu=mu_face) if c["name"].startswith("P ") else c))
    for f in (1.2, 1.4):
        out.append((f"link preload × {f:g}", dict(FINAL, link_preload=P0 * f, link_preload_ref=Pr * f), None))
    for f in (2.0, 3.0):
        out.append((f"root bearing area × {f:g} (stiffness in proportion)", FINAL, root_area(f)))
    out.append(("root bearing area × 2 and pad friction × 2", FINAL, both(root_area(2.0), pads_mu(2.0))))
    out.append(("frictionless root", FINAL, lambda c: dict(c, mu=0.0) if c["name"].startswith("S root") else c))
    out.append(("root 4 × softer (liner)", FINAL, lambda c: dict(c, k=c["k"] * 0.25) if c["name"].startswith("S root") else c))
    out.append(("rigid arms", dict(FINAL, flex_arms=False), None))
    return out


def job(arg):
    kind = arg[0]
    if kind == "size":
        _, D, seq = arg
        return arg, run_case(FINAL, D, seq)
    if kind == "lever":
        _, i = arg
        lab, des_, cm = lever_list()[i]
        return arg, dict(label=lab, **run_case(des_, 60, "A", cm))
    if kind == "check":
        _, what = arg
        if what == "zero amplitude":
            return arg, dict(label=what, **run_case(FINAL, 60, "A", zero=True))
        return arg, dict(label=what, **run_case(FINAL, 60, "A", lambda c: dict(c, mu=10.0) if c["name"][0] in "TMP" else c))
    if kind == "eye":
        _, x, y = arg
        ps = dict(FINAL["per_size"]); ps["60"] = dict(link_x=x, link_y=y)
        return arg, dict(x=x, y=y, **run_case(dict(FINAL, per_size=ps), 60, "A"))
    if kind == "mass":
        # side mass at which the shakedown root pressure equals the sustained limit (bisection on the mass factor)
        lo_, hi_ = 0.05, 1.0
        r_hi = run_case(FINAL, 60, "A", mscale=hi_)
        rows = [(hi_, r_hi["root_p"])]
        if r_hi["root_p"] <= P_SUS:
            return arg, dict(k=hi_, rows=rows, mass=MPT[60][0])
        for _ in range(7):
            mid = 0.5 * (lo_ + hi_)
            r_ = run_case(FINAL, 60, "A", mscale=mid)
            rows.append((mid, r_["root_p"]))
            if r_["root_p"] > P_SUS:
                hi_ = mid
            else:
                lo_ = mid
        return arg, dict(k=lo_, k_hi=hi_, rows=rows, mass=MPT[60][0] * lo_, mass_hi=MPT[60][0] * hi_)
    raise ValueError(kind)


def main():
    eyes = []
    ep = os.path.join(RES, "eye_tuning.json")
    if os.path.exists(ep):
        top = json.load(open(ep)).get("60", {}).get("top5", [])
        eyes = [("eye", float(t["x"]), float(t["y"])) for t in top]
    jobs = [("mass",)] + [("size", D, s) for D in dz.SIZES for s in ("A", "B")] + \
           [("lever", i) for i in range(len(lever_list()))] + eyes + \
           [("check", "zero amplitude"), ("check", "non-slipping pads (μ = 10)")]
    out = dict(note=__doc__.strip().split("\n\n")[1].replace("\n", " "), cat=CAT, set=te.set_counts()["1 g"], n_cyc=N_CYC, tol=TOL,
               p_sustained=P_SUS, sizes={}, levers=[], eyes=[], mass_limit=None, checks=[])
    ctx = mpr.get_context("fork")
    with cfu.ProcessPoolExecutor(4, mp_context=ctx) as ex:
        for arg, r in ex.map(job, jobs, chunksize=1):
            if arg[0] == "size":
                out["sizes"].setdefault(str(arg[1]), {})[arg[2]] = r
                log(f"D={arg[1]} {arg[2]}: root p {r.get('root_p_donned', float('nan')) / 1e3:.2f} -> {r.get('root_p', float('nan')) / 1e3:.2f} kPa "
                    f"({r.get('cycles')} cycles, converged {r.get('converged')}, released {r.get('n_rel')})")
            elif arg[0] == "lever":
                out["levers"].append(r)
                log(f"lever {r['label']}: root p {r.get('root_p', float('nan')) / 1e3:.2f} kPa, pad p max {r.get('pad_p_max', float('nan')) / 1e3:.2f} kPa")
            elif arg[0] == "check":
                out["checks"].append(r)
                log(f"check {r['label']}: root p {r.get('root_p_donned', float('nan')) / 1e3:.3f} -> {r.get('root_p', float('nan')) / 1e3:.3f} kPa")
            elif arg[0] == "eye":
                out["eyes"].append(r)
                log(f"eye ({r['x']}, {r['y']}): root p {r.get('root_p', float('nan')) / 1e3:.2f} kPa")
            else:
                out["mass_limit"] = r
                log(f"mass limit: {r['mass'] * 1e3:.1f} g (factor {r['k']:.3f})")
    json.dump(js(out), open(os.path.join(RES, "shakedown.json"), "w"), indent=1)
    log("written results/shakedown.json")


if __name__ == "__main__":
    main()
