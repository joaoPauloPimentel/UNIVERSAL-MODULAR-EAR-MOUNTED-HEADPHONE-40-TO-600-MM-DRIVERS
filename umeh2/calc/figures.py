#!/usr/bin/env python3
"""Figures for the report, drawn only from results/*.json."""
import json, os, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from umeh2 import acoustics as ac, analysis as an, materials as mt  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results"); FIG = os.path.join(ROOT, "report", "fig")
os.makedirs(FIG, exist_ok=True)


def J(n):
    p = os.path.join(RES, n + ".json")
    return json.load(open(p)) if os.path.exists(p) else None


def fig_acoustics():
    A = J("acoustics")
    if not A:
        return
    z_ = A.get("z_ear")
    zt = f"{z_ * 1e3:g} mm aperture to ear canal" if z_ else "reference distance"
    panels = [("dist", f"Aperture-to-ear-canal distance (open front, open back, 50 mm; Final {z_ * 1e3:g} mm)" if z_ else
               "Aperture-to-ear-canal distance (open front, open back, 50 mm)", lambda k: f"{float(k):g} mm"),
              ("sizes", f"Driver size (open/open, {zt})", lambda k: f"{k} mm"),
              ("rear", "Rear loading (50 mm)", str),
              ("felt", "Rear felt: flow resistivity x thickness (50 mm)", str),
              ("aperture", "Baffle aperture / driver diameter (50 mm)", lambda k: f"{float(k):.2f} D"),
              ("sealed_leak", "Sealed front (seal pad): leak slit height", lambda k: f"{k} mm")]
    fig, axs = plt.subplots(3, 2, figsize=(12, 12))
    for ax, (key, title, lab) in zip(axs.flat, panels):
        for k, c in A[key].items():
            ax.semilogx(c["f"], c["spl"], label=lab(k))
        ax.set_title(title, fontsize=10); ax.set_xlim(20, 20000); ax.grid(True, which="both", alpha=0.3)
        ax.axvspan(ac.F_LUMPED, 20000, color="0.9", zorder=-1)
        ax.set_xlabel("Hz"); ax.set_ylabel("dB SPL @ 1 V (model)"); ax.legend(fontsize=8)
    fig.suptitle(f"Lumped-model SPL at the ear (shaded > {ac.F_LUMPED / 1e3:g} kHz: indicative only; driver T/S are ASSUMPTIONS)", fontsize=11)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "acoustic_sweeps.png"), dpi=110); plt.close(fig)
    fig, ax = plt.subplots(figsize=(7, 4))
    for k, c in A["sizes"].items():
        ax.semilogx(c["f"], c["Z"], label=f"{k} mm")
    ax.set_title("Electrical impedance (model)"); ax.set_xlabel("Hz"); ax.set_ylabel("|Z| ohm"); ax.grid(True, which="both", alpha=0.3); ax.legend()
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "impedance.png"), dpi=110); plt.close(fig)
    fig, ax = plt.subplots(figsize=(7, 4))
    for D, rows in A["helmholtz_aperture"].items():
        ax.plot([r["ratio"] for r in rows], [r["fH"] / 1e3 for r in rows], "o-", label=f"{D} mm")
    ax.axhline(20, color="k", ls="--", lw=0.8, label="20 kHz")
    ch = [r["ratio"] for rows in A["helmholtz_aperture"].values() for r in rows if r.get("chosen")]
    if ch:
        ax.axvline(ch[0], color="C3", ls=":", lw=1.2, label="chosen aperture")
    ax.set_xlabel("aperture / D"); ax.set_ylabel("front-cavity Helmholtz f (kHz)")
    ax.set_title("Baffle aperture resonance vs aperture ratio"); ax.grid(alpha=0.3); ax.legend()
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "aperture_helmholtz.png"), dpi=110); plt.close(fig)


def fig_link():
    L = J("link")
    if not L:
        return
    fig, axs = plt.subplots(1, 2, figsize=(12, 4.5))
    for ax, nm in zip(axs, ("B", "Final")):
        g = L[nm]["grid"]
        ds = [row[0]["d"] for row in g]; ns = [x["n"] for x in g[0]]
        Z = np.array([[1.0 if x["ok"] else 0.0 for x in row] for row in g])
        SF = np.array([[min(x["SFy"] / 1.5, x["SFf"] / 1.5, 2.0 / max(x["Pr"], 1e-9) if x["Pr"] > 0 else 0) for x in row] for row in g])
        im = ax.imshow(np.clip(SF, 0, 1.6).T, origin="lower", aspect="auto", extent=[ds[0] - 0.05, ds[-1] + 0.05, -0.5, ns[-1] + 0.5], cmap="RdYlGn", vmin=0.4, vmax=1.6)
        ax.contour(ds, ns, Z.T, levels=[0.5], colors="k")
        ch = L[nm]["chosen"]
        if ch:
            ax.plot(ch["d_mm"], ch["n_coil"], "k*", ms=14)
        ax.set_xlabel("wire d (mm)"); ax.set_ylabel("apex coil turns")
        ax.set_title(f"Link wire, Design {nm}, 50 mm module path: min normalised margin\n(black: feasible edge; star: chosen"
                     + (", checked on all five modules)" if nm == "Final" else ")"), fontsize=9)
        plt.colorbar(im, ax=ax)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "link_wire.png"), dpi=110); plt.close(fig)


def _rows(S, sec):
    return S.get(sec, [])


def fig_sweeps():
    S = J("sweeps")
    if not S:
        return
    fig, axs = plt.subplots(2, 3, figsize=(15, 8.5))
    r = _rows(S, "arm_thickness")
    ax = axs[0, 0]
    ft = [x["foot_t"] for x in r]
    ax.plot(ft, [x["env"][0][0] for x in r], "o-", label="5 g envelope, von Mises")
    ax.plot(ft, [x["env"][1][0] for x in r], "s-", label="5 g envelope, interlayer")
    ax.plot(ft, [x["handling"][0][0] for x in r], "^-", label=f"{an.F_HANDLING:g} N handling, von Mises")
    ax.plot(ft, [x["handling"][1][0] for x in r], "v-", label=f"{an.F_HANDLING:g} N handling, interlayer")
    ax.axhline(mt.GAMMA_M_PRINT.v, color="r", ls="--", lw=0.8); ax.set_yscale("log"); ax.set_xlabel("foot thickness (mm); bar and leg scaled")
    ax.set_ylabel("lowest section SF"); ax.legend(fontsize=7); ax.set_title("Arm (frame) thickness")
    ax2 = ax.twinx(); ax2.plot(ft, [x["k_arm_mastoid"] / 1e3 for x in r], "k:"); ax2.set_ylabel("mastoid arm k_z (kN/m, dotted)")
    r = _rows(S, "pad_thickness")
    ax = axs[0, 1]; h = [x["key"] for x in r]
    ax.plot(h, [x.get("static_p", {}).get("M mastoid", np.nan) / 1e3 for x in r], "o-", label="mastoid p static (kPa)")
    ax.plot(h, [x["1 g normal"]["tilt"] for x in r], "s-", label="1 g worst tilt (deg)")
    ax.plot(h, [100 * x["2 g dynamic"]["slip"] for x in r], "^-", label="2 g released (% cases)")
    ax.set_xlabel("TPU pad height (mm)"); ax.legend(fontsize=8); ax.set_title("Pad (TPU) thickness"); ax.grid(alpha=0.3)
    r = _rows(S, "preload")
    des_ = [x for x in r if x["key"][1] == "design"]; low = [x for x in r if x["key"][1] == "mu_low"]
    ax = axs[0, 2]
    ax.plot([x["key"][0] for x in des_], [100 * x["1 g normal"]["slip"] for x in des_], "o-", label="1 g released %, design mu")
    ax.plot([x["key"][0] for x in low], [100 * x["1 g normal"]["slip"] for x in low], "s-", label="1 g released %, low mu")
    ax.plot([x["key"][0] for x in des_], [100 * x["2 g dynamic"]["slip"] for x in des_], "^-", label="2 g released %, design mu")
    ax.plot([x["key"][0] for x in des_], [100 * (x.get("static_mu_demand") or np.nan) for x in des_], "d:", label="static mu demand (% of design)")
    ax.set_xlabel("link preload P (N)"); ax.legend(fontsize=7); ax.set_title("Preload"); ax.grid(alpha=0.3)
    r = _rows(S, "eye_map")
    ax = axs[1, 0]
    sc = ax.scatter([x["key"][0] for x in r], [x["key"][1] for x in r],
                    c=[100 * x["2 g dynamic"]["slip"] if x["1 g normal"]["slip"] == 0 else 100 for x in r], s=160, cmap="RdYlGn_r", vmin=0, vmax=30)
    for x in r:
        if x["1 g normal"]["slip"] > 0 or x["1 g normal"]["unseated"] > 0 or not x["static_ok"]:
            ax.plot(x["key"][0], x["key"][1], "kx")
    plt.colorbar(sc, ax=ax, label="2 g released % (x: fails static or 1 g)"); ax.set_xlabel("eye x (mm, +fwd)"); ax.set_ylabel("eye y (mm, +up)")
    ax.set_title("Link eye location on the 50 mm cup"); ax.set_aspect("equal")
    r = _rows(S, "support_spacing")
    ax = axs[1, 1]; sc_ = [x["key"] for x in r]
    ax.plot(sc_, [100 * x["2 g dynamic"]["slip"] for x in r], "o-", label="2 g released %")
    ax.plot(sc_, [x["1 g normal"]["tilt"] for x in r], "s-", label="1 g tilt deg")
    ax.plot(sc_, [100 * x["1 g normal"]["slip"] for x in r], "^-", label="1 g released %")
    ax.set_xlabel("pad radius scale"); ax.legend(fontsize=8); ax.set_title("Support spacing"); ax.grid(alpha=0.3)
    r = _rows(S, "friction")
    ax = axs[1, 2]; lab = [x["key"] for x in r]
    ax.barh(lab, [100 * x["1 g normal"]["slip"] for x in r], label="1 g")
    ax.barh(lab, [100 * x["2 g dynamic"]["slip"] for x in r], alpha=0.5, label="2 g")
    ax.set_xlabel("% of load combinations with gross slip"); ax.legend(); ax.set_title("Friction sensitivity")
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "structure_support_sweeps.png"), dpi=110); plt.close(fig)
    # support angles + saddle arch
    fig, axs = plt.subplots(1, 2, figsize=(12, 4.2))
    r = _rows(S, "support_angle"); ax = axs[0]
    lab = [f"T{x['key'][0]:+d} P{x['key'][1]:+d}" for x in r]
    ax.bar(lab, [100 * x["2 g dynamic"]["slip"] for x in r], label="2 g released %")
    ax.bar(lab, [100 * x["1 g normal"]["slip"] for x in r], label="1 g released %", alpha=0.7)
    ax.set_ylabel("%"); ax.set_title("Pad angle shifts (deg): temporal T, post-superior P"); ax.legend(); ax.tick_params(axis="x", rotation=30)
    r = _rows(S, "saddle_arch"); ax = axs[1]
    for Rr in sorted({x["key"][0] for x in r}):
        rr = [x for x in r if x["key"][0] == Rr]
        ax.plot([x["key"][1] for x in rr], [100 * x["2 g dynamic"]["slip"] for x in rr], "o-", label=f"arch R {Rr:.0f} mm")
    ax.set_xlabel("saddle wrap angle (deg)"); ax.set_ylabel("2 g released %"); ax.set_title("Saddle arch ('hook') geometry"); ax.legend(); ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "support_angle_arch.png"), dpi=110); plt.close(fig)


def fig_limits():
    """Max driver mass per condition, cable tug limits, weight options, seal sweep, isolation."""
    MM = J("max_driver_mass"); C = J("cable"); W = J("weight"); A = J("acoustics"); DY = J("dynamics")
    if MM:
        fig, ax = plt.subplots(figsize=(9, 4.5))
        Ds = list(MM.keys()); conds = list(next(iter(MM.values())).keys())
        wbar = 0.8 / len(conds)
        for i, c in enumerate(conds):
            x = np.arange(len(Ds)) + i * wbar
            lo_ = [MM[D][c]["min_driver_g"] if MM[D][c]["holds_at_nominal"] else 0.0 for D in Ds]
            hi_ = [MM[D][c]["max_driver_g"] if MM[D][c]["holds_at_nominal"] else 0.0 for D in Ds]
            ax.bar(x, np.subtract(hi_, lo_), wbar, bottom=lo_, label=c)
            for xi, D in zip(x, Ds):
                if not MM[D][c]["holds_at_nominal"]:
                    ax.text(xi, 2, "fails at nominal", rotation=90, fontsize=6, ha="center", va="bottom")
        nom = [MM[D][conds[0]]["nominal_g"] for D in Ds]
        ax.scatter(np.arange(len(Ds)) + 0.4 - wbar / 2, nom, marker="_", s=900, color="k", zorder=5, label="nominal driver [A]")
        ax.set_xticks(np.arange(len(Ds)) + 0.4 - wbar / 2); ax.set_xticklabels([f"{D} mm" for D in Ds])
        ax.set_ylabel("driver mass (g)"); ax.set_title("Passing driver-mass range per condition (CAD mass of the rest of the side)")
        ax.legend(fontsize=7); ax.grid(axis="y", alpha=0.3)
        fig.tight_layout(); fig.savefig(os.path.join(FIG, "max_driver_mass.png"), dpi=110); plt.close(fig)
    if C and "tug_limits" in C:
        fig, ax = plt.subplots(figsize=(9, 4.2))
        Ds = list(C["tug_limits"].keys()); names = list(next(iter(C["tug_limits"].values()))["named"].keys())
        wbar = 0.8 / len(Ds)
        for i, D in enumerate(Ds):
            ax.bar(np.arange(len(names)) + i * wbar, [C["tug_limits"][D]["named"][k] for k in names], wbar, label=f"{D} mm")
        ax.set_xticks(np.arange(len(names)) + 0.4 - wbar / 2); ax.set_xticklabels(names, rotation=25, ha="right", fontsize=8)
        ax.set_ylabel("cable pull at the clip before the cradle releases (N)"); ax.set_yscale("log"); ax.grid(axis="y", alpha=0.3)
        ax.set_title("Cable tug limits while worn (support model)"); ax.legend()
        fig.tight_layout(); fig.savefig(os.path.join(FIG, "tug_limits.png"), dpi=110); plt.close(fig)
    if A and "seal_sweep" in A:
        fig, ax = plt.subplots(figsize=(9, 4.2))
        rows = A["seal_sweep"]["50"] if "50" in A["seal_sweep"] else next(iter(A["seal_sweep"].values()))
        lab = [f"{r['material']}, H {r['H_mm']:.0f}" for r in rows]
        ax.barh(lab, [r["loss_50"] for r in rows], label="50 Hz"); ax.barh(lab, [r["loss_100"] for r in rows], alpha=0.6, label="100 Hz")
        ax.set_xlabel("bass loss vs a perfect seal (dB)"); ax.set_title("Seal pad (sealed-front option), 50 mm"); ax.legend()
        ax.tick_params(axis="y", labelsize=7)
        fig.tight_layout(); fig.savefig(os.path.join(FIG, "seal_sweep.png"), dpi=110); plt.close(fig)
    if DY:
        fig, ax = plt.subplots(figsize=(7, 4))
        f = np.logspace(1.3, 4.3, 300)
        opts = DY["50"]["isolation_options"] if "50" in DY else next(iter(DY.values()))["isolation_options"]
        for k, o in opts.items():
            r_ = f / o["fn"]; z = o["zeta"]
            T = np.sqrt((1 + (2 * z * r_) ** 2) / ((1 - r_ ** 2) ** 2 + (2 * z * r_) ** 2))
            ax.loglog(f, T, label=f"{k}: fn {o['fn']:.0f} Hz")
        ax.axhline(1, color="k", lw=0.6); ax.set_xlabel("Hz"); ax.set_ylabel("force transmissibility driver -> baffle")
        ax.set_title("Driver mounting: TPU vs silicone rings (50 mm)"); ax.legend(fontsize=7); ax.grid(which="both", alpha=0.3)
        fig.tight_layout(); fig.savefig(os.path.join(FIG, "driver_isolation.png"), dpi=110); plt.close(fig)


def fig_mass():
    M = J("slip_vs_mass"); F = J("final_sizes")
    if M:
        fig, ax = plt.subplots(figsize=(7, 4))
        for k in ("1 g normal", "2 g dynamic", "3 g severe"):
            ax.plot([r["total_g"] for r in M], [100 * r[k] for r in M], "o-", label=k)
        ax.set_xlabel("total mass per side (g)"); ax.set_ylabel("% load combinations with gross slip"); ax.grid(alpha=0.3); ax.legend()
        ax.set_title("Retention vs mass (Final, 50 mm geometry)")
        fig.tight_layout(); fig.savefig(os.path.join(FIG, "slip_vs_mass.png"), dpi=110); plt.close(fig)
    if F:
        fig, ax = plt.subplots(figsize=(9, 5))
        groups = {}
        for D, r in F.items():
            for p in r["parts"]:
                nm = p["part"]
                key = ("screws/inserts/nuts" if ("screw" in nm or "insert" in nm or "nut" in nm or "pin" in nm) else
                       "link share" if "link" in nm else nm)
                groups.setdefault(key, {})[D] = groups.setdefault(key, {}).get(D, 0) + p["m"] * 1e3
        Ds = list(F.keys()); bottom = np.zeros(len(Ds))
        for k, v in sorted(groups.items(), key=lambda kv: -max(kv[1].values())):
            vals = np.array([v.get(D, 0) for D in Ds])
            ax.bar(Ds, vals, bottom=bottom, label=k); bottom += vals
        ax.set_ylabel("g per side"); ax.set_xlabel("driver (mm)"); ax.legend(fontsize=7, ncol=2); ax.set_title("Mass breakdown (from CAD meshes + hardware)")
        fig.tight_layout(); fig.savefig(os.path.join(FIG, "mass_breakdown.png"), dpi=110); plt.close(fig)


if __name__ == "__main__":
    fig_acoustics(); fig_link(); fig_sweeps(); fig_mass(); fig_limits()
    print("figures written")
