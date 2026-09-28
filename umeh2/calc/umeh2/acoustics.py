"""
Acoustic model of the UMEH-2 module — LUMPED ELECTRO-MECHANO-ACOUSTIC
circuit plus closed-form radiation. NO acoustic FEM/BEM was run.

Validity: lumped elements need every cavity dimension < lambda/4
(cup ~ 60 mm -> ~1.4 kHz strict, ~{f_l:g} kHz usable); the piston/edge
radiation formulas hold to ~8 kHz [A]; above that the pinna and head (HRTF)
dominate and nothing here is claimed. Everything above {f_l:g} kHz is labelled
"indicative".

Driver (per size): Thiele/Small values are REPRESENTATIVE ASSUMPTIONS [A]
(no manufacturer data available). Replace them with measured values
(impedance sweep, added-mass method, see report) and re-run.

Circuit (impedance analogy, SI):
  electrical   Ze  = Re + j w Le
  mechanical   Zm  = Rms + j w Mms + 1/(j w Cms)
  acoustic     Z_F (front load) and Z_B (rear load) seen by the diaphragm,
               reflected as Sd^2 (Z_F + Z_B)
  diaphragm velocity   u = Bl e / [ Ze (Zm + Sd^2 (Z_F + Z_B)) + Bl^2 ]
  volume velocity      U = Sd u
Front load, OPEN (off-ear): radiation impedance of a baffled piston
  Z_rad = rho c / S [ 1 - J1(2ka)/(ka) + j H1(2ka)/(ka) ]            (exact, Bessel/Struve)
  in series with the aperture tube (mass of the baffle hole incl. end corrections)
Front load, SEALED (seal-pad option): cavity compliance C_f = V_f/(rho c^2)
  in parallel with the leak (slit: mass + viscous resistance).
Rear load: cup volume compliance C_b = V_b/(rho c^2) in parallel with the
  outlet path (grille holes / vents: mass with end corrections, viscous
  resistance) in series with the felt resistance R_felt = sigma t / A.
Pressure at the ear (open front): on-axis piston near field
  p_F = rho c u [exp(-jkz) - exp(-jk sqrt(z^2 + a^2))]  x 2 (rigid head/pinna surface)
  z = aperture exit plane to the ear-canal entrance (ear_distance: CAD standoff
  and module face, mean pinna protrusion minus concha depth [A/LIT])
minus the rear wave (monopole of volume velocity U_out at the grille)
travelling around the module edge (path L_r) with an edge-diffraction
factor D = 1/sqrt(1 + (k r_edge)^2) per edge [estimate].
"""
import math
import numpy as np
from scipy.special import j1, struve
from .materials import RHO_AIR, C_AIR, MU_AIR, P_REF, ACOUSTIC_MAT
from . import design as dz

RHO, C = RHO_AIR, C_AIR
F = np.logspace(math.log10(20), math.log10(20000), 400)
F_LUMPED = 3.0e3     # Hz: upper limit of the lumped model as used ("usable", see the module docstring); above it: indicative
V_PINNA = 10e-6      # [A] m3 of the sealed front cavity taken up by the pinna (seal-pad option)
__doc__ = __doc__.format(f_l=F_LUMPED / 1e3)


def ear_distance(d, des):
    """Aperture exit plane -> ear-canal entrance plane on the module axis (m). The module head face stands
    standoff + z_mod0 off the skin (CAD); the canal entrance lies concha_depth under the pinna surface, which stands
    pinna_protrusion_mean off the skin (design.ANTHRO [A/LIT])."""
    a = dz.ANTHRO
    return (des["standoff"] + d["z_mod0"] - (a["pinna_protrusion_mean"] - a["concha_depth"])) * 1e-3


def sealed_front_volume(d, des):
    """Sealed front cavity of the seal-pad option (m3): skin -> ring head face inside the seal ID (the pad spans the
    standoff), plus the recess of the module head face in the ring bore (z_mod0), minus the pinna (V_PINNA [A])."""
    return (math.pi * (des["seal_id"] / 2e3) ** 2 * des["standoff"] * 1e-3
            + math.pi * (d["bore_d"] / 2e3) ** 2 * d["z_mod0"] * 1e-3 - V_PINNA)

# ------------------------------------------------------------------ drivers [A]
TS_ANCHOR = {40: dict(Mms=0.30e-3, Fs=120.0), 50: dict(Mms=0.45e-3, Fs=90.0), 60: dict(Mms=0.62e-3, Fs=70.0)}
QMS, QES, RE, LE = 2.0, 0.5, 30.0, 50e-6        # [A] typical dynamic headphone drivers
D_EFF_RATIO = 0.8    # [A] effective piston diameter / nominal D (includes half the surround)


def ts(D):
    """Representative T/S set [A]; 45 and 55 mm interpolated (Mms ~ D^2, Fs log-linear)."""
    if D in TS_ANCHOR:
        Mms, Fs = TS_ANCHOR[D]["Mms"], TS_ANCHOR[D]["Fs"]
    else:
        lo, hi = (40, 50) if D < 50 else (50, 60)
        t = (D - lo) / (hi - lo)
        Mms = TS_ANCHOR[lo]["Mms"] + t * (TS_ANCHOR[hi]["Mms"] - TS_ANCHOR[lo]["Mms"])
        Fs = math.exp(math.log(TS_ANCHOR[lo]["Fs"]) + t * (math.log(TS_ANCHOR[hi]["Fs"]) - math.log(TS_ANCHOR[lo]["Fs"])))
    a = D_EFF_RATIO * D / 2 * 1e-3
    Sd = math.pi * a ** 2
    ws = 2 * math.pi * Fs
    Cms = 1 / (ws ** 2 * Mms)
    Rms = ws * Mms / QMS
    Bl = math.sqrt(ws * Mms * RE / QES)
    Qts = QMS * QES / (QMS + QES)
    Vas = RHO * C ** 2 * Sd ** 2 * Cms
    return dict(D=D, a=a, Sd=Sd, Mms=Mms, Fs=Fs, Cms=Cms, Rms=Rms, Bl=Bl, Re=RE, Le=LE, Qms=QMS, Qes=QES, Qts=Qts, Vas=Vas)


# ------------------------------------------------------------------ elements
def z_rad_piston(a, f):
    k = 2 * math.pi * f / C
    x = 2 * k * a
    S = math.pi * a ** 2
    return RHO * C / S * (1 - 2 * j1(x) / x + 1j * 2 * struve(1, x) / x)


END_FLANGED = 0.85     # [STD] end correction / radius of a flanged tube end (8/3pi, the baffled-piston radiation mass)
END_UNFLANGED = 0.61   # [STD] end correction / radius of an unflanged tube end
AP_INNER = 0.5         # [A] share of the flanged end correction kept on the inner (mini-cavity) side of the chamfered aperture


def end_corrected(L, r, flanged_in=True, flanged_out=False):
    return L + (END_FLANGED if flanged_in else END_UNFLANGED) * r + (END_FLANGED if flanged_out else END_UNFLANGED) * r


def aperture_leff(t, a):
    """Effective length of the baffle aperture (radius a, plate thickness t): the inner end correction reduced to
    AP_INNER x END_FLANGED a (the chamfer and the nearby diaphragm shorten it) plus the outer END_FLANGED a, the
    radiation mass of the baffled piston that front_impedance_open carries in Z_rad."""
    return t + (AP_INNER + 1.0) * END_FLANGED * a


def tube(r, L, f, flanged_in=True, flanged_out=False, n=1):
    """n parallel short tubes: acoustic mass with end corrections + viscous (Poiseuille-like, wide-tube
    boundary layer) resistance. End corrections: END_FLANGED r flanged, END_UNFLANGED r unflanged [STD]."""
    w = 2 * math.pi * f
    Le_ = end_corrected(L, r, flanged_in, flanged_out)
    S = math.pi * r ** 2
    Ma = RHO * Le_ / S
    # low-frequency Poiseuille resistance, raised by the boundary-layer term at high f (Crandall)
    R_pois = 8 * MU_AIR * L / (math.pi * r ** 4)
    R_bl = (L + 2 * r) / (math.pi * r ** 3) * np.sqrt(2 * RHO * MU_AIR * w / 2)
    Z = (np.maximum(R_pois, R_bl) + 1j * w * Ma) / n
    return Z, Ma / n, Le_


def slit_leak(width, perimeter, depth, f):
    """Leak between a pad and the skin modelled as a thin slit (height h = width, length = depth
    through the pad land, span = perimeter): R = 12 mu L / (h^3 b), M = 1.2 rho L / (h b) [STD]."""
    w = 2 * math.pi * f
    R = 12 * MU_AIR * depth / (width ** 3 * perimeter)
    M = 1.2 * RHO * depth / (width * perimeter)
    return R + 1j * w * M


def compliance(V, f):
    return 1 / (1j * 2 * math.pi * f * V / (RHO * C ** 2))


def felt_R(sigma, t, A):
    return sigma * t / A


# ------------------------------------------------------------------ geometry from the CAD numbers
MOTOR_FILL = 0.85    # [A] share of the cylinder behind the driver rim (rear_d x depth) filled by the motor and basket
FIBRE_RHO = 1300.0   # [A] kg/m3, density of the felt fibre (polyester/wool 1.3-1.4 g/cm3)


def module_geometry(d, des, D):
    drv = dz.DRIVERS[D]
    cup_ri = d["cup_ri"] * 1e-3
    h_in = (d["cup_h"] - des["cup_end_t"] - des["clamp_depth"]) * 1e-3      # rim face -> inside of the cup end
    V_cup = math.pi * cup_ri ** 2 * h_in
    V_mag = math.pi * (drv["rear_d"] / 2e3) ** 2 * (drv["depth"] - drv["rim_t"]) * 1e-3 * MOTOR_FILL
    V_felt = d["felt_A"] * 1e-6 * des["felt_t"] * 1e-3 * (ACOUSTIC_MAT["felt_density"].v / FIBRE_RHO)   # fibre volume only
    V_boss = d.get("boss_in_bore_A", 0.0) * 1e-6 * (d["eye_ins_L"] + 1.0) * 1e-3    # link-eye boss inside the cup
    Vb = V_cup - V_mag - V_felt - V_boss
    # felt flow area: the felt disc (hole over the eye boss) minus its bonded PSA rim; the convergence of the flow
    # into the grille holes is not modelled (lower bound of the felt resistance)
    psa = des.get("felt_psa_w", 0.0)
    A_felt = (d["felt_A"] - math.pi * psa * (2 * d["cup_ri"] - psa)) * 1e-6
    # grille: hex pattern of holes on the cup end, same rule as CAD cup(): inside Ri - hole/2 - 0.8 and clear of the
    # eye boss by hole/2 + 0.8
    n_holes = 0
    if des["rear_type"] == "open":
        p = des["grille_pitch"]; Ri = d["cup_ri"]; hd = des["grille_hole"]
        ex, ey = des.get("link_x") or 0.0, des.get("link_y") or 0.0
        for i in range(-30, 31):
            for j in range(-30, 31):
                x = i * p + math.fmod(j, 2) * p / 2; y = j * p * 0.866
                if math.hypot(x, y) < Ri - hd / 2 - 0.8 and (des.get("link_mode") != "cup" or
                                                              math.hypot(x - ex, y - ey) > d["eye_boss_d"] / 2 + hd / 2 + 0.8):
                    n_holes += 1
    ap = d["aperture_d"] / 2 * 1e-3
    front_gap = 1.0e-3        # [A] diaphragm dome/surround to baffle aperture plane clearance at rest
    V_front = math.pi * (drv["front_open"] / 2e3) ** 2 * front_gap
    return dict(Vb=Vb, V_cup=V_cup, h_in=h_in, cup_ri=cup_ri, A_felt=A_felt, n_holes=n_holes, ap=ap,
                t_ap=des["baffle_front_t"] * 1e-3, V_front=V_front, R_mod=d["spig_d"] / 2e3,
                H_mod=(d["baffle_h"] + d["cup_h"]) * 1e-3)


def rear_impedance(g, des, f, felt_sigma=None, felt_t=None, rear_type=None, vent_n=None, vent_d=None):
    rear_type = rear_type or des["rear_type"]
    sig = felt_sigma if felt_sigma is not None else ACOUSTIC_MAT["felt_sigma"].v
    t = (felt_t if felt_t is not None else des["felt_t"]) * 1e-3
    Zc = compliance(g["Vb"], f)
    Rf = felt_R(sig, t, g["A_felt"]) if t > 0 else 0.0
    if rear_type == "open":
        Zo, _, _ = tube(des["grille_hole"] / 2e3, des["cup_end_t"] * 1e-3, f, True, False, n=max(g["n_holes"], 1))
    elif rear_type == "vented":
        Zo, _, _ = tube((vent_d or des["vent_d"]) / 2e3, des["cup_end_t"] * 1e-3, f, True, False, n=vent_n or des["vent_n"])
    else:
        Zo = np.full_like(f, 1e15, dtype=complex)
    Zpath = Rf + Zo
    ZB = Zc * Zpath / (Zc + Zpath)
    frac_out = Zc / (Zc + Zpath)          # share of the rear volume velocity that leaves through the path
    return ZB, frac_out, Rf


def front_impedance_open(g, T, f):
    Za = z_rad_piston(g["ap"], f)
    # aperture as a short, wide tube; the outer end correction is already inside Z_rad (its mass term),
    # so only the reduced inner correction (AP_INNER x END_FLANGED a, see aperture_leff) is added here
    w = 2 * math.pi * f
    Zt = 1j * w * RHO * (aperture_leff(g["t_ap"], g["ap"]) - END_FLANGED * g["ap"]) / (math.pi * g["ap"] ** 2)
    # front mini-cavity (diaphragm -> aperture) in parallel to the aperture path
    Zv = compliance(g["V_front"], f)
    Zser = Zt + Za
    return Zv * Zser / (Zv + Zser), Zv / (Zv + Zser)


def front_impedance_sealed(V_f, leak_w, leak_perim, leak_depth, f):
    Zc = compliance(V_f, f)
    Zl = slit_leak(leak_w, leak_perim, leak_depth, f)
    return Zc * Zl / (Zc + Zl)


def solve_driver(T, ZF, ZB, f, e=1.0):
    w = 2 * math.pi * f
    Ze = T["Re"] + 1j * w * T["Le"]
    Zm = T["Rms"] + 1j * w * T["Mms"] + 1 / (1j * w * T["Cms"])
    Zmt = Zm + T["Sd"] ** 2 * (ZF + ZB)
    u = T["Bl"] * e / (Ze * Zmt + T["Bl"] ** 2)
    Zin = Ze + T["Bl"] ** 2 / Zmt
    return u, Zin


def spl(p):
    return 20 * np.log10(np.abs(p) / math.sqrt(2) / P_REF + 1e-30)


def response_open(D, d, des, z_ear, f=F, felt_sigma=None, felt_t=None, rear_type=None, vent_n=None, vent_d=None,
                  aperture_d=None, head_factor=2.0):
    """SPL at the ear for 1 V (peak amplitude -> RMS in spl()) with an OPEN front."""
    T = ts(D)
    g = module_geometry(d, des, D)
    if aperture_d is not None:
        g["ap"] = aperture_d / 2e3
    ZF, frac_ap = front_impedance_open(g, T, f)
    ZB, frac_out, Rf = rear_impedance(g, des, f, felt_sigma, felt_t, rear_type, vent_n, vent_d)
    u, Zin = solve_driver(T, ZF, ZB, f)
    U = T["Sd"] * u
    k = 2 * math.pi * f / C
    a = g["ap"]
    u_ap = U * frac_ap / (math.pi * a ** 2)         # particle velocity in the aperture
    pF = RHO * C * u_ap * (np.exp(-1j * k * z_ear) - np.exp(-1j * k * np.sqrt(z_ear ** 2 + a ** 2))) * head_factor
    # rear wave: monopole of U_out at the back, path around the module edge to the ear (two edges)
    U_out = -U * frac_out
    L_r = g["R_mod"] + g["H_mod"] + math.hypot(g["R_mod"], z_ear)
    Dif = 1 / np.sqrt(1 + (k * g["R_mod"] / 2) ** 2)          # [estimate] per edge
    pB = 1j * 2 * math.pi * f * RHO * U_out / (4 * math.pi * L_r) * np.exp(-1j * k * L_r) * Dif ** 2 * head_factor
    return dict(f=f, p=pF + pB, pF=pF, pB=pB, Zin=Zin, u=u, T=T, g=g, Rf=Rf)


def response_sealed(D, d, des, V_f, leak_w, f=F, leak_depth=6e-3, **kw):
    T = ts(D)
    g = module_geometry(d, des, D)
    perim = math.pi * des["seal_id"] * 1e-3
    ZF = front_impedance_sealed(V_f, leak_w, perim, leak_depth, f)
    ZB, frac_out, Rf = rear_impedance(g, des, f, kw.get("felt_sigma"), kw.get("felt_t"), kw.get("rear_type"),
                                      kw.get("vent_n"), kw.get("vent_d"))
    u, Zin = solve_driver(T, ZF, ZB, f)
    U = T["Sd"] * u
    p = U * ZF            # pressure in the sealed front cavity (uniform below its first mode)
    return dict(f=f, p=p, Zin=Zin, T=T, g=g)


# ------------------------------------------------------------------ closed-box / Helmholtz / modes
def closed_box(T, Vb):
    alpha = T["Vas"] / Vb
    return dict(alpha=alpha, Qtc=T["Qts"] * math.sqrt(1 + alpha), Fc=T["Fs"] * math.sqrt(1 + alpha))


def helmholtz(V, r, L, n=1, flanged_in=True, flanged_out=False, L_eff=None):
    """Helmholtz resonance of volume V behind n tubes of radius r and length L (L_eff given: used as is)."""
    Le_ = end_corrected(L, r, flanged_in, flanged_out) if L_eff is None else L_eff
    S = n * math.pi * r ** 2
    return C / (2 * math.pi) * math.sqrt(S / (V * Le_)), Le_


def cavity_modes(radius, height):
    return dict(radial_11=1.841 * C / (2 * math.pi * radius), radial_01=3.832 * C / (2 * math.pi * radius),
                axial_1=C / (2 * height) if height > 0 else np.inf)
