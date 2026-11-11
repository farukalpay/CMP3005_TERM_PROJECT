"""Figure: parameter sensitivity (tuning seeds 101-105, 10 s per run).
(a) TS: tabu tenure x granularity k -> mean gap (team instance)  [heatmap]
(b) TS tenure on two instances (U-shape)                           [dot + range]
(c) GA: mutation rate x population -> mean gap                     [heatmap]
(d) GA population diversity over time for several mutation rates  [lines]
"""
from __future__ import annotations

import json
import re
from collections import defaultdict

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import BoundaryNorm

from data import RAW, ROOT, references
from medidrone import style

style.apply()


def load(folder, rx):
    out = defaultdict(list)
    for p in sorted((RAW / folder).glob("*.json")):
        m = re.match(rx, p.name)
        if not m:
            continue
        r = json.loads(p.read_text())
        out[m.groups()].append(r)
    return out


def heat(ax, M, xt, yt, xl, yl, title, fmt="{:.2f}", vmax=None):
    vmax = vmax or np.nanmax(M)
    levels = np.linspace(0, vmax, 9)
    norm = BoundaryNorm(levels, style.SEQ_CMAP.N, extend="max")
    im = ax.imshow(M, cmap=style.SEQ_CMAP, norm=norm, aspect="auto", origin="lower")
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            v = M[i, j]
            ax.text(j, i, fmt.format(v), ha="center", va="center", fontsize=5.6,
                    color="#ffffff" if v > 0.55 * vmax else style.INK)
    best = np.unravel_index(np.nanargmin(M), M.shape)
    ax.add_patch(plt.Rectangle((best[1] - 0.5, best[0] - 0.5), 1, 1, fill=False, ec=style.ALG["ts"], lw=1.4))
    ax.set_xticks(range(len(xt))); ax.set_xticklabels(xt)
    ax.set_yticks(range(len(yt))); ax.set_yticklabels(yt)
    ax.set_xlabel(xl); ax.set_ylabel(yl); ax.set_title(title)
    ax.grid(False)
    for sp in ax.spines.values():
        sp.set_visible(False)
    return im


def main():
    refs = references()
    ref = refs["MediDrone-7273"]
    ts = load("tune_ts", r"(.*)_t(\d+)-(\d+)_k(\d+)_s(\d+)\.json")
    ga = load("tune_ga", r".*_pm([\d.]+)_pop(\d+)_s(\d+)\.json")
    fig = plt.figure(figsize=(style.TEXTWIDTH, 2.45))
    gs = fig.add_gridspec(1, 4, width_ratios=[1.05, 0.95, 1.05, 1.1], wspace=0.62)
    # (a) TS heatmap
    tens = sorted({(int(a), int(b)) for (nm, a, b, k, s) in ts if nm == "MediDrone-7273"})
    ks = sorted({int(k) for (nm, a, b, k, s) in ts if nm == "MediDrone-7273"})
    M = np.full((len(tens), len(ks)), np.nan)
    agg = defaultdict(list)
    for (nm, a, b, k, s), R in ts.items():
        agg[(nm, int(a), int(b), int(k))] += [r["cost"] for r in R]
    for i, (a, b) in enumerate(tens):
        for j, k in enumerate(ks):
            v = agg.get(("MediDrone-7273", a, b, k))
            if v:
                M[i, j] = 100 * (np.mean(v) - ref) / ref
    ax = fig.add_subplot(gs[0])
    heat(ax, M, [str(k) for k in ks], [f"{a}–{b}" for a, b in tens], "neighbours k", "tabu tenure θ",
         "(a) TS: mean gap (%)", vmax=2.0)
    # (b) tenure U-shape on two instances
    ax = fig.add_subplot(gs[1])
    refA = 1763.0
    for nm, col, r0 in (("MediDrone-7273", style.ALG["ts"], ref), ("A-n80-k10", style.INK2, refA)):
        xs, med, lo, hi = [], [], [], []
        for i, (a, b) in enumerate(tens):
            v = agg.get((nm, a, b, 20))
            if not v:
                continue
            g = 100 * (np.array(v) - r0) / r0
            xs.append(i); med.append(np.mean(g)); lo.append(g.min()); hi.append(g.max())
        xs = np.array(xs, float) + (0.12 if nm.startswith("A") else -0.12)
        ax.vlines(xs, lo, hi, color=col, lw=1.0, alpha=0.6)
        ax.plot(xs, med, "-o", color=col, ms=3.2, lw=1.1, label=nm)
    ax.set_xticks(range(len(tens))); ax.set_xticklabels([f"{a}" for a, b in tens], fontsize=5.6)
    ax.set_xlabel("θ$_{min}$ (θ$_{max}$ ≈ 2.5 θ$_{min}$)"); ax.set_ylabel("gap (%), k = 20")
    ax.set_title("(b) Tenure: U-shape")
    style.legend_below(ax, ncol=1, dy=-0.33, fontsize=5.8)
    # (c) GA heatmap
    pms = sorted({float(pm) for (pm, pop, s) in ga}); pops = sorted({int(pop) for (pm, pop, s) in ga})
    G = np.full((len(pms), len(pops)), np.nan)
    gagg = defaultdict(list)
    for (pm, pop, s), R in ga.items():
        gagg[(float(pm), int(pop))] += [r["cost"] for r in R]
    for i, pm in enumerate(pms):
        for j, pop in enumerate(pops):
            v = gagg.get((pm, pop))
            if v:
                G[i, j] = 100 * (np.mean(v) - ref) / ref
    ax = fig.add_subplot(gs[2])
    heat(ax, G, [str(p) for p in pops], [f"{pm:g}" for pm in pms], "population μ", "mutation rate p$_m$",
         "(c) GA: mean gap (%)", fmt="{:.1f}", vmax=6.0)
    # (d) diversity over time
    ax = fig.add_subplot(gs[3])
    shades = {0.0: "#9ec5f4", 0.1: "#5598e7", 1.0: "#104281"}
    for pm in (0.0, 0.1, 1.0):
        curves = []
        for s in range(101, 106):
            R = ga.get((str(pm) if str(pm) in {k[0] for k in ga} else f"{pm}", "100", str(s)))
            if not R:
                continue
            d = np.array(R[0].get("div", []))
            if len(d):
                curves.append(d)
        if not curves:
            continue
        tg = np.logspace(-2, 1, 60)
        Y = np.array([np.interp(tg, c[:, 1], c[:, 4], left=np.nan) for c in curves])
        ax.plot(tg, np.nanmedian(Y, 0), color=shades[pm], lw=1.4, label=f"p$_m$ = {pm:g}")
    ax.set_xscale("log")
    ax.set_xlabel("time (s)"); ax.set_ylabel("mean broken-pairs distance")
    ax.set_title("(d) GA diversity (μ = 100)")
    style.legend_below(ax, ncol=3, dy=-0.33, fontsize=5.8)
    style.save(fig, "sensitivity")


if __name__ == "__main__":
    main()
