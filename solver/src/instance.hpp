// instance.hpp -- CVRP instance: parsing (CVRPLIB/TSPLIB format + MediDrone
// extension), distance matrix, neighbour lists.
//
// Own implementation (Faruk Alpay). File format follows the TSPLIB/CVRPLIB
// conventions (Reinelt 1991; Uchoa et al. 2017).  Our extension keys:
//   EDGE_WEIGHT_TYPE : EXACT_2D        Euclidean distance WITHOUT rounding
//   CROSSING_PENALTY : <P>             add P when the two endpoints lie on
//   SIDE_SECTION                       different sides (0 = Europe, 1 = Asia)
//   VEHICLES : <K>                     fleet size (max number of routes)
#pragma once
#include <string>
#include <vector>

struct Instance {
    std::string name;
    int n = 0;             // number of customers; nodes are 0 (depot) .. n
    int Q = 0;             // vehicle capacity
    int K = 0;             // fleet size = maximum number of routes
    bool rounded = true;   // TSPLIB EUC_2D: nint() of the Euclidean part
    double P = 0.0;        // Bosphorus crossing penalty (0 = none)
    std::vector<double> x, y;
    std::vector<int> q;    // demand per node, q[0] = 0
    std::vector<int> side; // side per node (empty if no penalty)
    std::vector<double> D; // (n+1) x (n+1) distance matrix, row-major
    std::vector<std::vector<int>> nbr;  // nbr[i]: customers sorted by d(i,.)

    inline double d(int i, int j) const { return D[(size_t)i * (size_t)(n + 1) + (size_t)j]; }
    int total_demand() const;
    // Build neighbour lists with the k closest customers of every customer.
    void build_neighbors(int k);
    // Recompute the distance matrix from coordinates, sides, P and rounding.
    void build_distances();
};

// Parse a file in CVRPLIB format. Node with the DEPOT_SECTION id becomes 0.
// fleet: -1 = infer K from VEHICLES / name "-kX" / comment; 0 = unlimited (K=n);
// >0 = explicit value.
Instance read_instance(const std::string& path, int fleet = -1);
