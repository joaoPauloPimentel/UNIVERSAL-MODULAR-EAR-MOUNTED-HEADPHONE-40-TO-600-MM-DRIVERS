"""UMEH-3: closed over-ear module on a behind-the-ear hook; one shell for 40-60 mm drivers. Reuses the UMEH-2
solver, materials and acoustic elements (package umeh2, ../../umeh2/calc)."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))      # .../umeh3
sys.path.insert(0, os.path.join(os.path.dirname(ROOT), "umeh2", "calc"))
CAD = os.path.join(ROOT, "cad")
RESULTS = os.path.join(ROOT, "results")

# Wire material switch (2026-10-09): UMEH_WIRE=ss302 uses the stainless AISI 302 hard (spring temper, ASTM A313) wire sold
# in Brazil on Mercado Livre instead of ASTM A228 music wire. Values from Shigley Table 10-4 / A313 data; the seller gives no
# certificate, so the real temper must be checked on the first hook [A].
if os.environ.get("UMEH_WIRE", "").lower() == "ss302":
    from umeh2 import materials as _mt
    _mt.WIRE.update(
        E=_mt.Val(193e9, "STD", "AISI 302 spring temper, ~193 GPa (Shigley Table A-5 stainless)"),
        rho=_mt.Val(7920, "STD", "AISI 302 density 7.92 g/cm3"),
        nu=_mt.Val(0.31, "STD", "Poisson's ratio of stainless steel"),
        Sy_ratio=_mt.Val(0.61, "A", "bending set limit ~0.61 Sut for A313 stainless (lower than music wire's 0.75) [A]"),
        Sut_A=_mt.Val(1867e6, "STD", "ASTM A313 stainless Sut = A / d^m (d in mm), Shigley Table 10-4"),
        Sut_m=_mt.Val(0.146, "STD", "exponent m, ASTM A313"),
    )
