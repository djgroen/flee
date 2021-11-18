from flee import flee
from flee.datamanager import handle_refugee_data
from flee.datamanager import DataTable  # DataTable.subtract_dates()
from flee import InputGeography
import numpy as np
import flee.postprocessing.analysis as a
import sys


def AddInitialRefugees(e, d, loc):
    """ Add the initial refugees to a location, using the location name"""
    num_refugees = int(d.get_field(name=loc.name, day=0, FullInterpolation=True))
    for i in range(0, num_refugees):
        e.addAgent(location=loc)


def date_to_sim_days(date):
    return DataTable.subtract_dates(date1=date, date2="2014-05-01")


if __name__ == "__main__":

    if len(sys.argv) > 1:
        end_time = int(sys.argv[1])
        last_physical_day = int(sys.argv[1])
    else:
        end_time = 300
        last_physical_day = 300

    e = flee.Ecosystem()
    flee.SimulationSettings.UseIDPMode = True

    ig = InputGeography.InputGeography()

    ig.ReadLocationsFromCSV(
        csv_name=os.path.join("iraq", "iraq-locations.csv"),
        columns=["region", "area (km^2)", "pop/cap", "name", "capital pop.", "gps_x", "gps_y"]
    )

    ig.ReadLinksFromCSV(csv_name=os.path.join("iraq", "iraq-links.csv"))

    lm = ig.StoreInputGeographyInEcosystem(e=e)

    # print("Network data loaded")

    d_spawn = handle_refugee_data.RefugeeTable(
        csvformat="generic",
        data_directory=os.path.join("iraq", "spawn_data"),
        start_date="2014-05-01"
    )
    d = handle_refugee_data.RefugeeTable(
        csvformat="generic",
        data_directory=os.path.join("iraq", "idp_counts"),
        start_date="2014-05-01"
    )

    output_header_string = "Day,"

    for l in e.locations:
        AddInitialRefugees(e, d, l)
        output_header_string += "{} sim,{} data,{} error,".format(l.name, l.name, l.name)

    output_header_string += (
        "Total error,refugees in camps (UNHCR),total refugees (simulation),"
        "raw UNHCR refugee count,refugees in camps (simulation),refugee_debt"
    )

    print(output_header_string)

    # Set up a mechanism to incorporate temporary decreases in refugees
    refugee_debt = 0
    # raw (interpolated) data from TOTAL UNHCR refugee count only.
    refugees_raw = 0

    e.add_conflict_zone(name="Baghdad")

    # Start with a refugee debt to account for the mismatch
    # between camp aggregates and total UNHCR data.
    # refugee_debt = e.numAgents()

    for t in range(0, end_time):

        e.refresh_conflict_weights()

        t_data = t

        new_refs = 100

        """
        # Determine number of new refugees to insert into the system.
        new_refs = d.get_daily_difference(day=t, FullInterpolation=True) - refugee_debt
        refugees_raw += d.get_daily_difference(day=t, FullInterpolation=True)
        if new_refs < 0:
          refugee_debt = -new_refs
          new_refs = 0
        elif refugee_debt > 0:
          refugee_debt = 0
        """

        for l in e.locations:
            new_IDPs = int(d_spawn.get_field(name=l.name, day=t + 1) -
                           d_spawn.get_field(name=l.name, day=t))
            if new_IDPs > 0:
                l.movechance = 1.0
            else:
                l.movechance = 0.001
            for i in range(0, int(new_IDPs / 6)):
                e.addAgent(location=l)

        e.evolve()

        # e.printInfo()

        # Validation / data comparison
        camps = e.locations
        camp_names = e.locationNames
        # TODO: refactor camp_names using list comprehension.

        # calculate retrofitted time.
        refugees_in_camps_sim = 0
        for c in camps:
            refugees_in_camps_sim += c.numAgents

        # calculate error terms.
        camp_pops = []
        errors = []
        abs_errors = []
        for i in range(0, len(camp_names)):
            # normal 1 step = 1 day errors.
            camp_pops += [d.get_field(name=camp_names[i], day=t, FullInterpolation=True)]
            errors += [a.rel_error(val=camps[i].numAgents, correct_val=camp_pops[-1])]
            abs_errors += [a.abs_error(val=camps[i].numAgents, correct_val=camp_pops[-1])]

        # Total error is calculated using
        # float(np.sum(abs_errors))/float(refugees_raw))

        locations = camps
        loc_data = camp_pops

        # if e.numAgents()>0:
        # print "Total error: ", float(np.sum(abs_errors))/float(e.numAgents())

        # write output (one line per time step taken.
        output = "%s" % (t)
        for i in range(0, len(locations)):
            output += ",{},{},{}".format(locations[i].numAgents, loc_data[i], errors[i])

        if float(sum(loc_data)) > 0:
            # Reminder: Total error,refugees in camps (UNHCR),total refugees
            # (simulation),raw UNHCR refugee count,retrofitted time,refugees in
            # camps (simulation),Total error (retrofitted)
            output += ",{},{},{},{},{},{}".format(
                float(np.sum(abs_errors)) / float(refugees_raw + 1),
                int(sum(loc_data)),
                e.numAgents(),
                refugees_raw,
                refugees_in_camps_sim,
                refugee_debt
            )
        else:
            output += ",0,0,0,0,0,0,0"

        print(output)
