// split.cpp -- see split.hpp. Own implementation.
//
// Notation (1-based positions in the giant tour t_1..t_n):
//   SD[j] = sum_{k<j} d(t_k, t_{k+1})       (distance along the tour, SD[1] = 0)
//   SQ[j] = q(t_1) + ... + q(t_j)            (prefix demand, SQ[0] = 0)
//   arc (i -> j), 0 <= i < j <= n, is the route t_{i+1} .. t_j, feasible iff
//   SQ[j] - SQ[i] <= Q, with cost c(i,j) = d(0,t_{i+1}) + SD[j] - SD[i+1] + d(t_j,0).
//   V[j] = min_i V[i] + c(i,j)  (shortest path 0 -> n in the DAG).
#include "split.hpp"

#include <deque>
#include <limits>

namespace {
const double INF = std::numeric_limits<double>::infinity();

struct Prefix {
    std::vector<double> SD;
    std::vector<int> SQ;
    Prefix(const Instance& I, const std::vector<int>& t) {
        int n = (int)t.size();
        SD.assign(n + 2, 0.0);
        SQ.assign(n + 1, 0);
        for (int j = 1; j <= n; ++j) {
            SQ[j] = SQ[j - 1] + I.q[t[j - 1]];
            if (j >= 2) SD[j] = SD[j - 1] + I.d(t[j - 2], t[j - 1]);
        }
        SD[n + 1] = SD[n];
    }
};

SplitResult build(const std::vector<int>& t, const std::vector<int>& pred, double cost) {
    SplitResult res;
    res.cost = cost;
    if (cost == INF) return res;
    int j = (int)t.size();
    while (j > 0) {
        int i = pred[j];
        res.R.emplace_back(t.begin() + i, t.begin() + j);
        j = i;
    }
    std::reverse(res.R.begin(), res.R.end());
    res.routes = (int)res.R.size();
    return res;
}
}  // namespace

SplitResult split_bellman(const Instance& I, const std::vector<int>& t) {
    const int n = (int)t.size();
    std::vector<double> V(n + 1, INF);
    std::vector<int> pred(n + 1, -1);
    V[0] = 0.0;
    for (int i = 0; i < n; ++i) {          // tail node of the arcs
        if (V[i] == INF) continue;
        int load = 0;
        double cost = 0.0;
        for (int j = i + 1; j <= n; ++j) { // route t_{i+1} .. t_j
            int c = t[j - 1];
            load += I.q[c];
            if (load > I.Q) break;         // at most L iterations
            if (j == i + 1) cost = I.d(0, c) + I.d(c, 0);
            else cost += I.d(t[j - 2], c) + I.d(c, 0) - I.d(t[j - 2], 0);
            if (V[i] + cost < V[j] - 1e-12) { V[j] = V[i] + cost; pred[j] = i; }
        }
    }
    return build(t, pred, V[n]);
}

SplitResult split_linear(const Instance& I, const std::vector<int>& t) {
    // V[j] = min_{i in window(j)} phi(i) + SD[j] + d(t_j, 0),
    // phi(i) = V[i] + d(0, t_{i+1}) - SD[i+1];  window(j) = { i : SQ[j]-SQ[i] <= Q }.
    // The window's left end is non-decreasing in j -> sliding-window minimum, O(n).
    const int n = (int)t.size();
    Prefix P(I, t);
    std::vector<double> V(n + 1, INF), phi(n + 1, INF);
    std::vector<int> pred(n + 1, -1);
    V[0] = 0.0;
    phi[0] = I.d(0, t[0]) - P.SD[1];
    std::vector<int> dq(n + 1);            // deque as array: indices with increasing phi
    int front = 0, back = 0;
    dq[back++] = 0;
    for (int j = 1; j <= n; ++j) {
        while (P.SQ[j] - P.SQ[dq[front]] > I.Q) ++front;  // drop infeasible predecessors
        int i = dq[front];
        V[j] = phi[i] + P.SD[j] + I.d(t[j - 1], 0);
        pred[j] = i;
        if (j < n) {
            phi[j] = V[j] + I.d(0, t[j]) - P.SD[j + 1];
            while (back > front && phi[dq[back - 1]] >= phi[j]) --back;  // dominance
            dq[back++] = j;
        }
    }
    return build(t, pred, V[n]);
}

SplitResult split_limited(const Instance& I, const std::vector<int>& t, int K) {
    // Layered DAG: V_k[j] = min_i V_{k-1}[i] + c(i,j); answer min_k V_k[n].
    const int n = (int)t.size();
    Prefix P(I, t);
    std::vector<double> prev(n + 1, INF), cur(n + 1, INF);
    std::vector<std::vector<int>> pred(K + 1, std::vector<int>(n + 1, -1));
    prev[0] = 0.0;
    double best = INF;
    int bestK = -1;
    std::vector<int> dq(n + 1);
    for (int k = 1; k <= K; ++k) {
        std::fill(cur.begin(), cur.end(), INF);
        int front = 0, back = 0;
        auto phi = [&](int i) { return prev[i] + I.d(0, t[i]) - P.SD[i + 1]; };
        if (prev[0] < INF) dq[back++] = 0;
        for (int j = 1; j <= n; ++j) {
            while (back > front && P.SQ[j] - P.SQ[dq[front]] > I.Q) ++front;
            if (back > front) {
                int i = dq[front];
                cur[j] = phi(i) + P.SD[j] + I.d(t[j - 1], 0);
                pred[k][j] = i;
            }
            if (j < n && prev[j] < INF) {
                double pj = phi(j);
                while (back > front && phi(dq[back - 1]) >= pj) --back;
                dq[back++] = j;
            }
        }
        if (cur[n] < best - 1e-12) { best = cur[n]; bestK = k; }
        std::swap(prev, cur);
    }
    SplitResult res;
    res.cost = best;
    if (bestK < 0) return res;
    int j = n;
    for (int k = bestK; k >= 1; --k) {
        int i = pred[k][j];
        res.R.emplace_back(t.begin() + i, t.begin() + j);
        j = i;
    }
    std::reverse(res.R.begin(), res.R.end());
    res.routes = (int)res.R.size();
    return res;
}

int split_min_routes(const Instance& I, const std::vector<int>& t) {
    int routes = 1, load = 0;
    for (int c : t) {
        if (load + I.q[c] > I.Q) { ++routes; load = 0; }
        load += I.q[c];
    }
    return t.empty() ? 0 : routes;
}
