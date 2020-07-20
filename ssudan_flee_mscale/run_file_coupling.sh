#!/bin/bash

export PYTHONPATH="$(dirname "$PWD")"

rm -rf out/file/*
mkdir -p out/file/coupled
mkdir -p out/file/macro
mkdir -p out/file/micro

python3 ssudan_flee_mscale.py --submodel macro --coupling_type file --end_time 5 2>macro-out &
python3 ssudan_flee_mscale.py --submodel micro --coupling_type file --end_time 5 2>micro-out &

wait
