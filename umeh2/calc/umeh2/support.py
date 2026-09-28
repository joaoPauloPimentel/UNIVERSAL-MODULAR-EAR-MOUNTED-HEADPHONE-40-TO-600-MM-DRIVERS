"""
Ear-attachment statics as a STATICALLY INDETERMINATE rigid body on
compliant, unilateral contacts.

Frame (right side, "skin frame", SI units):
    x forward, y up, z lateral/outward (away from the head), origin at the
    ring axis on the skin plane of the temporal/mastoid pads.

The ring is a rigid body; each ARM is flexible: its PETG compliance (structure.arm_tip_compliance,
unit-load method over foot, leg and bar) sits in series with the contacts it carries, as extra degrees of
freedom (a 3-DOF node at the pad for a one-contact arm, a 6-DOF node at the arm tip for the saddle arm,
whose cap carries several contacts). The saddle arm is about as compliant as its contacts, so a rigid-arm
model would misplace the load sharing. It is held by
    S_root   saddle on the top of the helix-root / auricle root   (normal +radial @ saddle_a)
    S_helix  lateral face of the saddle cap against the medial face of the
             upper helix that overhangs it (normal -z)            [A: contact exists for
             protrusion >= 15 mm; sensitivity run with it removed]
    T        temporal pad on the skin                            (normal +z)
    M        mastoid pad on the skin                             (normal +z)
    L        occipital spring link at the mastoid eye            (bilateral spring + preload, -z)
Each contact = normal spring (k_n, compression only) + two tangential
springs (k_t = 0.5 k_n [A], active only while the normal is in contact).
Load sharing therefore follows STIFFNESS, never an equal split.

A contact point displaces by  d = u + theta x r ; with n the outward
normal of the supporting surface the compression is  delta = -n.d  and the
force on the device is  k delta n. For the 6-vector q = [u, theta] the
row j = [n, r x n] gives delta = -j.q and the wrench -k j j^T q, so
    K q = W ,  K = sum_i k_i j_i j_i^T    (active set iterated)
All 6 equilibrium equations (sum F = 0, sum M = 0) are satisfied exactly
by construction; the residual is printed as a check. With flexible arms q is extended by the arm-node
displacements v (K_arm v = contact forces on the arm) and the rows j gain the terms n.L_i, L_i mapping
the node motion to the contact point.
"""
import math
import numpy as np
from .materials import G, TPU, TPU_PAD_EFF, TISSUE, FRICTION, CABLE, WIRE, SILICONE, SILICONE_GEL
from . import structure as st

KT_RATIO = 0.5          # [A] tangential/normal contact stiffness (soft tissue, Mindlin ~ 2(1-nu)/(2-nu) ~ 0.67 bulk; 0.5 conservative for skin shear layer)
# Small-displacement validity of the rigid-body/linear-contact model [A]. A solution that needs more
# rigid-body displacement or rotation than this is NOT an equilibrium of the real (large-motion, sliding)
# problem: the cradle is held only by soft springs (link, tangential stiffness) -> classified as gross
# slip / release, exactly like a singular stiffness matrix.
DISP_MAX = 3.0e-3      # m
ROT_MAX = 5.0          # deg
F_MIN = 0.10            # [A] N, minimum normal force regarded as "in contact" (noise, hair, sweat film)
PEAK_FACTOR = 2.0       # [C] peak/mean pressure of a dome on a thin soft layer over bone: paraboloid on a Winkler bed,
                        # p(r) = k (delta - r^2/2R) -> peak = 2 x mean (a Hertz half-space would give 1.5); same model as
                        # the contact-stress table (extras.pad_contact)
K_HELIX = 400.0         # [A] N/m, upper-helix cartilage stiffness pushing the helix outward
K_HELIX_RANGE = (150.0, 1000.0)   # [A] N/m, plausible range of that stiffness
K_LINK_T = 40.0         # [A] N/m, lateral/vertical stiffness of the link at the eye (wire twists easily)
EYE_Z_CUP = 1.0         # [A] mm, the wire's line of action above the cup end face at the eye (on the eye sleeve)

# head rotation axes (points in skin frame, m) [A: from head anthropometry]
AXES = {
    "yaw (turn)":  (np.array([0, 1.0, 0]), np.array([-0.005, 0.0, -0.075])),
    "pitch (nod)": (np.array([0, 0, 1.0]), np.array([-0.010, -0.045, -0.075])),
    "roll (tilt)": (np.array([1.0, 0, 0]), np.array([0.0, -0.120, -0.075])),
}
# head angular velocity / acceleration levels [A, from gait and head-motion literature: walking pitch
# alpha 10–50 rad/s^2, running 50–150, deliberate head shake up to ~200; impacts/jolts > 500]
OMEGA = {"normal": 3.0, "dynamic": 6.0, "severe": 10.0, "accidental": 20.0}          # rad/s
ALPHA = {"normal": 50.0, "dynamic": 100.0, "severe": 200.0, "accidental": 1000.0}    # rad/s^2


def pol(r, a_deg, z):
    a = math.radians(a_deg)
    return np.array([r * math.cos(a), r * math.sin(a), z])


PAD_AREA_FRAC = 0.5     # [A] loaded share of a dome pad's ellipse footprint


def pad_area(a_mm, b_mm, frac=PAD_AREA_FRAC):
    """Contact area of the dome pad: frac [A] of the ellipse footprint is loaded."""
    return math.pi * a_mm * b_mm / 4 * frac * 1e-6


ROOT_LEN = 25.0     # [A] mm straight length of the superior auricle root the saddle bar can bear on
ROOT_W = 8.0        # [A] mm loaded width across the root (bar Ø16 on a ~6 mm radius root)
ROOT_ARCH_R = 22.0  # [A] mm radius of the superior auricle-root arch seen from the side (range 18–30)
ROOT_PHI = 35.0     # [A] deg, half-angle to the two bearing zones on that arch (range 25–45)


def _pad_k(a_mm, b_mm, pad_h_mm, E_tis, t_tis, frac=PAD_AREA_FRAC, t_face_mm=0.0):
    """Series stiffness: TPU dome core (15 % gyroid) + silicone facing (if any) + soft tissue layer."""
    A = pad_area(a_mm, b_mm, frac)
    E_pad = TPU["E"].v * TPU_PAD_EFF["infill15"].v
    c = (pad_h_mm - t_face_mm) * 1e-3 / (E_pad * A) + t_face_mm * 1e-3 / (SILICONE["E"].v * A) + t_tis / (E_tis * A)
    return 1 / c, A


def liner_compliance(des, w_mm, l_mm):
    """Normal compliance (m/N) of the soft silicone liner cast on the saddle bar over one loaded root patch
    w x l (mm): a thin incompressible layer bonded to the cap and gripping the skin, E_c = E (1 + 2 k S^2)
    (Gent-Lindley), S = w l / (2 (w + l) t). 0 without a liner."""
    t = des.get("saddle_liner_t", 0.0)
    if t <= 0:
        return 0.0
    S = w_mm * l_mm / (2 * (w_mm + l_mm) * t)
    Ec = SILICONE_GEL["E"].v * (1 + 2 * SILICONE_GEL["k_gent"].v * S ** 2)
    return t * 1e-3 / (Ec * w_mm * l_mm * 1e-6)


def contact_set(d, des, k_helix=K_HELIX, helix=None, mu_level=0, mu_override=None, scalp=None, mu_scale=1.0):
    """Contact definitions from the CAD numbers (d = design.derived).
    Design B:  T, M, S root (+ S helix).  Final: + P post pad, + S scalp."""
    helix = des.get("rely_helix", True) if helix is None else helix
    scalp = des.get("saddle_scalp", False) if scalp is None else scalp
    C = []

    def add(name, r, n, k, area, mu_key, bilateral=False):
        n = np.asarray(n, float); n /= np.linalg.norm(n)
        t1 = np.cross(n, [0, 0, 1.0]) if abs(n[2]) < 0.9 else np.cross(n, [1.0, 0, 0])
        t1 /= np.linalg.norm(t1); t2 = np.cross(n, t1)
        C.append(dict(name=name, r=np.asarray(r) * 1e-3, n=n, t=[t1, t2], k=k, kt=KT_RATIO * k,
                      area=area, mu=mu_scale * (mu_override if mu_override is not None else FRICTION[mu_key][0][mu_level]),
                      mu_key=mu_key, bilateral=bilateral))

    tf = des.get("pad_face_t", 0.0) if des.get("pad_face") else 0.0
    skin_key = "silicone/dry skin" if des.get("pad_face") == "silicone" else "TPU/dry skin"
    k, A = _pad_k(des["pad_t_a"], des["pad_t_b"], des["pad_h"], TISSUE["E_temporal"].v, TISSUE["t_temporal"].v, t_face_mm=tf)
    add("T temporal", pol(des["temporal_r"], des["temporal_a"], 0), [0, 0, 1], k, A, skin_key)
    k, A = _pad_k(des["pad_m_a"], des["pad_m_b"], des["pad_h"], TISSUE["E_mastoid"].v, TISSUE["t_mastoid"].v, t_face_mm=tf)
    add("M mastoid", pol(des["mastoid_r"], des["mastoid_a"], 0), [0, 0, 1], k, A, skin_key)
    if des.get("post_a") is not None:
        k, A = _pad_k(des["pad_p_a"], des["pad_p_b"], des["pad_h"], TISSUE["E_temporal"].v, TISSUE["t_temporal"].v)
        add("P post-sup", pol(des["post_r"], des["post_a"], 0), [0, 0, 1], k, A, "TPU/hair (over temporal)")
    # saddle: Ø16 bearing bar of the cap on the superior auricle root
    r_root = des["saddle_r"] - des["foot_t"] / 2 - 16.0 + 1.0
    cap_t = des["saddle_cap_wall"] * 1e-3
    E_cap = TPU["E"].v * 0.6                     # [A] bearing zone of the cap is mostly perimeter walls
    z_r = des["saddle_skin_gap"] + des["foot_t"] / 2
    root_key = "silicone/dry skin" if des.get("saddle_liner_t", 0.0) > 0 else "TPU/dry skin"
    if des.get("saddle_arch", False):
        # Final: bar curved to the auricle-root arch (radius ROOT_ARCH_R); two bearing zones at
        # +-phi whose normals tilt fore/aft -> the cradle is LOCATED fore-aft by normal forces
        # (eyeglass-temple principle) instead of by friction alone.
        phi = math.radians(des.get("arch_phi", ROOT_PHI))
        a0 = math.radians(des["saddle_a"])
        top = np.array([r_root * math.cos(a0), r_root * math.sin(a0)])
        u = np.array([math.cos(a0), math.sin(a0)]); t = np.array([-math.sin(a0), math.cos(a0)])
        ctr = top - ROOT_ARCH_R * u
        L_zone = min(des["saddle_cap_L"] - 8.0, ROOT_LEN) / 2
        A_r = ROOT_W * L_zone * 0.7 * 1e-6
        k_r = 1 / (cap_t / (E_cap * A_r) + liner_compliance(des, ROOT_W, L_zone * 0.7)
                   + TISSUE["t_root"].v / (TISSUE["E_root"].v * A_r))
        for sgn, nm in ((+1, "S root F"), (-1, "S root B")):
            nv = math.cos(phi) * u + sgn * math.sin(phi) * (-t)    # -t points forward (+x) at the top (a0 ~ 90 deg)
            pt = ctr + ROOT_ARCH_R * nv
            add(nm, [pt[0], pt[1], z_r], [nv[0], nv[1], 0], k_r, A_r, root_key)
    else:
        L_r = min(des["saddle_cap_L"] - 8.0, ROOT_LEN)
        A_r = ROOT_W * L_r * 0.7 * 1e-6
        k_r = 1 / (cap_t / (E_cap * A_r) + liner_compliance(des, ROOT_W, L_r * 0.7)
                   + TISSUE["t_root"].v / (TISSUE["E_root"].v * A_r))
        add("S root", pol(r_root, des["saddle_a"], z_r),
            [math.cos(math.radians(des["saddle_a"])), math.sin(math.radians(des["saddle_a"])), 0], k_r, A_r, root_key)
    if scalp:
        A_s = 14.0 * des["saddle_cap_L"] * 0.4e-6   # [A] 40 % of the cap's medial footprint touches the scalp
        k_s = 1 / (cap_t / (E_cap * A_s) + TISSUE["t_temporal"].v / (TISSUE["E_temporal"].v * A_s))
        add("S scalp", pol(des["saddle_r"] - 8.0, des["saddle_a"], 0), [0, 0, 1], k_s, A_s, "TPU/hair (over temporal)")
    if helix:
        z_h = des["saddle_skin_gap"] + des["foot_t"] + des["saddle_cap_wall"]
        add("S helix", pol(r_root + 6.0, des["saddle_a"], z_h), [0, 0, -1], k_helix, 120e-6, "TPU/dry skin")
    if des.get("flex_arms", True):
        attach_arm_nodes(C, d, des)
    return C


ARM_OF = {"T temporal": "temporal", "M mastoid": "mastoid", "P post-sup": "post", "S root": "saddle",
          "S root F": "saddle", "S root B": "saddle", "S scalp": "saddle", "S helix": "saddle"}


def attach_arm_nodes(C, d, des):
    """Arm flexibility in series with the contacts: one node per arm. An arm carrying one contact gets a
    3-DOF node at the contact point with K = (L C_tip L^T)^-1; an arm carrying several (the saddle cap) gets a
    6-DOF node at its tip with K = C_tip^-1, the contacts riding on it rigidly (the TPU cap's own compliance
    is in the contact springs). C_tip from structure.arm_tip_compliance [C]."""
    for arm in dict.fromkeys(ARM_OF[c["name"]] for c in C if c["name"] in ARM_OF):
        idx = [i for i, c in enumerate(C) if ARM_OF.get(c["name"]) == arm]
        P0, Ct = st.arm_tip_compliance(d, des, arm)
        if len(idx) == 1:
            Lm = st.point_map(C[idx[0]]["r"], P0)
            node = dict(id=arm, m=3, r=C[idx[0]]["r"], K=np.linalg.inv(Lm @ Ct @ Lm.T))
        else:
            node = dict(id=arm, m=6, r=P0, K=np.linalg.inv(Ct))
        node["K"] = 0.5 * (node["K"] + node["K"].T)
        for i in idx:
            C[i]["node"] = node
    return C


def eye_point(d, des):
    """Where the link force acts (m). Design B: on the mastoid pad seat.
    Final: on a boss on the ring rim at link_a."""
    mode = des.get("link_mode", "mastoid")
    if mode == "mastoid":
        return pol(des["mastoid_r"], des["mastoid_a"], des["pad_h"] + des["foot_t_mastoid"]) * 1e-3
    if mode == "cup":
        return np.array([des["link_x"], des["link_y"], d["z_cuptop"] + EYE_Z_CUP]) * 1e-3
    return pol(d["link_r"], des["link_a"], des["standoff"] + 2.0) * 1e-3


LINK_EDGE_GAP = 4e-3     # [A] the wire passes the module's rear edge this far outside the spigot radius
LINK_SIDE_GAP = 6e-3     # [A] the wire's clearance off the head where it runs inward along the module side
LINK_APEX_EXTRA = 15e-3  # [A] apex of the cup-eye link behind the eye line: SAGITTA + this (the cup eye sits forward of the mastoid)


def link_path(d, des):
    """Planar link path (head-centred: X lateral, Y fore-aft, m) used by linkspring for the spring rate
    and stresses. mode 'cup': from the eye on the cup end (link_x fore-aft of the cup centre) the wire runs back
    across the cup face past the module's rear edge, inward along the module side to the head, then around the
    occiput. Other modes: None (linkspring's circular arc through the mastoid eyes)."""
    from .linkspring import SAGITTA
    from .design import ANTHRO
    hw = ANTHRO["head_half_width"] * 1e-3
    if des.get("link_mode", "mastoid") == "cup":
        ze = (d["z_cuptop"] + EYE_Z_CUP) * 1e-3
        Rm = d["spig_d"] / 2e3 + LINK_EDGE_GAP
        return dict(eye_x=hw + ze, hook_y=-(Rm + des["link_x"] * 1e-3), side_x=hw + LINK_SIDE_GAP, apex=SAGITTA + LINK_APEX_EXTRA)
    return None


def make_link(d, des):
    from .linkspring import link_design
    L = link_design(des["wire_d"], des["link_preload"], des.get("link_coils", 0), path=link_path(d, des))
    return (eye_point(d, des), des["link_preload"], L["k_side"], K_LINK_T), L


class Model:
    """Pre-assembled contact model (vectorised for speed). Same mechanics as described in the
    module docstring; unilateral normals + stick/slip tangential springs + bilateral link."""

    def __init__(self, C, link):
        self.C = C
        n = len(C)
        self.n = n
        self.k = np.array([c["k"] for c in C]); self.kt = np.array([c["kt"] for c in C])
        self.mu = np.array([c["mu"] for c in C]); self.area = np.array([c["area"] for c in C])
        self.bil = np.array([c["bilateral"] for c in C])
        # degrees of freedom: 6 rigid-body (ring) + the flexible-arm nodes attached to the contacts
        self.nodes = []
        off = 6
        for c in C:
            nd = c.get("node")
            if nd is not None and all(nd["id"] != x["id"] for x in self.nodes):
                self.nodes.append(dict(nd, off=off)); off += nd["m"]
        self.ndof = ndof = off
        noff = {x["id"]: x["off"] for x in self.nodes}
        JN = np.zeros((n, ndof)); JT = np.zeros((n, 2, ndof))
        for i, c in enumerate(C):
            JN[i, :6] = np.r_[c["n"], np.cross(c["r"], c["n"])]
            for a_, t in enumerate(c["t"]):
                JT[i, a_, :6] = np.r_[t, np.cross(c["r"], t)]
            nd = c.get("node")
            if nd is not None:
                o = noff[nd["id"]]
                Lm = np.eye(3) if nd["m"] == 3 else st.point_map(c["r"], nd["r"])
                JN[i, o:o + nd["m"]] = c["n"] @ Lm
                for a_, t in enumerate(c["t"]):
                    JT[i, a_, o:o + nd["m"]] = t @ Lm
        self.JN = JN; self.JT = JT                                                        # (n,ndof), (n,2,ndof)
        self.KN = self.k[:, None, None] * np.einsum("ni,nj->nij", self.JN, self.JN)
        self.KT = self.kt[:, None, None] * np.einsum("nai,naj->nij", self.JT, self.JT)
        self.KL = np.zeros((ndof, ndof)); self.WL = np.zeros(ndof); self.link = link
        for x in self.nodes:
            self.KL[x["off"]:x["off"] + x["m"], x["off"]:x["off"] + x["m"]] = x["K"]
        if link is not None:
            rp, P, kz, kt = link
            for e, kk in [(np.array([0, 0, 1.0]), kz), (np.array([1.0, 0, 0]), kt), (np.array([0, 1.0, 0]), kt)]:
                jj = np.r_[e, np.cross(rp, e)]; self.KL[:6, :6] += kk * np.outer(jj, jj)
            f = np.array([0, 0, -P]); self.WL[:6] = np.r_[f, np.cross(rp, f)]
        # step / residual scaling: rotations (ring and 6-DOF arm nodes) count as displacements at L_REF
        self.scale = np.ones(ndof); self.scale[3:6] = self.L_REF
        for x in self.nodes:
            if x["m"] == 6:
                self.scale[x["off"] + 3:x["off"] + 6] = self.L_REF

    def _pad(self, W):
        """Loads act on the ring (6 rigid-body DOFs); the arm nodes carry no external load."""
        W = np.asarray(W, float)
        return W if W.shape[0] == self.ndof else np.r_[W, np.zeros(self.ndof - W.shape[0])]

    # ---------------------------------------------------------------- incremental Coulomb friction
    # Quasi-static elastic-frictional contact solved INCREMENTALLY, as in rate-independent plasticity.
    # Each contact: unilateral normal spring k_n; tangential spring k_t in series with a rigid-plastic
    # slider (slip offset s) whose force is bounded by g = mu F_n (Coulomb). For one load increment with
    # the bounds g held fixed (Tresca), backward-Euler return mapping gives the exact incremental
    # potential of the whole cradle
    #     Pi(q) = 1/2 q.K_L.q - q.(W + W_L) + sum 1/2 k_n <-j_n.q>_+^2 + sum H(|J_t q - s_old|)
    #     H(t)  = 1/2 k_t t^2                      if k_t t <= g   (stick)
    #           = g t - g^2 / (2 k_t)              otherwise       (slide, Huber)
    # which is CONVEX and C1 in the six rigid-body coordinates q, so its minimiser is unique up to flat
    # directions and is found by damped Newton iteration without any stick/slip active-set guessing.
    # Coulomb's law (g depends on the unknown F_n) is reached by successive Tresca approximations
    # (fixed point g <- mu F_n). A separated contact has g = 0, so its tangential spring carries nothing
    # and re-anchors (s = u_t) - it grips again from its new position when it re-closes. A sliding
    # contact re-sticks automatically when its trial force falls back inside the cone.
    # Gross slip / release = no bounded minimiser (Pi decreases without limit: the loads cannot be
    # equilibrated inside the friction cones) or a minimiser outside the small-displacement range
    # (DISP_MAX, ROT_MAX). Loads are applied from the donned state (link preload, head upright, 1 g) to
    # the case load in N_STEPS proportional increments, so the answer is the path-dependent state.
    # Load-step cutting. A minimisation can also stop without being unbounded: the line search runs out of
    # representable decrease, or the iteration / Coulomb fixed-point limit is reached, at a small, bounded
    # displacement. That is a numerical failure of the increment, not a release (found by the dense 1 g
    # check: isolated cases that "released" at 4 increments hold at 5, 8 and 32, and at the load scaled by
    # 1 +/- 1e-4). Such a stalled increment is split in two halves solved in turn from the last converged
    # state, recursively up to MAX_CUTS times (increments down to 1/2^MAX_CUTS of one step); a runaway
    # (displacement beyond 3 DISP_MAX / 3 ROT_MAX during the minimisation) or a converged state beyond the
    # small-displacement range is a release at once. A stall that survives every cut is still counted as a
    # release (conservative) and is labelled as numerical in its reason.
    N_STEPS = 4
    MAX_CUTS = 3
    L_REF = 0.05          # m, converts rotations to contact-point displacements for step control
    STEP_MAX = 0.4e-3     # m, largest Newton step (scaled) - keeps runaway (released) cases finite
    TOL = 1e-8            # N (moments / L_REF): equilibrium residual; loads are O(1 N), round-off floor ~1e-9

    def _fresh(self):
        n = self.n
        return dict(q=np.zeros(self.ndof), s=np.zeros((n, 2)), g=np.zeros(n))

    def _terms(self, q, s_old, rr):
        """rr = g / k_t: radius of the stick region of each tangential spring (inf = never slips)."""
        dn = -self.JN @ q
        act = self.bil | (dn > 0)
        Fn = np.where(act, self.k * dn, 0.0)
        tv = self.JT @ q - s_old
        tm = np.sqrt(tv[:, 0] ** 2 + tv[:, 1] ** 2)
        stick = tm <= rr
        return dn, act, Fn, tv, tm, stick

    def _pi(self, q, W, s_old, gf, rr):
        dn, act, Fn, tv, tm, stick = self._terms(q, s_old, rr)
        kt = self.kt
        ht = np.where(stick, 0.5 * kt * tm ** 2, gf * tm - gf ** 2 / (2 * kt))
        dna = np.where(act, dn, 0.0)
        return 0.5 * q @ self.KL @ q - q @ (W + self.WL) + 0.5 * float(self.k @ (dna * dna)) + float(ht.sum())

    def _first_kink(self, q, d, s_old, rr, dn, tv, tm):
        """Smallest step fraction in (0, 1] at which a contact changes piece along q + a d (normal contact
        opens/closes, tangential spring enters/leaves its stick disc). Up to that point the Newton model is
        exact, so the step is a guaranteed descent without a line search."""
        a_min = 1.0
        ddn = -self.JN @ d
        with np.errstate(divide="ignore", invalid="ignore"):
            an = np.where(~self.bil & (dn * (dn + ddn) < 0), -dn / ddn, np.inf)
        a_min = min(a_min, float(np.min(np.where(an > 1e-10, an, np.inf))))
        dtv = self.JT @ d
        A = dtv[:, 0] ** 2 + dtv[:, 1] ** 2
        B = tv[:, 0] * dtv[:, 0] + tv[:, 1] * dtv[:, 1]
        fin = np.isfinite(rr) & (A > 0)
        Cc = np.where(fin, tm ** 2 - np.where(fin, rr, 0.0) ** 2, 0.0)
        disc = B * B - A * Cc
        ok = fin & (disc >= 0)
        sq = np.sqrt(np.where(ok, disc, 0.0))
        Asafe = np.where(A > 0, A, 1.0)
        for root in ((-B - sq) / Asafe, (-B + sq) / Asafe):
            r_ = np.where(ok & (root > 1e-10), root, np.inf)
            a_min = min(a_min, float(r_.min()))
        return a_min

    def _minimise(self, W, s_old, g, q0, max_it=400, fixed=()):
        """Newton on the convex incremental potential for fixed Tresca bounds g, with each step truncated at
        the first kink of the piecewise-quadratic potential (backtracking only as a safeguard).
        `fixed`: indices of q held at their start value (a hand holding the cradle while it is donned)."""
        q = q0.copy()
        ndof = self.ndof
        free = np.ones(ndof, bool); free[list(fixed)] = False
        kt = self.kt
        gf = np.where(np.isfinite(g), g, 0.0)
        with np.errstate(divide="ignore", invalid="ignore"):
            rr = np.where(np.isfinite(g), g / kt, np.inf)
        scale = self.scale
        fscale = 1 / scale
        reg_m = np.diag(1 / scale ** 2)
        FF = np.outer(free, free)
        I2 = np.eye(2)[None]
        gn_ro = None                             # residual when the last round-off-level step was taken
        for it in range(max_it):
            dn, act, Fn, tv, tm, stick = self._terms(q, s_old, rr)
            safe = np.maximum(tm, 1e-300)
            Gt = np.where(stick[:, None], kt[:, None] * tv, (gf / safe)[:, None] * tv)
            grad = self.KL @ q - (W + self.WL) - self.JN.T @ Fn + np.einsum("na,nai->i", Gt, self.JT)
            grad = np.where(free, grad, 0.0)
            gn = np.max(np.abs(grad * fscale))
            if gn < self.TOL:
                return True, q, it
            H = self.KL + np.einsum("n,ni,nj->ij", self.k * act, self.JN, self.JN)
            that = tv / safe[:, None]
            H2 = np.where(stick[:, None, None], kt[:, None, None] * I2,
                          (gf / safe)[:, None, None] * (I2 - np.einsum("na,nb->nab", that, that)))
            H = H + np.einsum("nai,nab,nbj->ij", self.JT, H2, self.JT)
            reg = 1e-9 * max(np.trace(H), 1e-12) / ndof
            H = np.where(FF, H, np.eye(ndof))
            d = -np.linalg.solve(H + reg * reg_m, grad)
            d[~free] = 0.0
            dsz = float(np.linalg.norm(d * scale))
            if dsz < 1e-11 and gn < 1e3 * self.TOL:
                # full Newton step below 1e-8 mm: the energy change is at floating-point resolution
                return True, q + d, it
            if dsz > self.STEP_MAX:
                d *= self.STEP_MAX / dsz
            slope = float(grad @ d)
            if slope >= 0:                       # not a descent direction (numerical): steepest descent
                d = -grad * scale ** 2
                d[~free] = 0.0
                d *= 0.1 * self.STEP_MAX / max(float(np.linalg.norm(d * scale)), 1e-300)
                slope = float(grad @ d)
            a = self._first_kink(q, d, s_old, rr, dn, tv, tm)
            f0 = self._pi(q, W, s_old, gf, rr)
            # Energy resolution. Near equilibrium the predicted decrease of a Newton step falls below the
            # floating-point resolution of Pi (~1e-16 |Pi|); comparing energies then only compares round-off
            # and the Armijo test rejects a correct step. Such a step (already truncated at the first kink,
            # where the model is exact for the contact terms) is taken on the model's word, and the gradient
            # test decides convergence. A round-off step that does not at least halve the residual ends the
            # iteration (converged if the residual is within 100 TOL, as for an exhausted line search).
            pred = a * slope + 0.5 * a * a * float(d @ H @ d)
            if -pred < 1e-13 * max(abs(f0), 1e-12):
                if gn_ro is not None and gn > 0.5 * gn_ro:
                    return gn < 100 * self.TOL, q, it
                gn_ro = gn
                q = q + a * d
                continue
            gn_ro = None
            while self._pi(q + a * d, W, s_old, gf, rr) > f0 + 1e-4 * a * slope and a > 1e-12:
                a *= 0.5
            if a <= 1e-12:                       # no further decrease representable in floating point
                return gn < 100 * self.TOL, q, it
            q = q + a * d
            if np.linalg.norm(q[:3]) > 3 * DISP_MAX or math.degrees(np.linalg.norm(q[3:6])) > 3 * ROT_MAX:
                return False, q, it              # runaway: no bounded equilibrium near the worn position
        return False, q, max_it

    @staticmethod
    def _runaway(q):
        return bool(np.linalg.norm(q[:3]) > 3 * DISP_MAX or math.degrees(np.linalg.norm(q[3:6])) > 3 * ROT_MAX)

    def _level(self, W, st, fric, max_it=60):
        """Equilibrium at one load level from state st (slip offsets s, bounds g of the previous level).
        On failure the returned state carries stalled = True when the minimisation stopped at a bounded position
        (numerical: see load-step cutting above) and False for a runaway (no bounded equilibrium)."""
        s_old = st["s"]
        q = st["q"].copy()
        if not fric:
            g = np.full(self.n, np.inf)
            ok, q, _ = self._minimise(W, s_old, g, q)
            if not ok:
                return False, None, "released (no bounded equilibrium)"
            return True, self._update(q, s_old, g), ""
        rel = "released: gross slip (no bounded equilibrium inside the friction cones)"
        stall = "no converged equilibrium (minimiser stalled at a bounded position; numerical, counted as a release)"
        g = st["g"].copy()
        for k in range(max_it):
            ok, q, _ = self._minimise(W, s_old, g, q)
            if not ok:
                run = self._runaway(q)
                return False, dict(q=q, stalled=not run), rel if run else stall
            dn = -self.JN @ q
            Fn = np.where(self.bil | (dn > 0), self.k * dn, 0.0)
            g_new = self.mu * np.maximum(Fn, 0.0)
            if np.max(np.abs(g_new - g)) < 1e-9 + 1e-6 * max(float(g_new.max()), 1e-9):
                g = g_new
                break
            g = g_new if k < 20 else 0.5 * (g + g_new)
        else:
            return False, dict(q=q, stalled=True), ("no convergence of the Coulomb fixed point "
                                                    "(numerical, counted as a release)")
        ok, q, _ = self._minimise(W, s_old, g, q)
        if not ok:
            run = self._runaway(q)
            return False, dict(q=q, stalled=not run), rel if run else stall
        return True, self._update(q, s_old, g), ""

    def _update(self, q, s_old, g):
        """Return mapping: new slip offsets; sliding / separated flags."""
        kt = self.kt
        with np.errstate(divide="ignore", invalid="ignore"):
            rr = np.where(np.isfinite(g), g / kt, np.inf)
        dn, act, Fn, tv, tm, stick = self._terms(q, s_old, rr)
        with np.errstate(divide="ignore", invalid="ignore"):
            excess = np.where(stick, 0.0, tm - np.where(np.isfinite(g), g, 0.0) / kt)
        s = s_old + np.maximum(excess, 0.0)[:, None] * tv / np.maximum(tm, 1e-300)[:, None]
        Ft = -kt[:, None] * (self.JT @ q - s)
        gf = np.where(np.isfinite(g), g, 0.0)
        slip = act & (gf > 0) & (np.linalg.norm(Ft, axis=1) >= gf * (1 - 1e-6))      # at the Coulomb limit
        return dict(q=q, s=s, g=gf, active=act, slip=slip, Fn=Fn, Ft=Ft)

    def _ramp(self, W0, W, st, fric, max_it, n_steps):
        for k in range(1, n_steps + 1):
            ok, st, why = self._increment(W0 + (W - W0) * ((k - 1) / n_steps), W0 + (W - W0) * (k / n_steps), st, fric,
                                          self.MAX_CUTS)
            if not ok:
                return False, st, why
        return True, st, ""

    def _increment(self, Wa, Wb, st, fric, cuts):
        """One load increment Wa -> Wb from the converged state st at Wa; a stalled increment is cut in halves."""
        ok, st2, why = self._level(Wb, st, fric)
        if not ok and cuts > 0 and (st2 or {}).get("stalled"):
            Wm = 0.5 * (Wa + Wb)
            ok, stm, why = self._increment(Wa, Wm, st, fric, cuts - 1)
            if not ok:
                return False, stm, why
            return self._increment(Wm, Wb, stm, fric, cuts - 1)
        if not ok:
            return False, st2 if st2 else st, why
        q = st2["q"]
        rot = math.degrees(float(np.linalg.norm(q[3:6]))); disp = float(np.linalg.norm(q[:3]))
        if rot > ROT_MAX or disp > DISP_MAX:
            return False, st2, (f"displacement beyond the small-displacement model ({disp * 1e3:.1f} mm, "
                                f"{rot:.1f} deg): gross slip / knocked off")
        return True, st2, ""

    # Donning. The cradle is put on by hand, so the state it starts from is set by the donning sequence,
    # which friction remembers. Two bounding sequences are modelled; both end with the hand letting go:
    #   "A" clamp-then-release: the hand holds the cradle in place (in-plane DOFs u_x, u_y, theta_z held)
    #       while the link preload settles it frictionlessly on the pads; the pads then grip, and the hand
    #       lets go, so the weight is shared by STIFFNESS (pads in shear + saddle roots in compression).
    #       Most weight on pad friction -> governs slip/retention; used as the base of every load case.
    #   "B" hang-then-clamp: the saddle is hung on the auricle root first (weight carried by the root
    #       normals, frictionless seating), the hand only holding the rotation theta_z; the link is closed,
    #       the pads grip, the hand lets go. Most weight on the root -> governs root pressure.
    # A frictionless settle with no hand has a zero-energy mode (spin about the link eye while the root is
    # unloaded), so the hand constraint is what makes the donned position determinate.
    DONNING = {"A": ((0, 1, 5), False), "B": ((5,), True)}

    def donned(self, W_static=None, seq="A"):
        """Returns (state, W_eq): the gripped donned state and the load at which it is in equilibrium
        without the hand (applied load + hand reaction); ramp W_eq -> W to let go."""
        fixed, with_weight = self.DONNING[seq]
        W = self._pad(W_static) if (with_weight and W_static is not None) else np.zeros(self.ndof)
        st0 = self._fresh()
        ok, q, _ = self._minimise(W, st0["s"], np.zeros(self.n), st0["q"], fixed=fixed)
        dn = -self.JN @ q
        Fn = np.where(self.bil | (dn > 0), self.k * dn, 0.0)
        hand = self.KL @ q - (W + self.WL) - self.JN.T @ Fn        # generalised gradient = hand reaction
        hand[[i for i in range(self.ndof) if i not in fixed]] = 0.0
        st = dict(q=q, s=self.JT @ q, g=self.mu * np.maximum(Fn, 0.0))
        return st, W + hand

    def set_base(self, W_base, max_it=60, seq="A"):
        """Donned state (see donned) then the hand lets go under the upright 1 g load, ramped with friction."""
        W_base = self._pad(W_base)
        st0, W_eq = self.donned(W_base, seq)
        ok, st, why = self._ramp(W_eq, W_base, st0, True, max_it, self.N_STEPS)
        self.base = (W_base, st) if ok else None
        self.base_why = why
        return ok

    def solve(self, W, fric=True, max_it=60):
        W = self._pad(W)
        if not fric:                                  # stick analysis: all tangential springs stuck from zero
            ok, st, why = self._level(W, self._fresh(), False)
        else:
            if getattr(self, "base", None) is None:
                st0, W0 = self.donned()
            else:
                W0, st0 = self.base
            ok, st, why = self._ramp(W0, W, st0, True, max_it, self.N_STEPS)
        if not ok:
            return dict(ok=False, reason=why, q=(st or {}).get("q"), numerical=bool((st or {}).get("stalled")))
        q, active, slip, Fn, Ft = st["q"], st["active"], st["slip"], st["Fn"], st["Ft"]
        Ft = np.where(active[:, None], Ft, 0.0)
        dn = -self.JN @ q
        # equilibrium residual (all six equations)
        R = W + self.WL - self.KL @ q + self.JN.T @ Fn + np.einsum("na,nai->i", Ft, self.JT)
        res = []
        for i, c in enumerate(self.C):
            Fv = Fn[i] * c["n"] + Ft[i, 0] * c["t"][0] + Ft[i, 1] * c["t"][1]
            ftn = float(np.linalg.norm(Ft[i]))
            res.append(dict(name=c["name"], Fn=float(Fn[i]), Ft=ftn, Fvec=Fv, dn=float(dn[i]),
                            mu_req=(ftn / Fn[i] if Fn[i] > 1e-9 else (np.inf if ftn > 1e-9 else 0.0)),
                            p_mean=Fn[i] / c["area"], p_peak=PEAK_FACTOR * Fn[i] / c["area"],
                            slipping=bool(slip[i]), active=bool(active[i])))
        lf = None
        if self.link is not None:
            rp, P, kz, kt = self.link
            dl = q[:3] + np.cross(q[3:6], rp)
            lf = np.array([-kt * dl[0], -kt * dl[1], -P - kz * dl[2]])
        return dict(ok=True, converged=True, q=q, contacts=res, residual=float(np.abs(R).max()),
                    slipping=bool(slip.any()), link_force=lf)


SKIN_PADS = ("T temporal", "M mastoid", "P post-sup")


def static_friction_demand(C, link, W_st, pads=SKIN_PADS):
    """Friction each skin pad needs to hold the donned state (sequence A) WITHOUT slipping: the pads are made
    non-slipping (mu = 10), root and scalp keep their design friction. Returns {pad: mu_required / mu_design}
    (> 1: the pad creeps at rest with the design coefficient and hands load to the ear root)."""
    Cs = [dict(c, mu=10.0) if c["name"] in pads else c for c in C]
    m = Model(Cs, link)
    if not m.set_base(W_st):
        return None
    r = m.solve(W_st)
    if not r["ok"]:
        return None
    mu_d = {c["name"]: c["mu"] for c in C}
    return {x["name"]: x["mu_req"] / mu_d[x["name"]] for x in r["contacts"] if x["name"] in pads}


def onset_of_slip(model, W0, W, n_bis=5):
    """Released case: the largest fraction lam of the load increment W0 -> W that is still held (bisection,
    precision 2^-n_bis) and its solution. The contact forces there bound what the head can push into the
    cradle before it lets go (afterwards the pads slide at the friction limit)."""
    lo_, hi_, r_lo = 0.0, 1.0, None
    for _ in range(n_bis):
        mid = 0.5 * (lo_ + hi_)
        r = model.solve(W0 + mid * (W - W0))
        if r["ok"]:
            lo_, r_lo = mid, r
        else:
            hi_ = mid
    if r_lo is None:
        r_lo = model.solve(W0)
    return lo_, r_lo


def solve(C, W, link=None, fric=True, max_it=80):
    return Model(C, link).solve(W, fric, max_it)


# ------------------------------------------------------------------ loads
def inertial_wrench(M, com, I, g_eff, axis=None, alpha=0.0, omega=0.0):
    """Wrench about the origin from: effective gravity g_eff (m/s^2 vector,
    = g - a_linear), head angular acceleration alpha about `axis`, and
    head angular velocity omega (centripetal)."""
    F = M * g_eff
    Mo = np.cross(com, F)
    if axis is not None:
        e, p0 = AXES[axis]
        rho = com - p0
        a_t = np.cross(alpha * e, rho)                      # tangential accel of COM
        a_c = -omega ** 2 * (rho - np.dot(rho, e) * e)      # centripetal
        Fi = -M * (a_t + a_c)
        Mo = Mo + np.cross(com, Fi) - I @ (alpha * e)      # d'Alembert: -I alpha about COM
        F = F + Fi
    return np.r_[F, Mo]


def cable_wrench(d, des, F_pull):
    """Cable force applied at the clip (strain relief) position."""
    a = math.radians(des["cable_a"])
    r = (d["bar_r1"] + des["cable_od"] / 2 + 3) * 1e-3
    p = np.array([r * math.cos(a), r * math.sin(a), (des["standoff"] - des["clip_post_L"] + 5 + des["clip_len"] / 2) * 1e-3])
    return np.r_[F_pull, np.cross(p, F_pull)], p


def static_wrench(mp, d, des):
    """Donned, head upright, 1 g, cable hanging (its own weight at the clip): the base state of every case."""
    M, com, I = mp
    w_cable = CABLE["mass_per_m"].v * CABLE["hang_len"].v * G
    return inertial_wrench(M, com, I, np.array([0, -G, 0])) + cable_wrench(d, des, np.array([0, -w_cable, 0]))[0]


def fib_sphere(n):
    i = np.arange(n) + 0.5
    phi = np.arccos(1 - 2 * i / n); th = math.pi * (1 + 5 ** 0.5) * i
    return np.c_[np.cos(th) * np.sin(phi), np.cos(phi) * -1, np.sin(th) * np.sin(phi)]   # first point ~ -y


def cone(dirs, axis, half_deg):
    return dirs[np.degrees(np.arccos(np.clip(dirs @ axis, -1, 1))) <= half_deg]


CABLE_CONE = 80.0       # [A] deg, the cable pull lies within this angle of straight down (it leaves the clip downwards)


def ring_grid(polar_deg, az_step):
    """Unit directions: straight down (-y) + rings at the polar angles polar_deg (deg from straight down) x azimuths
    every az_step deg (azimuth 0 = forward +x, 90 = lateral +z, away from the head). Deterministic; halving az_step
    keeps every direction (nested)."""
    out = [np.array([0, -1.0, 0])]
    for t in polar_deg:
        tr = math.radians(t)
        for p in np.arange(0.0, 360.0 - 1e-9, az_step):
            pr = math.radians(p)
            out.append(np.array([math.sin(tr) * math.cos(pr), -math.cos(tr), math.sin(tr) * math.sin(pr)]))
    return out


# 1 g normal carries pass/fail criteria (no gross slip, tripod kept, tilt limit), so its gravity and cable directions
# are a deterministic GRID that contains the edges of both cones: head tilt (deg from upright) at half and all of the
# 45 deg cone and the cable pull at the edge of its cone, each every az_step deg of azimuth. A sparse quasi-uniform sample
# can miss the worst corner (it did for the first Final: head tilted towards this side, this ear down, so the side hangs
# outward, while the cable pulls outward). The dense check (DENSE_1G, analysis.dense_1g_chunk) and its local refinement
# (analysis.refine_1g_chunk) check the grid's resolution; with 45 deg azimuth steps the tuned eyes failed the dense check
# at a combination between the grid azimuths, so the steps are 22.5 deg (the dense check's steps then 11.25 deg).
# The other categories are reported as released FRACTIONS, so they keep a quasi-uniform (Fibonacci) sample.
GRID_1G = dict(tilt=(22.5, 45.0), az_step=22.5, cable_polar=(CABLE_CONE,), cable_az_step=22.5)
DENSE_1G = dict(tilt=(11.25, 22.5, 33.75, 45.0), az_step=11.25, cable_polar=(20.0, 40.0, 60.0, CABLE_CONE), cable_az_step=11.25)

CATEGORIES = {
    # effective gravity = gravity (head tilt within `cone` deg of upright) + dynamic acceleration of magnitude
    # dyn (g) in ANY direction, combined as vectors; plus head angular acceleration/velocity about each axis
    # (both senses) and a cable pull in any direction within CABLE_CONE of straight down.
    "1 g normal":        dict(cone=45.0, dyn=0.0, ang="normal", cable=0.5, p_lim=TISSUE["p_sustained"].v, grid=True),
    # cable 1.0 N [A]: hanging-cable inertia at 2 g (0.15 N) + residual tug of a cable clipped to clothing;
    # sideways tugs above the tug limits (results/cable.json "tug_limits", ~1-1.5 N) release the cradle
    "2 g dynamic":       dict(cone=30.0, dyn=1.0, ang="dynamic", cable=1.0, p_lim=TISSUE["p_transient"].v),
    "3 g severe":        dict(cone=30.0, dyn=2.0, ang="severe", cable=2.0, p_lim=TISSUE["p_transient"].v),
    "5 g accidental":    dict(cone=None, dyn=5.0, ang="accidental", cable=CABLE["snag"].v, p_lim=TISSUE["p_pain"].v / 2),
}


MUST = ("T temporal", "M mastoid", "P post-sup", "S root", "S root F", "S root B")


def metrics(r, C):
    """Criteria of one solved case."""
    util = 0.0
    for c, x in zip(C, r["contacts"]):
        if x["Fn"] > 1e-9:
            util = max(util, x["Ft"] / (c["mu"] * x["Fn"]))
    fnmin = min(x["Fn"] for x in r["contacts"] if x["name"] in MUST)
    pk = max(x["p_peak"] for x in r["contacts"])
    pm = max(x["p_mean"] for x in r["contacts"])
    rot = math.degrees(np.linalg.norm(r["q"][3:6]))
    rot_xy = math.degrees(np.linalg.norm(r["q"][3:5]))      # tilt (changes driver-ear geometry); spin about z excluded
    n_skin = sum(1 for x in r["contacts"] if x["name"][0] in "TMP" or x["name"] == "S scalp" if x["Fn"] > F_MIN)
    root = any(x["Fn"] > F_MIN for x in r["contacts"] if x["name"].startswith("S root"))
    seated = n_skin >= 3          # tripod on the skin; root lift-off is reported separately
    return dict(util=util, Fn_min=fnmin, p_peak=pk, p_mean=pm, rot=rot, rot_xy=rot_xy, seated=seated,
                n_skin=n_skin, disp=float(np.linalg.norm(r["q"][:3])) * 1e3)


def load_cases(mp, d, des, cat, n_dir=60, n_cable=3, n_grav=7, grid=None):
    """Generator of (tag, wrench): gravity direction x dynamic direction x (angular axis, sign) x cable direction.
    A category with spec["grid"] (1 g normal) uses the worst-case grid `grid` (default GRID_1G; n_grav and n_cable
    are then not used); the others a quasi-uniform sample: upright + about n_grav directions of the tilt cone
    (Fibonacci points), n_dir dynamic directions, straight down + about n_cable cable directions."""
    M, com, I = mp
    spec = CATEGORIES[cat]
    down = np.array([0, -1.0, 0])
    if spec["cone"] is None:          # accidental: resultant of 5 g in any direction (gravity included)
        gset = [np.zeros(3)]
        dyn_dirs = fib_sphere(n_dir)
    elif spec.get("grid"):
        g_ = grid or GRID_1G
        assert max(g_["tilt"]) <= spec["cone"] + 1e-9
        gset = ring_grid(g_["tilt"], g_["az_step"])
        dyn_dirs = fib_sphere(n_dir) if spec["dyn"] > 0 else [np.zeros(3)]
    else:
        gd = cone(fib_sphere(max(n_grav * 400 // max(int(spec["cone"]), 1), 12)), down, spec["cone"])
        gset = [down] + list(gd[:: max(1, len(gd) // n_grav)])
        dyn_dirs = fib_sphere(n_dir) if spec["dyn"] > 0 else [np.zeros(3)]
    if spec.get("grid"):
        g_ = grid or GRID_1G
        cdirs = ring_grid(g_["cable_polar"], g_["cable_az_step"])
    else:
        cd_all = cone(fib_sphere(60), down, CABLE_CONE)
        cdirs = [down] + list(cd_all[:: max(1, len(cd_all) // n_cable)])
    # Head rotation: for oscillatory head motion theta = Th sin(W t) the angular acceleration peaks when the
    # angular velocity is zero and vice versa (quadrature), so the peaks are NOT combined. With x = cos^2(phase)
    # the squared inertial load alpha^2 rho^2 (1 - x) + omega^4 rho^2 x^2 is convex in x, so the two
    # end phases (alpha peak, omega = 0) and (omega peak, alpha = 0) bound every intermediate phase.
    for gdir in gset:
        for ddir in dyn_dirs:
            for ax, s, w in ANG_CASES:
                for cd in cdirs:
                    yield case_wrench(mp, d, des, cat, gdir, ddir, ax, s, w, cd)


# head-rotation cases of every category: none, +-alpha about each axis, omega about each axis (quadrature, see above)
ANG_CASES = [(None, 0.0, 0.0)] + [(ax, s, 0.0) for ax in AXES for s in (+1, -1)] + [(ax, 0.0, 1.0) for ax in AXES]


def case_wrench(mp, d, des, cat, gdir, ddir, ax, s, w, cd):
    """(tag, wrench) of one load case of category cat: gravity direction gdir, dynamic direction ddir, head rotation
    (axis ax, sign s of alpha, w = 1 for the omega phase) and cable pull direction cd (see load_cases)."""
    M, com, I = mp
    spec = CATEGORIES[cat]
    down = np.array([0, -1.0, 0])
    w_cable = CABLE["mass_per_m"].v * CABLE["hang_len"].v * G
    g_eff = G * (gdir + spec["dyn"] * np.asarray(ddir))
    gn = np.linalg.norm(g_eff)
    Wc_self, _ = cable_wrench(d, des, w_cable * (g_eff / gn if gn > 0 else down))
    W = inertial_wrench(M, com, I, g_eff, ax, s * ALPHA[spec["ang"]], w * OMEGA[spec["ang"]]) if ax \
        else inertial_wrench(M, com, I, g_eff)
    Wp, _ = cable_wrench(d, des, spec["cable"] * cd)
    return dict(g_dir=gdir, dyn_dir=np.asarray(ddir), g_eff=g_eff, axis=ax, sign=s,
                phase=("omega" if w else "alpha") if ax else None, cable_dir=cd), W + Wc_self + Wp


def sweep(mp, d, des, C, link, cat, n_dir=60, n_cable=3, fric=True, keep=False, n_grav=7):
    """Worst-case search. Stick analysis (fric=False) gives the friction
    utilisation Ft/(mu Fn) needed for no slip; fric=True lets contacts slide."""
    worst = {k: (-np.inf, None, None) for k in ("util", "p_peak", "p_mean", "rot", "rot_xy", "disp")}
    worst["Fn_min"] = (np.inf, None, None)
    n = 0; released = 0; unseated = 0; rows = []
    model = Model(C, link)
    model.set_base(static_wrench(mp, d, des))
    for tag, W in load_cases(mp, d, des, cat, n_dir, n_cable, n_grav):
        n += 1
        r = model.solve(W, fric=fric)
        if not r["ok"]:
            released += 1
            if keep:
                rows.append((tag, None))
            continue
        m = metrics(r, C)
        if not m["seated"]:
            unseated += 1
        for k in ("util", "p_peak", "p_mean", "rot", "rot_xy", "disp"):
            if m[k] > worst[k][0]:
                worst[k] = (m[k], tag, r)
        if m["Fn_min"] < worst["Fn_min"][0]:
            worst["Fn_min"] = (m["Fn_min"], tag, r)
        if keep:
            rows.append((tag, m))
    worst["n_cases"] = n; worst["released"] = released; worst["unseated"] = unseated
    return worst, rows


def shakedown(model, W_st, cases, seq="A", n_cyc=15, tol=0.005, pads=SKIN_PADS):
    """Frictional shakedown under repeated head motion: the sustained state in use.

    From the donned state (sequence `seq`, Model.donned / set_base) every load of `cases` is applied from the
    current state and removed again (Model._ramp both ways, friction on, slip offsets carried from case to case),
    cycle after cycle. A pad that reaches its friction limit during a case keeps its slip offset when the load
    is removed, so repeated head motion ratchets load from pad friction into the saddle's root normals until the
    contact forces repeat from cycle to cycle (pads may go on slipping back and forth). Converged when no contact
    normal force changes by more than tol x |W_st| over a whole cycle (at most n_cyc cycles). A case that releases the cradle leaves the state as it was (counted in n_rel).
    n_slip[k] = applications in cycle k at whose peak a skin pad (pads) is sliding.
    Returns dict(ok, cycles, converged, n_rel, n_slip, hist=[{contact: Fn} after each cycle], state=final state)."""
    W_st = model._pad(W_st)
    if not model.set_base(W_st, seq=seq):
        return dict(ok=False, why=model.base_why)
    st = model.base[1]
    names = [c["name"] for c in model.C]
    Wn = float(np.linalg.norm(W_st[:3]))
    hist = [dict(zip(names, map(float, st["Fn"])))]
    pmask = np.array([n in pads for n in names])
    n_rel = 0; conv = False; n_slip = []
    for cyc in range(n_cyc):
        Fn0 = np.array(st["Fn"], dtype=float)
        n_slip.append(0)
        for W in cases:
            W = model._pad(W)
            ok1, st1, _ = model._ramp(W_st, W, st, True, 60, model.N_STEPS)
            if not ok1:
                n_rel += 1
                continue
            n_slip[-1] += bool(np.any(np.asarray(st1["slip"]) & pmask))
            ok2, st2, _ = model._ramp(W, W_st, st1, True, 60, model.N_STEPS)
            if not ok2:
                n_rel += 1
                continue
            st = st2
        hist.append(dict(zip(names, map(float, st["Fn"]))))
        if float(np.max(np.abs(np.asarray(st["Fn"]) - Fn0))) < tol * Wn:
            conv = True
            break
    return dict(ok=True, cycles=len(hist) - 1, converged=conv, n_rel=n_rel, n_slip=n_slip, hist=hist, state=st)


def static_upright(mp, d, des, C, link):
    M, com, I = mp
    W = inertial_wrench(M, com, I, np.array([0, -G, 0]))
    Wc, _ = cable_wrench(d, des, CABLE["mass_per_m"].v * CABLE["hang_len"].v * G * np.array([0, -1.0, 0]))
    return solve(C, W + Wc, link, fric=False)
