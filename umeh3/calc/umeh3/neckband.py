"""
Neckband (user's choice 2026-10-01, for treadmill running): a music-wire band behind the head joins the two sides, like
a sport headphone. Its preload pulls each side towards the head (the pad ring then grips by friction) and the cable is
clipped to the band at the eye, so cable tugs reach the module at the eye instead of at the socket [A: design choice].

The band is the UMEH-2 occipital link (umeh2.linkspring: planar wire, preload P at the eyes, side rate k_side,
Castigliano; wire sized for yield / fatigue / head-size spread) on a path from the eye on the rear-bottom of the shell
back along the module side and around the back of the head at the nape. In the contact model it is a second preloaded
spring (-z at the eye, k_side; tangential K_T [A]) next to the pinna clamp.
"""
import math
import numpy as np
from umeh2 import support as sp
from umeh2 import linkspring as ls
from umeh2.design import ANTHRO
from . import geom

K_T = 40.0               # [A] N/m fore-aft / vertical stiffness of the band at the eye (umeh2 K_LINK_T)
NAPE_APEX = 0.075        # [A] m: the band runs around the nape, 75 mm behind the eye line (below the occipital bump)
LINK_SHARE = 0.35        # [A] share of the half band's mass carried by one side (rest lies on the neck / hair)
EYE_XY = [0.0, 0.0]      # mm: eye position on the back of the cup (on the pad axis: the band's pull loads the pad
                         # ring evenly; an eye on the shell rim tilts the module and lifts the opposite pad sector)
EYE_Z_OUT = -1.2         # mm, the wire's line of action relative to the cup end: in the back channel (geom.NECK_EYE_Z)


def eye_point():
    """Eye on the back of the cup (mm, skin frame)."""
    return np.array([EYE_XY[0], EYE_XY[1], geom.Z_F + geom.CUP_H + EYE_Z_OUT])


def path(eye_mm):
    hw = ANTHRO["head_half_width"] * 1e-3
    ze = eye_mm[2] * 1e-3
    # from the eye the wire runs back across the cup face past the module's rear edge, inward along its side, then
    # around the nape
    hook = (geom.POCKET_R + geom.HUB_WALL + 4.0) * 1e-3
    return dict(eye_x=hw + ze, hook_y=-hook, side_x=hw + 0.006, apex=NAPE_APEX)


def design(P, eye_mm=None):
    """Wire sized for preload P (umeh2.linkspring.size_wire); returns the chosen design dict."""
    eye_mm = eye_point() if eye_mm is None else eye_mm
    _, _, chosen, _ = ls.size_wire(P, ns=range(0, 9), path=path(eye_mm))
    return chosen


class ModelN(sp.Model):
    """umeh2.support.Model with several preloaded springs: links[0] is reported as link_force (the pinna clamp),
    the others (the neckband) only add their stiffness and preload."""

    def __init__(self, C, links):
        if not isinstance(links, list):
            links = [links]
        super().__init__(C, links[0])
        for rp, P, kz, kt in links[1:]:
            for e, kk in [(np.array([0, 0, 1.0]), kz), (np.array([1.0, 0, 0]), kt), (np.array([0, 1.0, 0]), kt)]:
                jj = np.r_[e, np.cross(rp, e)]; self.KL[:6, :6] += kk * np.outer(jj, jj)
            f = np.array([0, 0, -P]); self.WL[:6] += np.r_[f, np.cross(rp, f)]


def with_band(mp, P):
    """Mass properties (M, com, I, p_cable, rows) with the band's carried share as a point mass at the eye and the
    cable clipped to the band at the eye."""
    M, com, I, p_c, rows = mp
    e = eye_point() * 1e-3
    dz = design(P)
    m = LINK_SHARE * dz["mass_g"] / 2 * 1e-3 * 1.6      # x1.6 [A]: silicone sleeve + cable clips on the band
    M2 = M + m
    com2 = (M * com + m * e) / M2
    d1, d2 = com - com2, e - com2
    I2 = I + M * (np.dot(d1, d1) * np.eye(3) - np.outer(d1, d1)) + m * (np.dot(d2, d2) * np.eye(3) - np.outer(d2, d2))
    return M2, com2, I2, e, rows
