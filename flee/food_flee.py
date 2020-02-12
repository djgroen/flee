# food_flee.py
# A modified implementation of FLEE to account for the food security conditions. Movechances are modified.

# changes from the original food_flee file have been made by chris vassiliou

import numpy as np
import sys
import random
from flee import SimulationSettings
from flee import flee
import csv
import pandas as pd


def initiate_food():
    critict = pd.read_csv("~/codes/FabSim3/plugins/FabFlee/config_files/flee_ssudan_food/input_csv/IPC.csv")[
        "Dates"]
    IPC_all = pd.read_csv("~/codes/FabSim3/plugins/FabFlee/config_files/flee_ssudan_food/input_csv/IPC.csv",
                          index_col=0)
    current_i = 0

    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', -1)

    return [critict, IPC_all, current_i]


def line42day(t, current_i, critict):
    current_critict = critict[current_i]
    while current_critict < t:
        current_i = current_i + 1
        current_critict = critict[current_i]
    return current_critict


class Location(flee.Location):
    def __init__(self, name, x=0.0, y=0.0, movechance=0.001, capacity=-1, pop=0, foreign=False, country="unknown",
                 region="unknown", IPC=0):
        super().__init__(name, x, y, movechance, capacity, pop, foreign, country)
        self.region = region
        self.IPC = IPC


class Ecosystem(flee.Ecosystem):

    def __init__(self):
        super().__init__()

        # IPC specific configuration variables.
        self.total_weight = 0.0
        self.IPC_locations = []
        self.IPC_location_weights = []

        self.IPCAffectsMoveChance = True  # IPC modified move chances
        # (Warning: lower validation error correlates with higher average move chances)

        self.IPCAffectsSpawnLocation = False  # IPC affects Spawn location distribution.

    def update_IPC(self, line_IPC, IPC_all):  # maybe better (less computation time)

        for i in range(0, len(self.locationNames)):
            if self.locations[i].country == "South_Sudan":
                # 1. Update IPC scores for all locations
                self.locations[i].IPC = IPC_all.loc[line_IPC][self.locations[i].region]
                print(self.locations[i].name)
                print(self.locations[i].IPC)
                # 2. Update IPC spawning weights for all locations
                if self.IPCAffectsSpawnLocation:
                    self.IPC_locations.append(self.locations[i])
                    if not self.locations[i].conflict:
                        self.IPC_location_weights.append((self.locations[i].IPC / 100.0) * self.locations[i].pop)
                    else:
                        self.IPC_location_weights.append(
                            self.locations[i].pop)  # Conflict zones already have their full population as weight
                        # so food security should not increase it beyond that amount.
                    self.total_weight += self.IPC_location_weights[-1]

                # 3. Adjust move chances, taking into account IPC scores.
                if self.IPCAffectsMoveChance:
                    if not self.locations[i].conflict and not self.locations[i].camp and not self.locations[i].forward:
                        self.locations[i].movechance = self.locations[
                                                           i].IPC / 100.0 + SimulationSettings.SimulationSettings.DefaultMoveChance * (
                                                               1 - self.locations[i].IPC / 100.0)

    def pick_conflict_location(self):
        """
    Returns a weighted random element from the list of conflict locations.
    This function returns a number, which is an index in the array of conflict locations.
    """
        if self.IPCAffectsSpawnLocation:
            return np.random.choice(self.IPC_locations, p=self.IPC_location_weights / self.total_weight)
        else:
            return np.random.choice(self.conflict_zones, p=self.conflict_weights / self.conflict_pop)

    def addLocation(self, name, x="0.0", y="0.0", movechance=SimulationSettings.SimulationSettings.DefaultMoveChance,
                    capacity=-1, pop=0, foreign=False, country="unknown", region="unknown", IPC=0):
        """ Add a location to the ABM network graph """

        l = Location(name, x, y, movechance, capacity, pop, foreign, country, region, IPC)
        if SimulationSettings.SimulationSettings.InitLogLevel > 0:
            print("Location:", name, x, y, l.movechance, capacity, ", pop. ", pop, foreign, "State: ", l.region,
                  "IPC: ", l.IPC)
        self.locations.append(l)
        self.locationNames.append(l.name)
        return l

    def printInfo(self):
        # print("Time: ", self.time, ", # of agents: ", len(self.agents))
        if self.IPCAffectsSpawnLocation:
            for l in range(len(self.IPC_locations)):
                print(self.IPC_locations[l].name, "Conflict:", self.locations[l].conflict, "Pop:",
                      self.IPC_locations[l].pop, "IPC:", self.IPC_locations[l].IPC, "mc:",
                      self.IPC_locations[l].movechance, "weight:", self.IPC_location_weights[l], file=sys.stderr)
        else:
            for l in self.locations:
                print(l.name, "Agents: ", l.numAgents, "State: ", l.region, "IPC: ", l.IPC, "movechance: ",
                      l.movechance, file=sys.stderr)


if __name__ == "__main__":
    print("Flee, prototype version.")

    [critict, IPC_all, current_i] = initiate_food()  # has to go in the main part of flee before starting time count

    end_time = 604
    e = Ecosystem()
    e.update_IPC(line_IPC, IPC_all)
    l1 = e.addLocation("Source", region="Unity")
    l2 = e.addLocation("Sink1", region="Upper Nile")
    l3 = e.addLocation("Sink2", region="Jonglei")

    e.linkUp("Source", "Sink1", "5.0")
    e.linkUp("Source", "Sink2", "10.0")

    for i in range(0, 100):
        e.addAgent(location=l1)

    print("Initial state")
    e.printInfo()

    old_line = 0

    for t in range(0, end_time):
        line_IPC = line42day(t, current_i,
                             critict)  # has to go in the time count of flee to choose the values of IPC according to t
        if not old_line == line_IPC:
            print("Time = %d. Updating IPC indexes and movechances" % (t), file=sys.stderr)
            e.update_IPC(line_IPC,
                            IPC_all)  # update all locations in the ecosystem: IPC indexes and movechances (inside t loop)
            print("After updating IPC and movechance:")
            e.printInfo()
        e.evolve()
        old_line = line_IPC
    print("After evolving")
    e.printInfo()
