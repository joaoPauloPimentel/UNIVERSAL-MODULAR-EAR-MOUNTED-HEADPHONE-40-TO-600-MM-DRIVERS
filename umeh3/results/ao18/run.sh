#!/bin/bash
# UMEH-3 oval (AO) with the plain 1.8 mm band (user 2026-10-07), treadmill 60/50/40 + long run 60.
cd "$(dirname "$0")/../../calc"
export UMEH_VAR=AO UMEH_BAND=1.8,0
L=../results/ao18
for D in 60 50 40; do python3 studies/neckband_treadmill.py AO $D '[{"P": 0.5, "neck": 2.0}]' > $L/tread_$D.log 2>&1; echo "TREAD $D done" >> $L/progress.log; done
python3 studies/neckband_shakedown.py AO 60 '{"P": 0.5, "neck": 2.0}' > $L/shakedown_60.log 2>&1; echo "SHAKE done" >> $L/progress.log
python3 -c "import sys; sys.path.insert(0, '.')
from umeh3 import geom; geom.apply('AF'); geom.write_scad('../cad/params3.scad')"
echo ALLDONE >> $L/progress.log
