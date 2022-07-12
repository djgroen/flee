# food_flee.py
# A modified implementation of FLEE to account for the food security
# conditions. Movechances are modified.
import sys

import numpy as np
import pandas as pd

from flee import flee
from flee.SimulationSettings import SimulationSettings


def initiate_food():
    """
    Summary
    """
    # path = "~/Documents/Python/SSudan/ICCS/flee/source_data/ssudan2014/food/IPC.csv"
    # critict = pd.read_csv(path)["Dates"]
    # path = "~/Documents/Python/SSudan/ICCS/flee/source_data/ssudan2014/food/IPC.csv"
    # IPC_all=pd.read_csv(path,index_col=0)
    critict = pd.read_csv(
        "source_data/ssudan2014/food/IPC.csv")["Dates"]
    IPC_all = pd.read_csv(
        "source_data/ssudan2014/food/IPC.csv", index_col=0)
    current_i = 0

    return [critict, IPC_all, current_i]


def line42day(t, current_i, critict):
    """
    Summary
    """
    current_critict = critict[current_i]
    while current_critict < t:
        current_i = current_i + 1
        current_critict = critict[current_i]
    return current_critict


class Location(flee.Location):
    """
    the Location class
    """

    def __init__(self, name, x=0.0, y=0.0, location_type=None, capacity=-1, pop=0, foreign=False,
                 country="unknown", region="unknown", IPC=0):
        super().__init__(name, x, y, location_type, capacity, pop, foreign, country)
        self.region = region
        self.IPC = IPC


class Ecosystem(flee.Ecosystem):
    """
    the Ecosystem class
    """

    def __init__(self):
        super().__init__()

        # IPC specific configuration variables.
        self.IPCAffectsMoveChance = True  # IPC modified move chances
        # (Warning: lower validation error correlates with higher average move chances)
        self.IPCUseMezumanEq = False  # Use modified piece-wise equation.
        self.MezumanEqThresholdMstar = 0.8  # M* (used in Mezuman equation).
        # IPC affects Spawn location distribution.
        self.IPCAffectsSpawnLocation = False

    def update_IPC_MC(self, line_IPC, IPC_all):  # maybe better (less computation time)
        """
        Summary
        """
        self.IPC_location_weights = []
        self.IPC_locations = []
        self.total_weight = 0.0
        for i in range(0, len(self.locationNames)):
            if self.locations[i].country == "South_Sudan":  # needed??

                # 1. Update IPC scores for all locations
                self.locations[i].IPC = IPC_all.loc[
                    line_IPC, self.locations[i].region]

                # 2. Update IPC spawning weights for all locations
                if self.IPCAffectsSpawnLocation:
                    self.IPC_locations.append(self.locations[i])
                    if not self.locations[i].conflict:
                        self.IPC_location_weights.append(
                            (self.locations[i].IPC / 100.0) * self.locations[i].pop)
                    else:
                        # Conflict zones already have their full population as
                        # weight
                        self.IPC_location_weights.append(self.locations[i].pop)
                        # so food security should not increase it beyond that
                        # amount.
                    self.total_weight += self.IPC_location_weights[-1]

                # 3. Adjust move chances, taking into account IPC scores.
                if self.IPCAffectsMoveChance:
                    if not self.locations[i].conflict and \
                            not self.locations[i].camp and \
                            not self.locations[i].forward:
                        IPC = self.locations[i].IPC / 100.0
                        if self.IPCUseMezumanEq:
                            if self.locations[i].IPC < self.MezumanEqThresholdMstar:
                                self.locations[i].movechance = IPC +\
                                    SimulationSettings.move_rules["DefaultMoveChance"] * (1 - IPC)
                            else:
                                self.locations[i].movechance = (
                                    (
                                        (
                                            (1.0 - SimulationSettings.move_rules["DefaultMoveChance"]) *
                                            self.MezumanEqThresholdMstar
                                        ) + SimulationSettings.move_rules["DefaultMoveChance"]
                                    ) / (1.0 - self.MezumanEqThresholdMstar)
                                ) * (1 - IPC)
                        else:
                            self.locations[i].movechance = IPC + \
                                SimulationSettings.move_rules["DefaultMoveChance"] * (1 - IPC)

    def pick_conflict_location(self):
        """
        Returns a weighted random element from the list of conflict locations.
        This function returns a number, which is an index in the array of conflict locations.
        """
        if self.IPCAffectsSpawnLocation:
            return np.random.choice(
                self.IPC_locations, p=self.IPC_location_weights / self.total_weight
            )

        return np.random.choice(
            self.conflict_zones, p=self.conflict_spawn_weights / self.conflict_pop
        )

    def addLocation(self, name, x="0.0", y="0.0", location_type="default",
                    capacity=-1, pop=0, foreign=False, country="unknown", region="unknown", IPC=0):
        """
        Add a location to the ABM network graph
        """

        loc = Location(name=name, x=x, y=y, location_type=location_type, capacity=capacity,
                       pop=pop, foreign=foreign, country=country, region=region, IPC=IPC)
        if SimulationSettings.InitLogLevel > 0:
            print("Location:", name, x, y, loc.movechance, capacity,
                  ", pop. ", pop, foreign, "State: ", loc.region, "IPC: ", loc.IPC)
        self.locations.append(loc)
        self.locationNames.append(loc.name)
        return loc

    def printInfo(self):
        """
        Summary
        """
        # print("Time: ", self.time, ", # of agents: ", len(self.agents))
        if self.IPCAffectsSpawnLocation:
            for i, loc in enumerate(self.IPC_locations):
                print(
                    loc.name,
                    "Conflict:", self.locations[i].conflict,
                    "Pop:", loc.pop,
                    "IPC:", loc.IPC,
                    "mc:", loc.movechance,
                    "weight:", self.IPC_location_weights[i],
                    file=sys.stderr
                )
        else:
            for loc in self.locations:
                print(loc.name, "Agents: ", loc.numAgents, "State: ", loc.region,
                      "IPC: ", loc.IPC, "movechance: ", loc.movechance, file=sys.stderr)


if __name__ == "__main__":
    print("Flee, prototype version.")

    # has to go in the main part of flee before starting time count
    [critict, IPC_all, current_i] = initiate_food()

    end_time = 604
    e = Ecosystem()

    l1 = e.addLocation("Source", region="Unity")
    l2 = e.addLocation("Sink1", region="Upper Nile")
    l3 = e.addLocation("Sink2", region="Jonglei")

    e.linkUp("Source", "Sink1", "5.0")
    e.linkUp("Source", "Sink2", "10.0")

    for _ in range(0, 100):
        e.addAgent(location=l1)

    print("Initial state")
    e.printInfo()

    old_line = 0

    for t in range(0, end_time):
        # has to go in the time count of flee to choose the values of IPC
        # according to t
        line_IPC = line42day(t, current_i, critict)
        if not old_line == line_IPC:
            print("Time = %d. Updating IPC indexes and movechances" %
                  (t), file=sys.stderr)
            # update all locations in the ecosystem: IPC indexes and
            # movechances (inside t loop)
            e.update_IPC_MC(line_IPC, IPC_all)
            print("After updating IPC and movechance:")
            e.printInfo()
        e.evolve()
        old_line = line_IPC
    print("After evolving")
    e.printInfo()
