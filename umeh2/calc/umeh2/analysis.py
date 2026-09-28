"""
Glue: evaluates one design at one driver size end-to-end
(CAD -> mass properties -> support -> structure -> joints -> dynamics),
and the max-driver-mass searches. Used by run_all.py.
"""
import copy, inspect, math, os, json, hashlib, pickle
import numpy as np
from . import design as dz, massprops as mpz, support as sp, structure as st, dynamics as dy, layout as lo
from . import linkspring as ls, cable as cb
from .materials import PETG, TISSUE, FRICTION, G, SCREW, INSERT_PULLOUT, GAMMA_INSERT, GAMMA_M_PRINT, CABLE

CACHE = os.path.join(os.path.dirname(dz.CAD), "calc", "_cache")
ARMS_OF = {"B": ("saddle", "temporal", "mastoid"), "F": ("saddle", "temporal", "mastoid", "post")}


LINK_REF_D = 50      # the common occipital link is formed (free gap) on the 50 mm module [design decision]


def link_preload_at(des, D):
    """The occipital link is ONE part for every module: its free gap is formed so that P = link_preload_ref
    on the reference module (LINK_REF_D) at the nominal head. The eye sits on the cup end, so a deeper or
    shallower module moves the eye laterally by dz and changes the preload by k_side*dz [C]."""
    P_ref = des.get("link_preload_ref", des["link_preload"])
    if des.get("link_mode") != "cup" or D == LINK_REF_D:
        return P_ref
    ref = dict(des, link_preload=P_ref)
    ref.update((des.get("per_size") or {}).get(str(LINK_REF_D), {}))
    d_ref = dz.derived(ref, LINK_REF_D)
    _, L = sp.make_link(d_ref, ref)
    dzm = (dz.derived(des, D)["z_cuptop"] - d_ref["z_cuptop"]) * 1e-3
    return P_ref + L["k_side"] * dzm


def prepared(des, D):
    """Design dict for one driver size: per-module values (link eye on the cup) from des['per_size'],
    pad scale, and the preload that the common link gives on this module."""
    des = dict(des)
    des.update((des.get("per_size") or {}).get(str(D), {}))
    if "pad_scale" in des:
        des = lo.apply_pad_scale(des)
    des.setdefault("link_preload_ref", des["link_preload"])
    des["link_preload"] = link_preload_at(des, D)
    d = dz.derived(des, D)
    d["mastoid_r"] = des["mastoid_r"]
    return des, d


# ------------------------------------------------------------------ mass properties (cached on the CAD inputs)
def mass_properties(des, D, tag):
    """CAD mass properties of one side: the printed and cast parts integrated over their OpenSCAD meshes
    (massprops.assembly_props, cached) plus the hardware point masses (massprops.hardware, recomputed on every call:
    cheap, and it depends on design values that are not CAD parameters, e.g. the link wire and preload)."""
    des, d = prepared(des, D)
    dz.write_scad(d)
    flags = dict(has_post=bool(d.get("has_post")), mat_override={"gasket_umi": "FOAM"} if des.get("umi_mode") == "foam" else None,
                 has_face=des.get("pad_face_t", 0) > 0,
                 has_liner=bool(des.get("saddle_arch")) and des.get("saddle_liner_t", 0) > 0)
    # cache key of the mesh part: the CAD parameters and model, the mass model without hardware(), the densities,
    # the part flags and the driver mass
    h = hashlib.sha1(open(os.path.join(dz.CAD, "generated_params.scad"), "rb").read())
    h.update(open(os.path.join(dz.CAD, "umeh2.scad"), "rb").read())
    h.update(open(mpz.__file__).read().replace(inspect.getsource(mpz.hardware), "").encode())
    h.update(json.dumps([flags, dz.DRIVERS[D]["mass"],
                         [m["rho"].v for m in (mpz.PETG, mpz.TPU, mpz.FOAM, mpz.SILICONE, mpz.SILICONE_GEL)]],
                        sort_keys=True, default=str).encode())
    key = h.hexdigest()[:16]
    os.makedirs(CACHE, exist_ok=True)
    fn = os.path.join(CACHE, f"mpcad_{D}_{key}.pkl")
    if os.path.exists(fn):
        cad_rows = pickle.load(open(fn, "rb"))
    else:
        cad_rows = mpz.assembly_props(f"{tag}{D}", dz.DRIVERS[D]["mass"], **flags)
        tmp = f"{fn}.{os.getpid()}.tmp"
        pickle.dump(cad_rows, open(tmp, "wb"))
        os.replace(tmp, fn)
    rows = [dict(r) for r in cad_rows] + mpz.hardware(d, des)
    M, c, I = mpz.combine(rows)
    return dict(rows=rows, M=M, com=c, I=I)


def with_driver_mass(mp, D, m_driver_g, drv_row):
    """Replace the driver's mass (keeping its CAD centroid and scaling its inertia) -> new (M, com, I)."""
    rows = [dict(r) for r in mp["rows"]]
    for r in rows:
        if r["part"] == "driver":
            s = m_driver_g * 1e-3 / r["m"]
            r["m"] *= s; r["I"] = r["I"] * s
    return mpz.combine(rows)


# ------------------------------------------------------------------ support
def support_model(des, D, mu_level=1, gamma_mu=lo.GAMMA_MU, **kw):
    des, d = prepared(des, D)
    C = sp.contact_set(d, des, mu_level=mu_level, mu_scale=1 / gamma_mu, **kw)
    link, L = sp.make_link(d, des)
    return des, d, C, link, L


N_HANDLING_DIRS = 302    # directions of the handling load (Fibonacci sphere) in the Final evaluation
JOINT_KEYS = ("SF_engage", "SF_pullout", "SF_slot", "SF_tooth")


def track_joint(jt, arm, j, case):
    """Keep, per arm, the minimum of every joint safety factor and the full joint result at the minimum
    engagement factor (jt: dict arm -> record, filled in place)."""
    cur = jt.get(arm)
    if cur is None:
        jt[arm] = cur = {k: np.inf for k in JOINT_KEYS}
    for k in JOINT_KEYS:
        if j[k] < cur[k]:
            cur[k] = j[k]
            if k == "SF_engage":
                cur["at_min_engage"] = dict(j, case=case)


def support_eval(des, D, mpt, n_dir=40, n_grav=5, n_cable=3, struct=True, cats=None, bounds=True, n_acc=None,
                 max_released=None):
    """Static state (donning sequences A and B, static friction demand) and every load case of the categories
    `cats`. n_acc: number of 5 g directions (default max(3 n_dir, 100)). max_released: stop a category as soon
    as more cases than this release (used by the mass bisection; the category is then marked 'aborted')."""
    des, d, C, link, L = support_model(des, D)
    model = sp.Model(C, link)
    out = dict(link=L)
    W_st = sp.static_wrench(mpt, d, des)
    model.set_base(W_st)
    r0 = model.solve(W_st, fric=True)
    out["static"] = r0
    out["static_mu_demand"] = sp.static_friction_demand(C, link, W_st)
    # donning sequence B (hang on the ear root first): upper bound of the root load / pressure
    mB = sp.Model(C, link)
    out["static_B"] = mB.solve(W_st) if mB.set_base(W_st, seq="B") else dict(ok=False, reason=mB.base_why)
    cats = cats or list(sp.CATEGORIES)
    arms = [a for a in ("saddle", "temporal", "mastoid", "post") if a != "post" or des.get("post_a") is not None]
    for cat in cats:
        smax = {a: {} for a in arms}
        pk = {c["name"]: 0.0 for c in C}
        Fmax = {c["name"]: 0.0 for c in C}
        rows = []
        worst = {k: (-np.inf, None) for k in ("util", "p_peak", "rot_xy", "disp")}
        n = rel = uns = padslip = 0
        lams = []
        rel_by = {}          # released cases per head-motion case (axis + phase): what drives the releases
        rel_g = {"gravity upright": 0, "gravity tilted": 0}
        jt = {}
        envelope = struct and cat == "5 g accidental"
        nd = n_dir if sp.CATEGORIES[cat]["cone"] is not None else (n_acc or max(n_dir * 3, 100))
        aborted = False
        for tag, W in sp.load_cases(mpt, d, des, cat, nd, n_cable, n_grav):
            n += 1
            r = model.solve(W, fric=True)
            if not r["ok"]:
                rel += 1
                kk = f"{tag['axis']} {tag['phase']}" if tag["axis"] else "no head rotation"
                rel_by[kk] = rel_by.get(kk, 0) + 1
                if sp.CATEGORIES[cat]["cone"] is not None:        # 5 g: a resultant in any direction, no gravity split
                    rel_g["gravity upright" if np.allclose(tag["g_dir"], (0.0, -1.0, 0.0)) else "gravity tilted"] += 1
                if max_released is not None and rel > max_released:
                    aborted = True
                    break
                if not envelope:
                    continue
                # accidental: the cradle lets go; arm loads = contact forces at the onset of gross slip
                lam, r = sp.onset_of_slip(model, W_st, W)
                lams.append(lam)
                if not r["ok"]:
                    continue
            else:
                padslip += any(x["slipping"] for x in r["contacts"] if x["name"] in sp.SKIN_PADS)
            m = sp.metrics(r, C)
            if not m["seated"]:
                uns += 1
            for k in worst:
                if m[k] > worst[k][0]:
                    worst[k] = (m[k], dict(tag=tag, contacts=[(x["name"], x["Fn"], x["Ft"]) for x in r["contacts"]]))
            for x in r["contacts"]:
                pk[x["name"]] = max(pk[x["name"]], x["p_peak"]); Fmax[x["name"]] = max(Fmax[x["name"]], math.hypot(x["Fn"], x["Ft"]))
            if struct:
                for a in arms:
                    loads = st.arm_loads_from_contacts(r["contacts"], C, a)
                    if not loads:
                        continue
                    res = st.check_arm_sections(d, des, a, loads)
                    for sec, s in res.items():
                        cur = smax[a].get(sec)
                        if cur is None or s["vm"] > cur["vm"]:
                            smax[a][sec] = dict(s, case=tag)
                        cur = smax[a][sec]
                        cur["tau_il_max"] = max(cur.get("tau_il_max", 0.0), s["tau_il"])
                    if des.get("serrated"):
                        track_joint(jt, a, arm_joint(des, d, a, res[JOINT_SEC]), tag)
        out[cat] = dict(n=n, released=rel, unseated=uns, slip_fraction=rel / max(n, 1), worst=worst, p_peak=pk,
                        F_contact_max=Fmax, arm_stress=smax, pad_slip_fraction=padslip / max(n - rel, 1), joint=jt,
                        aborted=aborted, released_by=rel_by, released_by_gravity=rel_g)
        if aborted:
            out[cat]["slip_fraction"] = float("inf")
        if envelope:
            out[cat]["onset_lambda"] = dict(n=len(lams), min=float(min(lams)) if lams else None,
                                            p10=float(np.percentile(lams, 10)) if lams else None,
                                            median=float(np.median(lams)) if lams else None)
            if bounds:
                # information only: the WHOLE accidental load at one contact point (cannot occur while the
                # cradle releases first; shows how far the envelope is from a local overload)
                F_b = mpt[0] * 5.0 * G + F_SNAG
                out[cat]["F_bound"] = F_b
                out[cat]["arm_bound"] = arm_bound(des, d, C, F_b, arms)
    if struct and bounds:
        jh = {}
        out["handling"] = dict(F=F_HANDLING, n_dir=N_HANDLING_DIRS,
                               arm_bound=arm_bound(des, d, C, F_HANDLING, arms, n_dir=N_HANDLING_DIRS, joints=jh),
                               joint=jh)
    return out, (des, d, C, link, L)


def arm_joint(des, d, arm, v):
    """Serrated arm-to-tab joint under the section forces v at the clamp edge (structure.check_arm_sections,
    section 'bar at clamp edge (slot end)'); every force/moment component, see structure.serrated_joint."""
    j = st.serrated_joint(des["arm_screw"], des["arm_torque"], 2, F_radial=v["N"], F_tang=v["Vt"], M_tilt=v["Mt"],
                          pitch_m=d["tab_ins_pitch"] * 1e-3,
                          w_m=(des["saddle_arm_w"] if arm == "saddle" else des["arm_w"]) * 1e-3,
                          washer=des.get("arm_washer"), F_pull=v["Vh"], T_twist=v["T"], M_inplane=v["Mh"],
                          t_bear_m=des["bar_t"] * 1e-3)
    j["forces"] = {k: float(v[k]) for k in ("N", "Vt", "Vh", "T", "Mt", "Mh")}
    return j


JOINT_SEC = "bar at clamp edge (slot end)"
ARM_CONTACTS = {"temporal": ("T temporal",), "mastoid": ("M mastoid",), "post": ("P post-sup",),
                "saddle": ("S root", "S root F", "S root B", "S scalp", "S helix")}
F_SNAG = CABLE["snag"].v   # N, cable snag in the accidental case [A] (materials.CABLE)
F_HANDLING = 10.0      # N, [A] handling / snag load on ONE pad in any direction (removal by one pad, catching a
                       # collar or hair): ~6x the side weight; range 5-20 N, SF scales as 10/F


def arm_bound(des, d, C, F_mag, arms, n_dir=62, joints=None):
    """Conservative structural bound for the accidental case: the WHOLE accidental load F_mag (5 g inertia of
    the complete side + cable snag) acts at ONE contact point of an arm, in every direction of a Fibonacci
    sphere. Used because in most 5 g combinations the cradle does not stay in equilibrium on the head
    (gross slip), so the held-case contact forces do not bound the arm loads. Returns the worst value per
    section (von Mises, interlayer shear) and the section forces of that worst case (joint loads)."""
    dirs = sp.fib_sphere(n_dir)
    out = {}
    for arm in arms:
        worst = {}
        for c in C:
            if c["name"] not in ARM_CONTACTS[arm]:
                continue
            for e in dirs:
                res = st.check_arm_sections(d, des, arm, [(c["r"], F_mag * e)])
                for sec, v in res.items():
                    cur = worst.get(sec)
                    til = max(cur["tau_il_max"], v["tau_il"]) if cur else v["tau_il"]
                    if cur is None or v["vm"] > cur["vm"]:
                        worst[sec] = dict(v, contact=c["name"], dir=e)
                    worst[sec]["tau_il_max"] = til
                if joints is not None and des.get("serrated"):
                    track_joint(joints, arm, arm_joint(des, d, arm, res[JOINT_SEC]), dict(contact=c["name"], dir=e))
        out[arm] = worst
    return out


def criteria(ev):
    """Pass/fail per condition (definitions in the report, section 'Acceptance criteria')."""
    s = ev["static"]
    skin = [x for x in s["contacts"] if not x["name"].startswith("S root")] if s["ok"] else []
    c = {}
    c["static seated (all pads loaded)"] = s["ok"] and min(x["Fn"] for x in s["contacts"]) >= sp.F_MIN
    c[f"static skin pressure <= {TISSUE['p_sustained'].v / 1e3:g} kPa"] = s["ok"] and max(x["p_mean"] for x in skin) <= TISSUE["p_sustained"].v
    root = [x for x in s["contacts"] if x["name"].startswith("S root")] if s["ok"] else []
    c[f"static auricle-root pressure <= {TISSUE['p_sustained'].v / 1e3:g} kPa (donning A)"] = s["ok"] and all(x["p_mean"] <= TISSUE["p_sustained"].v for x in root)
    dem = ev.get("static_mu_demand")
    c["static friction: pads hold with design mu"] = bool(dem) and max(dem.values()) <= 1.0
    n1 = ev.get("1 g normal")
    if n1:
        c["1 g: no gross slip"] = n1["released"] == 0
        c["1 g: stays seated"] = n1["unseated"] == 0
        c[f"1 g: tilt <= {lo.ROT_NORMAL:g} deg"] = n1["worst"]["rot_xy"][0] <= lo.ROT_NORMAL
    n2 = ev.get("2 g dynamic")
    if n2:
        c["2 g: no gross slip"] = n2["released"] == 0
    return c


# ------------------------------------------------------------------ dense 1 g check
K_CRIT = 8        # most critical cases kept per module (lowest seating margin, largest tilt) as seeds of refine_1g


def _case_1g(model, C, tag, W, out):
    """Solve one 1 g case and add it to the tallies of out (dense_1g_chunk / refine_1g_chunk)."""
    tagc = dict(g_dir=[round(float(v), 6) for v in tag["g_dir"]], axis=tag["axis"], sign=tag["sign"], phase=tag["phase"],
                cable_dir=[round(float(v), 6) for v in tag["cable_dir"]])
    out["n"] += 1
    r = model.solve(W, fric=True)
    if not r["ok"]:
        out["released"] += 1
        out["released_numerical"] += bool(r.get("numerical"))
        out["fails"].append(dict(tagc, why="released", reason=r.get("reason"), numerical=bool(r.get("numerical"))))
        return
    m = sp.metrics(r, C)
    fs = sorted((x["Fn"] for x in r["contacts"] if x["name"][0] in "TMP" or x["name"] == "S scalp"), reverse=True)
    seat = (fs[2] if len(fs) > 2 else 0.0) - sp.F_MIN
    row = dict(tagc, seat=seat, tilt=m["rot_xy"])
    if m["rot_xy"] > out["worst_tilt"][0]:
        out["worst_tilt"] = (m["rot_xy"], tagc)
    if seat < out["min_seat"][0]:
        out["min_seat"] = (seat, tagc)
    out["crit_seat"] = sorted(out["crit_seat"] + [row], key=lambda x: x["seat"])[:K_CRIT]
    out["crit_tilt"] = sorted(out["crit_tilt"] + [row], key=lambda x: -x["tilt"])[:K_CRIT]
    bad = []
    if not m["seated"]:
        out["unseated"] += 1; bad.append("tripod lost")
    if m["rot_xy"] > lo.ROT_NORMAL:
        out["tilt_over"] += 1; bad.append(f"tilt {m['rot_xy']:.2f} deg")
    if bad:
        out["fails"].append(dict(tagc, why=", ".join(bad), tilt=m["rot_xy"], seat=seat))


def _tally():
    return dict(n=0, released=0, released_numerical=0, unseated=0, tilt_over=0, worst_tilt=(0.0, None),
                min_seat=(np.inf, None), crit_seat=[], crit_tilt=[], fails=[])


def _model_1g(des, D, mpt):
    des_, d, C, link, _ = support_model(des, D)
    model = sp.Model(C, link)
    model.set_base(sp.static_wrench(mpt, d, des_))
    return des_, d, C, model


def dense_1g_chunk(args):
    """One chunk of the dense check of the 1 g category (support.DENSE_1G, a finer nested version of the worst-case
    grid support.GRID_1G): args = (des, D, mpt, i0, i1[, grid]) -> gravity directions i0..i1-1 of the dense grid (or of
    `grid`) x every
    head-motion case x every cable direction, each solved from the donned state (sequence A) with friction.
    Returns the counts, the worst tilt and the smallest seating margin (third-largest skin contact force - F_min)
    with their cases, the K_CRIT most critical cases of each, and every failing case (released, tripod lost, or
    tilt over the limit)."""
    import itertools
    des, D, mpt, i0, i1 = args[:5]
    g_ = args[5] if len(args) > 5 and args[5] is not None else sp.DENSE_1G
    des_, d, C, model = _model_1g(des, D, mpt)
    per_g = len(sp.ring_grid(g_["cable_polar"], g_["cable_az_step"])) * len(sp.ANG_CASES)
    out = _tally()
    for tag, W in itertools.islice(sp.load_cases(mpt, d, des_, "1 g normal", 1, 0, 0, grid=g_), i0 * per_g, i1 * per_g):
        _case_1g(model, C, tag, W, out)
    return out


def fails_summary(fails):
    """Summary of a list of failing 1 g cases (dense_1g_chunk / refine_1g_chunk), over ALL of them (the saved lists are
    truncated): count, range of head tilt from upright, how many hang the side outward (gravity with a +z = outward
    component in the head frame: the head tilted towards this side, this ear down), how many pull the cable outward,
    both, and the count per head-tilt ring and per head-motion case."""
    if not fails:
        return dict(n=0)
    tl = [_polar_az(x["g_dir"])[0] for x in fails]
    ring, hm = {}, {}
    for t, x in zip(tl, fails):
        k = f"{t:.2f}"
        ring[k] = ring.get(k, 0) + 1
        h = f"{x['axis']} {x['sign']:+g} {x['phase']}" if x.get("axis") else "no head rotation"
        hm[h] = hm.get(h, 0) + 1
    return dict(n=len(fails), tilt_min=min(tl), tilt_max=max(tl),
                side_out=sum(1 for x in fails if x["g_dir"][2] > 1e-9),
                cable_out=sum(1 for x in fails if x["cable_dir"][2] > 1e-9),
                both_out=sum(1 for x in fails if x["g_dir"][2] > 1e-9 and x["cable_dir"][2] > 1e-9),
                released=sum(1 for x in fails if x["why"] == "released"),
                numerical=sum(1 for x in fails if x.get("numerical")), per_tilt=ring, per_head_motion=hm)


def dense_1g_jobs(des, D, mpt, chunk=None, grid=None):
    """Argument tuples of dense_1g_chunk covering the whole dense grid (or `grid`, e.g. support.GRID_1G) of one module
    (n_g // 26 directions per chunk: 33 chunks per module on DENSE_1G and on GRID_1G)."""
    g_ = grid or sp.DENSE_1G
    n_g = len(sp.ring_grid(g_["tilt"], g_["az_step"]))
    chunk = chunk or max(1, n_g // 26)
    return [(des, D, mpt, i, min(i + chunk, n_g), grid) for i in range(0, n_g, chunk)]


def dense_1g_merge(parts):
    """Merge the chunks of one module (dense_1g_chunk or refine_1g_chunk)."""
    out = _tally()
    for p in parts:
        for k in ("n", "released", "released_numerical", "unseated", "tilt_over"):
            out[k] += p[k]
        if p["worst_tilt"][0] > out["worst_tilt"][0]:
            out["worst_tilt"] = p["worst_tilt"]
        if p["min_seat"][0] < out["min_seat"][0]:
            out["min_seat"] = p["min_seat"]
        out["crit_seat"] = sorted(out["crit_seat"] + p["crit_seat"], key=lambda x: x["seat"])[:K_CRIT]
        out["crit_tilt"] = sorted(out["crit_tilt"] + p["crit_tilt"], key=lambda x: -x["tilt"])[:K_CRIT]
        out["fails"] += p["fails"]
    out["ok"] = out["released"] == 0 and out["unseated"] == 0 and out["tilt_over"] == 0
    return out


# Local refinement of the dense check. The dense grid is itself a finite sample, so around each of its most critical
# cases (up to K_CRIT failures, the K_CRIT lowest seating margins and the K_CRIT largest tilts) the cell of the dense
# grid is searched on a 4x finer local grid: head tilt +-1/2 dense ring spacing, gravity azimuth +-1/2 dense step, cable
# polar angle +-1/2 dense ring spacing, cable azimuth +-1/2 dense step, each in REFINE_N points (the seed's own
# head-motion case), clipped to the tilt cone and the cable cone. At a pole (head upright, cable straight down) the
# cell is the polar cap: the pole + rings at 1/4 and 1/2 of the ring spacing x POLE_AZ azimuths. Cells of neighbouring
# seeds overlap; every combination is solved and counted once. The change of the worst values from the dense grid to
# the refinement measures how well the dense grid resolves the worst case.
REFINE_N = 5
POLE_AZ = 12


def _polar_az(v):
    v = np.asarray(v, float)
    return math.degrees(math.acos(max(-1.0, min(1.0, -v[1])))), math.degrees(math.atan2(v[2], v[0]))


def _dir(t, p):
    t, p = math.radians(t), math.radians(p)
    return np.array([math.sin(t) * math.cos(p), -math.cos(t), math.sin(t) * math.sin(p)])


def refine_1g_seeds(dense):
    """Seeds of the local refinement from a merged dense check: failures first (released, then by seating margin; at
    most K_CRIT), then the critical cases; no duplicates."""
    fails = sorted(dense["fails"], key=lambda x: (x["why"] != "released", x.get("seat", -np.inf)))[:K_CRIT]
    seeds, seen = [], set()
    for x in fails + dense["crit_seat"] + dense["crit_tilt"]:
        k = (tuple(np.round(x["g_dir"], 4)), tuple(np.round(x["cable_dir"], 4)), x["axis"], x["sign"], x["phase"])
        if k not in seen:
            seen.add(k); seeds.append({kk: x[kk] for kk in ("g_dir", "cable_dir", "axis", "sign", "phase")})
    return seeds


def _cell(v, dt, dp, t_max):
    """Directions of the dense-grid cell around v (see above): +-dt polar, +-dp azimuth, or the polar cap at a pole."""
    t0, p0 = _polar_az(v)
    t0, p0 = round(t0, 4), round(p0, 4)            # the seeds carry rounded directions: snap back onto the grid values
    off = np.linspace(-1.0, 1.0, REFINE_N)
    if t0 < 1e-6:
        out = [_dir(0.0, 0.0)]
        for a in off[off > 0]:
            out += [_dir(min(a * dt, t_max), q) for q in np.arange(0.0, 360.0, 360.0 / POLE_AZ)]
        return out
    out, seen = [], set()
    for a in off:
        t = min(max(t0 + a * dt, 0.0), t_max)
        for b in off:
            key = (round(t, 4), round((p0 + b * dp) % 360.0, 4) if t > 1e-6 else 0.0)
            if key not in seen:
                seen.add(key); out.append(_dir(t, p0 + b * dp))
    return out


def refine_1g_cases(dense, grid=None):
    """(seeds, cases) of the local refinement of one module: cases = unique combinations
    [g_dir, cable_dir, axis, sign, w, seed indices] over the cells of all seeds."""
    g_ = grid or sp.DENSE_1G
    cone = sp.CATEGORIES["1 g normal"]["cone"]
    dt = 0.5 * float(np.min(np.diff((0.0,) + tuple(g_["tilt"]))))
    dp = 0.5 * g_["az_step"]
    dct = 0.5 * float(np.min(np.diff((0.0,) + tuple(g_["cable_polar"]))))
    dcp = 0.5 * g_["cable_az_step"]
    seeds = refine_1g_seeds(dense)
    cases = {}
    for i, sd in enumerate(seeds):
        w = 1.0 if sd["phase"] == "omega" else 0.0
        for g in _cell(sd["g_dir"], dt, dp, cone):
            for c in _cell(sd["cable_dir"], dct, dcp, sp.CABLE_CONE):
                key = (tuple(np.round(g, 6)), tuple(np.round(c, 6)), sd["axis"], float(sd["sign"]), w)
                cases.setdefault(key, [g, c, sd["axis"], sd["sign"], w, []])[5].append(i)
    return seeds, list(cases.values())


def refine_1g_chunk(args):
    """Local refinement: args = (des, D, mpt, cases) with cases from refine_1g_cases. Returns the tally of those cases
    and, per case, (seed indices, seating margin or None if released, tilt or None, failed)."""
    des, D, mpt, cases = args
    des_, d, C, model = _model_1g(des, D, mpt)
    out = _tally()
    out["per_case"] = []
    for g, c, ax, sg, w, idx in cases:
        tag, W = sp.case_wrench(mpt, d, des_, "1 g normal", g, np.zeros(3), ax, sg, w, c)
        n0 = len(out["fails"]); s0 = out["min_seat"][0]
        sub = _tally()
        _case_1g(model, C, tag, W, sub)
        for k in ("n", "released", "released_numerical", "unseated", "tilt_over"):
            out[k] += sub[k]
        if sub["worst_tilt"][0] > out["worst_tilt"][0]:
            out["worst_tilt"] = sub["worst_tilt"]
        if sub["min_seat"][0] < out["min_seat"][0]:
            out["min_seat"] = sub["min_seat"]
        out["crit_seat"] = sorted(out["crit_seat"] + sub["crit_seat"], key=lambda x: x["seat"])[:K_CRIT]
        out["crit_tilt"] = sorted(out["crit_tilt"] + sub["crit_tilt"], key=lambda x: -x["tilt"])[:K_CRIT]
        out["fails"] += sub["fails"]
        out["per_case"].append((idx, sub["min_seat"][0] if sub["crit_seat"] else None,
                                sub["worst_tilt"][0] if sub["crit_tilt"] else None, bool(sub["fails"])))
    return out


def refine_1g_jobs(des, D, mpt, dense, n_jobs=8):
    """(jobs, seeds): argument tuples of refine_1g_chunk for one module's dense check, and the seeds."""
    seeds, cases = refine_1g_cases(dense)
    if not cases:
        return [], seeds
    k = -(-len(cases) // n_jobs)
    return [(des, D, mpt, cases[i:i + k]) for i in range(0, len(cases), k)], seeds


def refine_1g_merge(parts, seeds):
    """Merge the refinement chunks of one module; per seed: its cell's combinations, smallest seating margin, largest
    tilt and failures."""
    out = dense_1g_merge(parts)
    ps = [dict(seed=sd, n=0, min_seat=np.inf, worst_tilt=0.0, n_fail=0) for sd in seeds]
    for p in parts:
        for idx, seat, tilt, failed in p["per_case"]:
            for i in idx:
                ps[i]["n"] += 1
                if seat is not None:
                    ps[i]["min_seat"] = min(ps[i]["min_seat"], seat)
                if tilt is not None:
                    ps[i]["worst_tilt"] = max(ps[i]["worst_tilt"], tilt)
                ps[i]["n_fail"] += int(failed)
    out["seeds"] = ps
    return out


# ------------------------------------------------------------------ max driver mass
def structural_ok(ev, cat, gamma=None):
    """Every arm section SF >= gamma_M (von Mises and interlayer shear, 40 C short-term allowables) and every
    arm joint keeps its serrations engaged (SF_engage >= 1 with the creep-relaxed preload), insert pull-out
    SF >= 1 (gamma_insert inside) and slot bearing SF >= 1 under the envelope of category `cat`."""
    gamma = gamma or GAMMA_M_PRINT.v
    S, Sil = st.strength("short", temp="40C")
    for a, secs in ev[cat]["arm_stress"].items():
        for sec, v in secs.items():
            if S / max(v["vm"], 1) < gamma or Sil / max(v["tau_il_max"], 1) < gamma:
                return False
    for a, j in ev[cat].get("joint", {}).items():
        if j["SF_engage"] < 1.0 or j["SF_pullout"] < 1.0 or j["SF_slot"] < 1.0:
            return False
    return True


def static_holds(des, D, mpt):
    """The side stays on at rest with the design friction (donning sequence A, static equilibrium found)."""
    des_, d_, C, link, _ = support_model(des, D)
    m = sp.Model(C, link)
    W = sp.static_wrench(mpt, d_, des_)
    return bool(m.set_base(W)) and bool(m.solve(W)["ok"])


def link_on_modules(des_w):
    """The occipital link design (linkspring.link_design) on every module at its own eye (path and P(D))."""
    out = {}
    for D_ in dz.SIZES:
        dd_, d_ = prepared(des_w, D_)
        out[D_] = sp.make_link(d_, dd_)[1]
    return out


def size_link_on_modules(des):
    """The link is ONE part on every module, and each module's eye sets its own path across the cup face and its own
    preload P(D). For each stock diameter the fewest apex turns that meet every criterion on EVERY module; chosen = the
    diameter with the largest smallest margin (linkspring.margin). Returns (candidates, chosen or None)."""
    from . import linkspring as ls
    cands = []
    for sd in ls.STOCK_D:
        for n in ls.N_COILS:
            Ls = link_on_modules(dict(des, wire_d=sd, link_coils=n))
            if all(L_["ok"] for L_ in Ls.values()):
                cands.append(dict(d_mm=sd, n_coil=n, margin=min(ls.margin(L_) for L_ in Ls.values()), modules=Ls))
                break
    return cands, (max(cands, key=lambda c: c["margin"]) if cands else None)


def n_cases(des, D, mpt, cat, n_dir, n_cable, n_grav):
    des_, d_ = prepared(des, D)
    return sum(1 for _ in sp.load_cases(mpt, d_, des_, cat, n_dir, n_cable, n_grav))


def max_driver_mass(des, D, mp, condition, lo_g=0.0, hi_g=150.0, tol=0.5, n_dir=24, allow=0.0, n_acc=26):
    """Driver-mass range over which one condition holds (the rest of the side keeps its CAD mass properties;
    the driver keeps its CAD centroid, inertia scaled with its mass).
    static:  the side stays on at rest with the design mu (static equilibrium, no gross slip)
    normal:  static seated (all pads >= F_min) + skin and auricle-root pressure <= {p_s:g} kPa as donned + static friction
             demand <= design mu AND the 1 g set: no gross slip, seated, tilt <= {tilt:g} deg
    dynamic: 'normal' AND the 2 g set with a released fraction <= allow (allow = 0: strict); the 2 g sweep
             stops as soon as the released count exceeds allow x n_cases
    maximum: 'static' AND, in the 5 g accidental set (n_acc directions), the structure survives the envelope
             loads (held cases + contact forces at the onset of gross slip for the cases that release):
             structural_ok(). Slip/release allowed.
    The condition is NOT monotonic in the mass: the link eye of each module is tuned for its nominal driver, so a
    lighter driver also moves the load resultant off the tuned line. The search is therefore anchored at the
    nominal driver mass m0 (design.DRIVERS): the condition is evaluated at m0 first; then bisection (to tol) on
    [m0, hi_g] for the largest passing mass and on [lo_g, m0] for the smallest (skipped when hi_g / lo_g pass).
    The passing masses are taken to form one interval around m0; this is checked at the interval quartiles
    ('interval_checked'). If m0 itself fails, the result says so, and the passing range below m0 (if lo_g
    passes) is found by bisection on [lo_g, m0]. 'maximum': the static limit is found first (cheap) and the
    structure is checked there; only if it fails there is the structural check bisected.
    Returns dict(nominal_g, holds_at_nominal, max_driver_g, min_driver_g, capped (max = hi_g), governs,
    interval_checked, n_eval)."""
    m0 = float(dz.DRIVERS[D]["mass"])
    n_eval = [0]
    memo = {}

    def ok(mg, cond=condition):
        key = (round(mg, 6), cond)
        if key in memo:
            return memo[key]
        n_eval[0] += 1
        mpt = with_driver_mass(mp, D, mg, None)
        if cond == "static":
            r = static_holds(des, D, mpt)
        elif cond == "maximum":
            r = static_holds(des, D, mpt)
            if r:
                ev, _ = support_eval(des, D, mpt, n_dir=n_dir, n_grav=3, n_cable=1, struct=True, cats=["5 g accidental"],
                                     bounds=False, n_acc=n_acc)
                r = structural_ok(ev, "5 g accidental")
        else:
            ev, _ = support_eval(des, D, mpt, n_dir=n_dir, n_grav=4, n_cable=2, struct=False, cats=["1 g normal"])
            r = all(criteria(ev).values())
            if r and cond == "dynamic":
                n_tot = n_cases(des, D, mpt, "2 g dynamic", n_dir, 2, 4)
                ev2, _ = support_eval(des, D, mpt, n_dir=n_dir, n_grav=4, n_cable=2, struct=False, cats=["2 g dynamic"],
                                      max_released=int(math.floor(allow * n_tot + 1e-9)))
                r = ev2["2 g dynamic"]["slip_fraction"] <= allow
        memo[key] = bool(r)
        return bool(r)

    def bisect(a, b, f):
        """f(a) passes, f(b) fails (a may lie above or below b) -> the passing end, within tol of the boundary."""
        while abs(b - a) > tol:
            m = 0.5 * (a + b)
            if f(m):
                a = m
            else:
                b = m
        return a

    out = dict(nominal_g=m0, governs=condition, hi_g=hi_g)
    out["holds_at_nominal"] = ok(m0)
    if not out["holds_at_nominal"]:
        if ok(lo_g):
            out.update(min_driver_g=lo_g, max_driver_g=bisect(lo_g, m0, ok), capped=False)
        else:
            out.update(min_driver_g=None, max_driver_g=None, capped=False)
        out.update(interval_checked=None, n_eval=n_eval[0])
        return out
    # upper end
    if condition == "maximum":
        f_st = lambda m: ok(m, "static")
        m_st = hi_g if f_st(hi_g) else bisect(m0, hi_g, f_st)
        if ok(m_st):
            out.update(max_driver_g=m_st, capped=m_st >= hi_g, governs="static hold (structure OK at the static limit)")
        else:
            out.update(max_driver_g=bisect(m0, m_st, ok), capped=False, governs="structure (5 g envelope)")
    elif ok(hi_g):
        out.update(max_driver_g=hi_g, capped=True)
    else:
        out.update(max_driver_g=bisect(m0, hi_g, ok), capped=False)
    # lower end
    out["min_driver_g"] = lo_g if ok(lo_g) else bisect(m0, lo_g, ok)
    lo_, hi_ = out["min_driver_g"], out["max_driver_g"]
    qs = [lo_ + (hi_ - lo_) * q for q in (0.25, 0.5, 0.75)]
    out["interval_checked"] = all(ok(q) for q in qs if abs(q - m0) > tol)
    out["n_eval"] = n_eval[0]
    return out


max_driver_mass.__doc__ = max_driver_mass.__doc__.format(p_s=TISSUE["p_sustained"].v / 1e3, tilt=lo.ROT_NORMAL)
