#!/bin/bash
export PYTHONPATH="$(dirname "$PWD")"

#-------------------------------------------------------
#             set global variables
#-------------------------------------------------------
NUM_INSTANCES=3
cores=1
# INPUT_DATA_DIR="ssudan-mscale"
INPUT_DATA_DIR="ssudan-mscale-test"
RUN_PYTHON_FILE="run_mscale.py"

LOG_EXCHANGE_DATA="True"
COUPLING_TYPE="muscle3"
YMMSL_TEMPLATE_FILE="macro_micro_template.ymmsl"
YMMSL_FILE="macro_micro.ymmsl"
WEATHER_COUPLING="False"

#-------------------------------------------------------
#             parse input arguments
#-------------------------------------------------------
#cores=${cores:-1}
while [ $# -gt 0 ]; do
  if [ "$1" == "-h" ] || [ "$1" == "--help" ]; then
    echo -e "\nUsage:"
    echo -e "\t ./run_muscle3_coupling.sh < --cores N > < --NUM_INSTANCES M >\n"
    exit 1
  fi
  if [[ $1 == *"--"* ]]; then
      param="${1/--/}"
      if [ -n "${!param}" ]; then
      	declare $param="$2"
      else
      	echo -e "\nError !!! Input arg --$param is not valid\n" 
        echo -e "you can use -h or --help option to see the valid input arguments\n"
      	exit 1
      fi
  fi
  shift
done

#-------------------------------------------------------
#             convert to lowercase
#-------------------------------------------------------
function covert_to_lowercase()
{
   echo $(echo "$1" | tr "[:upper:]" "[:lower:]")
}

LOG_EXCHANGE_DATA=$(covert_to_lowercase $LOG_EXCHANGE_DATA)
COUPLING_TYPE=$(covert_to_lowercase $COUPLING_TYPE)
WEATHER_COUPLING=$(covert_to_lowercase $WEATHER_COUPLING)


#-------------------------------------------------------
#             set run_command variable
#-------------------------------------------------------
function set_run_command()
{
  run_command=""  
  if [ "$cores" -gt "1" ];
  then
    run_command="mpirun -n $cores python3"
  else
    run_command="python3"
  fi
}

set_run_command

#-------------------------------------------------------
#             clean output directory
#-------------------------------------------------------
if [ $WEATHER_COUPLING = "true" ];
then
  rm -rf out/weather/$COUPLING_TYPE/*
  mkdir -p out/weather/$COUPLING_TYPE/coupled
  mkdir -p out/weather/$COUPLING_TYPE/macro
  mkdir -p out/weather/$COUPLING_TYPE/micro
  mkdir -p out/weather/$COUPLING_TYPE/log_exchange_data
  mkdir -p out/weather/$COUPLING_TYPE/plot_exchange_data
else
  rm -rf out/$COUPLING_TYPE/*
  mkdir -p out/$COUPLING_TYPE/coupled
  mkdir -p out/$COUPLING_TYPE/macro
  mkdir -p out/$COUPLING_TYPE/micro
  mkdir -p out/$COUPLING_TYPE/log_exchange_data
  mkdir -p out/$COUPLING_TYPE/plot_exchange_data
fi

#-------------------------------------------------------
#             create input ymmsl from template
#-------------------------------------------------------
# - copy ymmsl template file
cp $YMMSL_TEMPLATE_FILE $YMMSL_FILE 
# - set number of INSTANCEs into ymmsl file for both macro and micro model 
sed -i "s#NUM_INSTANCES#$NUM_INSTANCES#g" $YMMSL_FILE


#-------------------------------------------------------
#             return common input arguments
#-------------------------------------------------------
function ret_common_args()
{
  local common_args="--data_dir=$INPUT_DATA_DIR \
    --log_exchange_data $LOG_EXCHANGE_DATA \
    --instance_index $i \
    --coupling_type $COUPLING_TYPE \
    --num_instances $NUM_INSTANCES \
    --weather_coupling $WEATHER_COUPLING"
    echo $common_args
}



start_time="$(date -u +%s.%N)"

# load ymmsl file by muscle manager
muscle_manager $YMMSL_FILE &
manager_pid=$!

i=-1 # we set instance_index=-1 for muscle submodels manager
common_args="$(ret_common_args)"

# manager executed only by 1 cores not in parallel
python3 $RUN_PYTHON_FILE --submodel=macro_manager --muscle-instance=macro_manager $common_args &

python3 $RUN_PYTHON_FILE --submodel=micro_manager --muscle-instance=micro_manager $common_args &


# index should be started from 0
for i in $(seq 0 $(($NUM_INSTANCES-1)))
do
  common_args="$(ret_common_args)"

  $run_command $RUN_PYTHON_FILE --submodel=macro --muscle-instance=macro[$i] $common_args &
  $run_command $RUN_PYTHON_FILE --submodel=micro --muscle-instance=micro[$i] $common_args &
done


touch muscle3_manager.log
tail -f muscle3_manager.log --pid=${manager_pid}

wait


end_time="$(date -u +%s.%N)"
elapsed="$(bc <<<"$end_time-$start_time")"

#-------------------------------------------------------
#             move muscle3 log files to out/muscle3
#-------------------------------------------------------
mv muscle3*.log out/muscle3/


#-------------------------------------------------------
#             reporting
#-------------------------------------------------------
#printf '=%.0s' {1..70}
for i in {1..70}; do echo -n =; done
echo -e "\nExecuted commands :"


i=-1 # we set instance_index=-1 for muscle submodels manager
common_args="$(ret_common_args)"
# manager executed only by 1 cores not in parallel
echo -e "\t python3 $RUN_PYTHON_FILE --submodel=macro_manager --muscle-instance=macro_manager $common_args"
echo -e "\t python3 $RUN_PYTHON_FILE --submodel=micro_manager --muscle-instance=micro_manager $common_args"

for i in $(seq 0 $(($NUM_INSTANCES-1)))
do
  common_args="$(ret_common_args)"
  echo -e "\t $run_command $RUN_PYTHON_FILE --submodel=macro --muscle-instance=macro[$i] $common_args"  
  echo -e "\t $run_command $RUN_PYTHON_FILE --submodel=micro --muscle-instance=micro[$i] $common_args"
done  


echo -e "\n\nTotal Executing Time = $elapsed seconds\n" 
