// savings.hpp -- Clarke & Wright (1964) parallel savings heuristic.
// Own implementation following the textbook description (Toth & Vigo 2014, ch. 4).
#pragma once
#include "solution.hpp"

// Deterministic. Ignores the fleet limit K (may return more than K routes).
// Time: O(n^2 log n) -- dominated by sorting the n(n-1)/2 savings.
RouteList clarke_wright(const Instance& I);
