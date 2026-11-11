"""Figure: the Bosphorus penalty P as a control parameter (Proposition 8 on data).

(a)-(d) Real Istanbul instance: best routes for P = 0, 1, 2, 5 km (crossing routes highlighted).
(e) Istanbul: number of crossing routes vs P, the bin-packing bound and the threshold predicted
    by Proposition 8(d) from the two competing solutions.
(f) Team instance: the optimum is the same for every P (it already attains the bound at P = 0),
    so its cost is exactly e* + 20 P.
"""
from __future__ import annotations

import json
import math
from collections import defaultdict

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import Bounds, LinearConstraint, milp

from data import RAW, ROOT
from fig_instances import draw_districts, istanbul_axes
from medidrone import style
from medidrone.vrpio import read_instance

style.apply()
HL = "#6250d6"


def bin_packing(sizes, C):
    """exact minimum number of bins (assignment MILP, HiGHS)"""
    m = len(sizes)
    ub = math.ceil(sum(sizes) / C) + 2
    nx_ = m * ub + ub
    c = np.concatenate([np.zeros(m * ub), np.ones(ub)])
    A, lo, hi = [], [], []
    for i in range(m):
        row = np.zeros(nx_); row[i * ub:(i + 1) * ub] = 1; A.append(row); lo.append(1); hi.append(1)
    for b in range(ub):
        row = np.zeros(nx_)
        for i in range(m):
            row[i * ub + b] = sizes[i]
        row[m * ub + b] = -C
        A.append(row); lo.append(-np.inf); hi.append(0)
    for b in range(ub - 1):
        row = np.zeros(nx_); row[m * ub + b] = -1; row[m * ub + b + 1] = 1; A.append(row); lo.append(-np.inf); hi.append(0)
    res = milp(c, constraints=LinearConstraint(np.array(A), lo, hi), integrality=np.ones(nx_),
               bounds=Bounds(0, 1), options=dict(time_limit=60))
    return int(round(res.fun))


def euclid_part(inst, routes):
    xy = inst.xy
    return sum(sum(math.dist(xy[a], xy[b]) for a, b in zip([0, *r], [*r, 0])) for r in routes)


def crossings(inst, r):
    p = [0, *r, 0]
    return sum(int(inst.side[a] != inst.side[b]) for a, b in zip(p[:-1], p[1:]))


def collect(prefix):
    rows = defaultdict(list)
    for p in sorted((RAW / "psweep").glob(f"{prefix}-P*_*.json")):
        r = json.loads(p.read_text())
        rows[float(r["instance"].split("-P")[-1])].append(r)
    out = {}
    for P, R in sorted(rows.items()):
        inst = read_instance(ROOT / R[0]["path"])
        best = min(R, key=lambda r: r["cost"])
        cr = [crossings(inst, rt) for rt in best["routes"]]
        out[P] = dict(best=best, inst=inst, cross_routes=sum(c > 0 for c in cr), zigzag=sum(c >= 4 for c in cr),
                      euclid=euclid_part(inst, best["routes"]), penalty=P * sum(cr), crossings=sum(cr),
                      routes=len(best["routes"]),
                      all_cross=[sum(crossings(inst, rt) > 0 for rt in r["routes"]) for r in R])
    return out


def main():
    syn, ist = collect("MediDrone-7273"), collect("MediDrone-IST-7273")
    base = read_instance(ROOT / "data/medidrone/MediDrone-7273.vrp")
    baseI = read_instance(ROOT / "data/istanbul/MediDrone-IST-7273.vrp")
    nodes = pd.read_csv(ROOT / "data/istanbul/MediDrone-IST-7273_nodes.csv")
    lonlat = nodes[["lon", "lat"]].to_numpy()
    bpE = bin_packing([int(x) for x in base.q[base.side == 0]], base.Q)
    bpA_syn = bin_packing([int(x) for x in base.q[1:][base.side[1:] == 1]], base.Q)
    bpA = bin_packing([int(x) for x in baseI.q[1:][baseI.side[1:] == 1]], baseI.Q)
    # threshold predicted by Proposition 8(d): two best solutions with X and X-2 crossings
    Ps = sorted(ist)
    hi = [P for P in Ps if ist[P]["crossings"] > 2 * bpA]
    lo = [P for P in Ps if ist[P]["crossings"] == 2 * bpA]
    thr = None
    if hi and lo:
        a, b = ist[max(hi)], ist[min(lo)]
        thr = (b["euclid"] - a["euclid"]) / (a["crossings"] - b["crossings"])

    fig = plt.figure(figsize=(style.TEXTWIDTH, 3.8))
    outer = fig.add_gridspec(2, 1, height_ratios=[1.0, 1.05], hspace=0.38)
    gs = outer[0].subgridspec(1, 4, wspace=0.08)
    gb = outer[1].subgridspec(1, 2, wspace=0.32)
    for j, P in enumerate([0.0, 1.0, 2.0, 5.0]):
        d = ist[P]
        ax = fig.add_subplot(gs[0, j])
        istanbul_axes(ax, extent=(28.90, 29.26, 40.88, 41.11))
        draw_districts(ax, lw=0.25)
        for r in d["best"]["routes"]:
            c = crossings(d["inst"], r)
            pth = np.array([lonlat[0]] + [lonlat[v] for v in r] + [lonlat[0]])
            ax.plot(pth[:, 0], pth[:, 1], color=HL if c else "#b9b7ae", lw=1.0 if c else 0.6, zorder=4 if c else 3)
        ax.scatter(lonlat[1:, 0], lonlat[1:, 1], s=3, color=style.INK2, zorder=5, lw=0)
        ax.scatter([lonlat[0, 0]], [lonlat[0, 1]], marker="s", s=14, color=style.INK, zorder=6)
        ax.set_title(f"({'abcd'[j]}) P = {P:g} km", fontsize=7.5)
        ax.set_xlabel(f"{d['cross_routes']} crossing routes", fontsize=6.4, color=style.INK2, labelpad=2)
    # (e) Istanbul crossing routes vs P
    ax = fig.add_subplot(gb[0])
    xs = np.array(Ps)
    xplot = np.where(xs == 0, 0.25, xs)
    for P, x in zip(Ps, xplot):
        v = ist[P]["all_cross"]
        jit = np.exp(np.random.default_rng(int(P * 10)).normal(0, 0.04, len(v)))
        ax.scatter(x * jit, v, s=9, color=HL, alpha=0.35, lw=0)
    ax.plot(xplot, [ist[P]["cross_routes"] for P in Ps], "-o", color=HL, ms=3.5, lw=1.2, label="best solution")
    ax.axhline(bpA, color=style.INK2, lw=0.8, label=f"bin-packing bound = {bpA}")
    if thr:
        ax.axvline(thr, color=style.ALG["ts"], lw=1.0, ls=(0, (3, 2)), label=f"predicted threshold {thr:.2f} km")
    ax.set_xscale("log")
    ax.set_xticks([0.25, 0.5, 1, 2, 5, 10, 20, 50]); ax.set_xticklabels(["0", "0.5", "1", "2", "5", "10", "20", "50"])
    ax.set_ylim(4.5, 8.5); ax.set_yticks([5, 6, 7, 8])
    ax.set_xlabel("crossing penalty P (km)"); ax.set_ylabel("routes crossing")
    ax.set_title("(e) Istanbul: a phase transition")
    style.legend_below(ax, ncol=2, dy=-0.33, fontsize=5.8)
    # (f) synthetic: invariant optimum
    ax = fig.add_subplot(gb[1])
    Pss = np.array(sorted(syn))
    eu = np.array([syn[P]["euclid"] for P in Pss])
    pen = np.array([syn[P]["penalty"] for P in Pss])
    pos = np.arange(len(Pss))
    ax.bar(pos, eu, color=style.ALG["ga"], width=0.7, label="flight distance $e(s)$")
    ax.bar(pos, pen, bottom=eu, color=HL, width=0.7, label="crossing penalty")
    ax.set_xticks(pos); ax.set_xticklabels([f"{P:g}" for P in Pss], fontsize=6)
    ax.set_xlabel("crossing penalty P"); ax.set_ylabel("best cost")
    same = len({round(x, 3) for x in eu}) == 1
    ax.set_title("(f) Team instance: invariant optimum" if same else "(f) Team instance")
    style.legend_below(ax, ncol=2, dy=-0.33, fontsize=5.8)
    style.save(fig, "psweep")
    if style.SLIDES:   # two single-row versions for the slides
        f1 = plt.figure(figsize=(style.TEXTWIDTH, 1.75))
        g1 = f1.add_gridspec(1, 4, wspace=0.08)
        for j, P in enumerate([0.0, 1.0, 2.0, 5.0]):
            d = ist[P]
            ax = f1.add_subplot(g1[0, j])
            istanbul_axes(ax, extent=(28.90, 29.26, 40.88, 41.11))
            draw_districts(ax, lw=0.25)
            for r in d["best"]["routes"]:
                c = crossings(d["inst"], r)
                pth = np.array([lonlat[0]] + [lonlat[v] for v in r] + [lonlat[0]])
                ax.plot(pth[:, 0], pth[:, 1], color=HL if c else "#b9b7ae", lw=1.0 if c else 0.6, zorder=4 if c else 3)
            ax.scatter(lonlat[1:, 0], lonlat[1:, 1], s=3, color=style.INK2, zorder=5, lw=0)
            ax.scatter([lonlat[0, 0]], [lonlat[0, 1]], marker="s", s=14, color=style.INK, zorder=6)
            ax.set_title(f"P = {P:g} km", fontsize=8)
            ax.set_xlabel(f"{d['cross_routes']} crossing", fontsize=7.5, color=style.INK2, labelpad=2)
        style.save(f1, "psweep_maps")
    summ = dict(bpE=bpE, bpA_syn=bpA_syn, bpA_ist=bpA, threshold_km=thr, qE=int(base.q[base.side == 0].sum()),
                qA_ist=int(baseI.q[1:][baseI.side[1:] == 1].sum()), syn_same_routes=same,
                syn={str(P): dict(cross=syn[P]["cross_routes"], zig=syn[P]["zigzag"], euclid=syn[P]["euclid"],
                                  cost=syn[P]["best"]["cost"], all_cross=syn[P]["all_cross"]) for P in Pss},
                ist={str(P): dict(cross=ist[P]["cross_routes"], zig=ist[P]["zigzag"], euclid=ist[P]["euclid"],
                                  cost=ist[P]["best"]["cost"], crossings=ist[P]["crossings"],
                                  all_cross=ist[P]["all_cross"]) for P in Ps})
    json.dump(summ, open(ROOT / "results/psweep_stats.json", "w"), indent=1)
    print("threshold", thr, "bp", bpE, bpA_syn, bpA, "same", same)


if __name__ == "__main__":
    main()
