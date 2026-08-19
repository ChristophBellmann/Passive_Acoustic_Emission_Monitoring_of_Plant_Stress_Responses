# Paper build — run from src/characterization/paper/
PYTHON = ../.venv/bin/python
LATEX  = pdflatex
BIBTEX = bibtex

all: figures paper

figures:
	MPLCONFIGDIR=/tmp/matplotlib $(PYTHON) generate_figures.py

paper: main.tex paper_stats.tex figures/fig1_system.pdf
	$(LATEX)  -interaction=nonstopmode main
	-$(BIBTEX) main   # manual thebibliography: bibtex is optional, ignore its exit code
	$(LATEX)  -interaction=nonstopmode main
	$(LATEX)  -interaction=nonstopmode main

clean:
	rm -f *.aux *.bbl *.blg *.log *.out *.toc

.PHONY: all figures paper clean
