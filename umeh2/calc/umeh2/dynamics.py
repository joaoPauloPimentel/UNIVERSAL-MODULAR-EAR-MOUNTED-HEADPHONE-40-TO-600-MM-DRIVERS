"""
Natural frequencies and vibration isolation. NO modal FEA was run.

1. Rigid-body modes of the headphone on its contacts (6 DOF):
       K q = w^2 M q,   M = [[m I, -m [c]x], [m [c]x, I_O]]
   K = tangent stiffness of the active contacts + link at the static
   upright equilibrium (support.Model), solved with scipy.linalg.eigh.
2. Arm (cantilever) first bending mode by Rayleigh: f = (1/2pi) sqrt(k_tip / m_eff),
   m_eff = pad + (33/140) x arm mass (uniform cantilever, Rayleigh tip-mass equivalent, ARM_MASS_FACTOR).
3. Driver-in-module isolation: the driver rim sits on a TPU gasket; the
   driver reaction force (moving mass x diaphragm acceleration) is passed
   to the module through it. Single-DOF base-isolation transmissibility
       T(f) = sqrt(1 + (2 zeta r)^2) / sqrt((1 - r^2)^2 + (2 zeta r)^2), r = f/f_n
   (isolation only above sqrt(2) f_n).
4. Head-to-headphone transmissibility of walking/running excitation
   through the contact springs (same SDOF form per mode; undamped, which
   bounds T from above below sqrt(2) f_n), over the head-motion band F_HEAD [A].
"""
import math
import numpy as np
from scipy.linalg import eigh
from .materials import TPU
from . import support as sp

ARM_MASS_FACTOR = 33 / 140    # [STD] share of a uniform cantilever's mass at its tip for the first bending mode (Rayleigh)

F_HEAD = (1.0, 10.0)   # [A] Hz, head motion while walking or running (step rate and its first harmonics)


def skew(c):
    return np.array([[0, -c[2], c[1]], [c[2], 0, -c[0]], [-c[1], c[0], 0]])


def mass_matrix(M, com, Icom):
    I_O = Icom + M * (np.dot(com, com) * np.eye(3) - np.outer(com, com))
    Mm = np.zeros((6, 6))
    Mm[:3, :3] = M * np.eye(3)
    Mm[:3, 3:] = -M * skew(com)
    Mm[3:, :3] = M * skew(com)
    Mm[3:, 3:] = I_O
    return Mm


def tangent_stiffness(model, W):
    """Tangent stiffness of the active contacts + link + flexible arms at the static state, statically
    condensed onto the 6 rigid-body DOFs of the cradle (the arm nodes carry no mass here; the arms' own
    modes are computed separately): K_c = K_rr - K_rn K_nn^-1 K_nr [C]."""
    r = model.solve(W, fric=False)
    act = np.array([c["active"] for c in r["contacts"]])
    K = model.KL + model.KN[act].sum(0) + model.KT[act].sum(0)
    if K.shape[0] > 6:
        K = K[:6, :6] - K[:6, 6:] @ np.linalg.solve(K[6:, 6:], K[6:, :6])
    return K, r


def rigid_modes(mp, C, link):
    M, com, I = mp
    model = sp.Model(C, link)
    W = sp.inertial_wrench(M, com, I, np.array([0, -sp.G, 0]))
    K, r = tangent_stiffness(model, W)
    Mm = mass_matrix(M, com, I)
    w2, V = eigh(K, Mm)
    f = np.sqrt(np.maximum(w2, 0)) / (2 * math.pi)
    names = []
    for v in V.T:
        tr = np.linalg.norm(v[:3]); rot = np.linalg.norm(v[3:]) * 0.05     # compare at a 50 mm lever
        ax = "xyz"[int(np.argmax(np.abs(v[:3])))] if tr > rot else "xyz"[int(np.argmax(np.abs(v[3:])))]
        names.append(("translation " if tr > rot else "rotation about ") + ax)
    return f, V, names


def transmissibility(f, fn, zeta):
    r = f / fn
    return np.sqrt(1 + (2 * zeta * r) ** 2) / np.sqrt((1 - r ** 2) ** 2 + (2 * zeta * r) ** 2)


def driver_isolation(D, drv_mass_g, gasket_t_mm, rim_od_mm, rim_w_mm=2.5, squeeze_mm=0.3, zeta=0.10):
    """Axial stiffness of the rim gasket (annulus, TPU 95A solid). Shape factor S = loaded area /
    free (bulge) area; compression modulus Ec = E (1 + 2 k S^2), k = 0.75 [LIT, rubber blocks]."""
    E = TPU["E"].v
    ro = rim_od_mm / 2e3; ri = ro - rim_w_mm * 1e-3
    A = math.pi * (ro ** 2 - ri ** 2)
    t = (gasket_t_mm - squeeze_mm) * 1e-3
    S = A / (2 * math.pi * (ro + ri) * t)
    Ec = E * (1 + 2 * 0.75 * S ** 2)
    k = Ec * A / t
    m = drv_mass_g * 1e-3
    fn = math.sqrt(k / m) / (2 * math.pi)
    return dict(k=k, S=S, Ec=Ec, fn=fn, zeta=zeta, iso_from=math.sqrt(2) * fn)
