#!/usr/bin/env python3
"""
Bill of materials for one PAIR (left + right side), written from the design values and the CAD mass
properties in results/ (run after run_all.py). Writes BOM.csv and docs/bom_table.md.

Printed-part masses are the CAD-mesh masses (shell + infill model, calc/umeh2/massprops.py) [CAD];
hardware masses are typical catalogue values [DS]; nothing here is priced (prices are local: fill in).
Screw lengths are derived from the clamped stack and the insert depth (engagement window below).
"""
import csv, json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from umeh2 import design as dz, configs as cf, analysis as an, linkspring as ls
from umeh2.materials import SCREW, BRASS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
F = json.load(open(os.path.join(RES, "final_sizes.json")))
LK = json.load(open(os.path.join(RES, "link.json")))["Final"]["chosen"]
JT = json.load(open(os.path.join(RES, "joints.json")))
FINAL = cf.final_design()
FINAL["wire_d"] = LK["d_mm"]; FINAL["link_coils"] = LK["n_coil"]
des50, d50 = an.prepared(FINAL, 50)

ISO_LEN = {"M2": (4, 5, 6, 8, 10, 12, 16, 20), "M2.5": (4, 5, 6, 8, 10, 12, 16, 20, 25), "M3": (5, 6, 8, 10, 12, 16, 20, 25, 30)}


def screw_len(size, stack_mm, hole_mm, eng_min_mm):
    """Longest standard length whose thread engagement lies in [eng_min, hole depth - 0.3]; else the length
    to cut a longer screw to."""
    lo_, hi_ = stack_mm + eng_min_mm, stack_mm + hole_mm - 0.3
    ok = [L for L in ISO_LEN[size] if lo_ <= L <= hi_]
    if ok:
        return f"{size}x{max(ok)}", max(ok) - stack_mm
    L = next(L for L in ISO_LEN[size] if L > hi_)
    cut = math.floor(hi_ * 2) / 2
    return f"{size}x{L} cut to {cut:.1f} mm", cut - stack_mm


def part_mass(D, name):
    return next((p["m"] * 1e3 for p in F[str(D)]["parts"] if p["part"] == name), None)


rows = []
def add(item, qty, material, printed, source, mass_g, spec, tag):
    rows.append(dict(item=item, qty_per_pair=qty, material=material, printed=printed, source=source,
                     mass_each_g=(f"{mass_g:.2f}" if isinstance(mass_g, (int, float)) else (mass_g or "")), spec=spec, tag=tag))


# ------------------------------------------------------------------ printed: common cradle (identical for every driver)
add("Cradle ring (R and L)", 2, "PETG", "yes", "stl/common/ring_R.stl, ring_L.stl", part_mass(50, "ring"),
    f"ring OD {d50['ring_od']:.1f} mm, UMI-2 twist-lock groove, 5 tabs (tab radius {d50['tab_r']:.2f} mm); head face down; "
    "5 perimeters, 30 % gyroid", "CAD")
for a, lab in (("saddle", "Saddle arm (auricle-root arch)"), ("temporal", "Temporal arm"), ("mastoid", "Mastoid arm"),
               ("post", "Posterior-superior arm")):
    add(lab, 2, "PETG", "yes", f"stl/common/arm_{a}.stl", part_mass(50, f"arm_{a}"),
        f"bar {FINAL['bar_t']} / leg {FINAL['leg_t']} / foot {FINAL['foot_t'] if a != 'mastoid' else FINAL['foot_t_mastoid']} mm, "
        f"serrated clamp p {FINAL['serr_p']} mm; printed on its side; 5 perimeters, 40 % infill", "CAD")
add("Saddle cap", 2, "TPU 95A", "yes", "stl/common/saddle_cap.stl", part_mass(50, "saddle_cap"),
    "arched cap on the auricle root; flat, skin face down" + (
        f"; the bearing face is recessed {FINAL['saddle_liner_t']} mm for the cast liner" if FINAL.get("saddle_liner_t") else ""), "CAD")
if FINAL.get("saddle_liner_t"):
    add("Saddle liner (soft silicone, cast into the cap's bearing face)", 2,
        "skin-safe platinum silicone Shore 00-30 (100 % modulus ~69 kPa)", "no (cast)",
        "stl/common/cast_reference/saddle_liner.stl (mould reference)", part_mass(50, "saddle_liner"),
        f"{FINAL['saddle_liner_t']} mm, softens the auricle-root contact (root pressure <= 4 kPa at 55-60 mm, report §6); "
        "prime the TPU or key it mechanically; replace with the cap", "C")
for a in ("temporal", "mastoid", "post"):
    add(f"Pad, {a}", 2, "TPU 95A, 15 % gyroid", "yes", f"stl/common/pad_{a}.stl", part_mass(50, f"pad_{a}"),
        f"dome {des50['pad_' + a[0] + '_a']:.1f} x {des50['pad_' + a[0] + '_b']:.1f} mm, h {FINAL['pad_h']} mm, captive "
        f"{FINAL['pad_screw']} nut", "CAD")
add("Cable anchor", 2, "PETG", "yes", "stl/common/cable_anchor.stl", part_mass(50, "cable_anchor"),
    "holds the 2-pin socket; clip post; printed ON ITS SIDE (post bending in-layer)", "CAD")
add("Cable clip", 2, "TPU 95A", "yes", "stl/common/cable_clip.stl", part_mass(50, "cable_clip"),
    f"routing guide for a {FINAL['cable_od']} mm cable (interference {FINAL['clip_interf']} mm)", "CAD")
fs = JT.get("foam_spec", {})
add("UMI anti-rattle foam strips (3 per side)", 6, "PU foam, PSA backed", "no (die-cut)", "stl/common/gasket_umi.stl (cutting template)",
    part_mass(50, "gasket_umi"),
    f"{FINAL['foam_t']} mm sheet, CFD25 {fs.get('cfd25_spec', 0) / 1e3:.0f} kPa (window {fs.get('cfd25_lo', 0) / 1e3:.0f}-"
    f"{fs.get('cfd25_hi', 0) / 1e3:.0f} kPa), on the lug tops", "C")
add("Silicone pad facing, temporal + mastoid", 4, "platinum-cure silicone Shore 10-30A", "no (cast)",
    "stl/common/cast_reference/pad_face_*.stl (mould reference)", (part_mass(50, "pad_face_temporal") or 0),
    f"{FINAL['pad_face_t']} mm layer on the dome (static friction demand, report §9)", "C")
add("Seal pad (sealed-front option C, not in the default build)", 0, "TPU 95A, 15 % gyroid", "optional", "stl/common/seal_pad.stl", "",
    f"ring {FINAL['seal_id']}/{FINAL['seal_od']} mm; see report §16 (needs ~1 kPa on <= 30 kg/m3 foam to seal)", "C")

# ------------------------------------------------------------------ printed: driver modules (per size)
for D in dz.SIZES:
    dd = F[str(D)]["derived"]
    add(f"Baffle {D} mm", 2, "PETG", "yes", f"stl/module_{D}mm/baffle_{D}.stl", part_mass(D, "baffle"),
        f"aperture {dd['aperture_d']:.1f} mm, UMI-2 lugs; head face down", "CAD")
    add(f"Cup {D} mm (R and L: eye position)", 2, "PETG", "yes", f"stl/module_{D}mm/cup_{D}_R.stl, cup_{D}_L.stl", part_mass(D, "cup"),
        f"wall {FINAL['cup_wall']} mm, height {dd['cup_h']:.1f} mm, link eye at ({F[str(D)]['eye']['link_x']}, {F[str(D)]['eye']['link_y']}) mm",
        "CAD")
    add(f"Driver rim gasket {D} mm", 2, "TPU 95A", "yes", f"stl/module_{D}mm/gasket_driver_{D}.stl", part_mass(D, "gasket_driver"),
        f"{FINAL['driver_gasket_t']} mm, squeeze {FINAL['gasket_driver_squeeze']} mm", "CAD")
    add(f"Felt disc {D} mm", 2, "wool/polyester felt", "no", "die-cut", next((p["m"] * 1e3 for p in F[str(D)]["parts"] if p["part"] == "felt disc"), None),
        f"Ø{2 * dd['cup_ri']:.1f} x {FINAL['felt_t']} mm, hole Ø{dd['felt_hole_d']:.1f} at the link eye (pushed over the boss), "
        f"flow resistivity ~40 kPa s/m2 [A]", "C")
    add(f"Felt PSA rim {D} mm", 2, "acrylic PSA transfer tape", "no", "die-cut ring", None,
        f"OD {2 * dd['cup_ri']:.1f} / ID {2 * dd['cup_ri'] - 2 * FINAL['felt_psa_w']:.1f} mm; 90° peel on PETG >= 3 N/cm [A], mass < 0.02 g", "A")
    ln, eng = screw_len(FINAL["cup_screw"], dd["cup_h"], SCREW[FINAL["cup_screw"]]["insert_L"] + 1.0, 2.5)
    add(f"Cup screws {D} mm", 6, "A2 stainless", "no", "ISO 10642 countersunk", 0.55,
        f"{ln} (engagement {eng:.1f} mm in the baffle insert)", "C")
    add(f"Driver {D} mm", 2, "-", "no", "user supplied", dz.DRIVERS[D]["mass"],
        f"rim OD {dz.DRIVERS[D]['mount_d']} mm, depth {dz.DRIVERS[D]['depth']} mm (placeholder values [A]: measure and re-run)", "A")

# ------------------------------------------------------------------ hardware (common)
arm_ln, arm_eng = screw_len(FINAL["arm_screw"], FINAL["bar_t"] + 0.3, SCREW[FINAL["arm_screw"]]["insert_L"] + 0.3, 2.0)
anc_ln, anc_eng = screw_len(FINAL["anchor_screw"], 4.0 + 0.3, SCREW[FINAL["anchor_screw"]]["insert_L"] + 0.3, 2.5)
SCREW_G = {"M2": 0.35, "M2.5": 0.55, "M3": 0.95, "M4": 1.9}      # same unit masses as umeh2/massprops.py [DS]
INSERT_G = {"M2": 0.12, "M2.5": 0.20, "M3": 0.33, "M4": 0.60}
add("Arm screws", 16, "A2 stainless", "no", "ISO 7380 / ISO 4762", SCREW_G[FINAL["arm_screw"]],
    f"{arm_ln} (engagement {arm_eng:.1f} mm), torque {FINAL['arm_torque']} N m (torque driver); inserts {FINAL['arm_screw_pitch']} mm apart", "C")
add("Arm wave spring washers", 16, "spring steel", "no", "wave washer", 0.03,
    f"{FINAL['arm_screw']}: ID {SCREW[FINAL['arm_screw']]['d'] + 0.2:.1f}, OD <= {SCREW[FINAL['arm_screw']]['head_d'] + 0.5:.1f} mm, "
    f">= {FINAL['arm_washer'][0]:.0f} N flat load, rate <= {FINAL['arm_washer'][1] / 1e3:.0f} N/mm", "C")
add("Heat-set inserts, arm tabs", 16, "brass", "no", "knurled heat-set", INSERT_G[FINAL["arm_screw"]],
    f"{FINAL['arm_screw']}, OD {SCREW[FINAL['arm_screw']]['insert_od']} x {SCREW[FINAL['arm_screw']]['insert_L']} mm", "DS")
add("Cable anchor screws", 4, "A2 stainless", "no", "ISO 4762", SCREW_G[FINAL["anchor_screw"]],
    f"{anc_ln} (engagement {anc_eng:.1f} mm), torque {FINAL['anchor_torque']} N m, with a wave washer (next line)", "C")
add("Anchor wave spring washers", 4, "spring steel", "no", "wave washer", 0.04,
    f"{FINAL['anchor_screw']}: ID {SCREW[FINAL['anchor_screw']]['d'] + 0.2:.1f}, OD <= {SCREW[FINAL['anchor_screw']]['head_d'] + 0.5:.1f} mm, "
    f">= {FINAL['arm_washer'][0]:.0f} N flat load, rate <= {FINAL['arm_washer'][1] / 1e3:.0f} N/mm (same requirement as the arm joints)", "C")
add("Heat-set inserts, cable tab", 4, "brass", "no", "knurled heat-set", INSERT_G[FINAL["anchor_screw"]],
    f"{FINAL['anchor_screw']}, OD {SCREW[FINAL['anchor_screw']]['insert_od']} x {SCREW[FINAL['anchor_screw']]['insert_L']} mm", "DS")
add("Clip screw + nut", 2, "A2 stainless", "no", "ISO 4762 + ISO 4032", 1.23, f"{FINAL['anchor_screw']}x16", "DS")
add("Heat-set inserts, baffle (cup screws; per module pair)", 6, "brass", "no", "knurled heat-set", 0.20,
    f"{FINAL['cup_screw']}, OD {SCREW[FINAL['cup_screw']]['insert_od']} x {SCREW[FINAL['cup_screw']]['insert_L']} mm", "DS")
add("Pad screws + nuts", 6, "A2 stainless", "no", "ISO 7380 + ISO 4032", 0.72, f"{FINAL['pad_screw']}x10 (pad to arm foot)", "DS")
add("Saddle-cap pin", 2, "A2 stainless", "no", "M2x12 + nut", 0.45, "hinge pin of the saddle cap", "DS")
add("Link eye screw + insert + washer", 2, "A2 / brass", "no", "M2.5x8 ISO 7380 + heat-set M2.5", 0.85, "clamps the eye sleeve to the cup boss", "DS")
r_i = ls.eye_ri(FINAL["wire_d"]) * 1e3
add("Link eye sleeve", 2, "brass tube", "no", "cut", BRASS["rho"].v * 1e-6 * math.pi / 4 * ((2 * r_i) ** 2 - dz.EYE_SLEEVE_ID ** 2) * dz.EYE_SLEEVE_L,
    f"OD {2 * r_i:.1f} x ID {dz.EYE_SLEEVE_ID:g} x {dz.EYE_SLEEVE_L:g} mm (keeps the eye inner radius >= 1.5 d)", "C")
add("Occipital link wire", 1, "music wire ASTM A228", "no", "formed", LK["mass_g"],
    f"Ø{LK['d_mm']} mm, {LK['n_coil']} apex coils (mean Ø from linkspring.DC_COIL), length {LK['L'] * 1e3:.0f} mm + coils, "
    f"free half-gap {LK['free_half_gap'] * 1e3:.1f} mm", "C")
add("Link sleeve", 1, "silicone tube", "no", "tube", ls.link_sleeve_mass(LK["d_mm"], LK["L"]),
    f"ID {LK['d_mm']:g} mm (= wire), {ls.SLEEVE_WALL * 1e3:g} mm wall, {ls.SLEEVE_COVER * LK['L'] * 1e3:.0f} mm "
    f"({100 * ls.SLEEVE_COVER:g} % of the arc; the eye bends and the apex coil bare): skin and hair contact", "A")
add("2-pin 0.78 mm socket + JST pigtail", 2, "-", "no", "catalogue", 2.0, "in the cable anchor", "A")

os.makedirs(os.path.join(ROOT, "docs"), exist_ok=True)
with open(os.path.join(ROOT, "BOM.csv"), "w", newline="") as fh:
    wr = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
    wr.writeheader(); wr.writerows(rows)
with open(os.path.join(ROOT, "docs", "bom_table.md"), "w") as fh:
    fh.write("# UMEH-2 bill of materials (one pair)\n\nGenerated by `calc/bom.py` from the design values and the CAD masses. "
             "Tags: CAD mesh mass, C calculated, DS datasheet/typical, A assumption. No prices (local).\n\n")
    fh.write("| " + " | ".join(rows[0].keys()) + " |\n|" + "---|" * len(rows[0]) + "\n")
    for r in rows:
        fh.write("| " + " | ".join(str(v) for v in r.values()) + " |\n")
print("BOM rows", len(rows))
