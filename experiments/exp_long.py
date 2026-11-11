"""Reference values for our own instances (no published BKS exists): long runs of TS
and MA (300 s, 4 seeds). The best value over ALL runs of all experiments is the
reference used for the gap of MediDrone-7273 and MediDrone-IST-7273."""
from common import IST, PARAMS, RAW, TEAM, run_jobs


def jobs():
    J = []
    for nm, path in [("MediDrone-7273", TEAM), ("MediDrone-IST-7273", IST)]:
        for alg in ("ts", "ma"):
            for s in range(201, 205):
                J.append((RAW / "long" / f"{nm}_{alg}_s{s}.json",
                          ["solve", "--inst", path, "--alg", alg, "--time", 300, "--seed", s, *PARAMS[alg]]))
    return J


if __name__ == "__main__":
    run_jobs(jobs(), label="long")
