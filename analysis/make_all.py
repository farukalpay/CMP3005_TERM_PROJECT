"""Regenerate every figure and table of the report from results/raw (no solver runs)."""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = ["make_tables", "fig_instances", "fig_complexity", "fig_routes", "fig_convergence", "fig_psweep",
           "fig_sensitivity", "fig_stn", "fig_extended", "fig_osc", "make_text"]

if __name__ == "__main__":
    for s in sys.argv[1:] or SCRIPTS:
        print("==>", s, flush=True)
        subprocess.run([sys.executable, str(HERE / f"{s}.py")], check=True, cwd=HERE)
