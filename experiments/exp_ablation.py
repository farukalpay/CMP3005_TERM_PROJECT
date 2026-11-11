"""E9 -- ablation: GA without the Clarke-Wright seed individual (random initial population).
Same instances, budgets and seeds as exp_main.py; only --seedcw 0 differs."""
from common import MAIN_INSTANCES, PARAMS, RAW, SEEDS, run_jobs


def jobs():
    J = []
    for nm, (path, T) in MAIN_INSTANCES.items():
        for s in SEEDS:
            J.append((RAW / "ablation" / f"{nm}_ga-noseed_s{s}.json",
                      ["solve", "--inst", path, "--alg", "ga", "--time", T, "--seed", s, "--seedcw", 0, *PARAMS["ga"]]))
    return J


if __name__ == "__main__":
    run_jobs(jobs(), label="ablation")
