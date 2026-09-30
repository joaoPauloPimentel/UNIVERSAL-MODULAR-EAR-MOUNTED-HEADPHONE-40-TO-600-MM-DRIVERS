import os, subprocess, struct, sys
from concurrent.futures import ThreadPoolExecutor
CAD="/root/umeh2_work/cad"; OUT="/root/asm/out"; os.makedirs(OUT, exist_ok=True)
PARTS=["ring","gasket_umi","arm_saddle","arm_temporal","arm_mastoid","arm_post","saddle_cap","saddle_liner",
 "pad_temporal","pad_mastoid","pad_post","pad_face_temporal","pad_face_mastoid","baffle","gasket_driver","driver_visual","felt","cup","cable_anchor","cable_clip"]
base=open(f"{CAD}/umeh2.scad").read()
jobs=[]
for D in (40,45,50,55,60):
    src=f"{CAD}/_asm_{D}.scad"
    open(src,"w").write(base.replace("include <generated_params.scad>", f"include <params_{D}.scad>"))
    for p in PARTS: jobs.append((D,p,src))
def run(j):
    D,p,src=j; o=f"{OUT}/{D}_{p}.stl"
    if os.path.exists(o) and os.path.getsize(o)>0: return
    r=subprocess.run(["openscad","-o",o,"-D",f'part="placed_{p}"',"-D",'side="R"',src],capture_output=True,text=True)
    if r.returncode: print("FAIL",D,p,r.stderr[-300:],flush=True)
    else: print("ok",D,p,flush=True)
with ThreadPoolExecutor(4) as ex: list(ex.map(run,jobs))
print("DONE")
