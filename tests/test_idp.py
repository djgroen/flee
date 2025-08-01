import os
import sys

import flee.postprocessing.analysis as a
from flee import InputGeography, flee, spawning
from flee.datamanager import DataTable  # DataTable.subtract_dates()
from flee.datamanager import handle_refugee_data


def date_to_sim_days(date):
    return DataTable.subtract_dates(date1=date, date2="2010-01-01")

def test_idp():

    flee.SimulationSettings.ReadFromYML("test_data/test_data_idp/simsetting.yml")

    e = flee.Ecosystem()

    ig = InputGeography.InputGeography()

    ig.ReadLocationsFromCSV(csv_name=os.path.join("test_data", "test_data_idp/input_csv/locations.csv"))

    ig.ReadLinksFromCSV(csv_name=os.path.join("test_data", "test_data_idp/input_csv/routes.csv"))

    ig.ReadClosuresFromCSV(csv_name=os.path.join("test_data", "test_data_idp/input_csv/closures.csv"))

    e, lm = ig.StoreInputGeographyInEcosystem(e=e)

    d = handle_refugee_data.RefugeeTable(
        csvformat="generic",
        data_directory="test_data/test_data_idp",
        start_date="2010-01-01",
        data_layout="data_layout.csv",
        start_empty=False
    )

    camp_locations = ["D", "E", "F"]
    # TODO: Add Camps from CSV based on their location type.

    e.test_prefix = "test_data/test_data_idp"

    for camp_name in camp_locations:
        spawning.add_initial_refugees(e, d, lm[camp_name])
    

    for t in range(0, 11):
        # Insert refugee agents
        spawning.spawn_daily_displaced(e, t, d)
        spawning.refresh_spawn_weights(e)

        ig.AddNewConflictZones(e=e, time=t)

        e.evolve()

    print(f"NUM AGENTS: {len(e.agents)}", file=sys.stderr) 
    assert e.agents[0].attributes["ethnicity"] == "A"
