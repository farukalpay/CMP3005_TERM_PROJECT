"""Independent feasibility checker (Section 5, "Code" deliverable).

For every result JSON produced by the C++ solver it
  * re-reads the instance with the Python parser (no code shared with C++),
  * recomputes all distances from the coordinates (nint rounding for EUC_2D,
    exact for EXACT_2D, plus the crossing penalty),
  * checks: every customer exactly once, no route above capacity Q,
    at most K routes, and reported cost == recomputed cost.

Usage:  python -m medidrone.checker results/raw [--csv results/validation.csv]
Own implementation.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from functools import lru_cache
from pathlib import Path

from . import ROOT
from .vrpio import read_instance


@lru_cache(maxsize=None)
def _instance(path: str, K: int):
    saved = Path(path)
    if saved.is_absolute():
        # Old logs contain the experiment machine's absolute checkout path.
        # Prefer this checkout's data, so validation also works after a clone.
        parts = saved.parts
        candidates = [ROOT.joinpath(*parts[i:]) for i, part in enumerate(parts) if part == "data"]
        local = next((p for p in candidates if p.is_file()), None)
        resolved = local if local is not None else saved
    else:
        resolved = ROOT / saved
    inst = read_instance(resolved)
    inst.K = K          # fleet size actually used by the run (e.g. unlimited for X)
    return inst


def check(inst, routes, reported=None, tol=1e-6):
    """Return (ok, reason, recomputed_cost)."""
    seen = {}
    for r in routes:
        for v in r:
            if not 1 <= v <= inst.n:
                return False, f"invalid customer {v}", None
            seen[v] = seen.get(v, 0) + 1
    if any(c > 1 for c in seen.values()):
        return False, "customer visited more than once", None
    if len(seen) != inst.n:
        return False, f"{inst.n - len(seen)} customers not visited", None
    used = [r for r in routes if r]
    for r in used:
        load = int(inst.q[r].sum())
        if load > inst.Q:
            return False, f"route overloaded ({load} > {inst.Q})", None
    if len(used) > inst.K:
        return False, f"{len(used)} routes > K = {inst.K}", None
    cost = inst.cost(used)
    if reported is not None and abs(cost - reported) > tol * max(1.0, abs(cost)):
        return False, f"cost mismatch: reported {reported} vs recomputed {cost}", cost
    return True, "", cost


def check_file(path: Path):
    rec = json.loads(path.read_text())
    if rec.get("cost") is None or not rec.get("routes"):
        # the run found no fleet-feasible solution and reported none (e.g. GA/MA on P-n55-k15)
        return dict(file=str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),
                    instance=rec["instance"], alg=rec["alg"], seed=rec.get("seed"), reported=None, recomputed=None,
                    ok=True, reason="no solution reported", none=True, status="no_solution")
    inst = _instance(rec["path"], rec["K"])
    ok, why, cost = check(inst, rec["routes"], rec.get("cost"))
    status = "valid" if ok else "invalid"
    if not ok and rec.get("alg") == "cw" and rec.get("feasible") is False and "routes > K =" in why:
        # Verify coverage/capacity/cost too, but never count this as fleet-feasible.
        loose = _instance(rec["path"], 10 ** 9)
        consistent, other, cost = check(loose, rec["routes"], rec.get("cost"))
        if consistent:
            status = "fleet_infeasible_baseline"
        else:
            why = other
    return dict(file=str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),
                instance=rec["instance"], alg=rec["alg"], seed=rec.get("seed"),
                reported=rec.get("cost"), recomputed=cost, ok=ok, reason=why, none=False, status=status)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--csv", default=None)
    a = ap.parse_args()
    files = []
    for p in a.paths:
        p = Path(p)
        files += sorted(p.rglob("*.json")) if p.is_dir() else [p]
    files = [f for f in files if f.parent.name != "complexity"]      # timing records carry no solutions
    rows = [check_file(f) for f in files]
    if not rows:
        ap.error("no saved solution records found")
    bad = [r for r in rows if r["status"] == "invalid"]
    none = sum(r["none"] for r in rows)
    baselines = sum(r["status"] == "fleet_infeasible_baseline" for r in rows)
    valid = sum(r["status"] == "valid" for r in rows)
    if a.csv:
        with open(a.csv, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
    print(f"checked {len(rows)} records: {valid} fleet-feasible solutions, "
          f"{baselines} explicitly fleet-infeasible CW baselines, {len(bad)} unexpected invalid outputs, "
          f"{none} runs reporting no solution")
    for r in bad[:20]:
        print("  INVALID", r["file"], r["reason"])
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
