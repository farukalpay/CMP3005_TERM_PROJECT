"""E1 (Task 7 main comparison), E2 (tiny instances vs exact optimum), E8 (TS oscillation log).

E1: 6 instances x {GA, TS, MA} x 10 seeds, equal wall-clock budgets (30 s for n <= 50,
    60 s otherwise), best-so-far snapshots stored for search-trajectory networks; CW once.
E2: 9 tiny instances x {GA, TS, MA} x 10 seeds, 1 s each.
E8: TS on A-n80-k10 and MediDrone-7273 logging (distance, overload, lambda) every 2 iterations.
"""
import sys

from common import MAIN_INSTANCES, PARAMS, RAW, ROOT, SEEDS, TEAM, run_jobs


def jobs():
    J = []
    for nm, (path, T) in MAIN_INSTANCES.items():
        J.append((RAW / "main" / f"{nm}_cw_s0.json", ["solve", "--inst", path, "--alg", "cw", "--seed", 0]))
        for alg in ("ga", "ts", "ma"):
            for s in SEEDS:
                J.append((RAW / "main" / f"{nm}_{alg}_s{s}.json",
                          ["solve", "--inst", path, "--alg", alg, "--time", T, "--seed", s, "--snaps", 1, *PARAMS[alg]]))
    for path in sorted((ROOT / "data/tiny").glob("*.vrp")):
        J.append((RAW / "tiny" / f"{path.stem}_cw_s0.json", ["solve", "--inst", path, "--alg", "cw", "--seed", 0]))
        for alg in ("ga", "ts", "ma"):
            for s in SEEDS:
                J.append((RAW / "tiny" / f"{path.stem}_{alg}_s{s}.json",
                          ["solve", "--inst", path, "--alg", alg, "--time", 1, "--seed", s, *PARAMS[alg]]))
    for nm, path in [("A-n80-k10", ROOT / "data/cvrplib/A/A-n80-k10.vrp"), ("MediDrone-7273", TEAM)]:
        J.append((RAW / "osc" / f"{nm}_ts_s1.json",
                  ["solve", "--inst", path, "--alg", "ts", "--time", 10, "--seed", 1, "--osc", 2, *PARAMS["ts"]]))
    return J


if __name__ == "__main__":
    run_jobs(jobs(), label="main")
