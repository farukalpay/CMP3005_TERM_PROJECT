// localsearch.cpp -- see localsearch.hpp. Own implementation.
#include "localsearch.hpp"

#include <numeric>

int local_search(Routes& S, int kn, Rng& rng) {
    const int n = S.I->n, Q = S.I->Q;
    std::vector<int> order(n);
    std::iota(order.begin(), order.end(), 1);
    rng.shuffle(order);
    int applied = 0;
    bool improved = true;
    while (improved) {
        improved = false;
        for (int u : order) {
            int empty = S.empty_slot();
            Move best;
            bool found = false;
            for_each_move(S, u, kn, empty, [&](const Move& m) {
                if (m.dDist < -1e-7 && (m.k1 == m.k2 || (m.L1 <= Q && m.L2 <= Q))) {
                    best = m;
                    found = true;
                    return true;  // first improvement
                }
                return false;
            });
            if (found) {
                S.apply(best);
                ++applied;
                improved = true;
            }
        }
    }
    return applied;
}
