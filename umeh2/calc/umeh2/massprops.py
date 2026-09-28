"""
Mass properties computed DIRECTLY FROM THE CAD GEOMETRY.

Each part is exported by OpenSCAD in its assembled position (skin frame),
then volume, surface area, centroid and the full inertia tensor are
integrated exactly over the triangle mesh (divergence theorem / signed
tetrahedra). Printed-part mass uses a shell + infill model computed from
the part's own surface area:

    f = min(1, A_surf * t_shell / V) + (1 - min(...)) * infill      [calculated]
    m = rho * f * V

Assumption (stated): the infill/shell split is spread uniformly over the
part for the centroid and inertia (the shell lies on the outside, so the
true inertia is slightly larger; error < 5 % for these thin parts).
"""
import os, subprocess, concurrent.futures as cf
import numpy as np
from .materials import PETG, TPU, WIRE, SCREW, ACOUSTIC_MAT, FOAM, SILICONE, SILICONE_GEL, BRASS
from . import design as dz

CAD = dz.CAD
TMP = os.path.join(os.path.dirname(dz.CAD), "stl", "_placed")

# material, perimeters, top/bottom layers, infill  (from the print-orientation study, report §20)
PRINT = {
    "ring":          ("PETG", 5, 5, 0.30),
    "gasket_umi":    ("TPU", 2, 99, 1.00),
    "arm_saddle":    ("PETG", 5, 5, 0.40),
    "arm_temporal":  ("PETG", 5, 5, 0.40),
    "arm_mastoid":   ("PETG", 5, 5, 0.40),
    "arm_post":      ("PETG", 5, 5, 0.40),
    "pad_post":      ("TPU", 2, 3, 0.15),
    "saddle_cap":    ("TPU", 3, 4, 0.15),
    "pad_temporal":  ("TPU", 2, 3, 0.15),
    "pad_mastoid":   ("TPU", 2, 3, 0.15),
    "baffle":        ("PETG", 4, 5, 0.30),
    "gasket_driver": ("TPU", 2, 99, 1.00),
    "cup":           ("PETG", 4, 5, 0.20),
    "cable_anchor":  ("PETG", 4, 5, 0.40),
    "cable_clip":    ("TPU", 3, 99, 1.00),
    "pad_face_temporal": ("SILICONE", 0, 0, 1.00),    # cast, solid
    "pad_face_mastoid":  ("SILICONE", 0, 0, 1.00),
    "saddle_liner":      ("SILICONE_GEL", 0, 0, 1.00),   # cast into the saddle cap, solid
}
LINE_W = 0.42e-3
LAYER = 0.2e-3


def read_stl(path):
    with open(path, "rb") as fh:
        head = fh.read(5)
    if head == b"solid":
        pts = []
        with open(path) as fh:
            for line in fh:
                line = line.strip()
                if line.startswith("vertex"):
                    pts.append([float(x) for x in line.split()[1:4]])
        P = np.array(pts, dtype=float).reshape(-1, 3, 3)
    else:
        data = np.fromfile(path, dtype=np.uint8)
        n = int(np.frombuffer(data[80:84].tobytes(), dtype=np.uint32)[0])
        rec = np.frombuffer(data[84:84 + 50 * n].tobytes(), dtype=np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")]))
        P = rec["v"].astype(float)
    return P * 1e-3          # mm -> m


def mesh_props(P):
    a, b, c = P[:, 0], P[:, 1], P[:, 2]
    det = np.einsum("ij,ij->i", a, np.cross(b, c))            # 6 x signed tet volume
    V = det.sum() / 6.0
    cen = (det[:, None] * (a + b + c)).sum(0) / 24.0 / V
    Ccan = np.array([[2, 1, 1], [1, 2, 1], [1, 1, 2]]) / 120.0
    A = np.stack([a, b, c], axis=2)                           # columns = vertices
    C = np.einsum("n,nij,jk,nlk->il", det, A, Ccan, A)        # ∫ x x^T dV about origin
    area = 0.5 * np.linalg.norm(np.cross(b - a, c - a), axis=1).sum()
    if V < 0:
        V, C = -V, -C
    return V, area, cen, C


def export(part, out, extra=()):
    cmd = ["openscad", "-o", out, "-D", f'part="placed_{part}"', *extra, os.path.join(CAD, "umeh2.scad")]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(out):
        raise RuntimeError(f"OpenSCAD failed for {part}: {r.stderr[-400:]}")
    return out


def part_mass(name, V, area, mat_override=None):
    mat, per, tb, infill = PRINT[name]
    if mat_override:
        mat = mat_override
    if mat == "FOAM":                      # die-cut foam, not printed: solid density
        return FOAM["rho"].v * V, 1.0, mat
    if mat == "SILICONE":                  # cast, solid
        return SILICONE["rho"].v * V, 1.0, mat
    if mat == "SILICONE_GEL":
        return SILICONE_GEL["rho"].v * V, 1.0, mat
    rho = PETG["rho"].v if mat == "PETG" else TPU["rho"].v
    t_shell = per * LINE_W
    shell = min(1.0, area * t_shell / V) if V > 0 else 1.0
    f = shell + (1 - shell) * infill
    return rho * f * V, f, mat


def assembly_props(tag, driver_mass_g, parts=None, jobs=4, has_post=False, mat_override=None, has_face=False,
                   has_liner=False):
    """Exports every part placed, integrates, returns per-part table and totals."""
    os.makedirs(TMP, exist_ok=True)
    parts = parts or [p for p in list(PRINT) + ["driver"] if (p not in ("arm_post", "pad_post") or has_post)
                      and (not p.startswith("pad_face") or has_face) and (p != "saddle_liner" or has_liner)]
    outs = {p: os.path.join(TMP, f"{tag}_{p}.stl") for p in parts}
    with cf.ThreadPoolExecutor(jobs) as ex:
        list(ex.map(lambda p: export(p, outs[p]), parts))
    rows = []
    for p in parts:
        V, area, cen, C = mesh_props(read_stl(outs[p]))
        if p == "driver":
            m = driver_mass_g * 1e-3; f = m / V; mat = "driver [A]"   # mass-equivalent solid
            scale = m / V
        else:
            m, f, mat = part_mass(p, V, area, (mat_override or {}).get(p))
            scale = m / V
        # inertia about the part COM
        Cm = C * scale
        Io = np.trace(Cm) * np.eye(3) - Cm
        Ic = Io - m * (np.dot(cen, cen) * np.eye(3) - np.outer(cen, cen))
        rows.append(dict(part=p, mat=mat, V=V, area=area, f=f, m=m, c=cen, I=Ic, src="CAD"))
    return rows


LINK_SHARE = 0.35    # [A] share of the half link (wire + sleeve) carried by one cradle's supports; the rest rests on the occiput/hair


def hardware(d, des):
    """Point masses of non-printed parts at their CAD positions [DS / A]."""
    rows = []
    sd = des["standoff"] * 1e-3
    def add(name, m_g, pos_mm, src):
        rows.append(dict(part=name, mat="hardware", m=m_g * 1e-3, c=np.array(pos_mm) * 1e-3, I=np.zeros((3, 3)), src=src, V=0, area=0, f=1))
    def pol(r, a, z):
        a = np.radians(a); return [r * np.cos(a), r * np.sin(a), z]
    screw_mass = {"M2": 0.35, "M2.5": 0.55, "M3": 0.95, "M4": 1.9}          # socket/csk ~8–12 mm, A2 [DS]
    insert_mass = {"M2": 0.12, "M2.5": 0.20, "M3": 0.33, "M4": 0.60}         # knurled brass [DS]
    nut_mass = {"M2": 0.10, "M2.5": 0.17, "M3": 0.28, "M4": 0.55}
    z_tab = des["standoff"] + d["tab_t"] / 2
    for a in [t[0] for t in d["tabs"]]:
        anchor = a == des["cable_a"]
        size = (des.get("anchor_screw") or des["arm_screw"]) if anchor else des["arm_screw"]
        pitch = d["anchor_ins_pitch"] if anchor else d["tab_ins_pitch"]
        for r in [d["tab_r"] - pitch, d["tab_r"]]:
            add(f"{size} screw+insert @{a:.0f}°", screw_mass[size] + insert_mass[size], pol(r, a, z_tab), "DS")
            if des.get("arm_washer"):
                # steel wave washer OD = head_d + 0.5, ID = d + 0.2, 0.3 mm thick, steel density (WIRE rho) [C]
                sw = SCREW[size]
                add(f"{size} wave washer @{a:.0f}°",
                    WIRE["rho"].v * 1e-6 * np.pi / 4 * ((sw["head_d"] + 0.5) ** 2 - (sw["d"] + 0.2) ** 2) * 0.3,
                    pol(r, a, des["standoff"] + d["tab_t"]), "C")
    # clip screw + nut through the clip post (cable_anchor(): x = bar_r1 - clip_post_t, z = -clip_post_L + 5)
    ka = des.get("anchor_screw") or des["arm_screw"]
    add(f"clip {ka} screw+nut", screw_mass[ka] + nut_mass[ka],
        pol(d["bar_r1"] - des["clip_post_t"] / 2, des["cable_a"], des["standoff"] - des["clip_post_L"] + 5), "DS")
    pads = [(des["temporal_a"], des["temporal_r"]), (des["mastoid_a"], des["mastoid_r"])]
    if des.get("post_a") is not None:
        pads.append((des["post_a"], des["post_r"]))
    for a, r in pads:
        add(f"pad {des['pad_screw']} screw+nut @{a:.0f}°", screw_mass[des["pad_screw"]] + nut_mass[des["pad_screw"]], pol(r, a, des["pad_h"] + des["foot_t"]), "DS")
    add("saddle-cap pin M2 + nut", 0.45, pol(des["saddle_r"], des["saddle_a"], des["foot_t"] / 2 + 1), "DS")
    zc = des["standoff"] + d["floor_t"] + 1 + d["baffle_h"] + d["cup_h"] / 2
    for a in d["cup_screw_a"]:
        add(f"cup {des['cup_screw']} screw+insert", screw_mass[des["cup_screw"]] * (d["cup_h"] / 10) + insert_mass[des["cup_screw"]], pol(d["cup_screw_r"], a, zc), "DS")
    # felt disc (hole over the eye boss); the PSA rim (< 0.02 g) is neglected
    felt_m = d["felt_A"] * 1e-6 * des["felt_t"] * 1e-3 * ACOUSTIC_MAT["felt_density"].v * 1e3
    add("felt disc", felt_m, [0, 0, d["z_cuptop"] - des["cup_end_t"] - des["felt_t"] / 2], "C")
    add("2-pin socket + wires + JST", 2.0, pol(d["tab_r"] - 4, des["cable_a"], des["standoff"] - 5), "A")
    # half of the occipital link (each cradle carries its own half): the wire on its designed path (the same
    # link_design as the spring rate and stresses, support.make_link) with half the apex coil, and its comfort sleeve
    from .linkspring import link_design, link_sleeve_mass, eye_ri, DC_COIL
    from .support import link_path
    Ld = link_design(des["wire_d"], des["link_preload"], des.get("link_coils", 0), path=link_path(d, des))
    m_wire = Ld["mass_g"] / 2
    m_sleeve = link_sleeve_mass(des["wire_d"], Ld["L"]) / 2
    # eye hardware: M2.5 screw + heat-set insert + M2.5 washer + bend-radius sleeve. The sleeve keeps the
    # eye inner radius >= 1.5 d (linkspring.eye_ri): OD = 2 r_i, ID and length from design.EYE_SLEEVE_*, brass [C]
    r_i = eye_ri(des["wire_d"]) * 1e3
    m_sleeve_eye = BRASS["rho"].v * 1e-6 * np.pi / 4 * ((2 * r_i) ** 2 - dz.EYE_SLEEVE_ID ** 2) * dz.EYE_SLEEVE_L
    m_eye = screw_mass["M2.5"] + insert_mass["M2.5"] + 0.10 + m_sleeve_eye
    mode = des.get("link_mode", "mastoid")
    if mode == "ring":
        p = pol(d["link_r"], des["link_a"], des["standoff"])
        add("link eye M2.5 screw + insert + washer + sleeve", m_eye, p, "DS")
    elif mode == "cup":
        # eye boss on the cup end (cup(): EYE_X, link_y), screw head and sleeve just above the outer face
        from .support import EYE_Z_CUP
        p = [des["link_x"], des["link_y"], d["z_cuptop"] + EYE_Z_CUP]
        add("link eye M2.5 screw + insert + washer + sleeve", m_eye, p, "DS")
    else:
        p = pol(des["mastoid_r"], des["mastoid_a"], des["pad_h"] + des["foot_t"])
    # the link is a free spring between both cradles; only the end region near the eye is carried by this
    # cradle's supports (LINK_SHARE of the half link [A], the rest rests on the occiput/hair)
    add("occipital link, share carried by the cradle", LINK_SHARE * (m_wire + m_sleeve), [p[0] - 25, p[1] - 10, p[2] - 15], "C")
    return rows


def combine(rows):
    M = sum(r["m"] for r in rows)
    c = sum(r["m"] * r["c"] for r in rows) / M
    I = np.zeros((3, 3))
    for r in rows:
        dvec = r["c"] - c
        I += r["I"] + r["m"] * (np.dot(dvec, dvec) * np.eye(3) - np.outer(dvec, dvec))
    return M, c, I
