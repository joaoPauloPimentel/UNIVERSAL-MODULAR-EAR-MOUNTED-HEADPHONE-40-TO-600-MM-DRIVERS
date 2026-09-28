"""
Tolerance stack-ups: worst case, RSS and Monte Carlo ({n_mc} samples, each
tolerance a normal distribution with +-tol = 3 sigma [A]).

FDM tolerances [A, typical well-tuned 0.4 mm nozzle printer, PETG]:
  XY feature +-{xy:g} mm, Z (layer-quantised) +-{z:g} mm; printed hole and bore
  diameters enter the chains with the XY tolerance (a systematic hole undersize
  is a printer-calibration item: test print);
  linear shrink: both parts are the same material, so only the DIFFERENCE
  between two prints matters for a fit, +-{sd:g} % [A].
TPU parts: +-{tpu:g} mm thickness.
Driver: rim OD and rim thickness as in design.DRIVERS (tol_d, tol_depth) [A].
Acceptance: the Monte-Carlo 0.135 % / 99.865 % values (+-3 sigma) must lie in
the window [min, max]; the worst case (every term at its limit at once) is
reported for information.
"""
import math
import numpy as np
from . import design as dz
from .materials import FOAM

TOL = dict(xy=0.15, z=0.10, tpu=0.15, shrink_diff=0.002, rim_t=0.10)
N_MC = 100000
__doc__ = __doc__.format(n_mc=f"{N_MC:,}".replace(",", " "), xy=TOL["xy"], z=TOL["z"], sd=100 * TOL["shrink_diff"], tpu=TOL["tpu"])


def chain(terms, rng):
    """terms: list of (name, nominal, tol, sign). Returns dict with WC, RSS, MC percentiles and the
    term that contributes most (the LIMITING component)."""
    nom = sum(s * n for _, n, _, s in terms)
    wc_lo = sum(s * n - abs(t) for _, n, t, s in terms)
    wc_hi = sum(s * n + abs(t) for _, n, t, s in terms)
    rss = math.sqrt(sum(t ** 2 for _, _, t, _ in terms))
    samples = sum(s * rng.normal(n, abs(t) / 3, N_MC) for _, n, t, s in terms)
    lim = max(terms, key=lambda x: abs(x[2]))
    return dict(nom=nom, wc=(wc_lo, wc_hi), rss=(nom - rss, nom + rss), mc_p0135=np.percentile(samples, 0.135),
                mc_p99865=np.percentile(samples, 99.865), mc_min=samples.min(), mc_max=samples.max(), limiting=lim[0],
                share={n: t ** 2 / rss ** 2 for n, _, t, _ in terms}, samples=samples)


def stackups(d, des, D, seed=7):
    rng = np.random.default_rng(seed)
    drv = dz.DRIVERS[D]
    out = {}
    # 1. twist-lock axial: gasket compression = (lug_t + gasket_t) - groove_h   (must be > 0 and < 0.5 gasket_t)
    if des.get("umi_mode", "gasket") == "foam":
        # foam strain normal to the 45 deg cones: t_f - (groove_h + groove_rclr - lug_t)/sqrt2
        s2 = math.sqrt(2)
        out["UMI foam compression (anti-rattle strip)"] = (chain([
            ("foam sheet thickness (die-cut)", des["foam_t"], des["foam_t"] * FOAM["t_tol_rel"].v, +1),
            ("groove height (ring, Z) / sqrt2", d["groove_h"] / s2, TOL["z"] * 1.4 / s2, -1),
            ("groove radial clearance (XY) / sqrt2", des["groove_rclr"] / s2, TOL["xy"] / 2 / s2, -1),
            ("lug thickness (baffle, Z) / sqrt2", des["lug_t"] / s2, TOL["z"] / s2, +1)], rng),
            dict(min=0.10 * des["foam_t"], max=0.60 * des["foam_t"], unit="mm",
                 note="10-60 % strain: always touching, below densification (75 %)"))
    else:
      out["UMI axial gasket squeeze"] = (chain([
        ("groove height (ring, Z)", d["groove_h"], TOL["z"] * 1.4, -1),      # two Z-features -> sqrt(2)
        ("lug thickness (baffle, Z)", des["lug_t"], TOL["z"], +1),
        ("TPU gasket thickness", des["gasket_umi_t"], TOL["tpu"], +1),
        ("groove extra clearance", 0.15, 0.0, -1)], rng),
        dict(min=0.05, max=0.5 * des["gasket_umi_t"], unit="mm", note="0.05 mm min for rattle-free; <=50 % TPU compression"))
    # 2. radial fit spigot/bore
    Dsp = d["spig_d"]
    out["UMI radial clearance (diametral)"] = (chain([
        ("bore diameter (ring, XY)", d["bore_d"], TOL["xy"], +1),
        ("spigot diameter (baffle, XY)", Dsp, TOL["xy"], -1),
        ("shrink difference between prints", 0.0, TOL["shrink_diff"] * Dsp, +1)], rng),
        dict(min=0.0, max=0.8, unit="mm", note=">0 assembles; <0.8 keeps lug engagement and no wobble"))
    # 3. lug radial engagement: overlap of lug (R_L) and lip inner edge (R_B)
    R_S = Dsp / 2; R_L = R_S + des["lug_h"]; R_B = d["bore_d"] / 2
    out["lug radial overlap with lip"] = (chain([
        ("lug outer radius", R_L, TOL["xy"] / 2, +1),
        ("lip inner radius (bore)", R_B, TOL["xy"] / 2, -1),
        ("radial float (half clearance, worst side)", 0.0, (d["bore_d"] - Dsp) / 2, -1)], rng),
        dict(min=1.2, max=None, unit="mm", note=">= 1.2 mm bearing overlap on the 45 deg lip"))
    # 4. driver in its pocket (diametral clearance)
    pocket = drv["mount_d"] + 2 * des["driver_pocket_clr"]
    out["driver rim in pocket (diametral)"] = (chain([
        ("pocket diameter (baffle, XY)", pocket, TOL["xy"], +1),
        ("driver rim OD", drv["mount_d"], drv["tol_d"], -1)], rng),
        dict(min=0.0, max=0.8, unit="mm", note=">0 fits; <0.8 keeps the driver concentric (aperture overlap)"))
    # 5. driver clamp: gasket squeeze = (seat depth stack) ...
    gasket_sq = des["gasket_driver_squeeze"]
    out["driver gasket squeeze"] = (chain([
        ("baffle seat-to-rim-face height (Z)", d["baffle_h"] - d["seat_z"], TOL["z"], -1),
        ("driver rim thickness", drv["rim_t"], TOL["rim_t"], +1),
        ("driver gasket thickness", des["driver_gasket_t"], TOL["tpu"], +1),
        ("cup clamp step depth (Z)", des["clamp_depth"], TOL["z"], -1)], rng),
        dict(min=0.05, max=0.6 * des["driver_gasket_t"], unit="mm", note="sealed and clamped; <60 % compression"))
    # 6. pinna clearance under the module (p95 protrusion)
    out["pinna clearance to module (p95 ear)"] = (chain([
        ("standoff (ring head face)", des["standoff"], TOL["z"] * 2, +1),
        ("module head face above ring face", d["z_mod0"], TOL["z"], +1),
        ("p95 pinna protrusion", dz.ANTHRO["pinna_protrusion_p95"], 2.0, -1),        # [A] measurement scatter
        ("pad + tissue compression under preload", 0.6, 0.4, -1)], rng),
        dict(min=1.0, max=None, unit="mm", note="no pinna contact; 1 mm min so hair/earrings do not touch"))
    # 7. rear felt pushed over the link-eye boss (diametral interference; die-cut hole +-0.2 mm [A])
    if des.get("link_mode") == "cup":
        out["felt hole on the eye boss (interference)"] = (chain([
            ("eye boss OD (XY)", d["eye_boss_d"], TOL["xy"], +1),
            ("felt hole (die-cut)", d["felt_hole_d"], 0.20, -1)], rng),
            dict(min=0.0, max=None, unit="mm", note="felt stays compressed on the boss: no air by-pass around it"))
    return out
