// ga.cpp -- see ga.hpp. Own implementation (operators from Goldberg 1989,
// Davis 1985 (OX), Prins 2004 (giant tour + Split, clone rejection, replacement
// in the worse half)).
#include "ga.hpp"

#include <algorithm>
#include <limits>
#include <numeric>
#include <unordered_set>

#include "common.hpp"
#include "localsearch.hpp"
#include "routes.hpp"
#include "split.hpp"

namespace {
struct Indiv {
    std::vector<int> tour;
    RouteList R;
    double cost = std::numeric_limits<double>::infinity();
    int excess = 0;   // routes above the fleet limit K (0 = feasible)
    uint64_t h = 0;   // hash of the decoded edge set (clone detection)
};
inline bool better(const Indiv& a, const Indiv& b) {
    return a.excess < b.excess || (a.excess == b.excess && a.cost < b.cost - EPS);
}

void adjacency(const RouteList& R, int n, std::vector<int>& pr, std::vector<int>& su) {
    pr.assign(n + 1, -1);
    su.assign(n + 1, -1);
    for (auto& r : R) {
        int prev = 0;
        for (int v : r) { pr[v] = prev; if (prev) su[prev] = v; prev = v; }
        if (prev) su[prev] = 0;
    }
}
}  // namespace

double broken_pairs(const RouteList& A, const RouteList& B, int n) {
    std::vector<int> pa, sa, pb, sb;
    adjacency(A, n, pa, sa);
    adjacency(B, n, pb, sb);
    int broken = 0;
    for (int i = 1; i <= n; ++i) {
        int s = sa[i];
        if (!(s == sb[i] || s == pb[i])) ++broken;
    }
    return (double)broken / n;
}

RunResult genetic_algorithm(const Instance& I, const GAParams& p, uint64_t seed, const RouteList& cw) {
    Timer timer;
    Rng rng(seed);
    RunResult res;
    const int n = I.n, K = I.K;
    const int restart_gens = p.restart_gens > 0 ? p.restart_gens : (p.pls > 0 ? 40 : 400);

    // ---- decoding: Split (optimal for the given order) + optional local search
    auto decode = [&](Indiv& c, bool allowLS) {
        int mr = split_min_routes(I, c.tour);
        SplitResult s = p.bellman ? split_bellman(I, c.tour) : split_linear(I, c.tour);
        c.excess = 0;
        if (s.routes > K) {
            if (mr <= K) s = split_limited(I, c.tour, K);
            else c.excess = mr - K;
        }
        c.cost = s.cost;
        c.R = std::move(s.R);
        if (allowLS && p.pls > 0 && rng.coin(p.pls)) {
            Routes S;
            S.init(I, c.R, std::max<int>(K, (int)c.R.size()));
            local_search(S, p.nbr, rng);
            c.tour.clear();
            for (auto& r : S.r) c.tour.insert(c.tour.end(), r.begin(), r.end());
            mr = split_min_routes(I, c.tour);
            SplitResult s2 = split_linear(I, c.tour);
            c.excess = 0;
            if (s2.routes > K) {
                if (mr <= K) s2 = split_limited(I, c.tour, K);
                else c.excess = mr - K;
            }
            c.cost = s2.cost;
            c.R = std::move(s2.R);
        }
        c.h = solution_hash(c.R) ^ ((uint64_t)c.excess * 0x9E3779B97F4A7C15ULL);
        ++res.evaluations;
    };
    auto random_tour = [&]() {
        std::vector<int> t(n);
        std::iota(t.begin(), t.end(), 1);
        rng.shuffle(t);
        return t;
    };

    // ---- initial population: CW giant tour + random permutations, no clones
    std::vector<Indiv> pop;
    std::unordered_set<uint64_t> hashes;
    auto record_best = [&](const Indiv& c, long long gen) {
        if (c.excess > 0) return;
        if (c.cost < res.cost - EPS) {
            res.cost = c.cost;
            res.best = c.R;
            res.feasible = true;
            res.time_to_best = timer.elapsed();
            res.trace.push_back({res.time_to_best, (double)gen, res.cost});
            if (p.snaps) res.snaps.push_back({res.time_to_best, gen, res.cost, res.best});
        }
    };
    if (p.seed_cw) {
        Indiv c;
        for (auto& r : cw) c.tour.insert(c.tour.end(), r.begin(), r.end());
        decode(c, true);
        hashes.insert(c.h);
        record_best(c, 0);
        pop.push_back(std::move(c));
    }
    int attempts = 0;
    while ((int)pop.size() < p.pop && attempts < 50 * p.pop) {
        ++attempts;
        Indiv c;
        c.tour = random_tour();
        decode(c, true);
        if (hashes.count(c.h)) continue;
        hashes.insert(c.h);
        record_best(c, 0);
        pop.push_back(std::move(c));
    }
    auto sort_pop = [&]() { std::sort(pop.begin(), pop.end(), [](const Indiv& a, const Indiv& b) { return better(a, b); }); };
    sort_pop();
    const int mu = (int)pop.size();

    auto tournament = [&]() -> const Indiv& {
        const Indiv& a = pop[rng.uniform_int(0, mu - 1)];
        const Indiv& b = pop[rng.uniform_int(0, mu - 1)];
        return better(a, b) ? a : b;
    };
    std::vector<char> used(n + 1);
    auto ox = [&](const std::vector<int>& p1, const std::vector<int>& p2) {  // Order Crossover, O(n)
        std::vector<int> ch(n);
        int i = rng.uniform_int(0, n - 1), j = rng.uniform_int(0, n - 1);
        if (i > j) std::swap(i, j);
        std::fill(used.begin(), used.end(), 0);
        for (int k = i; k <= j; ++k) { ch[k] = p1[k]; used[p1[k]] = 1; }
        int pos = (j + 1) % n;
        for (int k = 0; k < n; ++k) {
            int g = p2[(j + 1 + k) % n];
            if (!used[g]) { ch[pos] = g; pos = (pos + 1) % n; }
        }
        return ch;
    };
    auto mutate = [&](std::vector<int>& t) {  // O(n)
        int type = p.mut == 3 ? rng.uniform_int(0, 2) : p.mut;
        int i = rng.uniform_int(0, n - 1), j = rng.uniform_int(0, n - 1);
        if (type == 0) std::swap(t[i], t[j]);
        else if (type == 1) { if (i > j) std::swap(i, j); std::reverse(t.begin() + i, t.begin() + j + 1); }
        else { int g = t[i]; t.erase(t.begin() + i); t.insert(t.begin() + j, g); }
    };
    auto diversity = [&]() {
        double s = 0; int cnt = 0;
        if (mu <= 60) {
            for (int a = 0; a < mu; ++a)
                for (int b = a + 1; b < mu; ++b) { s += broken_pairs(pop[a].R, pop[b].R, n); ++cnt; }
        } else {
            for (int k = 0; k < 2000; ++k) {
                int a = rng.uniform_int(0, mu - 1), b = rng.uniform_int(0, mu - 1);
                if (a == b) continue;
                s += broken_pairs(pop[a].R, pop[b].R, n); ++cnt;
            }
        }
        return cnt ? s / cnt : 0.0;
    };

    long long gen = 0, last_improve = 0;
    double last_best = res.cost;
    bool stop = false;
    long long clones = 0;
    while (!stop) {
        if (p.max_gens >= 0 && gen >= p.max_gens) break;
        // ---- one generation = mu offspring (steady state)
        for (int c = 0; c < mu; ++c) {
            if (p.max_gens < 0 && timer.elapsed() >= p.time_limit) { stop = true; break; }
            const Indiv& P1 = tournament();
            const Indiv& P2 = tournament();
            Indiv ch;
            ch.tour = rng.coin(p.pc) ? ox(P1.tour, P2.tour) : P1.tour;
            if (rng.coin(p.pm)) mutate(ch.tour);
            decode(ch, true);
            if (hashes.count(ch.h)) { ++clones; continue; }  // clone rejection
            record_best(ch, gen);
            // replace a random individual of the worse half (the best half is never touched)
            int victim = rng.uniform_int(mu / 2, mu - 1);
            hashes.erase(pop[victim].h);
            hashes.insert(ch.h);
            pop[victim] = std::move(ch);
            // restore the sorted order by bubbling the newcomer: O(mu)
            int k = victim;
            while (k > 0 && better(pop[k], pop[k - 1])) { std::swap(pop[k], pop[k - 1]); --k; }
            while (k + 1 < mu && better(pop[k + 1], pop[k])) { std::swap(pop[k], pop[k + 1]); ++k; }
        }
        if (stop) break;
        ++gen;
        if (res.cost < last_best - EPS) { last_best = res.cost; last_improve = gen; }
        if (p.div_every > 0 && gen % p.div_every == 0) {
            double mean = 0; int cnt = 0;
            for (auto& x : pop) if (x.excess == 0) { mean += x.cost; ++cnt; }
            res.div.push_back({gen, timer.elapsed(), res.cost, cnt ? mean / cnt : -1.0, diversity()});
        }
        // ---- partial restart when the search stagnates (diversification)
        if (gen - last_improve > restart_gens) {
            ++res.restarts;
            int keep = std::max(1, (int)(p.keep_frac * mu));
            for (int k = keep; k < mu; ++k) hashes.erase(pop[k].h);
            for (int k = keep; k < mu; ++k) {
                for (int tries = 0; tries < 20; ++tries) {
                    pop[k].tour = random_tour();
                    decode(pop[k], true);
                    if (!hashes.count(pop[k].h)) break;
                }
                hashes.insert(pop[k].h);
                record_best(pop[k], gen);
            }
            sort_pop();
            last_improve = gen;
        }
    }
    res.iterations = gen;
    res.total_time = timer.elapsed();
    res.extra = "\"clones_rejected\":" + std::to_string(clones);
    return res;
}
