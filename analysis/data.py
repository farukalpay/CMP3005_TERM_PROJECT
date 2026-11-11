"""Load raw run records (results/raw/**.json) into pandas tables + reference values."""
from __future__ import annotations

import json
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
RAW = ROOT / "results" / "raw"

from medidrone.vrpio import read_bks, read_instance  # noqa: E402

PUBLISHED_BKS = {"B-n50-k8": 1312, "B-n57-k7": 1153}   # official CVRPLIB values (mirror .sol routes differ)
ALGS = ["ga", "ts", "ma"]


def _load(folder, keep_heavy=False):
    rows = []
    for p in sorted((RAW / folder).glob("*.json")):
        r = json.loads(p.read_text())
        if not keep_heavy:
            for k in ("snaps", "osc", "div", "move_hist"):
                r.pop(k, None)
        r["file"] = str(p.relative_to(ROOT))
        rows.append(r)
    return rows


@lru_cache(maxsize=None)
def runs(folder, keep_heavy=False) -> pd.DataFrame:
    df = pd.DataFrame(_load(folder, keep_heavy))
    return df


def bks_for(name: str, path: str | None = None):
    if name in PUBLISHED_BKS:
        return PUBLISHED_BKS[name]
    if path:
        sol = (ROOT / path).with_suffix(".sol")
        b = read_bks(sol)
        if b is not None:
            return b
    return None


@lru_cache(maxsize=None)
def references() -> dict:
    """Best known value per instance: published BKS (CVRPLIB) or, for our own instances,
    the best feasible cost found in ANY run of ANY experiment."""
    best = {}
    for folder in ("main", "long", "tune_ts", "tune_ga", "tune_ma", "psweep", "tiny", "extended", "xset"):
        if not (RAW / folder).exists():
            continue
        for r in _load(folder):
            if not r.get("feasible") or r.get("cost") is None or r.get("alg") == "cw":
                continue
            name = r["instance"]
            for base, P in (("MediDrone-7273", "150"), ("MediDrone-IST-7273", "5")):  # identical matrices
                if name == f"{base}-P{P}":
                    name = base
            best[name] = min(best.get(name, np.inf), r["cost"])
    ref = {}
    for name, v in best.items():
        b = bks_for(name, None)
        ref[name] = v if b is None else b
    return ref


def with_gap(df: pd.DataFrame, use_files=True) -> pd.DataFrame:
    df = df.copy()
    refs = references()
    vals = []
    for _, r in df.iterrows():
        b = bks_for(r["instance"], r.get("path")) if use_files else None
        vals.append(b if b is not None else refs.get(r["instance"], np.nan))
    df["ref"] = vals
    df["gap"] = 100.0 * (df["cost"] - df["ref"]) / df["ref"]
    return df


def instance(path):
    return read_instance(ROOT / path)
