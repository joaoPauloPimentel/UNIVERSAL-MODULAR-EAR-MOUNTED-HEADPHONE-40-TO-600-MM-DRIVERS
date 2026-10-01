# Study (2026-10-01): strength of model A final (AF). Closed-form; NO FEA.
#  1. Hook in its friction bushing: twisting moment about the wire axis and axial pull from the skin contacts (static,
#     treadmill worst) vs the bushing's slip torque / slide force (tolerance range from light_checks).
#  2. Hook wire (ASTM A228 1.6 mm): bending stress per mm of opening at the leg (donning), the opening that reaches
#     the set limit, and the stress in use (worst treadmill case).
#  3. Bayonet lugs (3, PETG): the driver inertia they hold, as a deceleration in g (what a drop may impose).
#  4. Neckband channel in the back (PETG): band pull 2 N + cable tug on the trough, keyhole lips, wire-end pin.
#  5. Flange plate 1.2 mm under the pad lip: bending from the pad force at the rim.
# python3 studies/strength.py  -> results/strength.json + printed summary
import sys, os, json, math
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import umeh3
from umeh3 import geom, loads, contacts as ct, neckband as nb, RESULTS
from umeh2.materials import PETG, TPU, WIRE, music_wire_Sut as wire_sut, GAMMA_M_PRINT
from umeh2 import structure as stc

geom.apply("AF")
V = {"P": 0.5, "neck": 2.0}
out = {}
mp = nb.with_band(loads.mass_props(60), V["neck"])
C, link, info = ct.contact_set(V)
model = nb.ModelN(C, link)
W_st = loads.static_wrench(mp)
model.set_base(W_st)
P, lab, i_plate, i_apex = ct.hook_points()
hh = P[i_plate]                    # wire leaves the shell here (bushing axis = z through hh)
pp = np.asarray(link[0][0] if isinstance(link, list) else link[0])
hook_idx = [i for i, c in enumerate(C) if c["name"].startswith("H ")]


def hook_wrench(r):
    """Force and moment (about hh) that the skin contacts + pinna clamp put on the hook, i.e. what the bushing holds."""
    F = np.zeros(3); M = np.zeros(3)
    for i in hook_idx:
        x = r["contacts"][i]; f = np.asarray(x["Fvec"]); F += f; M += np.cross(C[i]["r"] - hh, f)
    lf = np.asarray(r["link_force"]); F += lf; M += np.cross(pp - hh, lf)
    return F, M


# ---------------------------------------------------------------- 1 + 2b: loads on the hook, static and running
r0 = model.solve(W_st)
F0, M0 = hook_wrench(r0)
worst = dict(Tz=(0, None), Fz=(0, None), Mb=(0, None))
n = 0
for tag, W in loads.cases(mp, "treadmill", n_grav=3, n_cable=2):
    r = model.solve(W)
    if not r["ok"]:
        continue
    n += 1
    F, M = hook_wrench(r)
    for k, v in (("Tz", abs(M[2])), ("Fz", abs(F[2])), ("Mb", float(np.hypot(M[0], M[1])))):
        if v > worst[k][0]:
            worst[k] = (float(v), tag)
lc = json.load(open(os.path.join(RESULTS, "light_checks.json")))["tolerances"]["bushing_force"]
T_nom, T_min = lc["nom"]["T_Nmm"], lc["min"]["T_Nmm"]
F_nom, F_min = lc["nom"]["F_N"], lc["min"]["F_N"]
out["bushing"] = dict(static_Tz_Nmm=abs(M0[2]) * 1e3, static_Fz_N=abs(F0[2]), run_Tz_Nmm=worst["Tz"][0] * 1e3,
                      run_Fz_N=worst["Fz"][0], run_Mbend_Nmm=worst["Mb"][0] * 1e3, slip_T_nom_Nmm=T_nom,
                      slip_T_min_Nmm=T_min, slide_F_nom_N=F_nom, slide_F_min_N=F_min, cases=n,
                      tags=dict(Tz=worst["Tz"][1], Fz=worst["Fz"][1]))

# rotation lock (pin at the end of the 15 mm crank in a PETG hole): the running twist goes into the pin
T_run = worst["Tz"][0]
F_pin = T_run / (geom.LOCK["r"] * 1e-3)
engaged = geom.LOCK["pin"] / 2 * 1e-3                      # pin half way in (height adjustment +-)
p_pin = F_pin / (geom.WIRE_D * 1e-3 * engaged)
S_bear = PETG["S_bear"].v * PETG["kT_40C"].v * stc.K_SUSTAINED / GAMMA_M_PRINT.v
s_crank = T_run / (math.pi * (geom.WIRE_D * 1e-3) ** 3 / 32)
out["lock"] = dict(F_pin_N=F_pin, p_hole_MPa=p_pin / 1e6, SF_hole=S_bear / p_pin, crank_stress_MPa=s_crank / 1e6,
                   SF_crank=0.75 * wire_sut(geom.WIRE_D) / s_crank)

# ---------------------------------------------------------------- 2. hook wire stress
d = geom.WIRE_D * 1e-3
Sut = wire_sut(geom.WIRE_D)
S_bend = 0.75 * Sut              # [STD] Shigley: music wire, bending set limit ~0.75-0.78 Sut (torsion springs)
S_tors = 0.45 * Sut              # [STD] torsional yield
Z = math.pi * d ** 3 / 32
E = WIRE["E"].v
# in use: worst bending moment at the bushing exit (the most loaded section: every hook force acts on it)
s_use = worst["Mb"][0] / Z
# donning: open the leg at the pinna point by delta (outwards +z and rearwards -x); stress along the wire from the
# bushing to the pinna point, unit-load method on the built-in wire (contacts off)
i_p = ct.nearest(P, pp)
Cw = ct.wire_compliance(P, i_plate, i_p, geom.WIRE_D)
Ct = Cw[:3, :3]


def stress_for_tip(delta_vec):
    F = np.linalg.solve(Ct, delta_vec)
    smax, at = 0.0, None
    lo, hi = sorted((i_plate, i_p))
    for k in range(lo, hi + 1):
        M = np.cross(P[i_p] - P[k], F)
        ax = (P[min(k + 1, hi)] - P[max(k - 1, lo)]); ax = ax / (np.linalg.norm(ax) + 1e-12)
        Mt = abs(M @ ax); Mb = np.linalg.norm(M - (M @ ax) * ax)
        s = math.hypot(Mb / Z, math.sqrt(3) * Mt / (2 * Z))          # von Mises, bending + torsion
        if s > smax:
            smax, at = s, lab[k]
    return smax, at, F


don = {}
for name, dv in (("outwards (+z)", [0, 0, 1.0]), ("rearwards (-x)", [-1.0, 0, 0]), ("down (-y)", [0, -1.0, 0])):
    s1, at, F1 = stress_for_tip(np.array(dv) * 1e-3)
    don[name] = dict(stress_per_mm_MPa=s1 / 1e6, at=at, force_per_mm_N=float(np.linalg.norm(F1)),
                     opening_at_set_mm=S_bend / s1)
out["wire"] = dict(Sut_MPa=Sut / 1e6, S_bend_MPa=S_bend / 1e6, use_worst_MPa=s_use / 1e6, SF_use=S_bend / max(s_use, 1),
                   donning=don)

# ---------------------------------------------------------------- 3. bayonet lugs
kT40 = PETG["kT_40C"].v
S_xy = PETG["S_xy"].v * kT40 / GAMMA_M_PRINT.v
S_sh = PETG["S_shear_il"].v * kT40 / GAMMA_M_PRINT.v
w = geom.LUG_W * 1e-3
t_lug = (geom.LUG_H - 0.15) * 1e-3          # ring lug (as drawn)
t_lip = (geom.RING_T - geom.LUG_H - 0.15) * 1e-3   # shell lip over the groove
a = 0.5 * geom.LUG_DEPTH * 1e-3             # lever: load at mid engagement
cap = []
for nm, t in (("ring lug", t_lug), ("shell lip", t_lip)):
    F_b = S_xy * w * t ** 2 / (6 * a)       # bending at the root
    F_s = S_sh * w * t / 1.5                # shear at the root (parabolic, 1.5 x mean)
    cap.append((nm, min(F_b, F_s), "bending" if F_b < F_s else "shear"))
F_lug = min(c[1] for c in cap) * geom.LUG_N
lim = min(cap, key=lambda c: c[1])
bay = {}
for D in geom.SIZES:
    m = (geom.DRIVERS[D]["mass"] + 1.2) * 1e-3      # driver + adapter
    bay[str(D)] = dict(capacity_N=F_lug, g_held=F_lug / (m * 9.81))
out["bayonet"] = dict(per_size=bay, limiting=f"{lim[0]} ({lim[2]})", per_lug_N=lim[1])

# ---------------------------------------------------------------- 4. eye clip
# band force at the eye: preload P_neck + stiffness x opening when putting on (head width +-15 mm [A])
dz = nb.design(V["neck"])
F_eye_use = V["neck"] + dz["k_side"] * 0.015
F_eye_tug = 3.0                    # [A] cable snag the band carries before the plug pulls out (2-pin retention 2-5 N)
# band channel in the back (refinement 2026-10-01, replaces the snap-on eye clip): the band pull presses the sleeve
# into the channel bottom (bearing on the trough over the embedded length); the keyhole lips (shell back, 1.2 mm) only
# keep the sleeve in: 0.4 mm interference on a 1 mm silicone wall, taken almost entirely by the silicone.
from umeh2.materials import SILICONE
L_ch = abs(geom.neck_path()[geom.neck_embedded()][0]) * 1e-3
p_tr = max(F_eye_use, F_eye_tug) / (geom.NECK_SLEEVE * 1e-3 * L_ch)
S_br = PETG["S_bear"].v * kT40 * stc.K_SUSTAINED / GAMMA_M_PRINT.v
# lip: cantilever 1.2 mm thick, 1.5 mm high, along the channel; silicone squeeze 0.2 mm per side over a 1 mm wall
k_sil = SILICONE["E"].v * (L_ch * 1.0e-3) / 1.0e-3
F_lip = k_sil * 0.2e-3
s_lip = 6 * F_lip * 1.5e-3 / (L_ch * (geom.WALL * 1e-3) ** 2)
S_z = PETG["S_z"].v * kT40 / GAMMA_M_PRINT.v
# pull-out along the channel is blocked by the bent wire end in its blind hole (pin bearing)
p_pin = F_eye_tug / (geom.NECK_WIRE_D * 1e-3 * geom.NECK_PIN * 1e-3)
out["band_channel"] = dict(F_use_N=F_eye_use, F_tug_N=F_eye_tug, trough_bearing_MPa=p_tr / 1e6, SF_trough=S_br / p_tr,
                           lip_force_N=F_lip, lip_stress_MPa=s_lip / 1e6, SF_lip=S_z * stc.K_SUSTAINED / s_lip,
                           pin_bearing_MPa=p_pin / 1e6, SF_pin=S_br / p_pin)

# ---------------------------------------------------------------- 5. flange plate under the pad lip
# worst pad force (treadmill) taken at the rim as a ring load on an annular plate fixed at the cup (outer edge free):
# Roark case, approximated as a radial cantilever strip of unit width: M = q (R_f - R_cup), q = F / (2 pi R_f)
F_pad = 1.69e3 * math.pi * ((geom.PAD["od"] / 2e3) ** 2 - (geom.PAD["id"] / 2e3) ** 2) * geom.PAD["contact_frac"]  # 1.69 kPa worst mean
R_f = geom.FLANGE_OD / 2e3
R_cup = (geom.POCKET_R + geom.HUB_WALL) * 1e-3 + geom.POCKET_E * 1e-3
q = F_pad / (2 * math.pi * R_f)
M_ = q * (R_f - R_cup)
s_pl = 6 * M_ / (geom.PLATE_T * 1e-3) ** 2
out["flange"] = dict(F_pad_N=F_pad, stress_MPa=s_pl / 1e6, SF=S_xy * stc.K_SUSTAINED / s_pl)


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


json.dump(_clean(out), open(os.path.join(RESULTS, "strength.json"), "w"), indent=1)
b = out["bushing"]
print(f"bushing: static twist {b['static_Tz_Nmm']:.1f} N mm, running worst {b['run_Tz_Nmm']:.1f} N mm vs slip torque nom "
      f"{b['slip_T_nom_Nmm']:.1f} (worst print {b['slip_T_min_Nmm']:.1f}); axial static {b['static_Fz_N']:.2f} N, running "
      f"{b['run_Fz_N']:.2f} N vs slide force nom {b['slide_F_nom_N']:.1f} (worst print {b['slide_F_min_N']:.1f}) N; "
      f"bending at the exit {b['run_Mbend_Nmm']:.0f} N mm")
lk = out["lock"]
print(f"rotation lock: pin force {lk['F_pin_N']:.1f} N, hole bearing {lk['p_hole_MPa']:.2f} MPa (SF {lk['SF_hole']:.1f}), crank {lk['crank_stress_MPa']:.0f} MPa (SF {lk['SF_crank']:.1f})")
wv = out["wire"]
print(f"wire: Sut {wv['Sut_MPa']:.0f} MPa, set limit {wv['S_bend_MPa']:.0f}; in use worst {wv['use_worst_MPa']:.0f} MPa (SF {wv['SF_use']:.1f})")
for k, x in wv["donning"].items():
    print(f"  open the leg {k}: {x['stress_per_mm_MPa']:.0f} MPa/mm at {x['at']}, {x['force_per_mm_N']:.2f} N/mm -> set at {x['opening_at_set_mm']:.1f} mm")
print(f"bayonet: limiting {out['bayonet']['limiting']}, {out['bayonet']['per_lug_N']:.0f} N per lug; held deceleration "
      + ", ".join(f"D{D} {x['g_held']:.0f} g" for D, x in out["bayonet"]["per_size"].items()))
e = out["band_channel"]
print(f"band channel: use {e['F_use_N']:.2f} N, tug {e['F_tug_N']:.1f} N; trough {e['trough_bearing_MPa']:.2f} MPa (SF {e['SF_trough']:.0f}); "
      f"lips {e['lip_stress_MPa']:.2f} MPa (SF {e['SF_lip']:.0f}); wire-end pin {e['pin_bearing_MPa']:.2f} MPa (SF {e['SF_pin']:.1f})")
f_ = out["flange"]
print(f"flange plate: pad {f_['F_pad_N']:.1f} N, {f_['stress_MPa']:.2f} MPa, SF sustained {f_['SF']:.0f}")
