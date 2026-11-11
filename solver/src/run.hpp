// run.hpp -- result record of one metaheuristic run (+ optional traces).
#pragma once
#include <array>
#include <limits>
#include <string>
#include <vector>

#include "solution.hpp"

struct Snapshot {          // best-so-far solution at an improvement (for STNs)
    double t; long long it; double cost; RouteList R;
};
struct OscPoint {          // TS current state (for the strategic-oscillation plot)
    long long it; double dist; int over; double lambda;
};
struct DivPoint {          // GA population statistics per generation
    long long gen; double t; double best, mean, diversity;
};

struct RunResult {
    RouteList best;
    double cost = std::numeric_limits<double>::infinity();
    bool feasible = false;
    double time_to_best = 0.0, total_time = 0.0;
    long long iterations = 0;          // TS iterations or GA generations
    long long evaluations = 0;         // TS move evaluations or GA children
    std::vector<std::array<double, 3>> trace;  // (time, iteration, best cost)
    std::vector<Snapshot> snaps;
    std::vector<OscPoint> osc;
    std::vector<DivPoint> div;
    std::array<long long, 4> move_count{};      // TS: applied moves per type
    std::vector<std::array<long long, 5>> move_hist;  // TS: (iter, counts...) every 1000 it
    long long restarts = 0;
    std::string extra;                 // algorithm-specific JSON fragment
};
