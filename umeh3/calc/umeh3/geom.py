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
LUG_N, LUG_W, LUG_H, LUG_DEPTH, TWIST = 3, 14.0, 1.0, 1.1, 30.0  # bayonet: 3 lugs 14 mm wide (drop, strength.py), 30 deg turn
CUP_H = 31.0           # cup outer height behind the plate front face; 10 mm deeper than the first draft: bigger rear
                       # chamber, lower closed-box resonance (studies/rear_options.py)
CUP_ROUND = 8.0
FIBRE_T = 11.8         # polyester fibre fill of the rear chamber above the motor (damping, isothermal volume gain)

# ------------------------------------------------------------------ hook
WIRE_D = 1.6           # mm ASTM A228 music wire (sized in hook.py)
HOOK_HOLE_R, HOOK_HOLE_A = 28.0, 50.0      # where the wire passes the plate (inside the pad opening, front-top)
BOSS_L = 16.0          # bushing boss behind the plate (wire guide + friction bushing)
BUSH_OD, BUSH_L = 4.4, 8.0                 # TPU friction bushing (printed), bore 1.45 on the 1.6 wire
# rotation lock: the wire tail is bent into a 12 mm radial crank whose end is bent down into a pin; the pin drops
# into one of 9 holes in an arc wall on the back of the plate (16 deg steps, +-64 deg; the wire bends by hand for fine
# tuning). The bushing only holds the height; running twists the hook up to ~66 N mm, more than its friction
# (strength.py). Height range = pin length in the hole. To turn: lift the pin out, turn, drop it in another hole.
LOCK = dict(r=12.0, w=4.0, hole=2.1, depth=9.0, step=16.0, n=9, pin=7.0)
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
    zc = Z_F + BOSS_L + 2.0 + LOCK["pin"] / 2               # crank above the lock wall, pin half way in its hole
    u = np.array([h[0] - pocket_c()[0], h[1] - pocket_c()[1]]); u = u / np.linalg.norm(u)     # away from the cup
    R = LOCK["r"]
    add([h[0] + R * u[0], h[1] + R * u[1], zc - LOCK["pin"]], "pin")
    add([h[0] + R * u[0], h[1] + R * u[1], zc - 1.5], "pin")
    add([h[0] + (R - 1.5) * u[0], h[1] + (R - 1.5) * u[1], zc], "crank")
    add([h[0] + 1.5 * u[0], h[1] + 1.5 * u[1], zc], "crank")
    add([h[0], h[1], zc - 1.5], "tail")
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


NECK_EYE_Z = -1.2      # band axis BELOW the back face: the sleeve lies in a keyhole channel in the back (3.6 mm
                       # opening on the 4 mm sleeve: it snaps in; 0.8 mm proud), the wire end bent down into a blind hole (= neckband.EYE_Z_OUT). Refinement
                       # 2026-10-01: no clip standing on the back, so a back-down drop no longer lands on a point in
                       # the middle of the flat back (studies/durability.py)
NECK_SLEEVE = 4.0      # [DS] silicone tube 2 x 4 mm over the band wire (was 5.8 mm OD: 7 g lighter per band)
NECK_PIN = 3.5         # wire end bent 90 deg into the back (blind hole): the band cannot slide out of the channel
NECK_EXIT_DEG = 68.0   # the channel follows the cup's rounded edge to this angle, then the band leaves tangentially


def neck_path():
    """First part of the neckband (mm, this side's frame; the rest runs around the nape). Index 0 is the bent end in
    the blind hole, then the eye (on the pad axis, in the back channel), along the channel over the cup's rounded edge
    (axis NECK_EYE_Z under the surface), out tangentially over the top of the pad, clear of its outer edge -> down
    behind the pad towards the head -> back and down towards the nape. Checked against the meshes (band_clearance.py).
    Returns the points; neck_embedded() gives the index of the last point inside the channel."""
    return _neck()[0]


def neck_embedded():
    return _neck()[1]


def _neck():
    zt = Z_F + CUP_H
    e = -NECK_EYE_Z
    pc = pocket_c()
    ro = PAD["od"] / 2 + 8.0               # outside the pad's outer edge + sleeve radius + gap
    u = np.array([-43.0, -5.0]); u = u / np.linalg.norm(u)
    r1 = POCKET_R + HUB_WALL - CUP_ROUND
    # where the line from the axis along u reaches r1 (from the pocket centre)
    s = np.linspace(0, 60, 6001)
    rr = np.linalg.norm(s[:, None] * u[None, :] - pc[None, :], axis=1)
    s1 = s[np.argmax(rr >= r1)]
    p1 = s1 * u
    v = (p1 - pc) / np.linalg.norm(p1 - pc)            # radial direction at the rim crossing
    pts = [(0.0, 0.0, zt - e - NECK_PIN), (0.0, 0.0, zt - e)]
    for f in (0.35, 0.7):
        q = f * p1; pts.append((q[0], q[1], zt - e))
    pts.append((p1[0], p1[1], zt - e))
    rc = CUP_ROUND - e
    for th in (18.0, 36.0, NECK_EXIT_DEG):
        t = math.radians(th)
        q = pc + v * (r1 + rc * math.sin(t))
        pts.append((q[0], q[1], zt - CUP_ROUND + rc * math.cos(t)))
    n_emb = len(pts) - 1
    t = math.radians(NECK_EXIT_DEG)
    last = np.array(pts[-1]); tan = np.r_[v * math.cos(t), -math.sin(t)]
    pts.append(tuple(last + 7.0 * tan))
    pts += [(-0.94 * ro, -8.0, Z_F + 9.0), (-ro, -12.0, Z_F + 2.0), (-ro - 1.0, -18.0, 12.0),
            (-ro - 3.0, -26.0, 0.0), (-ro - 9.0, -34.0, -10.0)]
    return [tuple(map(float, p)) for p in pts], n_emb


def _leg_dir():
    """Unit direction (xy) of the rear leg at the pinna clamp point."""
    P = np.array(LEG_PTS, float)
    d = P[-1, :2] - P[0, :2]
    return d / np.linalg.norm(d)


def _wp_scad():
    if not WP:
        return "WP = undef;"
    w = WP
    return ("WP = true; " + f"MEMB_T = {w['memb_t']}; OR_CORD = {w['cord']}; OR_G = [{w['groove'][0]}, {w['groove'][1]}]; "
            f"OR_GD = {w['gdepth']}; CABLE_D = {w['cable_d']}; GL_CORD = {w['gland_cord']}; GL_ID = {w['gland_id']}; "
            f"POGO = [{w['pogo_d']}, {w['pogo_l']}, {w['pogo_a']}, {w['pogo_z']}]; "
            f"SLIDER = [{w['slider'][0]}, {w['slider'][1]}, {w['slider'][2]}]; MAGNET = [{w['magnet'][0]}, {w['magnet'][1]}]; "
            f"MOD_SIDE = \"{w['module_side']}\"; BOARD = {list(w['board'])}; CHARGER = {list(w['charger'])}; "
            f"BATT = {list(w['battery'])}; POST_R = {w['post_r']}; POST_L = {w['post_l']};")


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
        f"LOCK = [{LOCK['r']}, {LOCK['w']}, {LOCK['hole']}, {LOCK['depth']}, {LOCK['step']}, {LOCK['n']}];",
        f"PTFE = [{PTFE[0]}, {PTFE[1]}]; SIL_ARCH = [{SIL_ARCH[0]}, {SIL_ARCH[1]}]; SIL_LEG = [{SIL_LEG[0]}, {SIL_LEG[1]}];",
        f"SOCKET = [{SOCKET['w']}, {SOCKET['l']}, {SOCKET['h']}]; SOCKET_A = {SOCKET['a']};",
        "HOOK = [" + ", ".join(f"[{p[0]:.3f}, {p[1]:.3f}, {p[2]:.3f}]" for p in P) + "];",
        f"HOOK_ARCH = [{a0}, {a1}];   // index range of the arch (wide sleeve)",
        f"HOOK_PLATE = {lab.index('plate')};",
        f"GROOVE = {'true' if GROOVE_R_IN is not None else 'false'}; GROOVE_R_IN = {GROOVE_R_IN or 0}; HOOK_A = {HOOK_HOLE_A};",
        f"HOOK_DESC = {lab.index('descent')};",
        f"PADDLE = {list(PADDLE) if PADDLE else 'undef'}; PINNA_PT = {list(PINNA_PT)};",
        f"LEG_DIR = [{_leg_dir()[0]:.4f}, {_leg_dir()[1]:.4f}];",
        f"NECK_EYE_Z = {NECK_EYE_Z}; NECK_PIN = {NECK_PIN}; NECK_EMB = {neck_embedded() if NECK else 0};",
        "NECK = " + ("[" + ", ".join(f"[{p[0]:.2f}, {p[1]:.2f}, {p[2]:.2f}]" for p in neck_path()) + "]" if NECK else "undef") + ";",
        f"NECK_D = {NECK_WIRE_D}; NECK_SL = {NECK_SLEEVE};",
        _wp_scad(),
        "SADDLE = " + (f"[{SADDLE['w']}, {SADDLE['t_foam']}, {SADDLE['carrier_t']}]" if SADDLE else "undef") + ";",
        f"ARCH_C = [{ARCH_C[0]}, {ARCH_C[1]}]; ARCH_R = {ARCH_R}; ARCH_A = [{ARCH_A0}, {ARCH_A1}]; Z_ROOT = {Z_ROOT};",
        "DRV = [ // D, rim OD, rim t, rear d, depth, aperture (umeh2.design.DRIVERS)",
        "  " + ", ".join(f"[{D}, {DRIVERS[D]['mount_d']}, {DRIVERS[D]['rim_t']}, {DRIVERS[D]['rear_d']}, "
                         f"{DRIVERS[D]['depth']}, {DRIVERS[D]['front_open']}]" for D in SIZES) + "];",
    ]
    with open(path, "w") as fh:
        fh.write("\n".join(lines) + "\n")
GROOVE_R_IN = None              # hook routed in a groove in the plate face under the pad (small pad): exits at this radius
SADDLE = None                    # wide soft saddle on the hook arch: dict(w, t_foam, E_foam, carrier_t) (model A, 2026-10-01)
NECK = False                     # neckband (user's choice 2026-10-01): eye on the back of the cup, wire to the nape
NECK_WIRE_D = 1.8                # sized in neckband.design for the 2 N band: 1.8 mm music wire, no coils (the plain
                                 # bent wire; the contact model has always used this one)
PADDLE = None                    # (w, L, t) mm: wide TPU paddle on the rear leg, against the back of the pinna
LOBE_PT = None                   # contact under the lobule attachment (only a hook that wraps under it)
# waterproof build (UMEH-3W, user 2026-10-03: shower + brief dive = IPX7, Bluetooth, one module, wires in the band).
# Seal chain (no glue): front ring -> ePTFE acoustic membrane -> O-ring A in the adapter front face; adapter back face
# -> O-ring B -> shell shoulder. The bayonet clamps the stack to a hard stop (squeeze set by the groove depth). Cable
# into each cup through an O-ring gland under the band sleeve; magnetic pogo charge port with an O-ring; power by a
# magnet slider over a reed switch (no hole). Electronics on printed trays twisted onto posts inside the cups.
WP = None

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
    # A final (user 2026-10-01: continue with A only, neckband, wide soft saddle approved): A + neckband + a 20 mm wide
    # saddle on the arch: TPU carrier clipped on the wire, 6 mm slow-rebound foam strip in a velour sock on the root side.
    # The arch radius grows by the saddle build-up so the bearing stays on the root (contact radius 17 mm as before).
    "AF": dict(ARCH_A0=35.0, ARCH_A1=145.0, PTFE=(2.0, 4.0), SIL_ARCH=(4.0, 10.0), SIL_LEG=(4.0, 7.0),
               ROOT_W=20.0, ROOT_ZONE_L=15.0, Z_ROOT=10.0, ARCH_R=26.0,
               LEG_PTS=[(-18.5, 8.0, 6.0), (-14.5, -5.0, 5.5), (-11.5, -17.0, 5.5), (-6.5, -25.5, 5.0)],
               TIP=(-0.5, -28.0, 6.5), PINNA_PT=(-14.5, -3.0, 5.5), SULCUS_PT=(-12.5, -12.0, 3.5),
               LOBE_PT=(-3.5, -27.0, 5.0), PADDLE=(14.0, 36.0, 3.0), NECK=True,
               SADDLE=dict(w=20.0, t_foam=6.0, E_foam=25e3, carrier_t=1.2, foam_rho=50.0)),
    # W: waterproof A final (see WP). Pocket +1.2 mm radius so the TPU adapter keeps a 1.25 mm wall outside the 60 mm
    # rim (it separates wet from dry); adapter 6 mm (2 mm lips carry the O-ring grooves); cup +2.5 mm (rear chamber
    # kept); band sleeve 4x6 (wire + 4-core cable); protein-leather pad (heavier) [A].
    "AW": dict(ARCH_A0=35.0, ARCH_A1=145.0, PTFE=(2.0, 4.0), SIL_ARCH=(4.0, 10.0), SIL_LEG=(4.0, 7.0),
               ROOT_W=20.0, ROOT_ZONE_L=15.0, Z_ROOT=10.0, ARCH_R=26.0,
               LEG_PTS=[(-18.5, 8.0, 6.0), (-14.5, -5.0, 5.5), (-11.5, -17.0, 5.5), (-6.5, -25.5, 5.0)],
               TIP=(-0.5, -28.0, 6.5), PINNA_PT=(-14.5, -3.0, 5.5), SULCUS_PT=(-12.5, -12.0, 3.5),
               LOBE_PT=(-3.5, -27.0, 5.0), PADDLE=(14.0, 36.0, 3.0), NECK=True,
               SADDLE=dict(w=20.0, t_foam=6.0, E_foam=25e3, carrier_t=1.2, foam_rho=50.0),
               PAD=dict(od=110.0, id=60.0, t=25.0, comp=1.0, lip_fit=96.0, mass=14.0, E_foam=20e3, contact_frac=0.7),
               POCKET_R=31.7, ADAPTER_H=6.0, ADAPTER_SQ=0.0, CUP_H=33.5, NECK_SLEEVE=6.0, NECK_EYE_Z=-1.7,
               WP=dict(memb_t=0.2, cord=1.5, groove=(28.0, 30.0), gdepth=1.2, oring="55 x 1,5 mm NBR",
                       cable_d=2.2, gland_cord=1.0, gland_id=2.0,
                       pogo_d=8.5, pogo_l=7.0, pogo_a=12.0, pogo_z=12.5,     # pogo_a/z: x, y on the back (pocket frame)
                      
                       slider=(11.0, -4.0, 12.0), magnet=(6.0, 2.0), module_side="R",
                       board=(23.0, 16.5, 3.0), charger=(17.0, 26.0, 4.0), battery=(30.0, 30.0, 5.0),
                       post_r=24.0, post_l=10.2)),
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
