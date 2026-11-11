"""E5 -- Bosphorus penalty sweep: how the crossing penalty P reshapes the routes.

Same coordinates and demands as the team instance (and the real Istanbul instance),
only P changes. TS and MA, 5 seeds, 20 s each.
"""
import copy

from common import IST, PARAMS, RAW, ROOT, TEAM, run_jobs
from medidrone.vrpio import read_instance, write_instance

P_SYN = [0, 10, 25, 50, 75, 100, 150, 200, 300, 500, 1000]
P_IST = [0, 0.5, 1, 2, 3, 5, 8, 12, 20, 50]


def make_variants():
    out = {}
    for base, Ps, tag in [(TEAM, P_SYN, "syn"), (IST, P_IST, "ist")]:
        inst = read_instance(base)
        for P in Ps:
            v = copy.copy(inst)
            v._D = None
            v.P = float(P)
            v.name = f"{inst.name}-P{P:g}"
            path = ROOT / "data/psweep" / f"{v.name}.vrp"
            path.parent.mkdir(parents=True, exist_ok=True)
            write_instance(path, v)
            out[(tag, P)] = path
    return out


def jobs():
    J = []
    for (tag, P), path in make_variants().items():
        for alg in ("ts", "ma"):
            for s in range(1, 6):
                J.append((RAW / "psweep" / f"{path.stem}_{alg}_s{s}.json",
                          ["solve", "--inst", path, "--alg", alg, "--time", 20, "--seed", s, *PARAMS[alg]]))
    return J


if __name__ == "__main__":
    run_jobs(jobs(), label="psweep")
