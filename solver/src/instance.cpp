// instance.cpp -- see instance.hpp. Own implementation.
#include "instance.hpp"

#include <algorithm>
#include <cmath>
#include <fstream>
#include <map>
#include <numeric>
#include <regex>
#include <sstream>
#include <stdexcept>

namespace {
std::string trim(const std::string& s) {
    size_t a = s.find_first_not_of(" \t\r\n\"");
    if (a == std::string::npos) return "";
    size_t b = s.find_last_not_of(" \t\r\n\"");
    return s.substr(a, b - a + 1);
}
std::string upper(std::string s) {
    for (auto& c : s) c = (char)std::toupper((unsigned char)c);
    return s;
}
}  // namespace

int Instance::total_demand() const { return std::accumulate(q.begin(), q.end(), 0); }

void Instance::build_distances() {
    const int N = n + 1;
    D.assign((size_t)N * N, 0.0);
    for (int i = 0; i < N; ++i)
        for (int j = i + 1; j < N; ++j) {
            double dx = x[i] - x[j], dy = y[i] - y[j];
            double e = std::sqrt(dx * dx + dy * dy);
            if (rounded) e = std::floor(e + 0.5);  // TSPLIB nint()
            if (P != 0.0 && !side.empty() && side[i] != side[j]) e += P;
            D[(size_t)i * N + j] = D[(size_t)j * N + i] = e;
        }
}

void Instance::build_neighbors(int k) {
    k = std::max(1, std::min(k, n - 1));
    nbr.assign(n + 1, {});
    std::vector<int> cand;
    for (int i = 1; i <= n; ++i) {
        cand.clear();
        for (int j = 1; j <= n; ++j)
            if (j != i) cand.push_back(j);
        // partial sort is O(n log k); ties broken by index for determinism
        std::partial_sort(cand.begin(), cand.begin() + k, cand.end(), [&](int a, int b) {
            double da = d(i, a), db = d(i, b);
            return da < db || (da == db && a < b);
        });
        nbr[i].assign(cand.begin(), cand.begin() + k);
    }
}

Instance read_instance(const std::string& path, int fleet) {
    std::ifstream in(path);
    if (!in) throw std::runtime_error("cannot open instance file: " + path);
    Instance I;
    std::string line, section, comment;
    int dim = 0, vehicles = -1;
    std::string ewt = "EUC_2D";
    std::map<int, std::pair<double, double>> coord;
    std::map<int, int> dem, sid;
    std::vector<int> depots;
    while (std::getline(in, line)) {
        std::string t = trim(line);
        if (t.empty()) continue;
        std::string T = upper(t);
        if (T == "EOF") break;
        if (T.find("_SECTION") != std::string::npos && T.find(':') == std::string::npos) {
            section = T;
            continue;
        }
        size_t colon = t.find(':');
        if (colon != std::string::npos && (section.empty() || std::isalpha((unsigned char)t[0]))) {
            std::string key = upper(trim(t.substr(0, colon)));
            std::string val = trim(t.substr(colon + 1));
            section.clear();
            if (key == "NAME") I.name = val;
            else if (key == "COMMENT") comment = val;
            else if (key == "DIMENSION") dim = std::stoi(val);
            else if (key == "CAPACITY") I.Q = std::stoi(val);
            else if (key == "EDGE_WEIGHT_TYPE") ewt = upper(val);
            else if (key == "VEHICLES") vehicles = std::stoi(val);
            else if (key == "CROSSING_PENALTY") I.P = std::stod(val);
            continue;
        }
        std::istringstream ss(t);
        if (section == "NODE_COORD_SECTION") {
            int id; double a, b;
            ss >> id >> a >> b;
            coord[id] = {a, b};
        } else if (section == "DEMAND_SECTION") {
            int id, v;
            ss >> id >> v;
            dem[id] = v;
        } else if (section == "DEPOT_SECTION") {
            int id;
            while (ss >> id)
                if (id >= 0) depots.push_back(id);
        } else if (section == "SIDE_SECTION") {
            int id, v;
            ss >> id >> v;
            sid[id] = v;
        }
    }
    if (ewt != "EUC_2D" && ewt != "EXACT_2D")
        throw std::runtime_error("unsupported EDGE_WEIGHT_TYPE " + ewt);
    I.rounded = (ewt == "EUC_2D");
    if (dim <= 1 || (int)coord.size() != dim) throw std::runtime_error("bad DIMENSION/coordinates in " + path);
    int depot = depots.empty() ? coord.begin()->first : depots[0];
    // internal order: depot first, then remaining ids in increasing order
    std::vector<int> ids{depot};
    for (auto& kv : coord)
        if (kv.first != depot) ids.push_back(kv.first);
    I.n = dim - 1;
    I.x.resize(dim); I.y.resize(dim); I.q.resize(dim);
    if (!sid.empty()) I.side.resize(dim);
    for (int k = 0; k < dim; ++k) {
        I.x[k] = coord[ids[k]].first;
        I.y[k] = coord[ids[k]].second;
        I.q[k] = (k == 0) ? 0 : dem[ids[k]];
        if (!sid.empty()) I.side[k] = sid[ids[k]];
    }
    // fleet size K
    std::smatch m;
    if (fleet > 0) I.K = fleet;
    else if (fleet == 0) I.K = I.n;
    else if (vehicles > 0) I.K = vehicles;
    else if (std::regex_search(I.name, m, std::regex("-k([0-9]+)"))) I.K = std::stoi(m[1]);
    else if (std::regex_search(comment, m, std::regex("trucks: *([0-9]+)"))) I.K = std::stoi(m[1]);
    else I.K = (I.total_demand() + I.Q - 1) / I.Q;
    for (int i = 1; i <= I.n; ++i)
        if (I.q[i] > I.Q) throw std::runtime_error("demand larger than capacity");
    I.build_distances();
    return I;
}
