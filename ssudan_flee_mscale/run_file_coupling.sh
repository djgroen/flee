#!/bin/bash

export PYTHONPATH="$(dirname "$PWD")"

rm -rf out/*
mkdir -p out/coupled
mkdir -p out/macro
mkdir -p out/micro

python3 ssudan_flee_mscale.py --submodel macro --coupling_type file &
python3 ssudan_flee_mscale.py --submodel micro --coupling_type file &

wait