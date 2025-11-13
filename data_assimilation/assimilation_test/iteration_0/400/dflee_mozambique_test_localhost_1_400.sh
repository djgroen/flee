#!/bin/bash

cd /home/laszlo/Documents/code/FabSim3/localhost_exe/FabSim/results/dflee_mozambique_test_localhost_1/RUNS/400
true

# copy files from config folder
config_dir=/home/laszlo/Documents/code/FabSim3/localhost_exe/FabSim/config_files/dflee_mozambique_test
rsync -pthrvz --inplace --exclude SWEEP $config_dir/* .

# copy files from SWEEP folder
rsync -pthrvz --inplace $config_dir/SWEEP/400/ .

# user run_prefix_commands
source ~/.bashrc 
source /home/laszlo/Documents/code/FabSim3/VirtualEnv/bin/activate

export FLEE_TYPE_CHECK=False

if [ -z "/home/laszlo/Documents/code/flee" ]
then
	echo "Please set $flee_location in your deploy/machines_user.yml file."
else
	export PYTHONPATH=/home/laszlo/Documents/code/flee:$PYTHONPATH
fi

/usr/bin/env > env.log

time python3 /home/laszlo/Documents/code/flee/runscripts/run.py input_csv source_data 5 simsetting.yml > out.csv

run_UNHCR_uncertainty="False"
# covert to lowercase
run_UNHCR_uncertainty=$(echo "$run_UNHCR_uncertainty" | tr "[:upper:]" "[:lower:]")

if [ "$run_UNHCR_uncertainty" = "true" ]
then
	python3 run_UNHCR_uncertainty.py input_csv source_data 5 simsetting.csv > out_uncertainty.csv
fi
