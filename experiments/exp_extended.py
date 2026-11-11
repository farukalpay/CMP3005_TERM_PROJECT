"""E6 -- extended benchmark on all Augerat A, B and P instances (74 real benchmark
instances, CVRPLIB mirror on HuggingFace) for the statistical comparison (Wilcoxon
signed-rank over instances) and the instance-feature analysis. 5 seeds x 10 s."""
from common import PARAMS, RAW, ROOT, run_jobs


def jobs():
    J = []
    for S in ("A", "B", "P"):
        for path in sorted((ROOT / "data/cvrplib" / S).glob("*.vrp")):
            for alg in ("ga", "ts", "ma"):
                for s in range(1, 6):
                    J.append((RAW / "extended" / f"{path.stem}_{alg}_s{s}.json",
                              ["solve", "--inst", path, "--alg", alg, "--time", 10, "--seed", s, *PARAMS[alg]]))
            J.append((RAW / "extended" / f"{path.stem}_cw_s0.json", ["solve", "--inst", path, "--alg", "cw", "--seed", 0]))
    return J


if __name__ == "__main__":
    run_jobs(jobs(), label="extended")
