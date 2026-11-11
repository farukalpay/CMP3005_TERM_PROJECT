"""Figure: search trajectory networks (STN, Ochoa et al. 2021) in *partition space*.

A location is the partition of the customers into routes (the order inside routes is
ignored), i.e. the bin-packing/clustering decision that Theorem 6 shows to be hard.
Nodes = partitions visited by the best-so-far trajectories of the 30 runs (10 GA,
10 TS, 10 MA) of one instance; edges = consecutive distinct partitions of a run.
Distances between partitions = transfer distance (minimum number of customers that must be
relocated to turn one partition into the other; Hungarian algorithm on the overlap matrix).
"""
from __future__ import annotations

import json
from collections import defaultdict

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from scipy.optimize import linear_sum_assignment

from data import RAW, ROOT, references
from medidrone import style
from medidrone.vrpio import read_sol_routes

style.apply()
ALGS = ["ga", "ma", "ts"]


def sig(routes):
    return frozenset(frozenset(r) for r in routes if r)


def transfer(A, B, n):
    A, B = [set(r) for r in A], [set(r) for r in B]
    M = np.array([[len(a & b) for b in B] for a in A])
    i, j = linear_sum_assignment(-M)
    return n - int(M[i, j].sum())


def load(name):
    runs = []
    for alg in ALGS:
        for p in sorted((RAW / "main").glob(f"{name}_{alg}_s*.json")):
            r = json.loads(p.read_text())
            runs.append((alg, r["seed"], r.get("snaps", []), r["n"]))
    return runs


def build(name, ref, best_routes, gmax=8.0):
    runs = load(name)
    n = runs[0][3]
    G = nx.DiGraph()
    best_sig = sig(best_routes)
    traj = []
    for alg, seed, snaps, _ in runs:
        seq, full = [], []
        for s in snaps:
            g = 100 * (s["cost"] - ref) / ref
            if g > gmax and s is not snaps[-1]:
                continue
            key = sig(s["routes"])
            full.append((g, key))
            if seq and seq[-1][0] == key:
                seq[-1] = (key, min(seq[-1][1], g), s["routes"])
                continue
            seq.append((key, g, s["routes"]))
        for k, (key, g, R) in enumerate(seq):
            if key not in G:
                G.add_node(key, gap=g, algs=set(), visits=0, routes=R, start=False, end=False)
            d = G.nodes[key]
            d["gap"] = min(d["gap"], g)
            d["algs"].add(alg)
            d["visits"] += 1
            d["start"] |= k == 0
            d["end"] |= k == len(seq) - 1
            if k:
                a = seq[k - 1][0]
                if G.has_edge(a, key):
                    G[a][key]["w"] += 1
                else:
                    G.add_edge(a, key, w=1, alg=alg)
        traj.append((alg, seed, full))
    for key, d in G.nodes(data=True):
        d["dist"] = transfer(d["routes"], best_routes, n)
        d["best"] = key == best_sig
    return G, traj, n


def node_color(d):
    if len(d["algs"]) > 1:
        return style.INK
    return style.ALG[next(iter(d["algs"]))]


def main():
    refs = references()
    fig = plt.figure(figsize=(style.TEXTWIDTH, 2.6))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.25, 1, 1], wspace=0.42)
    stats = {}
    for col, name in enumerate(["A-n45-k6", "MediDrone-7273"]):
        if not load(name):
            continue
        if name.startswith("A-"):
            ref = 944.0
            best_routes = read_sol_routes(ROOT / "data/cvrplib/A/A-n45-k6.sol")
        else:
            ref = refs[name]
            from fig_routes import best_solution
            best_routes = best_solution(name)["routes"]
        G, traj, n = build(name, ref, best_routes)
        stats[name] = dict(nodes=G.number_of_nodes(), edges=G.number_of_edges(),
                           shared=sum(len(d["algs"]) > 1 for _, d in G.nodes(data=True)),
                           best_reached={a: sum(1 for al, s, t in traj if al == a and t and t[-1][0] <= 1e-9)
                                         for a in ALGS},
                           end_dist={a: [G.nodes[t[-1][1]]["dist"] for al, s, t in traj if al == a and t] for a in ALGS})
        if col == 0:
            ax = fig.add_subplot(gs[0])
            U = G.to_undirected()
            pos = nx.spring_layout(U, k=0.9 / np.sqrt(max(1, U.number_of_nodes())), iterations=200, seed=7,
                                   weight=None)
            for a, b, d in G.edges(data=True):
                xa, ya = pos[a]; xb, yb = pos[b]
                ax.plot([xa, xb], [ya, yb], color=style.ALG[d["alg"]], lw=0.5, alpha=0.45, zorder=1)
            for key, d in G.nodes(data=True):
                x, y = pos[key]
                size = 6 + 5 * np.sqrt(d["visits"])
                mk = "s" if d["start"] else ("^" if d["end"] else "o")
                if d["best"]:
                    mk, size = "*", 120
                ax.scatter([x], [y], s=size, marker=mk, color=node_color(d) if not d["best"] else "#eda100",
                           edgecolor=style.SURFACE, lw=0.4, zorder=3 if not d["best"] else 5)
            ax.set_xticks([]); ax.set_yticks([]); ax.grid(False)
            for sp in ax.spines.values():
                sp.set_visible(False)
            ax.set_title(f"(a) STN, {name}")
            from matplotlib.lines import Line2D
            h = [Line2D([], [], marker="o", color=style.ALG[a], lw=1.0, ms=4, label=style.ALG_LABEL[a].split(" ")[0])
                 for a in ALGS]
            h += [Line2D([], [], marker="o", color=style.INK, lw=0, ms=4, label="shared"),
                  Line2D([], [], marker="s", color=style.MUTED, lw=0, ms=4, label="start"),
                  Line2D([], [], marker="^", color=style.MUTED, lw=0, ms=4, label="end of a run"),
                  Line2D([], [], marker="*", color="#eda100", lw=0, ms=7, label="optimum")]
            style.legend_top(fig, h, ncol=7, y=0.98)
        # ---------- distance-to-best vs gap trajectories (funnel view)
        ax = fig.add_subplot(gs[1 + col])
        for alg in ALGS:
            for al, seed, t in traj:
                if al != alg or not t:
                    continue
                xs = [G.nodes[k]["dist"] for _, k in t]
                ys = [max(g, 0) for g, _ in t]
                ax.plot(xs, ys, color=style.ALG[alg], lw=0.7, alpha=0.55, zorder=2)
                ax.scatter([xs[-1]], [ys[-1]], s=14, marker="^", color=style.ALG[alg], edgecolor=style.SURFACE,
                           lw=0.4, zorder=4)
        ax.set_yscale("symlog", linthresh=0.1, linscale=0.5)
        ax.set_ylim(-0.005, 12); ax.set_xlim(-1, None)
        ax.set_yticks([0, 0.1, 1, 10]); ax.set_yticklabels(["0", "0.1", "1", "10"])
        ax.set_xlabel("transfer distance to best")
        if col == 0:
            ax.set_ylabel("gap (%)")
        ax.set_title(f"({'bc'[col]}) Funnel, {name.replace('MediDrone-7273', 'team inst.')}")
    style.save(fig, "stn")
    json.dump({k: {kk: (vv if not isinstance(vv, dict) else vv) for kk, vv in v.items()} for k, v in stats.items()},
              open(ROOT / "results/stn_stats.json", "w"), indent=1, default=list)
    print(json.dumps(stats, default=list)[:1500])


if __name__ == "__main__":
    main()
