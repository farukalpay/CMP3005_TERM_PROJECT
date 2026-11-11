// main.cpp -- command line interface of the MediDrone CVRP solver.
// Own implementation (Faruk Alpay).
//
//   medidrone solve      --inst F --alg cw|ga|ma|ts --time T --seed S [--out F] [params]
//   medidrone bench-split --inst F --reps R --seed S        (Bellman O(nL) vs linear O(n) Split)
//   medidrone bench-eval  --inst F --seed S [--nbr k]       (delta vs route vs full re-evaluation)
//   medidrone bench-iter  --inst F --alg ga|ma|ts --iters N (time per GA generation / TS iteration)
//
// All output is JSON (one object), written to --out or stdout.
#include <cstdio>
#include <fstream>
#include <iostream>
#include <map>
#include <sstream>
#include <stdexcept>

#include "common.hpp"
#include "ga.hpp"
#include "localsearch.hpp"
#include "routes.hpp"
#include "savings.hpp"
#include "split.hpp"
#include "tabu.hpp"

namespace {
struct Args {
    std::map<std::string, std::string> kv;
    bool has(const std::string& k) const { return kv.count(k) > 0; }
    std::string s(const std::string& k, const std::string& d = "") const { return has(k) ? kv.at(k) : d; }
    double f(const std::string& k, double d) const { return has(k) ? std::stod(kv.at(k)) : d; }
    long long i(const std::string& k, long long d) const { return has(k) ? std::stoll(kv.at(k)) : d; }
};

std::string num(double x) {
    if (!std::isfinite(x)) return "null";
    std::ostringstream os;
    os.precision(10);
    os << x;
    return os.str();
}

void emit(const Args& a, const std::string& json) {
    if (a.has("out")) {
        std::ofstream o(a.s("out"));
        o << json << "\n";
    } else {
        std::cout << json << "\n";
    }
}

std::string g_inst_path;
std::string header(const Instance& I) {
    std::ostringstream os;
    os << "\"instance\":\"" << I.name << "\",\"path\":\"" << g_inst_path << "\",\"n\":" << I.n << ",\"Q\":" << I.Q << ",\"K\":" << I.K
       << ",\"P\":" << num(I.P) << ",\"rounded\":" << (I.rounded ? "true" : "false");
    return os.str();
}

std::string result_json(const Instance& I, const Args& a, const std::string& alg, uint64_t seed,
                        const RunResult& r, const std::string& params) {
    std::ostringstream os;
    os << "{" << header(I) << ",\"alg\":\"" << alg << "\",\"seed\":" << seed
       << ",\"time_limit\":" << num(a.f("time", 10)) << ",\"params\":{" << params << "}";
    std::string why = r.feasible ? check_solution(I, r.best) : "no feasible solution";
    double recomputed = r.feasible ? solution_cost(I, r.best) : NAN;
    int cross = 0, crossRoutes = 0;
    for (auto& R : r.best) { int c = route_crossings(I, R); cross += c; crossRoutes += c > 0; }
    os << ",\"cost\":" << num(r.cost) << ",\"recomputed_cost\":" << num(recomputed)
       << ",\"feasible\":" << (why.empty() ? "true" : "false") << ",\"check\":\"" << why << "\""
       << ",\"num_routes\":" << r.best.size() << ",\"crossings\":" << cross << ",\"crossing_routes\":" << crossRoutes
       << ",\"time_to_best\":" << num(r.time_to_best) << ",\"total_time\":" << num(r.total_time)
       << ",\"iterations\":" << r.iterations << ",\"evaluations\":" << r.evaluations
       << ",\"restarts\":" << r.restarts << ",\"routes\":" << routes_json(r.best);
    os << ",\"trace\":[";
    for (size_t k = 0; k < r.trace.size(); ++k)
        os << (k ? "," : "") << "[" << num(r.trace[k][0]) << "," << (long long)r.trace[k][1] << "," << num(r.trace[k][2]) << "]";
    os << "],\"move_count\":{";
    for (int t = 0; t < MV_COUNT; ++t) os << (t ? "," : "") << "\"" << move_name(t) << "\":" << r.move_count[t];
    os << "}";
    if (!r.move_hist.empty()) {
        os << ",\"move_hist\":[";
        for (size_t k = 0; k < r.move_hist.size(); ++k) {
            os << (k ? "," : "") << "[";
            for (int j = 0; j < 5; ++j) os << (j ? "," : "") << r.move_hist[k][j];
            os << "]";
        }
        os << "]";
    }
    if (!r.snaps.empty()) {
        os << ",\"snaps\":[";
        for (size_t k = 0; k < r.snaps.size(); ++k)
            os << (k ? "," : "") << "{\"t\":" << num(r.snaps[k].t) << ",\"it\":" << r.snaps[k].it
               << ",\"cost\":" << num(r.snaps[k].cost) << ",\"routes\":" << routes_json(r.snaps[k].R) << "}";
        os << "]";
    }
    if (!r.osc.empty()) {
        os << ",\"osc\":[";
        for (size_t k = 0; k < r.osc.size(); ++k)
            os << (k ? "," : "") << "[" << r.osc[k].it << "," << num(r.osc[k].dist) << "," << r.osc[k].over << ","
               << num(r.osc[k].lambda) << "]";
        os << "]";
    }
    if (!r.div.empty()) {
        os << ",\"div\":[";
        for (size_t k = 0; k < r.div.size(); ++k)
            os << (k ? "," : "") << "[" << r.div[k].gen << "," << num(r.div[k].t) << "," << num(r.div[k].best) << ","
               << num(r.div[k].mean) << "," << num(r.div[k].diversity) << "]";
        os << "]";
    }
    if (!r.extra.empty()) os << "," << r.extra;
    os << "}";
    return os.str();
}

GAParams ga_params(const Args& a, bool memetic, std::string& ps) {
    GAParams p;
    p.time_limit = a.f("time", 10);
    p.max_gens = a.i("iters", -1);
    p.pop = (int)a.i("pop", memetic ? 30 : 50);
    p.pc = a.f("pc", memetic ? 1.0 : 0.9);
    p.pm = a.f("pm", memetic ? 0.1 : 0.3);
    p.mut = (int)a.i("mut", 3);
    p.pls = a.f("pls", memetic ? 1.0 : 0.0);
    p.nbr = (int)a.i("nbr", 20);
    p.restart_gens = (int)a.i("restart", -1);
    p.keep_frac = a.f("keep", 0.2);
    p.bellman = a.i("bellman", 0) != 0;
    p.seed_cw = a.i("seedcw", 1) != 0;
    p.snaps = a.i("snaps", 0) != 0;
    p.div_every = (int)a.i("div", 0);
    std::ostringstream os;
    os << "\"pop\":" << p.pop << ",\"pc\":" << p.pc << ",\"pm\":" << p.pm << ",\"mut\":" << p.mut << ",\"pls\":" << p.pls
       << ",\"nbr\":" << p.nbr << ",\"restart\":" << p.restart_gens << ",\"keep\":" << p.keep_frac
       << ",\"split\":\"" << (p.bellman ? "bellman" : "linear") << "\",\"seedcw\":" << (p.seed_cw ? 1 : 0);
    ps = os.str();
    return p;
}

TSParams ts_params(const Args& a, std::string& ps) {
    TSParams p;
    p.time_limit = a.f("time", 10);
    p.max_iters = a.i("iters", -1);
    p.tmin = (int)a.i("tmin", 10);
    p.tmax = (int)a.i("tmax", 25);
    p.nbr = (int)a.i("nbr", 20);
    p.lambda0 = a.f("lambda0", -1);
    p.delta = a.f("delta", 0.3);
    p.restart_iters = a.i("restart", -1);
    p.perturb = (int)a.i("perturb", -1);
    p.snaps = a.i("snaps", 0) != 0;
    p.osc_every = (int)a.i("osc", 0);
    std::ostringstream os;
    os << "\"tmin\":" << p.tmin << ",\"tmax\":" << p.tmax << ",\"nbr\":" << p.nbr << ",\"lambda0\":" << p.lambda0
       << ",\"delta\":" << p.delta << ",\"restart\":" << p.restart_iters << ",\"perturb\":" << p.perturb;
    ps = os.str();
    return p;
}

int cmd_solve(const Args& a) {
    Instance I = read_instance(a.s("inst"), (int)a.i("fleet", -1));
    const std::string alg = a.s("alg", "ts");
    const uint64_t seed = (uint64_t)a.i("seed", 1);
    // granular neighbourhoods need neighbour lists (k = max nbr used)
    int nbr = (int)a.i("nbr", 20);
    if (nbr <= 0 || nbr >= I.n) nbr = I.n - 1;
    I.build_neighbors(nbr);
    Args b = a;
    b.kv["nbr"] = std::to_string(nbr);
    Timer t;
    RouteList cw = clarke_wright(I);
    double cw_time = t.elapsed();
    RunResult r;
    std::string ps;
    if (alg == "cw") {
        r.best = cw;
        r.cost = solution_cost(I, cw);
        r.feasible = check_solution(I, cw).empty();
        r.total_time = r.time_to_best = cw_time;
        r.trace.push_back({cw_time, 0, r.cost});
        if (!r.feasible) {  // report CW cost even if it exceeds K (flagged by the checker)
            r.extra = "\"cw_routes\":" + std::to_string(cw.size()) + ",\"cw_cost\":" + num(r.cost) + ",\"cw_check\":\"" +
                      check_solution(I, cw) + "\"";
            r.feasible = check_solution(I, cw, false).empty();
        }
    } else if (alg == "ts") {
        TSParams p = ts_params(b, ps);
        r = tabu_search(I, p, seed, cw);
    } else if (alg == "ga" || alg == "ma") {
        GAParams p = ga_params(b, alg == "ma", ps);
        r = genetic_algorithm(I, p, seed, cw);
    } else {
        throw std::runtime_error("unknown --alg " + alg);
    }
    emit(a, result_json(I, b, alg, seed, r, ps));
    return 0;
}

int cmd_bench_split(const Args& a) {
    Instance I = read_instance(a.s("inst"), 0);
    Rng rng((uint64_t)a.i("seed", 1));
    int reps = (int)a.i("reps", 200);
    std::vector<std::vector<int>> tours(reps, std::vector<int>(I.n));
    for (auto& t : tours) { std::iota(t.begin(), t.end(), 1); rng.shuffle(t); }
    double maxdiff = 0, sumB = 0, sumL = 0, avgLen = 0;
    Timer tb;
    for (auto& t : tours) sumB += split_bellman(I, t).cost;
    double timeB = tb.elapsed();
    Timer tl;
    for (auto& t : tours) sumL += split_linear(I, t).cost;
    double timeL = tl.elapsed();
    for (auto& t : tours) {
        auto x = split_bellman(I, t), y = split_linear(I, t);
        maxdiff = std::max(maxdiff, std::abs(x.cost - y.cost));
        avgLen += (double)I.n / x.routes;
    }
    // L = maximal number of customers that fit in one route (worst-case inner loop length)
    std::vector<int> qs(I.q.begin() + 1, I.q.end());
    std::sort(qs.begin(), qs.end());
    int L = 0, load = 0;
    for (int v : qs) { if (load + v > I.Q) break; load += v; ++L; }
    std::ostringstream os;
    os << "{" << header(I) << ",\"reps\":" << reps << ",\"t_bellman\":" << num(timeB / reps) << ",\"t_linear\":"
       << num(timeL / reps) << ",\"check\":" << num(std::abs(sumB - sumL)) << ",\"max_abs_diff\":" << num(maxdiff) << ",\"avg_route_len\":" << num(avgLen / reps)
       << ",\"L\":" << L << "}";
    emit(a, os.str());
    return 0;
}

int cmd_bench_eval(const Args& a) {
    // Evaluate the complete granular neighbourhood of the CW solution three ways:
    //   delta (O(1)), route-level re-evaluation (O(L)), full re-evaluation (O(n)).
    Instance I = read_instance(a.s("inst"), (int)a.i("fleet", 0));
    int nbr = (int)a.i("nbr", 20);
    if (nbr <= 0 || nbr >= I.n) nbr = I.n - 1;
    I.build_neighbors(nbr);
    Routes S;
    S.init(I, clarke_wright(I), (int)clarke_wright(I).size() + 1);
    std::vector<Move> moves;
    const int empty = S.empty_slot();
    for (int u = 1; u <= I.n; ++u) for_each_move(S, u, nbr, empty, [&](const Move& m) { moves.push_back(m); return false; });
    int reps = (int)a.i("reps", 3);
    double sink = 0;
    Timer t1;
    for (int r = 0; r < reps; ++r)
        for (int u = 1; u <= I.n; ++u)
            for_each_move(S, u, nbr, empty, [&](const Move& m) { sink += m.dDist + S.dOver(m); return false; });
    double tDelta = t1.elapsed() / reps;
    std::vector<int> A2, B2;
    double maxErrRoute = 0, maxErrFull = 0;
    Timer t2;
    for (int r = 0; r < reps; ++r)
        for (auto& m : moves) {
            S.build(m, A2, B2);
            double nc = route_cost(I, A2) - S.cost[m.k1];
            if (m.k2 != m.k1) nc += route_cost(I, B2) - S.cost[m.k2];
            sink += nc;
            if (r == 0) maxErrRoute = std::max(maxErrRoute, std::abs(nc - m.dDist));
        }
    double tRoute = t2.elapsed() / reps;
    Timer t3;
    for (auto& m : moves) {  // full: build the neighbour and recompute its cost from scratch, O(n)
        S.build(m, A2, B2);
        double full = 0.0;
        for (int k = 0; k < (int)S.r.size(); ++k)
            if (k != m.k1 && k != m.k2) full += route_cost(I, S.r[k]);
        full += route_cost(I, A2);
        if (m.k2 != m.k1) full += route_cost(I, B2);
        sink += full;
        maxErrFull = std::max(maxErrFull, std::abs((full - S.dist) - m.dDist));
    }
    double tFull = t3.elapsed();
    std::ostringstream os;
    os << "{" << header(I) << ",\"nbr\":" << nbr << ",\"moves\":" << moves.size() << ",\"t_delta\":" << num(tDelta)
       << ",\"t_route\":" << num(tRoute) << ",\"t_full\":" << num(tFull) << ",\"max_err_route\":" << num(maxErrRoute)
       << ",\"max_err_full\":" << num(maxErrFull) << ",\"sink\":" << num(sink > 0 ? 1 : 0) << "}";
    emit(a, os.str());
    return 0;
}

int cmd_bench_iter(const Args& a) {
    Instance I = read_instance(a.s("inst"), (int)a.i("fleet", 0));
    int nbr = (int)a.i("nbr", 20);
    if (nbr <= 0 || nbr >= I.n) nbr = I.n - 1;
    I.build_neighbors(nbr);
    Args b = a;
    b.kv["nbr"] = std::to_string(nbr);
    std::string alg = a.s("alg", "ts"), ps;
    long long iters = a.i("iters", 100);
    RouteList cw = clarke_wright(I);
    // warm-up run (iters/10) then the measured run; time per iteration excludes nothing
    // but initialisation is amortised by comparing two run lengths.
    auto run = [&](long long it) {
        b.kv["iters"] = std::to_string(it);
        Timer t;
        if (alg == "ts") { TSParams p = ts_params(b, ps); p.restart_iters = 1LL << 60; tabu_search(I, p, 1, cw); }
        else { GAParams p = ga_params(b, alg == "ma", ps); p.restart_gens = 1 << 30; genetic_algorithm(I, p, 1, cw); }
        return t.elapsed();
    };
    double t0 = run(std::max(1LL, iters / 10));
    double t1 = run(iters + std::max(1LL, iters / 10));
    double per = (t1 - t0) / iters;   // initialisation cancels out
    std::ostringstream os;
    os << "{" << header(I) << ",\"alg\":\"" << alg << "\",\"nbr\":" << nbr << ",\"iters\":" << iters
       << ",\"time_per_iter\":" << num(per) << ",\"params\":{" << ps << "}}";
    emit(a, os.str());
    return 0;
}
}  // namespace

int main(int argc, char** argv) {
    if (argc < 2) {
        std::fprintf(stderr, "usage: medidrone solve|bench-split|bench-eval|bench-iter --inst FILE [options]\n");
        return 2;
    }
    Args a;
    for (int k = 2; k < argc; ++k) {
        std::string s = argv[k];
        if (s.rfind("--", 0) == 0) {
            std::string key = s.substr(2), val = "1";
            if (k + 1 < argc && std::string(argv[k + 1]).rfind("--", 0) != 0) val = argv[++k];
            a.kv[key] = val;
        }
    }
    try {
        g_inst_path = a.s("inst");
        std::string cmd = argv[1];
        if (cmd == "solve") return cmd_solve(a);
        if (cmd == "bench-split") return cmd_bench_split(a);
        if (cmd == "bench-eval") return cmd_bench_eval(a);
        if (cmd == "bench-iter") return cmd_bench_iter(a);
        std::fprintf(stderr, "unknown command %s\n", cmd.c_str());
        return 2;
    } catch (const std::exception& e) {
        std::fprintf(stderr, "error: %s\n", e.what());
        return 1;
    }
}
