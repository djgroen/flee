from flee import flee
from flee.datamanager import handle_refugee_data, read_period
from flee import InputGeography
import numpy as np
import flee.postprocessing.analysis as a
import sys

insert_day0_refugees_in_camps = True


def AddInitialRefugees(e, d, loc):
    """ Add the initial refugees to a location, using the location name"""
    num_refugees = int(d.get_field(loc.name, 0, FullInterpolation=True))
    for i in range(0, num_refugees):
        e.addAgent(location=loc, attributes={})


if __name__ == "__main__":

    start_date, end_time = read_period.read_conflict_period(
        "{}/conflict_period.csv".format(sys.argv[1]))

    if len(sys.argv) < 4:
        print("Please run using: python3 run.py <your_csv_directory> "
              "<your_refugee_data_directory> <duration in days> "
              "<optional: simulation_settings.csv> > "
              "<output_directory>/<output_csv_filename>")

    input_csv_directory = sys.argv[1]
    validation_data_directory = sys.argv[2]
    if int(sys.argv[3]) > 0:
        end_time = int(sys.argv[3])

    if len(sys.argv) == 5:
        flee.SimulationSettings.ReadFromCSV(sys.argv[4])
    flee.SimulationSettings.ConflictInputFile = "%s/conflicts.csv" % (
        input_csv_directory)

    e = flee.Ecosystem()

    ig = InputGeography.InputGeography()

    ig.ReadConflictInputCSV(
        flee.SimulationSettings.ConflictInputFile)

    ig.ReadLocationsFromCSV("%s/locations.csv" % input_csv_directory)

    ig.ReadLinksFromCSV("%s/routes.csv" % input_csv_directory)

    ig.ReadClosuresFromCSV("%s/closures.csv" % input_csv_directory)

    e, lm = ig.StoreInputGeographyInEcosystem(e)

    d = handle_refugee_data.RefugeeTable(
        csvformat="generic", data_directory=validation_data_directory,
        start_date=start_date, data_layout="data_layout.csv")

    d.ReadL1Corrections("%s/registration_corrections.csv" %
                        input_csv_directory)

    output_header_string = "Day,"

    camp_locations = e.get_camp_names()

    for l in camp_locations:
        if insert_day0_refugees_in_camps:
            AddInitialRefugees(e, d, lm[l])
        output_header_string += "%s sim,%s data,%s error," % (
            lm[l].name, lm[l].name, lm[l].name)

    output_header_string += "Total error,refugees in camps (UNHCR)," + \
        "total refugees (simulation),raw UNHCR refugee count," + \
        "refugees in camps (simulation),refugee_debt"

    print(output_header_string)

    # Set up a mechanism to incorporate temporary decreases in refugees
    refugee_debt = 0

    for t in range(0, end_time):

        # Calculation of error terms
        errors = []
        abs_errors = []
        loc_data = []

        for i in camp_locations:
            loc_data += [d.get_field(i, t)]

            if d.get_field(i, t) == 0:
                lm[i].numAgents = 0
            else:
                lm[i].numAgents = np.random.randint(
                    low=d.get_field(i, t) * 0.9,
                    high=d.get_field(i, t) * 1.1,
                )
        # calculate errors
        j = 0
        for i in camp_locations:
            errors += [a.rel_error(lm[i].numAgents, loc_data[j])]
            abs_errors += [a.abs_error(lm[i].numAgents, loc_data[j])]

            j += 1

        output = "%s" % t

        for i in range(0, len(errors)):
            output += ",%s,%s,%s" % (lm[camp_locations[i]
                                        ].numAgents, loc_data[i], errors[i])

        output += ",0,0,0,0,0,0"

        print(output)
