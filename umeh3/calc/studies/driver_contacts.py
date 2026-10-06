# Study (2026-10-06): solder-free driver contacts. Two phosphor-bronze leaves in the TPU adapter press on the driver's
# solder pads (cad/umeh3.scad contact_cuts / contacts_vis). Each leaf is a cantilever (free length CT_FREE, contact
# dimple 0.6 mm from the tip) pre-bent CT_PRE towards the driver. A flush pad pushes it back CT_PRE; a raised pad of
# height h pushes it back CT_PRE + h until it bottoms on the window floor (CT_STOP behind the flat leaf); taller pads
# then squeeze the TPU floor, so the leaf stress is capped at the stop. Checks: contact force (want >= 0.3 N for a stable gold/tin contact) and root bending stress against
# phosphor bronze C5191 yield (half-hard ~380 MPa, hard/spring ~550 MPa). Writes results/driver_contacts.json.
import os, json, math
HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
E = 110e3                              # MPa
T, B = 0.2, 2.0                        # leaf thickness, width (mm)
FREE, PRE, DIMPLE, STOP = 8.0, 0.5, 0.6, 0.2
ADAPTER_H = 4.0
RIM_T = {40: 1.8, 45: 1.8, 50: 2.0, 55: 2.0, 60: 2.0}
YIELD = {"meio-duro": 380.0, "duro (mola)": 550.0}
L = FREE - DIMPLE
I = B * T ** 3 / 12


def leaf(delta):
    F = 3 * E * I * delta / L ** 3
    return F, 6 * F * L / (B * T ** 2)


out = {"leaf_mm": [T, B, FREE], "pre_mm": PRE, "sizes": {}}
print(f"lâmina {T} x {B} mm, livre {FREE} mm, pré-curva {PRE} mm, contato a {DIMPLE} mm da ponta")
print(f"{'driver':>6} {'lábio':>7} {'ressalto máx':>12} {'F plano':>8} {'F máx':>7} {'tensão máx':>10} {'FS duro':>7} {'FS meio':>7}")
for D, rt in RIM_T.items():
    lip = ADAPTER_H - 1.0 - rt
    hmax = STOP                        # pad height that bottoms the leaf on the window floor
    F0, _ = leaf(PRE)
    Fm, sm = leaf(PRE + hmax)
    sf = {k: y / sm for k, y in YIELD.items()}
    out["sizes"][D] = {"lip": lip, "pad_h_max": hmax, "F_flush": F0, "F_max": Fm, "stress_max": sm, "SF": sf}
    print(f"{D:>4}mm {lip:>6.1f} {hmax:>10.1f}mm {F0:>7.2f}N {Fm:>6.2f}N {sm:>8.0f}MPa {sf['duro (mola)']:>7.2f} {sf['meio-duro']:>7.2f}")
# contact resistance budget: leaf + dimple, gold/tin pad at ~0.5 N is ~10-30 mOhm vs 32 Ohm driver -> < 0.01 dB
os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
json.dump(out, open(os.path.join(HERE, "results", "driver_contacts.json"), "w"), indent=1)
