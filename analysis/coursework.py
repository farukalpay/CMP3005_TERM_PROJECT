"""Build the course report's evidence from SAVED runs. Never calls a solver.

Run from any directory: python3 /path/to/project/analysis/coursework.py
Tiny exact values are read from the existing results/summary.json, not recomputed.
The research pipeline in make_all.py remains available separately.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from statistics import mean, stdev

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from medidrone.checker import check
from medidrone.vrpio import read_instance

OUT = ROOT / "results/coursework"
FIG = ROOT / "figures/coursework"
TEX = ROOT / "report/coursework"
NAMES = ["A-n32-k5", "A-n45-k6", "A-n60-k9", "A-n80-k10", "MediDrone-7273"]
COLORS = {"ga": "#2563a6", "ts": "#c45a28"}


def read(path):
    return json.loads(path.read_text())


def load_runs(folder):
    return [read(p) for p in sorted((ROOT / "results/raw" / folder).glob("*.json"))]


def write_csv(name, rows):
    with (OUT / f"{name}.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def save(fig, name):
    fig.savefig(FIG / f"{name}.pdf", bbox_inches="tight")
    fig.savefig(FIG / f"{name}.png", dpi=170, bbox_inches="tight")
    plt.close(fig)


def table(name, columns, header, rows):
    content = [r"\begin{tabular}{@{}" + columns + r"@{}}", r"\toprule",
               " & ".join(header) + r" \\", r"\midrule"]
    content += [" & ".join(map(str, r)) + r" \\" for r in rows]
    content += [r"\bottomrule", r"\end{tabular}", ""]
    (TEX / f"{name}.tex").write_text("\n".join(content))


def main():
    for p in (OUT, FIG, TEX):
        p.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "axes.grid": True, "grid.alpha": .18, "pdf.fonttype": 42})
    cached = read(ROOT / "results/summary.json")
    refs = {name: cached["main"][name + "|ts"]["ref"] for name in NAMES}
    runs = [r for r in load_runs("main") if r["instance"] in NAMES and r["alg"] in ("cw", "ga", "ts")]
    groups = {(name, alg): [r for r in runs if r["instance"] == name and r["alg"] == alg]
              for name in NAMES for alg in ("cw", "ga", "ts")}
    for (name, alg), group in groups.items():
        expected = {0} if alg == "cw" else set(range(1, 11))
        if len(group) != len(expected) or {r["seed"] for r in group} != expected:
            raise ValueError(f"Incomplete or duplicate saved seeds: {name}, {alg}")
        if alg != "cw" and any(not r["feasible"] for r in group):
            raise ValueError(f"Missing feasible core result: {name}, {alg}")
        # Recheck saved solutions using the independent Python evaluator.
        for r in group:
            inst = read_instance(ROOT / ("data/medidrone/" if name.startswith("MediDrone") else "data/cvrplib/A/") / f"{name}.vrp")
            ok, why, _ = check(inst, r["routes"], r["cost"])
            if bool(r["feasible"]) != ok:
                raise ValueError(f"Feasibility disagreement: {name}, {alg}: {why}")

    rows, texrows = [], []
    for name in NAMES:
        for alg in ("cw", "ga", "ts"):
            group = groups[name, alg]
            feasible = all(r["feasible"] for r in group)
            costs = [r["cost"] for r in group]
            row = dict(instance=name, algorithm=alg.upper(), runs=len(group),
                       fleet_feasible=feasible, reference=refs[name], best=min(costs),
                       mean=mean(costs), sample_std=stdev(costs) if len(costs) > 1 else 0,
                       mean_runtime_s=mean(r["total_time"] for r in group),
                       mean_time_to_best_s=mean(r["time_to_best"] for r in group),
                       mean_gap_pct=100 * (mean(costs) / refs[name] - 1) if feasible else "",
                       hits=sum(abs(r["cost"]-refs[name]) < 1e-4 for r in group) if feasible else 0)
            rows.append(row)
            texrows.append([name.replace("MediDrone-7273", "Team (7273)"), alg.upper(),
                            f"{row['best']:,.1f}", f"{row['mean']:,.1f}" if alg != "cw" else "--",
                            f"{row['sample_std']:.2f}" if alg != "cw" else "--",
                            f"{row['mean_runtime_s']:.2f}" if alg != "cw" else "$<0.01$",
                            f"{row['mean_gap_pct']:.2f}" if feasible else r"infeasible"])
    write_csv("main", rows)
    table("main_table", "llrrrrr", ["Instance", "Alg.", "Best", "Mean", "SD", "Time (s)", "Mean gap (\\%)"], texrows)
    tinyrows = []
    tiny = load_runs("tiny")
    for t in cached["tiny"]:
        row = dict(instance=t["name"], n=t["n"], exact=t["opt"], exact_milp=t["milp"])
        if not np.isclose(t["opt"], t["milp"], rtol=1e-8):
            raise ValueError("Cached exact methods disagree")
        for alg in ("ga", "ts"):
            group = [r for r in tiny if r["instance"] == t["name"] and r["alg"] == alg]
            if len(group) != 10 or {r["seed"] for r in group} != set(range(1, 11)):
                raise ValueError(f"Incomplete tiny runs: {t['name']}, {alg}")
            row[alg + "_hits"] = sum(r["feasible"] and abs(r["cost"]-t["opt"]) < 1e-4 for r in group)
        tinyrows.append(row)
    write_csv("tiny", tinyrows)
    table("tiny_table", "lrrcc", ["Instance", "$n$", "Exact cost", "GA hits", "TS hits"],
          [[r["instance"], r["n"], f"{r['exact']:.2f}", f"{r['ga_hits']}/10", f"{r['ts_hits']}/10"] for r in tinyrows])

    inst = read_instance(ROOT / "data/medidrone/MediDrone-7273.vrp")
    fig, ax = plt.subplots(figsize=(6.8, 3.5), layout="constrained")
    ax.axvspan(0, 500, color="#eef3f7"); ax.axvspan(500, 1000, color="#f7f2e9")
    ax.axvline(500, color="#679bbb", linestyle="--", label="Bosphorus boundary")
    sc = ax.scatter(*inst.xy[1:].T, c=inst.q[1:], cmap="viridis", s=20, zorder=3)
    ax.scatter(*inst.xy[0], marker="*", c="black", s=170, zorder=5, label="Laboratory")
    ax.set(xlim=(0,1000), ylim=(0,1000), xlabel="x coordinate", ylabel="y coordinate")
    ax.text(20, 945, "Europe"); ax.text(820, 945, "Asia")
    fig.colorbar(sc, ax=ax, label="Demand"); ax.legend(loc="lower right", fontsize=8)
    save(fig, "instance")

    best = min(groups["MediDrone-7273", "ts"], key=lambda r:r["cost"])
    fig, ax = plt.subplots(figsize=(6.8, 3.5), layout="constrained")
    for j, route in enumerate(best["routes"]):
        xy = inst.xy[[0,*route,0]]
        color = plt.get_cmap("tab20")(j % 20)
        ax.plot(*xy.T, color=color, lw=1.25)
        ax.scatter(*inst.xy[route].T, color=[color], s=14, zorder=3)
    ax.axvline(500, color="#679bbb", ls="--")
    ax.scatter(*inst.xy[0], marker="*", c="black", s=150, zorder=5)
    ax.set(xlim=(0,1000), ylim=(0,1000), xlabel="x coordinate", ylabel="y coordinate")
    save(fig, "routes")

    # Step interpolation preserves best-so-far behaviour. No linear interpolation.
    name = "A-n45-k6"
    grid = np.geomspace(.001, 30, 300)
    fig, ax = plt.subplots(figsize=(6.8, 2.8), layout="constrained")
    for alg in ("ga", "ts"):
        ys=[]
        for r in groups[name, alg]:
            trace=np.array(r["trace"])
            idx=np.searchsorted(trace[:,0], grid, side="right")-1
            y=np.full(len(grid), np.nan)
            y[idx>=0]=trace[idx[idx>=0],2]
            ys.append(y)
        ys=np.array(ys)
        # Start after every seed has its first feasible solution.
        complete=np.isfinite(ys).all(axis=0)
        y=ys[:,complete]
        ax.plot(grid[complete], np.median(y,axis=0), color=COLORS[alg], label=alg.upper())
        ax.fill_between(grid[complete], *np.percentile(y,[25,75],axis=0), color=COLORS[alg], alpha=.12)
    ax.axhline(944, color="gray", ls="--", lw=1, label="BKS = 944")
    ax.set(xscale="log", xlabel="Elapsed time (s, log scale)", ylabel="Best cost so far")
    ax.legend(fontsize=9); save(fig, "convergence")

    timings=read(ROOT / "results/raw/complexity/complexity.json")
    fig, axs=plt.subplots(1,2,figsize=(7.2,2.9),layout="constrained")
    slopes=[]
    for kind,label,col in [("ts","TS (20 candidates)",COLORS["ts"]),
                            ("ts_full","TS (all candidates)","#8e542f"),
                            ("ga","GA (population 50)",COLORS["ga"])]:
        rr=sorted([r for r in timings if r["kind"]==kind],key=lambda r:r["n"])
        x=np.array([r["n"] for r in rr]); y=np.array([r["time_per_iter"] for r in rr])
        fit=x<=1600 if kind=="ts" else np.ones(len(x),dtype=bool)
        slope=float(np.polyfit(np.log(x[fit]),np.log(y[fit]),1)[0])
        slopes.append(dict(series=kind,slope=slope,fit_min_n=int(x[fit].min()),fit_max_n=int(x[fit].max())))
        axs[0].loglog(x,y*1000,"o-",ms=3,color=col,label=f"{label} ({slope:.2f})")
    axs[0].set(xlabel="Customers n",ylabel="ms per iteration / generation")
    axs[0].legend(fontsize=7)
    ev=sorted([r for r in timings if r["kind"]=="eval"],key=lambda r:r["n"])
    for key,label,color in [("t_delta","Delta evaluation",COLORS["ts"]),("t_full","Full evaluation",COLORS["ga"])]:
        axs[1].loglog([r["n"] for r in ev],[r[key]/r["moves"]*1e9 for r in ev],"o-",ms=3,label=label,color=color)
    axs[1].set(xlabel="Customers n",ylabel="ns per candidate move"); axs[1].legend(fontsize=8)
    save(fig,"complexity"); write_csv("slopes",slopes)

    tuning=[r for r in load_runs("tune_ts") if r["instance"]=="MediDrone-7273" and r["params"]["nbr"]==20]
    settings=sorted({(r["params"]["tmin"],r["params"]["tmax"]) for r in tuning})
    sensitivity=[]
    for lo,hi in settings:
        rr=[r for r in tuning if (r["params"]["tmin"],r["params"]["tmax"])==(lo,hi)]
        if len(rr)!=5 or {r["seed"] for r in rr} != set(range(101,106)) or not all(r["feasible"] for r in rr):
            raise ValueError(f"Incomplete tenure study: {(lo, hi)}")
        sensitivity.append(dict(tenure_min=lo,tenure_max=hi,mean_gap_pct=100*(mean(r["cost"] for r in rr)/refs["MediDrone-7273"]-1)))
    write_csv("sensitivity",sensitivity)
    fig,axs=plt.subplots(1,2,figsize=(7.2,2.8),layout="constrained")
    axs[0].plot(range(len(settings)),[r["mean_gap_pct"] for r in sensitivity],"o-",color=COLORS["ts"])
    axs[0].set_xticks(range(len(settings)),[f"{lo}-{hi}" for lo,hi in settings],rotation=40,ha="right",fontsize=8)
    axs[0].set(xlabel="Tabu tenure range",ylabel="Mean gap (%)",title="Tenure study (k = 20)")
    sweep=read(ROOT / "results/psweep_stats.json")["syn"]
    pairs=sorted((float(p),r) for p,r in sweep.items())
    axs[1].plot([p for p,r in pairs],[r["cross"] for p,r in pairs],"o-",color=COLORS["ts"])
    axs[1].set(xlabel="Penalty P per crossing",ylabel="Routes crossing the boundary",title="Saved team-instance sweep",ylim=(0,12))
    save(fig,"sensitivity")

    write_csv("runs",[dict(instance=r["instance"],algorithm=r["alg"],seed=r["seed"],cost=r["cost"],
                           fleet_feasible=r["feasible"],runtime_s=r["total_time"],time_to_best_s=r["time_to_best"]) for r in runs])
    (OUT / "provenance.json").write_text(json.dumps(dict(
        method="Summaries and plots from saved evidence only; no solver or exact optimiser invoked",
        main="results/raw/main/*.json (five core instances; CW, GA, TS)",
        tiny="results/raw/tiny/*.json; exact values cached in results/summary.json",
        timing="results/raw/complexity/complexity.json",tuning="results/raw/tune_ts/*.json",
        crossing="results/psweep_stats.json (cached summary of results/raw/psweep)",
        route_plot=dict(algorithm="ts",seed=best["seed"],cost=best["cost"]),
        standard_deviation="sample, denominator runs-1",references=refs,
        original_hardware=cached.get("hardware",{})),indent=2)+"\n")
    print(f"Coursework assets built from {len(runs)} saved core runs and {len(tinyrows)} cached exact cases. No experiments run.")


if __name__ == "__main__":
    main()
