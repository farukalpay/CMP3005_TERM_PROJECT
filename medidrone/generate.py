"""Team-specific MediDrone instance and tiny ground-truth instances (Task 2b, 2c).

Rules (project description, Task 2b):
  * depot at the centre (500, 500) of a 1000 x 1000 square;
  * European side x < 500, Asian side x >= 500  (so the depot is on the Asian side);
  * n = 100 customers: 4-6 Gaussian clusters spread over both sides + ~20 % uniform;
  * demands uniform in [1, 30], Q = 100, K = ceil(sum q / Q) + 1;
  * d(i, j) = Euclidean + P * [side(i) != side(j)],  P = 150  (no rounding).

The seed is the sum of the last four digits of all team members' student IDs.
Own implementation (numpy PCG64 generator => bit-for-bit reproducible).
"""
from __future__ import annotations

import argparse
import math

import numpy as np

from . import ROOT
from .vrpio import Instance, write_instance

STUDENT_IDS = ["2267273"]          # add team-mates' IDs here (or pass --ids)
TINY_Q = 50                        # tiny instances: Q = 50 so that capacity binds (2-4 routes)


def team_seed(ids) -> int:
    """Sum of the numbers formed by the last four digits of every student ID."""
    return sum(int(str(s)[-4:]) for s in ids)


def make_instance(seed: int, n: int = 100, n_clusters: int | None = None, P: float = 150.0,
                  Q: int = 100, name: str | None = None, uniform_frac: float = 0.2) -> Instance:
    rng = np.random.default_rng(seed)
    if n_clusters is None:
        n_clusters = int(rng.integers(4, 7))                  # 4, 5 or 6 clusters
    n_uni = int(round(uniform_frac * n))
    n_clu = n - n_uni
    # cluster centres: alternate sides so both sides get clusters, then random
    sides = np.array([k % 2 for k in range(n_clusters)])
    rng.shuffle(sides)
    cx = np.where(sides == 0, rng.uniform(70, 430, n_clusters), rng.uniform(570, 930, n_clusters))
    cy = rng.uniform(70, 930, n_clusters)
    sigma = rng.uniform(30, 70, n_clusters)
    sizes = rng.multinomial(n_clu, np.full(n_clusters, 1.0 / n_clusters))
    pts = []
    for k in range(n_clusters):
        p = rng.normal([cx[k], cy[k]], sigma[k], size=(sizes[k], 2))
        pts.append(np.clip(p, 0, 1000))
    pts.append(rng.uniform(0, 1000, size=(n_uni, 2)))
    pts = np.vstack(pts)
    pts = pts[rng.permutation(n)]
    pts = np.round(pts, 4)                                    # file precision
    xy = np.vstack([[500.0, 500.0], pts])
    q = np.concatenate([[0], rng.integers(1, 31, size=n)])   # [1, 30]
    K = math.ceil(q.sum() / Q) + 1
    side = (xy[:, 0] >= 500).astype(int)                      # 0 = Europe, 1 = Asia
    inst = Instance(name=name or f"MediDrone-s{seed}-n{n}", n=n, Q=Q, K=K, xy=xy, q=q,
                    rounded=False, P=P, side=side,
                    comment=f"MediDrone Istanbul synthetic instance, seed {seed}, {n_clusters} clusters")
    inst.meta = dict(seed=seed, n_clusters=n_clusters, centres=np.c_[cx, cy].tolist(),
                     sigma=sigma.tolist(), sizes=sizes.tolist())
    return inst


def tiny_seeds(seed: int):
    """Seeds of the tiny ground-truth instances: (n, idx) -> seed*100 + 10*n + idx."""
    return {(n, i): seed * 100 + 10 * n + i for n in (7, 8, 9) for i in range(3)}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ids", nargs="*", default=STUDENT_IDS)
    ap.add_argument("--out", default=str(ROOT / "data"))
    a = ap.parse_args()
    seed = team_seed(a.ids)
    print("student IDs:", a.ids, "-> seed =", " + ".join(str(s)[-4:] for s in a.ids), "=", seed)
    inst = make_instance(seed, n=100, name=f"MediDrone-{seed}")
    write_instance(f"{a.out}/medidrone/MediDrone-{seed}.vrp", inst)
    print(f"team instance: n={inst.n} clusters={inst.meta['n_clusters']} sum q={inst.q.sum()} K={inst.K}"
          f"  Europe={int((inst.side[1:] == 0).sum())} Asia={int((inst.side[1:] == 1).sum())}")
    for (n, i), s in tiny_seeds(seed).items():
        t = make_instance(s, n=n, n_clusters=2, Q=TINY_Q, name=f"tiny-n{n}-{i}")
        write_instance(f"{a.out}/tiny/tiny-n{n}-{i}.vrp", t)
    print("tiny instances written:", len(tiny_seeds(seed)))


if __name__ == "__main__":
    main()
