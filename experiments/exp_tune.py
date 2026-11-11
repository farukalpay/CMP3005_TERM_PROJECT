"""E4 -- parameter tuning / sensitivity (Task 4, 5 and the parameter study of Task 7).

TS  : tenure range x granularity k                  on MediDrone-7273 and A-n80-k10
GA  : mutation rate x population size (pure GA)     on MediDrone-7273 (+ diversity log)
MA  : local-search probability                      on MediDrone-7273
Tuning seeds (101-105) are disjoint from the evaluation seeds (1-10).
"""
from common import RAW, ROOT, TEAM, TUNE_SEEDS, run_jobs

T = 10  # seconds per tuning run

TENURES = [(1, 3), (3, 8), (5, 15), (10, 25), (20, 40), (40, 80), (80, 160)]
NBRS = [5, 10, 20, 40]
PMS = [0.0, 0.05, 0.1, 0.3, 0.6, 1.0]
POPS = [20, 50, 100, 200]


def jobs():
    J = []
    inst = {"MediDrone-7273": TEAM, "A-n80-k10": ROOT / "data/cvrplib/A/A-n80-k10.vrp"}
    for nm, path in inst.items():
        for (a, b) in TENURES:
            for k in (NBRS if nm == "MediDrone-7273" else [20]):
                for s in TUNE_SEEDS:
                    out = RAW / "tune_ts" / f"{nm}_t{a}-{b}_k{k}_s{s}.json"
                    J.append((out, ["solve", "--inst", path, "--alg", "ts", "--time", T, "--seed", s,
                                    "--tmin", a, "--tmax", b, "--nbr", k]))
    for pm in PMS:
        for pop in POPS:
            for s in TUNE_SEEDS:
                out = RAW / "tune_ga" / f"MediDrone-7273_pm{pm}_pop{pop}_s{s}.json"
                J.append((out, ["solve", "--inst", TEAM, "--alg", "ga", "--time", T, "--seed", s,
                                "--pm", pm, "--pop", pop, "--div", 50]))
    for pls in [0.0, 0.1, 0.25, 0.5, 1.0]:
        for s in TUNE_SEEDS:
            out = RAW / "tune_ma" / f"MediDrone-7273_pls{pls}_s{s}.json"
            J.append((out, ["solve", "--inst", TEAM, "--alg", "ma", "--time", T, "--seed", s, "--pls", pls]))
    return J


if __name__ == "__main__":
    run_jobs(jobs(), label="tune")
