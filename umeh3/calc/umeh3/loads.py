"""
Load cases and worst-case sweeps for UMEH-3 (same load model as UMEH-2, umeh2.support: categories 1/2/3/5 g,
head tilt cones, dynamic acceleration in any direction, head angular acceleration / velocity about the three head
axes, cable pull within 80 deg of straight down; the 1 g category on the deterministic worst-case grid).
The cable acts at the 2-pin socket (CAD position).
"""
import json, os
import numpy as np
from umeh2 import support as sp
from umeh2.materials import G, CABLE
from . import RESULTS, mass, geom, contacts as ct


def mass_props(D, refresh=False):
    """(M, com, I, p_cable, rows) of one side with driver D; cached in results/mass_<D>.json."""
    path = os.path.join(RESULTS, f"mass_{geom.VARIANT}_{D}.json")
    if refresh or not os.path.exists(path):
        geom.write_scad(os.path.join(mass.CAD, "params3.scad"))
        rows = mass.assembly(D, tag=f"{geom.VARIANT}_D{D}")
        M, com, I = mass.combine(rows)
        p_c = next(r["c"] for r in rows if r["part"] == "socket")
        js = dict(M=M, com=com.tolist(), I=I.tolist(), p_cable=p_c.tolist(),
                  rows=[dict(part=r["part"], mat=r["mat"], m_g=r["m"] * 1e3, c_mm=(r["c"] * 1e3).tolist(),
                             f=r["f"]) for r in rows])
        os.makedirs(RESULTS, exist_ok=True)
        with open(path, "w") as fh:
            json.dump(js, fh, indent=1)
    js = json.load(open(path))
    return js["M"], np.array(js["com"]), np.array(js["I"]), np.array(js["p_cable"]), js["rows"]


def cable_wrench(p, F):
    return np.r_[F, np.cross(p, F)]


def static_wrench(mp):
    M, com, I, p_c = mp[:4]
    w_cable = CABLE["mass_per_m"].v * CABLE["hang_len"].v * G
    return sp.inertial_wrench(M, com, I, np.array([0, -G, 0])) + cable_wrench(p_c, np.array([0, -w_cable, 0]))


# Treadmill running (the user's use case, 2026-10-01). Peak head accelerations while running, on top of gravity
# [A, from running gait literature: vertical ~1-2.5 g at the head (heel-strike shock attenuated by the body), fore-aft
# ~0.3-1 g, medio-lateral ~0.2-0.5 g]. Downwards the head cannot accelerate faster than free fall in running (flight
# phase: -1 g, the module weightless), so the vertical values are {-a_down, 0, +a_up}; fore-aft and lateral {-a, 0, +a}:
# every combination (27 vectors incl. 0),
# head tilt within 15 deg of upright, head angular acceleration / velocity of the "dynamic" level (umeh2: 100 rad/s2,
# 6 rad/s, walking/running), cable pull 1.0 N within 80 deg of straight down (bouncing cable).
TREADMILL = dict(a_up=1.5, a_down=1.0, a_ap=0.6, a_ml=0.4, cone=15.0, ang="dynamic", cable=1.0)


def treadmill_cases(mp, n_grav=5, n_cable=3, spec=TREADMILL):
    M, com, I, p_c = mp[:4]
    down = np.array([0, -1.0, 0])
    gd = sp.cone(sp.fib_sphere(400), down, spec["cone"])
    gset = [down] + list(gd[:: max(1, len(gd) // n_grav)])
    cd_all = sp.cone(sp.fib_sphere(60), down, sp.CABLE_CONE)
    cdirs = [down] + list(cd_all[:: max(1, len(cd_all) // n_cable)])
    w_cable = CABLE["mass_per_m"].v * CABLE["hang_len"].v * G
    acc = [np.array([i * spec["a_ap"], j, k * spec["a_ml"]])
           for i in (-1, 0, 1) for j in (-spec["a_down"], 0.0, spec["a_up"]) for k in (-1, 0, 1)]     # skin frame: x fore-aft, y up, z lateral
    for gdir in gset:
        for a in acc:
            for ax, s, w in sp.ANG_CASES:
                for cd in cdirs:
                    g_eff = G * (gdir - a)          # the module feels gravity minus the head's acceleration
                    gn = np.linalg.norm(g_eff)
                    W = sp.inertial_wrench(M, com, I, g_eff, ax, s * sp.ALPHA[spec["ang"]], w * sp.OMEGA[spec["ang"]]) \
                        if ax else sp.inertial_wrench(M, com, I, g_eff)
                    W = W + cable_wrench(p_c, w_cable * (g_eff / gn if gn > 0 else down)) + cable_wrench(p_c, spec["cable"] * np.asarray(cd))
                    yield dict(g=gdir.tolist(), acc=a.tolist(), axis=ax, sign=s, omega=bool(w), cable=np.asarray(cd).tolist()), W


def cases(mp, cat, n_dir=60, n_cable=3, n_grav=7, grid=None):
    """(tag, wrench) of every case of category cat (umeh2.support.load_cases with the cable at the socket);
    cat "treadmill": treadmill_cases."""
    if cat == "treadmill":
        yield from treadmill_cases(mp, n_grav=min(n_grav, 5), n_cable=n_cable)
        return
    M, com, I, p_c = mp[:4]
    spec = sp.CATEGORIES[cat]
    down = np.array([0, -1.0, 0])
    if spec["cone"] is None:
        gset = [np.zeros(3)]; dyn_dirs = sp.fib_sphere(n_dir)
    elif spec.get("grid"):
        g_ = grid or sp.GRID_1G
        gset = sp.ring_grid(g_["tilt"], g_["az_step"]); dyn_dirs = [np.zeros(3)]
    else:
        gd = sp.cone(sp.fib_sphere(max(n_grav * 400 // max(int(spec["cone"]), 1), 12)), down, spec["cone"])
        gset = [down] + list(gd[:: max(1, len(gd) // n_grav)])
        dyn_dirs = sp.fib_sphere(n_dir)
    if spec.get("grid"):
        g_ = grid or sp.GRID_1G
        cdirs = sp.ring_grid(g_["cable_polar"], g_["cable_az_step"])
    else:
        cd_all = sp.cone(sp.fib_sphere(60), down, sp.CABLE_CONE)
        cdirs = [down] + list(cd_all[:: max(1, len(cd_all) // n_cable)])
    w_cable = CABLE["mass_per_m"].v * CABLE["hang_len"].v * G
    for gdir in gset:
        for ddir in dyn_dirs:
            for ax, s, w in sp.ANG_CASES:
                for cd in cdirs:
                    g_eff = G * (gdir + spec["dyn"] * np.asarray(ddir))
                    gn = np.linalg.norm(g_eff)
                    W = sp.inertial_wrench(M, com, I, g_eff, ax, s * sp.ALPHA[spec["ang"]], w * sp.OMEGA[spec["ang"]]) \
                        if ax else sp.inertial_wrench(M, com, I, g_eff)
                    W = W + cable_wrench(p_c, w_cable * (g_eff / gn if gn > 0 else down)) + cable_wrench(p_c, spec["cable"] * np.asarray(cd))
                    yield dict(g=gdir.tolist(), dyn=np.asarray(ddir).tolist(), axis=ax, sign=s, omega=bool(w),
                               cable=np.asarray(cd).tolist()), W


KEYS_MAX = ("pad_p", "root_p", "helix_p", "sulcus_p", "lobe_p", "pinna_p", "rot", "disp", "util")


def sweep(mp, v, cat, seq="A", **kw):
    """Worst values over every case of cat for design variables v. Released = gross slip / beyond small motion;
    clamp_lost = the rear leg would leave the pinna (clamp force <= 0); pad_open = fewer than all 16 pad sectors
    touching (seal broken)."""
    C, link, info = ct.contact_set(v)
    model = sp.Model(C, link)
    if not model.set_base(static_wrench(mp), seq=seq):
        return dict(ok=False, why=model.base_why)
    worst = {k: (-np.inf, None) for k in KEYS_MAX}
    worst["n_pad"] = (np.inf, None); worst["clamp"] = (np.inf, None)
    n = rel = lost = opened = 0
    for tag, W in cases(mp, cat, **kw):
        n += 1
        r = model.solve(W)
        if not r["ok"]:
            rel += 1
            continue
        m = ct.metrics(r, C, info)
        lost += m["clamp"] <= 0
        opened += m["n_pad"] < ct.N_PAD
        for k in KEYS_MAX:
            if m[k] > worst[k][0]:
                worst[k] = (m[k], tag)
        for k in ("n_pad", "clamp"):
            if m[k] < worst[k][0]:
                worst[k] = (m[k], tag)
    return dict(ok=True, n=n, released=rel, clamp_lost=lost, pad_open=opened,
                worst={k: x[0] for k, x in worst.items()}, tags={k: x[1] for k, x in worst.items()}, info=info)


def static(mp, v, seq="A"):
    C, link, info = ct.contact_set(v)
    model = sp.Model(C, link)
    if not model.set_base(static_wrench(mp), seq=seq):
        return dict(ok=False, why=model.base_why)
    r = model.solve(static_wrench(mp))
    return dict(ok=r["ok"], m=ct.metrics(r, C, info) if r["ok"] else None, r=r, info=info, model=model, C=C)


def shakedown(mp, v, cat="2 g dynamic", seq="A", n_cyc=12, **kw):
    """Repeated head motion (every case of cat applied and removed, cycle after cycle) from donning sequence seq;
    the sustained state in use. Returns the umeh2.support.shakedown dict + metrics of the final state."""
    C, link, info = ct.contact_set(v)
    model = sp.Model(C, link)
    W_st = static_wrench(mp)
    W = [w for _, w in cases(mp, cat, **kw)]
    sd = sp.shakedown(model, W_st, W, seq=seq, n_cyc=n_cyc, pads=ct.PADS)
    if not sd.get("ok"):
        return sd
    model.base = (model._pad(W_st), sd["state"])
    r = model.solve(W_st)
    sd["m"] = ct.metrics(r, C, info) if r["ok"] else None
    sd["info"] = info
    return sd


def tug_limits(mp, v, polar=(0.0, 30.0, 60.0, 80.0), az_step=45.0, F_max=6.0, n_bis=7, seq="A"):
    """Largest cable pull (N) the side holds (no release) from the donned state, head upright, per direction of the
    pull: polar angle from straight down x azimuth (0 = forward, 90 = outward, away from the head). Bisection."""
    C, link, info = ct.contact_set(v)
    model = sp.Model(C, link)
    W0 = static_wrench(mp)
    if not model.set_base(W0, seq=seq):
        return None
    p_c = mp[3]
    out = []
    for d in sp.ring_grid(polar, az_step):
        lo, hi = 0.0, F_max
        if model.solve(W0 + cable_wrench(p_c, F_max * d))["ok"]:
            lo = F_max
        else:
            for _ in range(n_bis):
                mid = 0.5 * (lo + hi)
                if model.solve(W0 + cable_wrench(p_c, mid * d))["ok"]:
                    lo = mid
                else:
                    hi = mid
        out.append(dict(dir=np.round(d, 3).tolist(), F=lo))
    return out
