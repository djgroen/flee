#!/bin/bash

export PYTHONPATH="$(dirname "$PWD")"

rm -rf out/*
mkdir -p out/macro
mkdir -p out/micro

#. python/build/venv/bin/activate
muscle_manager macro_micro.ymmsl &

manager_pid=$!

#BINDIR=python
#BINDIR=.

python3 ssudan_flee_mscale.py --submodel macro --coupling_type muscle3 --muscle-instance=macro & 
python3 ssudan_flee_mscale.py --submodel micro --coupling_type muscle3 --muscle-instance=micro & 


touch muscle3_manager.log
tail -f muscle3_manager.log --pid=${manager_pid}

wait
