# Study (2026-10-07): universal driver seat of UMEH-3 oval (geom "AO"): EVA stack clamp, contact-strip force, ring torque.
# Closed form, small strain, linear foam. EVA = craft EVA sheet ("EVA de papelaria"), compressive modulus at 5-15 %
# strain E [A] 0.3-1.0 MPa (nominal 0.5). The front EVA spreads each spoke's load over ~its thickness each side [A].
# python3 studies/univ_seat.py
import sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from umeh3 import geom
from umeh2.design import DRIVERS
geom.apply("AO")
U = geom.UNIV; tF, tM, tS, tB = U["t"]; st, sw, sg = U["strip"]; n_sp, w_sp, r_in = U["spoke"]; rib_w, proud = U["rib"]
AP_R = 52.8 / 2; RO = geom.POCKET_R - 0.15
MU = 0.5                          # [A] PETG on EVA, friction at the ring's back face
T_HAND = 0.25                     # [A] N m a fingertip turn on two 3 mm notches manages comfortably
T_KEY = 1.0                       # [A] N m with the printed ring key (two pins in the notches, 60 mm lever)
out = {}
for E in (0.3e6, 0.5e6, 1.0e6):
    for D in geom.SIZES:
        d = DRIVERS[D]; ro = d["mount_d"] / 2; rt = d["rim_t"]; ap = d["front_open"] / 2; rb = d["rear_d"] / 2 + 0.6
        eva = tF + tS                                   # EVA in series with the rim (M is popped out there)
        eps = (rt - (tM - proud)) / eva                 # gap under the spokes = tF+tM+tS-proud; rim replaces tM
        # the rim is squeezed only where the proud rib (r AP_R..AP_R+rib_w) or a spoke backs the front EVA; elsewhere the
        # ring's flat back leaves the rim at eps_flat = (rt - tM) / eva <= 0 (no load). Each load path spreads +-tF.
        r0, r1 = ap, ro
        ov = lambda a, b: max(0.0, min(b, r1) - max(a, r0))
        a_rib_r = 2 * math.pi * (AP_R + rib_w / 2) * ov(AP_R - tF, AP_R + rib_w + tF)
        a_sp = n_sp * (w_sp + 2 * tF) * ov(r_in, AP_R - tF)
        a_sup = min(math.pi * (r1 ** 2 - r0 ** 2), a_rib_r + a_sp)
        F_clamp = E * max(eps, 0) * a_sup * 1e-6        # N, driver held between front EVA and the back (S on B)
        # strip: 0.2 mm more EVA squeeze under it in S (1 mm) where the back flange (r rb..ro) presses it
        L = max(0.0, ro - rb)
        F_strip = E * (max(eps, 0) + st / tS) * sw * L * 1e-6
        # ring torque: rib (EVA under it squeezed `proud` over F+M+S) + the spokes' share of the clamp + strips
        a_rib = math.pi * ((AP_R + rib_w) ** 2 - AP_R ** 2)
        F_rib = E * proud / (tF + tM + tS) * a_rib * 1e-6
        F_ax = F_rib + F_clamp + 2 * F_strip
        T = MU * F_ax * (AP_R + rib_w / 2) * 1e-3
        out[f"E{E/1e6:.1f}_D{D}"] = dict(eps=round(eps, 3), clamp_N=round(F_clamp, 2), strip_N=round(F_strip, 2),
                                         strip_len_mm=round(L, 1), axial_N=round(F_ax, 1), torque_Nm=round(T, 3),
                                         by_hand=T <= T_HAND, with_key=T <= T_KEY)
for k, v in out.items():
    print(k, v)
os.makedirs(os.path.join(os.path.dirname(__file__), "..", "..", "results"), exist_ok=True)
json.dump(out, open(os.path.join(os.path.dirname(__file__), "..", "..", "results", "univ_seat.json"), "w"), indent=1)
