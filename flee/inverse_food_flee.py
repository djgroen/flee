# inverse_food_flee.py

# Modified version of food flee implementation by Chris Vassiliou. This version implements my inverted movechance
# hypothesis: "The higher the food insecurity, then refugees are less likely to move elsewhere" this hypothesis
# adjusts the movechance for each location in the simulation based on the food security of that location. it does
# this in a new way, using a new formula i developed.

import numpy as np
import sys
from flee import SimulationSettings
from flee import flee
import pandas as pd


# This function initiate_food retrieves the IPC food security data matrix from it's CSV file and assigns it to two
# variables, critict and IPC_all. critict is the 'day' column of the matrix, and is used to tell the simulation when
# to update the IPC values. IPC_all stores all of the columns that hold IPC data. each column represents a region of
# S Sudan. These variables are made using pandas, an external python library.
def initiate_food():
    # these variables are created by using pandas to read the csv files from my system.
    critict = pd.read_csv("~/codes/FabSim3/plugins/FabFlee/config_files/flee_ssudan_food/input_csv/IPC.csv")[
        "Dates"]
    IPC_all = pd.read_csv("~/codes/FabSim3/plugins/FabFlee/config_files/flee_ssudan_food/input_csv/IPC.csv",
                          index_col=0)
    current_i = 0

    # i added these 4 lines so that i could see specific output of pandas variables in the out.csv file during the
    # testing of my simulations.
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', -1)

    return [critict, IPC_all, current_i]


# this function 'line42day' was used in the original food_flee.py file. it changes the current row being focused on
# in the IPC matrix, by updating the critict variable to match the day of the simulation. i did not edit this function.
def line42day(t, current_i, critict):
    current_critict = critict[current_i]
    while current_critict < t:
        current_i = current_i + 1
        current_critict = critict[current_i]
    return current_critict


# this small addition is copied from food_flee.py. the _init_ function of the location class from flee is given
# variables for region and IPC, so that the locations in the simulation can hold the information provided by the IPC
# data file.
class Location(flee.Location):
    def __init__(self, name, x=0.0, y=0.0, movechance=0.001, capacity=-1, pop=0, foreign=False, country="unknown",
                 region="unknown", IPC=0):
        super().__init__(name, x, y, movechance, capacity, pop, foreign, country)
        self.region = region
        self.IPC = IPC


class Ecosystem(flee.Ecosystem):

    def __init__(self):
        super().__init__()
        # this variable IPCAffectsMovechance is used to activate/deactivate the movechance IPC changes. in
        # future work, where several hypotheses are implemented into one file, this would allow different hypotheses
        # to be active at different times.
        self.IPCAffectsMoveChance = True

    def update_IPC(self, line_IPC, IPC_all):  # maybe better (less computation time)
        # first, loop through every location in the simulation.
        for i in range(0, len(self.locationNames)):
            # only act on locations in S Sudan:
            if self.locations[i].country == "South_Sudan":

                # Update the IPC scores for all locations in S Sudan by checking the location's region and assigning
                # it that region's IPC value from IPC_all
                self.locations[i].IPC = IPC_all.loc[line_IPC][self.locations[i].region]

                # next, adjust the movechance for each location using my inverse movechance formula. this is where the formula is implemented as code.
                if self.IPCAffectsMoveChance:
                    if not self.locations[i].conflict and not self.locations[i].camp and not self.locations[i].forward:
                        self.locations[i].movechance = SimulationSettings.SimulationSettings.DefaultMoveChance * (
                                1 - self.locations[i].IPC / 100.0)
                # below is a set of print statements i was using to test my output was behaving as it should have.
                # print(self.locations[i].name)
                # print("IPC is:")
                # print(self.locations[i].IPC)
                # print("movechance is")
                # print(self.locations[i].movechance)

    # this function, printinfo, prints specific details for each location, into the console as the simulation runs.
    # it is called every time the IPC values are updated for every location.
    def printInfo(self):
        for l in range(len(self.locations)):
            print(self.locations[l].name, "Conflict? ", self.locations[l].conflict, "Population:",
                  self.locations[l].pop, "IPC:", self.locations[l].IPC, "MC:",
                  self.locations[l].movechance, file=sys.stderr)

    not developed or modified
    by
    me
    at
    all.these
    are
    just
    a
    necessary
    inclusion

    # this function, addLocation, is not developed or modified by me at all. it is necessary to this file's
    # functionality, though, as it ensures that locations are being added correctly to the simulations, with their
    # IPC variable.
    def addLocation(self, name, x="0.0", y="0.0", movechance=SimulationSettings.SimulationSettings.DefaultMoveChance,
                    capacity=-1, pop=0, foreign=False, country="unknown", region="unknown", IPC=0):
        l = Location(name, x, y, movechance, capacity, pop, foreign, country, region, IPC)
        self.locations.append(l)
        self.locationNames.append(l.name)
        return l
