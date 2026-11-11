// tabu.hpp -- granular Tabu Search with adaptive capacity penalty.
// Own implementation; design follows Glover & Laguna (1997), Gendreau, Hertz &
// Laporte (1994, TABUROUTE: penalised infeasibility) and Toth & Vigo (2003,
// granular neighbourhoods).
#pragma once
#include "run.hpp"

struct TSParams {
    double time_limit = 10.0;       // seconds (wall clock)
    long long max_iters = -1;       // optional iteration limit
    int tmin = 10, tmax = 25;       // tabu tenure drawn uniformly in [tmin, tmax]
    int nbr = 20;                   // granularity: k nearest neighbours
    double lambda0 = -1.0;          // initial penalty per unit of overload (<0: auto)
    double delta = 0.3;             // lambda *= (1+delta) if infeasible, /= otherwise
    long long restart_iters = -1;   // restart from best after this many non-improving it (<0: auto)
    int perturb = -1;               // random relocations at restart (<0: auto)
    bool snaps = false;             // record best-so-far solutions (STN)
    int osc_every = 0;              // record (dist, overload, lambda) every k iterations
    int osc_max = 20000;
};

RunResult tabu_search(const Instance& I, const TSParams& p, uint64_t seed, const RouteList& init);
// Reduce a route list to at most K routes by cheapest (penalised) insertion of the
// customers of the smallest routes. May create overload, which TS then repairs.
RouteList reduce_routes(const Instance& I, RouteList R, int K);
