"""Appendix figure: inside Tabu Search (team instance, seed 1).
(a) strategic oscillation: the current solution in the (distance, overload) plane during
    the first 400 iterations (light = early, dark = late);
(b) share of feasible current solutions in a sliding window over the whole run;
(c) which neighbourhood produced the applied moves (shares per block of 1000 iterations).
"""
from __future__ import annotations

import json

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import LineCollection
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from data import RAW
from medidrone import style

style.apply()
MCOL = ["#6250d6", "#e87ba4", "#008300", "#eda100"]          # validated 4-slot order (violet, magenta, green, yellow)
MLAB = ["relocate", "swap", "2-opt", "2-opt*"]


def main():
    r = json.loads((RAW / "osc" / "MediDrone-7273_ts_s1.json").read_text())
    osc = np.array(r["osc"], float)       # it, dist, over, lambda (every 2nd iteration)
    fig = plt.figure(figsize=(style.TEXTWIDTH, 2.45))
    gs = fig.add_gridspec(1, 3, wspace=0.45, width_ratios=[1.1, 1.0, 1.0])

    ax = fig.add_subplot(gs[0])
    m = osc[:, 0] <= 400
    pts = osc[m][:, [1, 2]]
    seg = np.stack([pts[:-1], pts[1:]], 1)
    lc = LineCollection(seg, cmap=style.SEQ_CMAP, lw=0.8)
    lc.set_array(osc[m][:-1, 0])
    ax.add_collection(lc)
    ax.scatter(pts[:, 0], pts[:, 1], c=osc[m][:, 0], cmap=style.SEQ_CMAP, s=4, lw=0, zorder=3)
    ax.axhspan(-2, 0.6, color=style.ALG["ma"], alpha=0.15, lw=0)
    ax.set_xlim(pts[:, 0].min() - 100, pts[:, 0].max() + 100)
    ax.set_ylim(-2, pts[:, 1].max() * 1.08)
    ax.set_xlabel("total distance"); ax.set_ylabel("total overload")
    ax.set_title("(a) First 400 iterations")
    style.legend_below(ax, handles=[Line2D([], [], color=style.SEQ[2], lw=1.4, label="early"),
                                    Line2D([], [], color=style.SEQ[-1], lw=1.4, label="late"),
                                    Patch(color=style.ALG["ma"], alpha=0.3, label="feasible")],
                       ncol=3, dy=-0.3, fontsize=5.8)

    ax = fig.add_subplot(gs[1])
    feas = (osc[:, 2] == 0).astype(float)
    w = 250
    roll = np.convolve(feas, np.ones(w) / w, mode="valid")
    ax.plot(osc[w - 1:, 0], roll, color=style.ALG["ts"], lw=1.0)
    ax.set_ylim(0, 1)
    ax.set_xlabel("iteration"); ax.set_ylabel("share of feasible iterations")
    ax.set_title(f"(b) Feasible {100 * feas.mean():.0f}% of the time")

    ax = fig.add_subplot(gs[2])
    mh = np.array(r.get("move_hist", []), float)
    it = mh[:, 0]
    d = np.diff(np.vstack([np.zeros(5), mh]), axis=0)[:, 1:]
    share = d / np.maximum(d.sum(1, keepdims=True), 1)
    ax.stackplot(it, share.T, colors=MCOL, lw=0)
    ax.set_xlim(it[0], it[-1]); ax.set_ylim(0, 1)
    ax.set_xlabel("iteration"); ax.set_ylabel("share of applied moves")
    ax.set_title("(c) Moves actually applied")
    style.legend_below(ax, handles=[Patch(color=c, label=l) for c, l in zip(MCOL, MLAB)], ncol=4, dy=-0.3,
                       fontsize=5.8)
    style.save(fig, "ts_inside")
    tot = r["move_count"]
    s = sum(tot.values())
    print("feasible share", feas.mean(), {k: round(v / s, 3) for k, v in tot.items()})


if __name__ == "__main__":
    main()
