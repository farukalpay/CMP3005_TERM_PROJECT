// ga.hpp -- steady-state Genetic Algorithm with giant-tour chromosomes and the
// optimal Split decoder (Prins 2004).  With pls > 0 it becomes a memetic
// algorithm (local search applied to offspring).  Own implementation.
#pragma once
#include "run.hpp"

struct GAParams {
    double time_limit = 10.0;
    long long max_gens = -1;
    int pop = 50;            // population size (mu)
    double pc = 0.9;         // crossover (OX) probability
    double pm = 0.3;         // mutation probability per child
    int mut = 3;             // 0 swap, 1 inversion, 2 insertion, 3 one of them at random
    double pls = 0.0;        // probability of local search per child (memetic GA if > 0)
    int nbr = 20;            // granularity of the local search
    int restart_gens = -1;   // partial restart after this many non-improving generations
    double keep_frac = 0.2;  // fraction of best individuals kept at a restart
    bool bellman = false;    // decode with the O(nL) Bellman split instead of O(n)
    bool seed_cw = true;     // insert the Clarke-Wright giant tour into the initial population
    bool snaps = false;
    int div_every = 0;       // record population diversity every k generations
};

RunResult genetic_algorithm(const Instance& I, const GAParams& p, uint64_t seed, const RouteList& cw);
// Broken-pairs distance in [0,1] between two solutions (fraction of customers
// whose successor edge in A is not an edge of B).
double broken_pairs(const RouteList& A, const RouteList& B, int n);
