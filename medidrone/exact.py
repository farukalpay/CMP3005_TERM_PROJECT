"""Exact optimum of tiny CVRP instances (Task 2c) by two independent methods.

1. dp_optimum   : Held-Karp DP for the TSP cost of every capacity-feasible subset,
                  then a set-partitioning DP over subsets with at most K routes.
                  O(2^n n^2 + K 3^n) time -- trivial for n <= 9 (and fine up to ~14).
2. milp_optimum : two-index vehicle-flow MILP with MTZ load variables, solved by
                  HiGHS through scipy.optimize.milp (an ILP solver is allowed for the
                  tiny instances by Section 7 of the project description).
Own implementation.
"""
from __future__ import annotations

import itertools
import math

import numpy as np


def dp_optimum(D: np.ndarray, q: np.ndarray, Q: int, K: int):
    n = len(q) - 1
    full = (1 << n) - 1
    INF = math.inf
    # Held-Karp: C[S][j] = shortest path depot -> (all of S) -> j, j in S
    C = [dict() for _ in range(1 << n)]
    par = [dict() for _ in range(1 << n)]
    load = [0] * (1 << n)
    for S in range(1, 1 << n):
        low = (S & -S).bit_length() - 1
        load[S] = load[S & (S - 1)] + q[low + 1]
    for j in range(n):
        C[1 << j][j] = D[0, j + 1]
    for S in range(1, 1 << n):
        if load[S] > Q or bin(S).count("1") < 2:
            continue
        for j in range(n):
            if not S >> j & 1:
                continue
            R = S ^ (1 << j)
            best, arg = INF, -1
            for i, c in C[R].items():
                v = c + D[i + 1, j + 1]
                if v < best:
                    best, arg = v, i
            if arg >= 0:
                C[S][j] = best
                par[S][j] = arg
    route = [INF] * (1 << n)
    last = [-1] * (1 << n)
    for S in range(1, 1 << n):
        if load[S] <= Q:
            for j, c in C[S].items():
                v = c + D[j + 1, 0]
                if v < route[S]:
                    route[S], last[S] = v, j
    # set partitioning with at most K routes: F[k][T]
    F = [[INF] * (1 << n) for _ in range(K + 1)]
    choice = [[0] * (1 << n) for _ in range(K + 1)]
    F[0][0] = 0.0
    for k in range(1, K + 1):
        Fk, Fp = F[k], F[k - 1]
        Fk[0] = 0.0
        for T in range(1, 1 << n):
            low = T & -T
            rest = T ^ low
            best, arg = Fp[T] if Fp[T] < INF else INF, 0   # using fewer routes is allowed
            S = rest
            while True:                                    # S' = low | subset of rest
                Sp = S | low
                if route[Sp] < INF and Fp[T ^ Sp] < INF:
                    v = route[Sp] + Fp[T ^ Sp]
                    if v < best - 1e-12:
                        best, arg = v, Sp
                if S == 0:
                    break
                S = (S - 1) & rest
            Fk[T], choice[k][T] = best, arg
    opt = F[K][full]
    # reconstruct routes
    routes, T, k = [], full, K
    while T and k > 0:
        Sp = choice[k][T]
        if Sp == 0:          # optimum used fewer routes
            k -= 1
            continue
        j, S, seq = last[Sp], Sp, []
        while S:
            seq.append(j + 1)
            pj = par[S].get(j, -1)
            S ^= 1 << j
            j = pj
        routes.append(seq[::-1])
        T ^= Sp
        k -= 1
    return opt, routes


def milp_optimum(D: np.ndarray, q: np.ndarray, Q: int, K: int, time_limit: float = 60.0):
    from scipy.optimize import Bounds, LinearConstraint, milp
    from scipy.sparse import lil_matrix

    n = len(q) - 1
    V = n + 1
    arcs = [(i, j) for i in range(V) for j in range(V) if i != j]
    A = len(arcs)
    idx = {a: k for k, a in enumerate(arcs)}
    nv = A + n                       # x_ij binaries, then u_1..u_n
    c = np.concatenate([[D[i, j] for i, j in arcs], np.zeros(n)])
    rows, lo, hi = [], [], []
    M = lil_matrix((2 * n + 2 + n * (n - 1), nv))
    r = 0
    for i in range(1, V):            # out-degree 1
        for j in range(V):
            if j != i:
                M[r, idx[(i, j)]] = 1
        lo.append(1); hi.append(1); r += 1
    for j in range(1, V):            # in-degree 1
        for i in range(V):
            if i != j:
                M[r, idx[(i, j)]] = 1
        lo.append(1); hi.append(1); r += 1
    for j in range(1, V):            # at most K vehicles leave the depot
        M[r, idx[(0, j)]] = 1
    lo.append(0); hi.append(K); r += 1
    for j in range(1, V):            # flow balance at the depot
        M[r, idx[(0, j)]] = 1
        M[r, idx[(j, 0)]] = -1
    lo.append(0); hi.append(0); r += 1
    for i in range(1, V):            # MTZ load: u_i - u_j + Q x_ij <= Q - q_j
        for j in range(1, V):
            if i != j:
                M[r, A + i - 1] = 1
                M[r, A + j - 1] = -1
                M[r, idx[(i, j)]] = Q
                lo.append(-np.inf); hi.append(Q - q[j]); r += 1
    integrality = np.concatenate([np.ones(A), np.zeros(n)])
    bounds = Bounds(np.concatenate([np.zeros(A), q[1:]]), np.concatenate([np.ones(A), np.full(n, Q)]))
    res = milp(c, constraints=LinearConstraint(M.tocsr(), lo, hi), integrality=integrality,
               bounds=bounds, options=dict(time_limit=time_limit, mip_rel_gap=0))
    if not res.success:
        return math.inf, []
    x = res.x[:A] > 0.5
    succ = {i: j for (i, j), on in zip(arcs, x) if on}
    starts = [j for (i, j), on in zip(arcs, x) if on and i == 0]
    routes = []
    for s in starts:
        seq, v = [], s
        while v != 0:
            seq.append(v)
            v = succ[v]
        routes.append(seq)
    return float(res.fun), routes


def brute_force_check(D, q, Q, K):
    """Exhaustive enumeration (permutations + optimal split) for n <= 8: a third witness."""
    n = len(q) - 1
    best = math.inf
    for perm in itertools.permutations(range(1, n + 1)):
        # optimal split of this order with at most K routes (DP)
        V = [[math.inf] * (n + 1) for _ in range(K + 1)]
        V[0][0] = 0
        for k in range(1, K + 1):
            for i in range(n):
                if V[k - 1][i] == math.inf:
                    continue
                load, cost = 0, 0.0
                for j in range(i + 1, n + 1):
                    c = perm[j - 1]
                    load += q[c]
                    if load > Q:
                        break
                    cost = D[0, c] + D[c, 0] if j == i + 1 else cost - D[perm[j - 2], 0] + D[perm[j - 2], c] + D[c, 0]
                    V[k][j] = min(V[k][j], V[k - 1][i] + cost)
        best = min(best, min(V[k][n] for k in range(K + 1)))
    return best
