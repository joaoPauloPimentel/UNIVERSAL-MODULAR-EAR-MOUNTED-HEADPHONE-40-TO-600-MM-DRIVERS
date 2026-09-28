#!/usr/bin/env python3
"""
UMEH-2 master calculation. Re-run after changing any input:

    cd calc && python3 run_all.py [--quick]

Order: link wire derivation -> Design B / A evaluation -> Final design for
each driver size (CAD regenerated from the numbers, STL mass properties,
support, structure, joints, dynamics, acoustics, tolerances, cable) ->
max driver mass -> sweeps -> figures -> results/*.json. The report
(report/ENGINEERING_REPORT.md) is then written by make_report.py from
those results only.
"""
import json, math, os, sys, time, copy, pickle
import concurrent.futures as cfu, multiprocessing as mpr
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from umeh2 import (design as dz, configs as cf, analysis as an, support as sp, structure as st, linkspring as ls,
                   acoustics as ac, dynamics as dy, tolerance as tl, cable as cb, massprops as mpz, layout as lo,
                   extras as ex)
from umeh2.materials import (PETG, TPU, TISSUE, FRICTION, G, SCREW, GAMMA_M_PRINT, INSERT_PULLOUT, GAMMA_INSERT,
                             CABLE, ACOUSTIC_MAT, WIRE, BRASS, NUT_FACTOR_K, NUT_FACTOR_K_RANGE)

QUICK = "--quick" in sys.argv
# --smoke: code-path test only (tiny samples, writes results_smoke/); never for results
SMOKE = "--smoke" in sys.argv
# --resume: after a crash further down, re-use the checkpoints of the expensive support evaluations (same Final design,
# same sampling); only for re-running the later sections, never after a change to the support model
RESUME = "--resume" in sys.argv
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results_smoke" if SMOKE else "results"); FIG = os.path.join(ROOT, "report", "fig")
os.makedirs(RES, exist_ok=True); os.makedirs(FIG, exist_ok=True)
ND = 2 if SMOKE else (20 if QUICK else 40)
SE_KW = dict(n_grav=1, n_cable=1, n_acc=6) if SMOKE else {}
if SMOKE:       # code-path test: a tiny 1 g grid (the real one is support.GRID_1G)
    sp.GRID_1G = dict(tilt=(45.0,), az_step=180.0, cable_polar=(sp.CABLE_CONE,), cable_az_step=180.0)
T0 = time.time()


def log(*a):
    print(f"[{time.time() - T0:7.1f}s]", *a, flush=True)


from umeh2.util import js  # noqa: E402


def save(name, obj):
    with open(os.path.join(RES, name + ".json"), "w") as fh:
        json.dump(js(obj), fh, indent=1)


def ckpt(name, fn, extra=None):
    """Result of fn(), pickled under calc/_cache keyed by the Final design, the sampling and the source of the umeh2
    package (any model change invalidates it); with --resume an existing checkpoint is loaded instead of re-computing."""
    import hashlib, glob
    h = hashlib.sha1(json.dumps(js(dict(FINAL=FINAL, ND=ND, SE=SE_KW, SMOKE=SMOKE, extra=extra)), sort_keys=True).encode())
    for fp in sorted(glob.glob(os.path.join(os.path.dirname(an.__file__), "*.py"))):
        h.update(open(fp, "rb").read())
    key = h.hexdigest()[:12]
    p = os.path.join(an.CACHE, f"ckpt_{name}_{key}.pkl")
    if RESUME and os.path.exists(p):
        log(f"{name}: loaded from checkpoint {os.path.basename(p)}")
        with open(p, "rb") as fh:
            return pickle.load(fh)
    out = fn()
    with open(p, "wb") as fh:
        pickle.dump(out, fh)
    return out


CONTACT_KEYS = ("name", "Fn", "Ft", "mu_req", "p_mean", "p_peak", "slipping")


def summarize_support(ev):
    out = {}
    s = ev["static"]
    out["static"] = dict(ok=s["ok"])
    if s["ok"]:
        out["static"].update(q=s["q"], residual=s["residual"], link_force=s["link_force"],
                             contacts=[{k: x[k] for k in CONTACT_KEYS} for x in s["contacts"]])
    out["static_mu_demand"] = ev.get("static_mu_demand")
    sB = ev.get("static_B")
    if sB is not None:
        out["static_B"] = dict(ok=bool(sB.get("ok")), reason=sB.get("reason"))
        if sB.get("ok"):
            out["static_B"].update(q=sB["q"], contacts=[{k: x[k] for k in CONTACT_KEYS} for x in sB["contacts"]])
    for cat in sp.CATEGORIES:
        if cat not in ev:
            continue
        e = ev[cat]
        w = e["worst"]
        out[cat] = dict(n=e["n"], released=e["released"], unseated=e["unseated"], slip_fraction=e["slip_fraction"],
                        pad_slip_fraction=e.get("pad_slip_fraction"),
                        worst_tilt_deg=w["rot_xy"][0], worst_disp_mm=w["disp"][0], worst_util=w["util"][0],
                        worst_p_peak=w["p_peak"][0], p_peak=e["p_peak"], F_contact_max=e["F_contact_max"],
                        worst_tilt_case=w["rot_xy"][1], arm_stress=e["arm_stress"], joint=e.get("joint", {}),
                        released_by=e.get("released_by", {}), released_by_gravity=e.get("released_by_gravity", {}))
        for k in ("onset_lambda", "F_bound"):
            if k in e:
                out[cat][k] = e[k]
    return out


def sf_rows(secs_by_arm, temp="40C", sustained=False):
    """Safety factors per arm section (von Mises in-layer, interlayer shear) with the section forces."""
    S, Sil = st.strength("x", temp=temp, sustained=sustained)
    rows = []
    for arm, secs in secs_by_arm.items():
        for sec, v in secs.items():
            rows.append(dict(arm=arm, section=sec, sigma=v["sigma"], tau=v["tau"], vm=v["vm"], tau_il=v["tau_il_max"],
                             SF_vm=S / max(v["vm"], 1.0), SF_il=Sil / max(v["tau_il_max"], 1.0),
                             N=v["N"], T=v["T"], Mt=v["Mt"], Mh=v["Mh"], Vt=v["Vt"], Vh=v["Vh"],
                             contact=v.get("contact"), dir=v.get("dir"), case=v.get("case")))
    return rows


def arm_sf_table(ev, cat, temp="40C", sustained=False):
    return sf_rows(ev[cat]["arm_stress"], temp, sustained)


# =====================================================================================
# 0. Final layout (from the layout optimisation, calc/final_layout.json)
# =====================================================================================
FINAL = cf.final_design()
log("Final layout", {k: FINAL[k] for k in lo.BOUNDS})

# =====================================================================================
# 1. Link wire derivation (Design B preload and Final preload)
# =====================================================================================
res_link = {}
for nm, des in (("B", cf.DESIGN_B), ("Final", FINAL)):
    des, d = an.prepared(des, 50)
    path = sp.link_path(d, des)
    grid, best, chosen, margin = ls.size_wire(des["link_preload"], path=path, ns=ls.N_COILS)
    res_link[nm] = dict(P=des["link_preload"], path=path, chosen=chosen,
                        sweep=[dict(d=r[0]["d_mm"], best=b) for r, b in zip(grid, best)],
                        grid=[[dict(d=x["d_mm"], n=x["n_coil"], k=x["k_side"], SFy=x["SF_yield"], SFf=x["SF_fatigue"],
                                    Pr=x["P_ratio"], ok=x["ok"]) for x in row] for row in grid])
# The Final wire is sized on EVERY module at its tuned eye (analysis.size_link_on_modules; the 50 mm-only choice is
# kept for reference).
cands, cm = an.size_link_on_modules(FINAL)
res_link["Final"]["chosen_50_only"] = res_link["Final"]["chosen"]
res_link["Final"]["module_candidates"] = cands
if cm:
    res_link["Final"]["chosen"] = cm["modules"][50]
    res_link["Final"]["chosen_modules"] = cm
else:
    log("WARNING: no stock wire meets the link criteria on every module; keeping the 50 mm-only choice")
FINAL["wire_d"] = res_link["Final"]["chosen"]["d_mm"]; FINAL["link_coils"] = res_link["Final"]["chosen"]["n_coil"]
save("link", res_link)
log("link wire Final", FINAL["wire_d"], "mm,", FINAL["link_coils"], "coils")

# =====================================================================================
# 2./3. Design B (and A) at 50 mm and the Final design at every driver size, one process per evaluation.
# Mass properties first, in this process: they regenerate the CAD (one shared generated_params.scad).
# =====================================================================================
mpB = an.mass_properties(cf.DESIGN_B, 50, "B")
MP_F = {D: an.mass_properties(FINAL, D, "F") for D in dz.SIZES}
log("mass properties done: " + ", ".join(f"{D} mm {MP_F[D]['M'] * 1e3:.1f} g" for D in dz.SIZES))


# =====================================================================================
# 3c. Dense check of the 1 g grid on every module (analysis.dense_1g_chunk over support.DENSE_1G, a finer
#     nested version of support.GRID_1G): does a finer search of head tilt x head motion x cable pull find a
#     combination that fails where the grid found none (or a worse one)? Then the local refinement around the dense
#     check's most critical cases (analysis.refine_1g_chunk: its cells searched on a 4x finer local grid), which
#     measures how well the dense grid resolves the worst case. Run first (its result is the one most likely to send
#     the design back to the eye tune), before the long support runs.
# =====================================================================================
def sec3c():
    jobs = []
    for D in dz.SIZES:
        mp = MP_F[D]
        jobs += an.dense_1g_jobs(FINAL, D, (mp["M"], mp["com"], mp["I"]))
    if SMOKE:
        jobs = [j for j in jobs if j[1] == 50][-1:]
    parts = {D: [] for D in dz.SIZES}
    with cfu.ProcessPoolExecutor(4, mp_context=mpr.get_context("fork")) as pool:
        for a, r in zip(jobs, pool.map(an.dense_1g_chunk, jobs, chunksize=1)):
            parts[a[1]].append(r)
        dense = {D: an.dense_1g_merge(parts[D]) for D in dz.SIZES if parts[D]}
        rjobs, seeds = [], {}
        for D, r in dense.items():
            mp = MP_F[D]
            j_, seeds[D] = an.refine_1g_jobs(FINAL, D, (mp["M"], mp["com"], mp["I"]), r)
            rjobs += j_
        if SMOKE:
            rjobs = rjobs[:1]
        rparts = {D: [] for D in dense}
        for a, r in zip(rjobs, pool.map(an.refine_1g_chunk, rjobs, chunksize=1)):
            rparts[a[1]].append(r)
    return {D: dict(dense=dense[D], refine=an.refine_1g_merge(rparts[D], seeds[D]) if rparts[D] else None) for D in dense}


def _dense_save(r):
    """Saved form of a merged dense check / refinement: counts, worst cases, the summary over ALL failures, and the
    first 300 failures (the list is in grid order)."""
    if r is None:
        return None
    out = {k: v for k, v in r.items() if k not in ("fails", "seeds", "per_case")}
    out.update(n_fails=len(r["fails"]), fails_summary=an.fails_summary(r["fails"]), fails=r["fails"][:300])
    if "seeds" in r:
        out["seeds"] = r["seeds"]
    return out


res_dense = ckpt("dense_1g", sec3c)
log("dense 1 g check: " + ", ".join(f"{D} mm {rr['dense']['n']} cases, released {rr['dense']['released']}, tripod lost "
                                     f"{rr['dense']['unseated']}, tilt over {rr['dense']['tilt_over']}, worst tilt "
                                     f"{rr['dense']['worst_tilt'][0]:.2f} deg, min seat {rr['dense']['min_seat'][0]:.3f} N"
                                     + (f"; refinement {rr['refine']['n']} cases, fails {len(rr['refine']['fails'])}, worst tilt "
                                        f"{rr['refine']['worst_tilt'][0]:.2f} deg, min seat {rr['refine']['min_seat'][0]:.3f} N"
                                        if rr["refine"] else "") for D, rr in res_dense.items()))



def job_B():
    mptB = (mpB["M"], mpB["com"], mpB["I"])
    evB, _ = an.support_eval(cf.DESIGN_B, 50, mptB, n_dir=ND, struct=True, **SE_KW)
    return dict(mass=mpB["M"], com=mpB["com"], I=mpB["I"], parts=[(r["part"], r["m"], r["c"], r["src"]) for r in mpB["rows"]],
                support=summarize_support(evB), criteria=an.criteria(evB))


def job_A():
    # Design A: B geometry carrying A's mass and COM height
    comA = mpB["com"].copy(); comA[2] = cf.DESIGN_A_MASS["com_z"]
    IA = mpB["I"] * cf.DESIGN_A_MASS["M"] / mpB["M"]
    evA, _ = an.support_eval(cf.DESIGN_B, 50, (cf.DESIGN_A_MASS["M"], comA, IA), n_dir=ND, struct=False,
                             cats=["1 g normal", "2 g dynamic"], **SE_KW)
    return dict(mass=cf.DESIGN_A_MASS["M"], com=comA, support=summarize_support(evA), criteria=an.criteria(evA))


def job_final(D):
    mp = MP_F[D]
    mpt = (mp["M"], mp["com"], mp["I"])
    ev, (des, d, C, link, L) = an.support_eval(FINAL, D, mpt, n_dir=ND, struct=True, **SE_KW)
    r = dict(D=D, mass=mp["M"], com=mp["com"], I=mp["I"],
             parts=[dict(part=x["part"], m=x["m"], c=x["c"], src=x["src"], mat=x.get("mat"), f=x.get("f")) for x in mp["rows"]],
             support=summarize_support(ev), criteria=dict(an.criteria(ev), **{
                 "link wire on this module (SF yield and fatigue >= 1.5, preload ratio <= 2)": bool(L["ok"])}),
             contacts=[dict(name=c["name"], r=c["r"], n=c["n"], k=c["k"], kt=c["kt"], area=c["area"], mu=c["mu"], mu_key=c["mu_key"]) for c in C],
             link=dict(eye=link[0], P=link[1], k=link[2], design=L),
             arm_sf={cat: arm_sf_table(ev, cat, sustained=(cat == "1 g normal")) for cat in sp.CATEGORIES},
             handling=dict(F=ev["handling"]["F"], n_dir=ev["handling"].get("n_dir"), sf=sf_rows(ev["handling"]["arm_bound"]),
                          joint=ev["handling"]["joint"]),
             bound_5g=dict(F=ev["5 g accidental"]["F_bound"], sf=sf_rows(ev["5 g accidental"]["arm_bound"])),
             derived={k: d[k] for k in ("spig_d", "bore_d", "ring_od", "tab_r", "tab_t", "cup_h", "cup_ri", "cup_ro", "baffle_h",
                                        "aperture_d", "z_cuptop", "groove_h", "cup_screw_r", "link_r", "bar_r0", "bar_r1", "leg_r",
                                        "tab_ins_pitch", "felt_hole_d", "felt_A", "eye_boss_d")},
             eye=dict(link_x=des["link_x"], link_y=des["link_y"], r_max=d["cup_ro"] - d["eye_boss_d"] / 2 - 0.5))
    # arm compliance at each contact (in series with it in the support model) against the contact's own compliance,
    # in the contact frame (normal, t1, t2)
    rows_c = []
    for c in C:
        nd = c.get("node")
        if nd is None:
            continue
        Cn = np.linalg.inv(nd["K"]) if nd["m"] == 3 else (lambda Lm: Lm @ np.linalg.inv(nd["K"]) @ Lm.T)(st.point_map(c["r"], nd["r"]))
        R_ = np.vstack([c["n"], c["t"][0], c["t"][1]])
        Cl = R_ @ Cn @ R_.T
        rows_c.append(dict(contact=c["name"], arm=nd["id"], c_arm=[Cl[0, 0], Cl[1, 1], Cl[2, 2]], c_contact=[1 / c["k"], 1 / c["kt"], 1 / c["kt"]]))
    r["arm_compliance"] = rows_c
    # where each arm's compliance sits under its own contact forces at rest (static, donning A): shares of the
    # complementary energy by segment and mode (structure.arm_energy_split)
    if ev["static"]["ok"]:
        r["arm_energy_split"] = {}
        for a_ in ("temporal", "mastoid", "post", "saddle"):
            loads_ = st.arm_loads_from_contacts(ev["static"]["contacts"], C, a_)
            if loads_:
                sh_, U_ = st.arm_energy_split(d, des, a_, loads_)
                r["arm_energy_split"][a_] = dict(U=U_, shares=dict(list(sh_.items())[:4]))
    # arm fatigue: walking/running, structure.N_FATIGUE cycles [A]. Each section is taken to cycle from zero to its largest von Mises
    # stress over the held 2 g combinations (sigma_a = sigma_m = sigma_max/2: conservative, the steady 1 g part is not
    # split off; Kt kept as the fatigue notch factor); Goodman on the normalised S-N curve at N_FATIGUE cycles, T_SERVICE.
    fat = []
    for a_, secs in ev["2 g dynamic"]["arm_stress"].items():
        for sec, v in secs.items():
            fat.append(dict(arm=a_, section=sec, vm_2g=v["vm"], S_f=st.fatigue_strength(st.N_FATIGUE),
                            SF=st.goodman_sf(v["vm"] / 2, v["vm"] / 2, st.N_FATIGUE)))
    r["fatigue"] = sorted(fat, key=lambda x: x["SF"])[:8]
    # rigid-body modes
    f, V, names = dy.rigid_modes(mpt, C, link)
    r["modes"] = dict(f=f, names=names)
    return r


def sec23():
    with cfu.ProcessPoolExecutor(4, mp_context=mpr.get_context("fork")) as pool:
        futs = {D: pool.submit(job_final, D) for D in sorted(dz.SIZES, reverse=True)}
        futB = pool.submit(job_B); futA = pool.submit(job_A)
        res_ = {}
        for D in dz.SIZES:
            res_[D] = futs[D].result()
            log(f"Final D={D}: mass {res_[D]['mass'] * 1e3:.1f} g, criteria {res_[D]['criteria']}")
        return res_, futB.result(), futA.result()


res_final, resB, resA = ckpt("final_B_A", sec23)
save("design_B", resB); save("design_A", resA)

# =====================================================================================
# 3b. The eye tune's own objective at each tuned eye, re-scored with the Final's inputs (the link wire sized on all
#     modules above at the tuned eyes, P(D) from the tuned 50 mm eye, CAD mass properties with the eye boss where it
#     is). The tune sized the wire at the layout's reference eye and used the boss at the reference position; this
#     shows whether that mattered.
# =====================================================================================
import tune_eye as te  # noqa: E402
import legs_liner as ll_mod  # noqa: E402
if SMOKE:
    te.N_DIR2 = 1


def eye_check_job(D):
    P = FINAL["link_preload"]
    te.BASE = dict(FINAL); te.LEVEL[P] = dict(FINAL)
    te.MPT[(P, D)] = (MP_F[D]["M"], MP_F[D]["com"], MP_F[D]["I"])
    e = FINAL["per_size"][str(D)]
    r = te.evaluate((D, e["link_x"], e["link_y"], True, P, False))      # full evaluation (no early stop)
    return {k: r.get(k) for k in ("D", "x", "y", "prim", "margins", "slip2", "padslip1", "score", "score1", "tilt", "seat_N")}


def sec3b():
    with cfu.ProcessPoolExecutor(4, mp_context=mpr.get_context("fork")) as pool:
        return {D: r for D, r in zip(dz.SIZES, pool.map(eye_check_job, dz.SIZES))}


res_eyechk = ckpt("eye_check", sec3b)
save("eye_check", res_eyechk)
log("eye check: " + ", ".join(f"{D} mm prim {res_eyechk[D]['prim']:.3f} slip2 {res_eyechk[D].get('slip2')}" for D in dz.SIZES))
log("Design B", resB["criteria"]); log("Design A", resA["criteria"])

# 3c (computed above, before the long support runs): results and criteria
save("dense_1g", dict(grid=sp.DENSE_1G, grid_1g=sp.GRID_1G, refine_n=an.REFINE_N, k_crit=an.K_CRIT,
                      sizes={D: _dense_save(r["dense"]) for D, r in res_dense.items()},
                      refine={D: _dense_save(r["refine"]) for D, r in res_dense.items()}))
for D, rr in res_dense.items():
    r, rf = rr["dense"], rr["refine"]
    ok_ = bool(r["ok"]) and (rf is None or bool(rf["ok"]))
    res_final[D]["criteria"][f"1 g dense check and its local refinement: no release, tripod kept, tilt <= {lo.ROT_NORMAL:g} deg"] = ok_
    res_final[D]["dense_1g"] = dict({k: r[k] for k in ("n", "released", "released_numerical", "unseated", "tilt_over", "worst_tilt",
                                                       "min_seat", "ok")},
                                    refine=None if rf is None else {k: rf[k] for k in ("n", "released", "released_numerical", "unseated",
                                                                                        "tilt_over", "worst_tilt", "min_seat", "ok")})
save("final_sizes", res_final)

# =====================================================================================
# 3d. The Final as it was before iteration change 19 (calc/final_layout_before_grid.json: eyes tuned on a quasi-uniform
#     1 g sample at the layout preload, with the link wire of that run), solved on the 1 g worst-case grid
#     (support.GRID_1G): the evidence for change 19.
# =====================================================================================
PRE = cf.final_design(os.path.join(ROOT, "calc", "final_layout_before_grid.json"))
MP_PRE = {D: an.mass_properties(PRE, D, "F") for D in ((50,) if SMOKE else dz.SIZES)}


def sec3d():
    jobs = []
    for D, mp in MP_PRE.items():
        jobs += an.dense_1g_jobs(PRE, D, (mp["M"], mp["com"], mp["I"]), grid=sp.GRID_1G)
    if SMOKE:
        jobs = jobs[-1:]
    parts = {D: [] for D in MP_PRE}
    with cfu.ProcessPoolExecutor(4, mp_context=mpr.get_context("fork")) as pool:
        for a, r in zip(jobs, pool.map(an.dense_1g_chunk, jobs, chunksize=1)):
            parts[a[1]].append(r)
    return {D: an.dense_1g_merge(parts[D]) for D in MP_PRE if parts[D]}


res_pre = ckpt("grid_1g_before_grid", sec3d, extra=dict(PRE=PRE, grid=sp.GRID_1G))
_pre_lay = json.load(open(os.path.join(ROOT, "calc", "final_layout_before_grid.json")))
save("grid_1g_before_grid", dict(
    grid=sp.GRID_1G,
    design=dict(link_preload=PRE["link_preload"], wire_d=PRE["wire_d"], link_coils=PRE["link_coils"], per_size=PRE["per_size"],
                tune_set_1g=_pre_lay.get("_tune_set_1g")),
    mass={D: mp["M"] for D, mp in MP_PRE.items()},
    sizes={D: _dense_save(r) for D, r in res_pre.items()}))
log("1 g worst-case grid, Final before change 19: " + ", ".join(
    f"{D} mm released {r['released']}, tripod lost {r['unseated']}, tilt over {r['tilt_over']}, worst tilt {r['worst_tilt'][0]:.2f} deg"
    for D, r in res_pre.items()))

# =====================================================================================
# 4. Joints, inserts, fits, link eye, twist lock (Final, 50 and 60 mm = heaviest)
# =====================================================================================
res_joint = {}
for D in (50, 60):
    r = res_final[D]
    des, d = an.prepared(FINAL, D)
    rows = []
    srcs = [(cat, r["support"][cat]["joint"]) for cat in sp.CATEGORIES] + [("handling 10 N", r["handling"]["joint"])]
    for cat, jt in srcs:
        for arm, rec in jt.items():
            j = rec["at_min_engage"]; v = j["forces"]
            # the same section forces on a plain (friction-only) joint, as in Design A/B
            jB = st.screw_joint(des["arm_screw"], des["arm_torque"], 2, d["tab_ins_pitch"] * 1e-3, F_shear=abs(v["N"]),
                                M_joint_t=abs(v["Mt"]), M_joint_r=abs(v["Mh"]), F_axial=max(v["Vh"], 0.0))
            rows.append(dict(cat=cat, arm=arm, min={k: rec[k] for k in an.JOINT_KEYS}, serrated=j, friction_only=jB))
    res_joint[D] = rows
# inserts and bosses
INSERT_WALL_COUNTER = 1.0    # mm, a wall the rule excludes (counter-example for the report)
res_joint["inserts"] = [dict(st.insert_boss(s, w), role=r) for s, w, r in
                        (("M3", dz.insert_wall("M3"), "design"), ("M2.5", dz.insert_wall("M2.5"), "design"),
                         ("M2.5", INSERT_WALL_COUNTER, "counter-example"), ("M3", INSERT_WALL_COUNTER, "counter-example"))]
# rear felt: PSA rim bond (replaces the press-fit retainer ring of the earlier iteration)
d50 = an.prepared(FINAL, 50)[1]
res_joint["felt_bond"] = {D: ex.felt_bond(*reversed(an.prepared(FINAL, D))) for D in dz.SIZES}
# record of the rejected press-fit PETG retainer ring (radial interference 0.15 mm, wall 2 mm; +0.3 mm diametral at
# the XY tolerance extreme): whole interference as hoop strain, sustained strength (structure.press_fit)
res_joint["felt_retainer_rejected"] = {D: dict(nominal=st.press_fit(2 * an.prepared(FINAL, D)[1]["cup_ri"], 0.30, 2.0),
                                               upper_tolerance=st.press_fit(2 * an.prepared(FINAL, D)[1]["cup_ri"], 0.60, 2.0))
                                       for D in dz.SIZES}
# link eye on the cup: wire eye around a brass sleeve (inner radius r_i >= 1.5 d) clamped by an M2.5 screw into
# a heat-set insert in the cup-end boss. Wire on sleeve: Hertz line contact (wire section on the straight sleeve
# generatrix). Line load: a loop carrying the force as wire tension T = P presses on the pin with the uniform
# rope load q = T / r_i; a pin-bearing (cosine) distribution would give 2P/(pi r_i) = 0.64 of it. The larger
# (rope) value is used [C]. Insert: lateral load P at the sleeve mid-height e above the boss face, the insert
# a rigid short pile in an elastic (Winkler) bed: p(y) = a + b y from force and moment balance, peak at the face
# p = P / (d_ins L) (4 + 6 e / L) [C].
P = FINAL["link_preload"]
D_eye = max(dz.SIZES, key=lambda D: res_final[D]["link"]["design"]["P_don"])      # module with the largest donning load
Ldes = res_final[D_eye]["link"]["design"]
r_i = ls.eye_ri(FINAL["wire_d"])
q0 = Ldes["P_don"] / r_i
hz = ex.line_hertz(q0 * 1e-3, 1e-3, FINAL["wire_d"] / 2e3, 1e9, WIRE["E"].v, WIRE["nu"].v, BRASS["E"].v, BRASS["nu"].v)
e_arm = dz.EYE_SLEEVE_L / 2 * 1e-3; si = SCREW["M2.5"]           # lateral load at the sleeve mid-height
p_ins = Ldes["P_don"] / (si["insert_od"] * 1e-3 * si["insert_L"] * 1e-3) * (4 + 6 * e_arm / (si["insert_L"] * 1e-3))
res_joint["link_eye"] = dict(P=P, D=D_eye, P_don=Ldes["P_don"], e=e_arm, boss_d=d50["eye_boss_d"], r_i=r_i, q0=q0, hertz=hz,
                             tau_max_brass=ex.TAU_LINE * hz["p0"], SF_brass=0.5 * BRASS["Sy"].v / (ex.TAU_LINE * hz["p0"]),   # Tresca
                             p_insert=p_ins, SF_insert=PETG["S_bear"].v * st.kT() * st.K_SUSTAINED / p_ins)
# twist lock (Final: lugs on the rigid floor + foam anti-rattle strips; Design B: solid TPU gasket for comparison)
MOD_PARTS = ("baffle", "gasket_driver", "cup", "driver")


def module_mass(r):
    return sum(p["m"] for p in r["parts"] if p["part"] in MOD_PARTS or
               p["part"].startswith(("cup ", "felt disc", "link eye", "occipital link")))


tw_in = {}
for D in dz.SIZES:
    des, d = an.prepared(FINAL, D)
    ch = tl.stackups(d, des, D)["UMI foam compression (anti-rattle strip)"][0]
    tw_in[D] = (d, des, module_mass(res_final[D]), res_final[D]["link"]["P"],
                (ch["mc_p0135"] / des["foam_t"], ch["mc_p99865"] / des["foam_t"]))
win = {D: st.twistlock(*v) for D, v in tw_in.items()}
lo_req = max(w["cfd25_lo"] for w in win.values()); hi_all = min(w["cfd25_hi"] for w in win.values())
foam_spec = dict(cfd25_lo=lo_req, cfd25_hi=hi_all, feasible=lo_req < hi_all,
                 cfd25_spec=math.sqrt(lo_req * hi_all) if lo_req < hi_all else lo_req,
                 governing_lo=max(win, key=lambda D: win[D]["cfd25_lo"]), governing_hi=min(win, key=lambda D: win[D]["cfd25_hi"]))
res_joint["foam_spec"] = foam_spec
for D, v in tw_in.items():
    res_joint[f"twistlock_{D}"] = dict(m_module=v[2], P_link=v[3], **st.twistlock(*v, cfd25=foam_spec["cfd25_spec"]))
desB, dB = an.prepared(cf.DESIGN_B, 50)
chB = tl.stackups(dB, desB, 50)["UMI axial gasket squeeze"][0]
res_joint["designB_gasket"] = dict(chain=dict(nom=chB["nom"], mc_lo=chB["mc_p0135"], mc_hi=chB["mc_p99865"]),
                                   nominal=st.solid_gasket_lock(dB, desB, max(chB["nom"], 0.0)),
                                   mc_hi=st.solid_gasket_lock(dB, desB, chB["mc_p99865"]),
                                   design_value=st.solid_gasket_lock(dB, desB, desB["gasket_squeeze"]))
save("joints", res_joint)
log("joints done")

# =====================================================================================
# 5. Cable
# =====================================================================================
res_cable = dict(B=cb.design_cable_loads(cf.DESIGN_B), Final=cb.design_cable_loads(FINAL),
                 interf_sweep=cb.size_clip_interference(FINAL)[0],
                 interf_values=[0.0, FINAL["clip_interf"], FINAL["clip_interf"] + 2 * tl.TOL["xy"]],   # bore at -XY tolerance (diametral)
                 interf_range=[cb.clip_grip(FINAL["cable_od"], x, FINAL["clip_wall"], FINAL["clip_len"])["F_clip"]
                               for x in (0.0, FINAL["clip_interf"], FINAL["clip_interf"] + 2 * tl.TOL["xy"])])

# 5b. worn-cradle cable limits (support model): tug limit per pull direction, plug insertion / removal at the
# socket; anchor screws and clip post at the fuse loads
for D in (40, 50, 60):
    r = res_final[D]
    des, d, C, link, L = an.support_model(FINAL, D)
    model = sp.Model(C, link)
    W_st = sp.static_wrench((r["mass"], r["com"], r["I"]), d, des)
    model.set_base(W_st)
    res_cable.setdefault("tug_limits", {})[D] = ex.tug_limits(model, d, des, W_st, n_bis=2 if SMOKE else 12)
    res_cable.setdefault("plug", {})[D] = ex.plug_at_socket(model, d, des, W_st)
    log(f"cable tug limits D={D}: min {res_cable['tug_limits'][D]['sphere_min']:.2f} N")
des50, d50 = an.prepared(FINAL, 50)
cl = res_cable["Final"]
F_an = {"plug nominal (fuse)": cl["fuse"], f"plug upper ({cb.RETENTION_RANGE[1]:g} N)": cl["fuse_upper"],
        "clip + plug in series (upper)": cl["clip"]["F_clip"] + cl["fuse_upper"], f"snag {an.F_SNAG:g} N": an.F_SNAG}
res_cable["anchor"] = {k: ex.anchor_screws(d50, des50, v) for k, v in F_an.items()}
res_cable["clip_post"] = {k: ex.clip_post(d50, des50, v) for k, v in F_an.items()}
res_cable["tug_F_hi"] = ex.TUG_F_HI
save("cable", res_cable)
log("cable done")

# =====================================================================================
# 5c. Weight optimisation (CAD mass at 50 mm; each option alone against the pre-optimisation baseline,
#     with the check it moves)
# =====================================================================================
BEFORE = dict(arm_screw="M3", arm_torque=0.15, cup_wall=1.6, leg_t=5.0, foot_t=5.0)
base_des = dict(FINAL, **BEFORE)


def _v(x):
    return f"{x:g}" if isinstance(x, (int, float)) else str(x)


def wlabel(code, what, keys, o, unit=" mm"):
    """Option label generated from the values (baseline -> option, the arm-screw insert pitch when the option moves it
    without naming it, and the tightening torque when it changes); the decision is computed in the report from the
    checks and from whether the Final carries the change."""
    T_ = o.get("arm_torque") or o.get("anchor_torque")
    p0 = an.prepared(base_des, 50)[1]["tab_ins_pitch"]; p1 = an.prepared(dict(base_des, **o), 50)[1]["tab_ins_pitch"]
    pt = f" (insert pitch {p0:g} -> {p1:g} mm)" if "arm_screw_pitch" not in keys and abs(p1 - p0) > 1e-9 else ""
    return (f"{code} {what} {'/'.join(_v(base_des[k_]) for k_ in keys)} -> {'/'.join(_v(o[k_]) for k_ in keys)}{unit}{pt}"
            + (f" at {T_:.2f} N·m" if T_ else ""))


OPTS = {}
for code, what, keys, o, unit in (
        ("W1", "arm screws", ("arm_screw",), dict(arm_screw="M2.5", arm_torque=0.10, arm_screw_pitch=None), ""),
        ("W1b", "anchor screws", ("anchor_screw",), dict(anchor_screw="M2.5", anchor_torque=0.10), ""),
        ("W3", "cup wall", ("cup_wall",), dict(cup_wall=1.2), " mm"),
        ("W4a", "feet", ("foot_t",), dict(foot_t=4.5), " mm"),
        ("W4b", "legs", ("leg_t",), dict(leg_t=4.5), " mm"),
        ("W4c", "legs", ("leg_t",), dict(leg_t=6.5), " mm"),
        ("W4e", "legs", ("leg_t",), dict(leg_t=5.5), " mm"),
        ("W4d", "legs/feet", ("leg_t", "foot_t"), dict(leg_t=4.0, foot_t=4.0), " mm"),
        ("W5", "arm-screw insert pitch", ("arm_screw_pitch",), dict(arm_screw_pitch=10.0, arm_torque=0.10), " mm")):
    OPTS[wlabel(code, what, keys, o, unit)] = o
S40, Sil40 = st.strength("short", temp="40C")


def handling_min_sf(des_, D=50, joints=None):
    desx, dx, Cx, linkx, Lx = an.support_model(des_, D)
    arms_ = [a for a in ("saddle", "temporal", "mastoid", "post") if a != "post" or desx.get("post_a") is not None]
    B = an.arm_bound(desx, dx, Cx, an.F_HANDLING, arms_, n_dir=146, joints=joints)
    return min((min(S40 / v["vm"], Sil40 / max(v["tau_il_max"], 1)), a, sec) for a, secs in B.items() for sec, v in secs.items())


def handling_joints(des_, D=50):
    """Arm-joint safety factors under the 10 N handling load (tightening scatter included, structure.serrated_joint)."""
    jh = {}
    handling_min_sf(des_, D, joints=jh)
    return {a: {k: rec[k] for k in an.JOINT_KEYS} for a, rec in jh.items()}


def root_pressure_A(des_, D=60, mpt=None):
    """Largest auricle-root mean pressure at rest (donning A, head upright, 1 g), flexible arms."""
    if mpt is None:
        mp_ = an.mass_properties(des_, D, "W")
        mpt = (mp_["M"], mp_["com"], mp_["I"])
    desx, dx, Cx, linkx, Lx = an.support_model(des_, D)
    m_ = sp.Model(Cx, linkx)
    W_ = sp.static_wrench(mpt, dx, desx)
    if not m_.set_base(W_):
        return None
    r_ = m_.solve(W_)
    return max(x["p_mean"] for x in r_["contacts"] if x["name"].startswith("S root")) if r_["ok"] else None


res_w = {}
mb = an.mass_properties(base_des, 50, "W")
res_w["baseline"] = dict(mass=mb["M"], change=BEFORE, handling=handling_min_sf(base_des), root_p_60=root_pressure_A(base_des))
for k, o in OPTS.items():
    des_ = dict(base_des, **o)
    m_ = an.mass_properties(des_, 50, "W")
    row = dict(change={kk: vv for kk, vv in o.items() if vv is not None}, mass=m_["M"], delta=m_["M"] - mb["M"])
    if "leg_t" in o or "foot_t" in o:
        row["handling"] = handling_min_sf(des_)
    if "leg_t" in o:
        row["root_p_60"] = root_pressure_A(des_)
    if o.get("arm_screw_pitch") is not None:
        row["joints"] = handling_joints(des_)
    elif "arm_screw" in o or "anchor_screw" in o:
        size = o.get("arm_screw") or o.get("anchor_screw"); T_ = o.get("arm_torque") or o.get("anchor_torque")
        d_s = SCREW[size]["d"] * 1e-3
        row["Fi"] = T_ / (NUT_FACTOR_K.v * d_s)
        row["Fi_range"] = (T_ / (NUT_FACTOR_K_RANGE[1].v * d_s), T_ / (NUT_FACTOR_K_RANGE[0].v * d_s))
        row["pullout_SF_preload"] = INSERT_PULLOUT[size].v / GAMMA_INSERT.v / row["Fi_range"][1]
        dd, dv = an.prepared(des_, 50)
        if "anchor_screw" in o:
            row["anchor"] = {kk: ex.anchor_screws(dv, dd, vv) for kk, vv in F_an.items()}
        else:
            row["joints"] = handling_joints(des_)
    if "cup_wall" in o:
        dd, dv = an.prepared(des_, 50)
        row["cup_ro"] = dv["cup_ro"]; row["eye_r_max"] = dv["cup_ro"] - dv["eye_boss_d"] / 2 - 0.5
        row["perimeters"] = o["cup_wall"] * 1e-3 / mpz.LINE_W
    res_w[k] = row
    log(f"weight option {k}: {row['delta'] * 1e3:+.2f} g")
mf = MP_F[50]
res_w["final"] = dict(mass=mf["M"], delta=mf["M"] - mb["M"], handling=handling_min_sf(FINAL), joints=handling_joints(FINAL),
                      root_p_60=root_pressure_A(FINAL, 60, (MP_F[60]["M"], MP_F[60]["com"], MP_F[60]["I"])))
# M3 arm joint: insert pitch x tightening torque under the 10 N handling load (justifies pitch and torque)
res_w["pitch_torque_scan"] = [dict(pitch=an.prepared(dict(FINAL, arm_screw_pitch=p_), 50)[1]["tab_ins_pitch"], torque=T_,
                                   **{k_: min(j[k_] for j in handling_joints(dict(FINAL, arm_screw_pitch=p_, arm_torque=T_)).values())
                                      for k_ in ("SF_engage", "SF_pullout")})
                              for p_ in (None, 8.0, 9.0, 10.0, 11.0) for T_ in (0.08, 0.10, 0.12, 0.15)]
log("pitch/torque scan done")
# bar thickness at the XY print tolerance and one dimension step thinner, handling load (justifies bar_t)
BAR_TOL = tl.TOL["xy"]   # mm, XY print tolerance of the bar section (the tolerance.py stack-up input)
BAR_STEP = 0.1           # mm, dimension step of the arm sections (bar, legs, feet)
res_w["bar_t_print_tol"] = BAR_TOL; res_w["bar_t_step"] = BAR_STEP
res_w["bar_t_tolerance"] = {f"{t:.2f}": handling_min_sf(dict(FINAL, bar_t=t))
                            for t in (FINAL["bar_t"], FINAL["bar_t"] - BAR_TOL, FINAL["bar_t"] - BAR_STEP, FINAL["bar_t"] - BAR_STEP - BAR_TOL)}
# ring infill: the ring is perimeter-dominated (shell fraction from its own mesh)
rr = next(x for x in mf["rows"] if x["part"] == "ring")
mat, per, tb, infill = mpz.PRINT["ring"]
shell = min(1.0, rr["area"] * per * mpz.LINE_W / rr["V"]) if rr["V"] > 0 else 1.0
INFILL_W2 = 0.20
res_w[f"W2 ring infill {100 * infill:g} -> {100 * INFILL_W2:g} %"] = dict(shell_fraction=shell, change=dict(ring_infill=INFILL_W2),
                                                                        delta=PETG["rho"].v * (1 - shell) * (INFILL_W2 - infill) * rr["V"])
save("weight", res_w)
log("weight table done")

# =====================================================================================
# 5b. What sets the auricle-root load (donning A, head upright, 1 g). Every variant keeps the Final CAD mass
# properties of its size (the variants move the side mass by < 2 %), so the table isolates the stiffness effect.
# =====================================================================================
def root_state(des_, D, mpt):
    desx, dx, Cx, linkx, Lx = an.support_model(des_, D)
    m_ = sp.Model(Cx, linkx)
    W_ = sp.static_wrench(mpt, dx, desx)
    if not m_.set_base(W_):
        return dict(ok=False)
    r_ = m_.solve(W_)
    if not r_["ok"]:
        return dict(ok=False)
    dem = sp.static_friction_demand(Cx, linkx, W_) or {}
    root = [x for x in r_["contacts"] if x["name"].startswith("S root")]
    skin = [x for x in r_["contacts"] if not x["name"].startswith("S root")]
    nrm = {c["name"]: np.asarray(c["n"]) for c in Cx}
    kmax = max(dem, key=dem.get) if dem else None
    return dict(ok=True, root_p=max(x["p_mean"] for x in root), root_F=sum(x["Fn"] for x in root),
                root_Fy=float(sum(x["Fn"] * nrm[x["name"]][1] for x in root)), weight=float(mpt[0] * G),
                skin_p=max(x["p_mean"] for x in skin), min_Fn=min(x["Fn"] for x in r_["contacts"]),
                mu_pad=kmax, mu_demand=dem.get(kmax) if kmax else None)


NO_LINER = dict(FINAL, saddle_liner_t=0.0)
LT_ = FINAL["saddle_liner_t"]
LSTEP = min(b_ - a_ for a_, b_ in zip(sorted(ll_mod.LINERS), sorted(ll_mod.LINERS)[1:]))   # casting step of the liner grid
ROOT_VARIANTS = [
    (f"Final (liner {LT_:g} mm)", FINAL),
    ("no liner (Final otherwise)", NO_LINER),
    (f"liner {LT_ - LSTEP:g} mm", dict(FINAL, saddle_liner_t=LT_ - LSTEP)),
    (f"liner {LT_ + LSTEP:g} mm", dict(FINAL, saddle_liner_t=LT_ + LSTEP)),
    ("no liner, arms rigid", dict(NO_LINER, flex_arms=False)),
    (f"liner {LT_:g} mm, arms rigid", dict(FINAL, flex_arms=False)),
    (f"liner {LT_:g} mm, legs 5 mm", dict(FINAL, leg_t=5.0)),
    ("no liner, legs 5.0 mm", dict(NO_LINER, leg_t=5.0)),
    ("no liner, legs 8.0 mm", dict(NO_LINER, leg_t=8.0)),
    ("no liner, legs 9.0 + bar 7.5 mm", dict(NO_LINER, leg_t=9.0, bar_t=7.5)),
    ("no liner, arch half-angle 45°", dict(NO_LINER, arch_phi=45.0)),
    ("no liner, temporal pad 1.1 × 1.5 larger (needs a backing plate)", dict(NO_LINER, pad_t_stretch=(1.1, 1.5))),
    ("no liner, preload +0.8 N", dict(NO_LINER, link_preload=FINAL["link_preload"] + 0.8,
                                      link_preload_ref=(FINAL.get("link_preload_ref") or FINAL["link_preload"]) + 0.8)),
]
res_root = {"note": "static donning A, head upright; mass properties of the Final CAD at each size for every variant",
            "rows": []}
for lab, des_ in ROOT_VARIANTS:
    row = dict(variant=lab)
    for D in (55, 60):
        row[str(D)] = root_state(des_, D, (MP_F[D]["M"], MP_F[D]["com"], MP_F[D]["I"]))
    res_root["rows"].append(row)
# without the liner, is there ANY eye position on the cup that keeps the root <= 4 kPa? (4 mm grid, as tune_eye stage 1)
res_root["no_liner_eye_scan"] = {}
for D in (55, 60):
    ps = {k: v for k, v in (NO_LINER.get("per_size") or {}).items() if k != str(D)}
    best = None; n = 0
    for (_, x_, y_) in te.grid(D, te.GRID_STEPS[0]):       # the eye tune's stage-1 grid on this cup
        st_ = root_state(dict(NO_LINER, link_x=float(x_), link_y=float(y_), per_size=ps), D, (MP_F[D]["M"], MP_F[D]["com"], MP_F[D]["I"]))
        if st_.get("ok"):
            n += 1
            if best is None or st_["root_p"] < best[0]:
                best = (st_["root_p"], float(x_), float(y_))
    res_root["no_liner_eye_scan"][str(D)] = dict(n_eyes=n, grid_mm=te.GRID_STEPS[0], min_root_p=best[0] if best else None,
                                                 at=best[1:] if best else None)
# ... and single changes of the pad layout (each pad angle +-10 deg, each radius -4 mm or up to its search bound), no liner;
# feasible = inside the layout search bounds, pads 30 deg apart (layout.geometric_ok), pad inner edge >= PINNA_EDGE_R
res_root["no_liner_layout_scan"] = []
for k_, dv_ in (("temporal_a", -10), ("temporal_a", 10), ("temporal_r", -4), ("temporal_r", None), ("mastoid_a", -10),
                ("mastoid_a", 10), ("mastoid_r", -4), ("mastoid_r", None), ("post_a", -10), ("post_a", 10), ("post_r", -4),
                ("post_r", None)):
    lo_, hi_ = lo.BOUNDS[k_]
    v_ = float(hi_ if dv_ is None else FINAL[k_] + dv_)
    des_ = dict(NO_LINER, **{k_: v_})
    edge_ = min(lo.pad_edge_clearance(des_).values())
    row = dict(key=k_, delta=dv_, final=FINAL[k_], value=v_, edge_min=edge_,
               feasible=bool(lo_ <= v_ <= hi_ and lo.geometric_ok(lo.apply_pad_scale(dict(des_))) and edge_ >= lo.PINNA_EDGE_R))
    for D in (55, 60):
        row[str(D)] = root_state(des_, D, (MP_F[D]["M"], MP_F[D]["com"], MP_F[D]["I"]))
    res_root["no_liner_layout_scan"].append(row)
res_root["pad_edge_clearance_final"] = dict(lo.pad_edge_clearance(FINAL), limit=lo.PINNA_EDGE_R)
save("root_levers", res_root)
log("root levers: " + "; ".join(f"{r['variant']}: {r['60'].get('root_p', float('nan')) / 1e3:.2f} kPa" for r in res_root["rows"][:6]))

# =====================================================================================
# 6. Dynamics: driver isolation, arm modes (Rayleigh)
# =====================================================================================
res_dyn = {}
for D in dz.SIZES:
    drv = dz.DRIVERS[D]
    iso = dy.driver_isolation(D, drv["mass"], FINAL["driver_gasket_t"], drv["mount_d"], squeeze_mm=FINAL["gasket_driver_squeeze"])
    arms = {}
    des, d = an.prepared(FINAL, D)
    for a in ("temporal", "mastoid", "post", "saddle"):
        k = 1 / st.arm_compliance(d, des, a, [0, 0, 1])
        m_arm = next(p["m"] for p in res_final[D]["parts"] if p["part"] == f"arm_{a}")
        m_pad = next((p["m"] for p in res_final[D]["parts"] if p["part"] == f"pad_{a}"), 0.0)
        if a == "saddle":
            m_pad = next(p["m"] for p in res_final[D]["parts"] if p["part"] == "saddle_cap")
        m_eff = m_pad + dy.ARM_MASS_FACTOR * m_arm
        arms[a] = dict(k=k, m_eff=m_eff, f1=math.sqrt(k / m_eff) / (2 * math.pi))
    res_dyn[D] = dict(isolation=iso, arms=arms, rigid=res_final[D]["modes"],
                      isolation_options=ex.driver_isolation_options(D, drv["mass"], FINAL["driver_gasket_t"], drv["mount_d"],
                                                                    FINAL["gasket_driver_squeeze"]))
save("dynamics", res_dyn)

# =====================================================================================
# 7. Tolerances
# =====================================================================================
res_tol = {}
for D in (40, 50, 60):
    des, d = an.prepared(FINAL, D)
    s = tl.stackups(d, des, D)
    res_tol[D] = {k: dict({kk: vv for kk, vv in v[0].items() if kk != "samples"}, crit=v[1],
                          ok=(v[0]["mc_p0135"] >= v[1]["min"]) and (v[1]["max"] is None or v[0]["mc_p99865"] <= v[1]["max"]),
                          ok_wc=(v[0]["wc"][0] >= v[1]["min"]) and (v[1]["max"] is None or v[0]["wc"][1] <= v[1]["max"]))
                  for k, v in s.items()}
save("tolerance", res_tol)
log("tolerance done")

# =====================================================================================
# 8. Acoustics
# =====================================================================================
res_ac = {"ts": {}, "closed_box": {}, "geometry": {}, "modes": {}, "helmholtz_aperture": {}, "vent": {}}
f = ac.F
for D in dz.SIZES:
    des, d = an.prepared(FINAL, D)
    T = ac.ts(D); g = ac.module_geometry(d, des, D)
    res_ac["ts"][D] = T; res_ac["geometry"][D] = g
    res_ac["closed_box"][D] = ac.closed_box(T, g["Vb"])
    res_ac["modes"][D] = dict(cup=ac.cavity_modes(g["cup_ri"], g["h_in"]),
                              gap_standing=ac.C / (2 * (des["standoff"] * 1e-3)),
                              seal_cavity=ac.cavity_modes(des["seal_id"] / 2e3, des["standoff"] * 1e-3))
    # aperture (front mini-cavity) Helmholtz for a range of aperture ratios
    rows = []
    for ratio in sorted(set(np.round(np.arange(0.50, 1.001, 0.05), 2)) | {round(d["aperture_d"] / D, 3)}):
        ap = ratio * D / 2e3
        fH, Le_ = ac.helmholtz(g["V_front"], ap, 0.0, L_eff=ac.aperture_leff(des["baffle_front_t"] * 1e-3, ap))
        rows.append(dict(ratio=float(ratio), ap_d=2 * ap * 1e3, fH=fH, L_eff=Le_, chosen=abs(2 * ap * 1e3 - d["aperture_d"]) < 1e-6))
    res_ac["helmholtz_aperture"][D] = rows
    vrows = []
    for n in (1, 2, 3, 4, 6):
        for vd in (1.5, 2.0, 3.0, 4.0):
            fb, Le_ = ac.helmholtz(g["Vb"], vd / 2e3, des["cup_end_t"] * 1e-3, n, True, False)
            vrows.append(dict(n=n, d=vd, fb=fb, L_eff=Le_))
    res_ac["vent"][D] = vrows


def curve(r):
    return dict(f=r["f"][::4], spl=ac.spl(r["p"])[::4], Z=np.abs(r["Zin"])[::4])


d50 = an.prepared(FINAL, 50)[1]; des50 = an.prepared(FINAL, 50)[0]
Z_EAR = ac.ear_distance(d50, des50)     # aperture exit -> ear-canal entrance, from the CAD standoff and design.ANTHRO
res_ac["z_ear"] = Z_EAR
res_ac["z_ear_inputs"] = dict(standoff=des50["standoff"], z_mod0=d50["z_mod0"], pinna_protrusion_mean=dz.ANTHRO["pinna_protrusion_mean"],
                              concha_depth=dz.ANTHRO["concha_depth"])
res_ac["dist"] = {round((Z_EAR + dz_) * 1e3, 1): curve(ac.response_open(50, d50, des50, Z_EAR + dz_)) for dz_ in (-10e-3, -5e-3, 0.0, 5e-3, 10e-3)}
res_ac["sizes"] = {D: curve(ac.response_open(D, an.prepared(FINAL, D)[1], an.prepared(FINAL, D)[0],
                                             ac.ear_distance(an.prepared(FINAL, D)[1], an.prepared(FINAL, D)[0]))) for D in dz.SIZES}
res_ac["rear"] = {rt: curve(ac.response_open(50, d50, des50, Z_EAR, rear_type=rt)) for rt in ("open", "vented", "closed")}
res_ac["felt"] = {f"{s / 1e3:.0f}k x {t} mm": curve(ac.response_open(50, d50, des50, Z_EAR, felt_sigma=s, felt_t=t))
                  for s, t in ((20e3, 1.0), (40e3, 2.0), (80e3, 2.0), (40e3, 4.0), (40e3, 0.0))}
res_ac["aperture"] = {ratio: curve(ac.response_open(50, d50, des50, Z_EAR, aperture_d=ratio * 50))
                      for ratio in sorted({0.6, 0.75, dz.FRONT_OPEN_RATIO, 1.0})}
V_f = ac.sealed_front_volume(d50, des50)
res_ac["sealed_leak"] = {w: curve(ac.response_sealed(50, d50, des50, V_f, w * 1e-3)) for w in (0.02, 0.05, 0.1, 0.3, 1.0)}
res_ac["sealed_Vf"] = V_f
# seal-pad option: material x height -> conformity at the spare pressure -> residual leak -> bass loss
res_ac["seal_sweep"] = {}
for D in (40, 50, 60):
    desD, dD = an.prepared(FINAL, D)
    V_fD = ac.sealed_front_volume(dD, desD)
    res_ac["seal_sweep"][D] = ex.seal_sweep(D, dD, desD, V_fD)
res_ac["seal_params"] = dict(p=ex.SEAL_P, a_irr=ex.SEAL_A_IRR, h_min=ex.SEAL_H_MIN, materials=ex.seal_materials())
save("acoustics", res_ac)
log("acoustics done")

# =====================================================================================
# 8b. Contact stresses at every interface (50 and 60 mm)
# =====================================================================================
res_cs = {}
for D in (50, 60):
    r = res_final[D]
    des, d = an.prepared(FINAL, D)
    area = {c["name"]: c["area"] for c in r["contacts"]}
    rows = []
    stat = {x["name"]: x["Fn"] for x in r["support"]["static"]["contacts"]} if r["support"]["static"]["ok"] else {}
    for nm, A in area.items():
        for lab, F_ in (("static (sustained)", stat.get(nm, 0.0)), ("2 g max (transient)", r["support"]["2 g dynamic"]["F_contact_max"][nm]),
                        ("5 g max (accidental)", r["support"]["5 g accidental"]["F_contact_max"][nm])):
            pc = ex.pad_contact(F_, 0, 0, 0, A)
            lim = {"static (sustained)": TISSUE["p_sustained"].v, "2 g max (transient)": TISSUE["p_transient"].v,
                   "5 g max (accidental)": TISSUE["p_pain"].v}[lab]
            rows.append(dict(interface=f"saddle zone {nm} on the auricle root" if nm.startswith("S root") else f"pad {nm} on skin",
                             case=lab, F=F_, area=A, p_mean=pc["p_mean"], p_peak=pc["p_winkler"],
                             limit=lim, ratio=pc["p_winkler"] / lim))
    # highest preload of the tightening scatter (nut factor K = 0.20 [LIT]); the aged preload is lower
    Fi_arm = des["arm_torque"] / (NUT_FACTOR_K_RANGE[0].v * SCREW[des["arm_screw"]]["d"] * 1e-3)
    Fi_anc = des["anchor_torque"] / (NUT_FACTOR_K_RANGE[0].v * SCREW[des["anchor_screw"]]["d"] * 1e-3)
    hb = ex.screw_head_bearing(des["arm_screw"], Fi_arm)
    rows.append(dict(interface=f"arm screw head ({des['arm_screw']}) on PETG arm", case="highest preload (K 0.20)", F=Fi_arm, p_peak=hb["p"],
                     SF=hb["SF"], SF_sustained=hb["SF_sustained"]))
    hb = ex.screw_head_bearing(des["anchor_screw"], Fi_anc)
    rows.append(dict(interface=f"anchor screw head ({des['anchor_screw']}) on PETG anchor", case="highest preload (K 0.20)", F=Fi_anc, p_peak=hb["p"],
                     SF=hb["SF"], SF_sustained=hb["SF_sustained"]))
    for arm in ("temporal", "saddle"):
        w_ = (des["saddle_arm_w"] if arm == "saddle" else des["arm_w"]) * 1e-3
        sf_ = ex.serration_flank(2 * Fi_arm, int(st.L_ENG_SERR / (des["serr_p"] * 1e-3)), w_, des["serr_h"] * 1e-3)
        rows.append(dict(interface=f"serration flanks ({arm} arm, {w_ * 1e3:.0f} mm)", case="highest preload (2 screws, K 0.20)", F=2 * Fi_arm,
                         p_peak=sf_["p"], SF=sf_["SF"], SF_sustained=sf_["SF_sustained"]))
    le = res_joint["link_eye"]
    rows.append(dict(interface="link wire on brass eye sleeve (Hertz line)", case="donning preload", F=le["P_don"], p_peak=le["hertz"]["p0"],
                     SF=le["SF_brass"], half_width=le["hertz"]["b"]))
    rows.append(dict(interface="eye insert on PETG boss (lateral)", case="donning preload", F=le["P_don"], p_peak=le["p_insert"],
                     SF_sustained=le["SF_insert"]))
    res_cs[D] = rows
save("contact_stress", res_cs)
log("contact stresses done")

# =====================================================================================
# 9. Maximum driver mass (static hold / normal / dynamic / maximum design condition), one process per size
# =====================================================================================
MASS_CONDS = (("static", 0.0), ("normal", 0.0), ("dynamic", 0.0), ("dynamic", 0.10), ("maximum", 0.0))


def mass_job(D):
    mp = MP_F[D]
    rowm = {}
    for cond, allow in MASS_CONDS:
        t0 = time.time()
        res = an.max_driver_mass(FINAL, D, mp, cond, n_dir=2 if SMOKE else (16 if QUICK else 24), allow=allow,
                                 **(dict(tol=40.0, n_acc=4) if SMOKE else {}))
        key = cond if cond != "dynamic" else f"dynamic (released <= {allow:.0%})"
        rowm[key] = dict(res, seconds=time.time() - t0)
    return D, rowm


sizes_mm = (50,) if SMOKE else ((50, 60) if QUICK else tuple(dz.SIZES))
res_mass = {}
with cfu.ProcessPoolExecutor(4, mp_context=mpr.get_context("fork")) as pool:
    for D, rowm in pool.map(mass_job, sizes_mm):
        res_mass[D] = rowm
        log(f"max driver mass D={D}: " + ", ".join(
            f"{k} " + (f"{v['min_driver_g']:.1f}-{v['max_driver_g']:.1f} g" if v["holds_at_nominal"] else "fails at nominal")
            + f" ({v['n_eval']} evals)" for k, v in rowm.items()))
save("max_driver_mass", res_mass)

# released fraction vs driver mass (Final, 50 mm), one process per mass
mp50 = MP_F[50]


def slip_job(mg):
    mpt = an.with_driver_mass(mp50, 50, mg, None)
    ev, _ = an.support_eval(FINAL, 50, mpt, n_dir=2 if SMOKE else 24, n_grav=1 if SMOKE else 4, n_cable=1 if SMOKE else 2,
                            struct=False, cats=["1 g normal", "2 g dynamic", "3 g severe"])
    return dict(driver_g=mg, total_g=mpt[0] * 1e3, **{c: ev[c]["slip_fraction"] for c in ("1 g normal", "2 g dynamic", "3 g severe")},
                static_ok=bool(ev["static"]["ok"]))


with cfu.ProcessPoolExecutor(4, mp_context=mpr.get_context("fork")) as pool:
    curve_rows = list(pool.map(slip_job, (0, 80) if SMOKE else (0, 10, 20, 26, 40, 60, 80)))
save("slip_vs_mass", curve_rows)
log("mass curves done")
print("DONE", time.time() - T0)
