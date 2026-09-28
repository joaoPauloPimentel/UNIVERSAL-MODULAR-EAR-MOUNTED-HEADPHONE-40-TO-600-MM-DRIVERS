#!/usr/bin/env python3
"""
Regenerates cad/generated_params.scad from the Final design and exports every
printable STL (print orientation) into stl/. Common cradle parts are exported
once (they are identical for all drivers: the interface is sized by the 60 mm
driver); module parts are exported per driver size. Handed parts get _R/_L.
"""
import json, os, subprocess, sys, concurrent.futures as cf_
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from umeh2 import design as dz, configs as cf, analysis as an

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STL = os.path.join(ROOT, "stl")
SCAD = os.path.join(dz.CAD, "umeh2.scad")
FINAL = cf.final_design()
lk = json.load(open(os.path.join(ROOT, "results", "link.json")))["Final"]["chosen"]
FINAL["wire_d"] = lk["d_mm"]; FINAL["link_coils"] = lk["n_coil"]

COMMON = [("ring", True), ("gasket_umi", False), ("arm_saddle", False), ("arm_temporal", False), ("arm_mastoid", False),
          ("arm_post", False), ("saddle_cap", False), ("pad_temporal", False), ("pad_mastoid", False), ("pad_post", False),
          ("cable_anchor", False), ("cable_clip", False), ("seal_pad", False)]
MODULE = [("baffle", False), ("gasket_driver", False), ("cup", True)]
# cast silicone parts (pad facings, saddle liner): reference geometry for the casting moulds (not printed)
CAST = [("pad_face_temporal", False), ("pad_face_mastoid", False)] + \
    ([("saddle_liner", False)] if FINAL.get("saddle_liner_t", 0) > 0 else [])


def params_file(D):
    des, d = an.prepared(FINAL, D)
    path = os.path.join(dz.CAD, f"params_{D}.scad")
    dz.write_scad(d, path, header=f"Final design, driver {D} mm")
    return path


def job(args):
    part, side, D, pfile, out = args
    # use a per-size copy of the main file that includes the per-size parameter file
    src = os.path.join(dz.CAD, f"_umeh2_{D}.scad")
    cmd = ["openscad", "-o", out, "-D", f'part="{part}"', "-D", f'side="{side}"', src]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return out, r.returncode, r.stderr[-300:]


def main():
    os.makedirs(STL, exist_ok=True)
    jobs = []
    base = open(SCAD).read()
    for D in dz.SIZES:
        pf = params_file(D)
        open(os.path.join(dz.CAD, f"_umeh2_{D}.scad"), "w").write(base.replace("include <generated_params.scad>", f"include <params_{D}.scad>"))
    for part, handed in COMMON:
        for side in (("R", "L") if handed else ("R",)):
            out = os.path.join(STL, "common", f"{part}{'_' + side if handed else ''}.stl")
            os.makedirs(os.path.dirname(out), exist_ok=True)
            jobs.append((part, side, 60, None, out))
    for part, handed in CAST:
        out = os.path.join(STL, "common", "cast_reference", f"{part}.stl")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        jobs.append((part, "R", 60, None, out))
    for D in dz.SIZES:
        for part, handed in MODULE:
            for side in (("R", "L") if handed else ("R",)):
                out = os.path.join(STL, f"module_{D}mm", f"{part}_{D}{'_' + side if handed else ''}.stl")
                os.makedirs(os.path.dirname(out), exist_ok=True)
                jobs.append((part, side, D, None, out))
    fails = []
    with cf_.ThreadPoolExecutor(4) as ex:
        for out, rc, err in ex.map(job, jobs):
            ok = rc == 0 and os.path.exists(out) and os.path.getsize(out) > 200
            print(("OK  " if ok else "FAIL"), os.path.relpath(out, ROOT), flush=True)
            if not ok:
                fails.append((out, err))
    for D in dz.SIZES:
        os.remove(os.path.join(dz.CAD, f"_umeh2_{D}.scad"))
    # keep generated_params.scad = 50 mm Final (default for opening the CAD)
    des, d = an.prepared(FINAL, 50); dz.write_scad(d, header="Final design, driver 50 mm (default)")
    print("failures:", fails)
    return fails


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
