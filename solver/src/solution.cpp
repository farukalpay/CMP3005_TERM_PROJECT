// solution.cpp -- see solution.hpp. Own implementation.
#include "solution.hpp"

#include <sstream>

#include "common.hpp"

double route_cost(const Instance& I, const std::vector<int>& r) {
    if (r.empty()) return 0.0;
    double c = I.d(0, r.front()) + I.d(r.back(), 0);
    for (size_t k = 1; k < r.size(); ++k) c += I.d(r[k - 1], r[k]);
    return c;
}

double solution_cost(const Instance& I, const RouteList& R) {
    double c = 0.0;
    for (auto& r : R) c += route_cost(I, r);
    return c;
}

int route_load(const Instance& I, const std::vector<int>& r) {
    int l = 0;
    for (int v : r) l += I.q[v];
    return l;
}

int route_crossings(const Instance& I, const std::vector<int>& r) {
    if (I.side.empty() || r.empty()) return 0;
    int c = 0, prev = 0;
    for (int v : r) { c += I.side[prev] != I.side[v]; prev = v; }
    c += I.side[prev] != I.side[0];
    return c;
}

std::string check_solution(const Instance& I, const RouteList& R, bool check_fleet) {
    std::vector<int> seen(I.n + 1, 0);
    int used = 0;
    for (size_t k = 0; k < R.size(); ++k) {
        if (R[k].empty()) continue;
        ++used;
        int load = 0;
        for (int v : R[k]) {
            if (v < 1 || v > I.n) return "invalid customer id " + std::to_string(v);
            if (++seen[v] > 1) return "customer " + std::to_string(v) + " visited twice";
            load += I.q[v];
        }
        if (load > I.Q) return "route " + std::to_string(k) + " overloaded: " + std::to_string(load);
    }
    for (int v = 1; v <= I.n; ++v)
        if (!seen[v]) return "customer " + std::to_string(v) + " not visited";
    if (check_fleet && used > I.K)
        return "too many routes: " + std::to_string(used) + " > K=" + std::to_string(I.K);
    return "";
}

uint64_t solution_hash(const RouteList& R) {
    uint64_t h = 0;
    for (auto& r : R) {
        if (r.empty()) continue;
        int prev = 0;
        for (int v : r) { h += edge_hash(prev, v); prev = v; }
        h += edge_hash(prev, 0);
    }
    return h;
}

RouteList compact(const RouteList& R) {
    RouteList out;
    for (auto& r : R)
        if (!r.empty()) out.push_back(r);
    return out;
}

std::string routes_json(const RouteList& R) {
    std::ostringstream os;
    os << "[";
    bool first = true;
    for (auto& r : R) {
        if (r.empty()) continue;
        if (!first) os << ",";
        first = false;
        os << "[";
        for (size_t k = 0; k < r.size(); ++k) os << (k ? "," : "") << r[k];
        os << "]";
    }
    os << "]";
    return os.str();
}
