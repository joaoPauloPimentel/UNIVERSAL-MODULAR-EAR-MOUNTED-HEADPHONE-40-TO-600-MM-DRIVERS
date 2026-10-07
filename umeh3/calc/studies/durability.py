# Study (2026-10-01): durability of model A final (AF). Closed-form / Ritz; NO FEA. Four checks:
#  1. Drop from 1.0 m (and 0.75 m, a table) onto a hard floor, per driver size:
#     a. face down onto the pad: slow-rebound foam ring (plateau + densification, impact-rate factor [A]) -> peak
#        deceleration -> driver inertia on the bayonet lugs (strength.py capacity);
#     b. back down: the band's eye clip is the highest point of the back, so it lands on the clip and loads the
#        middle of the cup's flat back (clamped circular plate, radius = R_HUB - CUP_ROUND) -> von Karman Ritz model
#        (bending + membrane) -> energy the back takes before the in-layer strength / before cracking [A],
#        compared with the impact energy; then the driver inertia on the rear shoulder.
#  2. Neckband wire when it is opened to go over the head (umeh2.linkspring: yield on donning, Goodman fatigue over
#     1e4 donnings), for the band the contact model uses (neckband.design) and for the 1.6 mm / 2-coil one in geom.
#  3. Fatigue per stride (1e7 strides [A]): hook wire at the bushing exit and at the crank bends, lock hole, band.
#  4. Heat and relaxation: TPU flap preload after compression set (hot car), driver rattle margin; TPU bushing
#     after relaxation; PETG at 55-70 C (car), Tg.
# python3 studies/durability.py -> results/durability.json + printed summary
import sys, os, json, math
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import umeh3
from umeh3 import geom, neckband as nb, RESULTS
from umeh2.materials import PETG, TPU, WIRE, music_wire_Sut as wire_sut, GAMMA_M_PRINT, G
from umeh2 import linkspring as ls

geom.apply(os.environ.get("UMEH_VAR", "AF"))
out = {}
st = json.load(open(os.path.join(RESULTS, "strength" + ("" if geom.VARIANT == "AF" else "_" + geom.VARIANT) + ".json")))
mass = {D: json.load(open(os.path.join(RESULTS, f"mass_{geom.VARIANT}_{D}.json")))["M"] for D in (40, 50, 60)}   # kg, incl. band share

# ================================================================ 1. drop
H = (0.75, 1.0)            # m: table height, held at chest / putting on
EPS_CRACK = 0.04           # [A] in-layer strain at break of printed PETG (bulk 50-150 %, printed walls 3-8 %)

# ---- 1a face down onto the pad
A_pad = math.pi * ((geom.PAD["od"] / 2e3) ** 2 - (geom.PAD["id"] / 2e3) ** 2) * 0.9      # flat floor: most of the ring
T_pad = geom.PAD["t"] * 1e-3
SIG_P = 2.0e3              # [A] plateau stress of slow-rebound PU (CLD 40 % of 1.5-3 kPa)
EPS_D = 0.85               # [A] densification strain (50 kg/m3 foam)


def foam_sigma(e, kr):
    ey = SIG_P / geom.PAD["E_foam"]
    if e < ey:
        return kr * geom.PAD["E_foam"] * e
    return kr * SIG_P * ((EPS_D - ey) / max(EPS_D - e, 1e-4)) ** 2


def pad_drop(m, h, kr):
    E = m * G * h
    es = np.linspace(0, EPS_D - 1e-3, 20000)
    sg = np.array([foam_sigma(e, kr) for e in es])
    U = np.concatenate([[0], np.cumsum(0.5 * (sg[1:] + sg[:-1]) * np.diff(es))]) * A_pad * T_pad
    i = int(np.searchsorted(U, E))
    if i >= len(es):
        return dict(eps=float(es[-1]), F_N=float(sg[-1] * A_pad), a_g=float(sg[-1] * A_pad / m / G), bottomed=True)
    return dict(eps=float(es[i]), F_N=float(sg[i] * A_pad), a_g=float(sg[i] * A_pad / m / G), bottomed=False)


face = {}
for D in (40, 50, 60):
    m = mass[D]
    cap_g = st["bayonet"]["per_size"][str(D)]["g_held"]
    for kr in (1.0, 3.0):          # [A] impact-rate stiffening of viscoelastic foam (1 = quasi-static)
        for h in H:
            r = pad_drop(m, h, kr)
            r["SF_bayonet"] = cap_g / r["a_g"]
            face[f"D{D}_h{h}_rate{kr:g}"] = r
out["drop_face"] = face

# ---- 1b back down onto the eye clip: clamped circular plate, central load over the clip foot
a_pl = (geom.POCKET_R + geom.HUB_WALL - geom.CUP_ROUND) * 1e-3
R0 = 7.0e-3                # clip foot as an equivalent disc (obround 11 x 20 mm)
E_p, nu = PETG["E_xy"].v, PETG["nu"].v
S_imp = PETG["S_xy"].v     # short event: characteristic in-layer strength, no sustained / temperature factor
rr = np.linspace(1e-6, 1.0, 801)            # rho = r / a


def ritz_plate(t, a=a_pl, r0=R0):
    """von Karman Ritz: w = w0 (1 - rho^2)^2 ; u = a rho (1 - rho)(c1 + c2 rho). Returns w0 grid, load, energy,
    peak surface stress (bending corrected to the Roark local value for a load over r0) and strain."""
    D = E_p * t ** 3 / (12 * (1 - nu ** 2))
    r = rr * a
    phi = (1 - rr ** 2) ** 2
    dphi = -4 * rr * (1 - rr ** 2) / a
    d2phi = (-4 + 12 * rr ** 2) / a ** 2
    Ub1 = math.pi * D * np.trapezoid(((d2phi + dphi / r) ** 2 - 2 * (1 - nu) * d2phi * dphi / r) * r, r)
    # u basis
    g1 = a * rr * (1 - rr); g2 = a * rr ** 2 * (1 - rr)
    dg1 = (1 - 2 * rr); dg2 = (2 * rr - 3 * rr ** 2)
    Cm = math.pi * E_p * t / (1 - nu ** 2)

    def membrane(w0):
        q = 0.5 * (w0 * dphi) ** 2
        # energy quadratic in c: er = c.dg + q, et = c.g / r
        Gr = np.vstack([dg1, dg2]); Gt = np.vstack([g1 / r, g2 / r])
        K = np.zeros((2, 2)); f = np.zeros(2)
        for i in range(2):
            for j in range(2):
                K[i, j] = Cm * np.trapezoid((Gr[i] * Gr[j] + Gt[i] * Gt[j] + nu * (Gr[i] * Gt[j] + Gt[i] * Gr[j])) * r, r)
            f[i] = Cm * np.trapezoid((2 * q * Gr[i] + 2 * nu * q * Gt[i]) * r, r) / 2
        c = -np.linalg.solve(K, f)
        er = c @ Gr + q; et = c @ Gt
        Um = Cm * np.trapezoid((er ** 2 + et ** 2 + 2 * nu * er * et) * r, r)
        return Um, er, et
    # load: mean deflection under the foot
    wbar = np.trapezoid(phi[rr <= r0 / a] * r[rr <= r0 / a], r[rr <= r0 / a]) / (0.5 * r0 ** 2)
    # Roark local correction: centre bending stress of a clamped plate, load over r0 (linear) vs the Ritz value
    r0p = math.sqrt(1.6 * r0 ** 2 + t ** 2) - 0.675 * t if r0 < 1.7 * t else r0
    w0s = np.linspace(1e-6, 6 * t, 400)
    rows = []
    U_prev, w_prev = 0.0, 0.0
    for w0 in w0s:
        Um, er, et = membrane(w0)
        U = Ub1 * w0 ** 2 + Um
        rows.append((w0, U, er, et))
    W = np.array([x[0] for x in rows]); U = np.array([x[1] for x in rows])
    P = np.gradient(U, W) / wbar
    # stresses: Ritz bending at the centre and the edge, membrane from er/et; the centre bending is scaled so that at
    # small w it equals the Roark local value under the actual load P
    k_lin = P[1] / W[1]
    sb_c_ritz = lambda w0: 6 * D * (1 + nu) * 4 * w0 / a ** 2 / t ** 2
    sb_e_ritz = lambda w0: 6 * D * 8 * w0 / a ** 2 / t ** 2
    corr = (3 / (2 * math.pi * t ** 2)) * ((1 + nu) * math.log(a / r0p)) * k_lin * W[1] / sb_c_ritz(W[1])
    corr_e = (3 / (2 * math.pi * t ** 2)) * (1 - r0 ** 2 / (2 * a ** 2)) * k_lin * W[1] / sb_e_ritz(W[1])
    S = []
    for (w0, Ui, er, et) in rows:
        sm_c = E_p / (1 - nu ** 2) * (er[0] + nu * et[0]); sm_e = E_p / (1 - nu ** 2) * (er[-1] + nu * et[-1])
        S.append(max(abs(corr * sb_c_ritz(w0)) + sm_c, abs(corr_e * sb_e_ritz(w0)) + abs(sm_e)))
    S = np.array(S)
    return dict(w=W, U=U, P=P, S=S, k_lin=k_lin, corr=corr)


def back_drop(t):
    rp = ritz_plate(t)
    U_y = float(np.interp(S_imp, rp["S"], rp["U"]))                       # first in-layer yield (no mark)
    U_c = float(np.interp(E_p * EPS_CRACK, rp["S"], rp["U"]))             # strain at break [A] (elastic estimate)
    return rp, U_y, U_c


M_EFF = 0.85               # [A] share of the module mass whose motion the clip contact stops (CoM almost over the clip)
backs = {}
for t in (geom.WALL, 1.6, 2.0):
    rp, U_y, U_c = back_drop(t * 1e-3)
    res = dict(t_mm=t, E_no_mark_J=U_y, E_crack_J=U_c, k_lin_N_per_mm=rp["k_lin"] * 1e-3)
    for D in (40, 50, 60):
        for h in H:
            E_i = M_EFF * mass[D] * G * h
            i = int(np.searchsorted(rp["U"], E_i))
            P_pk = float(rp["P"][min(i, len(rp["P"]) - 1)])
            a_g = P_pk / (mass[D] * G)
            res[f"D{D}_h{h}"] = dict(E_J=E_i, F_N=P_pk, defl_mm=float(rp["w"][min(i, len(rp["w"]) - 1)] * 1e3), a_g=a_g,
                                    ratio_no_mark=U_y / E_i, ratio_crack=U_c / E_i)
    backs[f"t{t}"] = res
out["drop_back"] = backs

# ---- 1c refined back (2026-10-01): no clip on the back; the band's silicone sleeve lies in a channel, 1.4 mm proud.
# Back-down: the sleeve squeezes first (soft line contact along the channel), then the whole flat back meets the floor
# (the floor carries the back; the cup walls take the module's inertia in compression). Tilted: the rounded rim edge
# lands first -> local shell bending at the corner (Reissner point load on a shell, R_eff = sqrt(CUP_ROUND R_HUB),
# load spread over the plastic contact patch [A]).
from umeh2.materials import SILICONE
proud = geom.NECK_SLEEVE / 2 + geom.NECK_EYE_Z
L_ch = geom.neck_path()[geom.neck_embedded()][0] * -1e-3            # channel length from the axis (approx)
k_sl = SILICONE["E"].v * (L_ch * 2.5e-3) / 1.0e-3 * 2.0             # 1 mm wall, ~2.5 mm wide strip, x2 bulge-free [A]
E_sl = 0.5 * k_sl * (proud * 1e-3) ** 2
F_sl = k_sl * proud * 1e-3
# Tilted landings on the rounded rim: an elastic closed-form (Reissner point load on the shell) gives strains of 20-30 %,
# far outside its own validity (deflection >> t, PETG yields and dents). It cannot say whether the rim dents or cracks,
# so it is not reported: the drop test on a printed shell decides (report, open items).
out["drop_back_refined"] = dict(sleeve_proud_mm=proud, sleeve_k_N_per_mm=k_sl * 1e-3, sleeve_energy_J=E_sl, sleeve_force_N=F_sl,
                                flat_landing="floor carries the back; walls in compression: 2 pi R t S = %.0f N capacity" %
                                (2 * math.pi * (geom.POCKET_R + geom.HUB_WALL) * 1e-3 * geom.WALL * 1e-3 * S_imp),
                                corner="not computable in closed form; physical drop test")

# ---- rear shoulder: driver inertia (back-down drop) on the 1.2 mm shoulder ring, cantilever from the hub wall
L_sh = 2.0e-3              # lever: adapter back lip bears ~2 mm in from the hub wall [A]
r_sh = (geom.POCKET_R - 2.0) * 1e-3
t_sh = geom.SHOULDER_T * 1e-3
sh = {}
for D in (40, 50, 60):
    m_d = (geom.DRIVERS[D]["mass"] + 1.2) * 1e-3
    a_g = backs[f"t{geom.WALL}"][f"D{D}_h1.0"]["a_g"]
    F = m_d * a_g * G
    s = 6 * (F / (2 * math.pi * r_sh)) * L_sh / t_sh ** 2
    sh[str(D)] = dict(a_g=a_g, F_N=F, stress_MPa=s / 1e6, SF=S_imp / s)
out["drop_shoulder"] = sh

# ================================================================ 2. neckband on donning
nbd = {}
p = nb.path(nb.eye_point())
for name, (d, n) in (("in the contact model (neckband.design)", (nb.design(2.0)["d_mm"], nb.design(2.0)["n_coil"])),
                     ("geom / CAD note (1.6 mm, 2 coils)", (1.6, 2))):
    r = ls.link_design(d, 2.0, n, path=p)
    nbd[name] = dict(d_mm=d, n_coil=n, k_side_N_per_m=r["k_side"], P_min=r["P_min"], P_max=r["P_max"], P_don=r["P_don"],
                     sigma_don_MPa=r["sigma_don"] / 1e6, Sy_MPa=r["Sy"] / 1e6, SF_yield_don=r["SF_yield"],
                     SF_fatigue_1e4_don=r["SF_fatigue"], mass_g=r["mass_g"], ok=r["ok"])
nbd["spread_to_yield_mm_per_side"] = None
# how far each side can be pulled open before the band takes a set (stress linear in P)
dd = nb.design(2.0)
P_y = dd["P_don"] * dd["SF_yield"]
nbd["spread_to_yield_mm_per_side"] = (P_y - dd["P_max"]) / dd["k_side"] * 1e3 + ls.DON_EXTRA * 1e3 * 0
out["neckband"] = nbd

# ================================================================ 3. fatigue per stride
N_STRIDE = 1e7             # [A] 5 years, 3-4 runs a week, ~6000 strides a run, + walking
Sut = wire_sut(geom.WIRE_D)
Se_w = WIRE["Se_bend_ratio"].v * Sut          # fully reversed endurance (>1e7), unpeened, conservative [A]
KF_BEND = 1.3              # [A] cold-bent corner: residual stress + surface damage
s_run = st["wire"]["use_worst_MPa"] * 1e6     # worst treadmill case at the bushing exit
fat = {}
for nm, smax, kf in (("hook wire at the bushing exit", s_run, 1.0), ("hook crank bends (lock)", st["lock"]["crank_stress_MPa"] * 1e6, KF_BEND)):
    sa = kf * smax / 2; sm = kf * smax / 2       # 0 -> max every stride (conservative: the static part is ignored)
    n = 1 / (sa / Se_w + sm / Sut)
    fat[nm] = dict(s_max_MPa=smax / 1e6, Kf=kf, s_a_MPa=sa / 1e6, s_m_MPa=sm / 1e6, Se_MPa=Se_w / 1e6, SF_goodman=n)
# printed PETG lock hole: bearing pressure 0 -> max each stride, against the 1e7 endurance of printed PETG
S_fat_petg = PETG["fat_ratio"].v * PETG["S_bear"].v * PETG["kT_40C"].v / GAMMA_M_PRINT.v
p_hole = st["lock"]["p_hole_MPa"] * 1e6
fat["lock hole (PETG)"] = dict(p_max_MPa=p_hole / 1e6, S_fat_MPa=S_fat_petg / 1e6, SF=S_fat_petg / p_hole)
# eye clip: band pull changes each stride by k_side x eye motion (~1 mm [A]) on top of the preload
dF = dd["k_side"] * 1e-3
fat["band channel (PETG)"] = dict(dF_per_stride_N=dF, note="0.1 N swing pressing the sleeve into the channel; negligible")
# band wire: stress swing per stride from the same +-1 mm
s_per_N = dd["sigma_worn"] / dd["P_max"]
sa_b = s_per_N * dF / 2; sm_b = dd["sigma_worn"]
fat["neckband wire"] = dict(s_a_MPa=sa_b / 1e6, s_m_MPa=sm_b / 1e6, SF_goodman=1 / (sa_b / (WIRE["Se_bend_ratio"].v * dd["Sut"]) + sm_b / dd["Sut"]))
out["fatigue"] = fat

# ================================================================ 4. heat and relaxation
# 4a TPU adapter flap: conical annulus 0.8 mm, 3 mm wide, at r ~ POCKET_R - 1.5; ring strips as cantilevers
t_f, L_f = 0.8e-3, 3.0e-3
r_f = (geom.POCKET_R - 1.5) * 1e-3
k_flap = 3 * TPU["E"].v * (2 * math.pi * r_f * t_f ** 3 / 12) / L_f ** 3
sq = json.load(open(os.path.join(RESULTS, "light_checks" + ("" if geom.VARIANT == "AF" else "_" + geom.VARIANT) + ".json")))["tolerances"]["squeeze_60"]
heat = {}
for nm, set_ in (("new", 0.0), ("after years at body temperature [A] 10 %", 0.10), ("after a hot car, 70 C (ISO 815 22 h) 25 %", 0.25),
                 ("both", 0.33)):
    for D in (40, 60):
        m_d = (geom.DRIVERS[D]["mass"] + 1.2) * 1e-3
        F_min = k_flap * sq["mc_p0135"] * 1e-3 * (1 - set_)
        F_nom = k_flap * geom.ADAPTER_SQ * 1e-3 * (1 - set_)
        # axial = across the head: running 0.4 g, a hard jolt 3 g
        heat[f"flap {nm} D{D}"] = dict(F_min_print_N=F_min, F_nom_N=F_nom, rattle_g_min_print=F_min / (m_d * G),
                                       rattle_g_nom=F_nom / (m_d * G))
# 4b bushing (height only, the pin holds the rotation): relaxed by 33 %
bf = json.load(open(os.path.join(RESULTS, "light_checks" + ("" if geom.VARIANT == "AF" else "_" + geom.VARIANT) + ".json")))["tolerances"]["bushing_force"]
heat["bushing slide force after 33 % relaxation"] = dict(nom_N=bf["nom"]["F_N"] * 0.67, need_N=st["bushing"]["run_Fz_N"],
                                                       SF=bf["nom"]["F_N"] * 0.67 / st["bushing"]["run_Fz_N"])
# 4c PETG in a hot car: strength retention, worst sustained part (flange plate under the pad, lugs under flap preload)
F_flap_max = k_flap * sq["mc_p99865"] * 1e-3
heat["lugs under the flap preload, 55 C"] = dict(F_N=F_flap_max, capacity_N=st["bayonet"]["per_size"]["60"]["capacity_N"]
                                                * PETG["kT_55C"].v / PETG["kT_40C"].v * 0.5,
                                                SF=st["bayonet"]["per_size"]["60"]["capacity_N"] * PETG["kT_55C"].v / PETG["kT_40C"].v * 0.5 / F_flap_max)
heat["PETG Tg C"] = PETG["Tg"].v
out["heat"] = heat


def _clean(o):
    if isinstance(o, dict):
        return {str(k): _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_clean(v) for v in o]
    if isinstance(o, (np.floating, np.integer, np.bool_)):
        return o.item()
    return o


json.dump(_clean(out), open(os.path.join(RESULTS, "durability" + ("" if geom.VARIANT == "AF" else "_" + geom.VARIANT) + ".json"), "w"), indent=1)

print("== drop, face down on the pad")
for k, r in face.items():
    print(f"  {k}: foam strain {r['eps']:.2f}{' BOTTOMED' if r['bottomed'] else ''}, {r['F_N']:.0f} N, {r['a_g']:.0f} g, bayonet SF {r['SF_bayonet']:.1f}")
print("== drop, back down on the eye clip (flat back r %.1f mm)" % (a_pl * 1e3))
for k, r in backs.items():
    print(f"  t {r['t_mm']} mm: back takes {r['E_no_mark_J']:.2f} J before yield, {r['E_crack_J']:.2f} J before crack [A]; k {r['k_lin_N_per_mm']:.0f} N/mm")
    for D in (40, 50, 60):
        for h in H:
            x = r[f"D{D}_h{h}"]
            print(f"     D{D} h{h}: impact {x['E_J']:.2f} J, {x['F_N']:.0f} N, defl {x['defl_mm']:.1f} mm, {x['a_g']:.0f} g; "
                  f"no-mark x{x['ratio_no_mark']:.2f}, crack x{x['ratio_crack']:.2f}")
print(f"== refined back: sleeve {proud:.1f} mm proud" + " takes %.3f J at %.0f N, then flat landing; rim corner: drop test" % (E_sl, F_sl))
print("== shoulder (driver inertia, back-down 1 m, 1.2 mm back)")
for D, x in sh.items():
    print(f"  D{D}: {x['a_g']:.0f} g, {x['F_N']:.0f} N, {x['stress_MPa']:.0f} MPa, SF {x['SF']:.2f}")
print("== neckband donning")
for k, x in nbd.items():
    if isinstance(x, dict):
        print(f"  {k}: d {x['d_mm']} n {x['n_coil']}, k_side {x['k_side_N_per_m']:.0f} N/m, P {x['P_min']:.2f}-{x['P_max']:.2f} N, don {x['P_don']:.2f} N, "
              f"SF yield {x['SF_yield_don']:.2f}, fatigue {x['SF_fatigue_1e4_don']:.2f}, {x['mass_g']:.1f} g")
print(f"  spread to yield per side ~{nbd['spread_to_yield_mm_per_side']:.0f} mm beyond the largest head")
print("== fatigue per stride")
for k, x in fat.items():
    print("  ", k, {kk: round(v, 2) if isinstance(v, float) else v for kk, v in x.items()})
print("== heat / relaxation")
for k, x in heat.items():
    print("  ", k, {kk: round(v, 2) if isinstance(v, float) else v for kk, v in x.items()} if isinstance(x, dict) else x)
