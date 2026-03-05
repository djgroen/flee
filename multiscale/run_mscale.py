import argparse
import csv
import os
import sys

import numpy as np
import pandas as pd
from flee import coupling  # coupling interface for multiscale models
from flee.datamanager import handle_refugee_data, read_period
import flee.postprocessing.analysis as a
from flee.SimulationSettings import SimulationSettings

work_dir = os.path.dirname(os.path.abspath(__file__))
insert_day0_refugees_in_camps = False


def read_coupled_locations(csv_inputfile):
    c = []
    with open(csv_inputfile, newline="", encoding="utf-8") as csvfile:
        csvreader = csv.reader(csvfile)
        for row in csvreader:
            if row[0].startswith("#"):
                pass
            else:
                c += [row[0]]

    print("Coupling locations:", c, file=sys.stderr)
    return c


def run_micro_macro_model(e, c, submodel, ig, d, camp_locations, end_time):
    # Set up a mechanism to incorporate temporary decreases in refugees
    refugee_debt = 0
    # raw (interpolated) data from TOTAL UNHCR refugee count only.
    refugees_raw = 0

    while c.reuse_coupling():
        for t in range(0, end_time):

            # if t>0:
            ig.AddNewConflictZones(e=e, time=t)

            # Determine number of new refugees to insert into the system.
            new_refs = (
                d.get_daily_difference(day=t, FullInterpolation=True, SumFromCamps=False)
                - refugee_debt
            )

            refugees_raw += d.get_daily_difference(
                day=t, FullInterpolation=True, SumFromCamps=False
            )

            if log_exchange_data is True:
                c.logNewAgents(t=t, new_refs=new_refs)

            if new_refs < 0:
                refugee_debt = -new_refs
                new_refs = 0
            elif refugee_debt > 0:
                refugee_debt = 0

            # Insert refugee agents

            if submodel == "macro":
                print("t={}, inserting {} new agents".format(t, new_refs), file=sys.stderr)
                # e.add_agents_to_conflict_zones(number=new_refs)
                for _ in range(0, new_refs):
                    e.addAgent(location=e.pick_conflict_location())
                e.updateNumAgents(log=False)

            # e.printInfo()

            # exchange data with other code.
            # immediately after agent insertion to ensure ghost locations
            # work correctly.
            c.Couple(time=t)

            e.refresh_conflict_weights()

            # e.enact_border_closures(time=t)
            e.evolve()

            # Calculation of error terms
            errors = []
            abs_errors = []
            loc_data = []

            camps = []

            for i in camp_locations:
                camps += [lm[i]]
                loc_data += [d.get_field(name=i, day=t)]

            # calculate retrofitted time.
            refugees_in_camps_sim = 0

            for camp in camps:
                refugees_in_camps_sim += camp.numAgents

            if e.getRankN(t):
                output = "%s,%s" % (t, e.date_string)

                j = 0
                for i in camp_locations:
                    errors += [a.rel_error(val=lm[i].numAgents, correct_val=loc_data[j])]
                    abs_errors += [a.abs_error(val=lm[i].numAgents, correct_val=loc_data[j])]

                    j += 1

                for i in range(0, len(errors)):
                    output += ",{},{},{}".format(
                        lm[camp_locations[i]].numAgents, loc_data[i], errors[i]
                    )

                if refugees_raw > 0:
                    output += ",{},{},{},{},{},{}".format(
                        round(float(np.sum(abs_errors)) / float(refugees_raw), a.ROUND_NDIGITS),
                        int(sum(loc_data)),
                        e.numAgents(),
                        refugees_raw,
                        refugees_in_camps_sim,
                        refugee_debt,
                    )
                else:
                    output += ",0,0,0,0,0,0"

                # print(output)

                with open(out_csv_file, "a+", encoding="utf-8") as f:
                    f.write(output)
                    f.write("\n")
                    f.flush()
                # exit()

        # break while-loop(c.reuse_coupling) if coupling_type == file
        if not hasattr(c, "instance"):
            break


def run_manager(c, submodel, end_time):

    while c.reuse_coupling():
        for t in range(0, end_time):
            c.Couple(time=t)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    # Required parameters (mandatory)
    parser.add_argument(
        "--data_dir", required=True, action="store", type=str, help="the input data directory"
    )
    parser.add_argument(
        "--submodel",
        required=True,
        action="store",
        type=str,
        choices=["micro", "macro", "macro_manager", "micro_manager"],
        help="the current active coupled model",
    )
    parser.add_argument(
        "--coupling_type",
        required=True,
        action="store",
        type=str,
        choices=["file", "muscle3"],
        help="the coupling type to be used",
    )
    parser.add_argument(
        "--instance_index",
        required=True,
        action="store",
        type=int,
        help="the index of current active macro/micro session",
    )

    parser.add_argument(
        "--num_instances",
        required=True,
        action="store",
        type=int,
        help="set the number of concurrent launched sessions of macro and micro models",
    )

    # Optional parameters
    parser.add_argument("--end_time", action="store", type=int)

    parser.add_argument(
        "--log_exchange_data",
        action="store",
        type=str,
        default="True",
        help="boolean flag to enable/disable logging exchanged data between macro and micro models",
    )

    args, unknown = parser.parse_known_args()

    print("args: {}".format(args), file=sys.stderr)

    data_dir = os.path.join(work_dir, args.data_dir)

    coupled_locations = read_coupled_locations(os.path.join(data_dir, "coupled_locations.csv"))

    start_date, end_time = read_period.read_sim_period(
        fname=os.path.join(data_dir, "sim_period.csv")
    )

    submodel = args.submodel.lower()
    coupling_type = args.coupling_type
    instance_index = int(args.instance_index)
    num_instances = int(args.num_instances)

    if args.end_time is not None:
        end_time = int(args.end_time)
    last_physical_day = end_time

    # if args.log_exchange_data.lower() == "true":
    #     log_exchange_data = True
    # else:
    #     log_exchange_data = False
    log_exchange_data = bool(args.log_exchange_data.lower() == "true")

    SumFromCamps = False  # Set to TRUE for production runs.

    submodel_id = 0
    if submodel == "micro":
        submodel_id = 1

    if submodel in ["macro", "macro_manager", "micro", "micro_manager"]:
        from flee import InputGeography
        from flee import pflee as flee

        validation_data_directory = os.path.join(data_dir, f"source_data-{submodel_id}")
        if submodel in ["macro", "micro"]:
            out_csv_file = os.path.join(
                work_dir, "out", coupling_type, submodel, "out[{}].csv".format(instance_index)
            )

    print(f"This is submodel {submodel_id} of type {submodel}", file=sys.stderr)

    outputdir = os.path.join(work_dir, "out")

    flee.SimulationSettings.ReadFromYML("simsetting.yml")

    e = flee.Ecosystem()

    c = coupling.CouplingInterface(
        e=e,
        submodel=submodel,
        instance_index=instance_index,
        num_instances=num_instances,
        coupling_type=coupling_type,
        outputdir=outputdir,
        log_exchange_data=log_exchange_data,
    )

    if coupling_type == "muscle3":
        if hasattr(c, "instance"):
            print("Instance attribute found for coupling class c.", file=sys.stderr)
        else:
            print("WARNING: coupling class c does not have an instance attribute.", file=sys.stderr)

    # setting coupling output file name
    if coupling_type == "file":
        if submodel == "micro":
            c.setCouplingChannel(outputchannel="out", inputchannel="in")
        elif submodel == "macro":
            c.setCouplingChannel(outputchannel="in", inputchannel="out")

    ig = InputGeography.InputGeography()

    ig.ReadConflictInputCSV(
        csv_name=os.path.join(data_dir, "conflicts-{}.csv".format(submodel_id))
    )

    ig.ReadLocationsFromCSV(csv_name=os.path.join(data_dir, "locations-{}.csv".format(submodel_id)))

    ig.ReadLinksFromCSV(csv_name=os.path.join(data_dir, "routes-{}.csv".format(submodel_id)))

    ig.ReadClosuresFromCSV(csv_name=os.path.join(data_dir, "closures-{}.csv".format(submodel_id)))

    e, lm = ig.StoreInputGeographyInEcosystem(e=e)

    print(
        "Val dir: {}. Start date set to {}.".format(validation_data_directory, start_date),
        file=sys.stderr,
    )

    d = handle_refugee_data.RefugeeTable(csvformat="generic", data_directory=validation_data_directory, start_date=start_date, data_layout="data_layout.csv", population_scaledown_factor=SimulationSettings.optimisations["PopulationScaleDownFactor"], start_empty=SimulationSettings.spawn_rules["EmptyCampsOnDay0"])

    d.ReadL1Corrections(
        csvname=os.path.join(data_dir, "registration_corrections-{}.csv".format(submodel_id))
    )

    output_header_string = "Day,Date,"

    camp_locations = e.get_camp_names()

    for l in camp_locations:
        # Add initial refugees to camps is currently not supported in
        # coupled mode, because the totals are not added up correctly across
        # the submodels.
        # All agents therefore have to start in conflict zones.

        if insert_day0_refugees_in_camps:
            spawning.add_initial_refugees(e,d,lm[l])
        output_header_string += "%s sim,%s data,%s error," % (lm[l].name, lm[l].name, lm[l].name)

    output_header_string += "Total error,refugees in camps (UNHCR),total refugees (simulation),raw UNHCR refugee count,refugees in camps (simulation),refugee_debt"

    for loc_name in coupled_locations:
        c.addCoupledLocation(location=lm[loc_name], name=loc_name)

    if submodel in ["macro", "macro_manager"]:
        # Add ghost conflict zones to macro model ("out" mode)
        c.addGhostLocations(ig=ig)
    if submodel in ["micro", "micro_manager"]:
        # Couple all conflict locs in micro model ("in" mode)
        c.addMicroConflictLocations(ig=ig)

    if submodel in ["macro", "micro"]:
        # DO NOT generate output file for the micro/macro managers
        if e.getRankN(0):
            # output_header_string += "num agents,num agents in camps"
            print(output_header_string)
            with open(out_csv_file, "a+", encoding="utf-8") as f:
                f.write(output_header_string)
                f.write("\n")
                f.flush()

    # end_time = 30
    if submodel in ["macro", "micro"]:
        run_micro_macro_model(e, c, submodel, ig, d, camp_locations, end_time)
    elif submodel in ["macro_manager", "micro_manager"]:
        run_manager(c, submodel, end_time)

    if log_exchange_data is True and e.getRankN(0):
        c.saveExchangeDataToFile()
        # only for one submodel instance plot the data exchanged
        if instance_index == 0:
            c.plotExchangedData()
            c.sumOutputCSVFiles()
