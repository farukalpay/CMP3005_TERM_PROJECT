"""E3 -- empirical validation of the complexity analysis (Task 6).

Runs SEQUENTIALLY (one process) so that timings are not disturbed:
  (a) time per TS iteration (granular k=20 and full neighbourhood k=n-1) vs n,
  (b) time per GA generation (pure GA, linear and Bellman Split) and MA generation vs n,
  (c) cost per move: O(1) delta vs route-level vs full re-evaluation,
  (d) Split: Bellman O(nL) vs linear O(n) for growing route length L (n = 1000 fixed),
  (e) the same per-iteration measurements on the real X instances (overlay).
Synthetic scaling instances: uniform customers, demands U[1,30], Q = 155 (about 10
customers per route, so L stays constant while n grows).
"""
import json
import statistics
import subprocess

import numpy as np

from common import BIN, RAW, ROOT
from medidrone.vrpio import Instance, write_instance

NS = [25, 50, 100, 200, 400, 800, 1600, 3200]
QS = [50, 100, 200, 500, 1000, 2000, 5000, 15500]
XS = ["X-n101-k25", "X-n200-k36", "X-n303-k21", "X-n401-k29", "X-n502-k39", "X-n701-k44", "X-n801-k40",
      "X-n1001-k43"]
OUT = RAW / "complexity"
REPS = 3


def scaling_instance(n, Q=155, seed=11, tag="scale"):
    rng = np.random.default_rng(seed * 100003 + n)
    xy = np.vstack([[500.0, 500.0], rng.uniform(0, 1000, (n, 2))]).round(4)
    q = np.concatenate([[0], rng.integers(1, 31, n)])
    inst = Instance(name=f"{tag}-n{n}-Q{Q}", n=n, Q=Q, K=n, xy=xy, q=q, rounded=False)
    path = ROOT / "data/scaling" / f"{inst.name}.vrp"
    path.parent.mkdir(parents=True, exist_ok=True)
    write_instance(path, inst)
    return path


def call(args):
    r = subprocess.run([str(BIN), *map(str, args)], capture_output=True, text=True, check=True)
    return json.loads(r.stdout)


def median_of(args, key):
    vals, last = [], None
    for _ in range(REPS):
        last = call(args)
        vals.append(last[key])
    last[key] = statistics.median(vals)
    last["reps"] = vals
    return last


def tagged(kind, **res):
    res["kind"] = kind
    return res


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    paths = {n: scaling_instance(n) for n in NS}
    for n, p in paths.items():
        it_ts = int(np.clip(1.5 / (n * 20 * 9 * 2.5e-9), 50, 200000))
        rows.append(tagged(kind="ts", **median_of(["bench-iter", "--inst", p, "--alg", "ts", "--iters", it_ts,
                                                           "--nbr", 20], "time_per_iter")))
        if n <= 800:
            it_full = int(np.clip(1.5 / (n * n * 9 * 2.5e-9), 10, 100000))
            rows.append(tagged(kind="ts_full", **median_of(["bench-iter", "--inst", p, "--alg", "ts", "--iters",
                                                                      it_full, "--nbr", 0], "time_per_iter")))
        it_ga = int(np.clip(1.5 / (n * 50 * 30e-9), 20, 100000))
        rows.append(tagged(kind="ga", **median_of(["bench-iter", "--inst", p, "--alg", "ga", "--iters", it_ga],
                                                "time_per_iter")))
        rows.append(tagged(kind="ga_bellman", **median_of(["bench-iter", "--inst", p, "--alg", "ga", "--iters", it_ga,
                                                         "--bellman", 1], "time_per_iter")))
        if n <= 1600:
            it_ma = int(np.clip(2.0 / (n * n * 30 * 40e-9), 3, 2000))
            rows.append(tagged(kind="ma", **median_of(["bench-iter", "--inst", p, "--alg", "ma", "--iters", it_ma],
                                                    "time_per_iter")))
        ev = call(["bench-eval", "--inst", p, "--nbr", 20, "--reps", 5])
        rows.append(tagged(kind="eval", **ev))
        sp = call(["bench-split", "--inst", p, "--reps", 300])
        rows.append(tagged(kind="split_n", **sp))
        print("n =", n, "done", flush=True)
    for Q in QS:
        p = scaling_instance(1000, Q=Q, tag="splitQ")
        sp = call(["bench-split", "--inst", p, "--reps", 200])
        rows.append(tagged(kind="split_Q", **sp))
    print("split vs Q done", flush=True)
    for nm in XS:
        p = ROOT / "data/cvrplib/X" / f"{nm}.vrp"
        n = int(nm.split("-n")[1].split("-")[0]) - 1
        it_ts = int(np.clip(1.5 / (n * 20 * 9 * 2.5e-9), 50, 200000))
        rows.append(tagged(kind="x_ts", **median_of(["bench-iter", "--inst", p, "--alg", "ts", "--iters", it_ts,
                                                   "--nbr", 20, "--fleet", 0], "time_per_iter")))
        it_ga = int(np.clip(1.5 / (n * 50 * 30e-9), 20, 100000))
        rows.append(tagged(kind="x_ga", **median_of(["bench-iter", "--inst", p, "--alg", "ga", "--iters", it_ga,
                                                   "--fleet", 0], "time_per_iter")))
    (OUT / "complexity.json").write_text(json.dumps(rows, indent=1))
    print("wrote", OUT / "complexity.json")


if __name__ == "__main__":
    main()
