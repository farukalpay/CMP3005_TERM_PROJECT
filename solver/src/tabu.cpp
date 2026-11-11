// tabu.cpp -- see tabu.hpp. Own implementation.
//
// One iteration: evaluate every granular move (O(n k) moves, O(1) each),
// pick the best admissible one under f(s) = dist(s) + lambda * overload(s),
// apply it (O(L)), make the removed edges tabu, update lambda.
#include "tabu.hpp"

#include <algorithm>
#include <cmath>
#include <limits>
#include <numeric>

#include "common.hpp"
#include "routes.hpp"

RouteList reduce_routes(const Instance& I, RouteList R, int K) {
    R = compact(R);
    if ((int)R.size() <= K) return R;
    std::sort(R.begin(), R.end(), [&](auto& A, auto& B) { return route_load(I, A) > route_load(I, B); });
    std::vector<int> orphans;
    while ((int)R.size() > K) {
        for (int v : R.back()) orphans.push_back(v);
        R.pop_back();
    }
    double lam = 0.0;
    for (int i = 1; i <= I.n; ++i) lam += I.d(0, i);
    lam = 10.0 * lam / std::max(1, I.total_demand());
    for (int v : orphans) {  // cheapest insertion, penalised by overload
        double best = std::numeric_limits<double>::infinity();
        int bk = 0, bp = 0;
        for (int k = 0; k < (int)R.size(); ++k) {
            int L = route_load(I, R[k]);
            double pen = lam * (std::max(0, L + I.q[v] - I.Q) - std::max(0, L - I.Q));
            for (int p = 0; p <= (int)R[k].size(); ++p) {
                int a = p == 0 ? 0 : R[k][p - 1], b = p == (int)R[k].size() ? 0 : R[k][p];
                double c = I.d(a, v) + I.d(v, b) - I.d(a, b) + pen;
                if (c < best) { best = c; bk = k; bp = p; }
            }
        }
        R[bk].insert(R[bk].begin() + bp, v);
    }
    return R;
}

RunResult tabu_search(const Instance& I, const TSParams& p, uint64_t seed, const RouteList& init) {
    Timer timer;
    Rng rng(seed);
    RunResult res;
    const int n = I.n, N = n + 1;
    Routes S;
    S.init(I, reduce_routes(I, init, I.K), I.K);   // exactly K route slots: fleet limit always holds

    double lambda = p.lambda0;
    if (lambda <= 0) {  // auto: average depot distance per unit of demand
        double s = 0;
        for (int i = 1; i <= n; ++i) s += I.d(0, i);
        lambda = (s / n) / std::max(1.0, (double)I.total_demand() / n);
    }
    const long long restart_iters = p.restart_iters > 0 ? p.restart_iters : std::max(2000LL, 20LL * n);
    const int perturb = p.perturb >= 0 ? p.perturb : std::max(3, n / 15);
    std::vector<long long> tabu((size_t)N * N, 0);  // tabu[a*N+b] = iteration until which edge {a,b} is tabu
    auto tabu_idx = [N](int a, int b) { return a < b ? (size_t)a * N + b : (size_t)b * N + a; };

    auto record_best = [&](long long it) {
        res.best = S.routes();
        res.cost = S.dist;
        res.feasible = true;
        res.time_to_best = timer.elapsed();
        res.trace.push_back({res.time_to_best, (double)it, res.cost});
        if (p.snaps) res.snaps.push_back({res.time_to_best, it, res.cost, res.best});
    };
    if (S.over == 0) record_best(0);

    long long it = 0, last_improve = 0;
    while (true) {
        if (p.max_iters >= 0 && it >= p.max_iters) break;
        if (p.max_iters < 0 && timer.elapsed() >= p.time_limit) break;
        ++it;
        const int empty = S.empty_slot();
        Move best;
        bool have = false;
        double bestVal = std::numeric_limits<double>::infinity();
        int ties = 0;
        for (int u = 1; u <= n; ++u) {
            for_each_move(S, u, p.nbr, empty, [&](const Move& m) {
                ++res.evaluations;
                const int dO = S.dOver(m);
                const double val = m.dDist + lambda * dO;
                if (val > bestVal + EPS) return false;
                bool isTabu = false;
                for (int e = 0; e < m.nadd; ++e) {
                    auto [x, y] = m.add[e];
                    if ((x | y) != 0 && tabu[tabu_idx(x, y)] > it) { isTabu = true; break; }
                }
                if (isTabu) {  // aspiration: new overall best feasible solution
                    bool asp = (S.over + dO == 0) && (S.dist + m.dDist < res.cost - EPS);
                    if (!asp) return false;
                }
                if (val < bestVal - EPS) { bestVal = val; best = m; have = true; ties = 1; }
                else if (rng.uniform_int(1, ++ties) == 1) { best = m; }  // random tie-break
                return false;
            });
        }
        if (!have) {  // every move tabu: make a random relocation
            int u = rng.uniform_int(1, n), k = rng.uniform_int(0, (int)S.r.size() - 1);
            int ku = S.rid[u];
            S.r[ku].erase(S.r[ku].begin() + S.pos[u]);
            S.r[k].insert(S.r[k].begin() + rng.uniform_int(0, (int)S.r[k].size()), u);
            S.refresh(ku); if (k != ku) S.refresh(k);
            continue;
        }
        S.apply(best);
        res.move_count[best.type]++;
        for (int e = 0; e < best.nrem; ++e) {
            auto [x, y] = best.rem[e];
            if ((x | y) != 0) tabu[tabu_idx(x, y)] = it + rng.uniform_int(p.tmin, p.tmax);
        }
        // adaptive penalty (strategic oscillation around the feasibility border)
        if (S.over > 0) lambda = std::min(1e7, lambda * (1.0 + p.delta));
        else lambda = std::max(1e-4, lambda / (1.0 + p.delta));
        if (p.osc_every > 0 && it % p.osc_every == 0 && (int)res.osc.size() < p.osc_max)
            res.osc.push_back({it, S.dist, S.over, lambda});
        if (it % 1000 == 0)
            res.move_hist.push_back({it, res.move_count[0], res.move_count[1], res.move_count[2], res.move_count[3]});
        if (S.over == 0 && S.dist < res.cost - EPS) {
            record_best(it);
            last_improve = it;
        }
        if (it - last_improve > restart_iters && res.feasible) {  // diversification restart
            ++res.restarts;
            S.init(I, res.best, I.K);
            for (int r = 0; r < perturb; ++r) {
                int u = rng.uniform_int(1, n), k = rng.uniform_int(0, (int)S.r.size() - 1);
                int ku = S.rid[u];
                S.r[ku].erase(S.r[ku].begin() + S.pos[u]);
                S.r[k].insert(S.r[k].begin() + rng.uniform_int(0, (int)S.r[k].size()), u);
                S.refresh(ku); if (k != ku) S.refresh(k);
            }
            std::fill(tabu.begin(), tabu.end(), 0);
            last_improve = it;
        }
    }
    res.iterations = it;
    res.total_time = timer.elapsed();
    return res;
}
