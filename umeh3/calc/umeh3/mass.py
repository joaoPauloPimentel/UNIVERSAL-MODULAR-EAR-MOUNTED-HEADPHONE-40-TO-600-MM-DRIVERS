"""
Mass properties of one UMEH-3 side from the CAD (same method as umeh2.massprops: every part exported in its
assembled position, volume / centroid / inertia integrated over the mesh, printed parts as shell + infill).
Purchased parts: their mesh gives the position and shape, the mass is the listed value [DS/A] (pad, socket) or
material density x the real cross-section (wire, PTFE liner, silicone sleeves).
"""
import os, subprocess, concurrent.futures as cf
import numpy as np
from umeh2.massprops import read_stl, mesh_props, LINE_W, LAYER   # noqa: F401
from umeh2.materials import PETG, TPU, WIRE, SILICONE, ACOUSTIC_MAT, Val
from umeh2.design import DRIVERS
from . import CAD, ROOT, geom

TMP = os.path.join(ROOT, "stl", "_placed")
# material, perimeters, top/bottom layers, infill
PRINT = {
    "shell":      ("PETG", 3, 4, 0.20),
    "front_ring": ("PETG", 3, 4, 0.30),
    "adapter":    ("TPU", 2, 99, 1.00),
    "bushing":    ("TPU", 2, 99, 1.00),
    "stop_cap":   ("PETG", 3, 4, 0.30),
    "paddle":     ("TPU", 2, 3, 0.15),     # soft gyroid core
    "saddle_carrier": ("TPU", 2, 3, 0.30),
}
PTFE_RHO = Val(2200.0, "STD", "PTFE density")
FOAM_RETIC = Val(30.0, "DS", "kg/m3 reticulated PU foam (front foam), 25-35")
SOCKET_M = Val(0.6, "DS", "g, 0.78 mm 2-pin female socket")
PLUG_M = Val(1.5, "A", "g, cable plug seated in the socket (rides on the module)")
LEADS_M = Val(0.6, "A", "g, internal leads + JST-SH pair (driver <-> socket)")
PARTS = ["shell", "front_ring", "adapter", "driver", "bushing", "wire", "sleeve_arch", "sleeve_leg", "pad",
         "front_foam", "socket", "fibre", "paddle", "saddle_carrier", "saddle_foam", "neckband", "neck_eye"]


def export(part, out, D):
    cmd = ["openscad", "-o", out, "-D", 'part="none"', "-D", f'pp="{part}"', "-D", f"D={D}", os.path.join(CAD, "umeh3.scad")]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(out):
        raise RuntimeError(f"OpenSCAD failed for {part}: {r.stderr[-400:]}")
    return out


def _mass(p, V, area, D, wire_len):
    """(mass kg, fill fraction, material label)"""
    if p in PRINT:
        mat, per, tb, infill = PRINT[p]
        rho = PETG["rho"].v if mat == "PETG" else TPU["rho"].v
        shell = min(1.0, area * per * LINE_W / V) if V > 0 else 1.0
        f = shell + (1 - shell) * infill
        return rho * f * V, f, mat
    if p == "driver":
        return DRIVERS[D]["mass"] * 1e-3, None, "driver [A]"
    if p == "wire":
        return WIRE["rho"].v * np.pi * (geom.WIRE_D * 1e-3) ** 2 / 4 * wire_len, None, "music wire"
    if p in ("sleeve_arch", "sleeve_leg"):
        idd, od = geom.SIL_ARCH if p == "sleeve_arch" else geom.SIL_LEG
        # the mesh is a full rod of the sleeve OD: silicone = OD ring, PTFE liner inside
        frac_sil = 1 - (idd / od) ** 2
        frac_ptfe = ((geom.PTFE[1] ** 2 - geom.PTFE[0] ** 2) / od ** 2)
        return V * (SILICONE["rho"].v * frac_sil + PTFE_RHO.v * frac_ptfe), None, "silicone + PTFE"
    if p == "saddle_foam":      # slow-rebound PU foam + velour sock [A]
        return geom.SADDLE["foam_rho"] * V + 0.4e-3, None, "PU foam + velour sock"
    if p == "neckband":         # carried share of the band (rest on the neck/hair), wire + silicone sleeve
        from .neckband import LINK_SHARE
        Lw = np.linalg.norm(np.diff(np.array(geom.neck_path()), axis=0), axis=1).sum() * 1e-3
        return 0.0 * V, None, "neckband (point mass added in loads)"
    if p == "neck_eye":
        return PETG["rho"].v * 0.6 * V, None, "PETG eye clip"
    if p == "pad":
        return geom.PAD["mass"] * 1e-3, None, "purchased pad [A]"
    if p == "front_foam":
        return FOAM_RETIC.v * V, None, "reticulated PU"
    if p == "socket":
        return (SOCKET_M.v + PLUG_M.v + LEADS_M.v) * 1e-3, None, "socket + plug + leads"
    if p == "fibre":
        return ACOUSTIC_MAT["fibre_density"].v * V, None, "polyester fibre"
    raise KeyError(p)


def assembly(D, jobs=4, tag=None):
    """Per-part rows (kg, m, kg m^2 about the part COM) and the total (M, com, I about the COM) in the skin frame."""
    os.makedirs(TMP, exist_ok=True)
    tag = tag or f"D{D}"
    parts = [p for p in PARTS if (p != "paddle" or geom.PADDLE) and (not p.startswith("saddle") or geom.SADDLE)
             and (not p.startswith("neck") or geom.NECK)]
    if geom.SADDLE:
        parts = [p for p in parts if p != "sleeve_arch"]
    outs = {p: os.path.join(TMP, f"{tag}_{p}.stl") for p in parts}
    with cf.ThreadPoolExecutor(jobs) as ex:
        list(ex.map(lambda p: export(p, outs[p], D), parts))
    P, _ = geom.hook_path()
    wire_len = geom.path_length(P) * 1e-3
    rows = []
    for p in parts:
        V, area, cen, C = mesh_props(read_stl(outs[p]))
        m, f, mat = _mass(p, V, area, D, wire_len)
        s = m / V
        Cm = C * s
        Io = np.trace(Cm) * np.eye(3) - Cm
        Ic = Io - m * (np.dot(cen, cen) * np.eye(3) - np.outer(cen, cen))
        rows.append(dict(part=p, mat=mat, V=V, area=area, f=f, m=m, c=cen, I=Ic))
    return rows


def combine(rows):
    M = sum(r["m"] for r in rows)
    com = sum(r["m"] * r["c"] for r in rows) / M
    I = np.zeros((3, 3))
    for r in rows:
        d = r["c"] - com
        I += r["I"] + r["m"] * (np.dot(d, d) * np.eye(3) - np.outer(d, d))
    return M, com, I
