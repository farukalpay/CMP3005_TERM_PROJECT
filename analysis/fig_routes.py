"""Figure: best routes on the team instance and on the real Istanbul instance.

Colour per route (Task 7) with the 8-slot palette assigned by greedy colouring of the
route-neighbourhood graph (neighbouring routes never share a colour) + route numbers.
Right panels emphasise the routes that cross the Bosphorus (highlight one, grey the rest).
"""
from __future__ import annotations

import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from data import RAW, ROOT
from fig_instances import draw_districts, istanbul_axes, scale_bar, synthetic_axes
from medidrone import style
from medidrone.vrpio import read_instance

style.apply()
HIGHLIGHT = "#6250d6"   # violet slot: not used for algorithms


def best_solution(name):
    best = None
    for folder in ("main", "long", "tune_ts", "tune_ma", "tune_ga"):
        for p in (RAW / folder).glob(f"{name}_*.json"):
            r = json.loads(p.read_text())
            if r.get("feasible") and r["alg"] != "cw" and (best is None or r["cost"] < best["cost"]):
                best = r
    return best


def crossings(inst, route):
    s = inst.side
    path = [0, *route, 0]
    return sum(int(s[a] != s[b]) for a, b in zip(path[:-1], path[1:]))


def draw_routes(ax, xy, routes, colors=None, lw=1.1, emph=None, inst=None, labels=False):
    for k, r in enumerate(routes):
        path = np.array([xy[0]] + [xy[v] for v in r] + [xy[0]])
        if emph is not None:
            c = HIGHLIGHT if emph[k] else "#b9b7ae"
            z = 4 if emph[k] else 3
            ax.plot(path[:, 0], path[:, 1], color=c, lw=lw if emph[k] else 0.7, zorder=z, solid_joinstyle="round")
        else:
            ax.plot(path[:, 0], path[:, 1], color=colors[k], lw=lw, zorder=3, solid_joinstyle="round")
        pts = np.array([xy[v] for v in r])
        ax.scatter(pts[:, 0], pts[:, 1], s=6, color=style.INK2 if emph is not None else colors[k], zorder=5,
                   edgecolor=style.SURFACE, lw=0.3)
        if labels and emph is None:
            far = max(r, key=lambda v: np.hypot(*(xy[v] - xy[0])))
            style.label(ax, xy[far][0], xy[far][1], str(k + 1), fontsize=5.2, color=style.INK, ha="center",
                        va="center", zorder=7)


def main():
    syn = read_instance(ROOT / "data/medidrone/MediDrone-7273.vrp")
    ist = read_instance(ROOT / "data/istanbul/MediDrone-IST-7273.vrp")
    nodes = pd.read_csv(ROOT / "data/istanbul/MediDrone-IST-7273_nodes.csv")
    bs, bi = best_solution("MediDrone-7273"), best_solution("MediDrone-IST-7273")
    Rs = sorted(bs["routes"], key=lambda r: np.arctan2(*(syn.xy[r].mean(0) - syn.xy[0])[::-1]))
    Ri = sorted(bi["routes"], key=lambda r: np.arctan2(*(ist.xy[r].mean(0) - ist.xy[0])[::-1]))
    fig = plt.figure(figsize=(style.TEXTWIDTH, 2.55))
    gs = fig.add_gridspec(1, 3, width_ratios=[1, 1, 1.42], wspace=0.16)

    ax = fig.add_subplot(gs[0])
    synthetic_axes(ax, side_labels=False)
    draw_routes(ax, syn.xy, Rs, colors=style.route_colors(syn.xy, Rs))
    ax.scatter([500], [500], marker="s", s=26, color=style.INK, zorder=8)
    ax.set_title(f"(a) {len(Rs)} drones")
    ax.set_xlabel(f"total cost {bs['cost']:,.1f}\n{len(Rs)} drones used (K = {syn.K})", fontsize=6.4,
                  color=style.INK2)

    ax = fig.add_subplot(gs[1])
    synthetic_axes(ax, side_labels=False)
    emph = [crossings(syn, r) > 0 for r in Rs]
    draw_routes(ax, syn.xy, Rs, emph=emph)
    ax.scatter([500], [500], marker="s", s=26, color=style.INK, zorder=8)
    nc = sum(emph)
    cmax = max(crossings(syn, r) for r in Rs)
    ax.set_title(f"(b) {nc} of them cross")
    qE = int(syn.q[syn.side == 0].sum())
    ax.set_xlabel(f"European demand {qE}\n$\\Rightarrow$ at least {int(np.ceil(qE / 100))} crossing routes",
                  fontsize=6.4, color=style.INK2)

    ax = fig.add_subplot(gs[2])
    lonlat = nodes[["lon", "lat"]].to_numpy()
    istanbul_axes(ax, extent=(28.70, 29.36, 40.86, 41.16))
    draw_districts(ax)
    emph_i = [crossings(ist, r) > 0 for r in Ri]
    draw_routes(ax, lonlat, Ri, emph=emph_i, lw=1.1)
    ax.scatter([lonlat[0, 0]], [lonlat[0, 1]], marker="s", s=26, color=style.INK, zorder=8)
    qA = int(ist.q[ist.side == 1].sum())
    ax.set_title(f"(c) Istanbul: {sum(emph_i)} of {len(Ri)} cross")
    ax.set_xlabel(f"total {bi['cost']:.1f} km, Asian demand {qA}\n$\\Rightarrow$ at least {int(np.ceil(qA / 100))} crossing routes",
                  fontsize=6.4, color=style.INK2)
    scale_bar(ax, 29.24, 40.875)
    style.save(fig, "routes")
    stats = dict(syn_cost=bs["cost"], syn_alg=bs["alg"], syn_routes=len(Rs), syn_cross=nc, syn_maxc=cmax, syn_qE=qE,
                 ist_cost=bi["cost"], ist_alg=bi["alg"], ist_routes=len(Ri), ist_cross=sum(emph_i), ist_qA=qA,
                 ist_maxc=max(crossings(ist, r) for r in Ri))
    json.dump(stats, open(ROOT / "results/routes_stats.json", "w"), indent=1)
    print(stats)


if __name__ == "__main__":
    main()
