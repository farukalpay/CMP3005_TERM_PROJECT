// routes.hpp -- route-based solution with O(1) move evaluation, shared by
// Tabu Search and the memetic local search.  Own implementation.
//
// Neighbourhoods (all "granular": v is one of the k nearest neighbours of u,
// cf. Toth & Vigo 2003, so every move creates the short edge (u,v)):
//   RELOCATE  u is removed and re-inserted right after / right before v
//   SWAP      u and v (different routes) exchange their positions
//   2-OPT     intra-route segment reversal that creates edge (u,v)
//   2-OPT*    inter-route tail exchange (4 variants) that creates edge (u,v)
// Every evaluation is O(1): it touches a constant number of matrix entries and
// uses prefix loads for the capacity test.
#pragma once
#include <array>
#include <utility>

#include "solution.hpp"

enum MoveType : int { MV_RELOCATE = 0, MV_SWAP = 1, MV_2OPT = 2, MV_2OPTSTAR = 3, MV_COUNT = 4 };
inline const char* move_name(int t) {
    static const char* N[] = {"relocate", "swap", "2opt", "2optstar"};
    return N[t];
}

struct Move {
    int type = -1, variant = 0;
    int u = 0, v = 0;       // the two customers defining the move
    int k1 = -1, k2 = -1;   // routes involved (k1 = route of u)
    int c = 0;              // RELOCATE: u is inserted after node c of route k2 (0 = route start)
    double dDist = 0.0;     // change of total distance (O(1) delta evaluation)
    int L1 = 0, L2 = 0;     // new loads of k1 and k2 (k1 != k2)
    int nadd = 0, nrem = 0;
    std::array<std::pair<int, int>, 4> add{}, rem{};  // edges created / destroyed
};

struct Routes {
    const Instance* I = nullptr;
    std::vector<std::vector<int>> r;    // route slots (some may be empty)
    std::vector<int> rid, pos;          // route and position of every customer
    std::vector<std::vector<int>> pref; // pref[k][p] = load of r[k][0..p]
    std::vector<int> load;
    std::vector<double> cost;
    double dist = 0.0;                  // total distance
    int over = 0;                       // total overload  sum_k max(0, load_k - Q)

    void init(const Instance& inst, const RouteList& R, int slots) {
        I = &inst;
        int m = std::max<int>(slots, (int)R.size());
        r.assign(m, {});
        for (size_t k = 0; k < R.size(); ++k) r[k] = R[k];
        rid.assign(inst.n + 1, -1);
        pos.assign(inst.n + 1, -1);
        pref.assign(m, {});
        load.assign(m, 0);
        cost.assign(m, 0.0);
        dist = 0.0; over = 0;
        for (int k = 0; k < m; ++k) refresh(k);
    }
    // Recompute positions, prefix loads, load and cost of route k: O(|r_k|).
    void refresh(int k) {
        dist -= cost[k];
        over -= overQ(load[k]);
        auto& R = r[k];
        pref[k].resize(R.size());
        int l = 0;
        double c = 0.0;
        int prev = 0;
        for (size_t p = 0; p < R.size(); ++p) {
            int v = R[p];
            rid[v] = k; pos[v] = (int)p;
            l += I->q[v]; pref[k][p] = l;
            c += I->d(prev, v); prev = v;
        }
        if (!R.empty()) c += I->d(prev, 0);
        load[k] = l; cost[k] = c;
        dist += c;
        over += overQ(l);
    }
    inline int at(int k, int p) const { return (p < 0 || p >= (int)r[k].size()) ? 0 : r[k][p]; }
    inline int pred(int u) const { return at(rid[u], pos[u] - 1); }
    inline int succ(int u) const { return at(rid[u], pos[u] + 1); }
    inline int prefix(int k, int p) const { return p < 0 ? 0 : pref[k][p]; }
    inline int overQ(int L) const { return L > I->Q ? L - I->Q : 0; }
    int empty_slot() const {
        for (size_t k = 0; k < r.size(); ++k)
            if (r[k].empty()) return (int)k;
        return -1;
    }
    int used_routes() const {
        int c = 0;
        for (auto& R : r) c += !R.empty();
        return c;
    }
    RouteList routes() const { return compact(r); }
    // change of total overload produced by a move (O(1))
    inline int dOver(const Move& m) const {
        if (m.k1 == m.k2) return 0;
        return overQ(m.L1) + overQ(m.L2) - overQ(load[m.k1]) - overQ(load[m.k2]);
    }

    // Build the new customer sequences of the route(s) touched by m without
    // modifying the solution: A2 replaces route m.k1, B2 replaces m.k2 (if different).
    // O(L) where L is the length of the touched routes.
    void build(const Move& m, std::vector<int>& A2, std::vector<int>& B2) const {
        const int u = m.u, v = m.v, ku = rid[u], pu = pos[u];
        const auto& A = r[ku];
        if (m.type == MV_RELOCATE) {
            const int k2 = m.k2;
            A2 = A;
            A2.erase(A2.begin() + pu);
            auto& T = (k2 == ku) ? A2 : (B2 = r[k2]);
            int idx = 0;
            if (m.c != 0) idx = pos[m.c] + 1 - ((k2 == ku && pos[m.c] > pu) ? 1 : 0);
            T.insert(T.begin() + idx, u);
        } else if (m.type == MV_SWAP) {
            A2 = A; B2 = r[rid[v]];
            A2[pu] = v; B2[pos[v]] = u;
        } else if (m.type == MV_2OPT) {
            A2 = A;
            int ps = std::min(pu, pos[v]), pt = std::max(pu, pos[v]);
            if (m.variant == 0) std::reverse(A2.begin() + ps + 1, A2.begin() + pt + 1);
            else std::reverse(A2.begin() + ps, A2.begin() + pt);
        } else {  // MV_2OPTSTAR
            const auto& B = r[rid[v]];
            const int pv = pos[v];
            A2.clear(); B2.clear();
            switch (m.variant) {
                case 0:  // A : ku[..pu] + kv[pv..],  kv[..pv-1] + ku[pu+1..]
                    A2.assign(A.begin(), A.begin() + pu + 1); A2.insert(A2.end(), B.begin() + pv, B.end());
                    B2.assign(B.begin(), B.begin() + pv); B2.insert(B2.end(), A.begin() + pu + 1, A.end());
                    break;
                case 1:  // A': ku[..pu-1] + kv[pv+1..],  kv[..pv] + ku[pu..]
                    A2.assign(A.begin(), A.begin() + pu); A2.insert(A2.end(), B.begin() + pv + 1, B.end());
                    B2.assign(B.begin(), B.begin() + pv + 1); B2.insert(B2.end(), A.begin() + pu, A.end());
                    break;
                case 2:  // B : ku[..pu] + rev(kv[..pv]),  rev(ku[pu+1..]) + kv[pv+1..]
                    A2.assign(A.begin(), A.begin() + pu + 1); A2.insert(A2.end(), B.rend() - pv - 1, B.rend());
                    B2.assign(A.rbegin(), A.rend() - pu - 1); B2.insert(B2.end(), B.begin() + pv + 1, B.end());
                    break;
                default: // B': ku[..pu-1] + rev(kv[..pv-1]),  rev(ku[pu..]) + kv[pv..]
                    A2.assign(A.begin(), A.begin() + pu); A2.insert(A2.end(), B.rend() - pv, B.rend());
                    B2.assign(A.rbegin(), A.rend() - pu); B2.insert(B2.end(), B.begin() + pv, B.end());
                    break;
            }
        }
    }
    void apply(const Move& m) {
        std::vector<int> A2, B2;
        const int k1 = m.k1, k2 = m.k2;
        build(m, A2, B2);
        r[k1] = std::move(A2);
        if (k2 != k1) r[k2] = std::move(B2);
        refresh(k1);
        if (k2 != k1) refresh(k2);
    }
};

// Enumerate every granular move "anchored" at customer u.  The callback gets a
// fully evaluated Move and returns true to stop the enumeration early.
// Cost: O(k) evaluations of O(1) each.
template <class F>
inline bool for_each_move(const Routes& S, int u, int kn, int emptySlot, F&& f) {
    const Instance& I = *S.I;
    const int ku = S.rid[u], pu = S.pos[u];
    const int a = S.at(ku, pu - 1), b = S.at(ku, pu + 1);
    const int qu = I.q[u], Lu = S.load[ku];
    const double remU = I.d(a, b) - I.d(a, u) - I.d(u, b);  // removal gain of u
    Move m;
    m.u = u; m.k1 = ku;
    const auto& N = I.nbr[u];
    const int kk = std::min<int>(kn, (int)N.size());
    for (int t = 0; t < kk; ++t) {
        const int v = N[t];
        const int kv = S.rid[v], pv = S.pos[v];
        const int pvN = S.at(kv, pv - 1), svN = S.at(kv, pv + 1);  // pred / succ of v
        m.v = v; m.k2 = kv;
        // ---------------- RELOCATE u after v (variant 0) or before v (variant 1)
        for (int var = 0; var < 2; ++var) {
            int c = var == 0 ? v : pvN, e = var == 0 ? svN : v;
            if (c == u || e == u) continue;
            m.type = MV_RELOCATE; m.variant = var; m.c = c;
            m.dDist = remU + I.d(c, u) + I.d(u, e) - I.d(c, e);
            if (kv != ku) { m.L1 = Lu - qu; m.L2 = S.load[kv] + qu; } else { m.L1 = m.L2 = Lu; }
            m.nrem = 3; m.rem = {{{a, u}, {u, b}, {c, e}, {0, 0}}};
            m.nadd = 3; m.add = {{{a, b}, {c, u}, {u, e}, {0, 0}}};
            if (f(m)) return true;
        }
        if (kv != ku) {
            // ------------ SWAP u <-> v
            m.type = MV_SWAP; m.variant = 0;
            m.dDist = I.d(a, v) + I.d(v, b) - I.d(a, u) - I.d(u, b)
                    + I.d(pvN, u) + I.d(u, svN) - I.d(pvN, v) - I.d(v, svN);
            m.L1 = Lu - qu + I.q[v]; m.L2 = S.load[kv] - I.q[v] + qu;
            m.nrem = 4; m.rem = {{{a, u}, {u, b}, {pvN, v}, {v, svN}}};
            m.nadd = 4; m.add = {{{a, v}, {v, b}, {pvN, u}, {u, svN}}};
            if (f(m)) return true;
            // ------------ 2-OPT* (tail exchanges), all create edge (u,v)
            m.type = MV_2OPTSTAR;
            const int Pu = S.prefix(ku, pu), Pv = S.prefix(kv, pv);
            const int Pu1 = S.prefix(ku, pu - 1), Pv1 = S.prefix(kv, pv - 1);
            const int Lv = S.load[kv];
            // A : ...u -> v...      and ...pred(v) -> succ(u)...
            m.variant = 0;
            m.dDist = I.d(u, v) + I.d(pvN, b) - I.d(u, b) - I.d(pvN, v);
            m.L1 = Pu + (Lv - Pv1); m.L2 = Pv1 + (Lu - Pu);
            m.nrem = 2; m.rem = {{{u, b}, {pvN, v}, {0, 0}, {0, 0}}};
            m.nadd = 2; m.add = {{{u, v}, {pvN, b}, {0, 0}, {0, 0}}};
            if (f(m)) return true;
            // A': ...v -> u...      and ...pred(u) -> succ(v)...
            m.variant = 1;
            m.dDist = I.d(v, u) + I.d(a, svN) - I.d(a, u) - I.d(v, svN);
            m.L1 = Pu1 + (Lv - Pv); m.L2 = Pv + (Lu - Pu1);
            m.rem = {{{a, u}, {v, svN}, {0, 0}, {0, 0}}};
            m.add = {{{v, u}, {a, svN}, {0, 0}, {0, 0}}};
            if (f(m)) return true;
            // B : heads joined (u -> v, rest of v's head reversed), tails joined
            m.variant = 2;
            m.dDist = I.d(u, v) + I.d(b, svN) - I.d(u, b) - I.d(v, svN);
            m.L1 = Pu + Pv; m.L2 = (Lu - Pu) + (Lv - Pv);
            m.rem = {{{u, b}, {v, svN}, {0, 0}, {0, 0}}};
            m.add = {{{u, v}, {b, svN}, {0, 0}, {0, 0}}};
            if (f(m)) return true;
            // B': tails joined at (u,v), heads joined at (pred u, pred v)
            m.variant = 3;
            m.dDist = I.d(u, v) + I.d(a, pvN) - I.d(a, u) - I.d(pvN, v);
            m.L1 = Pu1 + Pv1; m.L2 = (Lu - Pu1) + (Lv - Pv1);
            m.rem = {{{a, u}, {pvN, v}, {0, 0}, {0, 0}}};
            m.add = {{{u, v}, {a, pvN}, {0, 0}, {0, 0}}};
            if (f(m)) return true;
        } else if (std::abs(pv - pu) > 1) {
            // ------------ 2-OPT inside the route, creates edge (s,t)
            const int s = pu < pv ? u : v, tt = pu < pv ? v : u;
            const int x = S.succ(s), y = S.succ(tt), ps = S.pred(s), pt = S.pred(tt);
            m.type = MV_2OPT; m.L1 = m.L2 = Lu; m.nrem = 2; m.nadd = 2;
            m.variant = 0;  // reverse succ(s)..t
            m.dDist = I.d(s, tt) + I.d(x, y) - I.d(s, x) - I.d(tt, y);
            m.rem = {{{s, x}, {tt, y}, {0, 0}, {0, 0}}};
            m.add = {{{s, tt}, {x, y}, {0, 0}, {0, 0}}};
            if (f(m)) return true;
            m.variant = 1;  // reverse s..pred(t)
            m.dDist = I.d(s, tt) + I.d(ps, pt) - I.d(ps, s) - I.d(pt, tt);
            m.rem = {{{ps, s}, {pt, tt}, {0, 0}, {0, 0}}};
            m.add = {{{s, tt}, {ps, pt}, {0, 0}, {0, 0}}};
            if (f(m)) return true;
        }
    }
    // ---------------- RELOCATE u into an empty route (opens a new vehicle)
    if (emptySlot >= 0 && S.r[ku].size() > 1) {
        m.type = MV_RELOCATE; m.variant = 2; m.v = 0; m.k2 = emptySlot; m.c = 0;
        m.dDist = remU + I.d(0, u) + I.d(u, 0);
        m.L1 = Lu - qu; m.L2 = qu;
        m.nrem = 2; m.rem = {{{a, u}, {u, b}, {0, 0}, {0, 0}}};
        m.nadd = 3; m.add = {{{a, b}, {0, u}, {u, 0}, {0, 0}}};
        if (f(m)) return true;
    }
    return false;
}
