# MediDrone Istanbul

CMP3005 Analysis of Algorithms · Fall 2026–2027 · Bahçeşehir University  
**Faruk Alpay — 2267273** · Instructor: Dr. Günet Eroğlu

Plan deliveries from one laboratory to clinics using drones with limited payload. Every clinic must be served once, every drone returns to the laboratory, and crossing the Bosphorus adds a fixed cost. The aim is to minimize total route cost while respecting capacity and fleet size.

This course project compares **Clarke–Wright savings**, a **Genetic Algorithm (GA)** and **Tabu Search (TS)**. The main report focuses on the four required benchmarks and the generated 100-clinic instance. Completed experiments are included.

## Start here

- [Teaching presentation (editable PPTX)](deliverables/CMP3005_Slides_FarukAlpay_2267273.pptx)
- [Türkçe konuşmacı notları](slides/speaker_notes_TR.md)
- [Course report (PDF)](deliverables/CMP3005_Report_FarukAlpay_2267273.pdf)
- [Türkçe anlama ve sözlü savunma rehberi](docs/UNDERSTANDING_TR.md)
- [Assignment requirements and dates](docs/COURSE_REQUIREMENTS.md)
- [Exact reproduction commands and evidence map](docs/REPRODUCIBILITY.md)
- [Code reading map](docs/CODE_MAP.md)

The report uses short explanations and worked examples for the required theory and Split DP. Additional research analyses are documented separately in [Extensions](docs/EXTENSIONS.md).

## Main findings

Saved runs use seeds 1–10 and equal GA/TS wall-clock budgets per instance.

| Instance | GA mean cost | TS mean cost | Reference |
|---|---:|---:|---:|
| A-n32-k5 | 827.0 | 784.0 | 784 |
| A-n45-k6 | 954.9 | 944.0 | 944 |
| A-n60-k9 | 1,396.2 | 1,354.0 | 1,354 |
| A-n80-k10 | 1,818.0 | 1,763.6 | 1,763 |
| MediDrone-7273 | 21,352.2 | 20,725.5 | 20,724.21095* |

*The team reference is the best value found in the saved project runs, not a proven optimum. Benchmark references are published BKS values. Full statistics, including runtime and sample standard deviation, are in [main.csv](results/coursework/main.csv).

Both GA and TS reach the exact optimum in all 90 tiny runs per method. CW exceeds the allowed fleet on A-n45-k6 and the team instance; those outputs are explicitly labelled infeasible. These findings concern these implementations and settings.

## Rebuild the report from saved results

Use Python 3.11 or newer (the recorded experiment environment used 3.14.2; NetworkX excludes 3.14.1). LaTeX with `latexmk` is needed only to rebuild the PDF. Run from the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
make assets
make report
make check
```

- `make assets` rebuilds the report's tables and plots from saved JSON/CSV evidence. It uses cached exact values and **does not run experiments**.
- `make report` rebuilds the assets and the simplified PDF, then updates the copy in `deliverables/`.
- `make check` independently checks saved main/tiny solutions, separating fleet-infeasible CW baselines from feasible plans. It does not optimize routes.
- On Windows, use WSL for these shell and Make commands.

## Compile and try the solver

A C++17 compiler and Make are required. A single demonstration run is separate from rebuilding the report:

```bash
make solver
solver/bin/medidrone solve --inst data/cvrplib/A/A-n32-k5.vrp --alg ts --time 2 --seed 1 --out demo.json
python3 -m medidrone.checker demo.json
```

Algorithms: `cw`, `ga`, `ts`; `ma` is the optional GA with local search. For the tuned GA settings, include `--pop 100 --pc 0.9 --pm 1.0`. All original experiment parameters remain in the saved logs. Full reruns are optional and documented in [REPRODUCIBILITY.md](docs/REPRODUCIBILITY.md).

## Repository layout

| Path | Purpose |
|---|---|
| `solver/src/` | C++ parser, route evaluation, CW, GA, Split and TS |
| `medidrone/` | Python parser/generators, exact methods, independent checker |
| `data/` | Required benchmarks, team and tiny instances, extension data |
| `experiments/` | Scripts that originally produced the saved runs |
| `results/raw/` | Original per-run JSON evidence, preserved |
| `results/all_runs.csv` | Original CSV of all experiment runs |
| `results/coursework/` | Simplified report summaries, validation and provenance |
| `analysis/coursework.py` | Builds only the simplified report's evidence |
| `figures/coursework/` | Report plots in PDF and PNG |
| `report/main.tex`, `report/coursework/` | Current report source |
| `deliverables/` | Current report and locally generated source ZIP |
| `docs/` | Reading guide, requirements and reproduction instructions |

The current 16-slide presentation includes six editable tables, all five report figures, worked algorithm examples and Turkish speaker notes. The original research report and Beamer source are retained as extensions. They are outside the simplified reading path. Local historical copies and build debris are excluded by `.gitignore`.

## Data, implementation and AI assistance

Benchmark files and reference solutions come from CVRPLIB, cached through the [ML4CO mirror](https://huggingface.co/datasets/ML4CO/VRPLIBOriDataset). The team seed is the last four digits of the sole listed student's ID: **7273**. Changing team membership changes the required seed and invalidates the current team-instance identity.

The C++ algorithms are project-local implementations of published methods. No existing VRP solver library produces the reported solutions. SciPy/HiGHS is used for tiny exact checks. Algorithm sources, optional geographic data attribution and AI assistance are described in the report and [code map](docs/CODE_MAP.md). “Own implementation” in older file headers identifies project code, not exclusively unaided human authorship.

The current contributor record lists one student. The announcement requests teams of 3–4; individual-submission approval and registration are not established by this repository. See the [submission checklist](docs/COURSE_REQUIREMENTS.md#before-submission).
