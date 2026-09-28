"""
Additional UMEH-2 checks. Closed-form or from the support model; NO FEA / BEM was run.

 1. Cable: tug limit per pull direction (support-model bisection), plug insertion / removal at the
    socket while worn, anchor screws (heat-set insert pull-out with prying), clip-post bending and the
    anchor print orientation that follows from it.
 2. Driver isolation: TPU 95A rim gasket vs silicone rings of Shore 30/40/50A (Gent's E(Shore)).
 3. Seal pad (sealed-front option): material x height -> modulus, conformity to the head at the
    pressure the preload can spare, residual leak slit, bass loss vs a perfect seal.
 4. Weight-reduction options, each with the check it moves (mass from the CAD meshes in run_all).
 5. Contact stresses at every interface: Hertz where the geometry is Hertzian, Winkler (thin
    compliant layer) for the pads on soft tissue, bearing pressure under screw heads and on the
    serration flanks.
Source tags as elsewhere: [C] calculated, [A] assumption, [LIT] literature, [DS] data sheet.
"""
import math
import numpy as np
from .materials import PETG, TPU, SILICONE, SCREW, INSERT_PULLOUT, GAMMA_INSERT, NUT_FACTOR_K, NUT_FACTOR_K_RANGE, CABLE, WIRE, G, Val, ACOUSTIC_MAT
from . import support as sp, structure as st, acoustics as ac, dynamics as dy

# ---------------------------------------------------------------------------------------------- 1 cable
TUG_DIRS = {
    "down": (0, -1, 0), "down-out 45": (0, -0.7071, 0.7071), "down-in 45": (0, -0.7071, -0.7071),
    "down-fwd 45": (0.7071, -0.7071, 0), "down-back 45": (-0.7071, -0.7071, 0),
    "out (10 deg below horizontal)": (0, -0.1736, 0.9848), "fwd (10 deg below)": (0.9848, -0.1736, 0),
    "back (10 deg below)": (-0.9848, -0.1736, 0),
}
F_INSERT_PLUG = 10.0     # [A] N, 0.78 mm 2-pin plug insertion force, 5-10 N (take the upper end)
SOCKET_OFFSET = (-4.0, -5.0)   # socket centre: tab_r - 4 mm, standoff - 5 mm (massprops.hardware) [C from CAD]


def point_wrench(p, F):
    F = np.asarray(F, float)
    return np.r_[F, np.cross(p, F)]


TUG_F_HI = 40.0      # N, upper end of the tug-limit bisection (a tug above it is reported as ">= TUG_F_HI")


def tug_limits(model, d, des, W_st, F_hi=TUG_F_HI, n_bis=14, dirs=None):
    """Cable pull at the clip that the worn cradle can take before gross slip, per direction (bisection on
    the magnitude, precision F_hi / 2^n_bis). Also the minimum over a 60-point sphere of pull directions
    within 80 deg of straight down."""
    out = {}
    def limit(e):
        lo_, hi_ = 0.0, F_hi
        for _ in range(n_bis):
            mid = 0.5 * (lo_ + hi_)
            if model.solve(W_st + sp.cable_wrench(d, des, mid * e)[0])["ok"]:
                lo_ = mid
            else:
                hi_ = mid
        return lo_
    for k, e in (dirs or TUG_DIRS).items():
        e = np.asarray(e, float); e /= np.linalg.norm(e)
        out[k] = limit(e)
    sph = sp.cone(sp.fib_sphere(60), np.array([0, -1.0, 0]), 80)
    vals = [(limit(e), e) for e in sph]
    fmin, emin = min(vals, key=lambda v: v[0])
    return dict(named=out, sphere_min=fmin, sphere_min_dir=emin, n_sphere=len(sph))


def plug_at_socket(model, d, des, W_st):
    """Plug insertion (towards the head, -z) and removal (+z, at the upper retention 15 N) while worn."""
    a = math.radians(des["cable_a"])
    r = (d["tab_r"] + SOCKET_OFFSET[0]) * 1e-3
    p = np.array([r * math.cos(a), r * math.sin(a), (des["standoff"] + SOCKET_OFFSET[1]) * 1e-3])
    res = {}
    for k, F in (("insert (push towards head)", (0, 0, -F_INSERT_PLUG)), ("remove at 15 N (pull out)", (0, 0, 15.0)),
                 ("remove at 8 N nominal", (0, 0, CABLE["connector_retention"].v))):
        r_ = model.solve(W_st + point_wrench(p, F))
        res[k] = dict(F=F, held=bool(r_["ok"]),
                      Fn_min=(min(x["Fn"] for x in r_["contacts"] if x["name"] in sp.SKIN_PADS) if r_["ok"] else None))
    return res


def anchor_screws(d, des, F_design, n_dir=146):
    """Cable anchor: 2 screws (des['anchor_screw'], M3 in the Final) into heat-set inserts in the ring tab at
    cable_a. Cable force F at the clip, any direction. Per-screw tension = axial share + prying (moment about
    the tangential axis over the screw pitch, about the radial screw line over the anchor width), added to
    the creep-relaxed preload (joint factor Phi = 1, conservative). Insert design capacity = pull-out /
    gamma_insert."""
    size = des.get("anchor_screw") or des["arm_screw"]; torque = des.get("anchor_torque") or des["arm_torque"]
    pitch = d.get("anchor_ins_pitch", d["tab_ins_pitch"])
    s = SCREW[size]
    a = math.radians(des["cable_a"])
    er = np.array([math.cos(a), math.sin(a), 0]); et = np.array([-math.sin(a), math.cos(a), 0]); ez = np.array([0, 0, 1.0])
    p_c = (d["bar_r1"] + des["cable_od"] / 2 + 3) * er + (des["standoff"] - des["clip_post_L"] + 5 + des["clip_len"] / 2) * ez
    p_0 = (d["tab_r"] - pitch / 2) * er + des["standoff"] * ez
    # tightening scatter: pull-out is checked at the highest preload T/(K_min d) (K range [LIT]); the aged value
    # is the same preload after 3 years of PETG creep under the wave washer (structure.retained_preload)
    Fi = torque / (NUT_FACTOR_K.v * s["d"] * 1e-3)
    Fi_max = torque / (NUT_FACTOR_K_RANGE[0].v * s["d"] * 1e-3)
    Fi_min = torque / (NUT_FACTOR_K_RANGE[1].v * s["d"] * 1e-3)
    Fi_eff = st.retained_preload(Fi_max, size, des.get("arm_washer"))[0]
    worst = None
    for e in sp.fib_sphere(n_dir):
        F = F_design * e
        M = np.cross((p_c - p_0) * 1e-3, F)
        T = max(0.0, -F @ ez) / 2 + abs(M @ et) / (pitch * 1e-3) + abs(M @ er) / (d["tab_w"] * 1e-3)
        if worst is None or T > worst["T_ext"]:
            worst = dict(T_ext=T, dir=e, M=M)
    cap = INSERT_PULLOUT[size].v / GAMMA_INSERT.v
    worst.update(size=size, torque=torque, Fi=Fi, Fi_min=Fi_min, Fi_max=Fi_max, Fi_eff=Fi_eff,
                 F_screw_initial=Fi_max + worst["T_ext"], F_screw_aged=Fi_eff + worst["T_ext"],
                 capacity=cap, SF_initial=cap / (Fi_max + worst["T_ext"]), SF_aged=cap / (Fi_eff + worst["T_ext"]),
                 SF_initial_nominal=cap / (Fi + worst["T_ext"]), lever_mm=np.linalg.norm(p_c - p_0))
    return worst


PSA_PEEL = Val(300.0, "A", "acrylic PSA transfer tape, 90 deg peel on printed PETG >= 3 N/cm (datasheet values on "
                             "steel 5-10 N/cm; PETG has a lower surface energy) - confirm with the chosen tape")
P_REAR_MAX = Val(89.0, "A", "bound on the rear-cavity pressure amplitude: 130 dB SPL peak (63 Pa rms)")


def felt_bond(d, des, accel_g=5.0):
    """Rear felt disc bonded to the inside of the cup end by a PSA rim (width felt_psa_w). Loads that pull it off the
    cup end: its own inertia at accel_g and the rear-cavity pressure amplitude over its free area. Capacity: the rim
    peels from its inner edge all round, so capacity = peel strength x inner rim perimeter (peel is the weakest mode
    of a PSA joint; the shear capacity of the rim is far higher and is not credited)."""
    psa = des["felt_psa_w"]
    m = d["felt_A"] * 1e-6 * des["felt_t"] * 1e-3 * ACOUSTIC_MAT["felt_density"].v
    A_free = (d["felt_A"] - math.pi * psa * (2 * d["cup_ri"] - psa)) * 1e-6
    F_in = m * accel_g * G
    F_p = P_REAR_MAX.v * A_free
    L_peel = 2 * math.pi * (d["cup_ri"] - psa) * 1e-3
    cap = PSA_PEEL.v * L_peel
    return dict(m_felt=m, A_free=A_free, F_inertia=F_in, F_pressure=F_p, F=F_in + F_p, peel_len=L_peel, capacity=cap,
                SF=cap / (F_in + F_p), psa_w=psa, hole_d=d["felt_hole_d"])


def clip_post(d, des, F_design, temp=st.T_SERVICE):
    """Clip post of the cable anchor: cantilever b = tab_w (tangential) x h = clip_post_t (radial), from the
    anchor block (z = standoff - anchor_h) to the clip screw (z = standoff - clip_post_L + 5); the cable
    axis is offset radially by e = clip_post_t/2 + cable_od/2 + 3 mm from the post centreline.
    Printed ON ITS SIDE (tangential face on the bed): bending stress along the post is in-layer; transverse
    shear across the width and torsion shear load the interlayer planes. Printed upright, the same bending
    stress would act ACROSS the layers (S_z), and every shear stress on the cross-section (torsion and both
    transverse shears) would lie in a layer interface (S_il)."""
    b = d["tab_w"] * 1e-3; h = des["clip_post_t"] * 1e-3
    L = (des["clip_post_L"] - 5 - des["anchor_h"]) * 1e-3
    e = (des["clip_post_t"] / 2 + des["cable_od"] / 2 + 3) * 1e-3
    Kt = st.KT_FILLET
    S, Sil = st.strength("short", temp=temp)
    Sz = PETG["S_z"].v * st.kT(temp)
    rows = {}
    for k, (Fr, Ft, Fa) in {"radial": (F_design, 0, 0), "tangential": (0, F_design, 0), "axial (along post)": (0, 0, F_design)}.items():
        M_t = Fr * L + Fa * e                 # bending about the tangential axis (thin direction h)
        M_r = Ft * L                          # bending about the radial axis (wide direction b)
        T = Ft * e                            # torsion from the offset cable
        sig = Fa / (b * h) + Kt * (6 * M_t / (b * h ** 2) + 6 * M_r / (h * b ** 2))
        tau_T = T * (3 + 1.8 * h / b) / (b * h ** 2)
        tau_il = tau_T + 1.5 * Ft / (b * h)
        tau_up = tau_T + 1.5 * math.hypot(Fr, Ft) / (b * h)     # upright: all cross-section shear is interlayer
        rows[k] = dict(sigma=sig, tau_il=tau_il, tau_il_upright=tau_up, SF_side=min(S / sig, Sil / max(tau_il, 1)),
                       SF_upright=min(Sz / sig, Sil / max(tau_up, 1)))
    return dict(L=L, e=e, b=b, h=h, F=F_design, cases=rows,
                SF_side=min(r["SF_side"] for r in rows.values()), SF_upright=min(r["SF_upright"] for r in rows.values()))


# ---------------------------------------------------------------------------------------------- 2 isolation
def gent_E(shore_a):
    """Gent (1958): E [MPa] = 0.0981 (56 + 7.62336 S) / (0.137505 (254 - 2.54 S)), S = Shore A (valid 20-80)."""
    return 0.0981 * (56 + 7.62336 * shore_a) / (0.137505 * (254 - 2.54 * shore_a)) * 1e6


def driver_isolation_options(D, drv_mass_g, gasket_t_mm, rim_od_mm, squeeze_mm, zeta_tpu=0.10, zeta_sil=0.15):
    rows = {}
    for name, E, zeta in (("TPU 95A (Final)", TPU["E"].v, zeta_tpu),
                          ("silicone 50A", gent_E(50), zeta_sil), ("silicone 40A", gent_E(40), zeta_sil),
                          ("silicone 30A", gent_E(30), zeta_sil)):
        r = dy.driver_isolation(D, drv_mass_g, gasket_t_mm, rim_od_mm, squeeze_mm=squeeze_mm, zeta=zeta)
        k = r["k"] * E / TPU["E"].v              # same shape factor, modulus scaled
        fn = math.sqrt(k / (drv_mass_g * 1e-3)) / (2 * math.pi)
        rows[name] = dict(E=E, k=k, fn=fn, zeta=zeta, iso_from=math.sqrt(2) * fn,
                          T_100=float(dy.transmissibility(100.0, fn, zeta)), T_1k=float(dy.transmissibility(1000.0, fn, zeta)),
                          T_5k=float(dy.transmissibility(5000.0, fn, zeta)),
                          # static sag of the driver on its ring under 5 g (seal must stay closed): x = 5 m g / k
                          sag_5g_um=5 * drv_mass_g * 1e-3 * G / k * 1e6)
    return rows


# ---------------------------------------------------------------------------------------------- 3 seal pad
SEAL_P = 0.5e3          # [A] Pa: seal-ring pressure the preload can spare (half of P over the ring area, see report)
SEAL_A_IRR = 1.0e-3     # [A] m: out-of-plane irregularity of the head around the ear (jaw hinge, temple hollow, hair)
SEAL_H_MIN = 0.02e-3    # [A] m: residual slit of a fully conforming seal on skin texture / fine hair


def seal_materials():
    """Effective compressive modulus of the candidate seal materials.
    TPU gyroid: bending-dominated lattice, E*/E = C (rho*/rho)^2 [LIT Gibson-Ashby], anchored at 15 % -> 0.045.
    PU foam (flexible, open cell): E* = E_s (rho/rho_s)^2 [LIT Gibson-Ashby], E_s = 45 MPa, rho_s = 1200 kg/m3."""
    m = {}
    for phi in (0.10, 0.15, 0.25):
        m[f"TPU gyroid {phi:.0%}"] = TPU["E"].v * 0.045 * (phi / 0.15) ** 2
    for rho in (30, 50, 80):
        m[f"PU foam {rho} kg/m3"] = 45e6 * (rho / 1200) ** 2
    return m


def seal_sweep(D, d, des, V_f, heights_mm=(10.0, 20.0, None)):
    """For each material and seal height H: conformity depth delta = p H / E at the spare pressure p, residual
    leak slit h = max(h_min, a_irr - delta), SPL at 50 Hz and 100 Hz relative to a perfect seal (h_min)."""
    f = np.array([50.0, 100.0])
    ref = ac.spl(ac.response_sealed(D, d, des, V_f, SEAL_H_MIN, f=f, leak_depth=(des["seal_od"] - des["seal_id"]) / 2e3)["p"])
    rows = []
    for name, E in seal_materials().items():
        for H in heights_mm:
            H = H or des["standoff"]
            delta = SEAL_P * H * 1e-3 / E
            h = max(SEAL_H_MIN, SEAL_A_IRR - delta)
            spl = ac.spl(ac.response_sealed(D, d, des, V_f, h, f=f, leak_depth=(des["seal_od"] - des["seal_id"]) / 2e3)["p"])
            rows.append(dict(material=name, E=E, H_mm=H, delta_mm=delta * 1e3, leak_mm=h * 1e3,
                             loss_50=float(ref[0] - spl[0]), loss_100=float(ref[1] - spl[1])))
    return rows


# ---------------------------------------------------------------------------------------------- 5 contact stresses
def pad_contact(F, a_mm, b_mm, pad_h_mm, area):
    """Dome pad on skin. Mean p = F / A (support model area). Peak: Hertz sphere-on-flat 1.5 p_mean (thick
    elastic half-space) vs Winkler thin layer over bone 2.0 p_mean (paraboloid indenting a bed of springs:
    p(r) = k (delta - r^2 / 2R), mean over the contact = half the peak)."""
    pm = F / area
    return dict(p_mean=pm, p_hertz=1.5 * pm, p_winkler=2.0 * pm)


TAU_LINE = 0.30      # [STD] largest subsurface shear stress of a Hertz line contact / peak pressure p0 (at 0.78 b depth)


def line_hertz(F, L, R1, R2, E1, nu1, E2, nu2):
    """Two parallel cylinders (R2 < 0: concave seat). Half-width b and peak p0 [LIT Hertz]."""
    Rs = 1 / (1 / R1 + 1 / R2)
    Es = 1 / ((1 - nu1 ** 2) / E1 + (1 - nu2 ** 2) / E2)
    b = math.sqrt(4 * F * Rs / (math.pi * L * Es))
    return dict(b=b, p0=2 * F / (math.pi * b * L))


def screw_head_bearing(size, Fi):
    s = SCREW[size]
    A = math.pi / 4 * ((s["head_d"] * 1e-3) ** 2 - (s["d"] * 1e-3 + 0.4e-3) ** 2)
    p = Fi / A
    return dict(size=size, Fi=Fi, p=p, SF=PETG["S_bear"].v * st.kT() / p, SF_sustained=PETG["S_bear"].v * st.kT() * st.K_SUSTAINED / p)


def serration_flank(Fi_total, n_teeth, w_m, serr_h_m, flank_deg=45.0):
    """Clamp force carried on the tooth flanks (both flanks of every tooth): normal pressure on the flank
    area n_teeth x 2 x w x (h / sin flank)."""
    A = n_teeth * 2 * w_m * serr_h_m / math.sin(math.radians(flank_deg))
    Fn = Fi_total / math.cos(math.radians(flank_deg))
    p = Fn / A
    return dict(p=p, SF=PETG["S_bear"].v * st.kT() / p, SF_sustained=PETG["S_bear"].v * st.kT() * st.K_SUSTAINED / p)
