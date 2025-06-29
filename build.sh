#!/usr/bin/env bash
# build.sh

# Upgrade pip and install build tools first
pip install --upgrade pip setuptools wheel

# Install your requirements
pip install -r requirements.txt