"""E7 -- scalability on Uchoa et al. (2017) X instances, n = 100 .. 1000 (unlimited fleet,
as in the X-set convention). 3 seeds x 60 s."""
from common import PARAMS, RAW, ROOT, run_jobs

X = ["X-n101-k25", "X-n148-k46", "X-n200-k36", "X-n251-k28", "X-n303-k21", "X-n401-k29", "X-n502-k39",
     "X-n599-k92", "X-n701-k44", "X-n801-k40", "X-n1001-k43"]


def jobs():
    J = []
    for nm in X:
        path = ROOT / "data/cvrplib/X" / f"{nm}.vrp"
        for alg in ("ga", "ts", "ma"):
            for s in range(1, 4):
                J.append((RAW / "xset" / f"{nm}_{alg}_s{s}.json",
                          ["solve", "--inst", path, "--alg", alg, "--time", 60, "--seed", s, "--fleet", 0, *PARAMS[alg]]))
        J.append((RAW / "xset" / f"{nm}_cw_s0.json", ["solve", "--inst", path, "--alg", "cw", "--seed", 0, "--fleet", 0]))
    return J


if __name__ == "__main__":
    run_jobs(jobs(), label="xset")
