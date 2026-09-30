// =====================================================================
//  UMEH-2 — Modular ear-mounted headphone, 40–60 mm drivers
//
//  ALL dimensions come from generated_params.scad, which is WRITTEN BY
//  calc/run_all.py from the engineering calculations. Do not edit
//  dimensions here; change the design inputs in calc/umeh2/design.py
//  and re-run the calculation, which rewrites the parameter file and
//  re-exports every STL.
//
//  Frame: origin on the ear-canal axis in the skin plane, x forward,
//  y up, z lateral (away from the head). Right side; "L" mirrors x.
//
//  part = "ring" | "arm_saddle" | "arm_temporal" | "arm_mastoid" |
//         "saddle_cap" | "saddle_liner" (cast) | "pad_temporal" | "pad_mastoid" | "gasket_umi" |
//         "baffle" | "gasket_driver" | "cup" |
//         "cable_anchor" | "cable_clip" | "seal_pad" |
//         "placed_<part>" (same part in assembled position, for mass
//         properties) | "assembly"
// =====================================================================
include <generated_params.scad>

part = "assembly";
side = "R";
$fn = $preview ? 48 : 96;

function mx(a) = side == "L" ? 180 - a : a;
module polar(r, a) { rotate([0, 0, a]) translate([r, 0, 0]) children(); }
module ring(ro, ri, h) { difference() { cylinder(r = ro, h = h); translate([0, 0, -1]) cylinder(r = ri, h = h + 2); } }
module sector(r, a0, a1, h) {
    n = max(3, ceil((a1 - a0) / 3));
    linear_extrude(h) polygon(concat([[0, 0]], [for (i = [0:n]) let(a = a0 + (a1 - a0) * i / n) [r * cos(a), r * sin(a)]]));
}
module fillet2d(r) { difference() { square([r, r]); translate([r, r]) circle(r = r, $fn = 48); } }

// ------------------------------------------------------------- derived
R_B    = bore_d / 2;                 // female bore radius
R_S    = spig_d / 2;                 // male spigot radius
R_L    = R_S + lug_h;                // lug outer radius
R_G    = R_L + groove_rclr;          // groove radius
Z_G0   = floor_t;                    // groove floor (head side)
Z_G1   = floor_t + groove_h;         // lip underside at R_G
Z_CONE = R_G - R_B;                  // 45° cone rise
H_RING = Z_G1 + Z_CONE + lip_t;      // ring height
Z_MOD0 = z_mod0;                     // module head face (lug bottom) in ring frame (calc: design.derived)
GAPV   = sqrt(2) * foam_t * (1 - foam_eps);          // compressed foam, vertical gap between the 45° cones
EYE_X  = side == "L" ? -link_x : link_x;              // link eye on the cup end (Final design)

// ================================================================ RING
// Printed head-face down: groove floor is a flat top surface, the lip
// underside is a 45° cone (self-supporting), no supports anywhere.
module lug_sectors(extra, h, z0 = -1) {
    for (l = lugs) translate([0, 0, z0]) sector(R_G + 5, l[0] - (l[1] + extra) / 2, l[0] + (l[1] + extra) / 2, h);
}
module ring_body() {
    difference() {
        union() {
            cylinder(r = ring_od / 2, h = H_RING);
            // tab: round end centred on the outer insert (t[1]), so the outer insert keeps a tab_w/2 - insert_od/2
            // wall on its outboard side and the screw head + washer bear fully on the tab
            for (t = tabs) rotate([0, 0, mx(t[0])]) hull() {
                translate([ring_od / 2 - 6, -tab_w / 2, 0]) cube([1, tab_w, tab_t]);
                translate([t[1], 0, 0]) cylinder(d = tab_w, h = tab_t);
            }
            if (link_mode == "ring") rotate([0, 0, mx(link_a)]) hull() {
                translate([ring_od / 2 - 6, -eye_boss_d / 2, 0]) cube([1, eye_boss_d, eye_boss_h]);
                translate([link_r, 0, 0]) cylinder(d = eye_boss_d, h = eye_boss_h);
            }
        }
        // bore
        translate([0, 0, -1]) cylinder(r = R_B, h = H_RING + 2);
        // matching serration grooves under every arm tab (printed on the bed face: plain 0.7 mm deep grooves)
        if (serrated) for (t = tabs) rotate([0, 0, mx(t[0])]) intersection() {
            translate([ring_od / 2 - 0.5, -tab_w, -1]) cube([t[1] + tab_w, 2 * tab_w, serr_h + 1.1]);
            rotate([90, 0, 0]) linear_extrude(height = saddle_arm_w + 1, center = true)
                for (k = [ceil(bar_r0 / serr_p) - 1 : floor(bar_r1 / serr_p) + 1])
                    polygon([[k * serr_p - 0.05, -1], [k * serr_p - 0.05, 0], [k * serr_p + serr_p / 2, serr_h + 0.1], [(k + 1) * serr_p + 0.05, 0], [(k + 1) * serr_p + 0.05, -1]]);
        }
        // groove + 45° lip underside
        rotate_extrude($fn = 128) polygon([[R_B - 0.01, Z_G0], [R_G, Z_G0], [R_G, Z_G1], [R_B - 0.01, Z_G1 + Z_CONE]]);
        // lug entry notches through the lip
        intersection() { cylinder(r = R_G, h = H_RING + 2); lug_sectors(notch_extra, H_RING + 2, Z_G0); }
        // rotation stop: leave material (handled below by union)
        // tab inserts (from head side)
        // (the cable tab carries the anchor: its own screw size and pitch, see extras.anchor_screws)
        for (t = tabs) let(ca = (t[0] == cable_a)) rotate([0, 0, mx(t[0])])
            for (r = [t[1] - (ca ? anchor_ins_pitch : tab_ins_pitch), t[1]])
                translate([r, 0, -0.01]) cylinder(d = ca ? anchor_ins_hole : tab_ins_hole,
                                                  h = (ca ? anchor_ins_L : tab_ins_L) + 0.3, $fn = 24);
        // link-eye insert (from the head side; eye + bushing clamped under an M2.5 screw)
        if (link_mode == "ring") rotate([0, 0, mx(link_a)]) translate([link_r, 0, -0.01])
            cylinder(d = eye_ins_hole, h = eye_ins_L + 0.3, $fn = 24);
        // lock-screw clearance (optional M2 lock through ring into lug)
        if (use_lock) polar(R_S + lug_h / 2, twist) translate([0, 0, -1]) cylinder(d = lock_clear, h = floor_t + 2, $fn = 16);
        // L/R emboss
        translate([0, -(ring_od / 2 - 4), -0.01]) mirror([1, 0, 0]) linear_extrude(0.5) text(side, size = 4, halign = "center", valign = "center");
    }
    // rotation stop block in the groove
    intersection() {
        rotate_extrude($fn = 128) polygon([[R_B, Z_G0], [R_G, Z_G0], [R_G, Z_G1], [R_B, Z_G1 + Z_CONE]]);
        translate([0, 0, Z_G0]) sector(R_G + 1, stop_a[0], stop_a[1], groove_h + Z_CONE);
    }
    // detent bump (TPU gasket rides over it: tactile lock position)
}
// UMI axial element. "gasket" (Design A/B): TPU 95A flat ring on the groove floor.
// "foam" (Final): lugs bear on the rigid floor; one die-cut PU-foam strip (PSA backed) on each
// lug top, covering the lead-in ramps. part "gasket_umi" = flat die-cut template of the 3 strips.
FOAM_W = (R_L - R_B) * sqrt(2) - 0.3;                // slant width of the lug/lip overlap band
FOAM_RM = (R_L + R_B) / 2;
module gasket_umi() {
    if (umi_mode == "foam") {
        for (i = [0:2]) translate([0, i * (FOAM_W + 3), 0]) cube([lugs[i][1] * PI / 180 * FOAM_RM, FOAM_W, foam_t]);
    } else difference() {
        ring(R_G - 0.4, R_B + 0.4, gasket_umi_t);
        translate([0, 0, 0]) sector(R_G, stop_a[0] - 1, stop_a[1] + 1, gasket_umi_t + 1);
    }
}
module umi_foam_placed() {   // compressed foam strips on the lug tops, ring frame (mass properties)
    intersection() {
        rotate_extrude($fn = 128) polygon([[R_B, Z_G0 + lug_t + (R_L - R_B)], [R_L, Z_G0 + lug_t],
                                           [R_L, Z_G0 + lug_t + GAPV], [R_B, Z_G0 + lug_t + (R_L - R_B) + GAPV]]);
        lug_sectors(0, 30, Z_G0 - 1);
    }
}

// ================================================================ ARMS
// Profile in the (r, z) plane, extruded tangentially; printed lying on
// its side so every bending stress is in-layer (see report §8).
module arm_profile(r_tip, mode, ft) {
    S  = standoff;
    fb = mode == "saddle" ? -S + saddle_skin_gap : -S + pad_h;
    union() {
        translate([bar_r0, -bar_t]) square([bar_r1 - bar_r0, bar_t]);
        translate([leg_r, fb]) square([leg_t, -bar_t - fb]);
        translate([r_tip - ft / 2, fb]) square([leg_r + leg_t - r_tip + ft / 2, ft]);
        translate([leg_r, -bar_t]) mirror([1, 0]) mirror([0, 1]) fillet2d(fillet_r);
        translate([leg_r, fb + ft]) mirror([1, 0]) fillet2d(fillet_r);
        translate([r_tip - ft / 2, fb + ft / 2]) circle(d = ft, $fn = 32);
        // serrations on the clamp face (Final): radial position is held by teeth, not by friction
        if (serrated) for (k = [ceil(bar_r0 / serr_p) : floor(bar_r1 / serr_p) - 1])
            polygon([[k * serr_p, -0.01], [k * serr_p + serr_p / 2, serr_h], [(k + 1) * serr_p, -0.01]]);
    }
}
module arm(mode) {
    r_tip = mode == "saddle" ? saddle_r : (mode == "mastoid" ? mastoid_r : (mode == "post" ? post_r : pad_r));
    w     = mode == "saddle" ? saddle_arm_w : arm_w;
    ft    = mode == "mastoid" ? foot_t_mastoid : foot_t;
    S     = standoff;
    fb    = mode == "saddle" ? -S + saddle_skin_gap : -S + pad_h;
    difference() {
        translate([0, 0, -w / 2]) linear_extrude(w) arm_profile(r_tip, mode, ft);
        for (r = [tab_r - tab_ins_pitch, tab_r]) hull() for (dr = [-slot_adj, slot_adj])
            translate([r + dr, 0, 0]) rotate([90, 0, 0]) cylinder(d = arm_screw_clear, h = 40, center = true, $fn = 24);
        if (mode == "temporal" || mode == "mastoid" || mode == "post")
            translate([r_tip, fb - 1, 0]) rotate([-90, 0, 0]) cylinder(d = pad_screw_clear, h = ft + 2, $fn = 32);
        if (mode == "mastoid" && link_mode == "mastoid") {
            translate([r_tip, fb + ft - eye_seat_h, 0]) rotate([-90, 0, 0]) cylinder(d = eye_seat_d, h = eye_seat_h + 1, $fn = 32);
        }
        if (mode == "saddle")
            translate([r_tip + 2, fb + ft / 2, 0]) cylinder(d = cap_pin_clear, h = w + 2, center = true, $fn = 24);
    }
}

// ================================================================ TPU contacts
// cross-section of the arched bearing bar (local: x radial from the bar centreline, y lateral); the skin-side
// (bearing) face is x = -8, i.e. radius arch_R about the arch centre
module bar_section(H) { hull() { translate([-8, 0]) square([16, H - 4]); translate([-6, H - 4]) square([12, 4]); } }
module bar_arc() {       // places a 2-D section of the bar along the arch (same frame as saddle_cap())
    translate([-15 - arch_R, 0, -saddle_cap_wall]) rotate([0, 0, -(arch_phi + 14)])
        rotate_extrude(angle = 2 * (arch_phi + 14), $fn = 96) translate([arch_R + 8, 0]) children();
}
module saddle_cap() {
    // Printed FLAT (skin/scalp face on the bed, local z up): the arched bar lies in the
    // bed plane (no overhang) and the sleeve is an open-top U-channel (no bridging);
    // the M2 pin through the arm retains it.
    L = saddle_cap_L; wall = saddle_cap_wall; ft = foot_t; w = saddle_arm_w; SL = saddle_strip_L;
    H = ft + 2 * wall;
    difference() {
        union() {
            if (saddle_arch) {
                // bearing bar curved to the auricle-root arch: bearing radius = arch_R. With a liner the TPU bar
                // stops saddle_liner_t short of it and the cast silicone (saddle_liner()) makes up the skin face.
                bar_arc() intersection() { bar_section(H); translate([saddle_liner_t, 0]) bar_section(H); }
                translate([-8, -10, -wall]) cube([16, 20, H]);
            } else {
                hull() {
                    translate([-6, -L / 2, -wall]) cube([14, L, H]);
                    translate([-8, 0, ft / 2]) rotate([90, 0, 0]) scale([1, H / 16, 1]) cylinder(d = 16, h = L - 8, center = true);
                }
            }
            translate([0, -w / 2 - wall, -wall]) cube([SL, w + 2 * wall, H]);
        }
        // open-top sleeve for the arm foot
        translate([-4, -w / 2 - 0.2, -0.2]) cube([SL + 6, w + 0.4, H]);
        translate([2, 0, ft / 2]) rotate([90, 0, 0]) cylinder(d = cap_pin_clear, h = L + 60, center = true, $fn = 24);
    }
}
// soft silicone liner (Shore 00-30, cast into the cap's bearing face): the band of the bar section within
// saddle_liner_t of the bearing face (support.liner_compliance: it softens the auricle-root contact)
module saddle_liner() {
    H = foot_t + 2 * saddle_cap_wall;
    if (saddle_arch && saddle_liner_t > 0)
        bar_arc() difference() { bar_section(H); translate([saddle_liner_t, 0]) bar_section(H); }
}
// Both pads: flat base (on the bed, against the foot), dome toward the skin,
// captive nut in the base, retained by a screw through the foot.
// half-ellipsoid dome, semi-axes pa/2, pb/2, h
module dome(pa, pb, h) { scale([1, pb / pa, h / (pa / 2)]) sphere(d = pa, $fn = 64); }
// faced = true: the TPU core is the dome shrunk by pad_face_t, the silicone facing (pad_face_*) makes up
// the outer pad_face_t, so the skin-side shape is unchanged (support.contact_set: silicone/dry-skin friction)
module pad_generic(pa, pb, faced = false) {
    t = faced ? pad_face_t : 0;
    difference() {
        dome(pa - 2 * t, pb - 2 * t, pad_h - t);
        translate([0, 0, -0.01]) cylinder(d = pad_nut_d, h = pad_nut_h, $fn = 6);
        translate([0, 0, -1]) cylinder(d = pad_screw_clear, h = pad_h - pad_skin_cover + 1, $fn = 24);
        translate([-60, -60, -60]) cube([120, 120, 60]);
    }
}
module pad_face_generic(pa, pb) {       // cast silicone cap, pad_face_t thick, over the TPU core
    difference() {
        dome(pa, pb, pad_h);
        translate([0, 0, -0.01]) dome(pa - 2 * pad_face_t, pb - 2 * pad_face_t, pad_h - pad_face_t + 0.01);
        translate([-60, -60, -60]) cube([120, 120, 60]);
    }
}
module pad_temporal() { pad_generic(pad_t_a, pad_t_b, pad_face_t > 0); }
module pad_mastoid()  { pad_generic(pad_m_a, pad_m_b, pad_face_t > 0); }
module pad_post()     { pad_generic(pad_p_a, pad_p_b); }
module pad_face_temporal() { pad_face_generic(pad_t_a, pad_t_b); }
module pad_face_mastoid()  { pad_face_generic(pad_m_a, pad_m_b); }

// ================================================================ MODULE
// Baffle: printed head-face down. Lugs sit on the bed (flat bearing face
// on the gasket), their outward face is the 45° cone that mates the lip.
// Lead-in ramp at a lug end (calc: structure.twistlock): the 45° top cone is lowered by lug_ramp_c at the
// end face and rises back to full height over lug_ramp_L, so turning the module cams the foam into
// compression. Local frame: x radial, y tangential INTO the lug; the plane follows the cone
// z = lug_t + (R_L - r), with r = sqrt(x^2 + y^2) ~ x + y^2/(2x) (correction at y = L).
module lug_ramp_cutter(a_end, into_positive) {
    L = lug_ramp_L; c = lug_ramp_c;
    rotate([0, 0, a_end]) mirror([0, into_positive ? 0 : 1, 0])
        hull() for (x = [R_S - 1.0, R_L + 0.6]) {
            translate([x, -0.02, lug_t + (R_L - x) - c]) cube(0.01);
            translate([x, L, lug_t + (R_L - x) - L * L / (2 * x) + 0.02]) cube(0.01);
            translate([x, -0.02, lug_t + (R_L - x) + 6]) cube(0.01);
            translate([x, L, lug_t + (R_L - x) + 6]) cube(0.01);
        }
}
module lugs3d() {
    difference() {
        intersection() {
            rotate_extrude($fn = 128) polygon([[R_S - 0.5, 0], [R_L, 0], [R_L, lug_t], [R_S - 0.5, lug_t + (R_L - R_S + 0.5)]]);
            lug_sectors(0, lug_t + lug_h + 2, -0.5);
        }
        if (lug_ramp_c > 0) for (l = lugs) {
            lug_ramp_cutter(l[0] - l[1] / 2, true);      // lower end: lug lies at larger angles
            lug_ramp_cutter(l[0] + l[1] / 2, false);     // upper end: lug lies at smaller angles
        }
    }
}
module baffle() {
    difference() {
        union() {
            cylinder(r = R_S, h = baffle_h);
            lugs3d();
        }
        // aperture with front chamfer (acoustic, see report §18)
        translate([0, 0, -1]) cylinder(r = aperture_d / 2, h = baffle_h + 2);
        translate([0, 0, -0.01]) cylinder(r1 = aperture_d / 2 + aperture_chamfer, r2 = aperture_d / 2, h = aperture_chamfer);
        // driver pocket from the outer side
        translate([0, 0, seat_z]) cylinder(r = driver_mount_d / 2 + driver_pocket_clr, h = baffle_h);
        // cup-screw inserts in the rim, from the outer face
        for (a = cup_screw_a) polar(cup_screw_r, a) translate([0, 0, baffle_h - cup_ins_L - 0.3]) cylinder(d = cup_ins_hole, h = cup_ins_L + 1, $fn = 24);
        // lead exit groove for driver wires (to the JST pigtail)
        rotate([0, 0, 270]) translate([driver_mount_d / 2 - 1, -1.6, seat_z - 1.5]) cube([R_S, 3.2, baffle_h]);
        // lock screw pilot in the wide lug (self-tapping into PETG), if used
        if (use_lock) polar(R_S + lug_h / 2, 0) translate([0, 0, -1]) cylinder(d = lock_pilot, h = lug_t, $fn = 16);
    }
}
module gasket_driver() { ring(driver_mount_d / 2 + driver_pocket_clr - 0.1, aperture_d / 2 + 0.3, driver_gasket_t); }

// Rear cup: printed outer end down (grille/vents on the bed). Its rim
// clamps the driver rim; screw bosses run full height.
module cup() {
    Ri = cup_ri; Ro = cup_ro; H = cup_h;
    difference() {
        union() {
            difference() {
                union() {
                    cylinder(r = Ro, h = H);
                    for (a = cup_screw_a) polar(cup_screw_r, a) cylinder(d = cup_boss_d, h = H, $fn = 32);
                    for (a = cup_screw_a) rotate([0, 0, a]) translate([Ro - 1, -cup_boss_d / 4, 0]) cube([cup_screw_r - Ro + 1, cup_boss_d / 2, H]);
                }
                translate([0, 0, cup_end_t]) cylinder(r = Ri, h = H);
                // rim step that clamps the driver rim (rim sits inside Ro)
                translate([0, 0, H - clamp_depth]) cylinder(r = driver_mount_d / 2 + driver_pocket_clr, h = clamp_depth + 1);
                for (a = cup_screw_a) polar(cup_screw_r, a) {
                    translate([0, 0, -1]) cylinder(d = cup_screw_clear, h = H + 2, $fn = 24);
                    translate([0, 0, -0.01]) cylinder(d1 = cup_csk_d, d2 = cup_screw_clear, h = (cup_csk_d - cup_screw_clear) / 2, $fn = 24);
                }
                if (rear_type == "open") {
                    p = grille_pitch;
                    for (i = [-30:30], j = [-30:30]) {
                        x = i * p + (j % 2) * p / 2; y = j * p * 0.866;
                        if (sqrt(x * x + y * y) < Ri - grille_hole / 2 - 0.8 &&
                            (link_mode != "cup" || sqrt((x - EYE_X) * (x - EYE_X) + (y - link_y) * (y - link_y)) > eye_boss_d / 2 + grille_hole / 2 + 0.8))
                            translate([x, y, -1]) cylinder(d = grille_hole, h = cup_end_t + 2, $fn = 6);
                    }
                }
                if (rear_type == "vented") for (i = [0:vent_n - 1])
                    polar(vent_ring_r, 90 + i * 360 / vent_n) translate([0, 0, -1]) cylinder(d = vent_d, h = cup_end_t + 2, $fn = 24);
                // lead pass-through notch at the rim
                rotate([0, 0, 270]) translate([Ri - 1, -1.6, H - clamp_depth - 2]) cube([Ro - Ri + 3, 3.2, 3]);
            }
            // link-eye boss (Final design): the occipital link is clamped on the cup end at (link_x, link_y). The boss
            // stands on the INSIDE of the cup end (added after the bore is cut) so the heat-set insert has its full
            // length in solid material; the felt disc is pushed over it (hole felt_hole_d, calc: design.derived).
            if (link_mode == "cup") translate([EYE_X, link_y, 0]) cylinder(d = eye_boss_d, h = cup_end_t + eye_ins_L + 1.0, $fn = 32);
        }
        if (link_mode == "cup") translate([EYE_X, link_y, -0.01]) cylinder(d = eye_ins_hole, h = eye_ins_L + 0.3, $fn = 24);
    }
}
// The rear felt disc is a cut part (not printed): outer diameter 2 cup_ri, hole felt_hole_d pushed over the eye
// boss, bonded to the inside of the cup end by an acrylic PSA rim felt_psa_w wide outside the grille
// (calc: extras.felt_bond). It replaces the press-fit retainer ring of the earlier iteration, which would clash with
// the eye boss and, as a PETG ring, exceeded its sustained hoop strength at the upper interference tolerance.

// ================================================================ CABLE
module cable_anchor() {
    c = connector_size;
    difference() {
        union() {
            translate([bar_r0, -tab_w / 2, -anchor_h]) cube([bar_r1 - bar_r0, tab_w, anchor_h]);
            translate([bar_r1 - clip_post_t, -tab_w / 2, -clip_post_L]) cube([clip_post_t, tab_w, clip_post_L]);
        }
        for (r = [tab_r - anchor_ins_pitch, tab_r]) translate([r, 0, -anchor_h - 1]) cylinder(d = anchor_screw_clear, h = anchor_h + 2, $fn = 24);
        for (r = [tab_r - anchor_ins_pitch, tab_r]) translate([r, 0, -anchor_h - 1]) cylinder(d = anchor_head_d + 0.6, h = anchor_h - anchor_screw_grip + 1, $fn = 24);
        translate([bar_r1 - clip_post_t - c[1] - 1, -c[0] / 2, -anchor_h - 0.01]) cube([c[1], c[0], c[2]]);
        translate([bar_r0 - 1, -1.5, -3.5]) cube([bar_r1 - bar_r0 - clip_post_t, 3, 2.5]);
        translate([bar_r1 - clip_post_t - 2, 0, -clip_post_L + 5]) rotate([0, 90, 0]) cylinder(d = anchor_screw_clear, h = 20, $fn = 24);
    }
}
module cable_clip() {
    difference() {
        union() { cylinder(d = cable_od + 2 * clip_wall, h = clip_len, $fn = 48); translate([0, -4, 0]) cube([cable_od / 2 + 9, 8, clip_len]); }
        translate([0, 0, -1]) cylinder(d = cable_od - 2 * clip_interf, h = clip_len + 2, $fn = 48);
        translate([-cable_od, -clip_gap / 2, -1]) cube([cable_od, clip_gap, clip_len + 2]);
        translate([cable_od / 2 + 5, 0, clip_len / 2]) rotate([90, 0, 0]) cylinder(d = anchor_screw_clear, h = 12, center = true, $fn = 24);
    }
}

// ================================================================ SEAL PAD (option C)
module seal_pad() {        // TPU 95A, 15 % gyroid: circumaural ring that closes the front volume
    difference() {
        ring(seal_od / 2, seal_id / 2, standoff);
        for (a = [100, 220, 340]) polar((seal_od + seal_id) / 4, a) translate([0, 0, standoff - 6]) cylinder(d = 3.2, h = 7, $fn = 24);
    }
}

// ================================================================ placement
// Assembled position in the skin frame (skin plane z = 0), used for the
// mass-property export: every part as it sits on the head.
Z_MOD   = standoff + Z_MOD0;                        // module head face
Z_CUPTOP = Z_MOD + baffle_h + cup_h;               // cup outer end
module placed(p) {
    if (p == "ring")         translate([0, 0, standoff]) ring_body();
    if (p == "gasket_umi")   { if (umi_mode == "foam") translate([0, 0, standoff]) umi_foam_placed();
                               else translate([0, 0, standoff + floor_t]) gasket_umi(); }
    if (p == "arm_saddle")   rotate([0, 0, mx(saddle_a)])   translate([0, 0, standoff]) rotate([90, 0, 0]) arm("saddle");
    if (p == "arm_temporal") rotate([0, 0, mx(temporal_a)]) translate([0, 0, standoff]) rotate([90, 0, 0]) arm("temporal");
    if (p == "arm_mastoid")  rotate([0, 0, mx(mastoid_a)])  translate([0, 0, standoff]) rotate([90, 0, 0]) arm("mastoid");
    if (p == "saddle_cap")   rotate([0, 0, mx(saddle_a)]) translate([saddle_r - foot_t / 2, 0, saddle_skin_gap]) saddle_cap();
    if (p == "saddle_liner" && saddle_liner_t > 0) rotate([0, 0, mx(saddle_a)]) translate([saddle_r - foot_t / 2, 0, saddle_skin_gap]) saddle_liner();
    if (p == "pad_temporal") polar(pad_r, mx(temporal_a)) translate([0, 0, pad_h]) mirror([0, 0, 1]) pad_temporal();
    if (p == "pad_mastoid")  polar(mastoid_r, mx(mastoid_a))  translate([0, 0, pad_h]) mirror([0, 0, 1]) pad_mastoid();
    if (p == "pad_face_temporal" && pad_face_t > 0) polar(pad_r, mx(temporal_a)) translate([0, 0, pad_h]) mirror([0, 0, 1]) pad_face_temporal();
    if (p == "pad_face_mastoid" && pad_face_t > 0)  polar(mastoid_r, mx(mastoid_a)) translate([0, 0, pad_h]) mirror([0, 0, 1]) pad_face_mastoid();
    if (p == "arm_post" && has_post)  rotate([0, 0, mx(post_a)]) translate([0, 0, standoff]) rotate([90, 0, 0]) arm("post");
    if (p == "pad_post" && has_post)  polar(post_r, mx(post_a)) translate([0, 0, pad_h]) mirror([0, 0, 1]) pad_post();
    if (p == "baffle")       translate([0, 0, Z_MOD]) baffle();
    if (p == "gasket_driver") translate([0, 0, Z_MOD + seat_z]) gasket_driver();
    if (p == "driver")       translate([0, 0, Z_MOD + seat_z + driver_gasket_t - gasket_driver_squeeze]) driver_dummy();
    if (p == "cup")          translate([0, 0, Z_CUPTOP]) mirror([0, 0, 1]) cup();
    if (p == "cable_anchor") rotate([0, 0, mx(cable_a)]) translate([0, 0, standoff]) cable_anchor();
    if (p == "cable_clip")   rotate([0, 0, mx(cable_a)]) translate([bar_r1 + cable_od / 2 + 3, 0, standoff - clip_post_L + 5]) cable_clip();
    if (p == "seal_pad")     seal_pad();
    if (p == "driver_visual") translate([0, 0, Z_MOD + seat_z + driver_gasket_t - gasket_driver_squeeze]) driver_visual();
    if (p == "felt")         translate([0, 0, Z_CUPTOP - cup_end_t]) mirror([0, 0, 1]) felt_disc();
}
module driver_dummy() {       // mass-equivalent solid for COM/inertia (density scaled to the driver mass in calc)
    ring(driver_mount_d / 2, aperture_d / 2 - 0.5, driver_rim_t);
    cylinder(r = driver_rear_d / 2, h = driver_depth);
}

module driver_visual() {       // display model of a generic dynamic driver (not used for mass properties)
    color("DimGray") ring(driver_mount_d / 2, aperture_d / 2 - 0.5, driver_rim_t);                          // front rim
    color("Gainsboro") translate([0, 0, driver_rim_t * 0.5])                                                  // cone diaphragm
        difference() { cylinder(r1 = aperture_d / 2 - 0.5, r2 = driver_rear_d * 0.18, h = driver_depth * 0.28);
                       translate([0, 0, -0.01]) cylinder(r1 = aperture_d / 2 - 1.1, r2 = driver_rear_d * 0.18 - 0.6, h = driver_depth * 0.28 - 0.5); }
    color("Silver") translate([0, 0, driver_rim_t * 0.5]) scale([1, 1, 0.45]) sphere(r = driver_rear_d * 0.18, $fn = 48);   // dust cap
    color("DimGray") translate([0, 0, driver_rim_t])                                                          // basket
        difference() { cylinder(r1 = driver_mount_d / 2 - 1, r2 = driver_rear_d / 2, h = driver_depth * 0.55);
                       translate([0, 0, -0.01]) cylinder(r1 = driver_mount_d / 2 - 2, r2 = driver_rear_d / 2 - 1, h = driver_depth * 0.55 + 0.02);
                       for (a = [0:60:300]) rotate([0, 0, a + 30]) translate([0, -driver_mount_d / 6, -1]) cube([driver_mount_d, driver_mount_d / 3, driver_depth]); }
    color("Black") translate([0, 0, driver_rim_t + driver_depth * 0.55]) cylinder(r = driver_rear_d / 2 * 0.85, h = driver_depth * 0.45 - driver_rim_t);  // magnet
}
module felt_disc() {          // rear felt, die-cut: OD 2 cup_ri, hole over the link-eye boss (see note under cup())
    difference() {
        cylinder(r = cup_ri, h = felt_t);
        if (link_mode == "cup") translate([EYE_X, link_y, -1]) cylinder(d = felt_hole_d, h = felt_t + 2, $fn = 32);
    }
}

PARTS = ["ring", "gasket_umi", "arm_saddle", "arm_temporal", "arm_mastoid", "arm_post", "saddle_cap", "pad_temporal",
         "pad_mastoid", "pad_post", "baffle", "gasket_driver", "cup", "cable_anchor", "cable_clip",
         "pad_face_temporal", "pad_face_mastoid", "saddle_liner"];

if (part == "assembly") {
    color("SteelBlue") placed("ring");
    color("Orange") { placed("arm_saddle"); placed("arm_temporal"); placed("arm_mastoid"); placed("arm_post"); }
    color("DimGray") { placed("pad_temporal"); placed("pad_mastoid"); placed("pad_post"); placed("saddle_cap"); placed("cable_anchor"); }
    color("Firebrick") { placed("pad_face_temporal"); placed("pad_face_mastoid"); placed("saddle_liner"); }
    color("Wheat") placed("baffle");
    placed("driver_visual");
    color("Khaki") placed("felt");
    color("LimeGreen") placed("gasket_umi");
    color("DarkSlateGray") { placed("gasket_driver"); placed("cable_clip"); }
    color("LightSteelBlue") placed("cup");
    %translate([0, 0, -0.5]) cylinder(r = 90, h = 0.5);
}
// printable parts in print orientation
if (part == "ring")          ring_body();
if (part == "gasket_umi")    gasket_umi();
if (part == "arm_saddle")    arm("saddle");
if (part == "arm_temporal")  arm("temporal");
if (part == "arm_mastoid")   arm("mastoid");
if (part == "saddle_cap")    translate([0, 0, saddle_cap_wall]) saddle_cap();
if (part == "saddle_liner" && saddle_liner_t > 0) translate([0, 0, saddle_cap_wall]) saddle_liner();   // casting reference
if (part == "arm_post" && has_post) arm("post");
if (part == "pad_post" && has_post) pad_post();
if (part == "pad_temporal")  pad_temporal();
if (part == "pad_mastoid")   pad_mastoid();
if (part == "pad_face_temporal" && pad_face_t > 0) pad_face_temporal();
if (part == "pad_face_mastoid" && pad_face_t > 0)  pad_face_mastoid();
if (part == "baffle")        baffle();
if (part == "gasket_driver") gasket_driver();
if (part == "cup")           cup();
// cable anchor printed ON ITS SIDE (tangential face on the bed): the clip-post bending stress is then in-layer
// (extras.clip_post: SF upright across the layers is far lower)
if (part == "cable_anchor")  rotate([90, 0, 0]) translate([0, tab_w / 2, 0]) cable_anchor();
if (part == "cable_clip")    cable_clip();
if (part == "seal_pad")      seal_pad();
if (part == "felt")          felt_disc();
// assembled-position exports (mass properties)
for (p = concat(PARTS, ["driver", "seal_pad", "driver_visual", "felt"])) if (part == str("placed_", p)) placed(p);
