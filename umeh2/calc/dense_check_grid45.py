#!/usr/bin/env python3
"""
History of iteration change 21: the dense 1 g check and its local refinement (run_all section 3c code:
analysis.dense_1g_chunk / refine_1g_chunk) on the Final of the first run of change 19, whose eyes and preload were
tuned on the 1 g grid at 45 deg azimuth steps (calc/final_layout_grid45.json). The dense grid of that run was
tilt 11.25/22.5/33.75/45 deg x 22.5 deg, cable down + 20/40/60/80 deg x 22.5 deg. Writes results/dense_1g_grid45.json.
(About 20 min on 4 cores.)
"""
import json, os, sys, time
import concurrent.futures as cfu, multiprocessing as mpr
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from umeh2 import analysis as an, configs as cf, design as dz, support as sp

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAY = os.path.join(ROOT, "calc", "final_layout_grid45.json")


def save_(r):
    out = {k: v for k, v in r.items() if k not in ("fails", "seeds", "per_case")}
    out.update(n_fails=len(r["fails"]), fails_summary=an.fails_summary(r["fails"]), fails=r["fails"][:300])
    if "seeds" in r:
        out["seeds"] = r["seeds"]
    return out


def main():
    t0 = time.time()
    sp.DENSE_1G = dict(tilt=(11.25, 22.5, 33.75, 45.0), az_step=22.5, cable_polar=(20.0, 40.0, 60.0, sp.CABLE_CONE),
                       cable_az_step=22.5)                          # the dense grid of that run (before change 21)
    lay = json.load(open(LAY))
    F = cf.final_design(LAY)
    MP = {D: an.mass_properties(F, D, "F") for D in dz.SIZES}
    MPT = {D: (MP[D]["M"], MP[D]["com"], MP[D]["I"]) for D in dz.SIZES}
    jobs = [j for D in dz.SIZES for j in an.dense_1g_jobs(F, D, MPT[D])]
    parts = {D: [] for D in dz.SIZES}
    with cfu.ProcessPoolExecutor(4, mp_context=mpr.get_context("fork")) as ex:
        for a, r in zip(jobs, ex.map(an.dense_1g_chunk, jobs, chunksize=1)):
            parts[a[1]].append(r)
        dense = {D: an.dense_1g_merge(parts[D]) for D in dz.SIZES}
        rj, seeds = [], {}
        for D in dz.SIZES:
            j_, seeds[D] = an.refine_1g_jobs(F, D, MPT[D], dense[D])
            rj += j_
        rparts = {D: [] for D in dz.SIZES}
        for a, r in zip(rj, ex.map(an.refine_1g_chunk, rj, chunksize=1)):
            rparts[a[1]].append(r)
    ref = {D: an.refine_1g_merge(rparts[D], seeds[D]) for D in dz.SIZES}
    out = dict(
        _note=("dense 1 g check and its local refinement of the Final of the first run of iteration change 19 (eyes and preload "
               "tuned on the 1 g grid at 45 deg azimuth steps); evidence for change 21 (calc/dense_check_grid45.py)"),
        grid_1g=lay["_grid_1g"], grid={k: list(v) if isinstance(v, tuple) else v for k, v in sp.DENSE_1G.items()},
        eyes_note=(f"preload {lay['link_preload']:g} N, wire Ø{lay['wire_d']:g} mm / {lay['link_coils']} coils, eyes "
                   + ", ".join(f"{D} mm ({v['link_x']:g}, {v['link_y']:g})" for D, v in lay["per_size"].items())),
        refine_n=an.REFINE_N, k_crit=an.K_CRIT,
        sizes={str(D): save_(r) for D, r in dense.items()}, refine={str(D): save_(r) for D, r in ref.items()})
    from umeh2.util import js
    json.dump(js(out), open(os.path.join(ROOT, "results", "dense_1g_grid45.json"), "w"), indent=1)
    print("written results/dense_1g_grid45.json", round(time.time() - t0), "s")


if __name__ == "__main__":
    main()
