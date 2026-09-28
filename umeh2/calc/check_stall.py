#!/usr/bin/env python3
"""
Solver check of iteration change 20 (load-step cutting, support.Model.MAX_CUTS).

The dense 1 g check of the Final of the first run of change 19 (calc/final_layout_grid45.json) reported two isolated
releases (40 and 45 mm) among 42 250 combinations per module. Each is re-solved here
  - without load-step cutting (MAX_CUTS = 0, the solver as it was) at 4, 5, 8, 16 and 32 load increments, and at
    the load scaled by 1 -/+ 1e-4 (4 increments),
  - with load-step cutting (the current solver, MAX_CUTS = support.Model.MAX_CUTS) at 4 increments,
and the kind of failure is recorded (runaway = displacement beyond 3 DISP_MAX / 3 ROT_MAX during the minimisation, i.e.
no bounded equilibrium; otherwise the minimisation stopped at a bounded position). Writes results/solver_stall_check.json.
"""
import json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from umeh2 import analysis as an, configs as cf, support as sp
from umeh2.util import js

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DES = cf.final_design(os.path.join(ROOT, "calc", "final_layout_grid45.json"))
# the two combinations the dense check released (support.DENSE_1G grid points; g_dir / cable_dir rounded to 4 digits)
CASES = [dict(D=40, g_dir=[0.3827, -0.9239, 0.0], axis="pitch (nod)", sign=-1, phase="alpha", cable_dir=[-0.3314, -0.5, 0.8001]),
         dict(D=45, g_dir=[0.1464, -0.9239, 0.3536], axis="pitch (nod)", sign=0.0, phase="omega", cable_dir=[0.6124, -0.5, -0.6124])]


def find_case(mpt, d, des, c):
    for tag, W in sp.load_cases(mpt, d, des, "1 g normal", 1, 0, 0, grid=sp.DENSE_1G_GRID45):
        if (np.allclose(tag["g_dir"], c["g_dir"], atol=2e-4) and np.allclose(tag["cable_dir"], c["cable_dir"], atol=2e-4)
                and tag["axis"] == c["axis"] and float(tag["sign"]) == float(c["sign"]) and tag["phase"] == c["phase"]):
            return W
    raise SystemExit(f"case not found: {c}")


def main():
    sp.DENSE_1G_GRID45 = dict(tilt=(11.25, 22.5, 33.75, 45.0), az_step=22.5, cable_polar=(20.0, 40.0, 60.0, sp.CABLE_CONE),
                              cable_az_step=22.5)          # the dense grid of that run
    orig = sp.Model._minimise
    last = {}

    def inst(self, W, s_old, g, q0, max_it=400, fixed=()):
        ok, q, it = orig(self, W, s_old, g, q0, max_it, fixed)
        if not ok:
            last["kind"] = "runaway" if sp.Model._runaway(q) else "stopped at a bounded position"
            last["disp_mm"] = float(np.linalg.norm(q[:3]) * 1e3); last["rot_deg"] = math.degrees(float(np.linalg.norm(q[3:6])))
        return ok, q, it
    sp.Model._minimise = inst
    out = []
    for c in CASES:
        D = c["D"]
        mp = an.mass_properties(DES, D, "S")
        mpt = (mp["M"], mp["com"], mp["I"])
        des_, d, C, model = an._model_1g(DES, D, mpt)
        W = find_case(mpt, d, des_, c)
        rows = []
        for cuts, n_steps, scale in ([(0, n, 1.0) for n in (4, 5, 8, 16, 32)] + [(0, 4, 1 - 1e-4), (0, 4, 1 + 1e-4)]
                                     + [(sp.Model.MAX_CUTS, 4, 1.0)]):
            model.MAX_CUTS = cuts; model.N_STEPS = n_steps
            last.clear()
            r = model.solve(W * scale, fric=True)
            row = dict(max_cuts=cuts, n_steps=n_steps, load_scale=scale, ok=bool(r["ok"]))
            if r["ok"]:
                m = sp.metrics(r, C)
                row.update(tilt=m["rot_xy"], seated=bool(m["seated"]), Fn={x["name"]: x["Fn"] for x in r["contacts"]})
            else:
                row.update(reason=r["reason"], first_failure=dict(last))
            rows.append(row)
            print(D, row.get("max_cuts"), n_steps, scale, row["ok"], row.get("tilt"), row.get("first_failure"), flush=True)
        out.append(dict(case=c, mass=mp["M"], runs=rows))
    json.dump(js(dict(design="calc/final_layout_grid45.json", cases=out)),
              open(os.path.join(ROOT, "results", "solver_stall_check.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
