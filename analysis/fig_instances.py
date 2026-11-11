"""Figure: the two MediDrone instances (synthetic team instance and real Istanbul geography).
Layout rule: no text on top of data -- side names sit outside the axes, the depot label is a
call-out placed in the emptiest region, water labels only on empty water."""
from __future__ import annotations

import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Polygon, Rectangle

from data import ROOT
from medidrone import style
from medidrone.vrpio import read_instance

style.apply()


def draw_districts(ax, lw=0.35):
    gj = json.loads((ROOT / "data/istanbul/istanbul_districts.geojson").read_text())
    for f in gj["features"]:
        g = f["geometry"]
        polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        col = style.LAND_EU if f["properties"]["side"] == "Europe" else style.LAND_AS
        for poly in polys:
            ax.add_patch(Polygon(np.array(poly[0]), closed=True, facecolor=col, edgecolor="#d4d2ca", lw=lw, zorder=1))


def istanbul_axes(ax, extent=(28.62, 29.40, 40.86, 41.24)):
    ax.set_facecolor(style.WATER)
    ax.set_xlim(extent[0], extent[1]); ax.set_ylim(extent[2], extent[3])
    ax.set_aspect(1 / np.cos(np.radians(41.03)))
    ax.set_xticks([]); ax.set_yticks([]); ax.grid(False)
    for sp in ax.spines.values():
        sp.set_visible(True); sp.set_color(style.AXIS); sp.set_linewidth(0.5)


def scale_bar(ax, lon, lat, km=5):
    dlon = km / (111.32 * np.cos(np.radians(lat)))
    ax.plot([lon, lon + dlon], [lat, lat], color=style.INK, lw=1.2, solid_capstyle="butt", zorder=6)
    ax.text(lon + dlon / 2, lat + 0.006, f"{km} km", ha="center", va="bottom", fontsize=6, color=style.INK, zorder=6)


def synthetic_axes(ax, P=None, side_labels=True):
    """Square with Europe/Asia tints and the strait; side names go below the axes."""
    ax.add_patch(Rectangle((-30, -30), 530, 1060, facecolor=style.LAND_EU, lw=0, zorder=0))
    ax.add_patch(Rectangle((500, -30), 530, 1060, facecolor=style.LAND_AS, lw=0, zorder=0))
    ax.add_patch(Rectangle((493, -30), 14, 1060, facecolor=style.WATER, lw=0, zorder=0.5))
    ax.set_xlim(-25, 1025); ax.set_ylim(-25, 1025); ax.set_aspect("equal")
    ax.grid(False)
    ax.set_yticks([])
    if side_labels:
        ax.set_xticks([250, 500, 750])
        ax.set_xticklabels(["EUROPE", "strait", "ASIA"], fontsize=6.2)
        ax.tick_params(axis="x", length=0, pad=3)
        for t, c in zip(ax.get_xticklabels(), [style.MUTED, "#2a5d93", style.MUTED]):
            t.set_color(c)
    else:
        ax.set_xticks([])


def main():
    inst = read_instance(ROOT / "data/medidrone/MediDrone-7273.vrp")
    ist = read_instance(ROOT / "data/istanbul/MediDrone-IST-7273.vrp")
    nodes = pd.read_csv(ROOT / "data/istanbul/MediDrone-IST-7273_nodes.csv")
    elig = pd.read_csv(ROOT / "data/istanbul/eligible_facilities.csv")

    fig = plt.figure(figsize=(style.TEXTWIDTH, 2.7))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.0, 1.55], wspace=0.12)
    # ---------------- (a) synthetic
    ax = fig.add_subplot(gs[0])
    synthetic_axes(ax)
    xy, q = inst.xy, inst.q
    ax.scatter(xy[1:, 0], xy[1:, 1], s=4 + q[1:] * 0.9, facecolor=style.INK2, edgecolor=style.SURFACE, lw=0.4,
               alpha=0.9, zorder=3)
    ax.scatter([500], [500], marker="s", s=34, color=style.INK, zorder=5)
    cands = [(x, y) for x in np.linspace(560, 940, 9) for y in np.linspace(300, 480, 5)]
    spot = style.free_spot(xy[1:], cands)
    style.callout(ax, (500, 500), spot, "central lab\n(500, 500):\nAsian side", fontsize=5.8, zorder=7)
    ax.set_title("(a) Team instance (seed 7273)")
    ax.set_xlabel(f"P = {inst.P:g} per crossing", fontsize=6.2, color=style.INK2, labelpad=2)

    # ---------------- (b) real Istanbul
    ax = fig.add_subplot(gs[1])
    istanbul_axes(ax)
    draw_districts(ax)
    ax.scatter(elig.lon, elig.lat, s=1.2, color=style.MUTED, alpha=0.55, lw=0, zorder=2)
    cl = nodes.iloc[1:]
    ax.scatter(cl.lon, cl.lat, s=4 + cl.demand * 0.9, facecolor=style.INK2, edgecolor=style.SURFACE, lw=0.4, zorder=3)
    d0 = nodes.iloc[0]
    ax.scatter([d0.lon], [d0.lat], marker="s", s=34, color=style.INK, zorder=5)
    style.callout(ax, (d0.lon, d0.lat), (28.86, 40.925), "central lab: Kasımpaşa (Beyoğlu)", fontsize=5.8, zorder=7)
    ax.text(28.80, 40.885, "Sea of Marmara", fontsize=6, color="#2a5d93", style="italic", ha="center", zorder=4)
    scale_bar(ax, 29.27, 40.875)
    ax.set_title("(b) Real Istanbul (OpenStreetMap)")
    nE = int((ist.side[1:] == 0).sum())
    ax.set_xlabel(f"Europe: {nE} clinics      Asia: {ist.n - nE} clinics      P = {ist.P:g} km per crossing",
                  fontsize=6.2, color=style.INK2, labelpad=3)
    style.save(fig, "instances")


if __name__ == "__main__":
    main()
