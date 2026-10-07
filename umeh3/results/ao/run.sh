#!/bin/bash
# UMEH-3 oval (AO) full calc chain, 2026-10-07. Logs in results/ao/.
cd "$(dirname "$0")/../../calc"
export UMEH_VAR=AO
L=../results/ao
for D in 60 50 40; do python3 studies/neckband_treadmill.py AO $D '[{"P": 0.5, "neck": 2.0}]' > $L/tread_$D.log 2>&1; echo "TREAD $D done" >> $L/progress.log; done
python3 -c "
import sys, json; sys.path.insert(0, '.')
from umeh3 import geom, loads; geom.apply('AO')
for D in (40, 50, 60):
    M, com, I, pc, rows = loads.mass_props(D)
    print(D, round(M * 1e3, 2), {r['part']: round(r['m_g'], 2) for r in rows})" > $L/mass.log 2>&1
python3 studies/neckband_shakedown.py AO 60 '{"P": 0.5, "neck": 2.0}' > $L/shakedown_60.log 2>&1; echo "SHAKE done" >> $L/progress.log
python3 studies/light_checks.py > $L/light_checks.log 2>&1
python3 studies/rear_options.py > $L/rear_options.log 2>&1
python3 studies/strength.py > $L/strength.log 2>&1
python3 studies/durability.py > $L/durability.log 2>&1; echo "CHECKS done" >> $L/progress.log
for D in 60 50 40; do python3 studies/categories.py $D > $L/categories_$D.log 2>&1; python3 studies/max_driver_mass.py $D > $L/max_driver_$D.log 2>&1; echo "HEAVY $D done" >> $L/progress.log; done
python3 -c "
import sys; sys.path.insert(0, '.')
from umeh3 import geom; geom.apply('AF'); geom.write_scad('../cad/params3.scad')"
echo ALLDONE >> $L/progress.log
