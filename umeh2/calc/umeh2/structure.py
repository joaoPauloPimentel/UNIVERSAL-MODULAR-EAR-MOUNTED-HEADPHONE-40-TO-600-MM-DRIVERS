"""
Structural checks of the cradle arms, joints, fasteners, inserts,
twist lock, link eye, press/snap fits, creep, temperature and fatigue.

NO FEA WAS RUN. Everything below is closed-form beam / joint theory with
Peterson stress-concentration factors. Where the geometry is not beam-like
(ring tab root, lug root, 45° lip, insert boss) the result is flagged as
"FEA recommended" in the report.

Beam model of an arm
--------------------
Centreline in the arm's own (r, z) plane at angle a:
    pad  (r_tip, z=0)  ->  foot  (z_f = pad_h + ft/2) out to the leg
    leg  (r_l = leg_r + leg_t/2) up to the bar (z_b = S - bar_t/2)
    bar  inwards to the clamp edge of the outer screw (built-in end)
Internal forces at a section located at point s, from the pad force F
applied at the pad contact point p (skin):
    F_int = F ,  M_int = (p - s) x F
decomposed into the section axes (axial a, in-plane h, tangential t):
    sigma = N/A + K_t [ |M_t| 6/(b h^2) + |M_h| 6/(h b^2) ]     (corner, both bending planes summed)
    tau   = T (3 + 1.8 h/b)/(b h^2)    (Roark, rectangle b >= h)  + 1.5 V/A
Printing: arms lie on their side, layers parallel to the (r, z) plane, so
all axial bending stress is IN-LAYER (S_xy); interlayer planes (normal t)
carry the transverse shear V_t and the torsion shear -> checked against
the interlayer shear strength.
"""
import math
import numpy as np
from .materials import (PETG, TPU, GAMMA_M_PRINT, SCREW, A2_70, INSERT_PULLOUT, INSERT_TORQUE_OUT,
                        GAMMA_INSERT, NUT_FACTOR_K, NUT_FACTOR_K_RANGE, FRICTION, CABLE, G)

E_PETG = PETG["E_xy"].v
G_PETG = PETG["E_xy"].v / (2 * (1 + PETG["nu"].v)) * 0.8    # [A] 0.8: printed interlayer shear modulus penalty
K_SUSTAINED = 0.5    # [LIT] creep-rupture: sustained-load strength ~ 45–55 % of short-term for copolyesters (1e4 h)
KT_FILLET = 1.25     # [STD] Peterson, stepped bar in bending, r/d = 0.8, D/d ~ 1.5–2 -> 1.2–1.3
KT_HOLE_BEND = 2.0   # [STD] Peterson, plate with transverse hole in bending, d/W ~ 0.35 -> ~1.9–2.1
KNURL_FLANK_DEG = 30.0   # [A] flank angle of a heat-set insert's knurl (radial wedge on the boss wall)
T_SERVICE = "40C"    # design temperature (skin contact + sun)
T_HOT = "55C"        # hot sensitivity (car, sun)
N_FATIGUE = 1e7      # [A] arm load cycles over the life (walking/running)
CREEP_YEARS = 3.0    # [A] service life over which the clamped PETG creeps (joint preload loss)


def kT(temp=T_SERVICE):
    return {"23C": 1.0, "40C": PETG["kT_40C"].v, "55C": PETG["kT_55C"].v}[temp]


def rect_section(b, h):
    """b = tangential width, h = in-plane thickness (m)."""
    A = b * h
    I_t = b * h ** 3 / 12          # bending about the tangential axis (in-plane bending)
    I_h = h * b ** 3 / 12          # about the in-plane transverse axis (out-of-plane bending)
    lo, hi = min(b, h), max(b, h)
    beta = 1 / 3 - 0.21 * lo / hi * (1 - lo ** 4 / (12 * hi ** 4))   # St Venant torsion constant factor
    J = beta * hi * lo ** 3
    return dict(A=A, I_t=I_t, I_h=I_h, J=J, b=b, h=h)


def arm_path(d, des, arm):
    """Discretised centreline (global points, local axis, section dims, Kt) and the named critical sections."""
    a = math.radians({"saddle": des["saddle_a"], "temporal": des["temporal_a"],
                      "mastoid": des["mastoid_a"], "post": des.get("post_a") or 0.0}[arm])
    er = np.array([math.cos(a), math.sin(a), 0.0]); et = np.array([-math.sin(a), math.cos(a), 0.0]); ez = np.array([0, 0, 1.0])
    S = des["standoff"] * 1e-3
    w = (des["saddle_arm_w"] if arm == "saddle" else des["arm_w"]) * 1e-3
    ft = (des["foot_t_mastoid"] if arm == "mastoid" else des["foot_t"]) * 1e-3
    r_tip = {"saddle": des["saddle_r"], "temporal": des["temporal_r"], "mastoid": des["mastoid_r"],
             "post": des.get("post_r", 0.0)}[arm] * 1e-3
    z_foot0 = (des["saddle_skin_gap"] if arm == "saddle" else des["pad_h"]) * 1e-3
    z_f = z_foot0 + ft / 2
    leg_t = des["leg_t"] * 1e-3; bar_t = des["bar_t"] * 1e-3
    r_l = d["leg_r"] * 1e-3 + leg_t / 2
    z_b = S - bar_t / 2
    as_ = SCREW[des["arm_screw"]]
    r_clamp = (d["tab_r"] + as_["head_d"] / 2 + des["slot_adj"]) * 1e-3   # clamp edge, arm at its outermost slot position
    segs = []
    def seg(p0, p1, b, h, kind, n=40):
        for s in np.linspace(0, 1, n, endpoint=False) + 0.5 / n:
            p = p0 + (p1 - p0) * s
            ax = (p1 - p0) / np.linalg.norm(p1 - p0)
            segs.append(dict(p=p, ax=ax, b=b, h=h, ds=np.linalg.norm(p1 - p0) / n, kind=kind))
    P0 = r_tip * er + z_f * ez; P1 = r_l * er + z_f * ez; P2 = r_l * er + z_b * ez; P3 = r_clamp * er + z_b * ez
    seg(P0, P1, w, ft, "foot"); seg(P1, P2, w, leg_t, "leg"); seg(P2, P3, w, bar_t, "bar")
    hole = (d["pad_screw_clear"] if arm != "saddle" else d["cap_pin_clear"]) * 1e-3
    fr = des["fillet_r"] * 1e-3
    sections = {
        "tip (pad-screw hole)": dict(p=P0 + 0 * er, ax=er, b=w - hole, h=ft, Kt=KT_HOLE_BEND),
        "foot at leg fillet": dict(p=(r_l - leg_t / 2 - fr) * er + z_f * ez, ax=er, b=w, h=ft, Kt=KT_FILLET),
        "leg bottom fillet": dict(p=r_l * er + (z_f + ft / 2 + fr) * ez, ax=ez, b=w, h=leg_t, Kt=KT_FILLET),
        "leg top fillet": dict(p=r_l * er + (S - bar_t - fr) * ez, ax=ez, b=w, h=leg_t, Kt=KT_FILLET),
        "bar at clamp edge (slot end)": dict(p=P3, ax=er, b=w - d["arm_screw_clear"] * 1e-3, h=bar_t, Kt=KT_HOLE_BEND),
    }
    return dict(segs=segs, sections=sections, er=er, et=et, ez=ez, w=w, clamp=P3, r_tip=r_tip, tip=P0)


def _local(ax, et):
    """Section axes: a (axial), t (tangential, = arm width direction), h = t x a (in-plane thickness)."""
    t = et; h = np.cross(t, ax)
    return ax, t, h


def section_stress(sec, et, loads):
    """loads = list of (point, force) acting on the arm OUTBOARD of the section (pad side)."""
    a, t, h = _local(sec["ax"], et)
    F = sum((f for _, f in loads), np.zeros(3))
    M = sum((np.cross(p - sec["p"], f) for p, f in loads), np.zeros(3))
    N = F @ a; Vt = F @ t; Vh = F @ h
    T = M @ a; Mt = M @ t; Mh = M @ h
    S = rect_section(sec["b"], sec["h"])
    b, hh = sec["b"], sec["h"]
    sig_b = abs(Mt) * 6 / (b * hh ** 2) + abs(Mh) * 6 / (hh * b ** 2)
    sig = abs(N) / S["A"] + sec["Kt"] * sig_b
    lo, hi = min(b, hh), max(b, hh)
    tau_T = abs(T) * (3 + 1.8 * lo / hi) / (hi * lo ** 2)
    tau = tau_T + 1.5 * math.hypot(Vt, Vh) / S["A"]
    tau_il = tau_T + 1.5 * abs(Vt) / S["A"]           # shear on interlayer planes (normal t)
    vm = math.sqrt(sig ** 2 + 3 * tau ** 2)
    return dict(N=N, Vt=Vt, Vh=Vh, T=T, Mt=Mt, Mh=Mh, sigma=sig, tau=tau, tau_il=tau_il, vm=vm)


def arm_compliance(d, des, arm, direction):
    """Tip displacement per unit pad force along `direction` (m/N) by Castigliano over the
    whole centreline (in-plane + out-of-plane bending, torsion, axial). Built-in at the clamp edge."""
    A = arm_path(d, des, arm)
    E = E_PETG * kT(); Gm = G_PETG * kT()
    pad = A["r_tip"] * A["er"]
    e = np.asarray(direction, float) / np.linalg.norm(direction)
    U2 = 0.0
    for s in A["segs"]:
        a, t, h = _local(s["ax"], A["et"])
        M = np.cross(pad - s["p"], e)
        S = rect_section(s["b"], s["h"])
        U2 += ((M @ t) ** 2 / (E * S["I_t"]) + (M @ h) ** 2 / (E * S["I_h"]) + (M @ a) ** 2 / (Gm * S["J"])
               + (e @ a) ** 2 / (E * S["A"])) * s["ds"]
    return U2


KAPPA_SHEAR = 1.2      # [STD] shear correction factor of a rectangular section (Timoshenko)


def _skew(v):
    return np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])


def arm_tip_compliance(d, des, arm, temp=T_SERVICE, shear=True):
    """6x6 flexibility of the arm tip P0 (foot centreline at the pad screw / saddle-cap pin), clamp edge built
    in: generalised load Q = [F, M] at P0 -> generalised displacement [u, theta] = C Q. Unit-load method over
    the whole centreline (foot, leg, bar): at a section s with axes (a, t, h) and rho = P0 - p_s the
    resultants are N = a.F, V_t = t.F, V_h = h.F, [T, M_t, M_h] = [a, t, h].(M + rho x F), and
        C = sum_s B_s^T diag(1/EA, kappa/GA, kappa/GA, 1/GJ, 1/EI_t, 1/EI_h) B_s ds       [C]
    (axial, both shears with kappa = 1.2, St Venant torsion, both bendings; E, G at the service temperature).
    Returns (P0, C)."""
    A = arm_path(d, des, arm)
    E = E_PETG * kT(temp); Gm = G_PETG * kT(temp)
    P0 = A["tip"]
    C = np.zeros((6, 6))
    for sgm in A["segs"]:
        a, t, h = _local(sgm["ax"], A["et"])
        S = rect_section(sgm["b"], sgm["h"])
        Sk = _skew(P0 - sgm["p"])
        B = np.zeros((6, 6))
        B[0, :3] = a; B[1, :3] = t; B[2, :3] = h
        for i, e in enumerate((a, t, h)):
            B[3 + i, :3] = e @ Sk; B[3 + i, 3:] = e
        k_s = KAPPA_SHEAR / (Gm * S["A"]) if shear else 0.0
        Dg = np.diag([1 / (E * S["A"]), k_s, k_s, 1 / (Gm * S["J"]), 1 / (E * S["I_t"]), 1 / (E * S["I_h"])])
        C += B.T @ Dg @ B * sgm["ds"]
    return P0, 0.5 * (C + C.T)


def arm_energy_split(d, des, arm, loads, temp=T_SERVICE):
    """Where an arm's compliance sits under a given set of contact forces: shares of the complementary energy
    U = 1/2 sum_s v_s^T diag(...) v_s ds (the same terms as arm_tip_compliance) by segment (foot / leg / bar) and
    mode (axial; shear; torsion; in-plane bending M_t, about the width axis; out-of-plane bending M_h).
    loads = [(point, force)] rigidly attached to the arm tip (the support model's contact forces). Returns
    {"<segment> <mode>": share} and the total U (J)."""
    A = arm_path(d, des, arm)
    E = E_PETG * kT(temp); Gm = G_PETG * kT(temp)
    P0 = A["tip"]
    Fs = sum(np.asarray(F, float) for _, F in loads)
    Ms = sum(np.cross(np.asarray(r, float) - P0, np.asarray(F, float)) for r, F in loads)
    Q = np.concatenate([Fs, Ms])
    parts = {}
    modes = (("axial", (0,)), ("shear", (1, 2)), ("torsion", (3,)), ("in-plane bending", (4,)), ("out-of-plane bending", (5,)))
    for sgm in A["segs"]:
        a, t, h = _local(sgm["ax"], A["et"])
        S = rect_section(sgm["b"], sgm["h"])
        Sk = _skew(P0 - sgm["p"])
        B = np.zeros((6, 6))
        B[0, :3] = a; B[1, :3] = t; B[2, :3] = h
        for i, e in enumerate((a, t, h)):
            B[3 + i, :3] = e @ Sk; B[3 + i, 3:] = e
        v = B @ Q
        k_s = KAPPA_SHEAR / (Gm * S["A"])
        dg = (1 / (E * S["A"]), k_s, k_s, 1 / (Gm * S["J"]), 1 / (E * S["I_t"]), 1 / (E * S["I_h"]))
        for nm, idx in modes:
            key = f"{sgm['kind']} {nm}"
            parts[key] = parts.get(key, 0.0) + 0.5 * sum(dg[i] * v[i] ** 2 for i in idx) * sgm["ds"]
    U = sum(parts.values())
    return {k: v / U for k, v in sorted(parts.items(), key=lambda kv: -kv[1])} if U > 0 else {}, U


def point_map(r, r_node):
    """3x6 map from the node's [u, theta] to the displacement of a point rigidly attached at r: u + theta x (r - r_node)."""
    return np.hstack([np.eye(3), -_skew(np.asarray(r) - np.asarray(r_node))])


def arm_loads_from_contacts(contacts, C, arm):
    """Pad forces from the support solution for a given arm (force ON the device, at the contact point)."""
    names = {"temporal": ("T temporal",), "mastoid": ("M mastoid",), "post": ("P post-sup",),
             "saddle": ("S root", "S root F", "S root B", "S scalp", "S helix")}[arm]
    return [(c["r"], x["Fvec"]) for c, x in zip(C, contacts) if x["name"] in names]


def check_arm_sections(d, des, arm, loads, temp=T_SERVICE):
    A = arm_path(d, des, arm)
    out = {}
    for nm, sec in A["sections"].items():
        out[nm] = section_stress(sec, A["et"], loads)
    return out


def strength(kind, temp=T_SERVICE, sustained=False):
    S = PETG["S_xy"].v * kT(temp)
    Sil = PETG["S_shear_il"].v * kT(temp)
    if sustained:
        S *= K_SUSTAINED; Sil *= K_SUSTAINED
    return S, Sil


# ------------------------------------------------------------------ fatigue (printed PETG)
def fatigue_strength(N, temp=T_SERVICE):
    """Normalised S-N (Basquin) anchored at S_xy for N=1 (quarter cycle) down to fat_ratio at 1e7 [A]."""
    Su = PETG["S_xy"].v * kT(temp)
    b = PETG["fat_b"].v
    Sf = Su * (2 * N) ** b
    return max(Sf, PETG["fat_ratio"].v * Su)


def goodman_sf(s_a, s_m, N, temp=T_SERVICE):
    Sf = fatigue_strength(N, temp); Su = PETG["S_xy"].v * kT(temp)
    return 1 / (s_a / Sf + s_m / Su) if (s_a > 0 or s_m > 0) else np.inf


# ------------------------------------------------------------------ bolted joints
def screw_joint(size, T_tight, n_screws, pitch_m, F_shear, M_joint_t, M_joint_r, F_axial, mu_joint=None,
                clamp_len=None, temp=T_SERVICE, creep_years=None):
    """Arm-to-tab joint: n screws in heat-set inserts, arm slotted (adjustment).
    Preload F_i = T / (K d)  [K nut factor, LIT].
    Slip (the slots rely on friction): resisting = mu * (n F_i,eff - F_sep) ; demand = F_shear + M_z / r_eff.
    Prying: moment about the tangential axis through the joint -> screw tension ~ M / pitch (lever rule, conservative).
    Preload loss by PETG creep in the clamped arm (Findley): F_eff = F_i / (1 + (t/tau)^n) with the joint
    compliance dominated by the printed parts [A]."""
    s = SCREW[size]
    d = s["d"] * 1e-3; As = s["As"] * 1e-6
    K = NUT_FACTOR_K.v
    Fi = T_tight / (K * d)
    creep_years = CREEP_YEARS if creep_years is None else creep_years
    t_h = creep_years * 8760
    tau = PETG["creep_tau_h"].v / (4 if temp in ("40C", "55C") else 1)
    loss = 1 / (1 + (t_h / tau) ** PETG["creep_n"].v)
    # the clamp is not all PETG: the screw and insert are rigid, so only the PETG strain relaxes; the relaxation
    # factor above is applied to the full preload (conservative).
    Fi_eff = Fi * loss
    mu = mu_joint if mu_joint is not None else FRICTION["PETG/PETG (bayonet)"][0][0]
    F_pry = abs(M_joint_t) / pitch_m + max(F_axial, 0) / n_screws
    F_screw = Fi + F_pry
    sig_screw = F_screw / As + 16 * T_tight * 0.5 / (math.pi * (0.9 * d) ** 3) / (F_screw / As + 1e-9) * 0   # torsion relaxes after tightening
    SF_screw = A2_70["Rp02"].v / (F_screw / As)
    SF_pull = INSERT_PULLOUT[size].v / GAMMA_INSERT.v / (Fi + F_pry)
    SF_spin = INSERT_TORQUE_OUT[size].v / T_tight
    head_area = math.pi / 4 * ((s["head_d"] * 1e-3) ** 2 - (s["d"] * 1e-3 + 0.4e-3) ** 2)
    p_bear = F_screw / head_area
    SF_bear = PETG["S_bear"].v * kT(temp) * K_SUSTAINED / p_bear
    r_eff = pitch_m / 2
    F_slip_dem = abs(F_shear) + abs(M_joint_r) / r_eff
    F_slip_cap = mu * max(n_screws * Fi_eff - F_pry, 0)
    return dict(size=size, T=T_tight, Fi=Fi, Fi_eff=Fi_eff, creep_loss=1 - loss, F_pry=F_pry, F_screw=F_screw,
                SF_screw=SF_screw, SF_pullout=SF_pull, SF_spin=SF_spin, p_bear=p_bear, SF_bear=SF_bear,
                F_slip_dem=F_slip_dem, F_slip_cap=F_slip_cap, SF_slip=F_slip_cap / max(F_slip_dem, 1e-9))


def insert_boss(size, wall_mm):
    """Heat-set insert boss: wall >= design.INSERT_WALL_RULE x insert OD [DS supplier guidance] and hoop stress from
    the pull-out load spread over the knurl (thick-walled cylinder, internal pressure p = F/(pi d L tan(phi)))."""
    from .design import INSERT_WALL_RULE
    s = SCREW[size]
    ro = s["insert_od"] / 2 + wall_mm; ri = s["insert_od"] / 2
    F = INSERT_PULLOUT[size].v / GAMMA_INSERT.v
    p = F / (math.pi * s["insert_od"] * 1e-3 * s["insert_L"] * 1e-3 * math.tan(math.radians(KNURL_FLANK_DEG)))  # [A] knurl flank
    hoop = p * (ro ** 2 + ri ** 2) / (ro ** 2 - ri ** 2)
    S = PETG["S_z"].v * kT()      # hoop acts across layers for a vertical boss -> interlayer strength
    return dict(size=size, wall=wall_mm, rule_ok=wall_mm >= INSERT_WALL_RULE * s["insert_od"] - 1e-9, p=p, hoop=hoop, SF=S / hoop)


def press_fit(D_mm, interf_mm, t_mm, E=None):
    """Ring pressed into a bore: hoop strain = interference / D (whole interference taken by the
    thinner, more compliant member = conservative)."""
    E = E or PETG["E_xy"].v
    eps = interf_mm / D_mm
    sig = E * eps
    return dict(eps=eps, sigma=sig, SF=PETG["S_xy"].v * kT() * K_SUSTAINED / sig)


def contact_pressure_cyl(F, L, R1, E1, nu1, R2=None, E2=None, nu2=0.38):
    """Hertz line contact (cylinder on plane/cylinder): b = sqrt(4 F R* / (pi L E*)), p0 = 2F/(pi b L)."""
    E2 = E2 or E1
    Es = 1 / ((1 - nu1 ** 2) / E1 + (1 - nu2 ** 2) / E2)
    Rs = R1 if R2 is None else 1 / (1 / R1 + 1 / R2)
    b = math.sqrt(4 * F * Rs / (math.pi * L * Es))
    return dict(b=b, p0=2 * F / (math.pi * b * L))


CREEP_L_EFF = 4.0e-3     # [A] m, effective creeping length of PETG under a screw head (stress spreads ~45 deg)


def retained_preload(F_start, size, washer, temp=T_SERVICE, creep_years=None):
    """Clamp force after PETG creep. Rigid joint (no washer): the preload relaxes with the PETG (displacement-
    controlled, Findley creep ratio cr): F = F_start / (1 + cr). Wave spring washer (flat load F0, rate k_w) in
    series: if F_start > F0 the washer is flat (solid) and the preload first relaxes rigidly down to F0 over a
    negligible displacement; from min(F_start, F0) the washer follows the remaining creep displacement
    delta = (F / A_head / E) cr L_eff, so F = min(F_start, F0) - k_w delta [C]. Returns (F, cr, info)."""
    s = SCREW[size]
    d = s["d"] * 1e-3
    creep_years = CREEP_YEARS if creep_years is None else creep_years
    t_h = creep_years * 8760
    t_eq = t_h + 4 * (2 * 365 * creep_years)      # 23 C storage + 2 h/day at 40 C (shift factor 4) [A]
    cr = (t_eq / PETG["creep_tau_h"].v) ** PETG["creep_n"].v          # Findley creep / elastic strain ratio
    F_rigid = F_start / (1 + cr)
    if not washer:
        return F_rigid, cr, None
    F0, k_w = washer
    A_head = math.pi / 4 * ((s["head_d"] * 1e-3) ** 2 - (d + 0.4e-3) ** 2)
    Fs = min(F_start, F0)
    delta = Fs / A_head / (PETG["E_xy"].v * kT(temp)) * cr * CREEP_L_EFF
    F_w = Fs - k_w * delta
    return max(F_rigid, F_w), cr, dict(F0=F0, k_w=k_w, F_start=F_start, delta_creep=delta, F_retained=F_w, washer_flat=F_start >= F0)


L_ENG_SERR = 14e-3   # [A] m, serrated length that carries the radial load (the clamped zone between and under the two
                    # screw heads); enters only the tooth-shear (serrated_joint) and flank-pressure (extras.serration_flank) checks


def serrated_joint(size, T_tight, n_screws, F_radial, F_tang, M_tilt, pitch_m, flank_deg=45.0, mu=None,
                   serr_p=1.2e-3, serr_h=0.6e-3, w_m=10e-3, L_eng=None, temp=T_SERVICE, creep_years=None,
                   washer=None, F_pull=0.0, T_twist=0.0, M_inplane=0.0, t_bear_m=None):
    """Arm-to-tab joint with serrations (Final design): n screws on the arm centreline at pitch p, arm width w.
    Section forces at the clamp edge (structure.section_stress, bar axis a = radial): F_r = N (radial),
    F_t = V_t (tangential), F_pull = pull-off normal to the joint face (V_h > 0), M_tilt = M_t (about the
    tangential axis), T_twist = T (about the radial axis = the screw line), M_inplane = M_h (about the
    joint normal).
    Preload from the tightening torque, F_i = T / (K d), with the nut-factor scatter K_lo..K_hi
    (materials.NUT_FACTOR_K_RANGE): F_i,max = T/(K_lo d) for the insert, F_i,min = T/(K_hi d) for engagement.
    Retained (aged) preload: retained_preload(F_i,min) (PETG creep, wave washer).
    External demand on the most loaded screw (lever rule, conservative bounds on the load factor Phi: the
    screw takes all of it for pull-out (Phi = 1), the clamp loses all of it for engagement (Phi = 0)):
        wedge   F_sep  = |F_r| tan(flank - phi), phi = atan(mu)     (radial load on the tooth flanks), shared by n
        prying  |M_t| / p                                          (couple of the two screws about the joint centre)
        twist   2 |T| / (n w)                                      (arm pivots on its edge, lever w/2)
        pull    F_pull / n
        D_screw = F_sep / n + |M_t| / p + 2 |T| / (n w) + F_pull / n
        SF_engage  = F_i,eff(min) / D_screw          (external loads can grow by SF before the teeth lift)
        SF_pullout = (pull-out / gamma_insert) / (F_i,max + D_screw)
    Tangential: the grooves run tangentially, so F_t and the in-plane moment go to the screw shanks bearing on
    the slot sides over the bar thickness t_bear: per screw |F_t| / n + |M_h| / p.
    Tooth root shear: tau = F_r / (n_teeth * w * p) (teeth in the arm, in-layer shear because the arm is
    printed on its side: the tooth profile lies in the print plane)."""
    s = SCREW[size]
    d = s["d"] * 1e-3
    t_bear = t_bear_m if t_bear_m is not None else w_m
    mu = mu if mu is not None else FRICTION["PETG/PETG (bayonet)"][0][0]
    K_lo, K_hi = NUT_FACTOR_K_RANGE[0].v, NUT_FACTOR_K_RANGE[1].v
    Fi = T_tight / (NUT_FACTOR_K.v * d)
    Fi_max = T_tight / (K_lo * d); Fi_min = T_tight / (K_hi * d)
    Fi_eff, cr, w_info = retained_preload(Fi_min, size, washer, temp, creep_years)
    Fi_eff_nom = retained_preload(Fi, size, washer, temp, creep_years)[0]
    phi = math.atan(mu)
    F_sep = abs(F_radial) * math.tan(math.radians(flank_deg) - phi) if math.radians(flank_deg) > phi else 0.0
    F_pry = abs(M_tilt) / pitch_m
    F_twist = 2 * abs(T_twist) / (n_screws * w_m)
    F_pull = max(F_pull, 0.0)
    D_screw = F_sep / n_screws + F_pry + F_twist + F_pull / n_screws
    n_teeth = int((L_eng if L_eng is not None else L_ENG_SERR) / serr_p)
    tau_tooth = abs(F_radial) / (n_teeth * w_m * serr_p)
    F_bear = abs(F_tang) / n_screws + abs(M_inplane) / pitch_m
    bearing_slot = F_bear / (d * t_bear)
    cap = INSERT_PULLOUT[size].v / GAMMA_INSERT.v
    return dict(size=size, T=T_tight, Fi=Fi, Fi_min=Fi_min, Fi_max=Fi_max, Fi_eff=Fi_eff, Fi_eff_nom=Fi_eff_nom,
                creep_ratio=cr, creep_retained=Fi_eff / Fi_min, washer=w_info, F_sep=F_sep, F_pry=F_pry,
                F_twist=F_twist, F_pull=F_pull, D_screw=D_screw,
                SF_engage=Fi_eff / max(D_screw, 1e-9),
                SF_pullout=cap / (Fi_max + D_screw), SF_pullout_nom=cap / (Fi + D_screw),
                SF_spin=INSERT_TORQUE_OUT[size].v / T_tight,
                tau_tooth=tau_tooth, SF_tooth=PETG["S_xy"].v * kT(temp) / math.sqrt(3) * K_SUSTAINED / max(tau_tooth, 1),
                F_bear=F_bear, p_slot=bearing_slot, SF_slot=PETG["S_bear"].v * kT(temp) / max(bearing_slot, 1),
                head_bearing=Fi_max / (math.pi / 4 * ((s["head_d"] * 1e-3) ** 2 - (d + 0.4e-3) ** 2)))


# ------------------------------------------------------------------ twist lock (UMI-2)
def solid_gasket_lock(d, des, squeeze_mm):
    """Design A/B: flat solid TPU 95A ring on the groove floor, squeezed by the lugs only.
    Each lug footprint is a strip of width w (gasket radial overlap) and length l (lug arc):
    shape factor S = w l / (2 (w + l) t_c), compression modulus Ec = E (1 + 2 k S^2), k = 0.75 [LIT],
    F = Ec A eps (linear; real TPU 95A is up to ~2x softer at 25-30 % strain, still >> hand force)."""
    E = TPU["E"].v
    R_S = d["spig_d"] / 2e3; R_B = d["bore_d"] / 2e3; R_L = R_S + des["lug_h"] * 1e-3
    R_G = R_L + des["groove_rclr"] * 1e-3
    r_in = R_B + 0.4e-3; r_out = min(R_G - 0.4e-3, R_L)
    w = r_out - r_in
    t = des["gasket_umi_t"] * 1e-3
    tc = t - max(squeeze_mm, 0) * 1e-3
    eps = max(squeeze_mm, 0) * 1e-3 / t
    F = 0.0
    for wd in des["lug_widths"]:
        l = math.radians(wd) * 0.5 * (r_in + r_out)
        S = w * l / (2 * (w + l) * tc)
        Ec = E * (1 + 2 * 0.75 * S ** 2)
        F += Ec * w * l * eps
    R_m = 0.5 * (R_B + R_L)
    mu = FRICTION["PETG/PETG (bayonet)"][0][1]
    return dict(squeeze=squeeze_mm, eps=eps, F=F, T_lock=F * R_m * (mu + mu), w=w)


def twistlock(d, des, m_module, P_link, eps_range, T_hand_max=0.30, a_offhead=2.0, a_acc=5.0, temp=T_SERVICE, cfd25=None):
    """Final twist lock (UMI-2): load paths and the DERIVED foam specification.

    * Link preload P and every inward (toward the head) load press the lug bottoms onto the rigid groove
      floor (PETG on PETG, flat bearing): the module position is fixed by printed faces, not by a spring.
    * An outward load larger than P lifts the lugs against the 45 deg lip through the foam strips; beyond
      the foam's densification the lug bears on the lip cone (conformal) -> bearing + lug-root checks.
    * The foam strips only (a) keep the module rattle-free when the headphone is carried (link preload
      absent) and (b) set the assembly torque. Their compression-force-deflection must lie in a window:
          F_ax,min = m_module a_offhead g / (1 - compression set)        (rattle-free off-head)
          F_ax,max = T_hand / k_ramp                                      (one-hand twist while climbing the ramp)
      with k_ramp = R_m [ (tan a + sqrt2 mu_f)/(1 - sqrt2 mu_f tan a) + mu_floor ]: wedge with friction on the
      45 deg cone face (normal force sqrt2 x axial) plus floor friction. With the foam curve
      sigma(eps) = CFD25 (eps/0.25)^n the window in CFD25 follows from the foam strain range of the
      tolerance stack (eps_range = Monte-Carlo 0.135 / 99.865 % values).
    * Spigot in the bore under a radial 5 g load: conformal Hertz line contact."""
    from .materials import FOAM
    s2 = math.sqrt(2)
    R_S = d["spig_d"] / 2e3; R_B = d["bore_d"] / 2e3; R_L = R_S + des["lug_h"] * 1e-3
    th = [math.radians(w) for w in des["lug_widths"]]
    R_m = 0.5 * (R_B + R_L)
    ramp = des.get("lug_ramp_c", 0) > 0
    th_r = des["lug_ramp_L"] * 1e-3 / R_m if ramp else 0.0
    band = 0.5 * (R_L ** 2 - R_B ** 2)
    A_floor = sum(th) * band
    A_cone = sum(th) * band * s2
    A_foam = sum(t - 2 * th_r for t in th) * band * s2
    mu_f = FOAM["mu"].v                                   # upper value: assembly torque
    mu_f_lo = 0.5                                         # [A] lower end of 0.5-1.0: holding torque
    mu_fl_lo, mu_fl, mu_fl_hi = FRICTION["PETG/PETG (bayonet)"][0]
    alpha = math.atan(des["lug_ramp_c"] / des["lug_ramp_L"]) if ramp else 0.0
    k_ramp = R_m * ((math.tan(alpha) + s2 * mu_f) / (1 - s2 * mu_f * math.tan(alpha)) + mu_fl_hi)
    k_run = R_m * (s2 * mu_f + mu_fl_hi)
    cs = FOAM["comp_set"].v; n = FOAM["cfd_exp"].v
    F_min = m_module * a_offhead * G / (1 - cs)
    F_max = T_hand_max / k_ramp
    e_lo, e_hi = eps_range
    g = lambda e: (max(e, 1e-6) / 0.25) ** n
    cfd_lo = s2 * F_min / A_foam / g(e_lo)
    cfd_hi = s2 * F_max / A_foam / g(e_hi)
    feasible = cfd_lo < cfd_hi
    cfd = cfd25 if cfd25 is not None else (math.sqrt(cfd_lo * cfd_hi) if feasible else cfd_lo)
    F_ax = lambda e, c=cfd: c * g(e) * A_foam / s2
    F_nom = F_ax(des["foam_eps"]); F_lo = F_ax(e_lo) * (1 - cs); F_hi = F_ax(e_hi)
    S_b = PETG["S_bear"].v * kT(temp)
    p_floor = P_link / A_floor
    p_floor_acc = (P_link + m_module * a_acc * G) / A_floor
    a_lift = (P_link + F_lo) / (m_module * G)
    F_out = m_module * a_acc * G                    # outward 5 g, link preload ignored (conservative)
    p_cone = s2 * F_out / A_cone
    h_root = min(des["lug_t"] + des["lug_h"], d["baffle_h"]) * 1e-3
    w_root = sum(th) * R_S
    tau_root = 1.5 * F_out / (w_root * h_root)
    sig_root = 2.5 * F_out * (R_m - R_S) / (w_root * h_root ** 2 / 6)     # Kt 2.5: sharp re-entrant corner [STD Peterson]
    Sil = PETG["S_shear_il"].v * kT(temp); Sxy = PETG["S_xy"].v * kT(temp)
    hz = contact_pressure_cyl(m_module * a_acc * G, d["baffle_h"] * 1e-3, R_S, E_PETG, PETG["nu"].v, R2=-R_B, E2=E_PETG)
    T_hold = R_m * (mu_fl_lo * (P_link + F_lo) + s2 * mu_f_lo * F_lo)
    return dict(A_floor=A_floor, A_cone=A_cone, A_foam=A_foam, R_m=R_m, alpha_deg=math.degrees(alpha),
                k_ramp=k_ramp, k_run=k_run, F_ax_min_req=F_min, F_ax_max_allow=F_max,
                eps_lo=e_lo, eps_hi=e_hi, cfd25_lo=cfd_lo, cfd25_hi=cfd_hi, feasible=feasible, cfd25_spec=cfd,
                F_foam_nom=F_nom, F_foam_lo_after_set=F_lo, F_foam_hi=F_hi, T_ramp_max=F_hi * k_ramp,
                T_run_nom=F_nom * k_run, T_hold_onhead=T_hold,
                p_floor=p_floor, p_floor_acc=p_floor_acc, SF_floor=S_b * K_SUSTAINED / p_floor, SF_floor_acc=S_b / p_floor_acc,
                a_lift_g=a_lift, F_out_5g=F_out, p_cone=p_cone, SF_cone=S_b / p_cone,
                tau_root=tau_root, SF_root_shear=Sil / tau_root, sig_root=sig_root, SF_root_bend=Sxy / sig_root,
                hertz_b=hz["b"], hertz_p0=hz["p0"], SF_hertz=S_b / hz["p0"], hertz_valid=hz["b"] < 0.2 * R_S)
