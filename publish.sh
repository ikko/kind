#!/usr/bin/env bash

set -e
set -x

twine check dist/*
twine upload dist/*
