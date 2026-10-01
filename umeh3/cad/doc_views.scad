// Images for the assembly guide (docs/img): xvfb-run -a openscad -o x.png -D 'view="explode"' doc_views.scad ...
include <umeh3.scad>
view = "assembly";
EXPL = [["pad", -40], ["front_foam", -28], ["front_ring", -18], ["driver", -10], ["adapter", -5], ["fibre", 22],
        ["bushing", 30]];
function ex(p) = let (k = search([p], EXPL)[0]) k == [] ? 0 : EXPL[k][1];
HOOK_PARTS = ["wire", "sleeve_leg", "paddle", "saddle_carrier", "saddle_foam"];
if (view == "explode") for (i = [0 : len(PARTS) - 1]) if (PARTS[i] != "neckband")
    color(COL[i]) translate([0, 0, ex(PARTS[i])]) placed(PARTS[i]);
if (view == "hook") for (i = [0 : len(PARTS) - 1]) if (len(search([PARTS[i]], HOOK_PARTS)[0]) != 0 || search([PARTS[i]], HOOK_PARTS) != [[]])
    if (search([PARTS[i]], HOOK_PARTS)[0] != []) color(COL[i]) placed(PARTS[i]);
if (view == "jig") { color("#8E9096") bend_jig(); color("Silver") translate([0, 0, 4.2]) scale([1, 1, 0.3]) sweep_tube(HOOK, WIRE_D * 1.4, HOOK_PLATE + 1, len(HOOK) - 1); }
if (view == "back") { color(COL[0]) shell(); color("#A27449") logo("R", false); color("#3A3D42") neckband(); }
