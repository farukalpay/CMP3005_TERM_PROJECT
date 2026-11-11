"""Python tooling of the MediDrone CVRP project (CMP3005, Fall 2026-27).

Modules
-------
vrpio      : reading/writing CVRPLIB-format instances (+ MediDrone extension)
generate   : team seed, MediDrone team instance, tiny instances
exact      : exact solvers for tiny instances (Held-Karp + set-partition DP, MILP)
checker    : independent feasibility checker for every reported solution
istanbul   : real-geography instance from OpenStreetMap health facilities
style      : shared matplotlib style for all figures

Author: Faruk Alpay (2267273) - own implementation.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
