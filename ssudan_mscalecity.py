from flee import pmicro_flee  # parallel implementation
from flee import coupling  # coupling interface for multiscale models
from datamanager import handle_refugee_data, read_period
from datamanager import DataTable  # DataTable.subtract_dates()
from flee import InputGeography
from post_processing import analysis as a
import numpy as np
import sys


def AddInitialRefugees(e, d, loc):
    """ Add the initial refugees to a location, using the location name"""
    num_refugees = int(d.get_field(loc.name, 0, FullInterpolation=True))
    for i in range(0, num_refugees):
        e.addAgent(location=loc)

insert_day0_refugees_in_camps = True


if __name__ == "__main__":

    data_dir = "conflict_inputs/ssudan-mscale-test"

    start_date, end_time = read_period.read_conflict_period(
        "{}/conflict_period.csv".format(data_dir))

    submodel_id = 0

    if len(sys.argv) > 1:
        if (sys.argv[1]).isnumeric():
            submodel_id = int(sys.argv[1])

    if (submodel_id == 0):
        validation_data_directory = ("{}/source_data-0/".format(data_dir))
        out_csv_file = 'out/macro/out.csv'
    if (submodel_id == 1):
        validation_data_directory = ("{}/source_data-1/".format(data_dir))
        out_csv_file = 'out/micro/out.csv'

    e = pmicro_flee.Ecosystem()
    c = coupling.CouplingInterface(e)

    c.setCouplingFilenames("in", "out")
    if(submodel_id > 0):
        c.setCouplingFilenames("out", "in")

    ig = InputGeography.InputGeography()

    ig.ReadFlareConflictInputCSV(
        "{}/conflicts-{}.csv".format(data_dir,submodel_id))

    ig.ReadLocationsFromCSV(
        "{}/locations-{}.csv".format(data_dir,submodel_id))

    ig.ReadLinksFromCSV(
        "{}/routes-{}.csv".format(data_dir,submodel_id))

    ig.ReadClosuresFromCSV(
        "{}/closures-{}.csv".format(data_dir,submodel_id))

    e, lm = ig.StoreInputGeographyInEcosystem(e)

    # DEBUG: print graph and show it on an image.
    #vertices, edges = e.export_graph()
    #analyze_graph.print_graph_nx(vertices, edges, print_dist=True)
    # sys.exit()

    #print("Network data loaded")

    d = handle_refugee_data.RefugeeTable(
        csvformat="generic", data_directory=validation_data_directory, start_date=start_date, data_layout="data_layout.csv")

    d.ReadL1Corrections(
        "{}/registration_corrections-{}.csv".format(data_dir,submodel_id))

    output_header_string = "Day,"

    coupled_locations = ["Bor", "Pochalla", "Panyikang"]


    camp_locations = e.get_camp_names()


    for i in camp_locations:
        # if (submodel_id == 0):
        AddInitialRefugees(e, d, lm[i])
        output_header_string += "%s sim,%s data,%s error," % (lm[i].name, lm[i].name, lm[i].name)


    output_header_string += "Total error,refugees in camps (UNHCR),total refugees (simulation),raw UNHCR refugee count,refugees in camps (simulation),refugee_debt"


    for l in coupled_locations:
        c.addCoupledLocation(lm[l], l)

    if submodel_id == 0:
        # Add ghost conflict zones to macro model ("in" mode)
        c.addGhostLocations(ig)
    if submodel_id == 1:
        # Couple all conflict locs in micro model ("out" mode)
        c.addMicroConflictLocations(ig)

    sys.exit()

    if e.getRankN(0):
        # output_header_string += "num agents,num agents in camps"
        print(output_header_string)
        with open(out_csv_file, 'a+') as f:
            f.write(output_header_string)
            f.write('\n')
            f.flush()        

    # Set up a mechanism to incorporate temporary decreases in refugees
    refugee_debt = 0
    # raw (interpolated) data from TOTAL UNHCR refugee count only.
    refugees_raw = 0


    for t in range(0, end_time):

        # if t>0:
        ig.AddNewConflictZones(e, t)

        # Determine number of new refugees to insert into the system.
        new_refs = d.get_daily_difference(t, FullInterpolation=True) - refugee_debt
        refugees_raw += d.get_daily_difference(t, FullInterpolation=True)


        if new_refs < 0:
            refugee_debt =- new_refs
            new_refs = 0
        elif refugee_debt > 0:
            refugee_debt = 0



        # Insert refugee agents

        for i in range(0, new_refs):
            e.addAgent(e.pick_conflict_location())


        # exchange data with other code.
        # immediately after agent insertion to ensure ghost locations
        # work correctly.
        c.Couple(t)
        


        e.refresh_conflict_weights()
        t_data = t

        # e.enact_border_closures(t)
        e.evolve()

        # Calculation of error terms
        errors = []
        abs_errors = []
        loc_data = []

        camps = []
       
        for i in camp_locations:
            camps += [lm[i]]
            loc_data += [d.get_field(i, t)]

        # calculate retrofitted time.
        refugees_in_camps_sim = 0
        
        for camp in camps:
            refugees_in_camps_sim += camp.numAgents

        if e.getRankN(t):
            output = "%s" % t

            j = 0
            for i in camp_locations:
                errors += [a.rel_error(lm[i].numAgents, loc_data[j])]
                abs_errors += [a.abs_error(lm[i].numAgents, loc_data[j])]

                j += 1

            output = "%s" % t



            for i in range(0, len(errors)):
                output += ",%s,%s,%s" % (lm[camp_locations[i]
                                            ].numAgents, loc_data[i], errors[i])

                
            #print(output)
            #exit()
            

            if refugees_raw > 0:
                output += ",%s,%s,%s,%s,%s,%s" % (float(np.sum(abs_errors)) / float(refugees_raw), int(
                    sum(loc_data)), e.numAgents(), refugees_raw, refugees_in_camps_sim, refugee_debt)
            else:
                output += ",0,0,0,0,0,0"

            print(output)
            with open(out_csv_file, 'a+') as f:
                f.write(output)
                f.write('\n')
                f.flush()
