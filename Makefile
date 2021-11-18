.PHONY: clean clean-test clean-pyc clean-build servedocs help
.DEFAULT_GOAL := help

.INTERMEDIATE:

define BROWSER_PYSCRIPT
import os, webbrowser, sys

from urllib.request import pathname2url

webbrowser.open("file://" + pathname2url(os.path.abspath(sys.argv[1])))
endef
export BROWSER_PYSCRIPT

define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	match = re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT

BROWSER := python -c "$$BROWSER_PYSCRIPT"




help:
	@python -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

clean: clean-build clean-pyc clean-test clean-lint ## remove all build, test, coverage and Python artifacts


clean-build: ## remove build artifacts
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +


clean-pyc: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +


clean-test: ## remove pytest artifacts
	rm -fr .pytest_cache .benchmarks .hypothesis

clean-lint: ## remove pytest artifacts
	rm -fr .linter_reports


lint/flake8: ## check style with flake8
	@if [ ! -d ".linter_reports" ]; then mkdir .linter_reports; fi
	@if [ -d ".linter_reports/flake-report" ]; then rm -rf .linter_reports/flake-report; fi
	$(info ************  RUNNING flake8 ************)
	flake8 --config=.linter_cfg/.flake8 flee/ multiscale/ tests/ || exit 0


lint/isort: ## check import module style with isort
	@if [ ! -d ".linter_reports" ]; then mkdir .linter_reports; fi
	$(info ************  RUNNING isort ************)		
	isort --settings-path=.linter_cfg/.isort.cfg --profile hug --check --diff --filter-files flee/ multiscale/ tests/ 2>&1 | tee .linter_reports/isort_report.txt || exit 0


lint/pylint: ## check code-style with pylint
	@if [ ! -d ".linter_reports" ]; then mkdir .linter_reports; fi	
	$(info ************  RUNNING pylint ************)	
	pylint --rcfile=.linter_cfg/.pylintrc --output-format=json:somefile,colorized flee/ multiscale/run_mscale.py tests/  2>&1 | tee .linter_reports/pylint_report.txt || exit 0
	@rm somefile



lint/black: ## check style with black
	@if [ ! -d ".linter_reports" ]; then mkdir .linter_reports; fi
	$(info ************  RUNNING black ************)	
	black  --config=.linter_cfg/.black flee/ multiscale/ tests/ > .linter_reports/black_report.ansi  || exit 0


lint: lint/flake8 lint/black lint/isort lint/black lint/pylint ## check all lint styles


test: ## run pytests quickly with the default Python
	$(info ************  RUNNING pytest ************)		
	python3 -m pytest -c=.linter_cfg/.pytest.ini -x


servedocs: ## generate MkDocs HTML documentation, including API docs, watching for changes
	mkdocs serve


install: clean ## install the package to the active Python's site-packages
	python setup.py install
