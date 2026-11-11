# Code reading map

Read the main report and the Turkish guide first. Then trace this path:

```text
instance file → parser → distance matrix
                         ↓
                  Clarke–Wright start
                   ↙             ↘
             GA + Split       Tabu Search
                   ↘             ↙
                    result JSON
                         ↓
               independent Python checker
                         ↓
                  saved-run analysis
```

| Read in order | File | What to find |
|---|---|---|
| 1 | `solver/src/instance.hpp`, `instance.cpp` | Inputs, distance convention, capacity, fleet, side labels |
| 2 | `solver/src/solution.hpp`, `solution.cpp` | Route representation, cost and validity |
| 3 | `solver/src/savings.cpp` | Savings order, endpoint and capacity checks |
| 4 | `solver/src/split.cpp` | Start with `split_bellman`; then linear and limited versions |
| 5 | `solver/src/ga.cpp` | Decode, tournament, OX, mutation, replacement and restarts |
| 6 | `solver/src/routes.hpp` | Cached loads, move deltas and applying moves |
| 7 | `solver/src/tabu.cpp` | Removed-edge memory, aspiration, penalty and restarts |
| 8 | `solver/src/main.cpp` | CLI parameters and JSON output |
| 9 | `medidrone/vrpio.py`, `checker.py` | Separate Python parser/evaluator and validation |
| 10 | `experiments/common.py`, `exp_main.py` | Recorded seeds, final settings, budgets, job construction |
| 11 | `analysis/coursework.py` | Convert saved evidence into the current report |

The C++ solver is intentionally unchanged by the documentation revision. It already includes fast Split, fleet-limited decoding and additional move types. The report describes these differences instead of claiming that the implementation is only the simplest classroom version.

## Where the algorithms come from

| Idea | Source |
|---|---|
| Savings construction | Clarke & Wright (1964) |
| Giant tour and Split-based GA | Prins (2004), earlier Split work by Beasley |
| Fast linear Split | Vidal (2016) |
| Order Crossover | Davis (1985) |
| Tabu Search | Glover & Laguna (1997) |
| Candidate lists and overload penalties | Toth & Vigo (2003); Gendreau, Hertz & Laporte (1994); Cordeau et al. (2001) |

Bibliographic entries are in `report/references.bib`; the current report gives its smaller core reading list directly. The code is project-local rather than an imported VRP solver. Older headers saying “own implementation” do not mean it was written without AI assistance. The author developed and researched the project, with ChatGPT/Codex assistance disclosed briefly in the report.

Optional first-reading exclusions: `localsearch.cpp`/MA, `medidrone/istanbul.py`, `approx.py`, search-trajectory analysis and extended benchmark scripts. See [EXTENSIONS.md](EXTENSIONS.md).
