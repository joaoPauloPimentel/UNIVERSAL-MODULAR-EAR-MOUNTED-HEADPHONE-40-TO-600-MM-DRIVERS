"""
The three design states compared in the report.

Design A  = UMEH-1 (rev A) as delivered: 194 g/side (50 mm module), Ø118 interface,
            tri-point cradle with the link eye on the mastoid pad, straight saddle bar,
            friction-clamped slotted arms. Its CAD is a different parametrisation, so for
            the support analysis A is represented by the Design B geometry carrying A's
            mass and COM (stated in the report).
Design B  = first UMEH-2 pass (this CAD, BASE inputs): lighter module sized for 40–60 mm,
            same attachment topology as A.
Final     = after the analysis-driven changes (see report "Iteration"):
            arched saddle (fore-aft location by normal forces), posterior-superior pad,
            link eye moved to the cup end (preload line through the support polygon),
            serrated arm clamps, re-derived link wire, re-sized pads/preload, cable fuse.
"""
import json, os
from . import design as dz

HERE = os.path.dirname(os.path.abspath(__file__))

DESIGN_A_MASS = dict(M=0.194, com_z=39.0e-3)     # UMEH-1 DESIGN.md / calc_results.md, 50 mm row: 194 g/side, COM 39 mm off the skin (UMEH-1 estimate, driver 30 g [A])

DESIGN_B = dict(dz.BASE, name="B")

FINAL_FIXED = dict(
    name="Final",
    link_mode="cup", rely_helix=False, saddle_scalp=True, saddle_arch=True, arch_R=22.0, arch_phi=35.0,
    serrated=True,
    # arm clamp (structure.serrated_joint, results/joints.json, report section 13): M3 arm screws at 0.10 N m with
    # the insert pair at 11 mm pitch. Tightening scatter is carried explicitly (nut factor K 0.20-0.35 [LIT]):
    # insert pull-out is checked at the highest preload T/(0.20 d) plus the screw's share of the 10 N handling
    # load, serration engagement at the lowest preload T/(0.35 d) after 3 years of PETG creep under the wave
    # washer. M2.5 (the first weight option) fails both under the handling load (results/weight.json W1).
    # The cable anchor is M3 as well, at 0.10 N m (its inserts see the upper plug-fuse load; W1b).
    arm_screw="M3", arm_torque=0.10, arm_screw_pitch=11.0, anchor_torque=0.10,
    # weight optimisation (results/weight.json, report section 5): cup wall 1.6 -> 1.2 mm (3 perimeters of
    # 0.42 mm lines), foot 5.0 -> 4.5 mm (the handling SF stays >= gamma_M; the bar clamp edge governs).
    # Legs 5.5 mm, heavier than the 5.0 mm baseline: with the arms modelled as flexible beams in series with the
    # contacts (support.attach_arm_nodes), in-plane bending of the mastoid leg lets the pads shed weight onto
    # the auricle root. Legs and saddle liner are chosen TOGETHER by calc/legs_liner.py (results/legs_liner.json):
    # legs 4.5-6.5 x liner 1.5-3.0 mm, the liner rule per leg thickness, then the eye tune's full evaluation; at the
    # tuned 5.0 N preload 5.5/2.5 and 6.5/2.0 score within SCORE_TIE and the lighter pair (5.5/2.5) is taken.
    # Rejected: leg/foot 4.0 (handling SF < gamma_M, W4d), ring infill (all perimeters, W2).
    cup_wall=1.2, leg_t=5.5, foot_t=4.5,
    # arm bar 4.0 -> 5.5 mm: 10 N handling load at any pad in any direction (analysis.arm_bound, 302 directions)
    # needs SF >= gamma_M = 1.6 at the bar clamp edge also at the -0.15 mm XY print tolerance (results/weight.json
    # "bar_t_tolerance"), and the M3 clamp needs the bar stiff enough to spread the screw pry load; 0.1 mm steps.
    bar_t=5.5,
    # cast silicone facing (Shore 10-30A) on the temporal and mastoid domes: with plain TPU domes the static
    # friction demand of the mastoid pad is above the TPU design coefficient (results/sweeps.json, friction rows
    # "no facing"); silicone/dry skin (0.45/0.70/1.00 [LIT]) brings it under 1. The posterior pad sits on hair and
    # stays TPU. 0.8 mm (casting in 0.1 mm steps); its mass is in the CAD mass properties.
    pad_face="silicone", pad_face_t=0.8,
    # 2.5 mm soft silicone liner (Shore 00-30) cast into the saddle bar's bearing face. Without it the donning-A
    # auricle-root pressure of the heavier 55 and 60 mm sides is above the sustained limit for EVERY eye position
    # on the cup (results/root_levers.json "no_liner_eye_scan"): the root's share of the weight follows its normal
    # stiffness against the pads' tangential stiffness, and thicker arms barely move it. The liner (Gent-Lindley
    # bonded layer, support.liner_compliance) makes the root contact compliant. Rule (calc/legs_liner.py): the
    # thinnest liner in 0.5 mm casting steps with >= 5 % root-pressure margin at both heavy sizes, chosen together
    # with the leg thickness; a thicker one hands more of the weight to the pads' friction and softens the saddle's
    # fore-aft location (sweeps.py "root_liner"). Rejected: a stretched temporal pad (needs a backing plate the
    # 10 mm foot cannot give, and would reach the zygomatic arch), arch phi 45 deg (the edge of the assumed
    # anatomical range; results/root_levers.json).
    saddle_liner_t=2.5,
    # wave spring washer under each arm-screw head keeps the serration clamped after the PETG creeps
    # (requirement, see structure.serrated_joint): >= 100 N flat load, rate <= 200 N/mm
    arm_washer=(100.0, 200e3),
    clip_interf=0.05,
    # twist lock: rigid floor + foam anti-rattle strips + 15.9 deg lead-in ramps (structure.twistlock)
    umi_mode="foam", foam_t=1.6, foam_eps=0.35, lug_ramp_c=1.0, lug_ramp_L=3.5,
    # driver pocket: 0.22 mm/side centres the Monte-Carlo band of the fit in its 0-0.8 mm window (tolerance.py)
    driver_pocket_clr=0.22,
)


def final_design(layout_file=os.path.join(HERE, "..", "final_layout.json")):
    des = dict(dz.BASE)
    des.update(FINAL_FIXED)
    with open(layout_file) as fh:
        lay = json.load(fh)
    des.update({k: v for k, v in lay.items() if not k.startswith("_")})
    return des
