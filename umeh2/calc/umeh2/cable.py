"""
Cable loads and the cable "mechanical fuse".

Load path: cable -> TPU clip (interference grip) on the clip post of the
cable anchor -> anchor (2 x M3 into the ring tab at cable_a) -> ring ->
arms -> head. Beyond the clip, the 0.78 mm 2-pin plug sits in the socket.

Design intent: under a snag the cable must let go BEFORE anything breaks.
  * the clip slips at F_clip (interference friction),
  * then the plug pulls out at F_plug (connector retention, [A] {ret_lo:g}–{ret_hi:g} N).
The cradle therefore never sees more than max(F_clip, F_plug) no matter how
hard the cable is snagged; that value, not the {snag:g} N snag, is the design
cable load for the structure. F_clip is sized below F_plug so that a tug
first slides the cable in the clip (harmless) and the plug is the final fuse.

Clip grip (Lame, interference fit of a TPU ring on a compliant round cable):
  p = delta_r / ( R [ (1/E_r) ((ro^2 + R^2)/(ro^2 - R^2) + nu_r) + (1 - nu_c)/E_c ] )
  F_clip = mu * p * pi * D * L
"""
import math
from .materials import TPU, CABLE, G

E_CABLE = 12e6          # [A] PVC/TPE cable jacket over copper, effective radial modulus 5–30 MPa
NU_CABLE = 0.45         # [A]
MU_CLIP = 0.5           # [A] TPU on PVC/TPE jacket, 0.3–0.8
RETENTION_RANGE = (4.0, 15.0)   # [A] N, friction retention of the 0.78 mm 2-pin plug (worn loose socket ... tight new
                                # socket); CABLE['connector_retention'] is the nominal
__doc__ = __doc__.format(ret_lo=RETENTION_RANGE[0], ret_hi=RETENTION_RANGE[1], snag=CABLE["snag"].v)


def clip_grip(cable_od_mm, interf_mm, wall_mm, length_mm, E_cable=E_CABLE, mu=MU_CLIP):
    R = cable_od_mm / 2e3
    ro = R + wall_mm * 1e-3
    dr = interf_mm / 2e3
    Er, nur = TPU["E"].v, TPU["nu"].v
    p = dr / (R * ((1 / Er) * ((ro ** 2 + R ** 2) / (ro ** 2 - R ** 2) + nur) + (1 - NU_CABLE) / E_cable))
    F = mu * p * math.pi * 2 * R * length_mm * 1e-3
    return dict(p=p, F_clip=F)


def cable_static():
    m = CABLE["mass_per_m"].v * CABLE["hang_len"].v
    return dict(mass_kg=m, weight_N=m * G)


def design_cable_loads(des):
    grip = clip_grip(des["cable_od"], des["clip_interf"], des["clip_wall"], des["clip_len"])
    F_plug = CABLE["connector_retention"].v
    return dict(
        weight=cable_static()["weight_N"],
        clip=grip,
        plug=F_plug,
        plug_upper=RETENTION_RANGE[1],
        fuse=max(grip["F_clip"], F_plug),
        fuse_upper=max(grip["F_clip"], RETENTION_RANGE[1]),
        order_ok=grip["F_clip"] < F_plug,
    )


def size_clip_interference(des, target=(2.0, 5.0)):
    """Interference that puts the clip slip force inside `target` (N): above normal tugs, below the plug."""
    rows = []
    for i in range(1, 41):
        interf = i * 0.02
        g = clip_grip(des["cable_od"], interf, des["clip_wall"], des["clip_len"])
        rows.append((interf, g["F_clip"]))
    ok = [r for r in rows if target[0] <= r[1] <= target[1]]
    mid = (target[0] * target[1]) ** 0.5
    best = min(ok, key=lambda r: abs(math.log(r[1] / mid))) if ok else None
    return rows, best
