#!/usr/bin/env python3
"""
Parameter sweeps (structure + support) around the Final design at 50 mm, one process per sweep point.
Writes results/sweeps.json. Run after run_all.py (uses its cached mass properties; no CAD is regenerated
here, so the worker processes never touch the shared generated_params.scad).
"""
import json, math, os, sys, time, copy
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from umeh2 import design as dz, configs as cf, analysis as an, support as sp, structure as st, layout as lo, linkspring as ls
from umeh2.materials import FRICTION, TISSUE, SCREW, PETG, GAMMA_M_PRINT, INSERT_PULLOUT, GAMMA_INSERT, SILICONE_GEL

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
QUICK = "--quick" in sys.argv
T0 = time.time()
FINAL = cf.final_design()
link_final = json.load(open(os.path.join(RES, "link.json")))["Final"]["chosen"]
FINAL["wire_d"] = link_final["d_mm"]; FINAL["link_coils"] = link_final["n_coil"]
D = 50
mp = an.mass_properties(FINAL, D, "F")
MPT = (mp["M"], mp["com"], mp["I"])
# the auricle-root sweeps run on the heaviest module, where the root pressure governs
mp60 = an.mass_properties(FINAL, 60, "F")
MPT_BY_SIZE = {50: MPT, 60: (mp60["M"], mp60["com"], mp60["I"])}
from umeh2.util import js  # noqa: E402


def log(*a):
    print(f"[{time.time() - T0:7.1f}s]", *a, flush=True)


def quick_support(des, cats=("1 g normal", "2 g dynamic"), n_dir=20, mpt=None, mu_level=1, gamma_mu=lo.GAMMA_MU, size=D, **kw):
    """Static state (with the static friction demand) and the released / unseated fractions, worst tilt and
    peak pressure of the given categories. Mass properties: the Final side of that size (geometry changes of a
    sweep move the mass by < 2 %, see the arm-thickness rows)."""
    mpt = mpt or MPT_BY_SIZE[size]
    des, d = an.prepared(des, size)
    C = sp.contact_set(d, des, mu_level=mu_level, mu_scale=1 / gamma_mu, **kw)
    link, L = sp.make_link(d, des)
    model = sp.Model(C, link)
    W_st = sp.static_wrench(mpt, d, des)
    based = model.set_base(W_st)
    r0 = model.solve(W_st) if based else dict(ok=False)
    out = dict(static_ok=bool(r0["ok"]), P=des["link_preload"])
    if r0["ok"]:
        out["static_Fn"] = {x["name"]: x["Fn"] for x in r0["contacts"]}
        out["static_p"] = {x["name"]: x["p_mean"] for x in r0["contacts"]}
        out["static_tilt"] = math.degrees(np.linalg.norm(r0["q"][3:5]))
        dem = sp.static_friction_demand(C, link, W_st)
        out["static_mu_demand"] = max(dem.values()) if dem else None
        out["static_mu_pad"] = max(dem, key=dem.get) if dem else None
    for cat in cats:
        w, _ = sp.sweep(mpt, d, des, C, link, cat, n_dir=n_dir, n_grav=4, n_cable=2)
        out[cat] = dict(slip=w["released"] / w["n_cases"], unseated=w["unseated"] / w["n_cases"],
                        tilt=w["rot_xy"][0], p_peak=w["p_peak"][0])
    return out


S40, SIL40 = st.strength("x", temp="40C")


def structural(des, n_acc=60):
    """5 g envelope (held + onset-of-slip contact forces) and the 10 N handling load at one pad: the lowest
    section safety factors (von Mises, interlayer) and the arm-joint minima."""
    ev, (des_, d_, C, link, L) = an.support_eval(des, D, MPT, n_dir=20, n_grav=3, n_cable=2, struct=True,
                                                  cats=["5 g accidental"], bounds=False, n_acc=n_acc)
    arms = [a for a in ("saddle", "temporal", "mastoid", "post") if a != "post" or des_.get("post_a") is not None]
    jh = {}
    hb = an.arm_bound(des_, d_, C, an.F_HANDLING, arms, n_dir=146, joints=jh)
    def low(secs_by_arm):
        vm = min(((S40 / max(v["vm"], 1), f"{a}: {sec}") for a, secs in secs_by_arm.items() for sec, v in secs.items()))
        il = min(((SIL40 / max(v["tau_il_max"], 1), f"{a}: {sec}") for a, secs in secs_by_arm.items() for sec, v in secs.items()))
        return vm, il
    return dict(env=low(ev["5 g accidental"]["arm_stress"]), handling=low(hb),
                joint_env={a: {k: j[k] for k in an.JOINT_KEYS} for a, j in ev["5 g accidental"]["joint"].items()},
                joint_handling={a: {k: j[k] for k in an.JOINT_KEYS} for a, j in jh.items()},
                onset=ev["5 g accidental"].get("onset_lambda"), ev=ev, jh=jh)


# ---------------------------------------------------------------- jobs (one process each; globals restored)
def job(args):
    sec, key, kind, kw = args
    t0 = time.time()
    if kind == "quick":
        glob = kw.pop("_glob", {})
        saved = {}
        try:
            for k, v in glob.items():
                if k == "tissue":
                    saved[k] = {kk: TISSUE[kk].v for kk in ("E_mastoid", "E_temporal", "E_root")}
                    for kk in saved[k]:
                        TISSUE[kk].v = saved[k][kk] * v
                elif k == "ROOT_ARCH_R":
                    saved[k] = sp.ROOT_ARCH_R; sp.ROOT_ARCH_R = v
                elif k == "KT_RATIO":
                    saved[k] = sp.KT_RATIO; sp.KT_RATIO = v
                elif k == "GEL_E":
                    saved[k] = SILICONE_GEL["E"].v; SILICONE_GEL["E"].v = saved[k] * v
            out = quick_support(**kw)
        finally:
            if "tissue" in saved:
                for kk, vv in saved["tissue"].items():
                    TISSUE[kk].v = vv
            if "ROOT_ARCH_R" in saved:
                sp.ROOT_ARCH_R = saved["ROOT_ARCH_R"]
            if "KT_RATIO" in saved:
                sp.KT_RATIO = saved["KT_RATIO"]
            if "GEL_E" in saved:
                SILICONE_GEL["E"].v = saved["GEL_E"]
    else:
        o = structural(kw["des"])
        o.pop("ev"); o.pop("jh")
        out = o
    return sec, key, out, time.time() - t0


R = {}
JOBS = []
# arm (frame) thickness: bar, leg, foot scaled together (structural)
ARM_S = (0.6, 0.8, 0.9, 1.0, 1.2, 1.4)
for s_ in ARM_S:
    JOBS.append(("arm_thickness", s_, "struct", dict(des=dict(FINAL, bar_t=FINAL["bar_t"] * s_, leg_t=FINAL["leg_t"] * s_,
                                                               foot_t=FINAL["foot_t"] * s_, foot_t_mastoid=FINAL["foot_t_mastoid"] * s_))))
# TPU pad thickness
for h in (3.0, 4.5, 6.0, 8.0, 10.0):
    JOBS.append(("pad_thickness", h, "quick", dict(des=dict(FINAL, pad_h=h))))
# support spacing (pad radii)
for s_ in (0.9, 0.95, 1.0, 1.05, 1.1):
    JOBS.append(("support_spacing", s_, "quick", dict(des=dict(FINAL, temporal_r=FINAL["temporal_r"] * s_,
                                                                mastoid_r=min(FINAL["mastoid_r"] * s_, 66), post_r=min(FINAL["post_r"] * s_, 66)))))
# support angles
for dT, dP in ((-15, 0), (15, 0), (0, -15), (0, 15), (-10, 10), (10, -10), (0, 0)):
    JOBS.append(("support_angle", (dT, dP), "quick", dict(des=dict(FINAL, temporal_a=FINAL["temporal_a"] + dT, post_a=FINAL["post_a"] + dP))))
# saddle arch ("hook") radius and wrap angle
for Rr in (16.0, 22.0, 30.0):
    for phi in (25.0, 35.0, 45.0):
        JOBS.append(("saddle_arch", (Rr, phi), "quick", dict(des=dict(FINAL, arch_R=Rr, arch_phi=phi), _glob={"ROOT_ARCH_R": Rr})))
# link eye location map (50 mm module)
xs = (-25, -20, -15, -10, -5, 0, 5) if not QUICK else (-20, -10, 0)
ys = (-5, 0, 5, 10, 15, 20) if not QUICK else (0, 10, 20)
r_eye = an.prepared(FINAL, D)[1]
r_eye = r_eye["cup_ro"] - r_eye["eye_boss_d"] / 2 - 0.5
for x in xs:
    for y in ys:
        if math.hypot(x, y) <= r_eye:
            # the module's own eye (per_size) would override link_x/link_y in analysis.prepared: drop it for D
            ps = {k: v for k, v in (FINAL.get("per_size") or {}).items() if k != str(D)}
            JOBS.append(("eye_map", (x, y), "quick", dict(des=dict(FINAL, link_x=x, link_y=y, per_size=ps), n_dir=16)))
# preload (design friction and low friction)
for P in sorted({2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0, float(FINAL["link_preload"])}):
    JOBS.append(("preload", (P, "design"), "quick", dict(des=dict(FINAL, link_preload=P, link_preload_ref=P))))
    JOBS.append(("preload", (P, "mu_low"), "quick", dict(des=dict(FINAL, link_preload=P, link_preload_ref=P), cats=("1 g normal",),
                                                           mu_level=0, gamma_mu=1.0)))
# friction
for label, lvl, gam, override in (("design: nominal/1.25", 1, 1.25, None), ("nominal", 1, 1.0, None), ("low", 0, 1.0, None),
                                  ("high", 2, 1.0, None), ("sweaty skin, all contacts", None, 1.0, FRICTION["TPU/sweaty or oily skin"][0][1]),
                                  ("sweaty, low", None, 1.0, FRICTION["TPU/sweaty or oily skin"][0][0]),
                                  ("hair everywhere", None, 1.0, FRICTION["TPU/hair (over temporal)"][0][1]),
                                  ("silicone everywhere, nominal", None, 1.0, FRICTION["silicone/dry skin"][0][1])):
    if override is None:
        JOBS.append(("friction", label, "quick", dict(des=FINAL, mu_level=lvl, gamma_mu=gam)))
    else:
        JOBS.append(("friction", label, "quick", dict(des=FINAL, mu_level=1, gamma_mu=1.0, mu_override=override)))
# the cast silicone facing on the temporal and mastoid domes, removed (TPU on skin; friction only, same mass properties)
for D_ in (50, 60):
    JOBS.append(("friction", f"no facing (TPU domes), {D_} mm", "quick", dict(des=dict(FINAL, pad_face=None, pad_face_t=0.0), size=D_)))
# tissue stiffness / helix contact
for lab, fac in (("tissue soft x0.5", 0.5), ("nominal", 1.0), ("tissue stiff x2", 2.0)):
    JOBS.append(("tissue_helix", lab, "quick", dict(des=FINAL, _glob={"tissue": fac})))
JOBS.append(("tissue_helix", f"helix contact also present (k={sp.K_HELIX:g} N/m)", "quick", dict(des=dict(FINAL, rely_helix=True))))
# auricle-root liner (60 mm, where the root pressure governs): thickness, gel modulus, and the tangential/normal
# contact-stiffness ratio [A] that decides how much weight the pads take by friction
for t in (0.0, 1.0, 1.5, 2.0, 2.5, 3.0):
    JOBS.append(("root_liner", t, "quick", dict(des=dict(FINAL, saddle_liner_t=t), size=60)))
for lab, fac in (("gel modulus x0.5", 0.5), ("nominal", 1.0), ("gel modulus x2 (or stiffer confinement)", 2.0)):
    JOBS.append(("liner_material", lab, "quick", dict(des=FINAL, size=60, _glob={"GEL_E": fac})))
for r_ in (0.33, 0.5, 0.67):
    JOBS.append(("kt_ratio", r_, "quick", dict(des=FINAL, size=60, _glob={"KT_RATIO": r_})))

log(len(JOBS), "sweep jobs")
import concurrent.futures as cfu, multiprocessing as mpr  # noqa: E402
done = 0
with cfu.ProcessPoolExecutor(4, mp_context=mpr.get_context("fork")) as pool:
    for sec, key, out, dt in pool.map(job, sorted(JOBS, key=lambda j: j[2] != "struct")):
        R.setdefault(sec, []).append(dict(key=key, **out))
        done += 1
        if done % 10 == 0 or sec == "arm_thickness":
            log(f"{done}/{len(JOBS)} {sec} {key} ({dt:.0f} s)")
for sec in R:
    R[sec].sort(key=lambda r: (str(type(r["key"])), r["key"]))

# arm thickness: stiffness and mass scale
for row in R["arm_thickness"]:
    s_ = row["key"]
    des_ = dict(FINAL, bar_t=FINAL["bar_t"] * s_, leg_t=FINAL["leg_t"] * s_, foot_t=FINAL["foot_t"] * s_,
                foot_t_mastoid=FINAL["foot_t_mastoid"] * s_)
    dx, dd = an.prepared(des_, D)
    row.update(bar_t=des_["bar_t"], leg_t=des_["leg_t"], foot_t=des_["foot_t"],
               k_arm_mastoid=1 / st.arm_compliance(dd, dx, "mastoid", [0, 0, 1]), arm_mass_rel=s_)

# ---------------------------------------------------------------- screw size (arm joint), from the Final envelope
base = structural(FINAL)
rows = []
for size in ("M2", "M2.5", "M3", "M4"):
    s_ = SCREW[size]
    pitch = max(7.0, s_["insert_od"] + 2.5) * 1e-3
    for T in (0.06, 0.10, 0.15, 0.25, 0.40):
        worst = None
        for src, jt in (("5 g envelope", base["ev"]["5 g accidental"]["joint"]), ("handling 10 N", base["jh"])):
            for a, rec in jt.items():
                v = rec["at_min_engage"]["forces"]
                j = st.serrated_joint(size, T, 2, F_radial=v["N"], F_tang=v["Vt"], M_tilt=v["Mt"], pitch_m=pitch,
                                      w_m=(FINAL["saddle_arm_w"] if a == "saddle" else FINAL["arm_w"]) * 1e-3,
                                      washer=FINAL.get("arm_washer"), F_pull=v["Vh"], T_twist=v["T"], M_inplane=v["Mh"],
                                      t_bear_m=FINAL["bar_t"] * 1e-3)
                key = min(j["SF_engage"], j["SF_pullout"], j["SF_spin"], j["SF_slot"])
                if worst is None or key < worst[0]:
                    worst = (key, f"{a} ({src})", j)
        rows.append(dict(size=size, T=T, min_SF=worst[0], governing=worst[1], **{k: worst[2][k] for k in (
            "Fi", "Fi_eff", "D_screw", "SF_engage", "SF_pullout", "SF_spin", "SF_tooth", "SF_slot", "head_bearing")},
            boss_wall=max(1.6, 0.5 * s_["insert_od"]), tab_w=max(12.0, s_["insert_od"] + 6.4),
            mass_pair_g={"M2": 0.47, "M2.5": 0.75, "M3": 1.28, "M4": 2.5}[size] * 2))
R["screw_size"] = rows
log("screw sweep done")

# ---------------------------------------------------------------- temperature
S23 = PETG["S_xy"].v; rows = []
for T in ("23C", "40C", "55C"):
    rows.append(dict(T=T, kT=st.kT(T), S=S23 * st.kT(T)))
R["temperature"] = rows

with open(os.path.join(RES, "sweeps.json"), "w") as fh:
    json.dump(js(R), fh, indent=1)
print("DONE", time.time() - T0)
