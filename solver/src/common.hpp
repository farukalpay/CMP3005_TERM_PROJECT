// common.hpp -- random numbers, timer, small helpers. Own implementation.
#pragma once
#include <algorithm>
#include <chrono>
#include <cstdint>
#include <random>
#include <vector>

struct Rng {
    std::mt19937_64 g;
    explicit Rng(uint64_t seed) : g(seed * 0x9E3779B97F4A7C15ULL + 12345) {}
    int uniform_int(int a, int b) { return std::uniform_int_distribution<int>(a, b)(g); }  // [a,b]
    double uniform() { return std::uniform_real_distribution<double>(0.0, 1.0)(g); }
    bool coin(double p) { return uniform() < p; }
    template <class T> void shuffle(std::vector<T>& v) { std::shuffle(v.begin(), v.end(), g); }
};

struct Timer {
    std::chrono::steady_clock::time_point t0 = std::chrono::steady_clock::now();
    double elapsed() const {
        return std::chrono::duration<double>(std::chrono::steady_clock::now() - t0).count();
    }
};

// 64-bit mixer (splitmix64) used for order-independent solution hashing.
inline uint64_t mix64(uint64_t z) {
    z += 0x9E3779B97F4A7C15ULL;
    z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ULL;
    z = (z ^ (z >> 27)) * 0x94D049BB133111EBULL;
    return z ^ (z >> 31);
}
inline uint64_t edge_hash(int a, int b) {
    if (a > b) std::swap(a, b);
    return mix64(((uint64_t)a << 32) | (uint64_t)b);
}

constexpr double EPS = 1e-9;
