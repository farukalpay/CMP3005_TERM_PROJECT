"""Shared helpers for the experiment scripts: paths, instance sets, parallel runner.

Every run is one call of the C++ binary that writes one JSON file.  Existing,
valid JSON files are skipped, so every script is resumable and idempotent.
"""
from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
BIN = ROOT / "solver" / "bin" / "medidrone"
RAW = ROOT / "results" / "raw"
SEEDS = list(range(1, 11))                 # evaluation seeds (10 runs per instance)
TUNE_SEEDS = [101, 102, 103, 104, 105]     # tuning seeds (disjoint from evaluation)
WORKERS = int(os.environ.get("MEDIDRONE_WORKERS", "8"))

TEAM = ROOT / "data/medidrone/MediDrone-7273.vrp"
IST = ROOT / "data/istanbul/MediDrone-IST-7273.vrp"
MAIN_INSTANCES = {   # name -> (path, time budget in seconds), budgets as in Task 7
    "A-n32-k5": (ROOT / "data/cvrplib/A/A-n32-k5.vrp", 30),
    "A-n45-k6": (ROOT / "data/cvrplib/A/A-n45-k6.vrp", 30),
    "A-n60-k9": (ROOT / "data/cvrplib/A/A-n60-k9.vrp", 60),
    "A-n80-k10": (ROOT / "data/cvrplib/A/A-n80-k10.vrp", 60),
    "MediDrone-7273": (TEAM, 60),
    "MediDrone-IST-7273": (IST, 60),
}
# published best-known solutions (CVRPLIB) used for the gap
BKS = {"A-n32-k5": 784, "A-n45-k6": 944, "A-n60-k9": 1354, "A-n80-k10": 1763}


def rel(p: Path) -> str:
    return str(Path(p).resolve().relative_to(ROOT))


def valid_json(p: Path) -> bool:
    try:
        json.loads(p.read_text())
        return True
    except Exception:
        return False


def run_jobs(jobs, workers: int = WORKERS, label: str = ""):
    """jobs: list of (out_path, [args...]) for `medidrone`. Runs in parallel, skips done jobs."""
    todo = [(o, a) for o, a in jobs if not (Path(o).exists() and valid_json(Path(o)))]
    print(f"[{label}] {len(jobs)} jobs, {len(jobs) - len(todo)} cached, {len(todo)} to run on {workers} workers",
          flush=True)
    t0 = time.time()

    def one(job):
        out, args = job
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        tmp = Path(str(out) + ".tmp")
        r = subprocess.run([str(BIN), *map(str, args), "--out", str(tmp)], capture_output=True, text=True, cwd=ROOT)
        if r.returncode != 0:
            raise RuntimeError(f"{args}: {r.stderr}")
        tmp.replace(out)
        return out

    done = 0
    with ThreadPoolExecutor(workers) as ex:
        futs = [ex.submit(one, j) for j in todo]
        for f in as_completed(futs):
            f.result()
            done += 1
            if done % max(1, len(todo) // 20) == 0 or done == len(todo):
                print(f"  [{label}] {done}/{len(todo)} done ({time.time() - t0:.0f}s)", flush=True)


def hardware():
    info = dict(platform=platform.platform(), python=platform.python_version(), machine=platform.machine())
    try:
        info["cpu"] = subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"], capture_output=True,
                                     text=True).stdout.strip()
        info["cores"] = subprocess.run(["sysctl", "-n", "hw.physicalcpu"], capture_output=True, text=True).stdout.strip()
        info["mem_gb"] = int(subprocess.run(["sysctl", "-n", "hw.memsize"], capture_output=True,
                                            text=True).stdout.strip()) / 2 ** 30
    except Exception:
        pass
    try:
        info["compiler"] = subprocess.run(["c++", "--version"], capture_output=True, text=True).stdout.splitlines()[0]
    except Exception:
        pass
    return info


def load_runs(pattern: str):
    out = []
    for p in sorted(RAW.glob(pattern)):
        if p.suffix == ".json":
            r = json.loads(p.read_text())
            r["_file"] = rel(p)
            out.append(r)
    return out

# Final parameter settings (chosen from the tuning study, exp_tune.py; see report Sec. 6)
PARAMS = {
    "ts": ["--tmin", 10, "--tmax", 25, "--nbr", 20, "--delta", 0.3],
    "ga": ["--pop", 100, "--pc", 0.9, "--pm", 1.0],
    "ma": ["--pop", 30, "--pc", 1.0, "--pm", 0.1, "--pls", 0.5, "--nbr", 20],
    "cw": [],
}
