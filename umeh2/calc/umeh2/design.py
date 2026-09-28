"""
UMEH-2 parameter model: design INPUTS (chosen by the engineer or by the
sizing routines) -> every CAD dimension. write_scad() emits
cad/generated_params.scad, so the CAD is always generated from the
numbers the calculations used.
"""
import copy, math, os
from .materials import SCREW

HERE = os.path.dirname(os.path.abspath(__file__))
CAD = os.path.normpath(os.path.join(HERE, "..", "..", "cad"))

SIZES = [40, 45, 50, 55, 60]

# ------------------------------------------------------------------ drivers
# PLACEHOLDER geometry and mass per nominal size [A]. Replace with calipers
# and scale readings of the real drivers (the whole chain re-runs).
FRONT_OPEN_RATIO = 0.88   # [A] clear diameter in front of the diaphragm / nominal D (clears diaphragm + half the surround)
DRIVERS = {
    D: dict(
        D=D,
        mount_d=D + 0.5,                 # [A] rim OD
        front_open=round(FRONT_OPEN_RATIO * D, 1),   # [A] clear diameter in front of the diaphragm
        rim_t=1.8 if D < 50 else 2.0,    # [A]
        depth=round(0.20 * D + 2.0, 1),  # [A] rim face -> back of magnet
        rear_d=round(0.84 * D, 1),       # [A] largest diameter behind the rim
        mass=m,                          # [A] g, typical neodymium headphone drivers
        tol_d=0.3, tol_depth=0.4,        # [A] +/- manufacturing tolerance on rim OD / depth
    )
    for D, m in [(40, 15.0), (45, 19.0), (50, 26.0), (55, 33.0), (60, 40.0)]
}

# ------------------------------------------------------------------ anthropometry [A]
ANTHRO = dict(
    pinna_protrusion_mean=20.0,   # mm, auricle protrusion (helix to mastoid skin), LIT 17–22 mean
    pinna_protrusion_p95=26.0,    # mm, LIT/A
    pinna_length_p95=72.0,        # mm
    concha_depth=12.0,            # mm, pinna surface to canal-entrance plane, LIT 10–16
    head_half_width=75.0,         # mm, tragion-to-midline (for the link geometry), LIT 70–80
    occiput_r=95.0,               # mm, radius of the head arc behind the ears at link height, A
)

PINNA_CLEAR = 3.0    # mm [A] clearance between the p95 pinna (helix) and the ring head face
STANDOFF = math.ceil((ANTHRO["pinna_protrusion_p95"] + PINNA_CLEAR) * 2) / 2    # mm, skin -> ring head face, 0.5 mm grid [C]

# ------------------------------------------------------------------ design inputs
BASE = dict(
    name="B",
    # --- attachment geometry (ear frame, degrees CCW from forward, right side)
    saddle_a=95.0, temporal_a=35.0, mastoid_a=225.0, cable_a=285.0,
    saddle_r=32.0, temporal_r=40.0, mastoid_r=45.0,
    standoff=STANDOFF,           # skin -> ring head face: p95 pinna protrusion + PINNA_CLEAR
    saddle_skin_gap=1.0,
    pad_h=6.0,
    # --- arm cross-sections (sized in structure.size_arms())
    bar_t=4.0, leg_t=5.0, foot_t=5.0, foot_t_mastoid=6.0, arm_w=10.0, saddle_arm_w=16.0, fillet_r=4.0,
    slot_adj=4.0,
    # --- pads (sized from pressure in support.size_pads())
    pad_t_a=26.0, pad_t_b=30.0, pad_m_a=30.0, pad_m_b=38.0, pad_face=None, pad_face_t=0.0,
    saddle_cap_L=40.0, saddle_cap_wall=2.0, saddle_strip_L=26.0, saddle_liner_t=0.0,
    # --- fasteners (selected in structure.select_fasteners())
    arm_screw="M3", pad_screw="M2.5", cup_screw="M2.5", use_lock=False,
    serrated=False, serr_p=1.2, serr_h=0.6, arm_torque=0.25,
    anchor_screw="M3", anchor_torque=0.15,     # cable anchor + clip: carries the cable fuse loads (extras.anchor_screws)
    # --- UMI-2 twist lock
    lug_h=2.5, lug_t=3.0, lip_t=2.2, floor_t=2.0, groove_rclr=0.35, radial_clr=0.2,
    gasket_umi_t=1.2, gasket_squeeze=0.35, notch_extra=2.0, twist=40.0,
    # UMI axial preload element: "gasket" = flat solid-TPU ring under the lugs (Design A/B);
    # "foam" = lug bottoms on the rigid groove floor + die-cut PU-foam strips on the lug tops (Final, see
    # structure.twistlock). foam_t: sheet thickness (1/16 in standard sheet), foam_eps: nominal strain.
    umi_mode="gasket", foam_t=1.6, foam_eps=0.35, lug_ramp_c=0.0, lug_ramp_L=3.5,
    lug_widths=(26.0, 18.0, 18.0),
    # --- link
    wire_d=1.6, link_preload=1.2, link_coils=0, link_mode="mastoid", link_a=180.0, link_x=0.0, link_y=0.0,
    post_a=None, post_r=55.0, pad_p_a=26.0, pad_p_b=30.0,
    rely_helix=True, saddle_scalp=False, saddle_arch=False, arch_R=22.0, arch_phi=35.0,
    # --- module / acoustics (sized in acoustics.size_module())
    baffle_front_t=2.4, aperture_chamfer=1.5, driver_pocket_clr=0.25, driver_gasket_t=1.0,
    gasket_driver_squeeze=0.3, clamp_depth=1.0, cup_wall=1.6, cup_end_t=2.0,
    felt_t=2.0, felt_psa_w=2.0,  # rear felt: cut disc bonded by an acrylic PSA rim felt_psa_w wide (extras.felt_bond)
    rear_type="open", grille_hole=3.0, grille_pitch=3.9, vent_n=3, vent_d=2.0,
    cup_h_extra=5.0,             # rear clearance above magnet (sets Vb; sized per driver)
    # --- cable
    connector_size=(5.0, 9.8, 7.0), cable_od=3.8, clip_wall=2.5, clip_interf=0.2, clip_len=8.0, clip_gap=1.2,
    anchor_h=9.0, clip_post_t=5.0, clip_post_L=22.0,
    # --- seal-pad option
    seal_id=62.0, seal_od=92.0,
)


TAB_WALL = 3.2   # mm [A] PETG wall around the arm-screw inserts in a ring tab (tab width = insert OD + 2 x this, >= 12 mm)
INSERT_WALL_MIN = 1.6    # mm [A] smallest printed wall around a heat-set insert
INSERT_WALL_RULE = 0.5   # [DS] supplier guidance: wall around a heat-set insert >= this x insert OD


def insert_wall(size):
    """Printed wall around a heat-set insert of `size` (baffle, eye boss): the supplier rule or the minimum wall."""
    return max(INSERT_WALL_MIN, INSERT_WALL_RULE * SCREW[size]["insert_od"])
EYE_SLEEVE_L = 4.0    # mm, brass sleeve of the link eye, clamped to the cup boss by the M2.5 eye screw
EYE_SLEEVE_ID = 2.7   # mm, clears the M2.5 screw


def screw(name):
    return SCREW[name]


def circle_overlap(R, r, c):
    """Area common to two circles of radii R and r whose centres are c apart (same units)."""
    if r <= 0 or c >= R + r:
        return 0.0
    if c <= abs(R - r):
        return math.pi * min(R, r) ** 2
    a1 = r * r * math.acos((c * c + r * r - R * R) / (2 * c * r))
    a2 = R * R * math.acos((c * c + R * R - r * r) / (2 * c * R))
    return a1 + a2 - 0.5 * math.sqrt((-c + r + R) * (c + r - R) * (c - r + R) * (c + r + R))


def derived(des, D):
    """All CAD numbers for design `des` and driver size D."""
    d = dict(des)
    drv = DRIVERS[D]
    Dmax = DRIVERS[max(SIZES)]
    cs = screw(des["cup_screw"]); as_ = screw(des["arm_screw"]); ps = screw(des["pad_screw"])
    # ---------------- module outer radius: set by the LARGEST driver (common interface)
    # rim clearance + insert hole + wall on both sides of the insert
    ins_wall = insert_wall(des["cup_screw"])                       # rule and hoop stress checked in structure.insert_boss()
    pocket_r = Dmax["mount_d"] / 2 + des["driver_pocket_clr"]
    cup_screw_r = pocket_r + ins_wall + cs["insert_hole"] / 2
    R_S = cup_screw_r + cs["insert_hole"] / 2 + ins_wall
    R_S = math.ceil(R_S * 2) / 2                                    # 0.5 mm grid
    d["spig_d"] = 2 * R_S
    d["bore_d"] = 2 * (R_S + des["radial_clr"])
    d["cup_screw_r"] = cup_screw_r
    d["cup_screw_a"] = [30.0, 150.0, 270.0]
    d["cup_ins_hole"] = cs["insert_hole"]; d["cup_ins_L"] = cs["insert_L"]
    d["cup_screw_clear"] = cs["d"] + 0.4; d["cup_csk_d"] = cs["csk_d"] + 0.4
    d["cup_boss_d"] = cs["d"] + 0.4 + 2 * 1.6
    # ---------------- ring
    if des.get("umi_mode", "gasket") == "foam":
        # lug bottoms bear on the rigid groove floor; the foam strip between the parallel 45 deg cones (lug top,
        # lip underside) is compressed to foam_t*(1-foam_eps) normal to the cones -> vertical gap sqrt2 x that
        gap_v = math.sqrt(2) * des["foam_t"] * (1 - des["foam_eps"])
        d["groove_h"] = des["lug_t"] - des["groove_rclr"] + gap_v
        d["z_mod0"] = des["floor_t"]
    else:
        d["groove_h"] = des["gasket_umi_t"] - des["gasket_squeeze"] + des["lug_t"] + 0.15
        d["z_mod0"] = des["floor_t"] + des["gasket_umi_t"] - des["gasket_squeeze"]
    R_G = R_S + des["lug_h"] + des["groove_rclr"]
    d["ring_od"] = 2 * (R_G + max(3.0, des["lip_t"] + 0.8))
    d["lugs"] = [[0.0, des["lug_widths"][0]], [120.0, des["lug_widths"][1]], [240.0, des["lug_widths"][2]]]
    w0 = des["lug_widths"][0]
    d["stop_a"] = [w0 / 2 + des["twist"] + 1.0, w0 / 2 + des["twist"] + 12.0]
    d["lock_clear"] = 2.4; d["lock_pilot"] = 1.6
    d["tab_w"] = max(12.0, as_["insert_od"] + 2 * TAB_WALL)
    d["tab_t"] = des["floor_t"] + d["groove_h"] + (R_G - (R_S + des["radial_clr"])) + des["lip_t"]
    d["tab_ins_hole"] = as_["insert_hole"]; d["tab_ins_L"] = as_["insert_L"]
    # arm screws: 2 on the arm centreline at pitch p; minimum p = insert OD + 2.5 mm (>= 7 mm); a larger pitch
    # (des['arm_screw_pitch']) moves only the OUTER insert outward (the inner one stays clear of the ring)
    p_min = max(7.0, as_["insert_od"] + 2.5)
    d["tab_ins_pitch"] = max(p_min, des.get("arm_screw_pitch") or 0.0)
    d["tab_r"] = d["ring_od"] / 2 + p_min * 0.5 + as_["insert_od"] / 2 + 2.0 + d["tab_ins_pitch"]
    d["tabs"] = [[des["saddle_a"], d["tab_r"]], [des["temporal_a"], d["tab_r"]],
                 [des["mastoid_a"], d["tab_r"]], [des["cable_a"], d["tab_r"]]]
    if des.get("post_a") is not None:
        d["tabs"].append([des["post_a"], d["tab_r"]])
    d["has_post"] = des.get("post_a") is not None
    d["post_a"] = des.get("post_a") or 0.0
    es = screw("M2.5")
    d["eye_ins_hole"] = es["insert_hole"]; d["eye_ins_L"] = es["insert_L"]
    d["eye_boss_d"] = es["insert_od"] + 2 * insert_wall("M2.5")
    d["eye_boss_h"] = es["insert_L"] + 2.0
    d["arch_R"] = des.get("arch_R", 22.0); d["arch_phi"] = des.get("arch_phi", 35.0)
    d["arm_screw_clear"] = as_["d"] + 0.4; d["arm_head_d"] = as_["head_d"]
    ks = screw(des.get("anchor_screw") or des["arm_screw"])       # cable tab: anchor + clip screws
    d["anchor_screw_clear"] = ks["d"] + 0.4; d["anchor_head_d"] = ks["head_d"]
    d["anchor_ins_hole"] = ks["insert_hole"]; d["anchor_ins_L"] = ks["insert_L"]
    d["anchor_ins_pitch"] = max(7.0, ks["insert_od"] + 2.5)
    d["anchor_screw_grip"] = 4.0
    # ---------------- arms
    d["bar_r0"] = d["tab_r"] - d["tab_ins_pitch"] - des["slot_adj"] - 4.0
    d["bar_r1"] = d["tab_r"] + des["slot_adj"] + 4.0
    d["leg_r"] = d["bar_r1"] - des["leg_t"]
    d["saddle_r"] = des["saddle_r"]; d["pad_r"] = des["temporal_r"]      # temporal uses pad_r in CAD
    d["pad_screw_clear"] = ps["d"] + 0.4
    d["pad_nut_d"] = {"M2": 4.4, "M2.5": 5.4, "M3": 6.4, "M4": 8.1}[des["pad_screw"]]
    d["pad_nut_h"] = {"M2": 1.8, "M2.5": 2.2, "M3": 2.6, "M4": 3.4}[des["pad_screw"]]
    d["pad_skin_cover"] = 2.0
    d["eye_seat_d"] = 2 * (ps["d"] / 2 + des["wire_d"]) + 3.0
    d["eye_seat_h"] = min(1.5, des["wire_d"])
    d["cap_pin_clear"] = 2.4
    d["link_r"] = d["ring_od"] / 2 + 0.5 * (screw("M2.5")["insert_od"] + 2 * insert_wall("M2.5")) - 1.0   # eye boss centre on the ring rim (link_mode 'ring')
    # ---------------- module
    d["driver_mount_d"] = drv["mount_d"]; d["driver_rim_t"] = drv["rim_t"]
    d["driver_rear_d"] = drv["rear_d"]; d["driver_depth"] = drv["depth"]
    d["aperture_d"] = des.get("aperture_d_override") or drv["front_open"]
    d["seat_z"] = des["baffle_front_t"]
    d["baffle_h"] = (d["seat_z"] + des["driver_gasket_t"] - des["gasket_driver_squeeze"]
                     + drv["rim_t"] - des["clamp_depth"])
    d["cup_ri"] = max(drv["rear_d"] / 2 + 0.8, drv["mount_d"] / 2 - 3.5)
    d["cup_ro"] = drv["mount_d"] / 2 + des["driver_pocket_clr"] + des["cup_wall"]
    d["cup_h"] = des["clamp_depth"] + (drv["depth"] - drv["rim_t"]) + des["cup_h_extra"] + des["felt_t"] + des["cup_end_t"]
    d["vent_ring_r"] = 0.55 * d["cup_ri"]
    # rear felt disc (cut part, not printed): pushed over the link-eye boss, which stands inside the cup (CAD cup()).
    # Hole 0.5 mm under the boss diameter: the felt is compressed on the boss, so no air by-passes it there.
    cup_eye = des.get("link_mode") == "cup"
    d["felt_hole_d"] = d["eye_boss_d"] - 0.5 if cup_eye else 0.0
    c_eye = math.hypot(des.get("link_x") or 0.0, des.get("link_y") or 0.0)
    d["boss_in_bore_A"] = circle_overlap(d["cup_ri"], d["eye_boss_d"] / 2, c_eye) if cup_eye else 0.0   # mm2
    d["felt_A"] = math.pi * d["cup_ri"] ** 2 - (circle_overlap(d["cup_ri"], d["felt_hole_d"] / 2, c_eye) if cup_eye else 0.0)
    d["z_cuptop"] = des["standoff"] + d["z_mod0"] + d["baffle_h"] + d["cup_h"]
    # ---------------- pads
    d["seal_id"] = des["seal_id"]; d["seal_od"] = des["seal_od"]
    return d


def scad_value(v):
    if isinstance(v, str):
        return f'"{v}"'
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (list, tuple)):
        return "[" + ", ".join(scad_value(x) for x in v) + "]"
    return repr(round(float(v), 4))


SCAD_KEYS = """bore_d spig_d lug_h groove_rclr floor_t groove_h lip_t ring_od tabs tab_w tab_t tab_ins_pitch
tab_ins_hole tab_ins_L notch_extra lugs stop_a use_lock lock_clear lock_pilot twist gasket_umi_t gasket_squeeze
umi_mode foam_t foam_eps lug_ramp_c lug_ramp_L z_mod0
standoff saddle_skin_gap pad_h bar_r0 bar_r1 bar_t leg_r leg_t fillet_r saddle_r pad_r saddle_arm_w arm_w foot_t
foot_t_mastoid tab_r slot_adj arm_screw_clear pad_screw_clear eye_seat_h eye_seat_d cap_pin_clear saddle_cap_L
saddle_cap_wall saddle_strip_L pad_t_a pad_t_b pad_m_a pad_m_b pad_nut_d pad_nut_h pad_skin_cover pad_face_t lug_t baffle_h
aperture_d aperture_chamfer seat_z driver_mount_d driver_pocket_clr cup_screw_a cup_screw_r cup_ins_L cup_ins_hole
driver_gasket_t gasket_driver_squeeze driver_rim_t driver_rear_d driver_depth cup_ri cup_ro cup_h cup_end_t cup_boss_d
clamp_depth cup_screw_clear cup_csk_d felt_t felt_psa_w felt_hole_d rear_type grille_pitch grille_hole
vent_n vent_d vent_ring_r connector_size anchor_h clip_post_t clip_post_L arm_head_d anchor_screw_grip cable_od
clip_wall clip_interf clip_len clip_gap seal_od seal_id saddle_a temporal_a mastoid_a cable_a
has_post post_a post_r pad_p_a pad_p_b link_mode link_a link_r eye_ins_hole eye_ins_L eye_boss_d eye_boss_h
saddle_arch arch_R arch_phi saddle_liner_t link_x link_y serrated serr_p serr_h
anchor_screw_clear anchor_head_d anchor_ins_hole anchor_ins_L anchor_ins_pitch""".split()


def write_scad(d, path=None, header=""):
    path = path or os.path.join(CAD, "generated_params.scad")
    lines = ["// AUTO-GENERATED by calc/run_all.py — do not edit by hand.",
             "// Every value below is an output of the UMEH-2 engineering calculations",
             "// (see report/ENGINEERING_REPORT.md for the derivation of each one)."]
    if header:
        lines += ["// " + h for h in header.splitlines()]
    for k in SCAD_KEYS:
        lines.append(f"{k} = {scad_value(d[k])};")
    # mastoid pad radius handled by an extra variable used only in placement
    lines.append(f"mastoid_r = {scad_value(d['mastoid_r'])};")
    with open(path, "w") as fh:
        fh.write("\n".join(lines) + "\n")
    return path
