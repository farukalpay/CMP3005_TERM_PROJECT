"""Figure: beyond the four required instances.
(a) Performance profiles (Dolan & More 2002) on all 74 Augerat A/B/P instances.
(b) Per-instance mean gap vs instance size (strip of 74 x 3 dots).
(c) Scalability on Uchoa et al. X instances (n = 100..1000, 60 s, 3 seeds).
"""
from __future__ import annotations

import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from data import RAW, ROOT, with_gap
from medidrone import style

style.apply()
ALGS = ["ga", "ma", "ts"]


def load(folder):
    rows = []
    for p in sorted((RAW / folder).glob("*.json")):
        r = json.loads(p.read_text())
        for k in ("snaps", "osc", "div", "move_hist", "trace", "routes"):
            r.pop(k, None)
        rows.append(r)
    return pd.DataFrame(rows)


def main():
    ext = with_gap(load("extended"))
    fig = plt.figure(figsize=(style.TEXTWIDTH, 2.45))
    gs = fig.add_gridspec(1, 3, wspace=0.38)
    # (a) performance profile, ratio of mean cost to BKS
    ax = fig.add_subplot(gs[0])
    m = ext[ext.alg.isin(ALGS)].groupby(["instance", "alg"]).cost.mean().unstack()
    ref = ext.groupby("instance").ref.first()
    taus = np.linspace(1.0, 1.08, 400)
    for a in ALGS:
        r = (m[a] / ref).to_numpy()
        rho = [(r <= t + 1e-12).mean() for t in taus]
        ax.step((taus - 1) * 100, rho, where="post", color=style.ALG[a], lw=1.4,
                label=style.ALG_LABEL[a].split(" ")[0])
    ax.set_xlabel("within τ % of the BKS (mean of 5 runs)")
    ax.set_ylabel("fraction of the 74 instances")
    ax.set_title("(a) Performance profiles")
    ax.set_ylim(0, 1.02); ax.set_xlim(0, 8)
    style.legend_below(ax, ncol=3, dy=-0.3, fontsize=5.8)
    # (b) per-instance mean gap vs n
    ax = fig.add_subplot(gs[1])
    g = ext[ext.alg.isin(ALGS)].groupby(["instance", "alg"]).agg(gap=("gap", "mean"), n=("n", "first")).reset_index()
    rng = np.random.default_rng(3)
    for a in ALGS:
        s = g[g.alg == a]
        ax.scatter(s.n * np.exp(rng.normal(0, 0.02, len(s))), np.maximum(s.gap, 0), s=7, color=style.ALG[a],
                   alpha=0.75, lw=0, label=style.ALG_LABEL[a].split(" ")[0])
    ax.set_yscale("symlog", linthresh=0.1, linscale=0.5)
    ax.set_yticks([0, 0.1, 1, 10]); ax.set_yticklabels(["0", "0.1", "1", "10"])
    ax.set_xlabel("customers n"); ax.set_ylabel("mean gap (%)")
    ax.set_title("(b) Every A/B/P instance")
    style.legend_below(ax, ncol=3, dy=-0.3, fontsize=5.8, handletextpad=0.1)
    # (c) X set
    ax = fig.add_subplot(gs[2])
    xs = load("xset")
    if not xs.empty:
        xs = with_gap(xs)
        for a in ALGS:
            s = xs[xs.alg == a]
            agg = s.groupby("n").gap.agg(["mean", "min", "max"]).reset_index()
            ax.vlines(agg.n, agg["min"], agg["max"], color=style.ALG[a], lw=1.0, alpha=0.5)
            ax.plot(agg.n, agg["mean"], "-o", color=style.ALG[a], ms=3, lw=1.2, label=style.ALG_LABEL[a].split(" ")[0])
        cw = xs[xs.alg == "cw"].sort_values("n")
        ax.plot(cw.n, cw.gap, ":", color=style.INK2, lw=1.0, label="CW")
        style.legend_below(ax, ncol=4, dy=-0.3, fontsize=5.8)
        ax.set_xscale("log")
        ax.set_xticks([100, 200, 500, 1000]); ax.set_xticklabels(["100", "200", "500", "1000"])
        ax.set_xlim(90, 1150)
        ax.set_xlabel("customers n (X set, 60 s)"); ax.set_ylabel("gap to BKS (%)")
    ax.set_title("(c) Scaling to n = 1000")
    style.save(fig, "extended")


if __name__ == "__main__":
    main()
