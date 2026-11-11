// savings.cpp -- Clarke-Wright parallel savings. Own implementation.
#include "savings.hpp"

#include <algorithm>
#include <tuple>

RouteList clarke_wright(const Instance& I) {
    const int n = I.n;
    // Doubly linked list of customers per route; 0 marks a route end.
    std::vector<int> nxt(n + 1, 0), prv(n + 1, 0), rid(n + 1), head(n + 1), tail(n + 1), load(n + 1);
    std::vector<std::vector<int>> members(n + 1);
    for (int i = 1; i <= n; ++i) {
        rid[i] = i; head[i] = tail[i] = i; load[i] = I.q[i]; members[i] = {i};
    }
    // 1) all savings s(i,j) = d(0,i) + d(0,j) - d(i,j)      -- O(n^2)
    std::vector<std::tuple<double, int, int>> S;
    S.reserve((size_t)n * (n - 1) / 2);
    for (int i = 1; i <= n; ++i)
        for (int j = i + 1; j <= n; ++j) {
            double s = I.d(0, i) + I.d(0, j) - I.d(i, j);
            if (s > 0) S.emplace_back(s, i, j);
        }
    // 2) sort by decreasing saving (ties: lexicographic, deterministic) -- O(n^2 log n)
    std::sort(S.begin(), S.end(), [](const auto& a, const auto& b) {
        if (std::get<0>(a) != std::get<0>(b)) return std::get<0>(a) > std::get<0>(b);
        return std::make_pair(std::get<1>(a), std::get<2>(a)) < std::make_pair(std::get<1>(b), std::get<2>(b));
    });
    auto reverse_route = [&](int r) {  // O(route length)
        for (int v : members[r]) std::swap(nxt[v], prv[v]);
        std::swap(head[r], tail[r]);
    };
    // 3) greedy merging                                      -- O(n^2) scan + O(n^2) worst-case merges
    for (auto& [s, i, j] : S) {
        int ri = rid[i], rj = rid[j];
        if (ri == rj || load[ri] + load[rj] > I.Q) continue;
        bool iEnd = (head[ri] == i || tail[ri] == i), jEnd = (head[rj] == j || tail[rj] == j);
        if (!iEnd || !jEnd) continue;            // i and j must both be adjacent to the depot
        if (tail[ri] != i) reverse_route(ri);   // now i is the tail of ri
        if (head[rj] != j) reverse_route(rj);   // now j is the head of rj
        // link ri -> rj ; relabel the smaller route (small-to-large)
        nxt[i] = j; prv[j] = i;
        int keep = ri, gone = rj;
        if (members[ri].size() < members[rj].size()) std::swap(keep, gone);
        int newHead = head[ri], newTail = tail[rj];
        for (int v : members[gone]) { rid[v] = keep; members[keep].push_back(v); }
        members[gone].clear();
        head[keep] = newHead; tail[keep] = newTail; load[keep] = load[ri] + load[rj];
    }
    RouteList R;
    for (int r = 1; r <= n; ++r) {
        if (members[r].empty()) continue;
        std::vector<int> route;
        for (int v = head[r]; v != 0; v = nxt[v]) route.push_back(v);
        R.push_back(route);
    }
    return R;
}
