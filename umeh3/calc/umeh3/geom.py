"""
UMEH-3 geometry: the single source of the CAD numbers (written to cad/params3.scad by write_scad()).

Frame (right side, mm in this module, m in the solver): x forward, y up, z lateral (away from the head);
origin on the pad axis in the skin plane. The left side is the mirror image (x -> -x in its own frame).

Concept
  * One closed PETG shell: a flange plate (carries the pad) + a cup behind it, printed in one piece.
  * Any 40-60 mm driver: a TPU 95A adapter ring per driver size sits in the shell's 60 mm pocket; a PETG front
    ring locks it from the front with a 3-lug bayonet (quarter turn by hand). No glue, no screws.
  * Round universal 110 mm velour pad (purchased), pulled over the flange by its elastic lip (tool-free).
  * Ear hook: spring-steel music wire in a friction bushing on the shell (turns and slides to set the height),
    hand-bendable; on the skin a silicone sleeve that turns freely on a PTFE liner (rolls instead of rubbing).
  * 2-pin 0.78 mm socket on each shell, cable leaves low and rearward.
Source tags as in umeh2.materials: STD, DS, LIT, A (assumption), C (computed).
"""
import math
import numpy as np

from umeh2.design import DRIVERS, ANTHRO   # noqa: F401  (driver table and anthropometry shared with UMEH-2)

SIZES = (40, 45, 50, 55, 60)

# ------------------------------------------------------------------ purchased pad [A: typical listing values]
PAD = dict(
    od=110.0,        # [A] universal round pad, outer diameter
    id=60.0,         # [A] opening at the head face
    t=25.0,          # [A] thickness at rest (deep variant; 20-25 mm on the market)
    comp=1.0,        # [A] compression in use: the hook clamps lightly (checked against the solver in retention.py)
    lip_fit=96.0,    # [A] flange diameter the elastic lip is pulled over (listed fits ~90-105 mm)
    mass=11.0,       # [A] g per pad, velour cover + PU foam (listings 8-14 g)
    E_foam=20e3,     # [A] Pa, compressive modulus of slow-rebound PU foam at 10-30 % strain (10-30 kPa)
    contact_frac=0.7,  # [A] share of the annulus touching the skin (rounded profile)
)
Z_F = PAD["t"] - PAD["comp"]           # plate front face above the skin (pad compressed), mm

# ------------------------------------------------------------------ shell
PLATE_T = 1.2          # [A] flange plate thickness (closed back: no openings under the pad)
FLANGE_OD = PAD["lip_fit"]
BEAD_R = 1.0           # rear bead on the flange rim: the pad lip hooks behind it
POCKET_E = 5.5         # mm, offset of the driver pocket from the pad axis ...
POCKET_A = 225.0       # deg ... towards the rear-bottom (frees the front-top for the hook, see HOOK_HOLE)
POCKET_R = 60.5 / 2 + 0.22     # pocket radius: 60 mm driver rim + clearance
RING_T = 2.0           # front locking ring (PETG) thickness, recessed flush with the plate face
ADAPTER_H = 4.0        # TPU adapter height = front lip 1.0 + rim seat 2.0 + back lip 1.0
ADAPTER_SQ = 0.3       # TPU squeeze when the ring is locked
SHOULDER_RI = 26.0     # rear shoulder inner radius (passes the 60 mm basket, rear_d 50.4)
SHOULDER_T = 1.2
WALL = 1.2             # [A] cup wall
HUB_WALL = 2.2         # pocket wall (holds the bayonet grooves)
LUG_N, LUG_W, LUG_H, LUG_DEPTH, TWIST = 3, 9.0, 1.0, 1.1, 30.0   # bayonet: 3 lugs, 30 deg turn
CUP_H = 21.0           # cup outer height behind the plate front face (clears the 60 mm magnet + fibre)
CUP_ROUND = 8.0
FIBRE_T = 3.0          # polyester fibre pad on the inside of the cup end (rear damping)

# ------------------------------------------------------------------ hook
WIRE_D = 1.6           # mm ASTM A228 music wire (sized in hook.py)
HOOK_HOLE_R, HOOK_HOLE_A = 28.0, 50.0      # where the wire passes the plate (inside the pad opening, front-top)
BOSS_L = 16.0          # bushing boss behind the plate (wire guide + friction bushing)
BUSH_OD, BUSH_L = 4.4, 8.0                 # TPU friction bushing (printed), bore 1.45 on the 1.6 wire
PTFE = (2.0, 3.0)      # [DS] PTFE liner tube ID x OD (the sleeve turns on the wire)
SIL_ARCH = (3.0, 8.0)  # [DS] silicone tube ID x OD over the liner on the root arch (wide bearing)
SIL_LEG = (3.0, 5.0)   # [DS] silicone tube ID x OD over the liner on the descent and the rear leg
# ear landmarks [A] relative to the pad axis (pinna centroid on the axis): the hook arch follows the
# superior auricle-root arch of radius ROOT_ARCH_R (umeh2.support, 18-30 mm) centred at ARCH_C
ARCH_C = (-3.0, 1.0)
ARCH_R = 22.0
ARCH_A0, ARCH_A1 = 44.0, 135.0   # deg, arch from where the descent meets it to where the rear leg leaves
ROOT_PHI = 35.0                  # deg, the two bearing zones at 90 +- phi (as UMEH-2's arched saddle)
ROOT_W = 6.0                     # [A] loaded width of the 8 mm silicone sleeve on the root skin
ROOT_ZONE_L = 12.5               # [A] loaded length per zone (25 mm of root, UMEH-2 ROOT_LEN)
Z_ROOT = 4.0                     # sleeve centre above the skin plane at the root (OD 8)
LEG_PTS = [(-14.0, 6.0, 5.0), (-12.0, -6.0, 5.0), (-10.0, -15.0, 6.5)]   # rear leg in the retro-auricular sulcus [A]
TIP = (-7.0, -20.0, 10.0)        # tip curls away from the skin (silicone end cap)
PINNA_PT = (-13.0, 0.0, 5.0)     # where the leg presses on the cranial face of the pinna (preload, -z on the device)
SULCUS_PT = (-12.0, -8.0, 2.5)   # where the leg can bear on the mastoid skin (+z)

# ------------------------------------------------------------------ cable socket [DS: common 0.78 mm 2-pin female]
SOCKET = dict(w=5.0, l=9.8, h=7.0, a=250.0, mass=0.6)   # a: position angle around the pocket centre (rear-bottom)


def pol(r, a_deg, z=0.0):
    a = math.radians(a_deg)
    return np.array([r * math.cos(a), r * math.sin(a), z])


def pocket_c():
    return pol(POCKET_E, POCKET_A)[:2]


def hook_hole():
    return pol(HOOK_HOLE_R, HOOK_HOLE_A)[:2]


def arch_pt(a_deg, z=Z_ROOT):
    return np.array([ARCH_C[0] + ARCH_R * math.cos(math.radians(a_deg)),
                     ARCH_C[1] + ARCH_R * math.sin(math.radians(a_deg)), z])


def hook_path(step_deg=7.0):
    """Wire centreline (mm), rear end first: stop cap behind the bushing -> plate -> descent through the pad opening
    -> root arch -> rear leg -> tip. Returns (points, segment labels)."""
    h = hook_hole()
    pts, lab = [], []

    def add(p, l):
        pts.append(np.asarray(p, float)); lab.append(l)
    add([h[0], h[1], Z_F + BOSS_L + 3.0], "tail")
    add([h[0], h[1], Z_F + BOSS_L - BUSH_L / 2], "bushing")
    if GROOVE_R_IN is None:
        add([h[0], h[1], Z_F], "plate")
        add([h[0], h[1], 12.0], "descent")
    else:
        zg = Z_F + 0.3                       # wire centre in the plate-face groove (behind the pad's back face)
        add([h[0], h[1], zg], "plate")
        g = pol(GROOVE_R_IN, HOOK_HOLE_A)[:2]
        add([g[0], g[1], zg], "groove")
        add([g[0] - 0.8, g[1] - 0.8, 12.0], "descent")
        h = g
    a0 = arch_pt(ARCH_A0)
    add([0.5 * (h[0] + a0[0]) + 0.6, 0.5 * (h[1] + a0[1]) + 0.6, 6.0], "descent")
    n = int(math.ceil((ARCH_A1 - ARCH_A0) / step_deg))
    for i in range(n + 1):
        add(arch_pt(ARCH_A0 + (ARCH_A1 - ARCH_A0) * i / n), "arch")
    for p in LEG_PTS:
        add(p, "leg")
    add(TIP, "tip")
    return np.array(pts), lab


def path_length(P):
    return float(np.linalg.norm(np.diff(P, axis=0), axis=1).sum())


def _leg_dir():
    """Unit direction (xy) of the rear leg at the pinna clamp point."""
    P = np.array(LEG_PTS, float)
    d = P[-1, :2] - P[0, :2]
    return d / np.linalg.norm(d)


def write_scad(path):
    """cad/params3.scad: every CAD number, generated (do not edit by hand)."""
    P, lab = hook_path()
    pc, hh = pocket_c(), hook_hole()
    a0 = lab.index("arch"); a1 = len(lab) - 1 - lab[::-1].index("arch")
    lines = [
        "// GENERATED by calc/umeh3/geom.py write_scad() - do not edit",
        f"PAD_OD = {PAD['od']}; PAD_ID = {PAD['id']}; PAD_T = {PAD['t']}; PAD_COMP = {PAD['comp']};",
        f"Z_F = {Z_F}; PLATE_T = {PLATE_T}; FLANGE_OD = {FLANGE_OD}; BEAD_R = {BEAD_R};",
        f"PC = [{pc[0]:.4f}, {pc[1]:.4f}]; POCKET_R = {POCKET_R}; RING_T = {RING_T}; ADAPTER_H = {ADAPTER_H};",
        f"ADAPTER_SQ = {ADAPTER_SQ}; SHOULDER_RI = {SHOULDER_RI}; SHOULDER_T = {SHOULDER_T}; WALL = {WALL};",
        f"HUB_WALL = {HUB_WALL}; LUG_N = {LUG_N}; LUG_W = {LUG_W}; LUG_H = {LUG_H}; LUG_DEPTH = {LUG_DEPTH}; TWIST = {TWIST};",
        f"CUP_H = {CUP_H}; CUP_ROUND = {CUP_ROUND}; FIBRE_T = {FIBRE_T};",
        f"WIRE_D = {WIRE_D}; HH = [{hh[0]:.4f}, {hh[1]:.4f}]; BOSS_L = {BOSS_L}; BUSH_OD = {BUSH_OD}; BUSH_L = {BUSH_L};",
        f"PTFE = [{PTFE[0]}, {PTFE[1]}]; SIL_ARCH = [{SIL_ARCH[0]}, {SIL_ARCH[1]}]; SIL_LEG = [{SIL_LEG[0]}, {SIL_LEG[1]}];",
        f"SOCKET = [{SOCKET['w']}, {SOCKET['l']}, {SOCKET['h']}]; SOCKET_A = {SOCKET['a']};",
        "HOOK = [" + ", ".join(f"[{p[0]:.3f}, {p[1]:.3f}, {p[2]:.3f}]" for p in P) + "];",
        f"HOOK_ARCH = [{a0}, {a1}];   // index range of the arch (wide sleeve)",
        f"HOOK_PLATE = {lab.index('plate')};",
        f"GROOVE = {'true' if GROOVE_R_IN is not None else 'false'}; GROOVE_R_IN = {GROOVE_R_IN or 0}; HOOK_A = {HOOK_HOLE_A};",
        f"HOOK_DESC = {lab.index('descent')};",
        f"PADDLE = {list(PADDLE) if PADDLE else 'undef'}; PINNA_PT = {list(PINNA_PT)};",
        f"LEG_DIR = [{_leg_dir()[0]:.4f}, {_leg_dir()[1]:.4f}];",
        "DRV = [ // D, rim OD, rim t, rear d, depth, aperture (umeh2.design.DRIVERS)",
        "  " + ", ".join(f"[{D}, {DRIVERS[D]['mount_d']}, {DRIVERS[D]['rim_t']}, {DRIVERS[D]['rear_d']}, "
                         f"{DRIVERS[D]['depth']}, {DRIVERS[D]['front_open']}]" for D in SIZES) + "];",
    ]
    with open(path, "w") as fh:
        fh.write("\n".join(lines) + "\n")
GROOVE_R_IN = None              # hook routed in a groove in the plate face under the pad (small pad): exits at this radius
PADDLE = None                    # (w, L, t) mm: wide TPU paddle on the rear leg, against the back of the pinna
LOBE_PT = None                   # contact under the lobule attachment (only a hook that wraps under it)

# ------------------------------------------------------------------ design variants
# base: first draft (2026-10-01). A "gancho maior": longer, wider hook for running: the arch covers more of the root
# with a 10 mm sleeve, the rear leg runs down behind the ear and its tip curls forward under the lobule attachment,
# so a bounce cannot lift the hook off the root. B "almofada menor": set in variant B (pad size chosen by the user).
VARIANTS = {
    "base": {},
    "A": dict(ARCH_A0=35.0, ARCH_A1=145.0, PTFE=(2.0, 4.0), SIL_ARCH=(4.0, 10.0), SIL_LEG=(4.0, 7.0),
              ROOT_W=7.5, ROOT_ZONE_L=15.0, Z_ROOT=5.0,
              LEG_PTS=[(-16.0, 8.0, 5.5), (-14.5, -5.0, 5.5), (-11.5, -17.0, 5.5), (-6.5, -25.5, 5.0)],
              TIP=(-0.5, -28.0, 6.5), PINNA_PT=(-14.5, -3.0, 5.5), SULCUS_PT=(-12.5, -12.0, 3.5),
              LOBE_PT=(-3.5, -27.0, 5.0), PADDLE=(14.0, 36.0, 3.0)),
    # B "almofada menor": round 90 mm pad (user's choice 2026-10-01), first-draft hook. The 50 mm opening is too small for
    # the wire to pass the plate inside it next to a 60 mm driver, so the wire passes the plate under the pad (r 35)
    # and runs in a groove in the plate face to the opening; the driver pocket is centred.
    "B": dict(PAD=dict(od=90.0, id=50.0, t=20.0, comp=1.0, lip_fit=78.0, mass=7.0, E_foam=20e3, contact_frac=0.7),
              FLANGE_OD=78.0, POCKET_E=0.0, HOOK_HOLE_R=35.0, GROOVE_R_IN=23.5, PADDLE=(14.0, 36.0, 3.0)),
}
_KEYS = sorted({k for v in VARIANTS.values() for k in v} | {"PAD"})
_BASE = {k: globals()[k] for k in _KEYS}
VARIANT = "base"


def apply(name, **extra):
    """Switch the module to design variant `name` (VARIANTS) plus extra overrides; recompute Z_F."""
    global VARIANT, Z_F
    import copy
    g = globals()
    for k, v in _BASE.items():
        g[k] = copy.deepcopy(v)
    for k, v in dict(VARIANTS[name], **extra).items():
        g[k] = copy.deepcopy(v)
    Z_F = g["PAD"]["t"] - g["PAD"]["comp"]
    g["FLANGE_OD"] = dict(VARIANTS[name], **extra).get("FLANGE_OD", g["PAD"]["lip_fit"])
    VARIANT = name
