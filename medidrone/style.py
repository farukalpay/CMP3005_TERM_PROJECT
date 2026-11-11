"""Shared matplotlib style: one palette, fixed colour roles, hairline chrome.

Colour roles (validated with the dataviz palette validator, --pairs all, light mode):
  GA  = blue  #2a78d6    TS = orange #eb6834    MA = aqua #1baf7a   (3 slots pass all-pairs)
  CW  = secondary ink (neutral baseline, not a categorical slot)
Routes on maps use the 8-slot categorical palette assigned by greedy graph colouring of
the route-neighbourhood graph (neighbouring routes never share a colour) plus direct
route labels (secondary encoding).  Sequential = one blue ramp; diverging = blue<->red
with a neutral grey midpoint.
"""
from __future__ import annotations

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

PALETTE = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
ALG = {"ga": "#2a78d6", "ts": "#eb6834", "ma": "#1baf7a", "cw": "#52514e"}
ALG_LABEL = {"ga": "GA", "ts": "TS", "ma": "MA (memetic GA)", "cw": "Clarke-Wright"}
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#898781"
GRID, AXIS, SURFACE = "#e1e0d9", "#c3c2b7", "#ffffff"
WATER, LAND_EU, LAND_AS = "#dbe9f7", "#f1efe9", "#ebeae4"
SEQ = ["#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec", "#5598e7", "#3987e5", "#2a78d6", "#256abf",
       "#1c5cab", "#184f95", "#104281", "#0d366b"]
SEQ_CMAP = LinearSegmentedColormap.from_list("seqblue", SEQ)
DIV_CMAP = LinearSegmentedColormap.from_list("divbr", ["#1c5cab", "#6da7ec", "#f0efec", "#ec8a8a", "#c23a3a"])

import os as _os
SLIDES = _os.environ.get("MEDIDRONE_SLIDES", "0") == "1"
TEXTWIDTH = 5.2 if SLIDES else 6.7   # inches: report text width (A4, 2 cm margins), or a 16:9 Beamer frame


def apply():
    mpl.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
        "mathtext.fontset": "custom",
        "mathtext.rm": "Helvetica Neue", "mathtext.it": "Helvetica Neue:italic", "mathtext.bf": "Helvetica Neue:bold",
        "font.size": 8, "axes.titlesize": 8.5, "axes.labelsize": 8, "xtick.labelsize": 7, "ytick.labelsize": 7,
        "legend.fontsize": 7, "legend.frameon": False,
        **({"font.size": 8.5, "axes.titlesize": 9, "axes.labelsize": 8.5, "xtick.labelsize": 7.5,
            "ytick.labelsize": 7.5} if SLIDES else {}),
        "axes.edgecolor": AXIS, "axes.linewidth": 0.6, "axes.labelcolor": INK2, "axes.titlecolor": INK,
        "axes.titleweight": "bold", "axes.titlelocation": "left", "axes.titlepad": 6,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.5, "grid.linestyle": "-",
        "xtick.color": MUTED, "ytick.color": MUTED, "xtick.major.width": 0.5, "ytick.major.width": 0.5,
        "xtick.major.size": 2.5, "ytick.major.size": 2.5, "xtick.labelcolor": INK2, "ytick.labelcolor": INK2,
        "lines.linewidth": 1.4, "lines.solid_capstyle": "round", "patch.linewidth": 0,
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "savefig.bbox": "tight", "savefig.pad_inches": 0.03, "pdf.fonttype": 42, "figure.dpi": 150,
        "text.color": INK,
    })


def save(fig, name, root=None):
    from . import ROOT
    out = (root or ROOT / ("figures/slides" if SLIDES else "figures"))
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / f"{name}.pdf")
    fig.savefig(out / f"{name}.png", dpi=220)
    plt.close(fig)


def route_colors(xy, routes):
    """Greedy colouring of the route-neighbourhood graph with the 8-slot palette.

    Two routes are neighbours if some pair of their customers are mutual near neighbours
    (k = 4) -- i.e. they share territory on the map. Routes are coloured in order of
    decreasing degree (Welsh-Powell); colours are slot indices, never generated hues."""
    m = len(routes)
    owner = {}
    for k, r in enumerate(routes):
        for v in r:
            owner[v] = k
    pts = np.array([xy[v] for r in routes for v in r])
    ids = [v for r in routes for v in r]
    D = np.sqrt(((pts[:, None] - pts[None]) ** 2).sum(-1))
    adj = [set() for _ in range(m)]
    for a in range(len(ids)):
        for b in np.argsort(D[a])[1:5]:
            ka, kb = owner[ids[a]], owner[ids[int(b)]]
            if ka != kb:
                adj[ka].add(kb)
                adj[kb].add(ka)
    order = sorted(range(m), key=lambda k: -len(adj[k]))
    col = {}
    for k in order:
        used = {col[j] for j in adj[k] if j in col}
        c = next((c for c in range(len(PALETTE)) if c not in used), len(col) % len(PALETTE))
        col[k] = c
    return [PALETTE[col[k]] for k in range(m)]


def label(ax, x, y, s, **kw):
    """Direct label in ink colour with a thin surface halo."""
    import matplotlib.patheffects as pe
    kw.setdefault("fontsize", 6.5)
    kw.setdefault("color", INK2)
    t = ax.text(x, y, s, **kw)
    t.set_path_effects([pe.withStroke(linewidth=2.2, foreground=SURFACE)])
    return t


# ---------------------------------------------------------------- layout helpers (no text on data)
def legend_below(ax, handles=None, ncol=3, dy=-0.30, **kw):
    """Legend centred below the axes, outside the data area."""
    kw.setdefault("fontsize", 6.2)
    if handles is None:
        handles, labels = ax.get_legend_handles_labels()
        return ax.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, dy), ncol=ncol,
                         handlelength=1.4, columnspacing=1.0, borderaxespad=0.0, **kw)
    return ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, dy), ncol=ncol,
                     handlelength=1.4, columnspacing=1.0, borderaxespad=0.0, **kw)


def legend_top(fig, handles, ncol=4, y=1.0, **kw):
    """One figure-level legend above all panels."""
    kw.setdefault("fontsize", 6.6)
    return fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, y), ncol=ncol, frameon=False,
                      handlelength=1.6, columnspacing=1.4, **kw)


def free_spot(points, candidates):
    """Pick the candidate position farthest from all data points (for leader-line labels)."""
    P = np.asarray(points, float)
    best, bd = None, -1.0
    for c in candidates:
        d = np.min(np.hypot(P[:, 0] - c[0], P[:, 1] - c[1]))
        if d > bd:
            best, bd = c, d
    return best


def callout(ax, xy, xytext, s, **kw):
    """Label placed in empty space and connected to its target by a hairline."""
    kw.setdefault("fontsize", 6.0)
    kw.setdefault("color", INK)
    return ax.annotate(s, xy=xy, xytext=xytext, ha=kw.pop("ha", "center"), va=kw.pop("va", "center"),
                       arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.5, shrinkA=1, shrinkB=2), **kw)
