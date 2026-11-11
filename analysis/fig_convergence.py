"""Figure: anytime behaviour. Row 1: convergence (median gap and inter-quartile band over
10 seeds) on three instances. Row 2: empirical attainment functions (EAF) on the team
instance: the probability that a run has reached gap <= g by time t, for every (t, g).
Each horizontal slice of an EAF panel is a time-to-target (TTT) distribution.
In slide mode the two rows are also saved as separate single-row figures."""
from __future__ import annotations

import json

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import BoundaryNorm
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from data import RAW, references
from medidrone import style

style.apply()
INST = [("A-n45-k6", 30), ("A-n80-k10", 60), ("MediDrone-7273", 60)]
ALGS = ["ga", "ma", "ts"]
BKS = {"A-n45-k6": 944, "A-n80-k10": 1763}


def runs(name, alg):
    out = []
    for p in sorted((RAW / "main").glob(f"{name}_{alg}_s*.json")):
        out.append(np.array(json.loads(p.read_text())["trace"], float))
    return out


def best_at(trace, grid):
    idx = np.searchsorted(trace[:, 0], grid, side="right") - 1
    return np.where(idx >= 0, trace[np.clip(idx, 0, None), 2], np.inf)


def legend(fig, y):
    style.legend_top(fig, [Line2D([], [], color=style.ALG[a], lw=1.6, label=style.ALG_LABEL[a]) for a in ALGS]
                     + [Patch(color=style.MUTED, alpha=0.25, label="inter-quartile range (10 seeds)")], ncol=4, y=y)


def conv_row(fig, cells, summary):
    refs = references()
    for j, (name, T) in enumerate(INST):
        ax = fig.add_subplot(cells[j])
        ref = BKS.get(name, refs.get(name))
        grid = np.logspace(-4, np.log10(T), 320)
        for alg in ALGS:
            R = runs(name, alg)
            if not R:
                continue
            G = np.array([100 * (best_at(t, grid) - ref) / ref for t in R])
            G = np.where(np.isinf(G), np.nan, G)
            med, q1, q3 = (np.nanpercentile(G, p, axis=0) for p in (50, 25, 75))
            ax.fill_between(grid, q1, q3, color=style.ALG[alg], alpha=0.18, lw=0)
            ax.plot(grid, med, color=style.ALG[alg], lw=1.3)
            summary[f"{name}|{alg}"] = float(med[-1])
        ax.set_xscale("log")
        ax.set_yscale("symlog", linthresh=0.1, linscale=0.6)
        ax.set_ylim(-0.01, 60)
        ax.set_yticks([0, 0.1, 1, 10]); ax.set_yticklabels(["0", "0.1", "1", "10"])
        ax.set_xticks([1e-4, 1e-2, 1, 1e2]); ax.set_xticklabels(["0.1 ms", "10 ms", "1 s", "100 s"])
        ax.set_xlim(1e-4, T * 1.3)
        ax.set_title(f"({'abc'[j]}) {name}")
        if j == 0:
            ax.set_ylabel("gap to best known (%)")
        ax.set_xlabel("wall-clock time")


def eaf_row(fig, cells, cax_rect, letters="def"):
    name, T = INST[2]
    ref = references().get(name)
    grid = np.logspace(-3, np.log10(T), 160)
    gaps = np.concatenate([[0], np.logspace(-2, np.log10(30), 120)])
    norm = BoundaryNorm(np.linspace(0, 1, 11), style.SEQ_CMAP.N)
    im = None
    for j, alg in enumerate(ALGS):
        ax = fig.add_subplot(cells[j])
        R = runs(name, alg)
        if not R:
            continue
        G = np.array([100 * (best_at(t, grid) - ref) / ref for t in R])
        A = (G[:, None, :] <= gaps[None, :, None] + 1e-9).mean(0)
        im = ax.pcolormesh(grid, np.arange(len(gaps)), A, cmap=style.SEQ_CMAP, norm=norm, shading="auto",
                           rasterized=True)
        ax.contour(grid, np.arange(len(gaps)), A, levels=[0.5], colors=[style.ALG[alg]], linewidths=1.3)
        ax.set_xscale("log")
        ax.set_yticks([0] + [int(np.searchsorted(gaps, v)) for v in (0.1, 1, 10)])
        ax.set_yticklabels(["0", "0.1", "1", "10"])
        ax.set_xticks([1e-3, 1e-1, 1e1]); ax.set_xticklabels(["1 ms", "0.1 s", "10 s"])
        ax.grid(False)
        ax.set_title(f"({letters[j]}) EAF, {style.ALG_LABEL[alg].split(' ')[0]}, team inst.")
        if j == 0:
            ax.set_ylabel("gap threshold g (%)")
        ax.set_xlabel("time t")
    cax = fig.add_axes(cax_rect)
    cb = fig.colorbar(im, cax=cax, ticks=[0, 0.5, 1])
    cb.set_label("P(gap ≤ g by t)", fontsize=6.5)
    cb.ax.tick_params(labelsize=6)
    cb.outline.set_visible(False)


def main():
    summary = {}
    fig = plt.figure(figsize=(style.TEXTWIDTH, 3.9))
    gs = fig.add_gridspec(2, 3, hspace=0.75, wspace=0.32)
    legend(fig, 0.955)
    conv_row(fig, [gs[0, j] for j in range(3)], summary)
    eaf_row(fig, [gs[1, j] for j in range(3)], [0.925, 0.11, 0.011, 0.27])
    style.save(fig, "convergence")
    if style.SLIDES:
        f1 = plt.figure(figsize=(style.TEXTWIDTH, 2.25))
        g1 = f1.add_gridspec(1, 3, wspace=0.34)
        legend(f1, 0.97)
        conv_row(f1, [g1[0, j] for j in range(3)], {})
        style.save(f1, "convergence_top")
        f2 = plt.figure(figsize=(style.TEXTWIDTH, 2.25))
        g2 = f2.add_gridspec(1, 3, wspace=0.34, right=0.9)
        eaf_row(f2, [g2[0, j] for j in range(3)], [0.925, 0.2, 0.012, 0.6], letters="abc")
        style.save(f2, "convergence_eaf")
    print(summary)


if __name__ == "__main__":
    main()
