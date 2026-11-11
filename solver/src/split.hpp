// split.hpp -- optimal segmentation of a giant tour into capacity-feasible
// routes (Beasley 1983; Prins 2004).  Three variants:
//
//  split_bellman      : DP over the DAG of feasible segments, O(n L) time
//                       (L = max customers per route), unlimited fleet.
//  split_linear       : same optimum in O(n) using a monotone deque
//                       (sliding-window minimum; cf. Vidal 2016), unlimited fleet.
//  split_limited      : at most K routes, layered DAG, O(K n) with the deque.
//
// Own implementation. The DAG and recurrences are documented in the report.
#pragma once
#include "solution.hpp"

struct SplitResult {
    double cost = 0;      // optimal cost (infinity if infeasible)
    int routes = 0;       // number of routes in the optimal segmentation
    RouteList R;          // the routes
};

// tour: permutation of customers 1..n (size n)
SplitResult split_bellman(const Instance& I, const std::vector<int>& tour);
SplitResult split_linear(const Instance& I, const std::vector<int>& tour);
SplitResult split_limited(const Instance& I, const std::vector<int>& tour, int K);
// Minimum number of routes for this tour order (next-fit), O(n).
int split_min_routes(const Instance& I, const std::vector<int>& tour);
