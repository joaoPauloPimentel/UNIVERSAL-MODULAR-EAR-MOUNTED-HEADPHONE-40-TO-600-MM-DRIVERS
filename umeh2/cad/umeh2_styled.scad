// =====================================================================
//  UMEH-2 — commercial finish layer (cosmetic parts only)
//
//  Adds non-structural trim over the calculated parts; it does NOT change
//  any load-bearing geometry (ring, arms, pads, saddle, baffle, cup, link).
//  The calculations in results/ were NOT re-run with these parts: their
//  mass is reported in docs/design_finish.md against the driver-mass margin.
//
//  cup_cap: 0.6 mm PETG shell bonded (PSA) on the cup outer end. Rounded
//  tri-lobe outline that hides the three cup-screw bosses, a 5 mm skirt
//  down the cup side, the grille holes repeated hole-for-hole (same open
//  pattern as the cup end) a clearance opening for the link eye and a channel for the link wire
//  (the wire keeps the calculated path and never touches the cap).
// =====================================================================
include <generated_params.scad>
use <umeh2.scad>
part = "cup_cap";
side = "R";
$fn = $preview ? 48 : 96;

cap_t = 0.6;          // top shell
cap_gap = 0.15;       // clearance to the cup / bosses
cap_skirt = 5.0;      // skirt height down the cup side
cap_round = 1.6;      // top edge round-over radius
wire_d = 2.5;         // occipital link wire (results/link.json, Final)

EYE_X = side == "L" ? -link_x : link_x;
function mx(a) = side == "L" ? 180 - a : a;
module polar(r, a) { rotate([0, 0, a]) translate([r, 0, 0]) children(); }

module outline(off) {         // tri-lobe outline around the cup and its screw bosses
    offset(r = off) hull() {
        circle(r = cup_ro);
        for (a = cup_screw_a) polar(cup_screw_r, a) circle(d = cup_boss_d);
    }
}
module grille_holes(h) {      // the cup's own grille pattern (umeh2.scad cup()), hole for hole
    p = grille_pitch;
    for (i = [-30:30], j = [-30:30]) {
        x = i * p + (j % 2) * p / 2; y = j * p * 0.866;
        if (sqrt(x * x + y * y) < cup_ri - grille_hole / 2 - 0.8 &&
            (link_mode != "cup" || sqrt((x - EYE_X) * (x - EYE_X) + (y - link_y) * (y - link_y)) > eye_boss_d / 2 + grille_hole / 2 + 0.8))
            translate([x, y, -1]) cylinder(d = grille_hole, h = h + 2, $fn = 6);
    }
}
// cap in the cup-end frame: z = 0 on the cup outer end face, +z away from the head
module cup_cap() {
    W = cap_gap + cap_t; R = cap_round; N = 8;
    difference() {
        union() {
            translate([0, 0, -cap_skirt]) linear_extrude(height = cap_skirt + cap_t - R) outline(W);
            for (k = [0:N - 1]) translate([0, 0, cap_t - R + R * k / N])     // round-over of the top edge
                linear_extrude(height = R / N + 0.001) outline(W - R + R * cos(asin((k + 1) / N)));
        }
        translate([0, 0, -cap_skirt - 1]) linear_extrude(height = cap_skirt + 1) outline(cap_gap);
        translate([0, 0, -0.01]) grille_holes(cap_t + 0.1);
        if (link_mode == "cup") translate([EYE_X, link_y, -1]) cylinder(d = eye_seat_d + 1.0, h = cap_t + 3);
        // wire channel: the link leaves the eye towards the module's rear edge (support.link_path), so the cap
        // keeps the wire where the calculation has it (1 mm above the cup end face) and never touches it
        if (link_mode == "cup") translate([EYE_X, link_y, -cap_skirt - 1]) rotate([0, 0, EYE_X < 0 ? 180 : 0])
            translate([0, -(wire_d + 1.0) / 2, 0]) cube([60, wire_d + 1.0, cap_skirt + cap_t + 3]);
        // shallow design groove following the outline
        translate([0, 0, cap_t - 0.25]) linear_extrude(1) difference() { outline(W - 2.4); outline(W - 2.8); }
    }
}
// front foam: reticulated (open-cell) PU foam disc on the module's head face, between the pinna and the driver.
// Acoustically near-transparent; covers the aperture and keeps dust and hair off the diaphragm. Bonded by a PSA
// ring outside the aperture chamfer. Thickness from the pinna-clearance chain (calc/umeh2/tolerance.py, chain 6):
// nominal 4.4 mm, Monte-Carlo -3 sigma 2.35 mm; 2 mm of foam leaves 2.4 mm nominal and 0.35 mm at -3 sigma, so the
// p95 ear does not reach it (below the 1 mm hair/earring rule at the low end: stated in docs/design_finish.md).
front_foam_t = 2.0;
module front_foam() { cylinder(r = spig_d / 2 - 0.5, h = front_foam_t, $fn = 128); }   // head side at z = 0

if (part == "cup_cap") cup_cap();
if (part == "front_foam") front_foam();
Z_CUPTOP = standoff + z_mod0 + baffle_h + cup_h;    // cup outer end in the skin frame (umeh2.scad placement)
if (part == "placed_cup_cap") translate([0, 0, Z_CUPTOP]) cup_cap();
if (part == "placed_front_foam") translate([0, 0, standoff + z_mod0 - front_foam_t]) front_foam();
// print orientation: top face on the bed, skirt up
if (part == "print") mirror([0, 0, 1]) translate([0, 0, -cap_t]) cup_cap();
