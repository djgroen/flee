# speed_food_flee.py

# Modified version of food flee implementation by Chris Vassiliou. This version implements my hypotheses for speed:
# "The higher the food insecurity, the faster migrants are likely to move."
# Instead of adjusting movechance, I adjust the speed of the agents.
# All comments are by chris vassiliou.

import numpy as np
import sys
import random
from flee import SimulationSettings
from flee import flee
import csv
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

    # for the speed simulations, i need the minimum agent move speed in SimulationSettings.py to be 0. i assign this
    # to the MinMoveSpeed variable in SimulationSettings, so that if i change it in the future, i don't need to change
    # every reference in the code.
    SimulationSettings.SimulationSettings.MinMoveSpeed = 0

    return [critict, IPC_all, current_i]


# this function 'line42day' was used in the original food_flee.py file. it changes the current row being focused on
# in the IPC matrix, by updating the critict variable to match the day of the simulation. i did not edit this function.
def line42day(t, current_i, critict):
    current_critict = critict[current_i]
    while current_critict < t:
        current_i = current_i + 1
        current_critict = critict[current_i]
    return current_critict


# This is a small addition to the location class. The _init_ function of the location class
# from flee is given variables for region and IPC, so that the locations in the simulation can hold the information
# provided by the IPC data file.
class Location(flee.Location):
    def __init__(self, name, x=0.0, y=0.0, movechance=0.001, capacity=-1, pop=0, foreign=False, country="unknown",
                 region="unknown", IPC=0):
        super().__init__(name, x, y, movechance, capacity, pop, foreign, country)
        self.region = region  # the IPC data is stored in a matrix, organised by region. each location in the
        # simulation resides in one of these regions.
        self.IPC = IPC  # This is where the IPC value is stored for each location.


# I import the person class from the original Flee.py file, but i add a speed variable.
class Person(flee.Person):
    def __init__(self, location):
        super().__init__(location)
        self.speed = 200  # this is the unique speed variable which is updated by the Update_IPC function.

    # i need my speed variable to be used in the finish_travel function, imported from flee.py. any changes made by me
    # have been pointed out by comments.
    def finish_travel(self, distance_moved_this_timestep=0):
        if self.travelling:

            # originally, the distance travelled was set to a static value. now, my speed variable is used, so that each
            # agent has their own speed, based on their current location's food security.
            self.distance_travelled_on_link += self.speed
            # print(self.distance_travelled_on_link) - for testing my changes

            if self.distance_travelled_on_link - distance_moved_this_timestep > self.location.distance:

                if SimulationSettings.SimulationSettings.AgentLogLevel > 0:
                    self.places_travelled += 1
                    self.distance_travelled += self.location.distance

                if self.location.closed == True:
                    self.location.numAgentsOnRank -= 1
                    self.location = self.location.startpoint
                    self.location.numAgentsOnRank += 1
                    self.travelling = False
                    self.distance_travelled_on_link = 0

                else:

                    # usually here, an agent will go through another evolve() if it moves less than the minimum
                    # speed. in the case of the speed simulations, i've changed the minimum speed value to 0. this
                    # keeps the simulation behaving in a way that is true to my hypothesis. people only move as far
                    # as their 'speed' allows them to, with no repeat runs of evolve().
                    evolveMore = False
                    if self.location.distance + distance_moved_this_timestep < SimulationSettings.SimulationSettings.MinMoveSpeed:
                        distance_moved_this_timestep += self.location.distance
                        evolveMore = True

                    self.location.numAgents -= 1
                    self.location = self.location.endpoint
                    self.location.numAgents += 1

                    self.travelling = False
                    self.distance_travelled_on_link = 0

                    if SimulationSettings.SimulationSettings.CampLogLevel > 0:
                        if self.location.Camp == True:
                            self.location.incoming_journey_lengths += [self.timesteps_since_departure]

                    if evolveMore == True:
                        self.evolve()
                        self.finish_travel(distance_moved_this_timestep)


class Ecosystem(flee.Ecosystem):
    def __init__(self):
        super().__init__()
        # this variable IPCAffectsMovementSpeed is a new one i've added which will trigger the speed changes. in
        # future work, where several hypotheses are implemented into one file, this would allow different hypotheses
        # to be active at different times.
        self.IPCAffectsMovementSpeed = True  # declares that IPC will effect the speed of the agents.

    # i designed and created this function to implement my speed hypothesis, using the formula and the pseudocode i
    # designed
    def update_IPC(self, line_IPC, IPC_all):
        # first, i cycle through each location in the simulation and give each an IPC value. because this function is
        # called whenever a new row is reached in the IPC data matrix (using the variable critict), the IPC value is
        # always up to date as the simulation progresses:
        for i in range(0, len(self.locationNames)):
            if self.locations[i].country == "South_Sudan":
                # Update the IPC scores for all locations by checking the location's region and assigning it that
                # region's IPC value from IPC_all
                self.locations[i].IPC = IPC_all.loc[line_IPC][self.locations[i].region]

        # next step, i cycle through each agent in the sim and give them a speed value based on their location.
        # the formula involves multiplying the maximum move speed of the agents by the IPC of that agent's location.
        for i in range(0, len(self.agents)):
            if self.IPCAffectsMovementSpeed:
                # find current location of the agent:
                agent_location = self.agents[i].location
                # when agents are located on links and not locations, they cannot be given an IPC value, so they are
                # given a speed of 100, halfway between minimum and maximum.
                if isinstance(agent_location, flee.Link):
                    self.agents[i].speed = 100
                else:
                    # if they are in a location and not a link, they can be given a custom speed.
                    # find the IPC value for the agent's current location:
                    agent_location_IPC = agent_location.IPC

                    # if the current IPC for an agent is zero, give the agent a minimum speed:
                    if agent_location.country != "South_Sudan":
                        self.agents[i].speed = 100

                    # check the agent's new speed by multiplying the max speed by the IPC value in decimal form.
                    # this is my formula being implemented as code.
                    else:
                        self.agents[i].speed = SimulationSettings.SimulationSettings.MaxMoveSpeed * \
                                               (agent_location_IPC / 100.0)
                        if self.agents[i].speed > 200:
                            self.agents[i].speed = 200
                    # print(self.agents[i].speed) - another test i was running to check for the correct output

    # this function, printinfo, prints specific details for each location, into the console as the simulation runs.
    # it is called every time the IPC values are updated.
    def printInfo(self):
        for l in range(len(self.locations)):
            print(self.locations[l].name, "Conflict? ", self.locations[l].conflict, "Population:",
                  self.locations[l].pop, "IPC:", self.locations[l].IPC, "MC:",
                  self.locations[l].movechance, file=sys.stderr)

    # the rest of the functions here are not developed or modified by me at all. these are just a necessary inclusion
    # to ensure that the above functions are being called correctly when the simulation runs.
    def addLocation(self, name, x="0.0", y="0.0", movechance=SimulationSettings.SimulationSettings.DefaultMoveChance,
                    capacity=-1, pop=0, foreign=False, country="unknown", region="unknown", IPC=0):
        l = Location(name, x, y, movechance, capacity, pop, foreign, country, region, IPC)
        self.locations.append(l)
        self.locationNames.append(l.name)
        return l

    def addAgent(self, location):
        if SimulationSettings.SimulationSettings.TakeRefugeesFromPopulation:
            if location.conflict:
                if location.pop > 0:
                    location.pop -= 1
                    location.numAgentsSpawned += 1
                else:
                    print(
                        "ERROR: Number of agents in the simulation is larger than the combined population of the conflict zones. Please amend locations.csv.",
                        file=sys.stderr)
                    location.print()
                    assert location.pop > 1

        self.agents.append(Person(location))

    def evolve(self):

        for l in self.locations:
            l.updateLocationScore(self.time)

        for l in self.locations:
            l.updateNeighbourhoodScore()

        for l in self.locations:
            l.updateRegionScore()

        for a in self.agents:
            a.evolve()

        for a in self.agents:
            a.finish_travel()

        if SimulationSettings.SimulationSettings.CampLogLevel > 0:
            self._aggregate_arrivals()

        if SimulationSettings.SimulationSettings.AgentLogLevel > 0:
            write_agents(self.agents, self.time)

        self.time += 1