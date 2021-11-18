from flee import flee
from flee.datamanager import handle_refugee_data
from flee.datamanager import DataTable  # DataTable.subtract_dates()
from flee import InputGeography
import numpy as np
import flee.postprocessing.analysis as a
import sys
import argparse
import time
import os


def date_to_sim_days(date):
    return DataTable.subtract_dates(date1=date, date2="2010-01-01")


def test_par_seq(end_time=10, last_physical_day=10,
                 parallel_mode="advanced", latency_mode="high_latency",
                 inputdir="test_data/test_input_csv",
                 initialagents=100000,
                 newagentsperstep=1000):
    t_exec_start = time.time()

    e = flee.Ecosystem()

    e.parallel_mode = parallel_mode
    e.latency_mode = latency_mode

    ig = InputGeography.InputGeography()

    ig.ReadLocationsFromCSV(csv_name=os.path.join(inputdir, "locations.csv"))

    ig.ReadLinksFromCSV(csv_name=os.path.join(inputdir, "routes.csv"))

    ig.ReadClosuresFromCSV(csv_name=os.path.join(inputdir, "closures.csv"))

    e, lm = ig.StoreInputGeographyInEcosystem(e=e)

    # print("Network data loaded")

    # d = handle_refugee_data.RefugeeTable(
    #     csvformat="generic",
    #     data_directory=os.path.join("test_data", "test_input_csv", "refugee_data"),
    #     start_date="2010-01-01",
    #     data_layout="data_layout.csv"
    # )

    output_header_string = "Day,"

    camp_locations = e.get_camp_names()

    ig.AddNewConflictZones(e=e, time=0)
    # All initial refugees start in location A.
    e.add_agents_to_conflict_zones(number=initialagents)

    for l in camp_locations:
        output_header_string += "{} sim,{} data,{} error,".format(
            lm[l].name, lm[l].name, lm[l].name
        )

    output_header_string += (
        "Total error,refugees in camps (UNHCR),total refugees (simulation),"
        "raw UNHCR refugee count,refugees in camps (simulation),refugee_debt"
    )

    if e.getRankN(0):
        print(output_header_string)

    # Set up a mechanism to incorporate temporary decreases in refugees
    # raw (interpolated) data from TOTAL UNHCR refugee count only.
    refugees_raw = 0

    t_exec_init = time.time()
    if e.getRankN(0):
        my_file = open("perf.log", "w", encoding="utf-8")
        print("Init time,{}".format(t_exec_init - t_exec_start), file=my_file)

    for t in range(0, end_time):

        if t > 0:
            ig.AddNewConflictZones(e=e, time=t)

        # Determine number of new refugees to insert into the system.
        new_refs = newagentsperstep
        refugees_raw += new_refs

        # Insert refugee agents
        e.add_agents_to_conflict_zones(number=new_refs)

        e.refresh_conflict_weights()
        t_data = t

        e.enact_border_closures(time=t)
        e.evolve()

        # Calculation of error terms
        errors = []
        abs_errors = []

        camps = []
        for i in camp_locations:
            camps += [lm[i]]

        # calculate retrofitted time.
        refugees_in_camps_sim = 0
        for c in camps:
            refugees_in_camps_sim += c.numAgents

        output = "%s" % t

        for i in range(0, len(camp_locations)):
            output += ",{}".format(lm[camp_locations[i]].numAgents)

        if refugees_raw > 0:
            output += ",{},{}".format(e.numAgents(), refugees_in_camps_sim)
        else:
            output += ",0,0"

        if e.getRankN(t):
            print(output)

    t_exec_end = time.time()
    if e.getRankN(0):
        my_file = open("perf.log", "a", encoding="utf-8")
        print("Time in main loop,{}".format(t_exec_end - t_exec_init), file=my_file)


if __name__ == "__main__":
    end_time = 10
    last_physical_day = 10

    parser = argparse.ArgumentParser(
        description="Run a parallel Flee benchmark.")
    parser.add_argument("-p", "--parallelmode", type=str, default="advanced",
                        help="Parallelization mode (advanced, classic, cl-hilat OR adv-lowlat)")
    parser.add_argument("-N", "--initialagents", type=int, default=100000,
                        help="Number of agents at the start of the simulation.")
    parser.add_argument("-d", "--newagentsperstep", type=int, default=1000,
                        help="Number of agents added per time step.")
    parser.add_argument("-t", "--simulationperiod", type=int, default=10,
                        help="Duration of the simulation in days.")
    parser.add_argument(
        "-i", "--inputdir", type=str, default="test_data/test_input_csv",
        help="Directory with parallel test input. Must have locations named 'A','D','E' and 'F'."
    )

    args = parser.parse_args()

    end_time = args.simulationperiod
    last_physical_day = args.simulationperiod
    inputdir = args.inputdir
    initialagents = args.initialagents
    newagentsperstep = args.newagentsperstep

    if args.parallelmode in ["advanced", "adv-lowlat"]:
        parallel_mode = "loc-par"
    else:
        parallel_mode = "classic"

    if args.parallelmode in ["advanced", "cl-hilat"]:
        latency_mode = "high_latency"
    else:
        latency_mode = "low_latency"

    print("MODE: ", args, file=sys.stderr)

    test_par_seq(
        end_time=end_time,
        last_physical_day=last_physical_day,
        parallel_mode=parallel_mode,
        latency_mode=latency_mode,
        inputdir=inputdir,
        initialagents=initialagents,
        newagentsperstep=newagentsperstep,
    )
