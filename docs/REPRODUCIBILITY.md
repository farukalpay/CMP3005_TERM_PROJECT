# Reproduction and evidence map

All commands below run from the project root. The default path uses completed experiments. It does not regenerate instances or rerun heuristics, timing studies, tuning or exact solvers.

## 1. Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

The pinned libraries require Python 3.11+ (NetworkX excludes Python 3.14.1). Recorded experiments used Python 3.14.2 on Apple M4 Pro, 48 GB RAM, macOS 26.3, Apple clang 17. A LaTeX installation with `latexmk` is needed for the report; a C++17 compiler is only needed for new solver runs.

## 2. Current report, using only saved evidence

```bash
make assets
make check
make report
```

Equivalent commands:

```bash
python3 analysis/coursework.py
python3 -m medidrone.checker results/raw/main results/raw/tiny --csv results/coursework/validation.csv
latexmk -pdf -interaction=nonstopmode -halt-on-error -cd report/main.tex
cp report/main.pdf deliverables/CMP3005_Report_FarukAlpay_2267273.pdf
```

`make report` already runs the asset step. Running `make assets` alone is useful when LaTeX is unavailable. `make check` includes optional MA and real-instance records stored in the same folders, so its record count is greater than the simplified report's 105 CW/GA/TS main records.

The checker resolves historical absolute instance paths against this checkout's `data/` directory. It distinguishes valid plans, explicitly fleet-infeasible CW baselines, unexpected invalid output and runs reporting no solution. Exit code 0 permits the explicitly labelled CW baseline failures; they are never counted as fleet-feasible solutions.

## 3. Every table and figure in the current report

The single exact command for each row is `python3 analysis/coursework.py`.

| Report item | Saved input | Generated output |
|---|---|---|
| Figure 1: team instance | `data/medidrone/MediDrone-7273.vrp` | `figures/coursework/instance.pdf` |
| Figure 2: timing and delta evaluation | `results/raw/complexity/complexity.json` | `figures/coursework/complexity.pdf`; `results/coursework/slopes.csv` |
| Table 1: main comparison | CW/GA/TS records for the five core instances in `results/raw/main/`; cached reference values in `results/summary.json` | `report/coursework/main_table.tex`; `results/coursework/main.csv`, `runs.csv` |
| Table 2: tiny optima and hits | `results/raw/tiny/`; cached exact optima in `results/summary.json` | `report/coursework/tiny_table.tex`; `results/coursework/tiny.csv` |
| Figure 3: convergence | Ten GA and TS traces for A-n45-k6 in `results/raw/main/` | `figures/coursework/convergence.pdf` |
| Figure 4: team routes | Best saved main TS plan for MediDrone-7273 | `figures/coursework/routes.pdf` |
| Figure 5: sensitivity and crossing count | Team tuning logs with `nbr=20` in `results/raw/tune_ts/`; cached `results/psweep_stats.json` | `figures/coursework/sensitivity.pdf`; `results/coursework/sensitivity.csv` |

PNG versions are generated beside every PDF plot. Appendix contribution and source-map tables are authored text in `report/coursework/appendix.tex`, not experimental measurements. `results/coursework/provenance.json` records sources, references, the chosen route seed and the sample-SD convention.

The tiny exact values were already computed by DP and MILP. Asset generation checks their agreement and recounts hits from the ten saved seeds, without recomputing optima. Penalty-sweep summary values are read from the saved analysis; original sweep logs remain in `results/raw/psweep/`.

Convergence uses stepwise best-so-far traces, not linear interpolation between improvements. Curves show medians and interquartile ranges, starting only once all ten runs have a feasible answer. No missing early value is invented.

## 4. Optional new solver runs

These commands perform new optimization. They are not needed to inspect the saved results or rebuild the report.

```bash
make solver
solver/bin/medidrone solve --inst data/cvrplib/A/A-n32-k5.vrp --alg ga --time 30 --seed 1 --pop 100 --pc 0.9 --pm 1.0 --out demo-ga.json
solver/bin/medidrone solve --inst data/cvrplib/A/A-n32-k5.vrp --alg ts --time 30 --seed 1 --tmin 10 --tmax 25 --nbr 20 --delta 0.3 --out demo-ts.json
python3 -m medidrone.checker demo-ga.json demo-ts.json
```

The CLI's GA defaults differ from the final tuned settings, so the settings above are explicit. A fixed wall-clock run can perform different numbers of iterations on a different computer and need not reproduce an identical final cost even with the same seed.

## 5. Optional experiment reruns

Existing valid JSON files are skipped. Missing outputs are computed. Inspect the script before deliberately requesting a fresh experiment; preserve the original evidence.

| Command | Scope |
|---|---|
| `python3 experiments/run_all.py exp_main` | Main runs, tiny runs and two oscillation logs |
| `python3 experiments/run_all.py exp_tune` | TS/GA/MA parameter tuning |
| `python3 experiments/run_all.py exp_complexity` | Timing benchmarks |
| `python3 experiments/run_all.py exp_psweep` | Crossing penalties |
| `python3 experiments/run_all.py` | All original stages, including extension benchmarks |

`MEDIDRONE_WORKERS=8` is the default concurrency for experiment scripts. The complexity study is sequential. Evaluation seeds are 1–10; tuning seeds 101–105. The full scripts include optional MA and real-Istanbul cases as well as the required core.

Instance generation is a separate, deliberate operation:

```bash
python3 -m medidrone.generate --ids 2267273
```

Do not regenerate the existing instance just to view the report. Adding members changes the seed and requires new matching team-instance evidence. There is no need to edit the original raw logs to make them look like a different team.

## 6. Historical research report

```bash
python3 analysis/make_all.py
latexmk -pdf -cd report/research.tex
```

This is the older, wider analysis pipeline. Unlike `coursework.py`, it includes exact-optimum calculations and extra analyses. It writes the old `report/sections/`, `report/tables/` and `figures/` assets, which the simplified report does not input. The old presentation can be rebuilt with the commands in [EXTENSIONS.md](EXTENSIONS.md).

## 7. Local source ZIP

```bash
make package
```

This builds the current report and creates `deliverables/CMP3005_Code_FarukAlpay_2267273.zip`. It includes source, saved data/results, docs and the report. It excludes local backups, historical PDF copies, binaries, LaTeX debris and nested ZIPs. It does not upload anything. `.gitignore` excludes the ZIP from GitHub to avoid storing a second copy of the repository inside itself.
