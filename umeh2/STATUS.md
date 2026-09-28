# UMEH-2: paused (2026-09-28 08:49 UTC)

UMEH-2 cradle sources (40–60 mm drivers): OpenSCAD model (`cad/`), calculation pipeline (`calc/`), results (`results/`).

Design in `calc/final_layout.json`: link preload 5.0 N; link eye (x, y) mm per module 40 (-15, 7), 45 (-18, 7),
50 (-19, 7), 55 (-18, 7), 60 (-18, 7). Legs 5.5 mm, saddle liner 2.5 mm, link wire 2.5 mm / 4 coils.

## Done (run_all.py on this design, 05:42–08:49 UTC)
- Final, Design A and B support runs, eye re-score (`eye_check.json`), 1 g dense check + refinement (`dense_1g.json`,
  `final_sizes.json`): every module passes the dense check and its refinement (no release, tripod kept); smallest
  seating margin 0.031 N (40 mm, refined), 0.038 N at 60 mm.
- Joints, cable, dynamics, tolerance, acoustics, contact stress, weight options, root levers (Final root 3.61 kPa donned).
- `eye_tuning.json` written by `calc/eye_record.py` as a RECORD: the tune's own output was lost with the machine
  that ran it (surviving log: `results/eye_tuning_partial.log`).

## Interrupted (paused on request)
- run_all.py stopped during max_driver_mass (40–55 mm finished in `results/run_all_interrupted.log`, 60 mm running).
  `results/max_driver_mass.json` is still the OLD one (2026-09-27).
- Not run yet: shakedown, sweeps, figures, build_stl, bom, make_report.

## Resume
Checkpoints of the expensive runs are in `/mnt/project-files/umeh2_snapshot2/_cache/` (copy into `umeh2/calc/_cache/`).
    cd umeh2/calc && python3 run_all.py --resume && python3 shakedown.py && python3 sweeps.py && python3 figures.py \
      && python3 build_stl.py && python3 bom.py && python3 eye_record.py && python3 make_report.py
(needs numpy, scipy, matplotlib, OpenSCAD; STL files are generated, not committed).
