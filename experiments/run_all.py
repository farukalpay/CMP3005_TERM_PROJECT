"""Run every experiment stage in order (resumable). Usage: python experiments/run_all.py [stage ...]"""
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
STAGES = ["exp_tune", "exp_complexity", "exp_main", "exp_psweep", "exp_extended", "exp_xset", "exp_long", "exp_ablation"]

if __name__ == "__main__":
    stages = sys.argv[1:] or STAGES
    for s in stages:
        t = time.time()
        print(f"=== {s}", flush=True)
        subprocess.run([sys.executable, str(HERE / f"{s}.py")], check=True, cwd=HERE.parent)
        print(f"=== {s} finished in {time.time() - t:.0f}s", flush=True)
