# speed_food_flee.py

# modified version of food flee implementation by Chris Vassiliou. This version implements my hypotheses for speed:
# "The higher the food insecurity, the faster migrants are likely to move."
# instead of adjusting movechance, we adjust the movespeed of the agents.

import numpy as np
import sys
import random
from flee import SimulationSettings
from flee import flee
import csv
import pandas as pd


# this function finds the IPC food data and assigns it to two variables, critict and IPC_all. critict is the just the
# dates column. IPC_all stores every cell in the file.
def initiate_food():
    critict = pd.read_csv("~/codes/FabSim3/plugins/FabFlee/config_files/flee_ssudan_food/input_csv/IPC.csv")[
        "Dates"]
    IPC_all = pd.read_csv("~/codes/FabSim3/plugins/FabFlee/config_files/flee_ssudan_food/input_csv/IPC.csv",
                          index_col=0)
    current_i = 0

    # added for testing output by chris vassiliou
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', -1)

    # for the speed simulations, i need the minmovespeed in SimulationSettings.py to be 0.
    SimulationSettings.SimulationSettings.MinMoveSpeed = 0
    # print(new_min_speed)

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


# this code imports the Person class from the original Flee.py file and adds a custom speed variable.
class Person(flee.Person):
    def __init__(self, location):
        super().__init__(location)
        self.custom_speed = 200

    def finish_travel(self, distance_moved_this_timestep=0):
        if self.travelling:

            # added by chris vassiliou
            # here, the simulations used to take a static value for speed. now, it takes a speed value which changes
            # based on a formula in UPDATE_IPC
            self.distance_travelled_on_link += self.custom_speed
            # print(self.distance_travelled_on_link)
            # If destination has been reached.
            if self.distance_travelled_on_link - distance_moved_this_timestep > self.location.distance:

                # update agent logs
                if SimulationSettings.SimulationSettings.AgentLogLevel > 0:
                    self.places_travelled += 1
                    self.distance_travelled += self.location.distance

                # if link is closed, bring agent to start point instead of the destination and return.
                if self.location.closed == True:
                    self.location.numAgentsOnRank -= 1
                    self.location = self.location.startpoint
                    self.location.numAgentsOnRank += 1
                    self.travelling = False
                    self.distance_travelled_on_link = 0

                else:

                    # usually here, an agent will go through another evolve() if it moves less than the minimum
                    # speed. in the case of the speed simulations, i've changed the minimum speed value to 0.
                    evolveMore = False
                    if self.location.distance + distance_moved_this_timestep < SimulationSettings.SimulationSettings.MinMoveSpeed:
                        distance_moved_this_timestep += self.location.distance
                        evolveMore = True

                    # update location (which is on a link) to link endpoint
                    self.location.numAgents -= 1
                    self.location = self.location.endpoint
                    self.location.numAgents += 1

                    self.travelling = False
                    self.distance_travelled_on_link = 0

                    if SimulationSettings.SimulationSettings.CampLogLevel > 0:
                        if self.location.Camp == True:
                            self.location.incoming_journey_lengths += [self.timesteps_since_departure]

                    # Perform another evolve step if needed. And if it results in travel, then the current
                    # travelled distance needs to be taken into account.
                    if evolveMore == True:
                        self.evolve()
                        self.finish_travel(distance_moved_this_timestep)


class Ecosystem(flee.Ecosystem):
    def __init__(self):
        super().__init__()
        # this variable is a new one i've added which will trigger the speed changes.
        self.IPCAffectsMovementSpeed = True  # IPC data affects the speed of the agents.

        self.IPCAffectsSpawnLocation = False

    # this function i've created will implement my speed hypothesis.
    def update_IPC(self, line_IPC, IPC_all):
        # first, cycle through each location in the simulation and give each an IPC value, which changes with the time:
        for i in range(0, len(self.locationNames)):
            if self.locations[i].country == "South_Sudan":
                # 1. Update IPC scores for all locations
                self.locations[i].IPC = IPC_all.loc[line_IPC][self.locations[i].region]

        # next step, we need to cycle through each agent in the sim and give them a speed value based on their location.
        # the formula involves multiplying the maximum move speed of the agents by the IPC of that agent's location.
        for i in range(0, len(self.agents)):
            if self.IPCAffectsMovementSpeed:
                # find the location for the current agent:
                agent_location = self.agents[i].location
                # when agents are located on links and not locations, they cannot be given an IPC value.
                if isinstance(agent_location, flee.Link):
                    self.agents[i].custom_speed = 200
                else:
                    # find the IPC value for the current agent's current location:
                    agent_location_IPC = agent_location.IPC

                    # this was a test i was running so i could see the output for each agent in the sim.
                    # agent_location_name = agent_location.name
                    # agent_region = agent_location.region
                    # test_string = "for agent %i the location is %a the region is %r the IPC is %f and the speed is " \
                    #               "below." % (i, agent_location_name, agent_region, agent_location_IPC)
                    # print(test_string)

                    # if IPC is zero, give the agent a minimum speed:
                    if agent_location_IPC == 0:
                        self.agents[i].custom_speed = 10
                    # else, check the agent's new speed by multiplying the max speed by the IPC value as a decimal.
                    else:
                        self.agents[i].custom_speed = SimulationSettings.SimulationSettings.MaxMoveSpeed * \
                                                      (agent_location_IPC / 100.0)
                        if self.agents[i].custom_speed > 200:
                            self.agents[i].custom_speed = 200
                    # print(self.agents[i].custom_speed)

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
        # if SimulationSettings.SimulationSettings.InitLogLevel > 0:
        # print("Location:", name, x, y, l.movechance, capacity, ", pop. ", pop, foreign, "State: ", l.region,
        #       "IPC: ", l.IPC)
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
        # update level 1, 2 and 3 location scores
        for l in self.locations:
            l.updateLocationScore(self.time)

        for l in self.locations:
            l.updateNeighbourhoodScore()

        for l in self.locations:
            l.updateRegionScore()

        # update agent locations
        for a in self.agents:
            a.evolve()

        for a in self.agents:
            a.finish_travel()

        # update link properties
        if SimulationSettings.SimulationSettings.CampLogLevel > 0:
            self._aggregate_arrivals()

        if SimulationSettings.SimulationSettings.AgentLogLevel > 0:
            write_agents(self.agents, self.time)

        self.time += 1
