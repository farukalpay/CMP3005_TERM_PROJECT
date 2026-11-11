// localsearch.hpp -- feasible first-improvement local search over the granular
// neighbourhoods of routes.hpp (used by the memetic GA).  Own implementation.
#pragma once
#include "common.hpp"
#include "routes.hpp"

// Improves S in place until no improving capacity-feasible move exists.
// Returns the number of applied moves.
int local_search(Routes& S, int kn, Rng& rng);
