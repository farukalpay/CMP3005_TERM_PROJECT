"""LaTeX tables + statistics: main comparison, tiny instances, significance tests,
extended benchmark summary.  Writes report/tables/*.tex and results/summary.json."""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from data import RAW, ROOT, references, with_gap
from medidrone.exact import dp_optimum, milp_optimum
from medidrone.vrpio import read_instance

TAB = ROOT / "report/tables"
TAB.mkdir(parents=True, exist_ok=True)
ALGS = ["ga", "ma", "ts"]
NAMES = {"ga": "GA", "ma": "MA", "ts": "TS", "cw": "CW"}
MAIN = ["A-n32-k5", "A-n45-k6", "A-n60-k9", "A-n80-k10", "MediDrone-7273", "MediDrone-IST-7273"]
BKS = {"A-n32-k5": 784, "A-n45-k6": 944, "A-n60-k9": 1354, "A-n80-k10": 1763}


def load(folder):
    rows = []
    for p in sorted((RAW / folder).glob("*.json")):
        r = json.loads(p.read_text())
        for k in ("snaps", "osc", "div", "move_hist", "trace", "routes"):
            r.pop(k, None)
        rows.append(r)
    return pd.DataFrame(rows)


def fmt(x, d=1):
    return f"{x:,.{d}f}".replace(",", "\\,")


def main_table(summary):
    df = load("main")
    refs = references()
    lines = [r"\begin{tabular}{@{}l r r l r r r r r r@{}}", r"\toprule",
             r"Instance & $n$ & $K$ & Alg. & Best & Mean & Std & Gap$_{\text{best}}$ & Gap$_{\text{mean}}$ & $t_{\text{best}}$ [s] \\",
             r"\midrule"]
    out = {}
    for name in MAIN:
        sub = df[df.instance == name]
        if sub.empty:
            continue
        ref = BKS.get(name, refs.get(name))
        n, K = int(sub.n.iloc[0]), int(sub.K.iloc[0])
        first = True
        for alg in ["cw", *ALGS]:
            s = sub[sub.alg == alg]
            if s.empty:
                continue
            c = s.cost.to_numpy(float)
            gb, gm = 100 * (c.min() - ref) / ref, 100 * (c.mean() - ref) / ref
            hits = int((c <= ref + 1e-6).sum())
            label = f"\\textbf{{{name}}}" if first else ""
            meta = f"{n} & {K}" if first else "&"
            extra = ""
            if alg == "cw":
                cw_routes = int(s.num_routes.iloc[0])
                extra = f" ({cw_routes} rt.)" if cw_routes > K else ""
                lines.append(f"{label} & {meta} & CW & {fmt(c[0])}{extra} & -- & -- & {gb:.2f} & -- & $<$0.01 \\\\")
            else:
                tb = s.time_to_best.mean()
                best_mark = "\\textbf{" if gm == min(
                    100 * (sub[sub.alg == a].cost.mean() - ref) / ref for a in ALGS if not sub[sub.alg == a].empty) else "{"
                lines.append(f"{label} & {meta} & {NAMES[alg]} & {fmt(c.min())} & {fmt(c.mean())} & {fmt(c.std(ddof=1), 2)}"
                             f" & {gb:.2f} & {best_mark}{gm:.2f}}} & {tb:.2f} \\\\")
            first = False
            out[(name, alg)] = dict(best=float(c.min()), mean=float(c.mean()), std=float(c.std(ddof=1)) if len(c) > 1 else 0.0,
                                    gap_best=gb, gap_mean=gm, hits=hits, runs=len(c),
                                    ttb=float(s.time_to_best.mean()), routes=int(s.num_routes.min()),
                                    crossing_routes=int(s.crossing_routes.min()) if "crossing_routes" in s else 0,
                                    ref=float(ref))
        lines.append(r"\addlinespace[2pt]")
    lines[-1] = r"\bottomrule"
    lines.append(r"\end{tabular}")
    (TAB / "main.tex").write_text("\n".join(lines) + "\n")
    summary["main"] = {f"{k[0]}|{k[1]}": v for k, v in out.items()}
    # compact version for the slides: mean gap (%) and runs at the best known value
    S = [r"\begin{tabular}{@{}l r r r r@{}}", r"\toprule",
         r"mean gap (\%) \quad [runs at best] & CW & \textcolor{gaC}{GA} & \textcolor{maC}{MA} & \textcolor{tsC}{TS} \\",
         r"\midrule"]
    for name in MAIN:
        if (name, "ts") not in out:
            continue
        cells = [f"{out[(name, 'cw')]['gap_best']:.2f}"]
        best_gap = min(out[(name, a)]["gap_mean"] for a in ALGS)
        for a in ALGS:
            o = out[(name, a)]
            txt = f"{o['gap_mean']:.2f} [{o['hits']}]"
            cells.append(f"\\textbf{{{txt}}}" if o["gap_mean"] == best_gap else txt)
        S.append(f"{name} & " + " & ".join(cells) + r" \\")
    S += [r"\bottomrule", r"\end{tabular}"]
    (TAB / "slides_main.tex").write_text("\n".join(S) + "\n")
    # significance per instance: Mann-Whitney U (two-sided), 10 vs 10 runs
    sig = []
    for name in MAIN:
        sub = df[df.instance == name]
        row = {"instance": name}
        for a, b in (("ts", "ga"), ("ts", "ma")):
            x, y = sub[sub.alg == a].cost.to_numpy(), sub[sub.alg == b].cost.to_numpy()
            if len(x) and len(y):
                if np.allclose(np.r_[x, y], x[0]):
                    p = 1.0
                else:
                    p = stats.mannwhitneyu(x, y, alternative="two-sided").pvalue
                # Vargha-Delaney A12: P(TS better than other)
                A = (np.sum(x[:, None] < y[None, :]) + 0.5 * np.sum(x[:, None] == y[None, :])) / (len(x) * len(y))
                row[f"{a}_{b}_p"] = float(p)
                row[f"{a}_{b}_A"] = float(A)
        sig.append(row)
    summary["mannwhitney"] = sig


def tiny_table(summary):
    df = load("tiny")
    rows = []
    for path in sorted((ROOT / "data/tiny").glob("*.vrp")):
        inst = read_instance(path)
        opt, R = dp_optimum(inst.D, inst.q, inst.Q, inst.K)
        opt2, _ = milp_optimum(inst.D, inst.q, inst.Q, inst.K)
        sub = df[df.instance == inst.name]
        row = dict(name=inst.name, n=inst.n, K=inst.K, Q=inst.Q, opt=opt, milp=opt2, routes=len(R))
        cw = sub[sub.alg == "cw"]
        row["cw"] = float(cw.cost.iloc[0]) if len(cw) else np.nan
        row["cw_routes"] = int(cw.num_routes.iloc[0]) if len(cw) else 0
        for alg in ALGS:
            s = sub[sub.alg == alg]
            row[f"{alg}_hits"] = int((np.abs(s.cost - opt) <= 1e-6 * opt).sum())
            row[f"{alg}_runs"] = len(s)
            row[f"{alg}_ttb"] = float(s.time_to_best.median()) if len(s) else np.nan
        rows.append(row)
    L = [r"\begin{tabular}{@{}l r r r r r r r r@{}}", r"\toprule",
         r"Instance & $n$ & $K$ & optimum (DP = MILP) & opt.\ routes & CW gap & GA & MA & TS \\", r"\midrule"]
    for r in rows:
        cwg = 100 * (r["cw"] - r["opt"]) / r["opt"]
        cwg = 0.0 if abs(cwg) < 5e-3 else cwg
        cwtxt = f"{cwg:.2f}\\,\\%" + ("$^\\dagger$" if r["cw_routes"] > r["K"] else "")
        L.append(f"{r['name']} & {r['n']} & {r['K']} & {r['opt']:.2f} & {r['routes']} & {cwtxt} & "
                 f"{r['ga_hits']}/{r['ga_runs']} & {r['ma_hits']}/{r['ma_runs']} & {r['ts_hits']}/{r['ts_runs']} \\\\")
    L += [r"\bottomrule", r"\end{tabular}"]
    (TAB / "tiny.tex").write_text("\n".join(L) + "\n")
    summary["tiny"] = rows


def extended(summary):
    df = load("extended")
    if df.empty:
        return
    df["cost"] = pd.to_numeric(df["cost"], errors="coerce")       # None = no fleet-feasible solution found
    df = with_gap(df)
    df["set"] = df.instance.str[0]
    sto = df[df.alg.isin(ALGS)]
    # an algorithm "fails" on an instance if none of its runs found a fleet-feasible solution
    piv = sto.groupby(["instance", "alg"]).gap.mean().unstack()
    fails = sto.groupby(["instance", "alg"]).cost.apply(lambda c: c.isna().all()).unstack()
    best = sto.groupby(["instance", "alg"]).cost.min().unstack()
    ref = df.groupby("instance").ref.first()
    out = {"n_instances": int(len(piv)),
           "failures": {a: sorted(fails.index[fails[a]].tolist()) for a in ALGS},
           "infeasible_runs": {a: int(sto[sto.alg == a].cost.isna().sum()) for a in ALGS},
           "below_bks": sorted({i for i in best.index for a in ALGS if best.loc[i, a] < ref[i] - 1e-6})}
    for a, b in (("ts", "ga"), ("ts", "ma"), ("ma", "ga")):
        both = piv[[a, b]].dropna()                                  # instances where both found solutions
        d = both[a] - both[b]
        w = stats.wilcoxon(both[a], both[b], zero_method="wilcox") if (np.abs(d) > 1e-12).any() else None
        out[f"{a}_vs_{b}"] = dict(p=float(w.pvalue) if w else 1.0, stat=float(w.statistic) if w else 0.0, n=int(len(both)),
                                  wins=int((d < -1e-9).sum()), losses=int((d > 1e-9).sum()),
                                  ties=int((np.abs(d) <= 1e-9).sum()), median_diff=float(d.median()))
    by = []
    for S in ("A", "B", "P"):
        sub = piv[piv.index.str.startswith(S)]
        bsub = best[best.index.str.startswith(S)]
        rsub = ref[ref.index.str.startswith(S)]
        row = {"set": S, "count": int(len(sub))}
        for a in ALGS:
            row[f"{a}_gap"] = float(sub[a].mean())                    # NaN (failed) instances excluded
            row[f"{a}_bks"] = int((bsub[a] <= rsub + 1e-6).sum())
            row[f"{a}_fail"] = int(sub[a].isna().sum())
        by.append(row)
    cw = df[df.alg == "cw"]
    cw_over = int((cw.num_routes > cw.K).sum())
    out["by_set"] = by
    out["cw_mean_gap"] = float(cw.gap.mean())
    out["cw_fleet_violations"] = cw_over
    L = [r"\begin{tabular}{@{}l r r r r r r r@{}}", r"\toprule",
         r"Set & inst. & \multicolumn{3}{c}{mean gap (\%)} & \multicolumn{3}{c}{BKS reached (instances)} \\",
         r"\cmidrule(lr){3-5}\cmidrule(l){6-8}", r" & & GA & MA & TS & GA & MA & TS \\", r"\midrule"]
    for r in by:
        dag = lambda a: "$^\\ddagger$" if r[f"{a}_fail"] else ""
        L.append(f"Augerat {r['set']} & {r['count']} & {r['ga_gap']:.2f}{dag('ga')} & {r['ma_gap']:.3f}{dag('ma')} & "
                 f"{r['ts_gap']:.3f} & {r['ga_bks']} & {r['ma_bks']} & {r['ts_bks']} \\\\")
    L += [r"\bottomrule", r"\end{tabular}"]
    (TAB / "extended.tex").write_text("\n".join(L) + "\n")
    summary["extended"] = out
    piv.to_csv(ROOT / "results/extended_mean_gaps.csv")
    def pfmt(p):
        return f"{p:.1e}".replace("e-0", "\\cdot10^{-").replace("e-", "\\cdot10^{-") + "}" if p < 1e-3 else f"{p:.3f}"
    (TAB / "slides_wilcoxon.tex").write_text(
        f"Wilcoxon signed-rank over {out['n_instances']} instances: TS vs GA $p={pfmt(out['ts_vs_ga']['p'])}$ "
        f"\\textperiodcentered{{}} TS vs MA $p={pfmt(out['ts_vs_ma']['p'])}$\n")


def xset(summary):
    df = load("xset")
    if df.empty:
        return
    df = with_gap(df)
    g = df.groupby(["instance", "alg"]).gap.agg(["mean", "min", "max"]).reset_index()
    summary["xset"] = g.to_dict(orient="records")
    piv = df.groupby(["instance", "alg"]).gap.mean().unstack()
    nn = df.groupby("instance").n.first()
    order = nn.sort_values().index
    L = [r"\begin{tabular}{@{}l r r r r r@{}}", r"\toprule", r"Instance & $n$ & CW & GA & MA & TS \\", r"\midrule"]
    for inst in order:
        vals = [piv.loc[inst].get(a, np.nan) for a in ("cw", "ga", "ma", "ts")]
        best = min(v for v in vals[1:] if not np.isnan(v))
        cells = [f"{v:.2f}" if not np.isnan(v) else "--" for v in vals]
        cells = [f"\\textbf{{{c}}}" if (i > 0 and abs(vals[i] - best) < 1e-12) else c for i, c in enumerate(cells)]
        L.append(f"{inst} & {int(nn[inst])} & " + " & ".join(cells) + r" \\")
    L += [r"\bottomrule", r"\end{tabular}"]
    (TAB / "xset.tex").write_text("\n".join(L) + "\n")


def export_csv():
    """One row per run of every experiment (raw results, Task 7 deliverable)."""
    frames = []
    for folder in ("tune_ts", "tune_ga", "tune_ma", "main", "tiny", "osc", "psweep", "extended", "xset", "long",
                   "ablation"):
        df = load(folder)
        if df.empty:
            continue
        df.insert(0, "experiment", folder)
        frames.append(df)
    allr = pd.concat(frames, ignore_index=True)
    keep = ["experiment", "instance", "n", "K", "Q", "P", "alg", "seed", "time_limit", "cost", "recomputed_cost",
            "feasible", "num_routes", "crossing_routes", "crossings", "time_to_best", "total_time", "iterations",
            "evaluations", "restarts", "path"]
    allr["params"] = allr["params"].apply(lambda d: json.dumps(d, sort_keys=True))
    allr[keep + ["params"]].to_csv(ROOT / "results/all_runs.csv", index=False)
    return len(allr)


def main():
    summary = {}
    summary["n_runs"] = export_csv()
    main_table(summary)
    tiny_table(summary)
    extended(summary)
    xset(summary)
    from experiments_hw import hw
    summary["hardware"] = hw()
    (ROOT / "results/summary.json").write_text(json.dumps(summary, indent=1, default=float))
    print(json.dumps({k: v for k, v in summary.items() if k in ("mannwhitney", "extended")}, indent=1, default=float)[:3000])


if __name__ == "__main__":
    main()
