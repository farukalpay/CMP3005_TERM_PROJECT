"""Reading and writing CVRP instances in CVRPLIB (TSPLIB) format.

Own implementation, written independently of the C++ parser so that the
feasibility checker does not share code with the solver.

Supported EDGE_WEIGHT_TYPE values
    EUC_2D    Euclidean distance rounded with nint() (TSPLIB / CVRPLIB convention)
    EXACT_2D  Euclidean distance, no rounding (our MediDrone instances)
MediDrone extension keys: VEHICLES, CROSSING_PENALTY and SIDE_SECTION.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np


@dataclass
class Instance:
    name: str
    n: int                      # number of customers; node 0 is the depot
    Q: int                      # capacity
    K: int                      # fleet size
    xy: np.ndarray              # (n+1, 2) coordinates, row 0 = depot
    q: np.ndarray               # (n+1,) demands, q[0] = 0
    rounded: bool = True
    P: float = 0.0              # crossing penalty
    side: np.ndarray | None = None
    comment: str = ""
    meta: dict = field(default_factory=dict)
    _D: np.ndarray | None = None

    @property
    def D(self) -> np.ndarray:
        if self._D is None:
            self._D = distance_matrix(self.xy, self.rounded, self.P, self.side)
        return self._D

    def route_cost(self, route) -> float:
        if len(route) == 0:
            return 0.0
        D = self.D
        path = [0, *route, 0]
        return float(sum(D[a, b] for a, b in zip(path[:-1], path[1:])))

    def cost(self, routes) -> float:
        return float(sum(self.route_cost(r) for r in routes))


def distance_matrix(xy, rounded=True, P=0.0, side=None) -> np.ndarray:
    diff = xy[:, None, :] - xy[None, :, :]
    E = np.sqrt((diff ** 2).sum(-1))
    if rounded:
        E = np.floor(E + 0.5)
    if P and side is not None:
        E = E + P * (side[:, None] != side[None, :])
    return E


def read_instance(path, fleet: int | None = None) -> Instance:
    """Parse a CVRPLIB file. fleet=None infers K, fleet=0 means unlimited (K=n)."""
    path = Path(path)
    hdr, coords, dem, sides, depots = {}, {}, {}, {}, []
    section = None
    for raw in path.read_text().splitlines():
        line = raw.strip().strip('"')
        if not line:
            continue
        up = line.upper()
        if up == "EOF":
            break
        if up.endswith("_SECTION") and ":" not in line:
            section = up
            continue
        if ":" in line and line[0].isalpha():
            k, v = line.split(":", 1)
            hdr[k.strip().upper()] = v.strip().strip('"').strip()
            section = None
            continue
        tok = line.split()
        if section == "NODE_COORD_SECTION":
            coords[int(tok[0])] = (float(tok[1]), float(tok[2]))
        elif section == "DEMAND_SECTION":
            dem[int(tok[0])] = int(tok[1])
        elif section == "SIDE_SECTION":
            sides[int(tok[0])] = int(tok[1])
        elif section == "DEPOT_SECTION":
            depots += [int(t) for t in tok if int(t) >= 0]
    ewt = hdr.get("EDGE_WEIGHT_TYPE", "EUC_2D").upper()
    if ewt not in ("EUC_2D", "EXACT_2D"):
        raise ValueError(f"unsupported EDGE_WEIGHT_TYPE {ewt}")
    depot = depots[0] if depots else min(coords)
    ids = [depot] + sorted(i for i in coords if i != depot)
    xy = np.array([coords[i] for i in ids], dtype=float)
    q = np.array([0] + [dem[i] for i in ids[1:]], dtype=int)
    side = np.array([sides[i] for i in ids], dtype=int) if sides else None
    name = hdr.get("NAME", path.stem)
    Q = int(hdr["CAPACITY"])
    n = len(ids) - 1
    if fleet is not None and fleet > 0:
        K = fleet
    elif fleet == 0:
        K = n
    elif "VEHICLES" in hdr:
        K = int(hdr["VEHICLES"])
    elif (m := re.search(r"-k(\d+)", name)):
        K = int(m.group(1))
    elif (m := re.search(r"trucks: *(\d+)", hdr.get("COMMENT", ""))):
        K = int(m.group(1))
    else:
        K = math.ceil(q.sum() / Q)
    return Instance(name=name, n=n, Q=Q, K=K, xy=xy, q=q, rounded=(ewt == "EUC_2D"),
                    P=float(hdr.get("CROSSING_PENALTY", 0.0)), side=side,
                    comment=hdr.get("COMMENT", ""))


def write_instance(path, inst: Instance, fmt: str = "{:.4f}") -> None:
    """Write an instance (EXACT_2D unless inst.rounded) incl. the MediDrone extension."""
    L = [f"NAME : {inst.name}"]
    if inst.comment:
        L.append(f"COMMENT : {inst.comment}")
    L += ["TYPE : CVRP", f"DIMENSION : {inst.n + 1}",
          f"EDGE_WEIGHT_TYPE : {'EUC_2D' if inst.rounded else 'EXACT_2D'}",
          f"CAPACITY : {inst.Q}", f"VEHICLES : {inst.K}"]
    if inst.P:
        L.append(f"CROSSING_PENALTY : {inst.P:g}")
    L.append("NODE_COORD_SECTION")
    for i, (x, y) in enumerate(inst.xy):
        L.append(f"{i + 1} {fmt.format(x)} {fmt.format(y)}")
    L.append("DEMAND_SECTION")
    for i, d in enumerate(inst.q):
        L.append(f"{i + 1} {int(d)}")
    if inst.side is not None:
        L.append("SIDE_SECTION")
        for i, s in enumerate(inst.side):
            L.append(f"{i + 1} {int(s)}")
    L += ["DEPOT_SECTION", "1", "-1", "EOF"]
    Path(path).write_text("\n".join(L) + "\n")


def read_bks(sol_path) -> float | None:
    """Best-known cost from a CVRPLIB .sol file ('Cost X' line, or first line for X set)."""
    p = Path(sol_path)
    if not p.exists():
        return None
    lines = [l.strip() for l in p.read_text().splitlines() if l.strip()]
    for l in lines:
        if l.lower().startswith("cost"):
            return float(l.split()[1])
    try:
        return float(lines[0])
    except (ValueError, IndexError):
        return None


def read_sol_routes(sol_path) -> list[list[int]] | None:
    """Routes from a CVRPLIB .sol file ('Route #k: a b c'); customer ids are 1..n."""
    p = Path(sol_path)
    if not p.exists():
        return None
    R = []
    for l in p.read_text().splitlines():
        if l.lower().startswith("route"):
            R.append([int(t) for t in l.split(":", 1)[1].split()])
    return R or None
