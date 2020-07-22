#!/bin/bash

export PYTHONPATH="$(dirname "$PWD")"

rm -rf out/file/*
mkdir -p out/file/coupled
mkdir -p out/file/macro
mkdir -p out/file/micro

python3 run_mscale.py -i $1 --submodel macro --coupling_type file --end_time 5 1>macro-out 2>macro-err &
python3 run_mscale.py -i $1 --submodel micro --coupling_type file --end_time 5 1>micro-out 2>micro-err &

wait
