# Optional extensions and historical material

The current entry point is `report/main.tex` and its `coursework/` inputs. The following material is retained for reference, outside the main reading path.

| Extension | Code / evidence |
|---|---|
| Memetic GA (`ma`) | `solver/src/localsearch.cpp`, `ga.cpp`; saved MA runs |
| Real Istanbul geography | `medidrone/istanbul.py`, `data/istanbul/`, cached OSM data |
| Approximation experiment | `medidrone/approx.py`, `results/itp.json` |
| All 74 A/B/P benchmarks | `experiments/exp_extended.py`, `results/raw/extended/` |
| Large X-set instances | `experiments/exp_xset.py`, `results/raw/xset/` |
| Search trajectories / networks | `analysis/fig_stn.py`, saved snapshots |
| Wider sensitivity and ablation | `exp_tune.py`, `exp_ablation.py`, saved outputs |
| Full theoretical treatment | `report/research.tex`, `report/sections/`, `report/references.bib` |
| Earlier presentation | `slides/slides.tex` and `slides/tikz/` |

The old report's title, claims and extra proofs are not the current course report's scope. The old Beamer source follows that earlier report. The current editable PPTX in `deliverables/` follows the simplified report and includes Turkish speaker notes.

Local historical PDFs and the original ZIP are in `archive/`, excluded from Git. A complete pre-cleanup recovery snapshot is in `.local-backup/`, also excluded. Original solver sources, instances and raw result JSON files are preserved.

To rebuild the **old** presentation deliberately:

```bash
MEDIDRONE_SLIDES=1 python3 analysis/make_all.py
latexmk -pdf -cd slides/tikz/split.tex
latexmk -pdf -cd slides/tikz/moves.tex
latexmk -pdf -cd slides/slides.tex
```

This uses the wider analysis pipeline, which can recompute tiny exact optima. It is not part of the simplified report build.

## Geographic data attribution

- Istanbul health facilities: © OpenStreetMap contributors, ODbL. Cached Overpass snapshot dated 8 November 2026 in the original project.
- District polygons: geoBoundaries gbOpen, CC BY 4.0.
- Benchmarks: CVRPLIB, cached through the ML4CO Hugging Face mirror. Original data attribution and bibliography remain in the research report sources.

The mandatory MediDrone instance is synthetic. It should not be described as real flight-ready Istanbul logistics data.
