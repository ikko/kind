SHELL := /bin/bash

.PHONY: install test lint build clean

VENV_PATH := $(HOME)/.virtualenvs/kind

install:
	uv venv --allow-existing $(VENV_PATH)
	uv pip install --python $(VENV_PATH)/bin/python -e .[dev,visual]

test:
	$(VENV_PATH)/bin/python -m pytest

lint:  # pyflakes, not ruff: ~100 KB instead of ~12 MB, and it catches what matters here (unused, undefined, redefined)
	$(VENV_PATH)/bin/python -m pyflakes kind tests

build:
	uv build

clean:
	rm -rf dist build *.egg-info
