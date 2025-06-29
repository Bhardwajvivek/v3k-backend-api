#!/usr/bin/env bash
set -o errexit

python -m pip install --upgrade pip
pip install --no-build-isolation setuptools==69.5.1 wheel==0.42.0
pip install --no-build-isolation -r requirements.txt