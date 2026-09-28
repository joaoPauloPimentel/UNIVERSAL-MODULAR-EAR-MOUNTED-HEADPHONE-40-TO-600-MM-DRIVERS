"""
Occipital spring link — the wire diameter is DERIVED, not chosen.

Geometry: a planar wire in the head's transverse plane (X lateral, Y fore-aft), symmetric about the midline.
  * Final, eye on the cup end (support.link_path): from the eye the wire runs back across the cup face to
    hook_y, inward along the module side to the head (side_x), then around the occiput as a circular arc whose
    apex lies `apex` behind the eye line (SAGITTA + 15 mm [A]).
  * Design B, eye on the mastoid pad: a circular arc through both eyes; eye half-spacing w = head_half_width +
    eye height above skin, the occiput a sagitta s = SAGITTA [A] behind the eye line, R = (w^2 + s^2) / (2 s).

End forces +-P act along the chord (eye to eye). Moment at a point of the
wire is  M = P * x  with x the distance from the chord, so by Castigliano
    delta_pair = (P / EI) * integral( x^2 ds )      (bending; the axial and shear share is bounded below the tables)
    k_pair = P / delta_pair ,  k_side = 2 k_pair  (each eye moves delta_pair/2)
Max bending moment  M_max = P * x_max  at the apex (x_max: the apex distance from the chord).
Apex torsion coil (n turns, mean diameter Dc) sits where M = P x_max, so it adds
    delta_coil = P x_max^2 L_coil / (E I),  L_coil = pi Dc n
and k_pair = EI / (int x^2 ds + x_max^2 L_coil). The coil lowers the rate (preload
stays nearly constant across head sizes) without raising the stress, apart
from the coil curvature factor Ki = (4C^2 - C - 1)/(4C(C - 1)), C = Dc/d.
Bending stress      sigma = 32 M / (pi d^3)
Eye (end loop) stress, Shigley hook formula with the moment arm = mean eye radius r1:
    sigma_eye = P [ K_A * 32 r1 / (pi d^3) + 4 / (pi d^2) ],
    K_A = (4 C1^2 - C1 - 1) / (4 C1 (C1 - 1)),  C1 = 2 r1 / d
Strength: music wire ASTM A228, Sut = {A:g} / d^{m:g} MPa [STD]; bending
yield ~{sy:g} Sut [STD]; fully reversed bending endurance {se:g} Sut [A].
"""
import math
import numpy as np
from .materials import WIRE, SILICONE, music_wire_Sut
from .design import ANTHRO

__doc__ = __doc__.format(A=WIRE["Sut_A"].v / 1e6, m=WIRE["Sut_m"].v, sy=WIRE["Sy_ratio"].v, se=WIRE["Se_bend_ratio"].v)

EYE_H = 12.0e-3          # eye height above skin (pad_h + foot_t_mastoid), from CAD
SAGITTA = 0.085          # [A] occiput 85 mm behind the mastoid line at link height
HEAD_VAR = 6.0e-3        # [A] +-6 mm per side: p5–p95 head breadth at the mastoids (~ +-12 mm total)
DON_EXTRA = 20.0e-3      # [A] extra spread per side while putting it on
SF_YIELD = 1.5           # required
SF_FATIGUE = 1.5         # required (Goodman)
P_RATIO_MAX = 2.0        # [A] comfort: largest-head preload / smallest-head preload
N_DON = 1e4              # [A] donning cycles over the life (about 5 a day for 5 years): the link's fatigue life


def geometry(sagitta=SAGITTA):
    w = ANTHRO["head_half_width"] * 1e-3 + EYE_H
    R = (w ** 2 + sagitta ** 2) / (2 * sagitta)
    # arc parametrised by angle from the apex; chord at distance (R - s) from centre
    half = math.asin(min(1.0, w / R)) if sagitta <= R else math.pi - math.asin(w / R)
    th = np.linspace(-half, half, 2001)
    x = R * np.cos(th) - (R - sagitta)            # distance from chord line
    ds = R * (th[1] - th[0])
    I2 = np.sum(x ** 2) * ds
    L = R * 2 * half
    return dict(w=w, R=R, s=sagitta, I2=I2, L=L, x_max=float(x.max()))


DC_COIL = 12.0e-3        # [A] apex coil mean diameter (fits behind the occiput under hair)
EYE_RI_MIN = 1.45e-3     # [A] smallest eye inner radius = sleeve OD / 2: the sleeve bore (design.EYE_SLEEVE_ID) + 0.1 mm wall
SLEEVE_WALL = 2.0e-3     # [A] wall of the silicone comfort sleeve over the wire (skin and hair contact)
SLEEVE_COVER = 0.9       # [A] share of the arc length (eye to eye, without the apex coil) the sleeve covers; bare at the eye bends
ALPHA_SHEAR = 10 / 9     # [STD] shear correction factor of a solid round section


def eye_ri(d_mm):
    """Inner radius of the wire eye (m): the minimum bend radius (WIRE min_bend_radius_d x d) or the eye sleeve's
    outer radius, whichever is larger."""
    return max(WIRE["min_bend_radius_d"].v * d_mm * 1e-3, EYE_RI_MIN)


def link_sleeve_mass(d_mm, L):
    """Mass (g) of the comfort sleeve on a link of arc length L (m): silicone tube, ID = wire, SLEEVE_WALL wall."""
    r = d_mm * 1e-3 / 2
    return SILICONE["rho"].v * math.pi * ((r + SLEEVE_WALL) ** 2 - r ** 2) * SLEEVE_COVER * L * 1e3


def axial_shear_share(r):
    """Upper bound of the axial + shear compliance of the wire relative to its bending compliance for one link
    design r: N, V <= P along the whole arc length L, so delta_as <= P L (1 + ALPHA_SHEAR E/G) / (E A),
    G = E / (2 (1 + nu)); the bending compliance is 1 / k_pair."""
    A = math.pi * (r["d_mm"] * 1e-3) ** 2 / 4
    EG = 2 * (1 + WIRE["nu"].v)
    return r["k_pair"] * r["L"] * (1 + ALPHA_SHEAR * EG) / (WIRE["E"].v * A)


def geometry_path(path, n=4001):
    """Polyline + circular arc link (see support.link_path): eye -> back across the cup face -> inward along
    the module side to the head -> semicircle-like arc behind the head to the other side (symmetric).
    Returns the same integrals as geometry(): moment arm is the distance from the eye-to-eye chord (Y = 0)."""
    ex, hy, sx, ap = path["eye_x"], path["hook_y"], path["side_x"], path["apex"]
    pts = [(ex, 0.0), (ex, hy), (sx, hy)]
    # arc from (sx, hy) around the back to (-sx, hy) passing through (0, hy - ap_depth)
    depth = ap
    R = (sx ** 2 + depth ** 2) / (2 * depth)
    cy = hy - depth + R
    th0 = math.atan2(hy - cy, sx); th1 = math.atan2(hy - cy, -sx)
    ths = np.linspace(th0, th1 - 2 * math.pi if th1 > th0 else th1, 400)
    arc = [(cy * 0 + R * math.cos(t), cy + R * math.sin(t)) for t in ths]
    half = pts + arc[1:len(arc) // 2 + 1]
    P = np.array(half)
    seg = np.diff(P, axis=0); L = np.linalg.norm(seg, axis=1); mid = (P[1:] + P[:-1]) / 2
    x = np.abs(mid[:, 1])
    I2 = 2 * np.sum(x ** 2 * L)
    return dict(w=ex, R=R, s=depth, I2=I2, L=2 * L.sum(), x_max=float(np.abs(P[:, 1]).max()))


def link_design(d_mm, P_nom, n_coil=0, eye_ri_=None, sagitta=SAGITTA, Dc=DC_COIL, path=None):
    g = geometry(sagitta) if path is None else geometry_path(path)
    d = d_mm * 1e-3
    E = WIRE["E"].v
    I = math.pi * d ** 4 / 64
    L_coil = math.pi * Dc * n_coil
    k_pair = E * I / (g["I2"] + g["x_max"] ** 2 * L_coil)
    Cc = Dc / d
    Ki = (4 * Cc ** 2 - Cc - 1) / (4 * Cc * (Cc - 1)) if n_coil else 1.0
    k_side = 2 * k_pair
    Sut = music_wire_Sut(d_mm)
    Sy = WIRE["Sy_ratio"].v * Sut
    Se = WIRE["Se_bend_ratio"].v * Sut
    P_min = P_nom - k_side * HEAD_VAR
    P_max = P_nom + k_side * HEAD_VAR
    P_don = P_max + k_side * DON_EXTRA
    sig = lambda P: Ki * 32 * P * g["x_max"] / (math.pi * d ** 3)
    # eye: inner radius = max(1.5 d, bushing radius); bushing chosen in design.derived
    r_i = eye_ri_ if eye_ri_ is not None else eye_ri(d_mm)
    r1 = r_i + d / 2
    C1 = 2 * r1 / d
    KA = (4 * C1 ** 2 - C1 - 1) / (4 * C1 * (C1 - 1))
    sig_eye = lambda P: P * (KA * 32 * r1 / (math.pi * d ** 3) + 4 / (math.pi * d ** 2))
    s_don = max(sig(P_don), sig_eye(P_don))
    # fatigue: donning cycle from worn (P_max) to donning spread (P_don) -> mean/alternating
    s_a = (sig(P_don) - sig(P_min)) / 2; s_m = (sig(P_don) + sig(P_min)) / 2
    # finite-life endurance at N cycles (Basquin between 1e3 @0.9Sut and 1e6 @Se)
    N = N_DON
    b = math.log10(0.9 * Sut / Se) / -3.0
    Sf = 0.9 * Sut * (N / 1e3) ** (-b)
    n_goodman = 1 / (s_a / Sf + s_m / Sut)
    return dict(d_mm=d_mm, n_coil=n_coil, Ki=Ki, P=P_nom, k_pair=k_pair, k_side=k_side, P_min=P_min, P_max=P_max, P_don=P_don,
                delta0_side=P_nom / k_side, free_half_gap=g["w"] - P_nom / k_side,
                Sut=Sut, Sy=Sy, Se=Se, sigma_worn=sig(P_max), sigma_don=sig(P_don), sigma_eye_don=sig_eye(P_don),
                SF_yield=Sy / s_don, SF_fatigue=n_goodman, N_cycles=N, P_ratio=P_max / max(P_min, 1e-9), KA=KA, eye_ri=r_i,
                R=g["R"], L=g["L"], mass_g=WIRE["rho"].v * math.pi * d ** 2 / 4 * (g["L"] + L_coil) * 1e3,
                ok=(Sy / s_don >= SF_YIELD and n_goodman >= SF_FATIGUE and P_max / max(P_min, 1e-9) <= P_RATIO_MAX and P_min > 0))


STOCK_D_DS = [1.0, 1.2, 1.4, 1.5, 1.6, 1.8, 2.0]   # [DS] common music-wire stock sizes, mm
STOCK_D_A = [2.25, 2.5]                             # [A] assumed stocked (confirm with the wire supplier), mm
STOCK_D = STOCK_D_DS + STOCK_D_A
N_COILS = range(0, 13)   # [A] apex torsion coil up to 12 turns (24 mm long at d = 2 mm, Dc 12 mm behind the occiput)


def margin(r):
    """Smallest normalised margin of one link design (SF_yield/1.5, SF_fatigue/1.5, 2/P_ratio)."""
    return min(r["SF_yield"] / SF_YIELD, r["SF_fatigue"] / SF_FATIGUE, P_RATIO_MAX / r["P_ratio"])


def size_wire(P_nom, ds=None, ns=range(0, 9), path=None):
    """Sweep diameter x apex-coil turns. For each d the fewest turns that
    satisfy all criteria; chosen = the stock diameter with the largest
    minimum normalised margin (SF_yield/1.5, SF_fatigue/1.5, 2/P_ratio)."""
    ds = ds if ds is not None else np.round(np.arange(0.8, 2.51, 0.1), 2)
    grid = [[link_design(float(x), P_nom, n, path=path) for n in ns] for x in ds]
    best = []
    for row in grid:
        ok = [r for r in row if r["ok"]]
        best.append(ok[0] if ok else None)
    cands = []
    for sd in STOCK_D:
        for n in ns:
            r = link_design(sd, P_nom, n, path=path)
            if r["ok"]:
                cands.append(r); break
    chosen = max(cands, key=margin) if cands else None
    return grid, best, chosen, margin
