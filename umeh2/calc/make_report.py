#!/usr/bin/env python3
"""Writes report/ENGINEERING_REPORT.md from results/*.json (numbers are never typed by hand)."""
import json, math, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from umeh2 import design as dz, configs as cf, support as sp, materials as mt, structure as st, layout as lo, acoustics as ac
from umeh2 import linkspring as ls, cable as cb, tolerance as tl, analysis as an, extras as ex, dynamics as dy
from umeh2 import massprops as mpz

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# UMEH2_RESULTS / UMEH2_REPORT / UMEH2_README: test hooks (e.g. render the smoke results elsewhere); default = the package
RES = os.environ.get("UMEH2_RESULTS", os.path.join(ROOT, "results"))
OUT = os.environ.get("UMEH2_REPORT", os.path.join(ROOT, "report", "ENGINEERING_REPORT.md"))


def J(n):
    p = os.path.join(RES, n + ".json")
    return json.load(open(p)) if os.path.exists(p) else {}


L = J("link"); B = J("design_B"); A = J("design_A"); F = J("final_sizes"); JT = J("joints"); CB = J("cable")
DY = J("dynamics"); TO = J("tolerance"); AC = J("acoustics"); MM = J("max_driver_mass"); SM = J("slip_vs_mass"); SW = J("sweeps")
# the 'dynamic' driver-mass conditions of run_all.MASS_CONDS, by allowed released fraction: strictest and most permissive
_DYN = sorted({k for r in MM.values() for k in r if k.startswith("dynamic (released <= ")},
              key=lambda k: float(k.split("<= ")[1].rstrip(")").rstrip("%")))
DYN0, DYNA = (_DYN[0], _DYN[-1]) if _DYN else ("dynamic (released <= 0%)", "dynamic (released <= 0%)")
DYNA_PCT = DYNA.split("<= ")[1].rstrip(")").replace("%", " %")


def sci(x):
    """1e7-style scientific notation for round powers of ten (e.g. cycle counts)."""
    m_, e_ = f"{x:.0e}".split("e")
    return f"{m_}e{int(e_)}"


def mmax(r):
    """Largest passing driver mass of one condition for a summary cell (max_driver_mass result dict)."""
    if not r:
        return None
    if not r.get("holds_at_nominal"):
        return f"fails at the nominal {r['nominal_g']:g} g"
    return (">= " if r.get("capped") else "") + f"{r['max_driver_g']:.1f}"


def mrange(r):
    """Passing driver-mass range of one condition for the section-10 table."""
    if not r:
        return "–"
    if not r.get("holds_at_nominal"):
        rng = f"; holds {r['min_driver_g']:.1f}–{r['max_driver_g']:.1f} g" if r.get("max_driver_g") is not None else "; fails at 0 g too"
        return f"fails at the nominal {r['nominal_g']:g} g" + rng
    hi = f"{r['max_driver_g']:.1f}" + ("+" if r.get("capped") else "")
    chk = "" if r.get("interval_checked") in (True, None) else " (interior point fails!)"
    return f"{r['min_driver_g']:.1f}–{hi}{chk}"
WT = J("weight"); CS = J("contact_stress"); EYE = J("eye_tuning"); RL = J("root_levers"); LL = J("legs_liner")
EC = J("eye_check"); SK = J("shakedown"); DN = J("dense_1g"); DP = J("grid_1g_before_grid"); ETP = J("eye_tuning_before_grid")
ETG45 = J("eye_tuning_grid45"); DG45 = J("dense_1g_grid45")
_g45p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "final_layout_grid45.json")
G45L = json.load(open(_g45p)) if os.path.exists(_g45p) else None       # the Final after change 19 (45° grid)
FINAL = cf.final_design()
if L:
    FINAL["wire_d"] = L["Final"]["chosen"]["d_mm"]; FINAL["link_coils"] = L["Final"]["chosen"]["n_coil"]
FS = lo.apply_pad_scale(dict(FINAL))
SIZES = [str(D) for D in dz.SIZES]
# criteria of the calculation modules as text (never typed by hand)
PSUS = f"{mt.TISSUE['p_sustained'].v / 1e3:g}"
TILT_N = f"{lo.ROT_NORMAL:g}"
REL = f"{sp.DISP_MAX * 1e3:g} mm / {sp.ROT_MAX:g}°"
FH = f"{an.F_HANDLING:g}"
NDH = f"{((F.get('50') or {}).get('handling') or {}).get('n_dir') or an.N_HANDLING_DIRS}"
GM = f"{mt.GAMMA_M_PRINT.v:g}"
RM_ = (LL or {}).get("root_margin", 0.05)
RM = f"{100 * RM_:g}"
_ti = (EYE or {}).get("_inputs") or {}      # inputs and load sets of the eye tune (results/eye_tuning.json)
_gs = _ti.get("grid_mm") or []


def f(x, n=3):
    if x is None:
        return "–"
    if isinstance(x, str):
        return x
    if isinstance(x, bool):
        return "yes" if x else "NO"
    if isinstance(x, float) and (math.isnan(x) or math.isinf(x)):
        return "–" if math.isnan(x) else ("∞" if x > 0 else "−∞")
    if x == 0:
        return "0"
    a = abs(x)
    if 1000 <= a < 1e6:
        return f"{x:.0f}"
    if a >= 1e6 or a < 0.01:
        return f"{x:.{n}g}"
    return f"{x:.{max(0, n - 1 - int(math.floor(math.log10(a))))}f}"


def table(headers, rows):
    s = "| " + " | ".join(headers) + " |\n|" + "|".join("---" for _ in headers) + "|\n"
    for r in rows:
        s += "| " + " | ".join(f(c) if not isinstance(c, str) else c for c in r) + " |\n"
    return s + "\n"


def liner_reason():
    """Rounding/source text of the liner thickness, from the root-lever table (results/root_levers.json)."""
    rows = {r_["variant"]: r_["60"] for r_ in (RL or {}).get("rows", [])}
    lt = FINAL["saddle_liner_t"]; ls_ = (LL or {}).get("liners") or [lt - 0.5, lt, lt + 0.5]
    step = min(y_ - x_ for x_, y_ in zip(sorted(ls_), sorted(ls_)[1:]))
    a, b = rows.get(f"liner {lt - step:g} mm", {}), rows.get(f"liner {lt + step:g} mm", {})
    if not (a.get("ok") and b.get("ok")):
        return f"§6 root-lever table; {step:g} mm steps (casting)"
    sl = {round(float(x_["key"]), 3): x_ for x_ in (SW or {}).get("root_liner", [])}
    x0, x1 = sl.get(round(float(lt), 3)), sl.get(round(float(lt + step), 3))
    loc = ""
    if x0 and x1:
        t0, t1 = x0["1 g normal"]["tilt"], x1["1 g normal"]["tilt"]
        s0, s1 = 100 * x0["2 g dynamic"]["slip"], 100 * x1["2 g dynamic"]["slip"]
        if t1 > t0 or s1 > s0:
            loc = f" and loosens the saddle's location (§18: 1 g tilt {f(t0)} → {f(t1)}°, 2 g released {f(s0)} → {f(s1)} %)"
    return (f"thinnest liner in {step:g} mm casting steps with ≥ {RM} % root margin at 60 mm (§6 lever table: {lt - step:g} mm → {f(a['root_p'] / 1e3)} kPa); "
            f"thicker hands weight to the pads' friction ({lt + step:g} mm → μ demand {f(b['mu_demand'])}){loc}")


def rng(xs, unit=""):
    """'a–b' of a list of numbers (one value when they print the same)."""
    a, b = f(min(xs)), f(max(xs))
    return (a if a == b else f"{a}–{b}") + unit


def pf(b):
    return "PASS" if b else "**FAIL**"


def ls_stock_tag(d_mm):
    """Source tag of a stock wire diameter (linkspring.STOCK_D_DS: datasheet sizes; STOCK_D_A: assumed stocked)."""
    return "DS" if any(abs(d_mm - x) < 1e-9 for x in ls.STOCK_D_DS) else "A: assumed stocked, confirm with the wire supplier"


def w_verdict(v):
    """Decision of a weight option, computed: adopted = the Final carries the change; the reasons are the checks the
    option fails (handling SF < γM, auricle-root p > sustained limit, insert pull-out or joint SF < 1)."""
    cur = lambda k_: mpz.PRINT["ring"][3] if k_ == "ring_infill" else FINAL.get(k_)
    same = lambda a_, b_: (abs(a_ - b_) < 1e-9) if isinstance(a_, (int, float)) and isinstance(b_, (int, float)) else a_ == b_
    ch = {k_: x_ for k_, x_ in (v.get("change") or {}).items() if x_ is not None}
    adopted = bool(ch) and all(same(cur(k_), x_) for k_, x_ in ch.items())
    fails = []
    if "handling" in v and v["handling"][0] < mt.GAMMA_M_PRINT.v:
        fails.append(f"handling SF {f(v['handling'][0])} < γM {GM}")
    if v.get("root_p_60") is not None and v["root_p_60"] > mt.TISSUE["p_sustained"].v:
        fails.append(f"auricle-root p {f(v['root_p_60'] / 1e3)} > {PSUS} kPa")
    if v.get("pullout_SF_preload") is not None and v["pullout_SF_preload"] < 1:
        fails.append(f"insert pull-out SF {f(v['pullout_SF_preload'])} < 1 at the highest preload")
    jmin = min((min(j["SF_engage"], j["SF_pullout"]) for j in (v.get("joints") or {}).values()), default=None)
    if jmin is not None and jmin < 1:
        fails.append(f"arm-joint SF {f(jmin)} < 1")
    an_ = ((v.get("anchor") or {}).get("clip + plug in series (upper)") or {}).get("SF_initial")   # design cable load (fuse)
    if an_ is not None and an_ < 1:
        fails.append(f"anchor insert SF {f(an_)} < 1 at the upper fuse load")
    if adopted:
        return "adopted" + (" (mass added)" if v.get("delta", 0) > 0 else "") + ("; BUT " + "; ".join(fails) if fails else "")
    if fails:
        return "rejected: " + "; ".join(fails)
    why = []
    fj = (WT.get("final") or {}).get("joints") or {}
    if jmin is not None and fj:
        why.append(f"lowest joint SF {f(jmin)} against {f(min(min(j['SF_engage'], j['SF_pullout']) for j in fj.values()))} in the Final (§13)")
    if abs(v.get("delta", 0.0)) < 5e-5:
        why.append("no mass saving" + (f" (ring shell fraction {f(v['shell_fraction'])})" if "shell_fraction" in v else ""))
    return "not taken" + (": " + "; ".join(why) if why else "")


def no_liner_history():
    """Iteration-record text of the saddle-liner change (results/root_levers.json)."""
    if not RL:
        return "§6 root-lever table"
    p_s = mt.TISSUE["p_sustained"].v
    ns = RL.get("no_liner_eye_scan", {})
    best = {D: (ns.get(D) or {}).get("min_root_p") for D in ("55", "60")}
    grid = (ns.get("60") or {}).get("grid_mm", 4.0)
    over = [D for D in ("55", "60") if best[D] and best[D] > p_s]
    if over:
        t = (f"without a liner the donning-A auricle-root pressure stays above the {PSUS} kPa limit at every eye position on the "
             f"cup ({grid:g} mm grid) at " + " and ".join(f"{D} mm (best eye {f(best[D] / 1e3)} kPa)" for D in over))
        rest = [D for D in ("55", "60") if D not in over and best[D]]
        if rest:
            t += "; " + ", ".join(f"at {D} mm the best eye leaves {f(100 * (1 - best[D] / p_s))} % margin" for D in rest)
    else:
        t = ("without a liner the best eye positions give " + " / ".join(f"{f(best[D] / 1e3)} kPa at {D} mm" for D in ("55", "60") if best[D]))
    lev = [r_ for r_ in RL.get("rows", []) if r_["variant"].startswith("no liner, ") and "rigid" not in r_["variant"]]
    good = [r_["variant"][len("no liner, "):] for r_ in lev if r_["60"].get("ok") and 1 - r_["60"]["root_p"] / p_s >= RM_]
    t += (f". Of the other single levers (thicker arms, larger pads, arch angle, preload) "
          + ("none reaches" if not good else "only " + "; ".join(good) + " reaches")
          + f" the {RM} % root margin at 60 mm (§6 lever table)")
    return t


def fail_pattern(summ):
    """Words for the pattern of a set of failing 1 g combinations, from analysis.fails_summary (over all of them)."""
    if not summ or not summ.get("n"):
        return ""
    n = summ["n"]
    t = f"head tilted {f(summ['tilt_min'])}–{f(summ['tilt_max'])}° from upright"
    t += (f"; {summ['side_out']} of {n} with this side hanging outward (head tilted towards it, this ear down)"
          f" and {summ['cable_out']} of {n} with the cable pulling outward ({summ['both_out']} both)")
    return t


def eyes_match_etp():
    """True when the first tune's best eyes (results/eye_tuning_before_grid.json) are the first Final's eyes."""
    ps0 = ((DP or {}).get("design") or {}).get("per_size") or {}
    for D in SIZES:
        b = ((ETP or {}).get(D) or {}).get("best") or {}
        if D not in ps0 or b.get("x") is None or abs(round(b["x"] * 2) / 2 - ps0[D]["link_x"]) > 1e-9 \
                or abs(round(b["y"] * 2) / 2 - ps0[D]["link_y"]) > 1e-9:
            return False
    return True


def grid_history():
    """Iteration-record text of change 19 (results/grid_1g_before_grid.json, eye_tuning.json preload levels)."""
    if not DP or not DP.get("sizes"):
        return "§8"
    bad = {D: r for D, r in DP["sizes"].items() if not r.get("ok")}
    if not bad:
        return "none: the first Final also passes the 1 g grid (§8)"
    wt = max(r["worst_tilt"][0] for r in DP["sizes"].values())
    n_ = lambda k: sum(int(r[k]) for r in bad.values())
    allf = dict(n=0, side_out=0, cable_out=0, both_out=0, tilt_min=float("inf"), tilt_max=-float("inf"))
    for r in bad.values():
        sm = r.get("fails_summary") or {}
        if sm.get("n"):
            for k in ("n", "side_out", "cable_out", "both_out"):
                allf[k] += sm[k]
            allf["tilt_min"] = min(allf["tilt_min"], sm["tilt_min"]); allf["tilt_max"] = max(allf["tilt_max"], sm["tilt_max"])
    _pp = [((ETP or {}).get(D) or {}).get("best", {}).get("prim") for D in SIZES]
    passed_own = all(x is not None and x >= 0 for x in _pp) and eyes_match_etp()
    t = (f"on the 1 g grid (§8) the first Final fails at {len(bad)} of {len(DP['sizes'])} modules ({n_('released')} released, "
         f"{n_('unseated')} tripod-lost, {n_('tilt_over')} over-tilted of {sum(int(r['n']) for r in DP['sizes'].values())} combinations; "
         f"worst tilt {f(wt)}°): {fail_pattern(allf)}"
         + ("; its tune had passed those eyes on a quasi-uniform sample (§8)" if passed_own else ""))
    _t19 = (ETG45 or {}).get("_inputs") or _ti
    lv = _t19.get("preload_levels") or []
    lo_ = [x for x in lv if x.get("n_pass") and x["P"] < float(_t19.get("link_preload", FINAL["link_preload"])) - 1e-9]
    _lo = []
    for x in lo_:
        nz = [D for D, n in x["n_pass"].items() if not n]
        if nz:
            _lo.append(f"{f(x['P'])} N (" + ("every module" if len(nz) == len(x["n_pass"]) else ", ".join(f"{D} mm" for D in nz)) + ")")
    if _lo:
        t += ("; with the grid (and each level's link wire, §11), lower preload levels left modules without a passing eye: "
              + "; ".join(_lo))
    return t


def stall_history():
    """Iteration-record text of change 20 (results/solver_stall_check.json)."""
    SC = J("solver_stall_check")
    if not SC or not SC.get("cases"):
        return "isolated releases in the dense 1 g check (§8)"
    parts = []
    for c in SC["cases"]:
        runs = c["runs"]
        r4 = next((r for r in runs if r["max_cuts"] == 0 and r["n_steps"] == 4 and r["load_scale"] == 1.0), None)
        held = [r["n_steps"] for r in runs if r["max_cuts"] == 0 and r["load_scale"] == 1.0 and r["ok"]]
        sc_ok = all(r["ok"] for r in runs if r["max_cuts"] == 0 and r["load_scale"] != 1.0)
        cut = next((r for r in runs if r["max_cuts"] > 0), None)
        if not r4 or r4["ok"]:
            continue
        ff = r4.get("first_failure") or {}
        parts.append(f"{c['case']['D']} mm: released at 4 increments ({ff.get('kind', '?')}, {f(ff.get('disp_mm'))} mm / {f(ff.get('rot_deg'))}°)"
                     + (f", held at {', '.join(str(n) for n in held)} increments" if held else "")
                     + (" and at the load × (1 ± 1e-4)" if sc_ok else "")
                     + (f"; with the cuts it holds (tilt {f(cut['tilt'])}°)" if cut and cut["ok"] else "; still released with the cuts"))
    return ("without the cuts the solver released these combinations of the dense 1 g check, which hold with more increments or a "
            "load changed by 1e-4 — stalled minimisations, not releases: " + "; ".join(parts)
            + " (`results/solver_stall_check.json`, `calc/check_stall.py`)") if parts else "§8"


def _on_grid(v, polar, az_step):
    """True if direction v is a point of ring_grid(polar, az_step)."""
    t, p = _az_deg(v)
    if t < 1e-6:
        return True
    return any(abs(t - x) < 1e-3 for x in polar) and abs(((p + 1e-6) % az_step) - 1e-6) < 1e-3


def _az_deg(v):
    v = np.asarray(v, float)
    return math.degrees(math.acos(max(-1.0, min(1.0, -v[1])))), math.degrees(math.atan2(v[2], v[0])) % 360


def grid45_history():
    """Iteration-record text of change 21 (results/dense_1g_grid45.json)."""
    G = DG45
    if not G or not G.get("sizes"):
        return "§8"
    g_ = G.get("grid_1g") or {}
    rf = G.get("refine") or {}
    bad, off = [], []
    for D, r in G["sizes"].items():
        r2 = rf.get(D) or {}
        if not r.get("ok") or not r2.get("ok", True):
            bad.append(f"{D} mm (dense check: {int(r['released'])} released, {int(r['unseated'])} tripod lost, {int(r['tilt_over'])} over-tilted, "
                       f"smallest seating margin {f(r['min_seat'][0])} N"
                       + (f"; refinement: {int(r2['n_fails'])} of {int(r2['n'])} failing, smallest {f(r2['min_seat'][0])} N" if r2 else "") + ")")
            c = r["min_seat"][1]
            if c:
                off.append(not (_on_grid(c["g_dir"], g_.get("tilt", ()), g_.get("az_step", 360)) and
                                _on_grid(c["cable_dir"], g_.get("cable_polar", ()), g_.get("cable_az_step", 360))))
    if not bad:
        return f"with the grid every {f(g_.get('az_step'))}° the tuned eyes passed the dense check and its refinement (§8)"
    return (f"with the grid every {f(g_.get('az_step'))}° (gravity) / {f(g_.get('cable_az_step'))}° (cable) the tuned eyes failed at "
            + "; ".join(bad)
            + ("; the worst combination is not a point of that grid" if off and all(off) else "") + " (§8)"
            + grid_eye_change(((G45L or {}).get("per_size") or {}), FINAL.get("per_size") or {})
            + (f"; preload {f((G45L or {}).get('link_preload'))} → {f(FINAL['link_preload'])} N"
               if G45L and abs(float(G45L.get("link_preload", 0)) - FINAL["link_preload"]) > 1e-9 else ""))


def grid_eye_change(ps0=None, ps1=None):
    """Eye movement between two per_size sets (default: change 19, the first Final -> the Final after change 19)."""
    if ps0 is None:
        ps0 = ((DP or {}).get("design") or {}).get("per_size") or {}
        ps1 = ((G45L or {}).get("per_size") or FINAL.get("per_size") or {})
    dy_ = [ps1[D]["link_y"] - ps0[D]["link_y"] for D in SIZES if D in ps0 and D in ps1]
    dx_ = [ps1[D]["link_x"] - ps0[D]["link_x"] for D in SIZES if D in ps0 and D in ps1]
    if not dy_:
        return ""
    if max(map(abs, dy_ + dx_)) < 1e-9:
        return ", eyes unchanged"
    return f", eyes moved Δy {rng(dy_)} mm, Δx {rng(dx_)} mm"


def grid_wire_change():
    """Link wire before and after change 19 (the Final after change 19: calc/final_layout_grid45.json)."""
    d0 = (DP or {}).get("design") or {}
    d1 = G45L or FINAL
    if not d0:
        return f"Ø{f(d1['wire_d'])} mm"
    return (f"Ø{f(d0.get('wire_d'))} mm / {d0.get('link_coils')} coils → Ø{f(d1['wire_d'])} mm / {d1['link_coils']} coils "
            f"({ls_stock_tag(d1['wire_d'])}), re-sized for the preload (§11)")


def joint_history():
    """Iteration-record text of the arm-joint change (results/weight.json: W1 and the pitch x torque scan)."""
    w1 = next((v for k, v in (WT or {}).items() if k.startswith("W1 ")), None)
    parts = []
    if w1 and w1.get("joints"):
        parts.append(f"the M2.5 weight option: serration engagement SF {f(min(j['SF_engage'] for j in w1['joints'].values()))}, "
                     f"insert pull-out SF {f(min(j['SF_pullout'] for j in w1['joints'].values()))} under the {FH} N handling load "
                     "with the preload scatter (§5, W1)")
    sc = [x for x in (WT or {}).get("pitch_torque_scan", []) if abs(x["pitch"] - FINAL["arm_screw_pitch"]) < 1e-9]
    if sc:
        hi = max(sc, key=lambda x: x["torque"])
        parts.append(f"{FINAL['arm_screw']} at {hi['torque']:.2f} N·m: insert pull-out SF {f(hi['SF_pullout'])} at the highest preload (§13)")
    return "; ".join(parts) or "§5, §13"


PAD_WORDS = {"T temporal": "temporal", "M mastoid": "mastoid", "P post-sup": "posterior-superior", "S root": "auricle-root saddle"}


def padn(name):
    """Plain name of a contact (support.contact_set names, e.g. "M mastoid" -> "mastoid")."""
    if not name:
        return "worst"
    for k, v in PAD_WORDS.items():
        if name.startswith(k):
            return v
    return name


def min_sf(rows):
    """(SF, where) of the lowest von Mises or interlayer SF in a list of section rows."""
    best = (math.inf, "")
    for x in rows:
        for k, lab in (("SF_vm", "vM"), ("SF_il", "interlayer")):
            if x[k] < best[0]:
                best = (x[k], f"{x['arm']}: {x['section']} ({lab})")
    return best


md = []
w = md.append

# ------------------------------------------------------------------------------------------------ header
w(f"# UMEH-2 — Engineering design report ({min(SIZES)}–{max(SIZES)} mm drivers)\n")
w("Universal Modular Ear-mounted Headphone, second design iteration. Scope: dynamic drivers of "
  f"**{', '.join(str(D) for D in SIZES[:-1])} and {SIZES[-1]} mm only**; nothing above {max(SIZES)} mm is designed or claimed.\n")
w("Every number in this report is written by `calc/make_report.py` from `results/*.json`, which `calc/run_all.py`, "
  "`calc/legs_liner.py`, `calc/tune_eye.py`, `calc/shakedown.py` and `calc/sweeps.py` compute. The CAD (`cad/umeh2.scad`) reads `cad/generated_params.scad` / "
  "`cad/params_<D>.scad`, which the same calculation writes, and the mass properties are integrated over the meshes that CAD "
  "exports — so the printed geometry is the calculated geometry, and the calculated masses are those of that geometry at the stated densities and fill factors (a printed part will scatter around them; weigh the first print). Re-run: "
  "`cd calc && python3 legs_liner.py && python3 tune_eye.py && python3 run_all.py && python3 shakedown.py && python3 sweeps.py && python3 figures.py && "
  "python3 build_stl.py && python3 bom.py && python3 make_report.py`.\n")
w("**What was NOT done, stated up front:** no finite-element analysis (structural or acoustic), no boundary-element analysis and "
  "no physical test was run. Structure is closed-form beam, joint and contact theory with Peterson stress-concentration factors; "
  "the ear attachment is a 6-DOF rigid-body model with elastic arms on compliant unilateral frictional contacts, solved by "
  "incremental energy minimisation without linearising the contact or friction laws (§6); acoustics is a lumped electro-mechano-acoustic model with exact baffled-piston radiation. §21 lists "
  "exactly where FEA/BEM or a test is needed. Driver Thiele/Small parameters, tissue properties and friction coefficients are "
  "literature ranges or assumptions and are tagged as such everywhere. Full precision is kept in the calculation; only final "
  "dimensions are rounded (§3 gives each rounding and its justification).\n")

w("## Source tags\n")
w(table(["tag", "meaning"], [["STD", "standard / handbook value (ISO, ASTM, Shigley, Peterson, Roark)"],
                             ["DS", "typical manufacturer datasheet (generic grade — your spool/part may differ)"],
                             ["LIT", "published test literature, approximate range"],
                             ["A", "engineering assumption — no reliable data; chosen conservatively; replace by measurement"],
                             ["C", "calculated in this report"], ["CAD", "measured on the CAD mesh (exact volume integration)"],
                             ["E", "estimate (order of magnitude, stated method)"],
                             ["EMP", "empirical relation (e.g. Gent E(Shore), Findley creep, nut factor)"],
                             ["SIM", "simulated — none: no FEA/BEM was run (§21)"],
                             ["M", "measured — none yet; the test plan in §22 produces them"]]))

# ------------------------------------------------------------------------------------------------ 1 summary
w("## 1. Summary\n")
if F:
    rows = []
    for D in SIZES:
        r = F[D]; s = r["support"]; c = r["criteria"]; mm = MM.get(D, {})
        dem = s.get("static_mu_demand") or {}
        onset = (s["5 g accidental"].get("onset_lambda") or {}).get("min")
        _sk = ((SK or {}).get("sizes", {}).get(D) or {}).get("A") or {}
        rows.append([f"{D} mm", r["mass"] * 1e3, r["com"][2] * 1e3, pf(all(v for k, v in c.items() if not k.startswith("2 g"))),
                     (_sk["root_p"] / 1e3 if _sk.get("ok") else "–"),
                     max(dem.values()) if dem else None,
                     100 * s["2 g dynamic"]["slip_fraction"], 100 * s["3 g severe"]["slip_fraction"], 100 * s["5 g accidental"]["slip_fraction"],
                     onset, min_sf(r["handling"]["sf"])[0], min_sf(r["arm_sf"]["5 g accidental"])[0],
                     mmax(mm.get("normal")), mmax(mm.get(DYNA)), mmax(mm.get("maximum"))])
    w("Final design, per driver size (driver masses and geometry are placeholders [A] until measured):\n")
    w(table(["driver", "mass/side g [CAD+DS]", "COM off skin mm [C]", "normal-use criteria [C]", f"auricle-root p in use kPa (≤ {PSUS}) [C]",
             "static μ demand / μ design [C]",
             "2 g: % combos released", "3 g: %", "5 g: %", "5 g onset λ min", f"{FH} N handling min SF", "5 g envelope min SF",
             "max driver g: normal (1 g grid)", f"max driver g: dynamic (≤ {DYNA_PCT} released)", "max driver g: max design"], rows))
    w(f"Definitions: *normal-use criteria* = all pads loaded at rest, sustained skin and auricle-root pressure ≤ {PSUS} kPa as donned (A), static friction demand ≤ design μ, "
      f"the 1 g grid, its dense check and the local refinement without gross slip, with the tripod kept and tilt ≤ {TILT_N}° (§8), and the link wire "
      f"within its criteria on the module (§11). *Max driver g*: 'normal' = the static criteria + the 1 g grid, 'dynamic' = that + the 2 g set, "
      f"'max design' = static hold + the 5 g structural envelope (§10); the dense check and its refinement run at the nominal driver only. "
      f"*Released* = no bounded equilibrium within "
      f"{REL} (gross slip). *Onset λ* = fraction of the 5 g load increment at which gross slip begins (§12). *Handling* = {FH} N at one "
      f"pad in any of {NDH} directions (§12). *Auricle-root p in use* = after the head-motion shakedown of the 1 g set (§6), the "
      f"sustained state once the headphone is worn. Required SF ≥ γM = {GM}.\n")
w("Headline findings (each is derived in the section named):\n")
w("@@HEADLINES@@\n")

# ------------------------------------------------------------------------------------------------ 2 inputs
w("## 2. Inputs and assumptions\n")
w("### 2.1 Materials\n")
rows = []
for nm, dct in (("PETG", mt.PETG), ("TPU 95A", mt.TPU), ("music wire", mt.WIRE), (f"silicone {mt.SILICONE_GRADE} (pad facing, link sleeve)", mt.SILICONE),
                (f"silicone {mt.SILICONE_GEL_GRADE} (saddle liner)", mt.SILICONE_GEL), ("brass", mt.BRASS), ("foam", mt.FOAM)):
    for k, v in dct.items():
        rows.append([nm, k, v.v, v.tag, v.note])
rows.append(["PETG", "partial factor γM", mt.GAMMA_M_PRINT.v, mt.GAMMA_M_PRINT.tag, mt.GAMMA_M_PRINT.note])
rows.append(["PETG", "sustained-load factor", st.K_SUSTAINED, "LIT", "creep rupture, 1e4 h"])
rows.append(["inserts", "partial factor γ_insert", mt.GAMMA_INSERT.v, mt.GAMMA_INSERT.tag, mt.GAMMA_INSERT.note])
rows.append(["screws", "nut factor K", mt.NUT_FACTOR_K.v, mt.NUT_FACTOR_K.tag, mt.NUT_FACTOR_K.note])
w(table(["material", "property", "value (SI)", "tag", "note"], rows))
w(table(["insert", "pull-out N (characteristic)", "tag", "note"], [[k, v.v, v.tag, v.note] for k, v in mt.INSERT_PULLOUT.items()]))
w(f"Music-wire strength: Sut = {mt.WIRE['Sut_A'].v / 1e6:g} MPa / d^{mt.WIRE['Sut_m'].v:g} (d in mm) [STD, ASTM A228, Shigley Table 10-4]. FDM anisotropy: in-layer strength "
  "S_xy, across-layer tension S_z and interlayer shear are separate allowables; every section check states which one applies from the "
  "part's print orientation (§20).\n")
w("### 2.2 Tissue, comfort thresholds and friction\n")
w(table(["quantity", "value", "tag", "note"], [[k, v.v, v.tag, v.note] for k, v in mt.TISSUE.items()]))
w(table(["pair", "μ low", "μ nominal", "μ high", "tag"], [[k, *v[0], v[1]] for k, v in mt.FRICTION.items()]))
w(f"Design friction = nominal / γ_μ = nominal / {lo.GAMMA_MU} [A]; the low and high values and several skin states are run as "
  "sensitivity (§9).\n")
w("### 2.3 Drivers (placeholders — measure and re-run)\n")
rows = []
for D, d in dz.DRIVERS.items():
    T = AC.get("ts", {}).get(str(D), {})
    rows.append([D, d["mount_d"], d["front_open"], d["rim_t"], d["depth"], d["rear_d"], d["mass"], T.get("Fs"), T.get("Mms", 0) * 1e3,
                 T.get("Sd", 0) * 1e4, T.get("Vas", 0) * 1e6, T.get("Qts"), T.get("Bl")])
w(table(["D mm", "rim OD mm [A]", "front open mm [A]", "rim t [A]", "depth [A]", "rear Ø [A]", "mass g [A]", "Fs Hz [A]",
         "Mms g [A]", "Sd cm² [C]", "Vas cm³ [C]", "Qts [A]", "Bl T·m [C]"], rows))
w(f"T/S basis [A]: D_eff = {ac.D_EFF_RATIO:g} D, Qms = {ac.QMS:g}, Qes = {ac.QES:g}, Re = {ac.RE:g} Ω, Le = {ac.LE * 1e6:g} µH; Mms/Fs anchored at "
  f"{'/'.join(str(k) for k in ac.TS_ANCHOR)} mm and interpolated (Mms linear, Fs log-linear in D). "
  "Cms = 1/((2πFs)² Mms), Rms = 2πFs Mms/Qms, Bl = √(2πFs Mms Re/Qes), Vas = ρc² Sd² Cms [C].\n")
w("### 2.4 Anthropometry [A/LIT]\n")
w(table(["quantity", "value mm"], [[k, v] for k, v in dz.ANTHRO.items()]))

# ------------------------------------------------------------------------------------------------ 3 geometry
w("## 3. Frame, architecture and final dimensions (with rounding)\n")
w("Frame: origin on the ring axis in the skin plane of the pads; x forward, y up, z lateral (away from the head); right side "
  "(left mirrors x). Architecture (Final): common cradle = PETG ring with the UMI-2 twist-lock + four arms (saddle, temporal, "
  "mastoid, posterior-superior) with serrated clamps; TPU pads (temporal and mastoid with a cast silicone facing); arched TPU saddle "
  "cap with a cast soft-silicone liner on the auricle root; driver module = baffle + cup (+ bonded rear felt) locked in the ring; occipital spring link clamped on "
  "the cup end at a module-specific eye; cable anchor + clip on the ring.\n")
if F:
    r = F["50"]; dd = r["derived"]
    rows = [["interface spigot / bore Ø", dd["spig_d"], dd["bore_d"], f"0.5 mm grid on the radius (FDM ±{tl.TOL['xy']:g} mm; the fit is set by the radial clearance, §17)"],
            ["ring OD", dd["ring_od"], "", "follows the groove + lip (C)"],
            ["tab radius / thickness", dd["tab_r"], dd["tab_t"], "C: insert pitch + walls; not rounded (derived)"],
            ["standoff skin → ring face", FINAL["standoff"], "", f"C: p95 pinna protrusion {dz.ANTHRO['pinna_protrusion_p95']:g} + {dz.PINNA_CLEAR:g} mm, 0.5 mm grid"],
            ["temporal pad angle / radius", FINAL["temporal_a"], FINAL["temporal_r"], "max–min layout search (§7), rounded 0.5°/0.5 mm; re-checked with the current model (§8)"],
            ["mastoid pad angle / radius", FINAL["mastoid_a"], FINAL["mastoid_r"], "same"],
            ["post-sup pad angle / radius", FINAL["post_a"], FINAL["post_r"], "same"],
            ["pad sizes T / M (a×b)", f"{FS['pad_t_a']:.1f}×{FS['pad_t_b']:.1f} / {FS['pad_m_a']:.1f}×{FS['pad_m_b']:.1f}",
             f"P {FS['pad_p_a']:.1f}×{FS['pad_p_b']:.1f}", f"pad_scale {FINAL['pad_scale']} (0.1 steps) on the Base pads: skin pressure ≤ {PSUS} kPa"],
            [f"pad height (TPU {100 * mpz.PRINT['pad_temporal'][3]:g} % gyroid) / silicone facing", FINAL["pad_h"], FINAL["pad_face_t"], "§18 sweep / §9 (0.1 mm: casting)"],
            ["saddle arch R / half-angle", FINAL["arch_R"], FINAL["arch_phi"], "A (anthropometry) + §18 sweep"],
            [f"saddle liner (silicone {mt.SILICONE_GEL_GRADE})", FINAL.get("saddle_liner_t", 0.0), f"E {f(mt.SILICONE_GEL['E'].v / 1e3)} kPa",
             liner_reason()],
            [f"link preload on the {an.LINK_REF_D} mm module (N)", FINAL["link_preload"], "",
             ((f"eye tune (§7): the lowest of the preload levels (layout {f(_ti['preload_layout'])} N + {f(_ti['preload_step'])} N steps) "
               "at which every module has an eye meeting the tune's normal-use criteria (static + the 1 g grid) that also passes "
               "the dense check and its local refinement (stage 4); P(D) per module below") if _ti.get("all_modules_pass") else
              "eye tune (§7): no preload level gave every module a passing eye; the last level tried is used (§7, §8)") if _ti.get("preload_levels")
             else "layout search (§7), 0.1 N; P(D) per module below"],
            ["link wire Ø / apex coils", FINAL["wire_d"], FINAL["link_coils"], "stock music-wire Ø (" + ls_stock_tag(FINAL["wire_d"]) + ("); for each Ø the fewest apex turns that meet every link criterion on all five modules at their eyes, then the Ø with the largest smallest margin (§11)"
             if (L or {}).get("Final", {}).get("chosen_modules") else "); no stock wire meets every link criterion on all five modules: sized on the 50 mm module only (§11)")],
            ["arm bar / leg / foot t", FINAL["bar_t"], f"{FINAL['leg_t']} / {FINAL['foot_t']}",
             f"bar: handling SF at −{tl.TOL['xy']:g} mm tolerance (§5, §12); legs and liner chosen together (§6); 0.1 mm"],
            ["arm screws / torque N·m", FINAL["arm_screw"], FINAL["arm_torque"], "§13: insert pull-out at the highest preload of the torque scatter (torque-driver resolution 0.01 N·m)"],
            ["arm-screw insert pitch / wave washer", FINAL["arm_screw_pitch"], f"≥ {f(FINAL['arm_washer'][0])} N flat, ≤ {f(FINAL['arm_washer'][1] / 1e3)} N/mm",
             "§13: pry lever of the clamp (0.5 mm); washer keeps the serrations engaged after PETG creep"],
            ["rear felt: hole on the eye boss / PSA rim", f"Ø{f(dd['felt_hole_d'])}", FINAL["felt_psa_w"], f"hole {f(dd['eye_boss_d'] - dd['felt_hole_d'])} mm under the boss Ø (seals, §17); rim outside the grille (§13)"],
            ["anchor screws / torque N·m", FINAL["anchor_screw"], FINAL["anchor_torque"], "§14"],
            ["serration pitch / height", FINAL["serr_p"], FINAL["serr_h"], "3 × nozzle-width rule (C)"],
            ["cup wall", FINAL["cup_wall"], "", f"{1 + int((FINAL['cup_wall'] - mpz.LINE_W * 1e3) / (mpz.LINE_W * 1e3 - mpz.LAYER * 1e3 * (1 - math.pi / 4)) + 1e-9)} perimeters of {mpz.LINE_W * 1e3:g} mm lines (§5, §20)"],
            ["driver pocket clearance / side", FINAL["driver_pocket_clr"], "", "centres the MC band of the fit (§17), 0.01 mm"]]
    w(table(["item", "value", "value 2", "rounding / source"], rows))
    rows = [[D, F[D]["eye"]["link_x"], F[D]["eye"]["link_y"], F[D]["eye"]["r_max"], F[D]["link"]["P"],
             F[D]["derived"]["cup_ro"], F[D]["derived"]["cup_h"], F[D]["derived"]["z_cuptop"]] for D in SIZES]
    w("Per-module values (the cradle and link are common; each module has its own eye and therefore its own preload P(D) = "
      "P_ref + k_side·Δz_cuptop, §7):\n")
    w(table(["D", "eye x mm", "eye y mm", "eye r_max mm", "P(D) N [C]", "cup R_o mm", "cup h mm", "cup top z mm"], rows))

# ------------------------------------------------------------------------------------------------ 4 iteration
w("## 4. Iteration record: Design A → Design B → Final\n")
rows = []
if A and B:
    for nm, R in (("A (UMEH-1 mass on B geometry)", A), ("B", B)):
        s = R["support"]
        rows.append([nm, R["mass"] * 1e3, pf(s["static"]["ok"]), s["1 g normal"]["slip_fraction"] * 100, s["1 g normal"]["worst_tilt_deg"],
                     s["2 g dynamic"]["slip_fraction"] * 100, pf(R["criteria"].get("1 g: no gross slip", False))])
if F:
    s = F["50"]["support"]
    rows.append(["Final", F["50"]["mass"] * 1e3, pf(s["static"]["ok"]), s["1 g normal"]["slip_fraction"] * 100, s["1 g normal"]["worst_tilt_deg"],
                 s["2 g dynamic"]["slip_fraction"] * 100, pf(F["50"]["criteria"].get("1 g: no gross slip", False))])
w(table(["design (50 mm)", "mass g", "static hold", "1 g: % released", "1 g worst tilt deg", "2 g: % released", "1 g no-slip"], rows))
w("""Each change was forced by a calculated failure, not by taste:

| # | change | failure that forced it | evidence |
|---|---|---|---|
| 1 | Module re-sized for 40–60 mm only (interface Ø from the 60 mm driver + insert walls) | UMEH-1 interface Ø118 served 40–600 mm: mass | §5 |
| 2 | Link eye moved from the mastoid pad to the cup end, one eye position per module | preload through the lowest contact gives no restoring moment → tilt/slide under 1 g; heavier modules need the eye higher | §6, §7 |
| 3 | Saddle bar curved to the auricle-root arch (R, ±φ) | straight bar: fore–aft held by friction only → gross slip | §6 |
| 4 | Posterior-superior pad added; pads re-positioned and enlarged; preload re-set | support polygon must contain the preload line with margin; skin pressure ≤ {psus} kPa | §7, §18 |
| 5 | Helix contact no longer relied on | its stiffness is unknown ({kh0:g}–{kh1:g} N/m [A]) | §9 |
| 6 | Serrated arm clamps, low torque, wave washers | friction clamp loses most of its preload by creep; insert pull-out caps preload | §13 |
| 7 | Link wire re-derived (Ø, apex coil turns) | higher preload + longer path around the module | §11 |
| 8 | Cable clip made a routing guide; 2-pin plug is the fuse; anchor keeps M3 | interference grip cannot be controlled within FDM tolerance; M2.5 anchor inserts fail at the fuse load | §14 |
| 9 | Solver replaced by a convex incremental energy minimisation (residual checked); donning sequences A/B | the earlier return-mapping solver stalled at its round-off floor and reported false releases | §6 |
| 10 | Cast silicone facing on the temporal and mastoid pads | static friction demand of the mastoid pad above the TPU design μ | §9 |
| 11 | Arm bar {b0} → {b1} mm; feet {f0} → {f1} mm; cup wall {c0} → {c1} mm | {fh} N handling load at one pad; then weight optimisation | §5, §12 |
| 12 | Ring tab extended to a full round end around the outer insert | the tab ended at the outer insert centre (half the insert outside the part) — CAD defect found by the mesh check | §20 |
| 13 | Twist lock: rigid floor + foam anti-rattle strips instead of a squeezed TPU gasket | gasket squeeze under the FDM stack-up spans zero to over-tight | §13, §17 |
| 14 | Arm joint back to {screw} (inserts {pitch} mm apart) at {tq} N·m; tightening scatter carried explicitly (nut factor {klo}–{khi}); cable anchor at {atq} N·m | {j14} | §5, §13 |
| 15 | Arms modelled as elastic beams in series with the contacts; legs {l0} → {l1} mm | the rigid-arm assumption was false: in-plane bending of the mastoid leg let the pad shed weight onto the auricle root (root pressure per leg thickness: §5 weight table, §6 lever table) | §5, §6, §12 |
| 16 | Link-eye boss restored inside the cup; rear felt bonded by a PSA rim instead of a press-fit ring | CAD defect: the bore cut removed the boss above the {ce:g} mm cup end, leaving the {il:g} mm eye insert {ce:g} mm of material; the PETG ring's sustained hoop SF was below 1 at the upper interference tolerance and it would clash with the boss | §13, §20 |
| 17 | Solver: Newton steps below the floating-point resolution of Π accepted on the model's word | with the arm degrees of freedom the energy line search stalled at the round-off floor of Π instead of converging | §6 |
| 18 | {liner} mm soft silicone liner ({gel}) cast into the saddle bar's bearing face | {nl18} | §6 |
| 19 | 1 g load set made a deterministic grid (edges of the tilt and cable cones included) with a dense check; link preload tuned together with the eyes ({p0} → {p1} N){eyes19}; link wire {w19} | {nl19} | §7, §8, §11 |
| 20 | Solver: a load increment whose minimisation stops at a bounded position is cut in halves (up to {cuts} times) before a release is declared | {nl20} | §6, §8 |
| 21 | 1 g grid azimuth steps halved; local refinement added to the dense check; the eye tune verifies its choice on both (stage 4) and was re-run | {nl21} | §7, §8 |
""".format(cuts=sp.Model.MAX_CUTS, nl20=stall_history(), nl21=grid45_history(), p0=f(_ti.get("preload_layout")),
           p1=f((G45L or FINAL)["link_preload"]), eyes19=grid_eye_change(), w19=grid_wire_change(), nl19=grid_history(),
           liner=FINAL.get("saddle_liner_t"), psus=PSUS, fh=FH, gel=mt.SILICONE_GEL_GRADE, kh0=sp.K_HELIX_RANGE[0], kh1=sp.K_HELIX_RANGE[1],
           ce=FINAL["cup_end_t"], il=mt.SCREW["M2.5"]["insert_L"],
           b0=dz.BASE["bar_t"], b1=FINAL["bar_t"], f0=dz.BASE["foot_t"], f1=FINAL["foot_t"], c0=dz.BASE["cup_wall"], c1=FINAL["cup_wall"],
           l0=dz.BASE["leg_t"], l1=FINAL["leg_t"], screw=FINAL["arm_screw"], pitch=f"{FINAL['arm_screw_pitch']:g}", tq=f"{FINAL['arm_torque']:.2f}",
           atq=f"{FINAL['anchor_torque']:.2f}", klo=f"{mt.NUT_FACTOR_K_RANGE[0].v:.2f}", khi=f"{mt.NUT_FACTOR_K_RANGE[1].v:.2f}", j14=joint_history(),
           nl18=no_liner_history()))
_sa4 = [((SK or {}).get("sizes", {}).get(D) or {}).get("A") or {} for D in SIZES]
_sa4 = [x for x in _sa4 if x.get("ok")]
if _sa4:
    _pu4 = [x["root_p"] for x in _sa4]
    w(f"After the last iteration the Final was checked for the state in use (§6, frictional shakedown under the 1 g head-motion set): "
      f"the auricle root then carries {rng([x / 1e3 for x in _pu4])} kPa"
      + (f", above the {PSUS} kPa sustained target that the leg and liner changes (15, 18) had met as donned. The lever study there finds no change "
         "within this concept that meets it, so the iteration stops here with that requirement open." if max(_pu4) > mt.TISSUE["p_sustained"].v
         else f", within the {PSUS} kPa sustained target.") + "\n")

# ------------------------------------------------------------------------------------------------ 5 mass
w("## 5. Mass properties from the CAD, weight breakdown and optimisation\n")
w("Method: every part is exported by OpenSCAD in its assembled position; volume V, centroid and the full inertia tensor are "
  "integrated exactly over the triangle mesh (signed tetrahedra, divergence theorem) [CAD]. Printed mass m = ρ f V with the "
  "shell + infill fill factor f = s + (1 − s)·infill, s = min(1, A_surf·n_perim·w_line / V) (A_surf from the mesh) [C]. Hardware "
  "are point masses at their CAD positions [DS]. The driver is a mass-equivalent solid of its CAD envelope scaled to the driver "
  "mass [A]. The COM used by every load case is this CAD COM.\n")
if F:
    r = F["50"]
    rows = [[p["part"], p["m"] * 1e3, p.get("f"), p["c"][0] * 1e3, p["c"][1] * 1e3, p["c"][2] * 1e3, p["src"]] for p in r["parts"]]
    w("Final, 50 mm (one side):\n")
    w(table(["part", "mass g", "fill f", "x mm", "y mm", "z mm", "source"], rows))
    rows = []
    for D in SIZES:
        r = F[D]; I = r["I"]
        rows.append([D, r["mass"] * 1e3, r["com"][0] * 1e3, r["com"][1] * 1e3, r["com"][2] * 1e3, I[0][0] * 1e9, I[1][1] * 1e9, I[2][2] * 1e9,
                     I[0][1] * 1e9, I[0][2] * 1e9, I[1][2] * 1e9])
    w(table(["D", "M g", "x̄ mm", "ȳ mm", "z̄ mm", "Ixx g·mm²", "Iyy", "Izz", "Ixy", "Ixz", "Iyz"], rows))
    w("![mass](fig/mass_breakdown.png)\n")
if WT:
    w("Weight optimisation at 50 mm — each option alone against the pre-optimisation baseline (CAD mass), with the check it moves:\n")
    b_ch = WT["baseline"].get("change") or {}
    b_lab = ("baseline (" + (f"{b_ch.get('arm_screw', '')} arm screws {b_ch['arm_torque']:.2f} N·m, cup wall {b_ch['cup_wall']:g}, "
                             f"legs/feet {b_ch['leg_t']:g}/{b_ch['foot_t']:g}" if b_ch else "pre-optimisation values")
             + "; saddle liner as the Final)")
    rows = [[b_lab, WT["baseline"]["mass"] * 1e3, "",
             f"handling SF {f(WT['baseline']['handling'][0])} ({WT['baseline']['handling'][1]}: {WT['baseline']['handling'][2]})"
             + (f"; auricle-root p at 60 mm {f(WT['baseline']['root_p_60'] / 1e3)} kPa" if WT["baseline"].get("root_p_60") else ""), ""]]
    for k, v in WT.items():
        if not k.startswith("W"):
            continue
        chk = ""
        if "handling" in v:
            chk = f"handling SF {f(v['handling'][0])} ({v['handling'][1]}: {v['handling'][2]})"
        if v.get("root_p_60") is not None:
            chk += f"; auricle-root p at 60 mm {f(v['root_p_60'] / 1e3)} kPa (≤ {PSUS})"
        if "pullout_SF_preload" in v:
            chk = (f"F_i {f(v['Fi_range'][0])}–{f(v['Fi_range'][1])} N (torque scatter), insert pull-out SF {f(v['pullout_SF_preload'])} "
                   "at the highest preload alone")
        if "joints" in v:
            chk += (f"; {FH} N handling: min SF engage {f(min(j['SF_engage'] for j in v['joints'].values()))}, "
                    f"min SF pull-out {f(min(j['SF_pullout'] for j in v['joints'].values()))} (≥ 1)")
        if "anchor" in v:
            a_ = v["anchor"].get("clip + plug in series (upper)", {})
            chk += f"; anchor insert SF {f(a_.get('SF_initial'))} at the upper fuse load"
        if "eye_r_max" in v:
            chk = f"{f(v['perimeters'])} perimeters; eye r_max {f(v['eye_r_max'])} mm"
        if "shell_fraction" in v:
            chk = f"ring shell fraction {f(v['shell_fraction'])}"
        rows.append([k, v["mass"] * 1e3 if "mass" in v else "", v["delta"] * 1e3, chk, w_verdict(v)])
    fj = WT["final"].get("joints") or {}
    _adp = [k.split()[0] for k, v in WT.items() if k.startswith("W") and w_verdict(v).startswith("adopted")]
    rows.append([f"Final ({' + '.join(_adp) + ', ' if _adp else ''}{FINAL['arm_screw']} arm screws at {FINAL['arm_torque']:.2f} N·m, "
                 f"{FINAL.get('anchor_screw') or FINAL['arm_screw']} anchor screws at {FINAL['anchor_torque']:.2f} N·m, tab fix, saddle liner)",
                 WT["final"]["mass"] * 1e3, WT["final"]["delta"] * 1e3,
                 f"handling SF {f(WT['final']['handling'][0])} ({WT['final']['handling'][1]}: {WT['final']['handling'][2]})"
                 + (f"; auricle-root p at 60 mm {f(WT['final']['root_p_60'] / 1e3)} kPa" if WT["final"].get("root_p_60") else "")
                 + (f"; joints min SF engage {f(min(j['SF_engage'] for j in fj.values()))}, pull-out {f(min(j['SF_pullout'] for j in fj.values()))}" if fj else ""), ""])
    w(table(["option", "mass g", "Δ g", "check moved", "decision"], rows))
    if "bar_t_tolerance" in WT:
        bt_ = WT["bar_t_tolerance"]; b0_ = FINAL["bar_t"]; tol_ = WT.get("bar_t_print_tol", tl.TOL["xy"]); gm_ = mt.GAMMA_M_PRINT.v
        stp_ = WT.get("bar_t_step", 0.1)
        sf_tol = (bt_.get(f"{b0_ - tol_:.2f}") or [None])[0]; sf_nxt = (bt_.get(f"{b0_ - stp_ - tol_:.2f}") or [None])[0]
        txt_ = ""
        if sf_tol is not None and sf_nxt is not None:
            txt_ = (f" At the −{tol_:g} mm XY print tolerance the {b0_:g} mm bar keeps SF {f(sf_tol)} "
                    f"({'≥' if sf_tol >= gm_ else '<'} γM {GM}); one {stp_:g} mm step thinner, its tolerance section gives {f(sf_nxt)} "
                    f"({'≥' if sf_nxt >= gm_ else '<'} γM)"
                    + (f", so the bar is the thinnest {stp_:g} mm step that keeps γM at the tolerance." if sf_tol >= gm_ > sf_nxt else
                       ": the bar is NOT the thinnest step that keeps γM at the tolerance." if sf_nxt >= gm_ else
                       ": the bar does NOT keep γM at the tolerance."))
        w(f"Arm bar thickness vs the {FH} N handling load: " + ", ".join(
            f"{k} mm → SF {f(v[0])}" for k, v in bt_.items()) + "." + txt_ + "\n")

# ------------------------------------------------------------------------------------------------ 6 statics
w("## 6. Ear attachment — the statically indeterminate frictional contact model\n")
TSV = st.T_SERVICE.rstrip("C")
N_NODE = sum(6 if a_ == "saddle" else 3 for a_ in an.ARMS_OF["F"])
N_CF = len(an.support_model(FINAL, 50)[2])
w(f"""The ring is a rigid body; each arm is an elastic beam (foot, leg and bar with axial, both shear, torsion and both bending
compliances, E and G at {TSV} °C, built in at its clamp) in series with its contacts, which are compliant, **unilateral** and
frictional; plus the occipital link (lateral spring k_side with preload P, small in-plane stiffness {sp.K_LINK_T:g} N/m). An arm carrying one
pad adds a 3-DOF node at the pad contact with stiffness K = (L C_tip Lᵀ)⁻¹; the saddle arm (both root zones and the scalp contact
on one cap) adds a 6-DOF node at its tip with K = C_tip⁻¹ (C_tip: unit-load method over the arm centreline,
`structure.arm_tip_compliance`; L maps the tip motion to the contact point). Generalised displacement q = [u, θ, arm nodes]
(6 + {N_NODE} DOF in the Final); for contact i with normal n_i and lever r_i the row j_i = [n_i, r_i × n_i, n_i·L_i], compression
δ_i = −j_i·q, tangential slip t_i = J_t,i q. The problem is statically indeterminate ({N_CF} contacts in the Final × 3 force components +
link against 6 equations), so the load sharing follows from compatibility and the stiffness of each contact in series with its
arm — no support is assumed to carry an equal share. The arm flexibility matters (computed below, "What sets the auricle-root
load", and §12 table of arm vs contact compliance).

**Solution (per load step):** the incremental potential

    Π(q) = ½ qᵀ K_L q − q·W + Σ_i ½ k_n,i ⟨δ_i⟩₊² + Σ_i H_i(|J_t,i q − s_i|)

is minimised, where ⟨·⟩₊ keeps compression only (unilateral contact), s_i is the accumulated slip and H is the Huber function
of the tangential spring with the friction bound g_i = μ F_n,i (stick ½ k_t t², slide g t − g²/2k_t). For a given friction bound
Π is convex and C¹, so a stationary point is its global minimum and satisfies all six equilibrium equations ΣF = 0, ΣM = 0
together with the contact and friction laws; the printed residual is the check. The friction bound follows F_n by a fixed point (Tresca → Coulomb). Newton steps are truncated at
the first contact or stick/slip change (backtracking only as a safeguard; a step whose predicted energy change is below the
floating-point resolution of Π is taken on the model's word and the gradient decides convergence); the load is applied in {sp.Model.N_STEPS}
ramp steps with a return mapping of the slip. **Gross slip /
release** = no bounded minimiser (the minimisation runs away beyond {3 * sp.DISP_MAX * 1e3:g} mm or {3 * sp.ROT_MAX:g}°), or the converged
minimiser beyond {sp.DISP_MAX * 1e3:g} mm or {sp.ROT_MAX:g}° (the cradle has left its seat). A minimisation that stops at a bounded position
without converging (line search out of representable decrease, iteration or Coulomb fixed-point limit) is a numerical failure of the
increment, not a release: that increment is cut in halves, solved in turn from the last converged state, down to 1/{2 ** sp.Model.MAX_CUTS} of a
step (change 20); one that still fails is counted as a release and flagged as numerical.

**Donning:** a head-mounted cradle is put on by hand, so the static state depends on the sequence. A: the hand holds the cradle
in place while the link is clamped (the preload settles without friction), then lets go — the weight is added with friction
active (conservative for slip; base state of every load case). B: the cradle is hung on the ear root first, then clamped — the
upper bound of the root (saddle) load. Both are reported.

Contact stiffness = pad core in series with the facing and the tissue: k = 1/(h_core/(E_core A) + t_face/(E_face A) + t_tissue/(E_tissue A)),
E_core = {mt.TPU_PAD_EFF['infill15'].v:g}·E_TPU ({100 * mpz.PRINT['pad_temporal'][3]:g} % gyroid [LIT]), A = {100 * sp.PAD_AREA_FRAC:g} % of the pad ellipse [A]; k_t = {sp.KT_RATIO:g} k_n [A] (below the Mindlin
ratio 2(1−ν)/(2−ν) = {2 * (1 - 0.5) / (2 - 0.5):.2f} of an incompressible half-space, ν = 0.5, for the compliant skin shear layer). Saddle: two bearing zones on the auricle-root arch at ±φ, normals tilted fore/aft; each zone is the TPU cap wall,
the cast soft-silicone liner and the root tissue in series, k = 1/(t_cap/(E_cap A) + t_L/(E_c A) + t_root/(E_root A)). The liner
is a thin, nearly incompressible layer bonded to the cap and gripping the skin, so its compression modulus is E_c = E (1 + 2 k S²)
(Gent–Lindley, k = 1 at the incompressible limit, the stiffer end), S = w l / (2 (w + l) t_L) for the loaded patch w × l; E = 3 σ₁₀₀ / 1.75
from the datasheet 100 % modulus (neo-Hookean) [DS → C]. The liner makes the root contact silicone on skin.

Pressure: the {PSUS} kPa sustained target is applied to the MEAN contact pressure F_n/A [A: design convention]. The dome centre
carries more: a paraboloid on a thin soft layer over bone (Winkler bed, p = k(δ − r²/2R)) peaks at {sp.PEAK_FACTOR:g} × the mean [C] (a Hertz
half-space would give 1.5). Peaks are reported in every table; where they exceed {PSUS} kPa that is a comfort risk to check in wear
trials, not a pass.
""")
if F:
    rows = [[c["name"], c["r"][0] * 1e3, c["r"][1] * 1e3, c["r"][2] * 1e3, f"({c['n'][0]:.2f}, {c['n'][1]:.2f}, {c['n'][2]:.2f})", c["k"], c["area"] * 1e6, c["mu"], c["mu_key"]]
            for c in F["50"]["contacts"]]
    w(table(["contact", "x mm", "y mm", "z mm", "normal", "k_n N/m [C]", "area mm² [A]", "μ design", "pair"], rows))
    for D in ("40", "50", "60"):
        s = F[D]["support"]["static"]
        if not s["ok"]:
            w(f"Static {D} mm: **no equilibrium**.\n")
            continue
        w(f"Static, head upright, 1 g, Final {D} mm, donning A — link force ({', '.join(f(x) for x in s['link_force'])}) N, rotation "
          f"({', '.join(f(math.degrees(x)) for x in s['q'][3:6])}) deg, equilibrium residual {f(s['residual'])} (N, N·m):\n")
        w(table(["contact", "Fn N", "Ft N", "μ required", "p mean kPa", "p peak kPa", "sliding"],
                [[x["name"], x["Fn"], x["Ft"], x["mu_req"], x["p_mean"] / 1e3, x["p_peak"] / 1e3, str(x["slipping"])] for x in s["contacts"]]))
    rows = []
    for D in SIZES:
        sb = F[D]["support"].get("static_B", {})
        if sb.get("ok"):
            root = [x for x in sb["contacts"] if x["name"].startswith("S root")]
            skin = [x for x in sb["contacts"] if not x["name"].startswith("S root")]
            rows.append([D, sum(x["Fn"] for x in root), max(x["p_mean"] for x in root) / 1e3, max(x["p_peak"] for x in root) / 1e3,
                         max(x["p_mean"] for x in skin) / 1e3])
        else:
            rows.append([D, "–", "–", "–", str(sb.get("reason", "no equilibrium"))])
    w("Donning sequence B (hung on the ear root, then clamped) — the most root load a donning sequence gives (head motion then "
      "moves the load further, see the shakedown below):\n")
    w(table(["D", "root ΣFn N", "root p mean kPa", "root p peak kPa", "max skin p kPa"], rows))
    p_s = mt.TISSUE["p_sustained"].v
    over_b = [D for D in SIZES if F[D]["support"].get("static_B", {}).get("ok")
              and max(x["p_mean"] for x in F[D]["support"]["static_B"]["contacts"] if x["name"].startswith("S root")) > p_s]
    if over_b:
        w(f"In sequence B the mean root pressure exceeds the {f(p_s / 1e3)} kPa sustained target at {', '.join(over_b)} mm even "
          "with the liner, so the donning instruction is clamp first, then let go (sequence A). Neither donned state lasts once the "
          "head moves: see *The sustained state in use* at the end of this section.\n")
    else:
        w(f"With the liner the mean root pressure stays within the {f(p_s / 1e3)} kPa sustained target in sequence B as well; "
          "clamp-first donning (sequence A) is still the instruction, because it is the base state of every load case.\n")
if RL:
    w("**What sets the auricle-root load.** At rest (donning A) the weight is shared by compatibility: the root zones carry it by "
      "normal force, the pads by their tangential springs through the arms. The root's share therefore follows its normal stiffness "
      "against the pads' tangential stiffness, and the soft-tissue layers dominate both, so stiffer arms move it little. Every row "
      "keeps the Final CAD mass properties of its size; static, head upright:\n")
    rows = []
    for r_ in RL["rows"]:
        a, b = r_.get("55", {}), r_.get("60", {})
        if not b.get("ok"):
            rows.append([r_["variant"], "–", "–", "–", "–", "–", "no equilibrium"]); continue
        rows.append([r_["variant"], a.get("root_p", float("nan")) / 1e3, b["root_p"] / 1e3, 100 * b["root_Fy"] / b["weight"],
                     b["skin_p"] / 1e3, f"{f(b['mu_demand'])} ({padn(b['mu_pad'])})", pf(b["root_p"] <= mt.TISSUE["p_sustained"].v and (b["mu_demand"] or 9) <= 1.0)])
    w(table(["variant", "root p 55 mm kPa", "root p 60 mm kPa", "root share of the weight % (60)", "max skin p kPa (60)",
             "static μ demand (60)", f"60 mm: root ≤ {f(mt.TISSUE['p_sustained'].v / 1e3)} kPa and μ ≤ 1"], rows))
    fin = next(r_ for r_ in RL["rows"] if r_["variant"].startswith("Final"))["60"]
    nol = next(r_ for r_ in RL["rows"] if r_["variant"].startswith("no liner (Final"))["60"]
    rig = next(r_ for r_ in RL["rows"] if r_["variant"] == "no liner, arms rigid")["60"]
    w(f"With rigid arms the root would carry {f(100 * rig['root_Fy'] / rig['weight'])} % of the weight instead of "
      f"{f(100 * nol['root_Fy'] / nol['weight'])} % (no liner, 60 mm) — but the mastoid pad would then need "
      f"{f(rig['mu_demand'])} × its design friction: the arm compliance is not a free error. The liner lowers the root share to "
      f"{f(100 * fin['root_Fy'] / fin['weight'])} % and moves the difference onto the pads' friction; the Final therefore uses the "
      f"thinnest liner that leaves a {RM} % root margin at 60 mm ({FINAL.get('saddle_liner_t')} mm). The temporal-pad row is the "
      f"model's answer for a pad that is fully backed; with the present {FINAL['arm_w']:g} mm wide foot the extra area would not carry load, so it would "
      "need a PETG backing plate (and it would reach the zygomatic arch).")
    p_s = mt.TISSUE["p_sustained"].v
    thin = [r_["variant"] + f" ({f(100 * (1 - r_['60']['root_p'] / p_s))} %)" for r_ in RL["rows"]
            if r_["60"].get("ok") and not r_["variant"].startswith(("Final", "liner "))
            and 0 <= 1 - r_["60"]["root_p"] / p_s < RM_]
    if thin:
        w(f" Rows that pass with less than {RM} % root margin at 60 mm were not taken, because the tissue stiffnesses behind the "
          "share are literature values [A]: " + "; ".join(thin) + ".")
    w(" Rows that add material (thicker legs or bar) keep the Final mass properties, so they are optimistic by their own added "
      "mass.")
    lsc = RL.get("no_liner_layout_scan", [])
    lok = [r_ for r_ in lsc if r_["feasible"] and r_["60"].get("ok")]
    if lok:
        b_ = min(lok, key=lambda r_: r_["60"]["root_p"])
        angs_ = sorted({abs(r_["delta"]) for r_ in lsc if r_["key"].endswith("_a") and r_.get("delta") is not None})
        rads_ = sorted({r_["delta"] for r_ in lsc if r_["key"].endswith("_r") and r_.get("delta") is not None})
        bnd_ = any(r_.get("delta", 0) is None for r_ in lsc)
        chg_ = (f"each pad angle ±{'/'.join(f'{a_:g}' for a_ in angs_)}°, each radius {'/'.join(f'{r2:+g}'.replace('-', '−') for r2 in rads_)} mm"
                + (" or up to its search bound" if bnd_ else "")) if (angs_ or rads_) else "see results/root_levers.json"
        w(f" Single changes of the pad layout without the liner ({chg_}; "
          f"{len(lok)} of {len(lsc)} inside the layout constraints of §7) give at best {f(b_['60']['root_p'] / 1e3)} kPa at 60 mm "
          f"({b_['key']} {f(b_['final'])} → {f(b_['value'])}, static μ demand {f(b_['60']['mu_demand'])}; all rows in "
          "results/root_levers.json).")
    ns = RL.get("no_liner_eye_scan", {}).get("60", {})
    if ns.get("min_root_p"):
        w(f" Without the liner no eye position on the 60 mm cup ({ns['n_eyes']} positions, {ns.get('grid_mm', 4.0):g} mm grid) brings the root below "
          f"{f(ns['min_root_p'] / 1e3)} kPa.")
    w("\n")
if LL:
    w("**Arm legs and saddle liner, chosen together** (`calc/legs_liner.py`, results/legs_liner.json). Both move weight between the "
      "auricle root and the pads' friction: thinner legs send it to the root, a thicker liner sends it to the pads. Every pair got its "
      f"own CAD mass properties and the static criteria of the eye tune on the {_gs[0] if _gs else 4.0:g} mm eye grid of the "
      f"{' and '.join(str(D_) for D_ in LL['sizes'])} mm cups (where the root "
      "limit binds). Cells: smallest static margin at the best eye, worse of 55/60 mm (root / friction margin in brackets; ≥ 0 "
      f"passes, the liner rule asks ≥ {RM} % on the root):\n")
    by = {(p["leg_t"], p["liner_t"]): p for p in LL["pairs"]}
    rows = []
    for leg in LL["legs"]:
        row = [f"legs {leg:g} mm"]
        for t in LL["liners"]:
            p = by[(leg, t)]
            bs = [p["sizes"][str(D)]["best"] for D in LL["sizes"] if p["sizes"][str(D)]["best"]]
            if not bs:
                row.append("no equilibrium"); continue
            wb = min(bs, key=lambda b: b["prim"])
            row.append(f"{f(100 * wb['prim'])} % ({f(100 * min(b['m']['static root p'] for b in bs))} / "
                       f"{f(100 * min(b['m']['static friction'] for b in bs))})" + (" ◀" if p.get("liner_rule") else ""))
        rows.append(row)
    w(table(["legs \\ liner"] + [f"{t:g} mm" for t in LL["liners"]], rows))
    _llA = any("n_pass_1g" in (p.get("full") or {}).get(str(D), {}) for p in LL["pairs"] for D in LL["sizes"])
    w(f"◀ = the liner rule for that leg thickness (thinnest liner with ≥ {RM} % root margin at both sizes). Those pairs were then run "
      + ("through the eye tune's evaluation (static + its 1 g set) at every eye that meets the static criteria with the "
         f"{RM} % root margin, and its full evaluation (+ the reduced 2 g set) at the {LL['max_eyes']} best eyes of each size that meet normal use"
         if _llA else
         "through the eye tune's full evaluation (static + its 1 g set + the reduced 2 g set) at every eye that meets the static "
         f"criteria with the {RM} % root margin (at most {LL['max_eyes']} per size)")
      + (f", at a link preload of {f(LL['link_preload'])} N"
         + (f" with the link wire the tune uses at that preload (Ø{f(LL['wire_d'])} mm, {LL['link_coils']} coils)" if LL.get("wire_d") else "")
         + f" and the 1 g grid of {LL['sets']['1 g']['cases']} combinations"
         + ("" if abs(float(LL["link_preload"]) - float(FINAL["link_preload"])) < 1e-9 else
            f" (the tune then moved the preload to {f(FINAL['link_preload'])} N; the Final re-checks the liner with its own preload "
            "and eyes, §6 root-lever table)")
         if LL.get("sets") else
         f"; this study ran before iteration change 19 (§4), with the first tune's quasi-uniform 1 g sample at the layout preload of "
         f"{f(_ti.get('preload_layout'))} N, and the Final re-checks the liner with its own preload and eyes (§6 root-lever table)")
      + ":\n")
    rows = []
    for p in LL["pairs"]:
        if not p.get("liner_rule"):
            continue
        cells = [f"{p['leg_t']:g} / {p['liner_t']:g}", f"{p['mass']['60'] * 1e3:.2f}"]
        for D in LL["sizes"]:
            b = (p.get("full") or {}).get(str(D), {}).get("best") or {}
            cells += [f"({b.get('x'):g}, {b.get('y'):g})" if b else "–", b.get("prim"),
                      100 * b["slip2"] if b.get("slip2") is not None else None]
        cells += [pf(p.get("passes_normal_use")), p.get("score_worse_size")]
        rows.append(cells)
    hdr = ["legs / liner mm", "mass at 60 mm g"]
    for D in LL["sizes"]:
        hdr += [f"{D} mm eye", f"{D} mm min normal-use margin", f"{D} mm 2 g released % (subset)"]
    w(table(hdr + ["normal use", "tune score, worse size"], rows))
    if LL.get("choice"):
        lc, tc = LL["choice"]
        cand = [p for p in LL["pairs"] if p.get("liner_rule") and p.get("full")]
        pc = next(p for p in cand if p["leg_t"] == lc and p["liner_t"] == tc)
        s2 = lambda p: max(((p["full"][str(D)]["best"] or {}).get("slip2") or 0) for D in LL["sizes"])
        lighter = [p for p in cand if p["mass"]["60"] < pc["mass"]["60"]]
        txt = (f"Choice: legs {lc:g} mm with a {tc:g} mm liner — every normal-use criterion met at both sizes and the highest tune "
               f"score of the worse size (pairs within {LL['score_tie']:.2f} of it count as equal and the lightest of those wins).")
        if lighter:
            txt += (f" The lighter pairs save up to {(pc['mass']['60'] - min(p['mass']['60'] for p in lighter)) * 1e3:.2f} g per side "
                    f"but release {100 * min(s2(p) for p in lighter):.1f}–{100 * max(s2(p) for p in lighter):.1f} % of the reduced 2 g "
                    f"set at the worse size, against {100 * s2(pc):.1f} %.")
        w(txt + " The eye itself is then tuned per module for this pair (§7).\n")
    else:
        w("**No pair met every normal-use criterion at both sizes** at this preload.\n")
    _fin = (float(FINAL["leg_t"]), float(FINAL.get("saddle_liner_t", 0.0)))
    if not LL.get("choice") or (float(LL["choice"][0]), float(LL["choice"][1])) != _fin:
        w(f"The Final uses legs {f(_fin[0])} mm with a {f(_fin[1])} mm liner"
          + (" — not the pair this study chose." if LL.get("choice") else ".") + "\n")
if SK and SK.get("sizes"):
    p_s = mt.TISSUE["p_sustained"].v
    s1 = SK.get("set") or {}
    w("**The sustained state in use: frictional shakedown under head motion** (`calc/shakedown.py`, `support.shakedown`, "
      "results/shakedown.json). The donned state is only where friction starts. Worn, the head moves: each combination of the "
      f"{s1.get('cat', '1 g normal')} set that the eye tune uses ({s1.get('cases')} combinations: {s1.get('gravity')} gravity directions "
      f"within the {sp.CATEGORIES['1 g normal']['cone']:g}° head-tilt cone, {s1.get('head_motion')} head-rotation phases, {s1.get('cable')} "
      "cable directions) is applied from the current state and removed again, cycle after cycle, with the same path-dependent "
      f"friction (at most {SK['n_cyc']} cycles; converged when no contact normal force changes by more than {100 * SK['tol']:g} % of "
      "the weight over a cycle). Wherever a pad reaches its friction limit during a combination it slips a little and keeps that "
      "offset when the load is removed, so the weight the pads held by friction is handed on, cycle by cycle, to the only supports "
      "that carry it by normal force: the saddle's root zones, until the contact forces repeat from one cycle to the next (the pads "
      "may go on slipping back and forth, but the load no longer moves)."
      + ("" if not SK.get("checks") else " Checks of the procedure at 60 mm: " + "; ".join(
          f"{x['label']}: root {f(x['root_p_donned'] / 1e3)} → {f(x['root_p'] / 1e3)} kPa" for x in SK["checks"] if x.get("ok")) + ".")
      + "\n")
    rows = []
    for D in SIZES:
        a_ = SK["sizes"].get(D, {}).get("A", {}); b_ = SK["sizes"].get(D, {}).get("B", {})
        if not (a_.get("ok") and b_.get("ok")):
            rows.append([D] + ["–"] * 8); continue
        rows.append([D, a_["root_p_donned"] / 1e3, a_["root_p"] / 1e3, 100 * a_["root_share_y"],
                     f"{a_['cycles']}" + ("" if a_["converged"] else " (not converged)"), b_["root_p_donned"] / 1e3, b_["root_p"] / 1e3,
                     a_["pad_p_max"] / 1e3, f"{a_['n_rel']} of {a_['n_cases'] * a_['cycles']}"])
    w(table(["D", "root p donned (A) kPa", "root p in use (from A) kPa", "vertical share of the weight on the root in use %", "cycles",
             "root p donned (B) kPa", "root p in use (from B) kPa", "max pad p in use kPa", "released applications"], rows))
    okA = [D for D in SIZES if SK["sizes"].get(D, {}).get("A", {}).get("ok")]
    if okA:
        pu = [SK["sizes"][D]["A"]["root_p"] for D in okA]; sh = [100 * SK["sizes"][D]["A"]["root_share_y"] for D in okA]
        pb_ = [SK["sizes"][D]["B"]["root_p"] for D in okA if SK["sizes"][D].get("B", {}).get("ok")]
        over_u = [D for D in okA if SK["sizes"][D]["A"]["root_p"] > p_s]
        c60 = (SK["sizes"].get("60", {}).get("A") or {}).get("contacts") or {}
        rz = [c_ for n_, c_ in c60.items() if n_.startswith("S root") and c_.get("p_mean")]
        F_r = sum(c_["Fn"] for c_ in rz); A_r = sum(c_["Fn"] / c_["p_mean"] for c_ in rz)
        w(f"In use the root zones carry {f(min(sh))}–{f(max(sh))} % of the side's weight (vertical component) at "
          f"{f(min(pu) / 1e3)}–{f(max(pu) / 1e3)} kPa mean pressure, {f(min(pu) / p_s)}–{f(max(pu) / p_s)} × the {PSUS} kPa sustained target"
          + (f" — **the sustained root-pressure requirement is NOT met in use at {', '.join(over_u)} mm**; the donned value (A) holds "
             "only until the head moves." if over_u else " — the sustained root-pressure requirement is met in use.")
          + (f" From sequence B the end state is {f(min(pb_) / 1e3)}–{f(max(pb_) / 1e3)} kPa: the donning order stops mattering once "
             "the head has moved." if pb_ else "")
          + (f" At 60 mm the root zones then carry {f(F_r)} N; at {PSUS} kPa that needs {f(F_r / p_s * 1e4)} cm² of bearing, "
             f"against the {f(A_r * 1e4)} cm² of the two root zones (support.ROOT_W × ROOT_LEN of the superior auricle root [A])."
             if F_r > 0 and A_r > 0 else "") + "\n")
    lv = [x for x in SK.get("levers") or [] if x.get("ok")]
    if lv:
        w("Levers at 60 mm, each row the Final with the change named (shakedown from A):\n")
        w(table(["lever", "root p donned kPa", "root p in use kPa", "vertical share on the root %", "max pad p in use kPa",
                 f"root and pads ≤ {PSUS} kPa in use"],
                [[x["label"], x["root_p_donned"] / 1e3, x["root_p"] / 1e3, 100 * x["root_share_y"], x["pad_p_max"] / 1e3,
                  pf(x["root_p"] <= p_s and x["pad_p_max"] <= p_s)] for x in lv]))
        good_l = [x["label"] for x in lv if x["root_p"] <= p_s and x["pad_p_max"] <= p_s]
        _sa = [SK["sizes"][D]["A"] for D in okA if SK["sizes"][D]["A"].get("n_slip")]
        sl1 = [100 * x["n_slip"][0] / x["n_cases"] for x in _sa]; slN = [100 * x["n_slip"][-1] / x["n_cases"] for x in _sa]
        best_l = min(lv, key=lambda x: x["root_p"])
        ey = [x for x in SK.get("eyes") or [] if x.get("ok")]
        ml = SK.get("mass_limit") or {}
        w(("Levers that meet the target in use: " + "; ".join(good_l) + "." if good_l else
           f"No lever in the table meets the target in use; the lowest is '{best_l['label']}' at {f(best_l['root_p'] / 1e3)} kPa.")
          + (f" The eye tune's {len(ey)} best eyes on the 60 mm cup give {f(min(x['root_p'] for x in ey) / 1e3)}–"
             f"{f(max(x['root_p'] for x in ey) / 1e3)} kPa in use: the eye position does not decide it." if ey else "")
          + (f" Scaling the side's mass and inertia (COM kept), the 60 mm side meets the {PSUS} kPa target in use only up to "
             f"{f(ml['mass'] * 1e3)} g, {f(100 * ml['k'])} % of its {f(SK['sizes']['60']['A']['mass'] * 1e3)} g." if ml.get("mass") and ml.get("k", 1) < 1 else "")
          + " The pads micro-slip in normal use (§8: the 1 g criterion is no gross slip, not no slip at all"
          + (f"; in the first cycle a skin pad slides at the peak of {rng(sl1)} % of the combinations, in the last "
             f"{rng(slN)} %" if sl1 else "") + "), and every micro-slip moves "
          "weight onto the root; an ear-mounted cradle of this mass therefore needs either pads that do not slip at all under head "
          "motion or a weight-bearing support of the area above. Neither exists in this design, so this is the limit of the "
          "concept at this mass, and the first thing wear trials must measure (pressure film at the auricle root after wear with "
          "head motion, §22).\n")

if B:
    s = B["support"]["static"]
    w("Design B, same case: " + ("equilibrium found (contact table in results/design_B.json)." if s["ok"] else
                                 "**no static equilibrium** (the cradle tips off the ear).") + "\n")

# ------------------------------------------------------------------------------------------------ 7 layout
w("## 7. Support layout, preload line and the per-module link eye\n")
_s1 = (_ti.get("sets") or {}).get("1 g"); _s2 = (_ti.get("sets") or {}).get("2 g")
_set1 = (f"{_s1['gravity']} gravity directions × {_s1['head_motion']} head-motion cases × {_s1['cable']} cable directions = "
         f"{_s1['cases']} load cases" if _s1 else "the SET1 load cases of `calc/tune_eye.py`")
_set2 = (f"{_s2['dynamic']} dynamic directions × {_s2['gravity']} gravity × {_s2['head_motion']} head-motion × {_s2['cable']} cable = "
         f"{_s2['cases']} load cases" if _s2 else "SET2 of `calc/tune_eye.py`")
_grid = (f"a {_gs[0]:g} mm grid over the cup end" if _gs else "a grid over the cup end")
_ref = (" and ".join(f"{g_:g}" for g_ in _gs[1:]) + " mm refinement around the best" if len(_gs) > 1 else "refinement around the best")
_last = (f"The eye positions therefore lie on a {_gs[-1]:g} mm grid" if _gs else
         "The eye positions lie on the grid of the last refinement step")
_p0txt = (f" (its preload, {f(_ti['preload_layout'])} N, is the first preload level of the eye tune)" if _ti.get("preload_levels") else "/0.1 N")
_k2 = _ti.get("k_2g", 10)
_st4 = ((f"; finally (stage 4) the dense 1 g check and its local refinement (§8) on the best candidates in score order until one "
         f"passes (at most {_ti['max_verify']} per module) — that candidate is the module's eye") if _ti.get("max_verify") else "")
_lvc = next((x for x in (_ti.get("preload_levels") or []) if x.get("n_pass") and abs(x["P"] - float(_ti.get("link_preload", float("nan")))) < 1e-9), None)
_n2 = [min(_k2, int(_lvc["n_pass"].get(D, 0))) for D in SIZES] if _lvc else None
_s2txt = (f"the 2 g set for the {_k2} best candidates meeting normal use" if _n2 and all(n == _k2 for n in _n2) else
          f"the 2 g set for the best candidates meeting normal use (at most {_k2}: " +
          (", ".join(f"{n} on the {D} mm module" for n, D in zip(_n2, SIZES)) if _n2 else "as many as pass") + ")")
_ptxt = ((", together with the link preload (one value for every module: the link is common). The preload runs through levels "
          f"from the layout's {f(_ti['preload_layout'])} N in {f(_ti['preload_step'])} N steps, each with the link wire sized for it; the "
          "lowest level is taken at which every module has candidates on the " + (f"{_gs[0]:g} mm " if _gs else "") + "eye grid of stage 1 "
          "meeting every normal-use criterion of the tune (static + the 1 g grid) and an eye of stages 1–3 (grid or refinement point) "
          "that also passes the dense check and its refinement [design rule: the least preload "
          "keeps the pad pressures and the wire stress lowest], and the later stages run at that level") if _ti.get("preload_levels") else "")
w(f"""Tipping moment per g: M₁ = m g z̄. For the preload P (acting along −z at the eye) and the weight to leave every pad loaded,
the resultant of P and the weight couple must lie inside the pad polygon with margin: y_eye ≈ y_centroid + M₁/P. Under a dynamic
factor n the resultant moves by (n−1)M₁/P, so a larger P gives robustness, capped by the skin-pressure limit. The ring rim cannot
reach that point; the cup end can. The cradle layout (pad angles/radii, pad size) is common to every module (max–min search,
`umeh2/layout.py`: random sampling of its bounds, then a coordinate pattern search). That search ran during the iterations on the model and load sample of its time; `calc/final_layout.json` holds its result rounded to 0.5°/0.5 mm{_p0txt}, it is not part of the re-run pipeline, and every result in this report re-checks the layout with the current model. The eye is part of the module and was tuned for each driver size by `calc/tune_eye.py` with the current model{_ptxt}: {_grid}
(static + the 1 g grid of {_set1} per candidate, §8), {_s2txt}, then {_ref}{_st4};
score = the smallest normalised normal-use margin, then the 2 g released fraction (weight 2) and the 1 g pad micro-slip fraction (0.5).
A candidate stops at its first failing 1 g case (it can no longer pass). {_last} (no further rounding; print XY tolerance ±{tl.TOL['xy']:g} mm). The 2 g column is
the reduced tuning subset ({_set2}); §8 gives the full 2 g set of the Final.
""")
_lv = _ti.get("preload_levels") or []
if _lv:
    rows = []
    for x in _lv:
        wr = x.get("wire")
        rows.append([x["P"], f"Ø{f(wr['d_mm'])} mm, {wr['n_coil']} coils" if wr else "no stock wire carries it"]
                    + [f"{(x.get('n_pass') or {}).get(D, '–')}/{(x.get('n_eval') or {}).get(D, '–')}" for D in SIZES]
                    + ["**chosen**" if abs(x["P"] - FINAL["link_preload"]) < 1e-9 else ""])
    w("Preload levels of the tune (stage 1, the whole " + (f"{_gs[0]:g} mm " if _gs else "") + "eye grid of each module; the link wire of each level sized on every module at "
      "the layout's reference eye, pulled inside the module's eye limit where it lies outside; candidates meeting every normal-use "
      "criterion / evaluated):\n")
    w(table(["P N", "link wire"] + [f"{D} mm" for D in SIZES] + [""], rows))
    if not _ti.get("all_modules_pass", True):
        w("**No preload level gave every module a passing eye**: the chosen level is the last one tried, and the modules without a "
          "passing eye do not meet normal use (§8).\n")
    rows = []
    for x in _lv:
        for D in SIZES:
            for c in ((x.get("dense_checks") or {}).get(D) or []):
                dn_, rf_ = c.get("dense") or {}, c.get("refine") or {}
                rows.append([x["P"], D, f"({f(c['x'])}, {f(c['y'])})", c.get("score"),
                             f"{int(dn_.get('released', 0))} / {int(dn_.get('unseated', 0))} / {int(dn_.get('tilt_over', 0))}",
                             dn_.get("min_seat"), rf_.get("min_seat"), dn_.get("worst_tilt"), rf_.get("worst_tilt"),
                             "**pass**" if c.get("ok") else "fail"])
    if rows:
        w("Stage 4 — dense check and local refinement of the candidates, in score order (released / tripod lost / over-tilted in the "
          "dense check; seating margin and tilt: dense → refined):\n")
        w(table(["P N", "D", "eye (x, y) mm", "tune score", "dense fails", "seat margin dense N", "refined N", "worst tilt dense °",
                 "refined °", ""], rows))
pec = (RL or {}).get("pad_edge_clearance_final")
if pec:
    w(f"Layout constraints [A] (`layout.geometric_ok`, `layout.BOUNDS`): pads, saddle and cable clip at least {lo.MIN_SEP_DEG:g}° apart on the ring "
      f"(tab width, screw access); pad centres inside the search bounds. Checked on the Final: the inner edge of every pad (centre "
      f"radius − a/2) clears the p95 pinna half-length {lo.PINNA_HALF_P95:g} mm + {lo.PINNA_EDGE_CLR:g} mm = {f(pec['limit'])} mm from the canal axis — temporal "
      f"{f(pec['temporal'])}, mastoid {f(pec['mastoid'])}, posterior-superior {f(pec.get('post'))} mm.\n")
ti = (EYE or {}).get("_inputs")
_rec = (EYE or {}).get("_record")
if _rec:
    w("**Record of the eye tune.** " + _rec + " The tune ran with wire "
      f"Ø{f(ti['wire_d'])} mm / {ti['link_coils']} coils, legs {f(ti['leg_t'])} mm, liner {f(ti['saddle_liner_t'])} mm; the per-candidate "
      "tables of the tune (candidates evaluated, top five, stage-4 checks of the other modules) are not available. The table below is "
      "the tune's objective at each chosen eye with the Final's own inputs; the dense check of §8 is the pass/fail evidence.\n")
if ti and F and not _rec:
    now = dict(wire_d=FINAL["wire_d"], link_coils=FINAL["link_coils"], leg_t=FINAL["leg_t"],
               saddle_liner_t=FINAL.get("saddle_liner_t", 0.0), bar_t=FINAL["bar_t"], link_preload=FINAL["link_preload"])
    diff = [k for k, v in now.items() if abs(float(ti.get(k, float("nan"))) - float(v)) > 1e-9]
    dm = max(abs(ti["mass"][D] - F[D]["mass"]) for D in SIZES if D in ti.get("mass", {}))
    dc = max((float(np.linalg.norm(np.subtract(ti["com"][D], F[D]["com"]))) for D in SIZES if D in ti.get("com", {})), default=None)
    w(f"Consistency: the eye tune ran with wire Ø{f(ti['wire_d'])} mm / {ti['link_coils']} coils, legs {f(ti['leg_t'])} mm, liner "
      f"{f(ti['saddle_liner_t'])} mm and the CAD mass properties of each side with the eye boss at the reference position: within "
      f"{f(dm * 1e3)} g" + (f" and {f(dc * 1e3)} mm (COM)" if dc is not None else "") + " of the Final's"
      + (" — the same inputs as the Final.\n" if not diff and dm < 0.5e-3 and (dc is None or dc < 0.2e-3)
         else f" — it differs from the Final in {', '.join(diff) or 'the mass properties'}"
         + ("; the second table below re-scores the tuned eyes with the Final's inputs.\n" if EC
            else ": **re-run tune_eye.py**.\n")))
if EYE and _rec:
    rows = []
    for D in SIZES:
        c = (EC or {}).get(D, {}); m = c.get("margins") or {}
        rows.append([D, c.get("x"), c.get("y"), c.get("prim"), c.get("slip2"), c.get("padslip1"), m.get("static friction"),
                     m.get("1g tilt"), m.get("1g seating margin")])
    w(table(["D", "eye x mm", "eye y mm", "min normal-use margin", "2 g released (subset)", "1 g pad micro-slip",
             "static-friction margin", "tilt margin", "seating margin"], rows))
if EYE and not _rec:
    rows = []
    for D in SIZES:
        e = EYE.get(D, {}); b = e.get("best", {})
        m = b.get("margins", {})
        pr = b.get("prim")
        if b.get("aborted") and pr is not None:          # stopped at its first failing case: partial 1 g margins
            pr = f"{f(pr)} (stopped at 1 g case {b.get('n1')}/{b.get('n1_all')}; partial)"
        rows.append([D, b.get("x"), b.get("y"), b.get("P_D", b.get("P")), pr, b.get("slip2"), b.get("padslip1"),
                     m.get("static friction"), m.get("1g tilt"), m.get("1g seating margin"), f"{e.get('n_pass')}/{e.get('n_eval')}"])
    w(table(["D", "eye x mm", "eye y mm", "P(D) N", "min normal-use margin", "2 g released (subset)", "1 g pad micro-slip",
             "static-friction margin", "tilt margin", "seating margin", "candidates passing / evaluated"], rows))
if EYE and EC and not _rec:
    rows = []
    for D in SIZES:
        b = EYE.get(D, {}).get("best", {}); c = EC.get(D, {})
        rows.append([D, f"({f(c.get('x'))}, {f(c.get('y'))})", b.get("prim"), c.get("prim"), b.get("slip2"), c.get("slip2"),
                     b.get("padslip1"), c.get("padslip1")])
    w("The same objective re-scored at each tuned eye with the Final's own inputs (link wire sized on all modules, §11; P(D) "
      f"from the tuned {an.LINK_REF_D} mm eye; CAD mass properties with the eye boss in place) — `results/eye_check.json`:\n")
    w(table(["D", "eye", "min normal-use margin: tune", "Final inputs", "2 g released: tune", "Final inputs",
             "1 g pad micro-slip: tune", "Final inputs"], rows))

# ------------------------------------------------------------------------------------------------ 8 loads
w("## 8. Load cases, vector combination and worst-orientation search\n")
rows = [[k, v["cone"] if v["cone"] is not None else "any (resultant)", v["dyn"], sp.ALPHA[v["ang"]], sp.OMEGA[v["ang"]], v["cable"]]
        for k, v in sp.CATEGORIES.items()]
w(table(["case", "gravity within ° of upright", "dynamic accel (g, any direction)", "head α rad/s² [A]", "head ω rad/s [A]", "cable pull N [A]"], rows))
w(f"""Effective gravity g_eff = g + a (vector sum, every direction of a on a Fibonacci sphere); head angular motion about the
yaw/pitch/roll axes through anthropometric pivots [A] adds the d'Alembert loads F = −m[α×ρ + ω×(ω×ρ)] and M = −I_G α − ω×(I_G ω).
For oscillatory head motion the angular-acceleration peak and the angular-velocity peak are in quadrature, so they are applied
as two separate phases (α-peak with ω = 0, ω-peak with α = 0); the squared inertial load is convex in the phase, so the two end
phases bound every intermediate one. Cable weight ({mt.CABLE['hang_len'].v:g} m × {mt.CABLE['mass_per_m'].v * 1e3:g} g/m [A]) along g_eff plus a cable pull at the clip in any
direction within {sp.CABLE_CONE:g}° of straight down [A]. **Every** combination of a set (gravity direction × dynamic direction × axis/sign/phase × cable direction)
is solved; the worst orientation is searched, not assumed. How the directions are chosen depends on what the category is used for:

* **1 g (pass/fail criteria): a deterministic grid** that contains the edges of both cones (`support.GRID_1G`): upright + head tilt
  {', '.join(f'{t:g}' for t in sp.GRID_1G['tilt'])}° × every {sp.GRID_1G['az_step']:g}° of azimuth; cable straight down + at {', '.join(f'{t:g}' for t in sp.GRID_1G['cable_polar'])}° from
  straight down × every {sp.GRID_1G['cable_az_step']:g}°. Its resolution is checked on every module by a **dense check** (`support.DENSE_1G`, nested: head tilt
  {', '.join(f'{t:g}' for t in sp.DENSE_1G['tilt'])}° × every {sp.DENSE_1G['az_step']:g}°, cable {', '.join(f'{t:g}' for t in sp.DENSE_1G['cable_polar'])}° × every {sp.DENSE_1G['cable_az_step']:g}°) and a **local
  refinement** of the dense check (`analysis.refine_1g_chunk`): around every failing and each of the {an.K_CRIT} lowest-seating-margin and {an.K_CRIT}
  largest-tilt dense combinations, its dense-grid cell (± half a dense step in head tilt, gravity azimuth, cable angle and cable azimuth) is
  searched on a {an.REFINE_N}-point grid per coordinate with the same head motion; the change from the dense to the refined worst values
  measures what a still finer search could add. Both belong to the normal-use criteria of the Final (tables below).
* **2 g, 3 g, 5 g (reported as released fractions): a quasi-uniform (Fibonacci) sample** of the gravity, dynamic and cable directions;
  a released fraction is a property of that sample, not a worst case. Where a sweep or mass table gives "1 g %", it is the released
  fraction of the 1 g grid ({len(sp.ring_grid(sp.GRID_1G['tilt'], sp.GRID_1G['az_step'])) * len(sp.ring_grid(sp.GRID_1G['cable_polar'], sp.GRID_1G['cable_az_step'])) * len(sp.ANG_CASES)} combinations per evaluation).
""")
if DN and DN.get("sizes"):
    def _gdesc(t):
        g_ = np.asarray(t["g_dir"]); c_ = np.asarray(t["cable_dir"])
        tl_ = math.degrees(math.acos(max(-1.0, min(1.0, -g_[1])))); az_ = math.degrees(math.atan2(g_[2], g_[0])) % 360
        tc_ = math.degrees(math.acos(max(-1.0, min(1.0, -c_[1])))); ac_ = math.degrees(math.atan2(c_[2], c_[0])) % 360
        hm_ = f"{t['axis']} {('+' if t['sign'] > 0 else '−' if t['sign'] < 0 else '')}{t.get('phase') or ''}" if t.get("axis") else "no head rotation"
        return f"tilt {tl_:.1f}° at azimuth {az_:.1f}°, {hm_}, cable {tc_:.0f}° at {ac_:.1f}°"
    def _dense_rows(DD):
        rows_ = []
        for D in SIZES:
            r_ = DD["sizes"].get(D)
            if not r_:
                continue
            wt_ = r_["worst_tilt"]; ms_ = r_["min_seat"]
            rows_.append([D, str(int(r_["n"])), str(int(r_["released"])), str(int(r_["unseated"])), str(int(r_["tilt_over"])),
                          wt_[0], _gdesc(wt_[1]) if wt_[1] else "–", ms_[0] if ms_[0] is not None else None,
                          _gdesc(ms_[1]) if ms_[1] else "–"])
        return rows_
    _HD = ["D", "combinations", "released", "tripod lost", f"tilt > {TILT_N}°", "worst tilt °", "worst-tilt case",
           "smallest seating margin N", "its case"]
    w(f"Dense check of the Final (`results/dense_1g.json`; azimuth 0° = forward, 90° = outward, away from the head: gravity at "
      f"azimuth 90° means the head is tilted towards this side, this ear down, so the side hangs outward; seating margin = "
      f"third-largest skin contact force − {sp.F_MIN:g} N):\n")
    w(table(_HD, _dense_rows(DN)))
    _nn = sum(int((DN["sizes"].get(D) or {}).get("released_numerical", 0)) for D in SIZES)
    if _nn:
        w(f"{_nn} of the released combinations are numerical (the minimiser stalled at a bounded position after every load-step cut, "
          "§6); they are counted as releases.\n")
    _RF = DN.get("refine") or {}
    if _RF:
        rows_ = []
        for D in SIZES:
            r0 = DN["sizes"].get(D); r1 = _RF.get(D)
            if not r0 or not r1:
                continue
            rows_.append([D, str(len(r1.get("seeds") or [])), str(int(r1["n"])), str(int(r1["n_fails"])),
                          f"{f(r0['worst_tilt'][0])} → {f(r1['worst_tilt'][0])}", f"{f(r0['min_seat'][0])} → {f(r1['min_seat'][0])}"])
        w("Local refinement around the dense check's critical combinations (`results/dense_1g.json` \"refine\"; dense → refined worst value):\n")
        w(table(["D", "seeds", "combinations", "failing", "worst tilt °", "smallest seating margin N"], rows_))
    if DG45 and DG45.get("sizes"):
        _g45 = DG45.get("grid_1g") or {}; _gd45 = DG45.get("grid") or {}; _rf45 = DG45.get("refine") or {}
        rows_ = []
        for D in SIZES:
            r0 = DG45["sizes"].get(D); r1 = _rf45.get(D) or {}
            if not r0:
                continue
            rows_.append([D, f"{int(r0['released'])} / {int(r0['unseated'])} / {int(r0['tilt_over'])}", r0["min_seat"][0],
                          f"{int(r1.get('n_fails', 0))} of {int(r1.get('n', 0))}" if r1 else "–", r1.get("min_seat", [None])[0] if r1 else None,
                          "pass" if r0.get("ok") and r1.get("ok", True) else "**fail**"])
        w(f"History (§4 change 21): the eyes tuned on the 1 g grid at every {f(_g45.get('az_step'))}° (gravity) / {f(_g45.get('cable_az_step'))}° "
          f"(cable) — {DG45.get('eyes_note', '')} — in the dense check of that time (every {f(_gd45.get('az_step'))}° / "
          f"{f(_gd45.get('cable_az_step'))}°) and its local refinement (`results/dense_1g_grid45.json`; released / tripod lost / over-tilted):\n")
        w(table(["D", "dense fails", "seat margin dense N", "refinement failing", "seat margin refined N", ""], rows_))
        w(f"Change 21 halved the grid and dense-check azimuth steps and re-ran the tune with the stage-4 verification (§7): "
          f"{grid45_history()}.\n")
    if DP and DP.get("sizes"):
        _d0 = DP.get("design") or {}; _ts = _d0.get("tune_set_1g") or {}
        w(f"The Final before iteration change 19 on the 1 g grid (§4; `results/grid_1g_before_grid.json`): eyes tuned on a quasi-uniform "
          f"1 g sample ({_ts.get('gravity', '–')} gravity × {_ts.get('head_motion', '–')} head-motion × {_ts.get('cable', '–')} cable directions = "
          f"{_ts.get('cases', '–')} combinations) at the layout preload {f(_d0.get('link_preload'))} N, link wire Ø{f(_d0.get('wire_d'))} mm:\n")
        w(table(_HD, _dense_rows(DP)))
        _pp = [((ETP or {}).get(D) or {}).get("best", {}).get("prim") for D in SIZES]
        _pp = [x for x in _pp if x is not None]
        _sm = [(DP["sizes"].get(D) or {}).get("fails_summary") or {} for D in SIZES]
        _sm = [x for x in _sm if x.get("n")]
        if _sm:
            allf = dict(n=sum(x["n"] for x in _sm), side_out=sum(x["side_out"] for x in _sm), cable_out=sum(x["cable_out"] for x in _sm),
                        both_out=sum(x["both_out"] for x in _sm), tilt_min=min(x["tilt_min"] for x in _sm), tilt_max=max(x["tilt_max"] for x in _sm))
            _L19 = G45L or FINAL                            # the Final right after change 19 (change 21 is in §4 / above)
            _p1 = _L19["link_preload"] > float(_d0.get("link_preload", 1e9)) + 1e-9
            _dy = [_L19["per_size"][D]["link_y"] - _d0["per_size"][D]["link_y"] for D in SIZES
                   if D in (_d0.get("per_size") or {}) and D in (_L19.get("per_size") or {})]
            w(f"The {allf['n']} failing combinations: {fail_pattern(allf)}."
              + (f" On its own sample the first tune had passed these eyes (smallest normal-use margin {f(min(_pp))}–{f(max(_pp))} over the "
                 "modules, `results/eye_tuning_before_grid.json`)." if _pp and min(_pp) >= 0 and eyes_match_etp() else "")
              + (f" With the grid (change 19; the link wire re-sized for each preload level, §11) the tune moved to {f(_L19['link_preload'])} N "
                 f"from {f(_d0.get('link_preload'))} N" + (f", with the eyes {'lower' if max(_dy) < 0 else 'moved'} (Δy {rng(_dy)} mm)" if _dy else "")
                 + " (§7)." if _p1 else "") + "\n")
if F:
    rows = []
    for D in SIZES:
        r = F[D]
        for cat in sp.CATEGORIES:
            s = r["support"][cat]
            rows.append([D, cat, str(int(s["n"])), str(int(s["released"])), 100 * s["slip_fraction"], 100 * (s.get("pad_slip_fraction") or 0),
                         str(int(s["unseated"])),
                         s["worst_tilt_deg"], s["worst_disp_mm"], max(s["p_peak"].values()) / 1e3])
    w(table(["D", "case", "combinations", "released", "%", "pad micro-slip % of held", "tripod lost", "worst tilt deg*", "worst disp mm*", "peak p kPa*"], rows))
    w("*over combinations that stayed in equilibrium. Tilt = rotation about x and y (changes the driver–ear geometry). Pad micro-slip = "
      "a skin pad slides locally while the cradle as a whole stays in equilibrium; each combination here starts from the donned "
      "state, so the micro-slips do not add up in this table — repeated, they do (§6, the sustained state in use).\n")
    keys = sorted({k for D in SIZES for cat in sp.CATEGORIES for k in (F[D]["support"][cat].get("released_by") or {})})
    if keys:
        rows = []
        for k in keys:
            row = [k]
            for cat in sp.CATEGORIES:
                tot = sum(F[D]["support"][cat]["released"] for D in SIZES)
                n_ = sum((F[D]["support"][cat].get("released_by") or {}).get(k, 0) for D in SIZES)
                row.append(f"{n_} ({f(100 * n_ / tot) if tot else '–'} %)")
            rows.append(row)
        for gk in ("gravity upright", "gravity tilted"):
            row = [f"of which: {gk}"]
            for cat in sp.CATEGORIES:
                tot = sum(F[D]["support"][cat]["released"] for D in SIZES)
                if sp.CATEGORIES[cat]["cone"] is None:
                    row.append("–"); continue
                n_ = sum((F[D]["support"][cat].get("released_by_gravity") or {}).get(gk, 0) for D in SIZES)
                row.append(f"{n_} ({f(100 * n_ / tot) if tot else '–'} %)")
            rows.append(row)
        w("What drives the releases — released combinations per head-motion case, all five sizes summed (share of the "
          "category's releases). 'alpha' = angular-acceleration peak, 'omega' = angular-velocity peak; 'gravity tilted' = "
          "head tilted within the category's cone (not split for 5 g: its resultant acceleration has any direction):\n")
        w(table(["head motion", *sp.CATEGORIES], rows))
    wc = F["50"]["support"]["1 g normal"]["worst_tilt_case"]
    if wc:
        t = wc["tag"]
        w(f"Worst 1 g orientation found (50 mm): gravity direction ({f(t['g_dir'][0])}, {f(t['g_dir'][1])}, {f(t['g_dir'][2])}), head "
          f"{t['axis']} {('+' if t['sign'] > 0 else '−' if t['sign'] < 0 else '')}{t.get('phase') or ''}, cable pull along "
          f"({', '.join(f(x) for x in t['cable_dir'])}).\n")

# ------------------------------------------------------------------------------------------------ 9 friction
w("## 9. Friction, minimum normal force, sensitivity\n")
if F:
    rows = []
    for D in SIZES:
        dem = F[D]["support"].get("static_mu_demand") or {}
        rows.append([D] + [dem.get(k) for k in sp.SKIN_PADS])
    w("Static friction demand (donning A, the skin pads made non-slipping, root and scalp at design μ): μ_required / μ_design per pad; "
      "> 1 means the pad creeps at rest with the design coefficient:\n")
    w(table(["D", *sp.SKIN_PADS], rows))
if SW:
    rows = [[x["key"], 100 * x["1 g normal"]["slip"], x["1 g normal"]["tilt"], 100 * x["2 g dynamic"]["slip"], x.get("static_mu_demand")] for x in SW.get("friction", [])]
    w(table(["friction case (50 mm)", "1 g: % released", "1 g tilt deg", "2 g: % released", "static μ demand"], rows))
    des_ = [x for x in SW.get("preload", []) if x["key"][1] == "design"]
    low = {x["key"][0]: x for x in SW.get("preload", []) if x["key"][1] == "mu_low"}
    rows = [[x["key"][0], 100 * x["1 g normal"]["slip"], 100 * low.get(x["key"][0], {}).get("1 g normal", {}).get("slip", float("nan")),
             100 * x["2 g dynamic"]["slip"], x.get("static_mu_demand"), x.get("static_p", {}).get("M mastoid", float("nan")) / 1e3] for x in des_]
    w("Preload sweep — the minimum normal force is the smallest P with zero 1 g release (design μ, then the low-μ column):\n")
    w(table(["P N", "1 g % (μ design)", "1 g % (μ low)", "2 g % (μ design)", "static μ demand", "mastoid p kPa"], rows))
    rows = [[x["key"], 100 * x["1 g normal"]["slip"], x["1 g normal"]["tilt"], 100 * x["2 g dynamic"]["slip"]] for x in SW.get("tissue_helix", [])]
    w(table(["tissue / helix case", "1 g %", "1 g tilt deg", "2 g %"], rows))

# ------------------------------------------------------------------------------------------------ 10 max mass
w("## 10. Maximum driver mass\n")
w("\n".join(l.strip() for l in an.max_driver_mass.__doc__.splitlines()) + "\n")
if MM:
    conds = list(next(iter(MM.values())).keys())
    rows = [[D, dz.DRIVERS[int(D)]["mass"]] + [mrange(MM[D][c]) for c in conds] for D in MM]
    w(table(["D", "nominal driver g [A]"] + [f"{c}: passing driver g" for c in conds], rows))
    _hig = next((v_.get("hi_g") for D_ in MM for v_ in MM[D_].values() if isinstance(v_, dict) and v_.get("hi_g")), None)
    w("Each cell is the range of driver masses for which the condition holds, found from the nominal driver outwards. "
      f"'+' = the upper search bound ({f'{_hig:g} g' if _hig else 'analysis.max_driver_mass hi_g'}) was reached, so the condition does not limit the driver mass there. 'fails at the "
      "nominal' = the condition is not met with the driver the module is designed for; the range after it, if any, is where it "
      "would hold. Governing check of the maximum design condition: " + "; ".join(f"{D} mm: {MM[D]['maximum'].get('governs')}" for D in MM) + ".\n")
    _ml = (SK or {}).get("mass_limit") or {}
    _a60 = ((SK or {}).get("sizes", {}).get("60") or {}).get("A") or {}
    if _ml.get("mass") and _a60.get("mass") and _ml.get("k", 1) < 1:
        _bare = _a60["mass"] - dz.DRIVERS[60]["mass"] * 1e-3
        w(f"These ranges use the normal-use criteria as donned. The in-use auricle-root pressure (§6 shakedown) sets a limit on the whole "
          f"side instead: at 60 mm it is met only up to {f(_ml['mass'] * 1e3)} g per side (mass and inertia scaled, COM kept), while the "
          f"60 mm side without its driver already weighs {f(_bare * 1e3)} g"
          + (" — no driver mass meets it." if _bare > _ml["mass"] else f" — a driver of at most {f((_ml['mass'] - _bare) * 1e3)} g would.") + "\n")
if SM:
    w(table(["driver g (50 mm)", "total g", "static hold", "1 g % released", "2 g %", "3 g %"],
            [[r["driver_g"], r["total_g"], pf(r.get("static_ok")), 100 * r["1 g normal"], 100 * r["2 g dynamic"], 100 * r["3 g severe"]] for r in SM]))
    w("![slip vs mass](fig/slip_vs_mass.png)\n![max driver mass](fig/max_driver_mass.png)\n")

# ------------------------------------------------------------------------------------------------ 11 link
w("## 11. Occipital spring link — wire derived, not chosen\n")
w(ls.__doc__ + "\n")
if L:
    for nm in ("B", "Final"):
        c = L[nm]["chosen"]
        if not c:
            continue
        w(f"**{nm}** (P = {f(L[nm]['P'])} N): chosen Ø{f(c['d_mm'])} mm, {c['n_coil']} apex coils (mean Ø{ls.DC_COIL * 1e3:.0f} mm).\n")
        w(table(["quantity", "value"], [["rate per side k (N/m)", c["k_side"]], ["preload range (p5–p95 head) N", f"{f(c['P_min'])} – {f(c['P_max'])}"],
                                        ["max/min preload ratio", c["P_ratio"]], ["donning force N", c["P_don"]],
                                        ["Sut MPa (d)", c["Sut"] / 1e6], ["σ worn / σ donning MPa", f"{f(c['sigma_worn'] / 1e6)} / {f(c['sigma_don'] / 1e6)}"],
                                        ["eye stress (donning) MPa, K_A", f"{f(c['sigma_eye_don'] / 1e6)}, {f(c['KA'])}"],
                                        [f"eye inner radius mm (≥ {mt.WIRE['min_bend_radius_d'].v:g} d = minimum bend radius)", c["eye_ri"] * 1e3],
                                        [f"SF yield (≥ {ls.SF_YIELD:g})", c["SF_yield"]], ["SF fatigue Goodman, " + f"{int(c.get('N_cycles', ls.N_DON)):,}".replace(",", " ") + f" donning cycles (≥ {ls.SF_FATIGUE:g})", c["SF_fatigue"]],
                                        ["free half-gap mm (form the wire to this)", c["free_half_gap"] * 1e3], ["wire length m", c["L"]], ["mass g", c["mass_g"]]]))
    cF = L["Final"]["chosen"] or {}
    if cF:
        w(f"Bending only: with the axial and shear forces taken as P along the whole {f(cF['L'])} m arc (an upper bound), their compliance is "
          f"{f(100 * ls.axial_shear_share(cF))} % of the bending compliance of the Final wire (shear factor {ls.ALPHA_SHEAR:.3g}, "
          f"ν = {mt.WIRE['nu'].v:g}) [C].\n")
    hy_ = min(((F[D]["link"]["design"]["SF_yield"], D) for D in SIZES), default=None) if F else None
    w(f"The common link is formed on the {an.LINK_REF_D} mm module; on the other modules the cup end sits Δz deeper or shallower, so P(D) = P_ref + "
      "k_side Δz (table in §3)." + (f" The lowest yield SF over the five modules is {f(hy_[0])} ({hy_[1]} mm) against the required "
      f"{ls.SF_YIELD:g}: {f(100 * (hy_[0] / ls.SF_YIELD - 1))} % headroom." if hy_ else "")
  + f" The preload itself comes from the eye tune (§7); stock diameters {', '.join(f'{x:g}' for x in ls.STOCK_D_DS)} mm [DS] and "
    f"{', '.join(f'{x:g}' for x in ls.STOCK_D_A)} mm [A: assumed stocked, confirm with the wire supplier] are considered.\n")
    if F:
        w("The same wire on every module: each module's eye sets its own path across the cup face (and its own P(D)), so the wire "
          "is checked on each (link_design with that module's path):\n")
        rows = [[D, F[D]["eye"]["link_x"], F[D]["eye"]["link_y"], F[D]["link"]["design"]["P"], F[D]["link"]["design"]["k_side"],
                 F[D]["link"]["design"]["P_ratio"], F[D]["link"]["design"]["SF_yield"], F[D]["link"]["design"]["SF_fatigue"],
                 pf(F[D]["link"]["design"]["ok"])] for D in SIZES]
        w(table(["D", "eye x mm", "eye y mm", "P(D) N", "k_side N/m", "max/min preload", f"SF yield (≥ {ls.SF_YIELD:g})", f"SF fatigue (≥ {ls.SF_FATIGUE:g})", "all"], rows))
    w("![link](fig/link_wire.png)\n")

# ------------------------------------------------------------------------------------------------ 12 structure
w("## 12. Structural analysis of the cradle arms\n")
w(st.__doc__ + "\n")
w(f"Allowables at {TSV} °C: S_xy·kT = {f(mt.PETG['S_xy'].v * st.kT() / 1e6)} MPa (in-layer), interlayer shear {f(mt.PETG['S_shear_il'].v * st.kT() / 1e6)} MPa; "
  f"sustained (1 g) × {st.K_SUSTAINED}. Required SF ≥ γM = {mt.GAMMA_M_PRINT.v}. Kt: fillet {st.KT_FILLET}, hole in bending {st.KT_HOLE_BEND} [STD Peterson]. "
  "Combined loading: σ = |N|/A + Kt(|M_t|/Z_t + |M_h|/Z_h), τ = τ_torsion + 1.5 |V|/A, σ_vM = √(σ² + 3τ²); interlayer shear uses the "
  "shear acting on the layer planes (arms printed on their side).\n")
w(f"""Three structural load definitions:
* **1 g sustained** — every held 1 g combination, sustained allowables.
* **5 g accidental envelope** — every 5 g combination: when it stays in equilibrium, its contact forces; when it releases, the contact
  forces at the **onset of gross slip** (bisection on the load factor λ of the increment from the static state). Beyond the onset the
  cradle slides off and the arm loads cannot grow, so the envelope bounds the arm loads. λ_min per size is in §1.
* **{FH} N handling** — {FH} N at one pad in any of {NDH} directions (a hand catching a pad, a collar, hair) [A]: the local load that the
  retention cannot limit. It sized the arm bar.
The whole-load-at-one-pad bound of the 5 g case (m·5g + {an.F_SNAG:g} N snag on a single pad) is printed for information only: it cannot occur
because the cradle releases first.
""")
N_LOW = 6    # sections listed per table
if F:
    for D in ("50", "60"):
        for cat, rws, lab in (("1 g normal", F[D]["arm_sf"]["1 g normal"], "sustained allowables"),
                              ("5 g accidental", F[D]["arm_sf"]["5 g accidental"], "short-term allowables, onset envelope"),
                              (f"handling {FH} N", F[D]["handling"]["sf"], "short-term allowables")):
            rows = sorted(rws, key=lambda x: min(x["SF_vm"], x["SF_il"]))[:N_LOW]
            w(f"{D} mm, {cat} ({lab}), {N_LOW} lowest sections:\n")
            w(table(["arm", "section", "σ MPa", "τ MPa", "σ_vM MPa", "SF vM", "τ interlayer MPa", "SF interlayer", "N N", "T N·mm", "M_t N·mm", "M_h N·mm"],
                    [[x["arm"], x["section"], x["sigma"] / 1e6, x["tau"] / 1e6, x["vm"] / 1e6, x["SF_vm"], x["tau_il"] / 1e6, x["SF_il"], x["N"],
                      x["T"] * 1e3, x["Mt"] * 1e3, x["Mh"] * 1e3] for x in rows]))
        b5 = F[D]["bound_5g"]
        w(f"Information: whole 5 g load ({f(b5['F'])} N) at one pad → lowest SF {f(min_sf(b5['sf'])[0])} ({min_sf(b5['sf'])[1]}).\n")
    w("Arm compliance in series with each contact (Final 60 mm; the support model carries it, §6), in the contact frame "
      "(n = contact normal, t1/t2 = tangents), against the contact's own compliance:\n")
    rows = [[x["contact"], x["arm"]] + [v * 1e3 for v in x["c_arm"]] + [x["c_contact"][0] * 1e3, x["c_contact"][1] * 1e3]
            + [max(a / c for a, c in zip(x["c_arm"], x["c_contact"]))] for x in F["60"].get("arm_compliance", [])]
    w(table(["contact", "arm", "arm n mm/N [C]", "arm t1 mm/N", "arm t2 mm/N", "contact n mm/N [C]", "contact t mm/N",
             "largest arm/contact ratio"], rows))
    acs = F["60"].get("arm_compliance", [])
    if acs:
        ratio = lambda x: max(a / c for a, c in zip(x["c_arm"], x["c_contact"]))
        pads_ = [x for x in acs if x["contact"] in sp.SKIN_PADS]
        top = max(pads_ or acs, key=ratio)
        es_ = F["60"].get("arm_energy_split") or {}
        if es_:
            w("Where each arm's compliance sits at rest (60 mm; share of the arm's complementary energy under its own contact "
              "forces, `structure.arm_energy_split`): " + "; ".join(
                  f"{a_} — " + ", ".join(f"{k_} {f(100 * v_)} %" for k_, v_ in list(v["shares"].items())[:2]) for a_, v in es_.items())
              + ". ")
        w("Among the skin pads the arm is most "
          f"compliant against its contact at the {padn(top['contact'])} pad (ratio {f(ratio(top))}); where the arm compliance is comparable to "
          "the contact's, the pad sheds weight onto the auricle root (rigid against flexible arms: §6 lever table). Leg thickness "
          "and saddle liner were therefore chosen together (§6, 'Arm legs and saddle liner').\n")
    fat = [(D, x) for D in SIZES for x in F[D].get("fatigue", [])[:1]]
    fat_txt = ""
    if fat:
        Dm, xm = min(fat, key=lambda t: t[1]["SF"])
        fat_txt = (f"Fatigue: walking/running {sci(st.N_FATIGUE)} cycles [A]; each arm section is taken to cycle from zero to its largest von Mises "
                   f"stress over the held 2 g combinations (conservative: the steady 1 g part is not split off, Kt kept as the notch "
                   f"factor), Goodman on the normalised S-N curve (`structure.fatigue_strength`, fatigue ratio [A]) at {sci(st.N_FATIGUE)} cycles, "
                   f"{TSV} °C: lowest SF {f(xm['SF'])} at {Dm} mm, {xm['arm']} {xm['section']} (σ_max {f(xm['vm_2g'] / 1e6)} MPa, "
                   f"S_f {f(xm['S_f'] / 1e6)} MPa). ")
    w(f"Temperature: at {st.T_HOT.rstrip('C')} °C (car, sun) strength ×{f(st.kT(st.T_HOT))} [LIT] against ×{f(st.kT())} at {TSV} °C: every short-term SF "
      f"above scales by {f(st.kT(st.T_HOT) / st.kT())}. " + fat_txt + "Creep rupture of the arms is covered by the sustained "
      f"allowables (×{st.K_SUSTAINED}) in the 1 g tables; creep of the preload matters in the bolted joints (§13).\n")
if CS:
    w("### 12.1 Contact stresses at every interface\n")
    for D in ("50", "60"):
        rows = [[x["interface"], x["case"], x.get("F"), x["p_mean"] / 1e3 if x.get("p_mean") is not None else None,
                 x["p_peak"] / 1e3, x["limit"] / 1e3 if x.get("limit") else None, x.get("ratio"), x.get("SF"), x.get("SF_sustained")]
                for x in CS.get(D, [])]
        w(f"{D} mm:\n")
        w(table(["interface", "case", "F N", "p mean kPa", "p peak kPa", "limit kPa", "peak/limit", "SF short", "SF sustained"], rows))
    w(f"Pads on skin: Winkler thin-layer peak = {sp.PEAK_FACTOR:g} × mean (paraboloid on a bed of springs) [C]; screw heads and serration flanks: "
      "bearing on PETG (S_bear) [DS]; link wire on the brass sleeve: Hertz line contact [STD]; eye insert: lateral bearing on the boss "
      "with the moment of the sleeve height [C].\n")

# ------------------------------------------------------------------------------------------------ 13 joints
w("## 13. Joints, fasteners, inserts, fits, twist lock\n")
w(st.serrated_joint.__doc__ + "\n")
if JT:
    for D in ("50", "60"):
        rows = []
        for x in JT.get(D, []):
            s_, b_, mn = x["serrated"], x["friction_only"], x["min"]
            rows.append([x["cat"], x["arm"], f"{f(s_.get('Fi_min'))}–{f(s_.get('Fi_max'))}", s_["Fi_eff"], s_["D_screw"], mn["SF_engage"], mn["SF_pullout"],
                         s_.get("SF_pullout_nom"), mn["SF_slot"], s_["SF_spin"], s_["SF_tooth"], b_["SF_slip"]])
        w(f"{D} mm — minimum over every load combination of each category (F_i range, D_screw and the nominal-preload pull-out SF shown for "
          "the combination with the lowest engagement SF):\n")
        w(table(["case", "arm", f"F_i range N (K {mt.NUT_FACTOR_K_RANGE[1].v:.2f}–{mt.NUT_FACTOR_K_RANGE[0].v:.2f})", "F_i after creep (from the lowest) N", "D_screw N", "SF engage (≥1)",
                 "SF insert pull-out at the highest F_i (≥1)", "pull-out SF at nominal F_i", "SF slot bearing (≥1)",
                 "SF spin-out", "SF tooth shear", "plain joint: SF slip"], rows))
    sc = (WT or {}).get("pitch_torque_scan")
    if sc:
        pts = sorted({x["pitch"] for x in sc}); tqs = sorted({x["torque"] for x in sc})
        cell = {(x["pitch"], x["torque"]): x for x in sc}
        w5 = next((v for k, v in WT.items() if k.startswith("W5") and "delta" in v), None)
        w(f"{FINAL['arm_screw']} arm joint under the {FH} N handling load (50 mm, all arms): lowest engagement / pull-out SF over the insert pitch "
          "(rows) and the tightening torque (columns). Both must be ≥ 1: more torque helps engagement and hurts pull-out, a wider "
          "pitch helps both (shorter pry lever ratio)"
          + (f" and costs {f(-w5['delta'] * 1e3)} g per mm per side (§5, W5)" if w5 and w5["delta"] < 0 else "") + ":\n")
        w(table(["insert pitch mm"] + [f"{t:.2f} N·m: engage / pull-out" for t in tqs],
                [[p_] + [f"{f(cell[(p_, t)]['SF_engage'])} / {f(cell[(p_, t)]['SF_pullout'])}" for t in tqs] for p_ in pts]))
        ch = min(cell.get((FINAL["arm_screw_pitch"], FINAL["arm_torque"]), {}).get(k_, float("nan")) for k_ in ("SF_engage", "SF_pullout"))
        nar = [(min(x["SF_engage"], x["SF_pullout"]), x["pitch"], x["torque"]) for x in sc if x["pitch"] < FINAL["arm_screw_pitch"] - 1e-9]
        bn = max(nar) if nar else None
        w(f"Chosen: {FINAL['arm_screw_pitch']:g} mm at {FINAL['arm_torque']:.2f} N·m, lowest SF {f(ch)}"
          + (f"; the best narrower combination ({bn[1]:g} mm at {bn[2]:.2f} N·m) keeps {f(bn[0])}" if bn else "")
          + f". The margin is wanted on engagement, which rests on the least certain input (the {st.CREEP_YEARS:g}-year creep of the clamped PETG).\n")
    hj = F["50"]["handling"].get("joint") if F else None
    if hj:
        w(f"{FH} N handling load at one pad ({NDH} directions), 50 mm — minimum joint SFs per arm: " + "; ".join(
            f"{a}: engage {f(v.get('SF_engage'))}, pull-out {f(v.get('SF_pullout'))}, slot {f(v.get('SF_slot'))}" for a, v in hj.items()) + ".\n")
    w("'Plain joint' = the same section forces on a friction-only slotted clamp (Design A/B): where its SF is < 1 it slips — the reason "
      "for the serrations.\n")
    _cw = [x["wall"] for x in JT["inserts"] if x.get("role") == "counter-example"]
    w("Heat-set insert bosses (the design walls: the rule or the {:g} mm minimum wall, whichever is larger; ring tabs have {:g} mm"
      .format(dz.INSERT_WALL_MIN, dz.TAB_WALL) + (f"; and a {f(_cw[0])} mm wall as the counter-example that the wall rule excludes" if _cw else "") + "):\n")
    w(table(["insert", "role", "wall mm", f"rule wall ≥ {dz.INSERT_WALL_RULE:g}·OD", "hoop MPa", "SF (interlayer)"],
            [[x["size"], x.get("role", ""), x["wall"], bool(x["rule_ok"]), x["hoop"] / 1e6, x["SF"]]
             for x in JT["inserts"]]))
    fb = JT.get("felt_bond") or {}
    if fb:
        _hd = [JT["link_eye"]["boss_d"] - v["hole_d"] for v in fb.values() if v.get("hole_d")] if JT.get("link_eye") else []
        _prm = ex.P_REAR_MAX.v
        w(f"Rear felt: a die-cut disc pushed over the link-eye boss (hole {f'{min(_hd):g}' if _hd else '–'} mm under the boss diameter, so no air by-passes the felt "
          "there; §17 chain) and bonded to the inside of the cup end by an acrylic PSA rim outside the grille. It replaces the "
          f"press-fit PETG retainer ring of the earlier iteration, which failed its own check (sustained hoop SF "
          f"{f(min(v['upper_tolerance']['SF'] for v in (JT.get('felt_retainer_rejected') or {}).values()) if JT.get('felt_retainer_rejected') else None)}"
          f"–{f(max(v['upper_tolerance']['SF'] for v in (JT.get('felt_retainer_rejected') or {}).values()) if JT.get('felt_retainer_rejected') else None)} "
          "at the upper interference tolerance) and would clash with the eye boss, which now stands inside the cup so the insert has its full "
          f"length in solid material. Loads pulling the felt off: its inertia at 5 g plus a rear-cavity pressure amplitude of {_prm:g} Pa "
          f"({20 * math.log10(_prm / math.sqrt(2) / 20e-6):.0f} dB SPL) [A] on its free area; capacity: the rim peels from its inner edge all "
          f"round at ≥ {ex.PSA_PEEL.v / 100:g} N/cm [A]:\n")
        w(table(["D", "felt g", "hole Ø mm", "load N", "peel capacity N", "SF"],
                [[D, v["m_felt"] * 1e3, v["hole_d"], v["F"], v["capacity"], v["SF"]] for D, v in fb.items()]))
    le = JT["link_eye"]
    w(f"Link eye on the cup ({str(le['D']) + ' mm module: the largest donning load of the five' if le.get('D') else str(an.LINK_REF_D) + ' mm module'}): P = {f(le['P'])} N on the "
      f"{an.LINK_REF_D} mm reference, donning {f(le['P_don'])} N. The wire eye wraps a brass sleeve (r_i = {f(le['r_i'] * 1e3)} mm ≥ {mt.WIRE['min_bend_radius_d'].v:g} d): "
      f"line load q = P_don/r_i (wire tension on the pin, rope bound; a cosine pin-bearing distribution gives 2/π = {2 / math.pi:.2f} of it) = {f(le['q0'])} N/m, Hertz half-width {f(le['hertz']['b'] * 1e6)} µm, p0 {f(le['hertz']['p0'] / 1e6)} MPa, "
      f"τ_max ≈ {ex.TAU_LINE:g} p0 → SF {f(le['SF_brass'])} on brass shear yield (Tresca, 0.5 × {mt.BRASS['Sy'].v / 1e6:g} MPa [LIT]); the M2.5 insert bears laterally on the boss (rigid short pile in an elastic bed, peak p = P/(d L)·(4 + 6e/L), e = {le.get('e', 2e-3) * 1e3:g} mm, the sleeve mid-height) at {f(le['p_insert'] / 1e6)} MPa "
      f"(SF {f(le['SF_insert'])} sustained).\n")
    fs = JT.get("foam_spec", {})
    if fs:
        w(f"Twist lock (UMI-2): the lug bottoms bear on the rigid groove floor; PSA-backed foam strips on the lug tops only keep the module "
          f"rattle-free off the head and set the assembly torque. Derived foam specification: CFD25 window {f(fs['cfd25_lo'] / 1e3)}–"
          f"{f(fs['cfd25_hi'] / 1e3)} kPa over all modules (feasible: {f(fs['feasible'])}); specified {f(fs['cfd25_spec'] / 1e3)} kPa "
          f"(governing: {fs['governing_lo']} mm low end, {fs['governing_hi']} mm high end).\n")
    rows = []
    for D in SIZES:
        t = JT.get(f"twistlock_{D}")
        if t:
            rows.append([D, t["m_module"] * 1e3, t["P_link"], t["F_foam_lo_after_set"], t["T_ramp_max"], t["T_hold_onhead"], t["SF_floor"],
                         t["a_lift_g"], t["SF_cone"], t["SF_root_shear"], t["SF_root_bend"], t["SF_hertz"]])
    w(table(["D", "module g", "P N", "foam F after set N", "twist torque max N·m", "hold torque on head N·m", "SF floor (sustained)",
             "lift-off accel g", "SF cone bearing", "SF lug root shear", "SF lug root bending", "SF Hertz spigot"], rows))
    g = JT.get("designB_gasket")
    if g:
        w(f"Design B's squeezed TPU gasket for comparison: nominal squeeze {g['chain']['nom']:.3g} mm, Monte-Carlo range "
          f"{f(g['chain']['mc_lo'])} … {f(g['chain']['mc_hi'])} mm — from zero (rattle) to over-tight: lock torque at the high end "
          f"{f(g['mc_hi']['T_lock'])} N·m.\n")

# ------------------------------------------------------------------------------------------------ 14 cable
w("## 14. Cable loads\n")
w(cb.__doc__ + "\n")
if CB:
    for nm in ("B", "Final"):
        c = CB[nm]
        w(f"{nm}: cable weight {f(c['weight'])} N; clip grip {f(c['clip']['F_clip'])} N (contact p {f(c['clip']['p'] / 1e6)} MPa); plug {f(c['plug'])} N "
          f"(upper {f(c['plug_upper'])} N); force reaching the cradle before release {f(c['fuse'])} N (upper {f(c['fuse_upper'])} N); clip grip below the plug retention: {f(bool(c['order_ok']))}.\n")
    _iv = CB.get("interf_values")
    _ivt = (" / ".join(f"{x_:g}" for x_ in _iv) + " mm") if _iv else "0 / nominal / nominal + bore tolerance"
    w(f"Clip grip across the FDM tolerance of the bore (interference {_ivt}): {', '.join(f(x) for x in CB['interf_range'])} N — the grip cannot be "
      "set by interference within printing tolerance, so the clip is a routing guide and the plug is the fuse.\n")
    if "tug_limits" in CB:
        names = list(next(iter(CB["tug_limits"].values()))["named"].keys())
        rows = [[k] + [CB["tug_limits"][D]["named"][k] for D in CB["tug_limits"]] for k in names]
        rows.append(["minimum over the downward hemisphere"] + [CB["tug_limits"][D]["sphere_min"] for D in CB["tug_limits"]])
        w("Tug limits while worn — the cable pull at the clip that the cradle takes before gross slip (support model, bisection):\n")
        w(table(["pull direction"] + [f"{D} mm N" for D in CB["tug_limits"]], rows))
        hz = [CB["tug_limits"][D]["named"][k] for D in CB["tug_limits"] for k in names if "below" in k]
        dn = [CB["tug_limits"][D]["named"]["down"] for D in CB["tug_limits"] if "down" in CB["tug_limits"][D]["named"]]
        fu = CB["Final"]["fuse"]
        _fhi = CB.get("tug_F_hi", ex.TUG_F_HI)
        cap = lambda v: (f"≥ {_fhi:g}" if v > _fhi * (1 - 2e-3) else f(v))
        w(f"Near-horizontal tugs (out, forward, back) of {cap(min(hz))}–{cap(max(hz))} N release the cradle"
          + (f", less than the {f(fu)} N that reaches the cradle before the plug lets go" if max(hz) < fu else "")
          + (f"; straight down it takes {cap(min(dn))}–{cap(max(dn))} N" if dn else "")
          + ". The cable must therefore be routed down the neck — a user instruction.\n![tug limits](fig/tug_limits.png)\n")
        rows = [[D, k, v["F"][2], str(v["held"]), v.get("Fn_min")] for D, pl in CB["plug"].items() for k, v in pl.items()]
        w(table(["D", "plug action while worn", "F_z N", "cradle held", "min skin-pad Fn N"], rows))
        acts = {}
        for D, pl in CB["plug"].items():
            for k, v in pl.items():
                if not v["held"]:
                    acts.setdefault(k, []).append(D)
        w(("Plug actions that release the worn cradle: " + "; ".join(f"{k} ({', '.join(v)} mm)" for k, v in acts.items())
           + " — plug in and out off the head (instruction).\n") if acts else "The cradle holds every plug action while worn.\n")
    if "anchor" in CB:
        rows = [[k, v["size"], v["torque"], v["T_ext"], v["Fi"], v["Fi_eff"], v["SF_initial"], v["SF_aged"], v["lever_mm"]]
                for k, v in CB["anchor"].items()]
        w("Cable anchor screws (prying about both axes, joint factor 1; capacity = pull-out / γ_insert):\n")
        w(table(["cable load case", "screw", "torque N·m", "T_ext per screw N", "F_i N", "F_i aged N", "SF initial", "SF aged", "lever mm"], rows))
        rows = [[k, v["F"], v["SF_side"], v["SF_upright"]] for k, v in CB["clip_post"].items()]
        w("Clip post (cantilever from the anchor block): printed on its side the bending is in-layer; upright it would load the layers in tension:\n")
        w(table(["cable load case", "F N", "SF printed on its side", "SF if printed upright"], rows))

# ------------------------------------------------------------------------------------------------ 15 dynamics
w("## 15. Natural frequencies and vibration isolation\n")
w(dy.__doc__ + "\n")
if DY:
    rows = [[D] + [f"{f(x)} ({n})" for x, n in zip(r["rigid"]["f"], r["rigid"]["names"])] for D, r in DY.items()]
    w(table(["D", "mode 1 Hz", "2", "3", "4", "5", "6"], rows))
    _ar = {D: {a: (v["k"], v["m_eff"], v["f1"]) for a, v in r["arms"].items()} for D, r in DY.items()}
    _same = all(abs(_ar[D][a][i] - _ar["50"][a][i]) <= 1e-3 * abs(_ar["50"][a][i]) for D in _ar for a in _ar["50"] for i in range(3))
    rows = [["all" if _same else D, a, v["k"], v["m_eff"] * 1e3, v["f1"]] for D, r in DY.items() for a, v in r["arms"].items()
            if D == "50" or not _same]
    w(table(["D", "arm", "k_z N/m", "m_eff g", "f1 Hz"], rows))
    rows = [[D, r["isolation"]["k"], r["isolation"]["S"], r["isolation"]["fn"], r["isolation"]["iso_from"]] for D, r in DY.items()]
    w(table(["D", "driver gasket k N/m", "shape factor", "f_n Hz", "isolates above Hz"], rows))
    rows = [[k, o["E"] / 1e6, o["k"], o["fn"], o["iso_from"], o["T_100"], o["T_1k"], o["T_5k"], o["sag_5g_um"]]
            for k, o in DY["50"]["isolation_options"].items()]
    w("Driver mounting options at 50 mm (Gent E(Shore) [EMP] for the silicone rings, same shape factor):\n")
    w(table(["mount", "E MPa", "k N/m", "f_n Hz", "isolates above Hz", "T(100 Hz)", "T(1 kHz)", "T(5 kHz)", "5 g sag µm"], rows))
    io = DY["50"]["isolation_options"]
    sil = [o for k, o in io.items() if k.startswith("silicone")]
    tpu = next((o for k, o in io.items() if "Final" in k), None)
    rig = [x for D in DY for x in DY[D]["rigid"]["f"]]
    arms_f = {a: min(DY[D]["arms"][a]["f1"] for D in DY) for a in DY["50"]["arms"]}
    pad_f = [v for a, v in arms_f.items() if a != "saddle"]
    txt = ""
    if sil and tpu:
        txt += (f"Soft silicone rings put the driver-on-mount resonance at {f(min(o['fn'] for o in sil) / 1e3)}–"
                f"{f(max(o['fn'] for o in sil) / 1e3)} kHz, inside the audio band (they amplify there and isolate only above √2 f_n); "
                f"the TPU 95A rim gasket puts it at {f(tpu['fn'] / 1e3)} kHz, above the range where the lumped model is claimed (§21: "
                "measure it), and it also seals the rim — it is kept. ")
    _fh = dy.F_HEAD[1]; _rh = _fh / min(rig)
    txt += (f"On the skin the whole headphone has its rigid-body modes at {f(min(rig))}–{f(max(rig))} Hz, above the head-motion band "
            f"({dy.F_HEAD[0]:g}–{_fh:g} Hz [A]): the headphone follows the head quasi-statically, amplified by at most "
            f"T = 1/(1 − r²) = {f(1 / (1 - _rh ** 2))} (undamped bound, lowest mode, {_fh:g} Hz). Free-arm first modes (Rayleigh, no skin contact): pad arms "
            f"{f(min(pad_f))}–{f(max(pad_f))} Hz")
    if "saddle" in arms_f:
        txt += (f", saddle arm {f(arms_f['saddle'])} Hz" + (" — inside the bass band; on the head the root and scalp contacts add "
                "stiffness and damping, which this free-arm value leaves out, so a buzz check in the sine sweep is in the test plan (§22)"
                if arms_f["saddle"] < 300 else ""))
    w(txt + ".\n")
    w("![isolation](fig/driver_isolation.png)\n")

# ------------------------------------------------------------------------------------------------ 16 acoustics
w("## 16. Acoustics\n")
w(ac.__doc__ + "\n")
if AC:
    rows = []
    for D in SIZES:
        g = AC["geometry"][D]; cbx = AC["closed_box"][D]; T = AC["ts"][D]; m = AC["modes"][D]
        rows.append([D, g["Vb"] * 1e6, T["Vas"] * 1e6, cbx["alpha"], T["Qts"], cbx["Qtc"], T["Fs"], cbx["Fc"], g["n_holes"], m["cup"]["radial_11"], m["cup"]["axial_1"], m["gap_standing"]])
    w(table(["D", "Vb cm³ [CAD]", "Vas cm³", "α = Vas/Vb", "Qts", "Qtc (closed)", "Fs Hz", "Fc Hz (closed)", "grille holes", "cup (1,1) Hz", "cup axial Hz", "gap λ/2 Hz"], rows))
    fc = [AC["closed_box"][D]["Fc"] for D in SIZES]; qc = [AC["closed_box"][D]["Qtc"] for D in SIZES]
    w(f"**Consequence:** a closed rear raises the resonance to Fc = {f(min(fc))}–{f(max(fc))} Hz with Qtc = {f(min(qc))}–{f(max(qc))} — "
      "unusable. Hence the open, felt-damped rear (default) or a heavily vented rear.\n")
    def _fh(D, ratio):
        rs_ = AC["helmholtz_aperture"][D]
        r_ = min(rs_, key=lambda r: abs(r["ratio"] - ratio))
        return f"{f(r_['fH'] / 1e3)} kHz" if abs(r_["ratio"] - ratio) < 0.006 else "–"
    _rat = sorted({0.6, 0.75, 1.0} | {round(r_["ratio"], 3) for D in SIZES for r_ in AC["helmholtz_aperture"][D] if r_.get("chosen")})
    _chr = {round(r_["ratio"], 3) for D in SIZES for r_ in AC["helmholtz_aperture"][D] if r_.get("chosen")}
    rows = [[D] + [_fh(D, q_) for q_ in _rat] for D in SIZES]
    w("Baffle aperture: diaphragm-to-aperture mini-cavity + aperture tube Helmholtz resonance f = c/2π·√(S/(V·L_eff)), "
      f"L_eff = t + ({ac.AP_INNER:g} + 1)·{ac.END_FLANGED:g}a: the outer end correction is the baffled piston's radiation mass, the inner one "
      "is reduced by the chamfer and the nearby diaphragm [A] (the same aperture mass as in the response model):\n")
    w(table(["D"] + [f"aperture {q_:.2f} D" + (" (chosen)" if q_ in _chr else "") for q_ in _rat], rows))
    ch = [r_["fH"] for D in SIZES for r_ in AC["helmholtz_aperture"][D] if r_.get("chosen")]
    w(f"Aperture = {dz.FRONT_OPEN_RATIO:g} D [A] (not D): it clears the moving diaphragm and half the surround and overlaps the driver's front frame lip "
      f"so the rim gasket seals; the 45° × {FINAL['aperture_chamfer']:g} mm chamfer removes the sharp step."
      + (f" The front mini-cavity resonance is then at {f(min(ch) / 1e3)}–{f(max(ch) / 1e3)} kHz — inside the audio band and above "
         "the range where the lumped model is claimed, so its level and damping are left to measurement (§21, §22); widening the "
         "aperture to D raises it only to the last column." if ch else "") + "\n")
    rows = [[str(int(r["n"])), r["d"], r["fb"], r["L_eff"] * 1e3] for r in AC["vent"]["50"]]
    w(f"Vent (rear port) Helmholtz, 50 mm cup, end corrections {ac.END_FLANGED:g} r (flanged, inside) + {ac.END_UNFLANGED:g} r (unflanged, outside) [STD]:\n")
    w(table(["n vents", "Ø mm", "f_b Hz", "L_eff mm"], rows))
    w(f"Sealed front (seal-pad option): V_f = {f(AC['sealed_Vf'] * 1e6)} cm³ [C: skin to ring face inside the seal ID plus the module "
      f"recess in the bore, minus {ac.V_PINNA * 1e6:g} cm³ of pinna A]; leak = slit between pad and skin "
      "(R = 12μL/(h³b), M = 1.2ρL/(hb)).\n")
    if "seal_sweep" in AC:
        sp_ = AC["seal_params"]
        w(f"Seal pad material × height at the pressure the preload can spare ({sp_['p'] / 1e3:g} kPa [A]): conformity δ = pH/E against a head "
          f"irregularity of {sp_['a_irr'] * 1e3:g} mm [A] leaves a slit h = max({sp_['h_min'] * 1e3:g} mm, a − δ); bass loss against a perfect seal:\n")
        rows = [[r["material"], r["E"] / 1e3, r["H_mm"], r["delta_mm"], r["leak_mm"], r["loss_50"], r["loss_100"]] for r in AC["seal_sweep"]["50"]]
        w(table(["material", "E kPa", "H mm", "δ mm", "slit mm", "loss 50 Hz dB", "loss 100 Hz dB"], rows))
        Emin = min(sp_["materials"].values()); mat_min = min(sp_["materials"], key=sp_["materials"].get)
        Hmax = max(r["H_mm"] for r in AC["seal_sweep"]["50"]) * 1e-3
        p_need = (sp_["a_irr"] - sp_["h_min"]) * Emin / Hmax
        w(f"Closing the {sp_['a_irr'] * 1e3:g} mm irregularity down to the {sp_['h_min'] * 1e3:g} mm slit with the softest material "
          f"({mat_min}, the tallest pad {Hmax * 1e3:g} mm) needs p = (a − h_min)·E/H = {f(p_need / 1e3)} kPa, "
          f"{f(p_need / sp_['p'])} × the {sp_['p'] / 1e3:g} kPa the preload can spare — so the Final is open (the seal pad stays an "
          "option for users who accept the pressure).\n![seal](fig/seal_sweep.png)\n")
    w("Damping: felt disc (flow resistivity σ, thickness t) at the cup end, R = σ t / A; it sits at the pressure antinode of the cup axial "
      "mode and in series with the grille, adding resistance behind the diaphragm (lower Q at Fs) and absorbing the cup modes above.\n")
    w("![acoustic sweeps](fig/acoustic_sweeps.png)\n![impedance](fig/impedance.png)\n![aperture](fig/aperture_helmholtz.png)\n")
    def _spl(c, fq):
        return float(np.interp(fq, c["f"], c["spl"]))
    rr = AC.get("rear", {}); dd_ = AC.get("dist", {})
    rtxt = ", ".join(f"{k} {f(_spl(v, 100))} dB" for k, v in rr.items())
    dz_ = sorted(dd_, key=float)
    _z = AC.get("z_ear"); _zi = AC.get("z_ear_inputs") or {}
    _zt = (f"{_z * 1e3:g} mm from the aperture to the ear-canal entrance: standoff {_zi['standoff']:g} + module recess {_zi['z_mod0']:g} − "
           f"(mean pinna protrusion {_zi['pinna_protrusion_mean']:g} − concha depth {_zi['concha_depth']:g}) mm [CAD, A/LIT]"
           if _z and _zi else "reference distance")
    dtxt = (f"Aperture-to-ear distance {float(dz_[0]):g} → {float(dz_[-1]):g} mm costs {f(_spl(dd_[dz_[0]], 100) - _spl(dd_[dz_[-1]], 100))} dB at 100 Hz and "
            f"{f(_spl(dd_[dz_[0]], 1000) - _spl(dd_[dz_[-1]], 1000))} dB at 1 kHz (near-field term e^{{−jkz}} − e^{{−jk√(z²+a²)}}) — keep the "
            "module close; the standoff is set by the p95 pinna." if len(dz_) > 1 else "")
    w(f"Open vs semi-open vs closed (50 mm, {_zt}; SPL at 100 Hz for the same drive: {rtxt}): open (grille + felt) keeps "
      "Fs low and the response smooth but, being open off the ear, loses bass to front/rear cancellation; vented is a compromise; "
      "closed is unusable with these cup volumes. " + dtxt + "\n")

# ------------------------------------------------------------------------------------------------ 17 tolerance
w("## 17. Tolerance stack-ups\n")
w(tl.__doc__ + "\n")
if TO:
    for D, st_ in TO.items():
        rows = [[k, v["nom"], f"{f(v['wc'][0])} … {f(v['wc'][1])}", f"{f(v['rss'][0])} … {f(v['rss'][1])}", f"{f(v['mc_p0135'])} … {f(v['mc_p99865'])}",
                 v["crit"]["min"], v["crit"]["max"], v["limiting"], pf(v["ok"]), pf(v["ok_wc"])] for k, v in st_.items()]
        w(f"Driver {D} mm:\n")
        w(table(["chain", "nominal mm", "worst case", "RSS", "MC ±3σ", "min", "max", "limiting component", "MC ok", "WC ok"], rows))
    _mc_bad = sorted({k for st_ in TO.values() for k, v in st_.items() if not v["ok"]})
    _wc_bad = {}
    for D, st_ in TO.items():
        for k, v in st_.items():
            if not v["ok_wc"]:
                lo_, hi_ = v["crit"]["min"], v["crit"]["max"]
                out_ = max((lo_ - v["wc"][0]) if lo_ is not None else 0.0, (v["wc"][1] - hi_) if hi_ is not None else 0.0)
                _wc_bad[k] = max(_wc_bad.get(k, 0.0), out_)
    w((f"Every chain meets the ±3σ window for every size checked ({', '.join(f'{D} mm' for D in TO)})." if not _mc_bad else
       f"Chains outside the ±3σ window: {', '.join(_mc_bad)} — **not acceptable**.")
      + (" At the worst case " + "; ".join(f"{k} leaves the window by up to {f(v)} mm" for k, v in _wc_bad.items())
         + ": each needs every term at its 3σ limit at once, which the statistical criterion accepts; the rare part pair that "
           "lands there is found at assembly (fit check)." if _wc_bad else " The worst cases also stay inside the windows.") + "\n")

# ------------------------------------------------------------------------------------------------ 18 sweeps
w("## 18. Structural and support parameter sweeps (50 mm)\n")
if SW:
    rows = [[x["key"], f"{f(x['bar_t'])}/{f(x['leg_t'])}/{f(x['foot_t'])}", x["env"][0][0], x["env"][0][1], x["env"][1][0], x["handling"][0][0],
             x["handling"][0][1], x["handling"][1][0], x["k_arm_mastoid"], (x.get("onset") or {}).get("min")] for x in SW.get("arm_thickness", [])]
    w("Arm (frame) thickness — bar, leg and foot scaled together:\n")
    w(table(["scale", "bar/leg/foot mm", "5 g SF vM", "at", "5 g SF interlayer", "handling SF vM", "at", "handling SF interlayer", "k_arm mastoid N/m", "5 g onset λ min"], rows))
    rows = [[x["size"], x["T"], x["min_SF"], x["governing"], x["Fi"], x["Fi_eff"], x["D_screw"], x["SF_engage"], x["SF_pullout"], x["SF_spin"], x["SF_slot"], x["mass_pair_g"]]
            for x in SW.get("screw_size", [])]
    w("Arm screw size and torque (serrated joint under the 5 g envelope and the handling load):\n")
    w(table(["screw", "T N·m", "min SF", "governing", "F_i N", "F_i aged N", "D_screw N", "SF engage", "SF pull-out", "SF spin", "SF slot", "pair mass g"], rows))
    w(table(["pad (TPU) h mm", "static mastoid p kPa", "static tilt deg", "static μ demand", "1 g %", "1 g tilt", "2 g %"],
            [[x["key"], x.get("static_p", {}).get("M mastoid", float("nan")) / 1e3, x.get("static_tilt"), x.get("static_mu_demand"), 100 * x["1 g normal"]["slip"],
              x["1 g normal"]["tilt"], 100 * x["2 g dynamic"]["slip"]] for x in SW.get("pad_thickness", [])]))
    w(table(["pad radius scale (support spacing)", "static", "1 g %", "1 g tilt", "2 g %"],
            [[x["key"], bool(x["static_ok"]), 100 * x["1 g normal"]["slip"], x["1 g normal"]["tilt"], 100 * x["2 g dynamic"]["slip"]] for x in SW.get("support_spacing", [])]))
    w(table(["Δ temporal angle", "Δ post angle", "static", "1 g %", "1 g tilt", "2 g %"],
            [[x["key"][0], x["key"][1], bool(x["static_ok"]), 100 * x["1 g normal"]["slip"], x["1 g normal"]["tilt"], 100 * x["2 g dynamic"]["slip"]] for x in SW.get("support_angle", [])]))
    w(table(["arch ('hook') R mm", "half-angle °", "root p kPa (static)", "1 g %", "2 g %"],
            [[x["key"][0], x["key"][1], max((v for k, v in x.get("static_p", {}).items() if k.startswith("S root")), default=float("nan")) / 1e3,
              100 * x["1 g normal"]["slip"], 100 * x["2 g dynamic"]["slip"]] for x in SW.get("saddle_arch", [])]))
    def _rootp(x):
        return max((v for k, v in x.get("static_p", {}).items() if k.startswith("S root")), default=float("nan")) / 1e3
    if SW.get("root_liner"):
        w("Saddle liner thickness (60 mm module, its own eye):\n")
        w(table(["liner mm", "root p kPa (static)", "static μ demand", "1 g %", "1 g tilt deg", "2 g %"],
                [[x["key"], _rootp(x), x.get("static_mu_demand"), 100 * x["1 g normal"]["slip"], x["1 g normal"]["tilt"],
                  100 * x["2 g dynamic"]["slip"]] for x in SW["root_liner"]]))
    if SW.get("liner_material"):
        w(table(["liner material (60 mm)", "root p kPa (static)", "static μ demand", "1 g %", "2 g %"],
                [[x["key"], _rootp(x), x.get("static_mu_demand"), 100 * x["1 g normal"]["slip"], 100 * x["2 g dynamic"]["slip"]]
                 for x in SW["liner_material"]]))
    if SW.get("kt_ratio"):
        w("Tangential/normal contact-stiffness ratio k_t/k_n [A] (it decides how much weight the pads take by friction):\n")
        w(table(["k_t/k_n (60 mm)", "root p kPa (static)", "static μ demand", "1 g %", "1 g tilt deg", "2 g %"],
                [[x["key"], _rootp(x), x.get("static_mu_demand"), 100 * x["1 g normal"]["slip"], x["1 g normal"]["tilt"],
                  100 * x["2 g dynamic"]["slip"]] for x in SW["kt_ratio"]]))
    w("![sweeps](fig/structure_support_sweeps.png)\n![angles](fig/support_angle_arch.png)\n")

# ------------------------------------------------------------------------------------------------ 19 worst case
w("## 19. Worst-case summary and limiting components\n")
LIM = []      # (check, where, value, requirement, utilisation = demand / allowed)
if F and JT and TO:
    p_s = mt.TISSUE["p_sustained"].v; p_t = mt.TISSUE["p_transient"].v; gM = mt.GAMMA_M_PRINT.v
    worst_h = min(((min_sf(F[D]["handling"]["sf"]), D) for D in SIZES), key=lambda t: t[0][0])
    worst_5 = min(((min_sf(F[D]["arm_sf"]["5 g accidental"]), D) for D in SIZES), key=lambda t: t[0][0])
    worst_1 = min(((min_sf(F[D]["arm_sf"]["1 g normal"]), D) for D in SIZES), key=lambda t: t[0][0])
    LIM.append([f"arm section, {FH} N handling, {TSV} °C", f"{worst_h[1]} mm, {worst_h[0][1]}", worst_h[0][0], f"SF ≥ γM {f(gM)}", gM / worst_h[0][0]])
    LIM.append([f"arm section, 5 g onset envelope, {TSV} °C", f"{worst_5[1]} mm, {worst_5[0][1]}", worst_5[0][0], f"SF ≥ γM {f(gM)}", gM / worst_5[0][0]])
    LIM.append(["arm section, 1 g sustained", f"{worst_1[1]} mm, {worst_1[0][1]}", worst_1[0][0], f"SF ≥ γM {f(gM)}", gM / worst_1[0][0]])
    fat = [(D, x) for D in SIZES for x in F[D].get("fatigue", [])[:1]]
    if fat:
        Dm, xm = min(fat, key=lambda t: t[1]["SF"])
        LIM.append([f"arm section, fatigue {sci(st.N_FATIGUE)} cycles (2 g held envelope, zero-to-peak)", f"{Dm} mm, {xm['arm']}: {xm['section']}",
                    xm["SF"], f"SF ≥ γM {f(gM)}", gM / xm["SF"]])
    for D in ("50", "60"):
        rs = JT.get(D, [])
        if rs:
            je = min(rs, key=lambda x: x["min"]["SF_engage"]); jp = min(rs, key=lambda x: x["min"]["SF_pullout"])
            LIM.append([f"arm joint engagement ({D} mm)", f"{je['arm']}, {je['cat']}", je["min"]["SF_engage"], "SF ≥ 1 with aged preload",
                        1 / je["min"]["SF_engage"]])
            LIM.append([f"arm joint insert pull-out ({D} mm)", f"{jp['arm']}, {jp['cat']}", jp["min"]["SF_pullout"],
                        "SF ≥ 1 on the design value (γ = 2 inside)", 1 / jp["min"]["SF_pullout"]])
    if CB.get("anchor"):
        k_, v_ = min(CB["anchor"].items(), key=lambda kv: kv[1]["SF_initial"])
        LIM.append(["cable anchor insert pull-out", k_, v_["SF_initial"], "SF ≥ 1 (γ = 2 inside)", 1 / v_["SF_initial"]])
    for D in SIZES:
        dem = F[D]["support"].get("static_mu_demand") or {}
        if dem:
            k_ = max(dem, key=dem.get)
            LIM.append([f"static friction demand ({D} mm)", f"{padn(k_)} pad", dem[k_], "μ_req/μ_design ≤ 1", dem[k_]])
    for D in SIZES:
        s0 = F[D]["support"]["static"]
        if s0["ok"]:
            pk = max(x["p_mean"] for x in s0["contacts"] if not x["name"].startswith("S root"))
            pr = max(x["p_mean"] for x in s0["contacts"] if x["name"].startswith("S root"))
            LIM.append([f"skin pressure static ({D} mm)", "max pad", pk / 1e3, f"≤ {f(p_s / 1e3)} kPa", pk / p_s])
            LIM.append([f"auricle-root pressure, donning A ({D} mm)", "arch zones", pr / 1e3,
                        f"≤ {f(p_s / 1e3)} kPa sustained (as donned; in use see the shakedown rows)", pr / p_s])
        _a = ((SK or {}).get("sizes", {}).get(D) or {}).get("A") or {}
        if _a.get("ok"):
            LIM.append([f"auricle-root pressure in use, after the head-motion shakedown ({D} mm)", "arch zones", _a["root_p"] / 1e3,
                        f"≤ {f(p_s / 1e3)} kPa sustained" + ("; NOT met (§6)" if _a["root_p"] > p_s else ""), _a["root_p"] / p_s])
    sb = F["60"]["support"].get("static_B", {})
    if sb.get("ok"):
        pb = max(x["p_mean"] for x in sb["contacts"] if x["name"].startswith("S root"))
        LIM.append(["root pressure if hung on the ear before clamping (donning B, 60 mm)", "arch zones", pb / 1e3,
                    f"≤ {f(p_s / 1e3)} kPa sustained (as donned)"
                    + ("; not met → clamp-first donning (A) is the instruction" if pb > p_s else ""),
                    pb / p_s])
    tmin = min(((k, v) for k, v in TO["60"].items()), key=lambda kv: (kv[1]["mc_p0135"] - kv[1]["crit"]["min"]))
    rows = sorted(LIM, key=lambda r_: -r_[4])
    _s2 = F['60']['support']['2 g dynamic']['slip_fraction']
    rows.append(["retention, 2 g set (60 mm)", "friction at pads + arch",
                 f"{f(100 * _s2)} % combos released", "0 % (strict) — " + ("met" if _s2 == 0 else "not met"), "–"])
    rows.append(["tolerance chain with least margin (60 mm)", tmin[0], f"MC low {f(tmin[1]['mc_p0135'])} vs min {f(tmin[1]['crit']['min'])}",
                 tmin[1]["limiting"], "–"])
    w("Sorted by utilisation (demand / allowed; 1 = at the limit). The 2 g retention is not a utilisation: it is the released "
      "fraction of the 2 g set of load combinations (§8):\n")
    w(table(["check", "where", "value", "requirement", "utilisation"], rows))

# ------------------------------------------------------------------------------------------------ 20 printing
w("## 20. Print orientation (per part) and why\n")
_lw = mpz.LINE_W * 1e3; _lh = mpz.LAYER * 1e3; _cw = FINAL["cup_wall"]
_n_per = 1 + int((_cw - _lw) / (_lw - _lh * (1 - math.pi / 4)) + 1e-9)   # slicer perimeter spacing w - h(1 - π/4) [LIT]
_cp = (CB or {}).get("clip_post") or {}
_cp_txt = (f"§14: lowest SF {f(min(v['SF_side'] for v in _cp.values()))} printed on its side, "
           f"{f(min(v['SF_upright'] for v in _cp.values()))} if printed upright" if _cp else "§14")
w(table(["part", "material", "orientation", "reason (anisotropy / supports / accuracy)"], [
    ["ring", "PETG", "head face down", f"groove floor = flat top surface, lip underside is a 45° cone (self-supporting); tab serration grooves on the bed face; lug-contact stress is in-layer compression; tabs end in a full round around the outer insert (wall ≥ {dz.TAB_WALL:g} mm)"],
    ["arms (4)", "PETG", "on the side (profile on the bed)", "all bending stress is along the arm in the layer plane; only transverse/torsion shear crosses layers (interlayer column, §12); serration teeth profile lies in the print plane (accurate)"],
    ["baffle", "PETG", "head face down", "lugs on the bed (flat bearing face); driver pocket floor is a top surface; aperture chamfer 45°"],
    ["cup", "PETG", "outer end down", f"grille/vents and the eye-boss insert hole on the bed; the eye boss rises inside the cup as a plain column; screw bosses full height; {_cw:g} mm wall = {_n_per} perimeters of {_lw:g} mm lines at {_lh:g} mm layers"],
    ["rear felt", "felt + PSA rim", "die-cut (not printed)", "pushed over the eye boss, bonded to the inside of the cup end"],
    ["cable anchor", "PETG", "on its side (tangential face on the bed; the STL is exported so)", f"clip-post bending in-layer ({_cp_txt})"],
    ["pads (3)", f"TPU 95A {100 * mpz.PRINT['pad_temporal'][3]:g} % gyroid", "flat base down", "dome needs no support; captive nut pocket in the base"],
    ["pad facings (2)", f"silicone {mt.SILICONE_GRADE}", "cast (not printed)", f"{FINAL['pad_face_t']:g} mm layer brushed or cast on the temporal and mastoid domes; mould reference STLs in stl/common/cast_reference"],
    ["saddle cap", "TPU 95A", "flat, skin face down", "arched bar in the bed plane (no overhang); open-top sleeve (no bridging); pin hole horizontal; bearing face recessed for the liner"],
    ["saddle liner", f"silicone {mt.SILICONE_GEL_GRADE}", "cast into the cap (not printed)", "mould reference STL in stl/common/cast_reference; prime the TPU (silicone does not bond to it unprimed) or key it; replaced with the cap"],
    ["driver gasket, clip, seal pad", "TPU 95A", "flat", "thin rings"],
    ["UMI foam strips", "PU foam, PSA", "die-cut", "template STL"]]))

# ------------------------------------------------------------------------------------------------ 21 FEA
w("## 21. Where FEA, acoustic simulation or tests are required\n")
w(f"""No FEA or BEM was run for this report; nothing here is presented as simulated.
* **Ring tab root and lug root** (3-D stress concentration where the tab joins the ring; lugs under drop impact): beam theory gives nominal values → solid FEA with orthotropic printed properties, and a drop test (1.5 m onto a hard floor [A]).
* **Arm bar at the clamp edge** (governs the handling load): a notched plate under combined bending and torsion; an FE model with the serration and slot geometry would replace the Kt = {st.KT_HOLE_BEND:g} hole factor.
* **Heat-set insert bosses**: the hoop-stress estimate assumes a {st.KNURL_FLANK_DEG:g}° knurl flank → FEA or, better, pull-out tests on printed coupons (§22). The link-eye insert sits in a column rising from the cup end and is loaded sideways by the link: FE of the boss or a lateral pull test.
* **Arm compliance** (it sets how much weight the auricle root carries, §6, §12): Timoshenko beams along the arm centreline; the corners (foot–leg, leg–bar) are stiffer than beam theory assumes, so the model errs towards softer arms → FE of one arm, or a load–deflection test of a printed arm at its pad.
* **Saddle cap on the auricle root** and the pads on skin: contact pressure on curved, layered soft tissue is not Hertzian → FE contact model or pressure-film measurement. The liner's compression modulus comes from the bonded-layer formula and the datasheet modulus: a load–deflection test of the lined cap on a skin simulant calibrates it (the §18 gel-modulus rows show what a factor of 2 does).
* **Acoustics above ~{ac.F_LUMPED / 1e3:g} kHz** (pinna, cup modes, grille, felt as a porous layer): BEM/FEM or measurement on a head-and-torso simulator; the lumped model is not claimed there.
* **Retention under real head motion**: IMU-recorded head kinematics replayed on a head form, or wear trials.
* **Weight migration onto the auricle root in use** (§6 shakedown): the model's friction is elastic–Coulomb without skin creep or
  re-sticking; the in-use root pressure it predicts is the first quantity to measure (pressure film at the root after wear with head motion).
""")

# ------------------------------------------------------------------------------------------------ 22 limitations & tests
w("## 22. Limitations and the measurements that replace the assumptions\n")
w(f"""| assumption | why it matters | measure |
|---|---|---|
| driver mass/geometry/T-S | mass, COM, acoustics | scale, calipers, impedance sweep + added-mass Vas |
| tissue moduli and thicknesses | contact stiffness → load sharing | not needed exactly: §9 sweep shows the sensitivity; comfort trials |
| friction μ (TPU and silicone on skin) | retention | incline test of a pad on forearm skin (dry/sweaty) |
| TPU pad effective modulus | contact stiffness, pressure | load–deflection of a printed pad |
| PETG strength/creep | joint preload loss | torque-retention test on a printed tab over 1 week at {TSV} °C |
| wave-washer rate and flat load | aged joint preload | washer datasheet; load–deflection check |
| tightening torque → preload (nut factor {mt.NUT_FACTOR_K_RANGE[0].v:.2f}–{mt.NUT_FACTOR_K_RANGE[1].v:.2f}) | insert pull-out at the highest preload, serration engagement at the lowest | torque–tension test of the {FINAL['arm_screw']} screw in a printed insert coupon |
| printed-arm stiffness (E, G at {TSV} °C) | load sharing between the pads and the auricle root | load–deflection of a printed arm at its pad |
| PSA peel strength on printed PETG | rear-felt bond | 90° peel of the chosen tape from a printed coupon |
| heat-set insert pull-out | arm and anchor joints | pull-out of inserts set in printed coupons |
| head angular accelerations | 2 g/3 g retention | phone IMU on a headband while walking/running |
| skin friction under cyclic load (elastic–Coulomb, no creep or re-sticking) | how fast and how far the weight migrates to the auricle root in use (§6 shakedown) | pressure film at the auricle root after 30 min of wear with walking, nodding and looking down |
| auricle root arch radius | saddle fit | photograph with a scale; the arch R is a CAD parameter |
| saddle-liner compression modulus (datasheet 100 % modulus, Gent–Lindley confinement) | auricle-root pressure vs mastoid friction | load–deflection of the lined cap; pressure film at the root in wear trials |
| k_t/k_n = {sp.KT_RATIO:g} for skin contacts | how much weight the pads take by friction | §18 sweep; shear load–deflection of a pad on the forearm |
| foam CFD25 | twist-lock feel, rattle | foam datasheet; compress a strip with a known weight |
| response above ~{ac.F_LUMPED / 1e3:g} kHz: front mini-cavity (aperture) resonance, driver-on-gasket resonance, cup modes | treble balance | frequency response on an ear simulator / head-and-torso simulator |
| saddle-arm free mode (Rayleigh, no skin contact) | possible buzz in the bass band | sine sweep 20–500 Hz at full level on a head form; accelerometer or listening at the saddle arm |
""")
w(f"The contact model is linear-elastic with small rotations (valid to ~{sp.ROT_MAX:g}°); once a case releases it is classified, not followed. "
  "The pinna capture that retains the cradle after slip is not modelled.\n")

# ------------------------------------------------------------------------------------------------ 23 files
w("## 23. Files\n")
w("""* `cad/umeh2.scad` + `cad/generated_params.scad` (50 mm default) + `cad/params_<D>.scad` — parametric CAD and the generated parameters.
* `stl/common/` — cradle parts (identical for every driver); `stl/common/cast_reference/` — silicone facing geometry; `stl/module_<D>mm/` — module parts per driver size (cups handed: eye position).
* `calc/umeh2/*.py` — the models (materials, design, massprops, support, layout, linkspring, structure, cable, dynamics, acoustics, tolerance, extras, analysis).
* `calc/legs_liner.py`, `calc/tune_eye.py`, `calc/run_all.py`, `calc/shakedown.py`, `calc/sweeps.py`, `calc/figures.py`, `calc/build_stl.py`, `calc/bom.py`, `calc/make_report.py`.
* `results/*.json` — every computed number; `report/fig/*.png`.
* `BOM.csv`, `docs/bom_table.md`.
""")

# ------------------------------------------------------------------------------------------------ headline findings (from the results)
H = []
if B and A:
    H.append(f"**Design B could not stay on the head** (§4, §6): static hold {pf(B['support']['static']['ok'])}, 1 g released "
             f"{f(100 * B['support']['1 g normal']['slip_fraction'])} % — the link eye on the mastoid pad puts the preload through the "
             "lowest contact, so nothing resists the tipping moment of the COM; Design A (UMEH-1 mass) is worse.")
if F:
    ok_all = [D for D in SIZES if all(v for k, v in F[D]["criteria"].items() if not k.startswith("2 g"))]
    nf = [x for x in (SW or {}).get("friction", []) if str(x["key"]).startswith("no facing") and x.get("static_mu_demand")]
    nf_txt = ""
    if nf:
        xw = max(nf, key=lambda x: x["static_mu_demand"])
        if xw["static_mu_demand"] > 1:
            nf_txt = (f"; with plain TPU domes the {padn(xw.get('static_mu_pad'))} pad would need {f(xw['static_mu_demand'])} × its "
                      "design friction at rest, which the cast silicone facing provides (§9)")
    _bad0 = [D for D, r in ((DP or {}).get("sizes") or {}).items() if not r.get("ok")]
    H.append(f"**Normal use (static + the 1 g grid, its dense check and the local refinement) passes for {', '.join(ok_all) + ' mm' if ok_all else 'no size'}** "
             f"{'(all five sizes)' if len(ok_all) == len(SIZES) else '(the others fail: §8)'} with an eye position per module and a common "
             f"link preload of {f(FINAL['link_preload'])} N tuned together (§7)" + nf_txt
             + (f". The first Final, tuned on a quasi-uniform 1 g sample at {f(((DP or {}).get('design') or {}).get('link_preload'))} N, fails the 1 g grid at "
                f"{len(_bad0)} of {len(DP['sizes'])} modules (§4 change 19, §8)" if _bad0 else "") + ".")
    _ska = [((SK or {}).get("sizes", {}).get(D) or {}).get("A") or {} for D in SIZES]
    _ska = [x for x in _ska if x.get("ok")]
    if _ska:
        _pu = [x["root_p"] for x in _ska]; _pd = [x["root_p_donned"] for x in _ska]; _ps = mt.TISSUE["p_sustained"].v
        _ml = (SK.get("mass_limit") or {})
        _gl = [x["label"] for x in SK.get("levers") or [] if x.get("ok") and x["root_p"] <= mt.TISSUE["p_sustained"].v
               and x["pad_p_max"] <= mt.TISSUE["p_sustained"].v]
        H.append((f"**In use the auricle root carries the weight — the sustained root-pressure target is NOT met** (§6): "
                  if max(_pu) > _ps else "**In use the auricle-root pressure stays within the sustained target** (§6): ")
                 + f"the pads micro-slip under normal head motion and hand the side's weight to the saddle; after that shakedown the "
                 f"root carries {f(min(_pu) / 1e3)}–{f(max(_pu) / 1e3)} kPa ({f(min(_pu) / _ps)}–{f(max(_pu) / _ps)} × {PSUS} kPa), "
                 f"against {f(min(_pd) / 1e3)}–{f(max(_pd) / 1e3)} kPa as donned. "
                 + ((f"Levers that would meet it at 60 mm: {'; '.join(_gl)} (§6). " if _gl else
                     "None of the levers studied (pad friction, preload, root bearing area, liner, arms, eye position) meets it at 60 mm") 
                    + (f"; the 60 mm side would have to weigh ≤ {f(_ml['mass'] * 1e3)} g" if _ml.get("mass") and _ml.get("k", 1) < 1 else "")
                    + (". This is the limit of an ear-mounted cradle at this mass. " if not _gl else ". ") if max(_pu) > _ps else "")
                 + "Wear trials must measure it first (§22).")
    r2 = [100 * F[D]["support"]["2 g dynamic"]["slip_fraction"] for D in SIZES]
    rb = {}
    for D in SIZES:
        for k, v in (F[D]["support"]["2 g dynamic"].get("released_by") or {}).items():
            rb[k] = rb.get(k, 0) + v
    tot_rb = sum(rb.values())
    top_rb = ", ".join(f"{k} {f(100 * v / tot_rb)} %" for k, v in sorted(rb.items(), key=lambda kv: -kv[1])[:3]) if tot_rb else ""
    zero2 = [D for D in MM if MM[D].get(DYN0, {}).get("holds_at_nominal") is False and MM[D].get(DYN0, {}).get("max_driver_g") is None]
    if max(r2) > 0:
        H.append(f"**Ear-mounted retention has a hard physical limit above 1 g** (§8, §10): under the 2 g set {f(min(r2))}–{f(max(r2))} % "
                 "of the combinations release" + (f"; the head-motion cases with the most releases are {top_rb} of all 2 g releases" if top_rb else "")
                 + ". The strict 'no 2 g combination may slip' condition " + (f"fails even with a massless driver ({', '.join(zero2)} mm). "
                 if zero2 else "is evaluated in §10. ") + "The released fractions are reported, not hidden. After a release the cradle "
                 "still surrounds the pinna and hangs on the link; that catch is not modelled (§22), so no retention credit is taken for it.")
    else:
        H.append("**No combination of the 2 g set releases** at any size (§8).")
    hmin = min(min_sf(F[D]["handling"]["sf"])[0] for D in SIZES); emin = min(min_sf(F[D]["arm_sf"]["5 g accidental"])[0] for D in SIZES)
    if hmin <= emin:
        H.append(f"**Structure:** the governing structural load is the {FH} N handling load at one pad (lowest SF {f(hmin)}, §12), which sized the "
                 f"arm bar; in the 5 g case the cradle releases first and the onset envelope bounds the arm loads (lowest SF {f(emin)}).")
    else:
        H.append(f"**Structure:** the governing structural load is the 5 g onset envelope (lowest SF {f(emin)}, §12); the {FH} N handling "
                 f"load at one pad gives SF {f(hmin)}.")
if JT and CB.get("anchor"):
    w1b = next((v for k, v in (WT or {}).items() if k.startswith("W1b") and v.get("anchor")), None)
    sf1b = min(v_.get("SF_initial", math.inf) for v_ in w1b["anchor"].values()) if w1b else None
    H.append(f"**Joints:** serrations carry the radial load, wave washers keep the clamp after the PETG creeps, and the cable anchor keeps "
             f"{FINAL.get('anchor_screw') or FINAL['arm_screw']} inserts (SF {f(min(v['SF_initial'] for v in CB['anchor'].values()))} at the highest "
             "cable load, §13, §14)" + (f"; M2.5 inserts would reach SF {f(sf1b)} there (§5, W1b)" if sf1b is not None else "") + ".")
if MM:
    gu = lambda t: t if t.startswith("fails") or t == "–" else t + " g"
    H.append("**Driver mass range** (§10), normal use: " + ", ".join(f"{D} mm {gu(mrange(MM[D].get('normal')))}" for D in MM) +
             "; maximum design condition: " + ", ".join(f"{D} mm {gu(mrange(MM[D].get('maximum')))}" for D in MM) + ".")
if LIM:
    import re as _re
    top, fam_ = [], set()
    for r_ in sorted(LIM, key=lambda r_: -r_[4]):          # highest utilisation of each kind of check (sizes merged)
        k_ = _re.sub(r" \(\d+ mm\)", "", r_[0])
        if k_ not in fam_:
            fam_.add(k_); top.append(r_)
        if len(top) == 4:
            break
    H.append("**Limiting components** (§19): retention friction under 2 g and above (released fractions, not a utilisation); then, "
             "by utilisation (demand / allowed): " + "; ".join(f"{r_[0]} — {r_[1]}: {f(r_[4])}" + (f" ({r_[3]})" if r_[4] > 1 else "")
                                                             for r_ in top) + ".")
text = "\n".join(md).replace("@@HEADLINES@@\n", "\n".join(f"{i + 1}. {h}" for i, h in enumerate(H)) + "\n")
os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, "w").write(text)
print("report written", OUT, len(text), "chars")

# ------------------------------------------------------------------------------------------------ README (same rule: numbers from results/)
R_OUT = os.environ.get("UMEH2_README", os.path.join(ROOT, "README.md"))
rd = []
r_ = rd.append
r_("# UMEH-2 — ear-mounted headphone cradle for 40–60 mm drivers\n")
r_("Second design iteration of the Universal Modular Ear-mounted Headphone: one common cradle (ring, four arms, pads, arched "
   "saddle, occipital spring link) that sits around the ear, and a driver module per size (40, 45, 50, 55 and 60 mm only) "
   "that twist-locks into it. Everything in this package is generated from the calculations: the CAD reads the parameter "
   "files the calculation writes, and the masses and centres of mass used by the load cases are integrated over the meshes "
   "that CAD exports.\n")
r_("**Read first:** `report/ENGINEERING_REPORT.md` (derivations, every load case, safety factors, limitations). No FEA, "
   "BEM or physical test was run; the report says where each is needed. Driver data, tissue properties and friction "
   "coefficients are assumptions or literature ranges and are tagged as such; measure your drivers and re-run.\n")
if F:
    rows = []
    for D in SIZES:
        r = F[D]; c = r["criteria"]; mm = MM.get(D, {})
        _sk = ((SK or {}).get("sizes", {}).get(D) or {}).get("A") or {}
        rows.append([f"{D} mm", r["mass"] * 1e3, pf(all(v for k, v in c.items() if not k.startswith("2 g"))),
                     (_sk["root_p"] / 1e3 if _sk.get("ok") else "–"),
                     100 * r["support"]["2 g dynamic"]["slip_fraction"], min_sf(r["handling"]["sf"])[0],
                     mmax(mm.get("normal")), mmax(mm.get("maximum"))])
    r_("## Key results (Final design)\n")
    r_(table(["driver", "mass per side g", "normal use (static + 1 g + link)", f"auricle-root pressure in use kPa (target ≤ {PSUS})",
              "2 g: % combinations released", f"{FH} N handling min SF",
              "max driver g, normal use (1 g grid)", "max driver g, max design"], rows))
    r_(f"Normal use means: all pads loaded at rest, skin and auricle-root pressure ≤ {PSUS} kPa as donned (clamp first; in use: see below), static friction "
       f"within the design coefficient, and no gross slip, loss of the tripod or tilt > {TILT_N}° anywhere in the 1 g grid of head "
       "orientations (up to the edge of the tilt cone), head rotations and cable pulls, nor in a finer dense check and its local "
       "refinement (report §8), and the link wire within its criteria on that module (report §11). "
       + ("Above 1 g the cradle, held by friction, releases in part of the combinations (" +
          ", ".join(f"{D} mm: {f(100 * F[D]['support'][c_]['slip_fraction'])} %" for D in SIZES for c_ in ("2 g dynamic",)) +
          " of the 2 g set); the report gives the fractions per case and why (§8, §10).\n"
          if any(F[D]["support"]["2 g dynamic"]["slip_fraction"] > 0 for D in SIZES) else
          "No combination of the 2 g set releases at any size; the 3 g and 5 g fractions are in the report (§8, §10).\n"))
    _pu = [((SK or {}).get("sizes", {}).get(D) or {}).get("A", {}).get("root_p") for D in SIZES]
    _pu = [x for x in _pu if x]
    if _pu and max(_pu) > mt.TISSUE["p_sustained"].v:
        r_(f"**Not met: the auricle-root pressure in use.** Normal use is judged as donned. Once the head moves, the pads micro-slip "
           f"and the saddle ends up carrying the side's weight on the auricle root at {f(min(_pu) / 1e3)}–{f(max(_pu) / 1e3)} kPa, "
           f"above the {PSUS} kPa sustained comfort target"
           + (" at every size" if len(_pu) == len(SIZES) and min(_pu) > mt.TISSUE["p_sustained"].v else "")
           + (". None of the design levers studied meets it (report §6)" if not any(x.get("ok") and x["root_p"] <= mt.TISSUE["p_sustained"].v
                                                                           and x["pad_p_max"] <= mt.TISSUE["p_sustained"].v for x in SK.get("levers") or [])
              else ". The levers that would meet it are in report §6") + ". Expect pressure "
           "at the top of the ear in long sessions, and measure it first (report §22).\n")
# assembly/use statements, each from the results it cites
don = ""
if F:
    ratios = []
    for D in SIZES:
        sa, sb = F[D]["support"]["static"], F[D]["support"].get("static_B", {})
        if sa.get("ok") and sb.get("ok"):
            pa = max(x["p_mean"] for x in sa["contacts"] if x["name"].startswith("S root"))
            pb = max(x["p_mean"] for x in sb["contacts"] if x["name"].startswith("S root"))
            ratios.append(pb / pa)
    if ratios:
        don = (f" Hanging it on the ear first and then clamping puts {f(min(ratios))}–{f(max(ratios))} × the auricle-root pressure "
               "on the ear (report §6).")
cab = ""
if CB.get("tug_limits"):
    hz_ = [v for D in CB["tug_limits"] for k, v in CB["tug_limits"][D]["named"].items() if "below" in k]
    cab = (f" Near-horizontal tugs of {f(min(hz_))}–{f(max(hz_))} N release the cradle"
           + (" before the plug gives" if max(hz_) < CB["Final"]["fuse"] else "") + " (report §14).")
fac = ""
nf_ = [x for x in (SW or {}).get("friction", []) if str(x["key"]).startswith("no facing") and x.get("static_mu_demand")]
if nf_:
    xw_ = max(nf_, key=lambda x: x["static_mu_demand"])
    if xw_["static_mu_demand"] > 1:
        fac = (f"; without it the {padn(xw_.get('static_mu_pad'))} pad needs {f(xw_['static_mu_demand'])} × the design "
               "friction of TPU at rest (report §9)")
lin = ""
if RL:
    nol_ = [r_x for r_x in RL["rows"] if r_x["variant"].startswith("no liner (Final")]
    if nol_:
        over_ = [D for D in ("55", "60") if nol_[0][D].get("ok") and nol_[0][D]["root_p"] > mt.TISSUE["p_sustained"].v]
        if over_:
            lin = (f"; without it the auricle root carries " + " and ".join(f"{f(nol_[0][D]['root_p'] / 1e3)} kPa at {D} mm" for D in over_)
                   + f" at rest, over the {PSUS} kPa target (report §6)")
r_(f"""## Assembly and use (these are part of the design)

* **Donning:** hold the cradle in place around the ear, clamp the link, then let go.{don}
* **Cable:** route it down the neck.{cab} Plug in and unplug with the headphone off the head.
* **Arm screws:** torque driver at the value in `BOM.csv`, with a wave spring washer under every head; the serrations carry
  the load, the washer keeps the clamp after the PETG creeps (report §13).
* **Pad facings:** cast the silicone facing on the temporal and mastoid pads (reference geometry in
  `stl/common/cast_reference/`){fac}.
* **Saddle liner:** cast the soft ({mt.SILICONE_GEL_GRADE}) silicone liner into the saddle cap's recessed bearing face{lin}.
* **Print orientation and settings:** report §20 and the `spec` column of `BOM.csv`. The STLs are exported in print
  orientation.

""")
def _env_txt():
    import platform, subprocess
    import scipy, matplotlib
    try:
        osc = subprocess.run(["openscad", "--version"], capture_output=True, text=True, timeout=30)
        osc = (osc.stdout or osc.stderr).strip().splitlines()[0]
    except Exception:
        osc = "OpenSCAD (version not read)"
    return (f"Python {platform.python_version()}, numpy {np.__version__}, scipy {scipy.__version__}, "
            f"matplotlib {matplotlib.__version__}, {osc}")


ENV_TXT = _env_txt()
r_("""## Contents

* `report/ENGINEERING_REPORT.md`, `report/fig/` — the engineering report and its figures.
* `cad/umeh2.scad` — parametric OpenSCAD model; `cad/generated_params.scad` (50 mm default) and `cad/params_<D>.scad` are
  written by the calculation.
* `stl/common/` — cradle parts (the same for every driver size); `stl/module_<D>mm/` — module parts per size (cups are
  handed because the link eye sits at a module-specific position).
* `calc/` — the models (`calc/umeh2/*.py`) and the scripts that produce every result.
* `results/*.json` — every computed number the report quotes.
* `BOM.csv`, `docs/bom_table.md` — bill of materials for one pair, masses from the CAD.

## Re-running

Requirements: Python 3 with numpy, scipy and matplotlib, and OpenSCAD on the PATH. Run for this delivery with
""" + ENV_TXT + """.

```
cd calc
python3 legs_liner.py    # arm-leg and saddle-liner thickness, chosen together (results/legs_liner.json)
python3 tune_eye.py      # per-module link-eye position and the link preload (writes calc/final_layout.json)
python3 run_all.py       # link, designs B/A/Final, joints, cable, weight, dynamics, tolerances, acoustics, max mass
python3 shakedown.py     # the sustained state in use: head-motion shakedown of the contact forces (results/shakedown.json)
python3 sweeps.py        # parameter sweeps
python3 figures.py
python3 build_stl.py     # STLs + cad/params_<D>.scad
python3 bom.py
python3 make_report.py   # report/ENGINEERING_REPORT.md and this README
```

The records of iteration changes 19–21 come from earlier states of the design, kept as inputs:
`calc/final_layout_before_grid.json` (run_all section 3d → results/grid_1g_before_grid.json), and
`calc/final_layout_grid45.json` (`python3 check_stall.py` → results/solver_stall_check.json;
`python3 dense_check_grid45.py` → results/dense_1g_grid45.json). They are not needed to re-run the design.

`legs_liner.py`, `tune_eye.py`, `run_all.py`, `shakedown.py` and `sweeps.py` use four processes and are the long steps (the contact model
solves every load combination of every candidate). Change an input (driver
data in `calc/umeh2/design.py`, materials in `calc/umeh2/materials.py`, design decisions in `calc/umeh2/configs.py`) and
re-run the chain; nothing in the report is typed by hand.
""")
open(R_OUT, "w").write("\n".join(rd))
print("README written", R_OUT)
