.PHONY: clean clean-test clean-pyc clean-build docs
.DEFAULT_GOAL := all

define BROWSER_PYSCRIPT
import os, webbrowser, sys

try:
	from urllib import pathname2url
except:
	from urllib.request import pathname2url

webbrowser.open("file://" + pathname2url(os.path.abspath(sys.argv[1])))
endef
export BROWSER_PYSCRIPT

BROWSER := python -c "$$BROWSER_PYSCRIPT"
export VERSION = sterling@`cat .bumpversion.cfg | egrep -o "(\d+\.\d+.\d+)"`

clean: clean-build clean-pyc clean-test clean-docs ## remove all build, test, coverage and Python artifacts

clean-build: ## remove build artifacts
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +
	find . -name '*.egg' -exec rm -f {} +
	rm -f dump.rdb
	rm -f logs.txt

clean-pyc: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test: ## remove test and coverage artifacts
	rm -fr .pytest_cache

clean-docs: ## clean built docs
	rm -fr site/

format: ## format code with black
	poetry run black snoo tests

lint: ## check style with flake8
	poetry run flake8 --max-line-length=88 snoo tests

test: ## run tests quickly with the default Python
	poetry run python -m pytest

docs:
	poetry run mkdocs serve

all: format lint test
