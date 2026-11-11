.DEFAULT_GOAL := help
PYTHON ?= python3

.PHONY: help solver assets report check package
help:
	@echo "make assets  - rebuild coursework tables/plots from saved results only"
	@echo "make report  - rebuild the simplified report PDF (no experiments)"
	@echo "make check   - independently check saved main/tiny solutions"
	@echo "make solver  - compile the C++17 solver"
	@echo "make package - build the current report + source ZIP"

solver:
	$(MAKE) -C solver

assets:
	$(PYTHON) analysis/coursework.py

report: assets
	latexmk -pdf -interaction=nonstopmode -halt-on-error -cd report/main.tex
	cp report/main.pdf deliverables/CMP3005_Report_FarukAlpay_2267273.pdf

check:
	$(PYTHON) -m medidrone.checker results/raw/main results/raw/tiny --csv results/coursework/validation.csv

package: report
	$(PYTHON) tools/package_submission.py
