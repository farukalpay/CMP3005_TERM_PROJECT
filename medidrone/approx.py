"""Iterated tour partitioning with a provable guarantee (bonus of Task 1).

  1. TSP tour by the double-tree heuristic (MST + preorder walk): alpha = 2 on metric
     instances (shortcutting is safe because d satisfies the triangle inequality);
  2. for every rotation of the tour, cut it optimally into capacity-feasible routes
     (the GA's Split DP, here the O(nL) Bellman version); keep the best rotation.
The best-rotation split is never worse than the unsplittable iterated tour
partitioning (UITP) of Altinkemer & Gavish (1987), which cuts the same tour into
consecutive segments, so it inherits UITP's bound  cost <= (2 + (1 - 2/Q) alpha) OPT.
Own implementation.
"""
from __future__ import annotations

import numpy as np
from scipy.sparse.csgraph import depth_first_order, minimum_spanning_tree


def double_tree_tour(D: np.ndarray) -> list[int]:
    T = minimum_spanning_tree(D).toarray()
    T = np.maximum(T, T.T)
    order, _ = depth_first_order(T > 0, i_start=0, directed=False)
    return [int(v) for v in order]           # starts at the depot 0


def split_cost(D, q, Q, tour):
    n = len(tour)
    V = np.full(n + 1, np.inf)
    V[0] = 0.0
    pred = np.zeros(n + 1, dtype=int)
    for i in range(n):
        load, cost = 0, 0.0
        for j in range(i + 1, n + 1):
            c = tour[j - 1]
            load += q[c]
            if load > Q:
                break
            cost = D[0, c] + D[c, 0] if j == i + 1 else cost - D[tour[j - 2], 0] + D[tour[j - 2], c] + D[c, 0]
            if V[i] + cost < V[j]:
                V[j], pred[j] = V[i] + cost, i
    routes, j = [], n
    while j > 0:
        routes.append(tour[pred[j]:j])
        j = pred[j]
    return float(V[n]), routes[::-1]


def itp(D: np.ndarray, q: np.ndarray, Q: int):
    tour = [v for v in double_tree_tour(D) if v != 0]
    tsp_len = D[0, tour[0]] + sum(D[a, b] for a, b in zip(tour[:-1], tour[1:])) + D[tour[-1], 0]
    best = (np.inf, None)
    for r in range(len(tour)):
        t = tour[r:] + tour[:r]
        c, R = split_cost(D, q, Q, t)
        if c < best[0]:
            best = (c, R)
    radial = 2.0 / Q * float((q[1:] * D[0, 1:]).sum())   # lower bound on OPT
    return dict(cost=best[0], routes=best[1], tsp=float(tsp_len), radial_lb=radial)
