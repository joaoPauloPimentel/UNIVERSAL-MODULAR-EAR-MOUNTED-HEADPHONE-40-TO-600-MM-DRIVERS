# Study (2026-10-04): closed-back response of model A final with real drivers the user may buy.
# Tymphany (Peerless) HPD-50N25PR00-32: full T/S from the maker's sheet [D]. ELFINEAR 40/50 mm: the maker publishes no
# T/S, so a box of plausible values is swept [A] (Fs, Qts, Mms) and the spread is reported.
# Cup as built: +10 mm and filled with polyester fibre (same model as rear_options.py "copo cheio de fibra").
import sys, os, json, math, itertools
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import umeh3
from umeh3 import geom, RESULTS
from umeh2 import acoustics as ac
from umeh2.materials import ACOUSTIC_MAT
geom.apply("AF")
lc = json.load(open(os.path.join(RESULTS, "light_checks.json")))["acoustics"]
f = ac.F
R_pad_i = geom.PAD["id"] / 2e3
V_front = math.pi * R_pad_i ** 2 * (geom.PAD["t"] - geom.PAD["comp"]) * 1e-3 + math.pi * (geom.POCKET_R * 1e-3) ** 2 * geom.RING_T * 1e-3 - ac.V_PINNA
land = (geom.PAD["od"] - geom.PAD["id"]) / 2 * geom.PAD["contact_frac"] * 1e-3
ZF = ac.front_impedance_sealed(V_front, 0.05e-3, math.pi * geom.PAD["id"] * 1e-3, land, f)


def ts_from(Re, Le, Mms, Fs, Qms, Qes, Sd):
    ws = 2 * math.pi * Fs
    Cms = 1 / (ws ** 2 * Mms)
    return dict(Sd=Sd, Mms=Mms, Fs=Fs, Cms=Cms, Rms=ws * Mms / Qms, Bl=math.sqrt(ws * Mms * Re / Qes), Re=Re, Le=Le,
                Qms=Qms, Qes=Qes, Qts=Qms * Qes / (Qms + Qes), Vas=ac.RHO * ac.C ** 2 * Sd ** 2 * Cms)


def run(Ts, D, R_extra=0.0):
    Vb = lc[str(D)]["Vb_cm3"] * 1e-6
    A_v = 0.30 * math.pi * (geom.DRIVERS[D]["rear_d"] / 2e3) ** 2
    R_fib = ACOUSTIC_MAT["fibre_sigma"].v * 0.010 / A_v
    ZB = R_fib + R_extra + ac.compliance(1.3 * Vb, f)
    u, _ = ac.solve_driver(Ts, ZF, ZB, f)
    s = ac.spl(Ts["Sd"] * u * ZF)
    ref = float(np.interp(100, f, s)); band = (f > 150) & (f < 3000)
    return dict(spl100=ref, rel30=float(np.interp(30, f, s)) - ref, peak=float(s[band].max() - ref),
                at=float(f[band][np.argmax(s[band])]), curve=[round(float(x), 2) for x in s])


res = {}
# Tymphany HPD-50N25PR00-32 spec sheet rev 1 (2018): Re 31, Le 0.13 mH, Mms 0.7 g, Fs 69.5, Qms 2.07, Qes 0.70, Sd 15.9 cm2
res["Tymphany HPD-50N25PR00-32 (50 mm, ficha)"] = run(ts_from(31.0, 0.13e-3, 0.7e-3, 69.5, 2.07, 0.70, 15.9e-4), 50)
# fix for its high Vas (2.7 L in a ~70 cm3 cup -> Qtc ~3.6): a needle-felt disc t mm over the rear of the driver, flow
# through the same area as the fibre path (A_v); felt sigma from umeh2.materials
A_v50 = 0.30 * math.pi * (geom.DRIVERS[50]["rear_d"] / 2e3) ** 2
for t in (2.0, 4.0):
    res[f"Tymphany + feltro {t:.0f} mm atrás do driver"] = run(ts_from(31.0, 0.13e-3, 0.7e-3, 69.5, 2.07, 0.70, 15.9e-4), 50,
                                                          ac.felt_R(ACOUSTIC_MAT["felt_sigma"].v, t * 1e-3, A_v50))
for D in (50, 40):
    res[f"representativo {D} mm (modelo usado até hoje)"] = run(ac.ts(D), D)
# ELFINEAR sweep [A]: graphene/silk domes; Fs, Qts box from typical 40/50 mm headphone drivers
BOX = {40: dict(Fs=(90, 120, 160), Qes=(0.4, 0.6, 0.9), Mms=(0.25e-3, 0.35e-3)),
       50: dict(Fs=(60, 85, 120), Qes=(0.4, 0.6, 0.9), Mms=(0.4e-3, 0.6e-3))}
for D, b in BOX.items():
    Sd = math.pi * (ac.D_EFF_RATIO * D / 2e3) ** 2
    rows = [run(ts_from(32.0, 50e-6, M, F, 2.0, Q, Sd), D) for F, Q, M in itertools.product(b["Fs"], b["Qes"], b["Mms"])]
    pk = [r["peak"] for r in rows]; s1 = [r["spl100"] for r in rows]; r30 = [r["rel30"] for r in rows]
    res[f"ELFINEAR {D} mm (faixa estimada)"] = dict(peak_min=min(pk), peak_max=max(pk), spl100_min=min(s1), spl100_max=max(s1),
                                                   rel30_min=min(r30), rel30_max=max(r30), n=len(rows))
json.dump({k: {kk: vv for kk, vv in v.items() if kk != "curve"} for k, v in res.items()},
          open(os.path.join(RESULTS, "real_drivers.json"), "w"), indent=1)
for k, r in res.items():
    if "peak_min" in r:
        print(f"{k:48s} 30 Hz {r['rel30_min']:+.1f}..{r['rel30_max']:+.1f} dB, pico {r['peak_min']:+.1f}..{r['peak_max']:+.1f} dB, 100 Hz {r['spl100_min']:.0f}..{r['spl100_max']:.0f} dB/1V ({r['n']} casos)")
    else:
        print(f"{k:48s} 30 Hz {r['rel30']:+.1f} dB, pico {r['peak']:+.1f} dB @ {r['at']:.0f} Hz, 100 Hz {r['spl100']:.0f} dB/1V")
