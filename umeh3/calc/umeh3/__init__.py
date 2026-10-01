"""UMEH-3: closed over-ear module on a behind-the-ear hook; one shell for 40-60 mm drivers. Reuses the UMEH-2
solver, materials and acoustic elements (package umeh2, ../../umeh2/calc)."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))      # .../umeh3
sys.path.insert(0, os.path.join(os.path.dirname(ROOT), "umeh2", "calc"))
CAD = os.path.join(ROOT, "cad")
RESULTS = os.path.join(ROOT, "results")
