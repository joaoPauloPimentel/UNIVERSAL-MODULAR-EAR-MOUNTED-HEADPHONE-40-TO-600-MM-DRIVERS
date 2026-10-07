# Study (2026-10-01): closed-back rear chamber options for model A final (lumped; T/S values representative [A]).
# Peak of the closed-box resonance above the 100 Hz level, and the 100 Hz level, for: as drawn; cup 10 mm deeper;
# chamber filled with polyester fibre (isothermal: effective volume x1.3 [LIT 1.2-1.4], plus flow resistance);
# a damped vent (n holes of d mm through the cup end, covered with needle felt t mm) - semi-closed.
import sys, os, json, math
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import umeh3
from umeh3 import geom, RESULTS
from umeh2 import acoustics as ac
from umeh2.materials import ACOUSTIC_MAT
geom.apply(os.environ.get("UMEH_VAR", "AF"))
lc = json.load(open(os.path.join(RESULTS, "light_checks" + ("" if geom.VARIANT == "AF" else "_" + geom.VARIANT) + ".json")))["acoustics"]
f = ac.F
R_pad_i = geom.PAD["id"] / 2e3
V_front = math.pi * R_pad_i * geom.pad_x("id") / 2e3 * (geom.PAD["t"] - geom.PAD["comp"]) * 1e-3 + math.pi * (geom.POCKET_R * 1e-3) ** 2 * geom.RING_T * 1e-3 - ac.V_PINNA
land = (geom.PAD["od"] - geom.PAD["id"]) / 2 * geom.PAD["contact_frac"] * 1e-3
perim = math.pi * (geom.PAD["id"] + geom.pad_x("id")) / 2 * 1e-3      # ellipse ~ mean diameter
R_in = (geom.POCKET_R + geom.HUB_WALL - geom.WALL) * 1e-3
ZF = ac.front_impedance_sealed(V_front, 0.05e-3, perim, land, f)


def run(D, Vb, R_series=0.0, vent=None):
    Ts = ac.ts(D)
    Zc = ac.compliance(Vb, f)
    if vent:
        n, dmm, tmm = vent
        Zt, _, _ = ac.tube(dmm / 2e3, geom.WALL * 1e-3, f, True, False, n=n)
        Rf = ac.felt_R(ACOUSTIC_MAT["felt_sigma"].v, tmm * 1e-3, n * math.pi * (dmm / 2e3) ** 2 * 4)   # felt over 2x d
        Zv = Zt + Rf
        ZB = R_series + Zc * Zv / (Zc + Zv)
    else:
        ZB = R_series + Zc
    u, _ = ac.solve_driver(Ts, ZF, ZB, f)
    s = ac.spl(Ts["Sd"] * u * ZF)
    ref = float(np.interp(100, f, s)); band = (f > 150) & (f < 5000)
    return dict(spl100=ref, spl30=float(np.interp(30, f, s)), peak=float(s[band].max() - ref), at=float(f[band][np.argmax(s[band])]))


res = {}
for D in (40, 50, 60):
    Vb = lc[str(D)]["Vb_cm3"] * 1e-6
    A_v = 0.30 * math.pi * (geom.DRIVERS[D]["rear_d"] / 2e3) ** 2
    R_fib = ACOUSTIC_MAT["fibre_sigma"].v * 0.010 / A_v          # ~10 mm of fibre in the flow path behind the motor
    deeper = Vb + math.pi * R_in ** 2 * 10e-3
    res[D] = {
        "como desenhado": run(D, Vb),
        "copo 10 mm mais fundo": run(D, deeper),
        "copo cheio de fibra": run(D, 1.3 * Vb, R_fib),
        "copo +10 mm e cheio de fibra": run(D, 1.3 * deeper, R_fib),
        "respiro amortecido (2 furos 1,5 mm + feltro 3 mm)": run(D, Vb, 0.0, (2, 1.5, 3.0)),
        "copo +10 mm, fibra e respiro": run(D, 1.3 * deeper, R_fib, (2, 1.5, 3.0)),
    }
json.dump(res, open(os.path.join(RESULTS, "rear_options" + ("" if geom.VARIANT == "AF" else "_" + geom.VARIANT) + ".json"), "w"), indent=1)
for D, rows in res.items():
    print(f"D{D}")
    for k, r in rows.items():
        print(f"  {k:52s} 30 Hz {r['spl30'] - r['spl100']:+5.1f} dB, pico {r['peak']:+5.1f} dB @ {r['at']:.0f} Hz (100 Hz = {r['spl100']:.0f} dB/1V)")
