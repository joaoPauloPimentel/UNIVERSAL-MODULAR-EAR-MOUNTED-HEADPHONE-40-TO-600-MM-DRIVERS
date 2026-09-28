"""Record of the final eye tune (tune_eye.py at 5.0 N, legs 5.5 mm / liner 2.5 mm) whose output file was lost.

The machine that ran the tune lost its disk before results/eye_tuning.json could be copied out. What survives:
the tune's log up to its first stage-4 result (results/eye_tuning_partial.log: preload levels, stage-1 pass counts,
the 40 mm dense verification) and the chosen eyes and preload, written to calc/final_layout.json by hand from the
session notes. This script writes results/eye_tuning.json as a RECORD (flag "_record"): the tune's settings from
tune_eye.py, the preload levels read from the log, and per module the tune objective re-scored at the chosen eye
with the Final's inputs (results/eye_check.json from run_all.py). The chosen eyes are verified independently by
run_all.py's dense 1 g check and its refinement (results/dense_1g.json, report §8).

Run after run_all.py:  cd calc && python3 eye_record.py
"""
import json
import os
import re

import tune_eye as te
from umeh2 import support as sp
from umeh2.util import js

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
LOG = os.path.join(RES, "eye_tuning_partial.log")


def levels_from_log(txt):
    wire = {float(p): dict(d_mm=float(d), n_coil=int(n)) for p, d, n in
            re.findall(r"preload ([\d.]+) N: wire ([\d.]+) mm, (\d+) coils", txt)}
    npass = {float(p): {k: int(v) for k, v in re.findall(r"(\d+): (\d+)", s)} for p, s in
             re.findall(r"preload ([\d.]+) N: candidates passing normal use per module \{([^}]*)\}", txt)}
    return [dict(P=P, wire=wire.get(P), n_pass=npass[P], n_eval=None) for P in sorted(npass)]


def dense_ok(d):
    return bool(d and d.get("ok") and (d.get("refine") is None or d["refine"].get("ok")))


def main():
    txt = open(LOG).read()
    lay = json.load(open(os.path.join(ROOT, "calc", "final_layout.json")))
    fin = json.load(open(os.path.join(RES, "final_sizes.json")))
    ec = json.load(open(os.path.join(RES, "eye_check.json")))
    lk = json.load(open(os.path.join(RES, "link.json")))["Final"]["chosen"]
    import umeh2.configs as cf
    F = cf.final_design()
    lv = levels_from_log(txt)
    out = {}
    for D, e in lay["per_size"].items():
        c = ec.get(D, {})
        out[D] = dict(best=dict(c, x=e["link_x"], y=e["link_y"], _from="results/eye_check.json (tune objective at the chosen eye, Final inputs)"),
                      n_pass=(lv[-1]["n_pass"].get(D) if lv else None), n_eval=None, dense_verified=None)
    out["_record"] = ("The tune's own output (results/eye_tuning.json) was lost with the machine that ran it. Chosen eyes and "
                      "preload: calc/final_layout.json; preload levels and stage-1 pass counts: results/eye_tuning_partial.log; "
                      "per-module values: the tune objective re-scored at the chosen eye with the Final's inputs "
                      "(results/eye_check.json); verification: run_all.py dense 1 g check + refinement (results/dense_1g.json).")
    out["_inputs"] = dict(wire_d=lk["d_mm"], link_coils=lk["n_coil"], leg_t=F["leg_t"], link_preload=lay["link_preload"],
                          saddle_liner_t=F.get("saddle_liner_t", 0.0), bar_t=F["bar_t"],
                          sets=te.set_counts(), grid_mm=list(te.GRID_STEPS), k_2g=te.K_2G,
                          preload_layout=lay.get("_link_preload_layout"), preload_step=te.PRELOAD_STEP, preload_levels=lv,
                          all_modules_pass=all(dense_ok((fin.get(D) or {}).get("dense_1g")) for D in lay["per_size"]),
                          max_verify=te.MAX_VERIFY, grid_1g=sp.GRID_1G, dense_1g=sp.DENSE_1G)
    json.dump(js(out), open(os.path.join(RES, "eye_tuning.json"), "w"), indent=1)
    print("written results/eye_tuning.json (record)", [(x["P"], x["n_pass"]) for x in lv])


if __name__ == "__main__":
    main()
