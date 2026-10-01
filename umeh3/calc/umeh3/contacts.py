"""
UMEH-3 ear attachment as a statically indeterminate body on compliant frictional contacts, solved with the UMEH-2
contact solver (umeh2.support.Model: unilateral normal springs, Coulomb friction solved incrementally, flexible
nodes, a preloaded bilateral spring). Frame and units as umeh2.support (skin frame, m, N).

Contacts (right side)
  Pad 00..15   the round velour pad on the skin: 16 normal springs (+z) on the circle of the annulus' radius of
               gyration, each carrying 1/16 of the loaded annulus; foam (slow-rebound PU [A]) in series with the
               soft tissue; velour on skin, or on hair for the upper sectors
  H root F/B   the silicone sleeve of the hook arch on the superior auricle root: two bearing zones at 90 +- phi
               on the root arch (normals radial, in the head plane) -> weight carried by normals, the cradle
               located fore-aft by shape (eyeglass-temple principle, as UMEH-2's arched saddle)
  H helix      the medial face of the upper helix over the arch (-z): the pinna overhangs the hook there
  H sulcus     the rear leg on the mastoid skin in the retro-auricular sulcus (+z), if it is pressed there
  pinna clamp  the rear leg pre-bent against the cranial face of the pinna: a preloaded spring pulling the
               module towards the head (-z) = the solver's "link" (P, k_z, k_t); a case in which its force
               would turn into tension (the leg leaves the pinna) is a loss of the clamp
The hook wire is flexible: its 6x6 compliance from the plate exit to the arch apex (unit-load method, bending
and torsion of the round wire) is a 6-DOF node carrying the root, helix and sulcus contacts.
"""
import math
import numpy as np
from umeh2 import support as sp
from umeh2 import structure as st
from umeh2.materials import TISSUE, SILICONE, WIRE, FRICTION, Val
from . import geom

FRICTION.update({
    "velour/dry skin": ((0.35, 0.50, 0.70), "A"),     # [A] cotton/poly velour on dry skin (fabric-skin 0.3-0.8)
    "velour/hair": ((0.20, 0.30, 0.40), "A"),         # [A] velour over the hair above the ear
    "silicone/dry skin": FRICTION["silicone/dry skin"],
})
N_PAD = 16
HAIR_SECTOR = (35.0, 145.0)    # [A] deg, pad sectors over hair (above the ear)
K_PINNA = Val(400.0, "A", "N/m, cranial face of the pinna pushed outward by the rear leg (UMEH-2 K_HELIX range 150-1000)")
K_HELIX = Val(400.0, "A", "N/m, upper helix pushed outward by the hook arch (UMEH-2 K_HELIX)")
LEG_W = 3.5      # [A] mm loaded width of the 5 mm leg sleeve on skin
LEG_L = 20.0     # [A] mm loaded length of the leg on the pinna's cranial face
SULC_L = 15.0    # [A] mm loaded length of the leg on the mastoid skin
K_LINK_T = 40.0  # [A] N/m tangential stiffness of the clamp (the pinna moves with the leg)
DEF = dict(P=0.30, mu_level=1, mu_root=None, root_w=None, root_zone_L=None, k_pinna=K_PINNA.v,
           k_helix=K_HELIX.v, helix=True, arch=True, E_foam=None, leg_od=None, arch_od=None, wire_d=None,
           mu_scale=1.0, lobe=True, paddle=None, neck=None, k_root_scale=1.0)   # k_root_scale: softer root bearing (compliant saddle); neck: band preload N (None = no band)   # paddle: (w, L) mm of a wide rear paddle on the leg
E_LOBE = Val(60e3, "A", "Pa, soft tissue of the lobule attachment (no cartilage), 30-100 kPa")
T_LOBE = Val(5e-3, "A", "m, tissue depth at the lobule attachment")
LOBE_L = 10.0    # [A] mm loaded length of the tip under the lobule


def mm(p):
    return np.asarray(p, float) * 1e-3


def wire_compliance(P, i0, i1, d_mm):
    """6x6 flexibility at point P[i1] of the wire polyline built in at P[i0] (m, unit-load method: bending about
    both axes and torsion of a round wire, axial and shear neglected)."""
    E = WIRE["E"].v; G = E / (2 * (1 + WIRE["nu"].v))
    d = d_mm * 1e-3
    I = math.pi * d ** 4 / 64; J = 2 * I
    tip = P[i1]
    C = np.zeros((6, 6))
    lo, hi = (i0, i1) if i0 < i1 else (i1, i0)
    for k in range(lo, hi):
        a, b = P[k], P[k + 1]
        L = np.linalg.norm(b - a)
        if L < 1e-9:
            continue
        ax = (b - a) / L
        n = 8
        for j in range(n):
            p = a + (b - a) * (j + 0.5) / n
            Sk = st._skew(tip - p)
            B = np.zeros((3, 6))           # section moment from the tip wrench
            B[:, :3] = Sk; B[:, 3:] = np.eye(3)
            # torsion about ax with GJ, bending about the two normal axes with EI
            Dm = np.outer(ax, ax) / (G * J) + (np.eye(3) - np.outer(ax, ax)) / (E * I)
            C += B.T @ Dm @ B * L / n
    return 0.5 * (C + C.T)


def hook_points():
    P, lab = geom.hook_path()
    P = mm(P)
    i_plate = lab.index("groove") if "groove" in lab else lab.index("plate")    # wire built in where it leaves the shell
    arch = [i for i, l in enumerate(lab) if l == "arch"]
    # apex = arch point nearest to 90 deg
    ang = [math.degrees(math.atan2(P[i][1] - geom.ARCH_C[1] * 1e-3, P[i][0] - geom.ARCH_C[0] * 1e-3)) for i in arch]
    i_apex = arch[int(np.argmin([abs(a - 90.0) for a in ang]))]
    return P, lab, i_plate, i_apex


def nearest(P, p):
    return int(np.argmin(np.linalg.norm(P - p, axis=1)))


def contact_set(v=None):
    """Contacts + clamp spring for the design variables v (DEF overridden). Returns (C, link, info)."""
    v = dict(DEF, **(v or {}))
    for k, g in (("root_w", geom.ROOT_W), ("root_zone_L", geom.ROOT_ZONE_L), ("E_foam", geom.PAD["E_foam"]),
                 ("leg_od", geom.SIL_LEG[1]), ("arch_od", geom.SIL_ARCH[1]), ("wire_d", geom.WIRE_D),
                 ("paddle", tuple(geom.PADDLE[:2]) if geom.PADDLE else False)):
        if v[k] is None:
            v[k] = g
    C = []

    def add(name, r, n, k, area, mu_key, node=None, mu=None):
        n = np.asarray(n, float); n /= np.linalg.norm(n)
        t1 = np.cross(n, [0, 0, 1.0]) if abs(n[2]) < 0.9 else np.cross(n, [1.0, 0, 0])
        t1 /= np.linalg.norm(t1); t2 = np.cross(n, t1)
        mu_v = mu if mu is not None else FRICTION[mu_key][0][v["mu_level"]]
        c = dict(name=name, r=np.asarray(r, float), n=n, t=[t1, t2], k=k, kt=sp.KT_RATIO * k, area=area,
                 mu=v["mu_scale"] * mu_v, mu_key=mu_key, bilateral=False)
        if node is not None:
            c["node"] = node
        C.append(c)

    # ---- pad ring
    R1, R2 = geom.PAD["id"] / 2, geom.PAD["od"] / 2
    r_g = math.sqrt((R1 ** 2 + R2 ** 2) / 2)
    A_seg = math.pi * (R2 ** 2 - R1 ** 2) * geom.PAD["contact_frac"] / N_PAD * 1e-6
    t_pad = (geom.PAD["t"] - geom.PAD["comp"]) * 1e-3
    k_seg = 1 / (t_pad / (v["E_foam"] * A_seg) + TISSUE["t_temporal"].v / (TISSUE["E_temporal"].v * A_seg))
    for i in range(N_PAD):
        a = 360.0 * (i + 0.5) / N_PAD
        hair = HAIR_SECTOR[0] <= a <= HAIR_SECTOR[1]
        add(f"Pad {i:02d}", mm(geom.pol(r_g, a, 0.0)), [0, 0, 1], k_seg, A_seg, "velour/hair" if hair else "velour/dry skin")

    # ---- hook node (flexible wire from the plate exit to the arch apex)
    P, lab, i_plate, i_apex = hook_points()
    Cw = wire_compliance(P, i_plate, i_apex, v["wire_d"])
    node = dict(id="hook", m=6, r=P[i_apex], K=np.linalg.inv(Cw))
    node["K"] = 0.5 * (node["K"] + node["K"].T)
    phi = math.radians(geom.ROOT_PHI)
    t_sl = (v["arch_od"] - geom.SIL_ARCH[0]) / 2 * 1e-3
    A_r = v["root_w"] * v["root_zone_L"] * 0.7 * 1e-6
    sad = geom.SADDLE
    if sad:
        # soft saddle: slow-rebound foam strip (the compliant layer) on a TPU carrier, velour sock on the skin
        k_r = 1 / (sad["t_foam"] * 1e-3 / (sad["E_foam"] * A_r) + TISSUE["t_root"].v / (TISSUE["E_root"].v * A_r))
        r_c = geom.ARCH_R - 2.0 - sad["carrier_t"] - sad["t_foam"]        # bearing radius (root surface)
        root_key = "velour/dry skin"
    else:
        k_r = 1 / (t_sl / (SILICONE["E"].v * A_r) + TISSUE["t_root"].v / (TISSUE["E_root"].v * A_r))
        r_c = geom.ARCH_R - v["arch_od"] / 2
        root_key = "silicone/dry skin"
    mu_root = v["mu_root"]
    zones = ((+1, "H root F"), (-1, "H root B")) if v["arch"] else ((0, "H root"),)
    for sgn, nm in zones:
        th = math.pi / 2 - sgn * phi
        u = np.array([math.cos(th), math.sin(th), 0.0])
        pt = np.array([geom.ARCH_C[0], geom.ARCH_C[1], geom.Z_ROOT]) * 1e-3 + r_c * 1e-3 * u
        k_z, A_z = (k_r, A_r) if v["arch"] else (2 * k_r, 2 * A_r)
        k_z *= v["k_root_scale"]
        add(nm, pt, u, k_z, A_z, root_key, node, mu_root)
    if v["helix"]:
        z_h = geom.Z_ROOT + (sad["w"] / 2 if sad else v["arch_od"] / 2)
        pt = np.array([geom.ARCH_C[0], geom.ARCH_C[1] + r_c + 3.0, z_h]) * 1e-3
        add("H helix", pt, [0, 0, -1], v["k_helix"], 120e-6, root_key, node, mu_root)   # saddle: its velour side
    # sulcus: leg on the mastoid skin; the leg's own compliance (apex -> point) in series
    ps = mm(geom.SULCUS_PT)
    i_s = nearest(P, ps)
    C_leg = wire_compliance(P, i_apex, i_s, v["wire_d"])
    A_s = 0.7 * v["leg_od"] * SULC_L * 0.7 * 1e-6 if not v["paddle"] else v["paddle"][0] * v["paddle"][1] * 0.5 * 0.7 * 1e-6
    t_leg = (v["leg_od"] - geom.SIL_LEG[0]) / 2 * 1e-3
    k_s = 1 / (C_leg[2, 2] + t_leg / (SILICONE["E"].v * A_s) + TISSUE["t_mastoid"].v / (TISSUE["E_mastoid"].v * A_s))
    add("H sulcus", ps, [0, 0, 1], k_s, A_s, "silicone/dry skin", node, mu_root)

    if geom.LOBE_PT is not None and v["lobe"]:
        # tip curled forward under the lobule attachment: holds the hook down when the module bounces up
        pl = mm(geom.LOBE_PT)
        C_tip = wire_compliance(P, i_apex, nearest(P, pl), v["wire_d"])
        A_l = 0.7 * v["leg_od"] * LOBE_L * 0.7 * 1e-6
        k_l = 1 / (C_tip[1, 1] + t_leg / (SILICONE["E"].v * A_l) + T_LOBE.v / (E_LOBE.v * A_l))
        add("H lobe", pl, [0, -1, 0], k_l, A_l, "silicone/dry skin", node, mu_root)

    # ---- pinna clamp (rear leg pre-bent onto the cranial face of the pinna)
    pp = mm(geom.PINNA_PT)
    i_p = nearest(P, pp)
    C_pl = wire_compliance(P, i_plate, i_p, v["wire_d"])      # whole wire plate -> leg point, z
    A_p = (0.7 * v["leg_od"] * LEG_L if not v["paddle"] else v["paddle"][0] * v["paddle"][1]) * 0.7 * 1e-6
    kz = 1 / (C_pl[2, 2] + 1 / v["k_pinna"] + t_leg / (SILICONE["E"].v * A_p))
    link = (pp, v["P"], kz, K_LINK_T)
    neck = None
    if v["neck"]:
        from . import neckband as nb
        e = nb.eye_point()
        dz = nb.design(v["neck"], e)
        if dz is None:
            raise ValueError(f"no stock wire carries a {v['neck']} N neckband")
        neck = dz
        link = [link, (mm(e), v["neck"], dz["k_side"], nb.K_T)]
    info = dict(r_g=r_g, A_seg=A_seg, k_seg=k_seg, k_root=k_r, A_root=A_r, A_pinna=A_p, A_sulcus=A_s, k_sulcus=k_s,
                k_clamp=kz, neck=neck, wire_k_apex=np.linalg.inv(Cw[:3, :3]), P=v["P"], v=v)
    return C, link, info


PADS = tuple(f"Pad {i:02d}" for i in range(N_PAD))


def metrics(r, C, info):
    """Criteria of one solved case."""
    ct = {x["name"]: x for x in r["contacts"]}
    pads = [ct[n] for n in PADS]
    n_pad = sum(1 for x in pads if x["Fn"] > 1e-4)
    root = [x for n, x in ct.items() if n.startswith("H root")]
    lf = r["link_force"]
    clamp = -lf[2]                      # > 0: the leg still presses on the pinna
    util = 0.0
    for c, x in zip(C, r["contacts"]):
        if x["Fn"] > 1e-9:
            util = max(util, x["Ft"] / (c["mu"] * x["Fn"]))
    return dict(
        n_pad=n_pad, pad_p=max(x["p_mean"] for x in pads), pad_F=sum(x["Fn"] for x in pads),
        root_p=max((x["p_mean"] for x in root), default=0.0), root_F=sum(x["Fn"] for x in root),
        helix_p=ct["H helix"]["p_mean"] if "H helix" in ct else 0.0,
        sulcus_p=ct["H sulcus"]["p_mean"], lobe_p=ct["H lobe"]["p_mean"] if "H lobe" in ct else 0.0, clamp=clamp, pinna_p=max(clamp, 0.0) / info["A_pinna"],
        rot=math.degrees(float(np.linalg.norm(r["q"][3:6]))), disp=float(np.linalg.norm(r["q"][:3])) * 1e3,
        util=util, pad_slip=any(x["slipping"] for x in pads),
        root_slip=any(x["slipping"] for x in root))
