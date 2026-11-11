// solution.hpp -- route-based solution helpers: cost, feasibility, hashing,
// JSON serialisation. Own implementation.
#pragma once
#include <cstdint>
#include <string>
#include <vector>

#include "instance.hpp"

using RouteList = std::vector<std::vector<int>>;  // each route: customers only (no depot)

double route_cost(const Instance& I, const std::vector<int>& r);
double solution_cost(const Instance& I, const RouteList& R);
int route_load(const Instance& I, const std::vector<int>& r);
// Number of times the route changes side (depot -> ... -> depot). Always even.
int route_crossings(const Instance& I, const std::vector<int>& r);
// Empty string if feasible; otherwise a human-readable reason.
std::string check_solution(const Instance& I, const RouteList& R, bool check_fleet = true);
// Order-independent hash of the undirected edge multiset (incl. depot edges).
uint64_t solution_hash(const RouteList& R);
// Remove empty routes.
RouteList compact(const RouteList& R);
std::string routes_json(const RouteList& R);
