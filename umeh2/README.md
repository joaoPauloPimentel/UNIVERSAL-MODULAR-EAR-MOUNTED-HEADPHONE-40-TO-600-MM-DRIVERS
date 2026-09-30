# UMEH-2 — ear-mounted headphone cradle for 40–60 mm drivers

Second design iteration of the Universal Modular Ear-mounted Headphone: one common cradle (ring, four arms, pads, arched saddle, occipital spring link) that sits around the ear, and a driver module per size (40, 45, 50, 55 and 60 mm only) that twist-locks into it. Everything in this package is generated from the calculations: the CAD reads the parameter files the calculation writes, and the masses and centres of mass used by the load cases are integrated over the meshes that CAD exports.

**Read first:** `report/ENGINEERING_REPORT.md` (derivations, every load case, safety factors, limitations). No FEA, BEM or physical test was run; the report says where each is needed. Driver data, tissue properties and friction coefficients are assumptions or literature ranges and are tagged as such; measure your drivers and re-run.

## Key results (Final design)

| driver | mass per side g | normal use (static + 1 g + link) | auricle-root pressure in use kPa (target ≤ 4) | 2 g: % combinations released | 10 N handling min SF | max driver g, normal use (1 g grid) | max driver g, max design |
|---|---|---|---|---|---|---|---|
| 40 mm | 156 | PASS | 18.0 | 1.94 | 1.72 | 27.7 | 126.0 |
| 45 mm | 163 | PASS | 18.4 | 1.26 | 1.72 | 34.4 | 122.9 |
| 50 mm | 173 | PASS | 19.4 | 1.42 | 1.72 | 31.8 | 84.6 |
| 55 mm | 182 | PASS | 20.5 | 2.08 | 1.72 | 41.2 | 54.9 |
| 60 mm | 190 | PASS | 21.4 | 2.52 | 1.72 | 45.2 | 109.2 |


Normal use means: all pads loaded at rest, skin and auricle-root pressure ≤ 4 kPa as donned (clamp first; in use: see below), static friction within the design coefficient, and no gross slip, loss of the tripod or tilt > 2° anywhere in the 1 g grid of head orientations (up to the edge of the tilt cone), head rotations and cable pulls, nor in a finer dense check and its local refinement (report §8), and the link wire within its criteria on that module (report §11). Above 1 g the cradle, held by friction, releases in part of the combinations (40 mm: 1.94 %, 45 mm: 1.26 %, 50 mm: 1.42 %, 55 mm: 2.08 %, 60 mm: 2.52 % of the 2 g set); the report gives the fractions per case and why (§8, §10).

**Not met: the auricle-root pressure in use.** Normal use is judged as donned. Once the head moves, the pads micro-slip and the saddle ends up carrying the side's weight on the auricle root at 18.0–21.4 kPa, above the 4 kPa sustained comfort target at every size. None of the design levers studied meets it (report §6). Expect pressure at the top of the ear in long sessions, and measure it first (report §22).

## Assembly and use (these are part of the design)

* **Donning:** hold the cradle in place around the ear, clamp the link, then let go. Hanging it on the ear first and then clamping puts 5.15–5.21 × the auricle-root pressure on the ear (report §6).
* **Cable:** route it down the neck. Near-horizontal tugs of 1.34–2.02 N release the cradle before the plug gives (report §14). Plug in and unplug with the headphone off the head.
* **Arm screws:** torque driver at the value in `BOM.csv`, with a wave spring washer under every head; the serrations carry
  the load, the washer keeps the clamp after the PETG creeps (report §13).
* **Pad facings:** cast the silicone facing on the temporal and mastoid pads (reference geometry in
  `stl/common/cast_reference/`).
* **Saddle liner:** cast the soft (Shore 00-30) silicone liner into the saddle cap's recessed bearing face; without it the auricle root carries 4.41 kPa at 55 mm and 4.63 kPa at 60 mm at rest, over the 4 kPa target (report §6).
* **Print orientation and settings:** report §20 and the `spec` column of `BOM.csv`. The STLs are exported in print
  orientation.


## Contents

* `report/ENGINEERING_REPORT.md`, `report/fig/` — the engineering report and its figures.
* `cad/umeh2.scad` — parametric OpenSCAD model; `cad/generated_params.scad` (50 mm default) and `cad/params_<D>.scad` are
  written by the calculation.
* `stl/common/` — cradle parts (the same for every driver size); `stl/module_<D>mm/` — module parts per size (cups are
  handed because the link eye sits at a module-specific position).
* `calc/` — the models (`calc/umeh2/*.py`) and the scripts that produce every result.
* `results/*.json` — every computed number the report quotes.
* `BOM.csv`, `docs/bom_table.md` — bill of materials for one pair, masses from the CAD.

## Re-running

Requirements: Python 3 with numpy, scipy and matplotlib, and OpenSCAD on the PATH. Run for this delivery with
Python 3.11.15, numpy 2.4.6, scipy 1.17.1, matplotlib 3.11.2, OpenSCAD version 2021.01.

```
cd calc
python3 legs_liner.py    # arm-leg and saddle-liner thickness, chosen together (results/legs_liner.json)
python3 tune_eye.py      # per-module link-eye position and the link preload (writes calc/final_layout.json)
python3 run_all.py       # link, designs B/A/Final, joints, cable, weight, dynamics, tolerances, acoustics, max mass
python3 shakedown.py     # the sustained state in use: head-motion shakedown of the contact forces (results/shakedown.json)
python3 sweeps.py        # parameter sweeps
python3 figures.py
python3 build_stl.py     # STLs + cad/params_<D>.scad
python3 bom.py
python3 make_report.py   # report/ENGINEERING_REPORT.md and this README
```

The records of iteration changes 19–21 come from earlier states of the design, kept as inputs:
`calc/final_layout_before_grid.json` (run_all section 3d → results/grid_1g_before_grid.json), and
`calc/final_layout_grid45.json` (`python3 check_stall.py` → results/solver_stall_check.json;
`python3 dense_check_grid45.py` → results/dense_1g_grid45.json). They are not needed to re-run the design.

`legs_liner.py`, `tune_eye.py`, `run_all.py`, `shakedown.py` and `sweeps.py` use four processes and are the long steps (the contact model
solves every load combination of every candidate). Change an input (driver
data in `calc/umeh2/design.py`, materials in `calc/umeh2/materials.py`, design decisions in `calc/umeh2/configs.py`) and
re-run the chain; nothing in the report is typed by hand.
