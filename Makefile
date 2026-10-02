SHELL := /bin/bash

.PHONY: install test lint build clean

VENV_PATH := $(HOME)/.virtualenvs/kind

install:
	uv venv --allow-existing $(VENV_PATH)
	uv pip install --python $(VENV_PATH)/bin/python -e .[dev,visual]

test:
	PYTHONPATH=. $(VENV_PATH)/bin/python -m pytest

lint:
	echo "was 'ruff check --exit-zero . ' but because big disk size (11.6Mb around??) footprint"

build:
	uv build

clean:
	rm -rf dist build *.egg-info
