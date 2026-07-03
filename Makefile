.PHONY: all setup download build analyze figures dashboard clean

# AI Labor Impact Observatory — reproducible pipeline
# `make all` rebuilds everything from raw data through final outputs.

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
DBT := $(VENV)/bin/dbt
DBT_DIR := warehouse/dbt

all: download build analyze figures dashboard

setup:
	python3.12 -m venv $(VENV)
	$(PIP) install -e .

download:
	$(PYTHON) src/ingest.py

build:
	cd $(DBT_DIR) && ../../$(DBT) run
	cd $(DBT_DIR) && ../../$(DBT) test

analyze:
	$(PYTHON) analysis/01_descriptives.py > reports/descriptives.txt
	$(PYTHON) analysis/02_regressions.py > reports/regressions.txt

figures:
	$(PYTHON) analysis/03_figures.py

dashboard:
	$(PYTHON) analysis/04_dashboard.py

clean:
	rm -rf warehouse/*.duckdb warehouse/*.duckdb.wal
	rm -rf $(DBT_DIR)/target $(DBT_DIR)/logs
	rm -rf figures/*.png figures/*.html
	rm -f dashboard/index.html
