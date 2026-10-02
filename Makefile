SHELL := /bin/bash

.PHONY: install test lint typecheck security check readme build clean

VENV_PATH := $(HOME)/.virtualenvs/kind
PYTHON ?= python3  # the interpreter the venv is built from (CI: the matrix version)

install:
	uv venv --allow-existing --python $(PYTHON) $(VENV_PATH)
	uv pip install --python $(VENV_PATH)/bin/python -e .[dev,visual] -e ./scheduler

test:
	$(VENV_PATH)/bin/python -m pytest

lint:  # pyflakes, not ruff: ~100 KB instead of ~12 MB, and it catches what matters here (unused, undefined, redefined)
	$(VENV_PATH)/bin/python -m pyflakes kind tests scheduler

typecheck:
	$(VENV_PATH)/bin/python -m mypy kind scheduler/kind_scheduler

security:  # static security scan (bandit); config in pyproject [tool.bandit]
	$(VENV_PATH)/bin/python -m bandit -q -c pyproject.toml -r kind scheduler/kind_scheduler

check: lint typecheck security test

readme:  # the PyPI readme: README.md with repository-relative links made absolute
	$(VENV_PATH)/bin/python tools/update.py --input-md README.md --output-md docs/package/README.md --repo https://github.com/ikko/kind/blob/master/

build:
	uv build && uv build scheduler

clean:
	rm -rf dist build *.egg-info
