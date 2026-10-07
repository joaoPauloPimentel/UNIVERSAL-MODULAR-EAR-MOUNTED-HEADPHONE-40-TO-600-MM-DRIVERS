# Study (2026-10-01): the light checks of model A final (AF): print tolerances of the tool-free fits, vibration
# (driver isolation, rigid-body modes on the head), closed-back acoustics (closed box, sealed front, leak while
# running) and contact pressures at every skin interface. Closed-form / lumped; NO FEA, NO acoustic FEM/BEM.
# python3 studies/light_checks.py  -> results/light_checks.json + printed summary
import sys, os, json, math
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import umeh3
from umeh3 import geom, loads, contacts as ct, neckband as nb, RESULTS
from umeh2 import tolerance as tol, acoustics as ac, dynamics as dy
from umeh2.materials import TPU, PETG

geom.apply(os.environ.get("UMEH_VAR", "AF"))
V = {"P": 0.5, "neck": 2.0}
out = {}
rng = np.random.default_rng(7)
T = tol.TOL


def mc(terms):
    r = tol.chain(terms, rng)
    r.pop("samples"); r.pop("share")
    return {k: (list(map(float, v)) if isinstance(v, tuple) else (float(v) if not isinstance(v, str) else v)) for k, v in r.items()}


# ------------------------------------------------------------------ 1. tolerances (FDM, [A] umeh2.tolerance.TOL)
tl = {}
# 1a axial squeeze of the TPU adapter flap when the bayonet ring is locked (holds the driver without glue).
#     squeeze = ring back face + adapter height - shoulder; nominal ADAPTER_SQ. The flap can take 0.05..0.9 mm.
#     A driver rim thicker than its seat pushes the stack (one-sided, taken as a symmetric term: conservative).
for D in geom.SIZES:
    terms = [("shell: lug groove -> shoulder (Z, two faces)", geom.ADAPTER_SQ, math.hypot(T["z"], T["z"]), +1),
             ("ring: lug -> back face (Z)", 0.0, T["z"], +1),
             ("TPU adapter height", 0.0, T["tpu"], +1),
             ("driver rim thickness vs seat", 0.0, geom.DRIVERS[D]["tol_depth"] * 0 + T["rim_t"], +1)]
    tl[f"squeeze_{D}"] = mc(terms)
# 1b driver rim in the adapter seat (diametral): seat = rim OD + 0.10; rim OD +-tol_d [A], TPU bore +-tpu.
for D in geom.SIZES:
    terms = [("seat bore (TPU)", 0.10, T["tpu"], +1), ("driver rim OD", 0.0, geom.DRIVERS[D]["tol_d"], -1)]
    tl[f"rim_fit_{D}"] = mc(terms)
# 1c adapter OD in the shell pocket (diametral): adapter OD = pocket - 0.30
tl["adapter_in_pocket"] = mc([("pocket bore (PETG XY)", 0.30, T["xy"], +1), ("adapter OD (TPU)", 0.0, T["tpu"], -1),
                              ("shrink difference", 0.0, T["shrink_diff"] * 2 * geom.POCKET_R, +1)])
# 1d bayonet: lug radial engagement = LUG_DEPTH + 0.35 - 0.5 - 0.15 clearance chain; must stay > 0.5 mm
tl["bayonet_engagement"] = mc([("lug radial reach (ring XY)", geom.LUG_DEPTH - 0.30, T["xy"], +1),
                               ("groove radial depth (shell XY)", 0.0, T["xy"], -1),
                               ("pocket / ring diameter (XY)", 0.0, T["xy"], -1)])
# 1e hook wire in the TPU friction bushing: diametral interference 0.15 nominal (bore WIRE_D - 0.15)
d_w = geom.WIRE_D * 1e-3
Do = (geom.BUSH_OD - 0.1) * 1e-3
E_t, nu_t = TPU["E"].v, TPU["nu"].v
MU_TPU_STEEL = 0.4          # [A] TPU 95A on polished steel, dry 0.3-0.5


def bushing_force(delta_mm):
    """Axial holding force (N) and turning torque (N mm) of the TPU bushing on the wire: thick ring on a rigid
    shaft, p = (delta/d) E (Do^2 - d^2) / ((1 + nu) Do^2 + (1 - nu) d^2) [STD, Lame]."""
    if delta_mm <= 0:
        return 0.0, 0.0, 0.0
    d = d_w
    p = (delta_mm * 1e-3 / d) * E_t * (Do ** 2 - d ** 2) / ((1 + nu_t) * Do ** 2 + (1 - nu_t) * d ** 2)
    F = MU_TPU_STEEL * p * math.pi * d * geom.BUSH_L * 1e-3
    return p, F, F * d / 2 * 1e3


bi = mc([("bushing bore (TPU XY), interference = wire - bore", 0.15, T["tpu"], +1), ("wire diameter", 0.0, 0.01, +1)])
tl["bushing_interference"] = bi
tl["bushing_force"] = {k: dict(zip(("p_Pa", "F_N", "T_Nmm"), bushing_force(x)))
                       for k, x in (("min", bi["mc_p0135"]), ("nom", 0.15), ("max", bi["mc_p99865"]))}
out["tolerances"] = tl

# ------------------------------------------------------------------ 2. vibration
vib = {}
for D in geom.SIZES:
    drv = geom.DRIVERS[D]
    # rim clamped between the TPU front lip/flap and the back lip: 1.0 mm TPU each side, 2.5 mm land [A]
    vib[f"driver_isolation_{D}"] = dy.driver_isolation(D, drv["mass"], 1.0 + geom.ADAPTER_SQ, drv["mount_d"], rim_w_mm=2.5,
                                                       squeeze_mm=geom.ADAPTER_SQ)
mp = nb.with_band(loads.mass_props(60), V["neck"])
C, link, info = ct.contact_set(V)
model = nb.ModelN(C, link)
W = loads.static_wrench(mp)
model.set_base(W)
try:
    K, r = dy.tangent_stiffness(model, W)
    Mm = dy.mass_matrix(mp[0], mp[1], mp[2])
    from scipy.linalg import eigh
    w2, Vv = eigh(K, Mm)
    f = np.sqrt(np.maximum(w2, 0)) / (2 * math.pi)
    names = []
    for v in Vv.T:
        trn = np.linalg.norm(v[:3]); rot = np.linalg.norm(v[3:]) * 0.05
        names.append(("translation " if trn > rot else "rotation about ") + "xyz"[int(np.argmax(np.abs(v[:3] if trn > rot else v[3:])))])
    vib["rigid_modes_60"] = [dict(f_Hz=float(a), mode=n) for a, n in zip(f, names)]
except Exception as e:      # report, do not hide
    vib["rigid_modes_60"] = f"FAILED: {e!r}"
out["vibration"] = vib

# ------------------------------------------------------------------ 3. acoustics (closed back, sealed front)
acu = {}
R_in = (geom.POCKET_R + geom.HUB_WALL - geom.WALL) * 1e-3
ZL_CH = geom.RING_T + geom.ADAPTER_H - geom.ADAPTER_SQ + geom.SHOULDER_T
h_ch = (geom.CUP_H - ZL_CH - geom.WALL) * 1e-3
V_ch = math.pi * R_in ** 2 * h_ch - (1 - math.pi / 4) * (2 * (geom.CUP_ROUND - geom.WALL) * 1e-3) ** 2 * 2 * math.pi * (R_in - 0.4 * (geom.CUP_ROUND - geom.WALL) * 1e-3)
V_fibre = math.pi * R_in ** 2 * geom.FIBRE_T * 1e-3 * 0.03          # fibre volume share ~3 % [A]
f = ac.F
R_pad_i = geom.PAD["id"] / 2e3
V_front_base = math.pi * R_pad_i * geom.pad_x("id") / 2e3 * (geom.PAD["t"] - geom.PAD["comp"]) * 1e-3 + math.pi * (geom.POCKET_R * 1e-3) ** 2 * geom.RING_T * 1e-3 - ac.V_PINNA
land = (geom.PAD["od"] - geom.PAD["id"]) / 2 * geom.PAD["contact_frac"] * 1e-3
perim = math.pi * (geom.PAD["id"] + geom.pad_x("id")) / 2 * 1e-3      # ellipse ~ mean diameter
LEAKS = {"vedado (fresta 0,05 mm em toda a volta) [A]": (0.05e-3, perim),
         "correndo, abertura leve (0,2 mm em 1/4 da volta) [A]": (0.2e-3, perim / 4),
         "correndo, abertura forte (0,5 mm em 1/2 da volta) [A]": (0.5e-3, perim / 2)}
for D in geom.SIZES:
    drv = geom.DRIVERS[D]
    Ts = ac.ts(D)
    V_mag = math.pi * (drv["rear_d"] / 2e3) ** 2 * max(drv["depth"] - drv["rim_t"] - (geom.ADAPTER_H - 1.0 - drv["rim_t"]), 0) * 1e-3 * ac.MOTOR_FILL
    Vb = V_ch - V_mag - V_fibre + math.pi * (geom.SHOULDER_RI * 1e-3) ** 2 * geom.SHOULDER_T * 1e-3
    # chamber filled with polyester fibre: isothermal compression -> effective volume x FILL_GAIN [LIT 1.2-1.4], and
    # ~10 mm of fibre in the flow path behind the motor (open area 30 % of the rear disc [A])
    FILL_GAIN = 1.3
    from umeh2.materials import ACOUSTIC_MAT as _AM
    R_fib = _AM["fibre_sigma"].v * 0.010 / (0.30 * math.pi * (drv["rear_d"] / 2e3) ** 2)
    cb = ac.closed_box(Ts, FILL_GAIN * Vb)
    ZB = R_fib + ac.compliance(FILL_GAIN * Vb, f)
    row = dict(Vb_cm3=Vb * 1e6, Vb_eff_cm3=FILL_GAIN * Vb * 1e6, Vfront_cm3=V_front_base * 1e6, Fc_Hz=cb["Fc"], Qtc=cb["Qtc"], alpha=cb["alpha"])
    spl = {}
    for name, (w, pr) in LEAKS.items():
        ZF = ac.front_impedance_sealed(V_front_base, w, pr, land, f)
        u, Zin = ac.solve_driver(Ts, ZF, ZB, f)
        p = Ts["Sd"] * u * ZF
        s = ac.spl(p)
        spl[name] = {str(int(fr)): float(np.interp(fr, f, s)) for fr in (30, 50, 100, 200, 500, 1000)}
    row["spl_1V"] = spl
    acu[str(D)] = row
# 3b damping the closed-box resonance: needle felt disc over the driver's rear vents (acoustic resistance in series
#     with the rear chamber). Open area of the basket behind the motor ~30 % of the rear disc [A].
from umeh2.materials import ACOUSTIC_MAT
damp = {}
for D in geom.SIZES:
    drv = geom.DRIVERS[D]; Ts = ac.ts(D); Vb = acu[str(D)]["Vb_cm3"] * 1e-6
    A_v = 0.30 * math.pi * (drv["rear_d"] / 2e3) ** 2
    ZF = ac.front_impedance_sealed(V_front_base, 0.05e-3, perim, land, f)
    rows = []
    for t_mm in (0.0, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0):
        R_fib = ACOUSTIC_MAT["fibre_sigma"].v * 0.010 / A_v
        ZB = ac.felt_R(ACOUSTIC_MAT["felt_sigma"].v, t_mm * 1e-3, A_v) + R_fib + ac.compliance(1.3 * Vb, f)
        u, _ = ac.solve_driver(Ts, ZF, ZB, f)
        sdb = ac.spl(Ts["Sd"] * u * ZF)
        ref = float(np.interp(100, f, sdb)); band = (f > 150) & (f < 5000)
        rows.append(dict(felt_mm=t_mm, spl100=ref, peak_rel_dB=float(sdb[band].max() - ref), peak_Hz=float(f[band][np.argmax(sdb[band])]),
                         spl1k_rel=float(np.interp(1000, f, sdb) - ref)))
    damp[str(D)] = rows
acu["felt_damping"] = damp
acu["modes_front_cavity_Hz"] = ac.cavity_modes(R_pad_i, (geom.PAD["t"] - geom.PAD["comp"]) * 1e-3)
acu["modes_rear_chamber_Hz"] = ac.cavity_modes(R_in, h_ch)
out["acoustics"] = acu

# ------------------------------------------------------------------ 4. contact pressures (60 mm, static + treadmill worst)
s = loads.static(mp, V)
cp = {"static": {x["name"]: dict(F_N=x["Fn"], p_kPa=x["p_mean"] / 1e3) for x in s["r"]["contacts"] if x["Fn"] > 1e-6}}
m = s["m"]
cp["static_summary"] = {k: float(m[k]) for k in ("pad_p", "root_p", "helix_p", "sulcus_p", "lobe_p", "pinna_p")}
sw = loads.sweep(mp, V, "treadmill", n_grav=3, n_cable=2)
cp["treadmill_worst"] = {k: float(sw["worst"][k]) for k in ("pad_p", "root_p", "helix_p", "sulcus_p", "lobe_p", "pinna_p")}
out["contacts"] = cp


def _clean(o):
    if isinstance(o, dict):
        return {str(k): _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_clean(v) for v in o]
    if isinstance(o, (np.floating, np.integer)):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    return o


json.dump(_clean(out), open(os.path.join(RESULTS, "light_checks" + ("" if geom.VARIANT == "AF" else "_" + geom.VARIANT) + ".json"), "w"), indent=1)

# ------------------------------------------------------------------ summary
print("== tolerances")
for D in geom.SIZES:
    q = tl[f"squeeze_{D}"]; r_ = tl[f"rim_fit_{D}"]
    print(f"D{D}: flap squeeze nom {q['nom']:.2f} mm, 3-sigma {q['mc_p0135']:.2f}..{q['mc_p99865']:.2f} (ok 0.05..0.9); "
          f"rim fit {r_['mc_p0135']:+.2f}..{r_['mc_p99865']:+.2f} mm (+ clearance, - interference)")
for k in ("adapter_in_pocket", "bayonet_engagement", "bushing_interference"):
    q = tl[k]; print(f"{k}: nom {q['nom']:.2f}, 3-sigma {q['mc_p0135']:.2f}..{q['mc_p99865']:.2f}")
for k, x in tl["bushing_force"].items():
    print(f"bushing {k}: p {x['p_Pa'] / 1e6:.2f} MPa, slide force {x['F_N']:.1f} N, turn torque {x['T_Nmm']:.1f} N mm")
print("== vibration")
for D in geom.SIZES:
    x = vib[f"driver_isolation_{D}"]; print(f"D{D}: driver on TPU fn {x['fn']:.0f} Hz, isolates above {x['iso_from']:.0f} Hz")
print("rigid modes 60 mm:", vib["rigid_modes_60"] if isinstance(vib["rigid_modes_60"], str) else
      ", ".join(f"{x['f_Hz']:.1f} Hz {x['mode']}" for x in vib["rigid_modes_60"]))
print("== acoustics")
for D in geom.SIZES:
    a = acu[str(D)]
    print(f"D{D}: Vb {a['Vb_cm3']:.1f} cm3, Vfront {a['Vfront_cm3']:.1f} cm3, closed box Fc {a['Fc_Hz']:.0f} Hz Qtc {a['Qtc']:.2f}")
    for name, sp_ in a["spl_1V"].items():
        print(f"    {name}: " + ", ".join(f"{k} Hz {v:.1f} dB" for k, v in sp_.items()))
for D in geom.SIZES:
    print(f"D{D} felt on driver back: " + "; ".join(f"{r['felt_mm']:.1f} mm peak {r['peak_rel_dB']:+.1f} dB @ {r['peak_Hz']:.0f} Hz, 100 Hz {r['spl100']:.0f} dB" for r in acu["felt_damping"][str(D)]))
print("front cavity modes", {k: round(v) for k, v in acu["modes_front_cavity_Hz"].items()},
      "rear", {k: round(v) for k, v in acu["modes_rear_chamber_Hz"].items()})
print("== contacts 60 mm (kPa)")
print("static ", {k: round(v / 1e3, 2) for k, v in cp["static_summary"].items()})
print("running", {k: round(v / 1e3, 2) for k, v in cp["treadmill_worst"].items()})
