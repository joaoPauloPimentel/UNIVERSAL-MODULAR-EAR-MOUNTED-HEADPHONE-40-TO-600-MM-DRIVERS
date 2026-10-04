// UMEH-3 wire forming aids (user 2026-10-04: "a housing for the steel wire so it is easier to bend it the right way").
// All printed in PETG, flat on the bed, no supports. Music wire springs back after bending, so these are CHECK forms:
// bend by hand / with pliers, over-bend a little, and keep correcting until the wire drops into the form all along.
//   gabarito_gancho  3-D cradle for the ear-hook wire (1.6 mm), side R or L: from the straight part that goes through
//                    the bushing, down the descent, round the arch, down the leg to the tip. The wire drops in from above.
//   chave_trava      key for the lock bend after the wire is through the bushing: rests on the boss, the wire is bent
//                    over its top (crank height) and over its end (crank length 12 mm); the tab hole cuts the pin to 7 mm.
//   gabarito_faixa   board with the FREE shape of the neckband wire (1.8 mm), both halves; free = 2 N when worn on a
//                    150 mm wide head (calc/studies/band_free_shape.py). Eye pins drop into the holes at the ends.
include <params3.scad>
include <params_jig.scad>
part = "gabarito_gancho";
side = "R";
CL = 0.5;                          // channel clearance on the wire diameter
$fn = 24;

module sided() { if (side == "L") mirror([1, 0, 0]) children(); else children(); }
function unit(v) = v / norm(v);
U = unit([HH[0] - PC[0], HH[1] - PC[1]]);               // from the cup centre out through the hook boss
I0 = 5;                                                 // HOOK index: wire in the middle of the bushing

// ------------------------------------------------------------------ hook cradle
module hook_channel() {
    for (i = [I0 : len(HOOK) - 2]) hull() for (p = [HOOK[i], HOOK[i + 1]]) {
        translate(p) sphere(d = WIRE_D + CL, $fn = 16);
        translate(p + [0, 0, 60]) sphere(d = WIRE_D + CL, $fn = 16);
    }
}
module gabarito_gancho() {
    zb = 0.0;
    difference() {
        union() {
            // base plate under the arch and leg (2 mm), rounded
            translate([0, 0, zb]) linear_extrude(2) offset(r = 6) hull() for (i = [I0 + 3 : len(HOOK) - 1]) translate([HOOK[i][0], HOOK[i][1]]) circle(r = 1);
            // supports up to the wire centre line
            for (i = [I0 + 2 : len(HOOK) - 2]) hull() for (p = [HOOK[i], HOOK[i + 1]])
                translate([p[0], p[1], zb]) cylinder(d = 7, h = p[2] - zb);
            // column beside the straight part (on the outer side, away from the arch); the wire lies in its groove
            translate([HH[0] + 2.6 * U[0], HH[1] + 2.6 * U[1], zb]) cylinder(d = 6.4, h = HOOK[I0][2] - zb);
            hull() {
                translate([HH[0] + 2.6 * U[0], HH[1] + 2.6 * U[1], zb]) cylinder(d = 6.4, h = 2);
                translate([HOOK[I0 + 4][0], HOOK[I0 + 4][1], zb]) cylinder(d = 7, h = 2);
            }
        }
        hook_channel();
        // labels on the base
        m = side == "L" ? 1 : 0;                       // the side mirror flips the labels back
        translate([-3, -8, 1.4]) mirror([m, 0, 0]) linear_extrude(1) text(side, size = 7, halign = "center", font = "Liberation Sans:style=Bold");
        translate([-3, 3, 1.4]) mirror([m, 0, 0]) linear_extrude(1) text("1,6", size = 4, halign = "center", font = "Liberation Sans");
    }
}

// ------------------------------------------------------------------ lock bend key
// the wire's crank sits 5.5 mm above the boss top and runs 12 mm out to the pin; the key's outer part is raised to clear
// the lock wall (from Z_F + PLATE_T, BOSS_L tall: its top is PLATE_T above the boss top)
module chave_trava() {
    zc = HOOK[3][2] - (Z_F + BOSS_L);                   // crank centre above the boss top (5.5)
    h0 = zc - WIRE_D / 2;                               // key top = bottom of the crank
    lift = (Z_F + PLATE_T + BOSS_L) - (Z_F + BOSS_L) + 0.4;   // clear the lock wall top
    L = LOCK[0] - WIRE_D / 2;                           // end face: the pin's inner side
    difference() {
        union() {
            hull() { translate([-3.5, -3, 0]) cube([1, 6, h0]); translate([5.5, -3, 0]) cube([1, 6, h0]); }
            translate([5.5, -3, lift]) cube([L - 5.5, 6, h0 - lift]);
            // cut tab: the pin goes through, the crank rests on the top, cut flush underneath -> 7 mm pin
            translate([-3.5 - 9, -4, 0]) cube([9, 8, 7 - WIRE_D / 2]);
        }
        // slot for the wire (open to the side so the key comes off after the bend)
        hull() { cylinder(d = WIRE_D + 0.3, h = 30, center = true); translate([0, -10, 0]) cylinder(d = WIRE_D + 0.3, h = 30, center = true); }
        translate([0, 0, h0]) rotate([0, 90, 0]) cylinder(d = WIRE_D + 0.2, h = L + 1);       // groove on top for the crank
        translate([-3.5 - 4.5, 0, -1]) cylinder(d = WIRE_D + 0.3, h = 20);                   // cut-tab hole
        translate([-3.5 - 4.5, -2.6, 7 - WIRE_D / 2 - 0.6]) linear_extrude(1) text("7", size = 2.6, halign = "center", valign = "center", font = "Liberation Sans:style=Bold");
    }
}

// ------------------------------------------------------------------ neckband board
module band_curve(d) {
    pts = concat([for (i = [len(BAND_FREE) - 1 : -1 : 1]) [-BAND_FREE[i][0], BAND_FREE[i][1]]], BAND_FREE);
    for (i = [0 : len(pts) - 2]) hull() { translate(pts[i]) circle(d = d); translate(pts[i + 1]) circle(d = d); }
}
module gabarito_faixa() {
    e = BAND_FREE[len(BAND_FREE) - 1];
    T = 4;
    difference() {
        union() {
            linear_extrude(T) band_curve(14);
            translate([-e[0] - 6, 4, 0]) cube([2 * e[0] + 12, 8, T]);                      // bar between the eyes
            for (s = [-1, 1]) translate([s * e[0] - 7, -6, 0]) cube([14, 16, T]);
        }
        translate([0, 0, T - 1.6]) linear_extrude(5) band_curve(NECK_D + CL);              // groove: wire half sunk
        for (s = [-1, 1]) translate([s * e[0], e[1], -1]) cylinder(d = NECK_D + 0.4, h = T + 2);   // eye pins
        translate([0, BAND_FREE[0][1] + 3.5, T - 0.6]) linear_extrude(1) text("|", size = 4, halign = "center", valign = "center");
        translate([0, 8, T - 0.6]) linear_extrude(1) text("faixa 1,8 mm - forma solta (2 N)", size = 4.5, halign = "center", valign = "center", font = "Liberation Sans");
    }
}

if (part == "gabarito_gancho") sided() gabarito_gancho();
if (part == "chave_trava") chave_trava();
if (part == "gabarito_faixa") gabarito_faixa();
if (part == "preview_gancho") sided() { color("#8E9096") gabarito_gancho(); color("Silver") for (i = [I0 : len(HOOK) - 2]) hull() { translate(HOOK[i]) sphere(d = WIRE_D, $fn = 12); translate(HOOK[i + 1]) sphere(d = WIRE_D, $fn = 12); } }
if (part == "preview_faixa") { color("#8E9096") gabarito_faixa(); color("Silver") translate([0, 0, 4 - 1.6 + NECK_D / 2 - 0.2]) linear_extrude(NECK_D) band_curve(NECK_D); }
