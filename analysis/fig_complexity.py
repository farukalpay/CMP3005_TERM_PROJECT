"""Figure: empirical validation of the complexity analysis (Task 6) + LaTeX table of slopes."""
from __future__ import annotations

import json
from collections import defaultdict

import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

from data import ROOT
from medidrone import style

style.apply()


def fit(x, y):
    """log-log least squares: slope, 95% CI half-width, intercept."""
    lx, ly = np.log(x), np.log(y)
    r = stats.linregress(lx, ly)
    t = stats.t.ppf(0.975, len(x) - 2) if len(x) > 2 else np.nan
    return r.slope, t * r.stderr, r.intercept


def main():
    rows = json.loads((ROOT / "results/raw/complexity/complexity.json").read_text())
    K = defaultdict(list)
    for r in rows:
        K[r["kind"]].append(r)
    for k in K:
        K[k].sort(key=lambda r: (r["n"], r.get("Q", 0)))

    def series(kind, key="time_per_iter", maxn=None):
        R = [r for r in K[kind] if maxn is None or r["n"] <= maxn]
        return np.array([r["n"] for r in R], float), np.array([r[key] for r in R], float)

    fig = plt.figure(figsize=(style.TEXTWIDTH, 2.6))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.1, 1.25, 0.95], wspace=0.3)

    # ---------------- (a) time per iteration / generation
    ax = fig.add_subplot(gs[0])
    spec = [("ts", "TS iteration, $k=20$", style.ALG["ts"], "o", 1600),
            ("ts_full", "TS iteration, $k=n-1$", style.ALG["ts"], "s", None),
            ("ga", "GA generation ($\\mu=50$)", style.ALG["ga"], "o", None),
            ("ma", "MA generation ($\\mu=30$)", style.ALG["ma"], "D", None)]
    slopes = {}
    for kind, lab, col, mk, maxfit in spec:
        x, y = series(kind)
        filled = kind != "ts_full"
        ax.plot(x, y * 1e3, color=col, lw=1.1, alpha=0.9, zorder=2)
        ax.scatter(x, y * 1e3, s=16, marker=mk, facecolor=col if filled else style.SURFACE, edgecolor=col,
                   linewidth=1.0, zorder=3)
        xf, yf = series(kind, maxn=maxfit)
        s, ci, _ = fit(xf, yf)
        slopes[kind] = (s, ci)
        style.label(ax, x[-1] * 1.12, y[-1] * 1e3, f"{s:.2f}", fontsize=6.5, va="center", color=style.INK)
    xx, yx = series("x_ts")
    ax.scatter(xx, yx * 1e3, s=14, marker="^", facecolor=style.SURFACE, edgecolor=style.INK2, lw=0.8, zorder=4,
               label="TS on X instances")
    slopes["x_ts"] = fit(xx, yx)[:2]
    x, y = series("ts")
    ax.annotate("matrix exceeds\non-chip cache", xy=(3200, y[-1] * 1e3 * 0.8), xytext=(900, 0.03), fontsize=5.8,
                color=style.INK2, ha="center", arrowprops=dict(arrowstyle="-", color=style.MUTED, lw=0.5))
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("customers $n$"); ax.set_ylabel("ms per iteration / generation")
    ax.set_title("(a) Cost per step")
    ax.set_xlim(18, 9000)
    from matplotlib.lines import Line2D
    h = [Line2D([], [], color=style.ALG["ts"], marker="o", lw=1, ms=3.5, label="TS, $k=20$"),
         Line2D([], [], color=style.ALG["ts"], marker="s", mfc=style.SURFACE, lw=1, ms=3.5, label="TS, full $k=n-1$"),
         Line2D([], [], color=style.ALG["ga"], marker="o", lw=1, ms=3.5, label="GA"),
         Line2D([], [], color=style.ALG["ma"], marker="D", lw=1, ms=3.5, label="MA"),
         Line2D([], [], color=style.INK2, marker="^", mfc=style.SURFACE, lw=0, ms=3.5, label="TS on X set")]
    style.legend_below(ax, handles=h, ncol=2, dy=-0.27, fontsize=5.6)

    # ---------------- (b) predicted vs measured exponents
    ax = fig.add_subplot(gs[1])
    ev = K["eval"]
    n_ev = np.array([r["n"] for r in ev], float)
    for key, nm in (("t_delta", "delta"), ("t_route", "route"), ("t_full", "full")):
        y = np.array([r[key] / r["moves"] for r in ev])
        slopes["eval_" + nm] = fit(n_ev, y)[:2] if nm == "full" else fit(n_ev[n_ev <= 800], y[n_ev <= 800])[:2]
    sq = K["split_Q"]
    Ls = np.array([r["avg_route_len"] for r in sq])
    slopes["split_bellman_L"] = fit(Ls, np.array([r["t_bellman"] for r in sq]))[:2]
    slopes["split_linear_L"] = fit(Ls, np.array([r["t_linear"] for r in sq]))[:2]
    items = [("TS, $k$ fixed", "ts", 1), ("TS, $k=n{-}1$", "ts_full", 2), ("TS, X set", "x_ts", 1),
             ("GA generation", "ga", 1), ("delta eval.", "eval_delta", 0),
             ("route re-eval.", "eval_route", 0), ("full re-eval.", "eval_full", 1),
             ("Bellman vs $L$", "split_bellman_L", 1), ("deque vs $L$", "split_linear_L", 0)]
    for i, (lab, key, th) in enumerate(items):
        s, ci = slopes[key]
        yv = len(items) - 1 - i
        ax.plot([th], [yv], marker="o", ms=6, mfc=style.SURFACE, mec=style.INK2, mew=1.0, zorder=3)
        col = style.ALG["ts"] if ("TS" in lab or "eval" in lab) else style.ALG["ga"]
        ax.errorbar([s], [yv], xerr=[[ci], [ci]], fmt="o", ms=3.6, color=col, elinewidth=1.0, capsize=0, zorder=4)
        ax.text(-2.4, yv, lab, ha="left", va="center", fontsize=6.3, color=style.INK2)
    ax.set_yticks([]); ax.set_xlim(-2.45, 2.45); ax.set_ylim(-0.7, len(items) - 0.3)
    ax.set_xticks([0, 1, 2]); ax.set_xticklabels(["$n^0$", "$n^1$", "$n^2$"])
    ax.tick_params(axis="x", pad=1)
    ax.grid(axis="y", visible=False)
    ax.set_title("(b) Exponents")
    from matplotlib.lines import Line2D as L2
    style.legend_below(ax, handles=[L2([], [], marker="o", ms=5, mfc=style.SURFACE, mec=style.INK2, lw=0,
                                       label="predicted"),
                                    L2([], [], marker="o", ms=3.6, color=style.INK2, lw=1, label="fitted ± 95% CI")],
                       ncol=2, dy=-0.12, fontsize=5.6)
    ax.spines["left"].set_visible(False)

    # ---------------- (c) Split vs route length
    ax = fig.add_subplot(gs[2])
    ax.plot(Ls, [r["t_bellman"] * 1e6 for r in sq], "-o", color=style.ALG["ga"], ms=3.2, lw=1.1, label="Bellman $O(nL)$")
    ax.plot(Ls, [r["t_linear"] * 1e6 for r in sq], "-s", color=style.INK2, ms=3.2, lw=1.1, mfc=style.SURFACE,
            label="deque $O(n)$")
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("customers per route $L$")
    ax.set_ylabel("µs per Split call")
    ax.set_title("(c) Split, $n=1000$")
    yb, yl = sq[-1]["t_bellman"] * 1e6, sq[-1]["t_linear"] * 1e6
    ax.annotate("", xy=(Ls[-1] * 1.15, yb), xytext=(Ls[-1] * 1.15, yl),
                arrowprops=dict(arrowstyle="<->", color=style.MUTED, lw=0.6))
    style.label(ax, Ls[-1] * 0.95, np.sqrt(yb * yl), f"{yb / yl:.0f}×", ha="right", va="center", fontsize=6.5,
                color=style.INK)
    ax.set_yticks([20, 50, 100, 200, 500]); ax.set_yticklabels(["20", "50", "100", "200", "500"])
    ax.set_xlim(1.6, 900)
    style.legend_below(ax, ncol=1, dy=-0.27, fontsize=5.6)
    style.save(fig, "complexity")

    # LaTeX table of slopes
    names = {"ts": ("TS iteration, granular $k=20$", "1"), "ts_full": ("TS iteration, full neighbourhood", "2"),
             "x_ts": ("TS iteration on X instances", "1"), "ga": ("GA generation, linear Split", "1"),
             "ma": ("MA generation (incl.\\ local search)", "--"), "eval_delta": ("one move, $O(1)$ delta", "0"),
             "eval_route": ("one move, route re-evaluation", "0 ($L$ fixed)"),
             "eval_full": ("one move, full re-evaluation", "1"),
             "split_bellman_L": ("Bellman Split vs.\\ $L$ ($n$ fixed)", "1"),
             "split_linear_L": ("linear Split vs.\\ $L$ ($n$ fixed)", "0")}
    L = ["\\begin{tabular}{lcc}", "\\toprule", "Measured quantity & predicted exponent & fitted slope (95\\% CI) \\\\",
         "\\midrule"]
    for k, (nm, th) in names.items():
        s, ci = slopes[k]
        L.append(f"{nm} & {th} & ${s:.2f}\\pm{ci:.2f}$ \\\\")
    L += ["\\bottomrule", "\\end{tabular}"]
    (ROOT / "report/tables").mkdir(parents=True, exist_ok=True)
    (ROOT / "report/tables/slopes.tex").write_text("\n".join(L) + "\n")
    json.dump({k: list(v) for k, v in slopes.items()}, open(ROOT / "results/slopes.json", "w"), indent=1)
    print({k: (round(v[0], 3), round(v[1], 3)) for k, v in slopes.items()})


if __name__ == "__main__":
    main()
