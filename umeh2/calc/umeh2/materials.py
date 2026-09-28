"""
Material and component data for UMEH-2.

Every value carries a SOURCE TAG:
  STD  standard / handbook value (ISO, ASTM, Shigley) — reliable
  DS   typical manufacturer datasheet range (generic grade; your spool may differ)
  LIT  published test literature, approximate range (FDM results scatter widely)
  A    engineering assumption (no reliable data; chosen conservatively)
  M    measured (none yet — fill in from the home tests in the report)

Design values = characteristic value x environmental factor / partial factor.
"""
from dataclasses import dataclass, field

G = 9.80665          # STD
RHO_AIR = 1.18       # STD, kg/m3 at 25 °C
C_AIR = 346.1        # STD, m/s at 25 °C
MU_AIR = 1.84e-5     # STD, Pa·s at 25 °C
P_REF = 20e-6        # STD


@dataclass
class Val:
    v: float
    tag: str
    note: str = ""

    def __float__(self):
        return float(self.v)


# ----------------------------------------------------------------- PETG (FDM)
PETG = dict(
    rho=Val(1270, "DS", "bulk density, kg/m3"),
    E_xy=Val(1.90e9, "LIT", "FDM PETG in-layer tensile modulus, typical 1.7–2.1 GPa"),
    E_z=Val(1.60e9, "LIT", "across layers, ~0.8–0.9 x E_xy"),
    nu=Val(0.38, "LIT"),
    S_xy=Val(45e6, "LIT", "in-layer (perimeter-dominated) tensile strength, printed; 40–50 MPa range, lower bound-ish"),
    S_z=Val(22e6, "LIT", "interlayer tensile strength, printed; 15–35 MPa range, conservative"),
    S_shear_il=Val(14e6, "LIT", "interlayer shear strength, conservative (~0.6 x S_z)"),
    S_bear=Val(55e6, "DS", "compressive yield, short-term"),
    Tg=Val(80.0, "DS", "glass transition, °C"),
    # temperature knock-down on strength and modulus at the service temperature
    kT_40C=Val(0.85, "LIT", "strength/modulus retention at 40 °C vs 23 °C"),
    kT_55C=Val(0.70, "LIT", "retention at 55 °C (car / direct sun)"),
    # fatigue: fully reversed endurance ratio at 1e7 cycles for printed PETG
    fat_ratio=Val(0.20, "A", "Se/S_xy at 1e7 cycles; printed-PETG fatigue data is scarce, 0.2 is conservative"),
    fat_b=Val(-0.085, "A", "Basquin exponent of normalized S-N curve (typical thermoplastics −0.07…−0.12)"),
    # Findley power-law creep: eps(t) = sigma/E0 * (1 + (t/tau)^n)
    creep_n=Val(0.20, "LIT", "Findley exponent for amorphous copolyesters, 0.15–0.25"),
    creep_tau_h=Val(40.0, "A", "time (h) at which creep strain equals elastic strain at 23 °C; 40 °C divides by 4"),
    cte=Val(68e-6, "DS", "1/K"),
    shrink=Val(0.004, "LIT", "as-printed linear shrinkage, 0.2–0.6 %"),
)
# partial factor on printed-polymer strength (material + process scatter)
GAMMA_M_PRINT = Val(1.6, "A", "covers perimeter defects, voids, moisture, spool variation")

# ----------------------------------------------------------------- PU foam (twist-lock anti-rattle strips)
# The required compression-force-deflection (CFD) window is an OUTPUT of structure.twistlock (purchase
# specification). Only the curve SHAPE and the density are assumed here.
FOAM = dict(
    rho=Val(240.0, "A", "microcellular PU foam sheet, 200–400 kg/m3; mass is negligible (< 0.1 g)"),
    cfd_exp=Val(0.30, "A", "plateau shape sigma(eps) = CFD25*(eps/0.25)^n, n 0.2–0.5 for microcellular PU, 10–60 % strain"),
    eps_dens=Val(0.75, "A", "onset of densification (strain)"),
    comp_set=Val(0.10, "A", "compression set after long-term squeeze at 40 °C (PU microcellular: 2–10 % typical)"),
    mu=Val(0.8, "A", "friction PU-foam skin on printed PETG, 0.5–1.0 (upper value used for the assembly torque)"),
    t_tol_rel=Val(0.10, "A", "die-cut sheet thickness tolerance +-10 %"),
)

# ----------------------------------------------------------------- TPU 95A
TPU = dict(
    rho=Val(1210, "DS"),
    E=Val(26e6, "DS", "95A Young's modulus at small strain, typical 20–35 MPa"),
    nu=Val(0.48, "LIT"),
    elong=Val(4.5, "DS", "elongation at break, 450 %"),
    compression_set=Val(0.25, "DS", "22 h at 70 °C, ISO 815 typical 20–35 %; at 40 °C for 8 h use 0.10 (A)"),
    creep_n=Val(0.12, "LIT"),
    creep_tau_h=Val(8.0, "A"),
)
# printed TPU pads with gyroid infill: effective modulus is a fraction of bulk
TPU_PAD_EFF = dict(
    infill15=Val(0.045, "LIT", "E_eff/E for 15 % gyroid, 2 walls (lattice scaling ~ rho^2)"),
    infill25=Val(0.10, "LIT"),
    solid=Val(1.0, "STD"),
)

# ----------------------------------------------------------------- skin/tissue
TISSUE = dict(
    E_mastoid=Val(120e3, "LIT", "soft tissue over bone, indentation modulus 50–300 kPa"),
    t_mastoid=Val(4.0e-3, "LIT", "skin + subcutis over mastoid, 3–6 mm"),
    E_temporal=Val(100e3, "LIT"),
    t_temporal=Val(6.0e-3, "LIT", "incl. temporalis fascia edge, 4–10 mm"),
    E_root=Val(150e3, "LIT", "auricle root / sulcus skin over cartilage-bone junction"),
    t_root=Val(3.0e-3, "LIT"),
    # comfort thresholds
    p_sustained=Val(4.0e3, "LIT", "sustained contact pressure target; capillary closure ~4.3 kPa (32 mmHg)"),
    p_transient=Val(8.0e3, "A", "tolerated for seconds (walking peaks)"),
    p_pain=Val(150e3, "LIT", "pressure-pain threshold over bone ~150–400 kPa (algometry)"),
)

SILICONE = dict(
    rho=Val(1100.0, "DS", "platinum-cure casting silicone Shore 10-30A, 1.07-1.15 g/cm3"),
    E=Val(0.6e6, "LIT", "Young's modulus of Shore ~20A silicone, 0.3-1.0 MPa (Gent: E = 0.0981(56+7.62336 S)/(0.137505(254-2.54 S)) MPa)"),
)
SILICONE_GRADE = "Shore 10–30A"     # pad facings (the grade range SILICONE describes)
# soft skin-safe platinum silicone for the saddle liner (Shore 00-30 class, e.g. Smooth-On Ecoflex 00-30)
SILICONE_GEL_GRADE = "Shore 00-30"   # saddle liner (the grade SILICONE_GEL describes)
_S100 = 68.9e3   # Pa, 100 % tensile modulus, 10 psi [DS]
SILICONE_GEL = dict(
    rho=Val(1070.0, "DS", "Shore 00-30 platinum silicone, specific gravity 1.07"),
    sigma100=Val(_S100, "DS", "100 % tensile modulus 10 psi (Ecoflex 00-30 technical bulletin)"),
    # neo-Hookean fit to the 100 % point: sigma_eng = G (lam - lam^-2) at lam = 2 -> G = sigma100 / 1.75; E = 3 G
    E=Val(3 * _S100 / 1.75, "C", "small-strain Young's modulus from the neo-Hookean fit to the 100 % modulus"),
    # compression modulus of a thin layer bonded to the cap, in high-friction contact with skin: Gent-Lindley
    # E_c = E (1 + 2 k S^2), S = loaded area / free (bulge) area; k = 1 is the incompressible limit (k = 0.93 is
    # tabulated for IRHD 30, softer rubbers approach 1) -> the stiffer, conservative value for the root load
    k_gent=Val(1.0, "LIT", "Gent-Lindley bonded-layer constant, incompressible limit"),
)

# ----------------------------------------------------------------- friction (ranges!)
FRICTION = {
    # (low, nominal, high), tag
    "TPU/dry skin": ((0.35, 0.55, 0.80), "LIT"),
    "silicone/dry skin": ((0.45, 0.70, 1.00), "LIT"),
    "TPU/sweaty or oily skin": ((0.20, 0.35, 0.50), "LIT"),
    "TPU/hair (over temporal)": ((0.15, 0.25, 0.35), "LIT"),
    "TPU/silicone (sleeve on wire)": ((0.50, 0.80, 1.10), "LIT"),
    "PETG/PETG (bayonet)": ((0.18, 0.25, 0.35), "LIT"),
}

# ----------------------------------------------------------------- music wire
def music_wire_Sut(d_mm):
    """ASTM A228 music wire minimum tensile strength, Shigley Table 10-4:
    Sut = A / d^m, A = WIRE Sut_A, m = WIRE Sut_m (0.10–6.5 mm)."""
    return WIRE["Sut_A"].v / d_mm ** WIRE["Sut_m"].v


WIRE = dict(
    E=Val(207e9, "STD"),
    rho=Val(7850, "STD"),
    Sy_ratio=Val(0.75, "STD", "bending yield ~0.75 Sut for cold-drawn wire (Shigley, torsion 0.45, bending ~0.75)"),
    Se_bend_ratio=Val(0.30, "A", "fully-reversed bending endurance / Sut for unpeened music wire, conservative"),
    min_bend_radius_d=Val(1.5, "STD", "minimum inside bend radius ~ 1–2 x d for music wire (supplier practice)"),
    nu=Val(0.29, "STD", "Poisson's ratio of carbon spring steel"),
    Sut_A=Val(2211e6, "STD", "ASTM A228 tensile strength Sut = A / d^m (d in mm), A in Pa·mm^m (Shigley Table 10-4)"),
    Sut_m=Val(0.145, "STD", "exponent m of Sut = A / d^m, ASTM A228, 0.10–6.5 mm"),
)

# brass (link eye sleeve, heat-set inserts)
BRASS = dict(
    rho=Val(8500, "DS", "CuZn37 / CuZn39Pb3 brass, 8.4–8.5 g/cm3"),
    E=Val(100e9, "LIT", "Young's modulus of brass, 97–110 GPa"),
    nu=Val(0.34, "LIT"),
    Sy=Val(250e6, "LIT", "half-hard brass tube, yield ~200–300 MPa"),
)

# ----------------------------------------------------------------- fasteners
# ISO 898 / ISO 3506 geometry; A2-70 stainless
SCREW = {
    "M2":   dict(d=2.0, p=0.40, As=2.07, head_d=3.8, csk_d=3.8, insert_od=3.2, insert_hole=3.0, insert_L=3.0),
    "M2.5": dict(d=2.5, p=0.45, As=3.39, head_d=4.5, csk_d=4.7, insert_od=4.0, insert_hole=3.6, insert_L=4.0),
    "M3":   dict(d=3.0, p=0.50, As=5.03, head_d=5.5, csk_d=5.6, insert_od=4.6, insert_hole=4.0, insert_L=5.0),
    "M4":   dict(d=4.0, p=0.70, As=8.78, head_d=7.0, csk_d=7.5, insert_od=5.9, insert_hole=5.6, insert_L=6.0),
}
A2_70 = dict(Rp02=Val(450e6, "STD", "ISO 3506-1 A2-70 0.2 % proof"), Rm=Val(700e6, "STD"))
# heat-set insert pull-out (brass, knurled) in PETG — empirical, scatter large
INSERT_PULLOUT = {
    "M2":   Val(250.0, "LIT", "N characteristic; published hobby/industry tests 200–500 N"),
    "M2.5": Val(380.0, "LIT", "N; 300–700 N"),
    "M3":   Val(550.0, "LIT", "N; 400–1000 N in PLA/PETG at proper install temperature"),
    "M4":   Val(900.0, "LIT", "N"),
}
INSERT_TORQUE_OUT = {  # N·m characteristic spin-out torque
    "M2": Val(0.35, "LIT"), "M2.5": Val(0.6, "LIT"), "M3": Val(1.0, "LIT"), "M4": Val(1.8, "LIT"),
}
GAMMA_INSERT = Val(2.0, "A", "partial factor on insert pull-out (installation quality dominates)")
NUT_FACTOR_K = Val(0.28, "LIT", "T = K F d for dry stainless on brass, 0.2–0.35")
# torque-preload scatter: the same torque gives F_i = T/(K d) for any K in this range (VDI 2230 tightening factor
# alpha_A = K_hi/K_lo = 1.75, torque driver) -> insert pull-out is checked at K_lo (highest preload), serration
# engagement at K_hi (lowest preload)
NUT_FACTOR_K_RANGE = (Val(0.20, "LIT", "lubricated/smooth stainless on brass"), Val(0.35, "LIT", "dry, rough"))

# ----------------------------------------------------------------- cable
CABLE = dict(
    mass_per_m=Val(0.022, "A", "kg/m, typical 4-core IEM/headphone cable 15–30 g/m — weigh yours"),
    hang_len=Val(0.35, "A", "m of cable hanging from each cradle before it rests on the chest/shoulder"),
    connector_retention=Val(8.0, "A", "N, 0.78 mm 2-pin friction retention 4–15 N — measure (test M-3)"),
    snag=Val(20.0, "A", "N, accidental snag design load (arm sweeping the cable)"),
)

# ----------------------------------------------------------------- acoustic materials
ACOUSTIC_MAT = dict(
    felt_sigma=Val(40e3, "LIT", "Pa·s/m2, wool/polyester needle felt 20–80 kPa·s/m2 (flow resistivity)"),
    fibre_sigma=Val(8e3, "LIT", "Pa·s/m2, loose polyester fibre at ~20 kg/m3, 4–15 kPa·s/m2"),
    voile_R=Val(12.0, "LIT", "Pa·s/m specific flow resistance (Rayl) of nylon voile, 5–30 Rayl"),
    felt_density=Val(200.0, "DS", "kg/m3 needle felt"),
    fibre_density=Val(20.0, "A", "kg/m3 packing of polyester fibre fill"),
)


def tagged_table(d):
    rows = []
    for k, v in d.items():
        if isinstance(v, Val):
            rows.append((k, v.v, v.tag, v.note))
    return rows
