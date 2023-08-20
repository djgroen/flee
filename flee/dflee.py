from __future__ import annotations, print_function
from flee import flee
import copy
import os
import random
import math
import sys
from typing import List, Optional, Tuple
import numpy as np
from flee.Diagnostics import write_agents, write_links
from flee.SimulationSettings import SimulationSettings
import flee.moving as moving
import flee.dspawning as spawning
import flee.scoring as scoring

if os.getenv("FLEE_TYPE_CHECK") is not None and os.environ["FLEE_TYPE_CHECK"].lower() == "true":
    from beartype import beartype as check_args_type
else:
    def check_args_type(func):
        return func


class Person(flee.Person):
    """
    The Person class
    """

    __slots__ = [
        "location",
        "distance_travelled",
        "home_location",
        "timesteps_since_departure",
        "places_travelled",
        "recent_travel_distance",
        "distance_moved_this_timestep",
        "travelling",
        "distance_travelled_on_link",
        "attributes",
        "locations_visited",
        "route",
    ]

    @check_args_type
    def __init__(self, location, attributes):
        super().__init__(location, attributes)

    @check_args_type
    def evolve(self, e, time: int, flood_level: int = 0) -> None:
        """
        Summary

        Args:
            time (int): Description
            ForceTownMove (bool, optional): towns have a move chance of 1.0.
        """
        super().evolve(e, time=time)

        if self.travelling is False:
            if flood_level > 0: # called through evolveMore
                movechance *= (float(max(self.location.pop, self.location.capacity)) / SimulationSettings.move_rules["MovechancePopBase"])**SimulationSettings.move_rules["MovechancePopScaleFactor"]
            else:
                movechance = 0

            outcome = random.random()
            # print(movechance)

            if outcome < movechance:
                #only plan a route if the agent has no existing route.
                if len(self.route) == 0:
                    # determine here which route to take
                    self.route = moving.selectRoute(self, time=time)

                # attempt to follow route. Return None if fail.    
                chosenDest = self.take_next_step(e)

                # if there is a viable route to a different location.
                if chosenDest:
                    # update location to link endpoint
                    self.handle_travel(chosenDest, travelling=True)

class Location(flee.Location):
    """
    The Location class of DFlee
    """

    @check_args_type
    def __init__(
        self,
        name: str,
        x: float = 0.0,
        y: float = 0.0,
        location_type: Optional[str] = None,
        movechance: float = 0.001,
        capacity: int = -1,
        pop: int = 0,
        foreign: bool = False,
        country: str = "unknown",
        attributes: dict = {},
    ) -> None:
        self.flood = -1.0
        self.flood_time = -1 # date that last flood erupted.
        self.time_of_flood = -1 # Time that a major flood event last took place.
        self.numAgentsSpawned = 0

        if location_type is not None:
            if "camp" in location_type.lower():
                self.movechance = SimulationSettings.move_rules["CampMoveChance"]
                self.camp = True
                if "idp" in location_type.lower():
                    self.idpcamp = True
                    self.movechance = SimulationSettings.move_rules["IDPCampMoveChance"]
            elif "flood" in location_type.lower():
                self.movechance = SimulationSettings.move_rules["FloodMoveChance"]
                self.flood = float(self.attributes.get("flood_level",1.0))
            elif "forward" in location_type.lower():
                self.movechance = 1.0
                self.forward = True
            elif "marker" in location_type.lower():
                self.movechance = 1.0
                self.marker = True
            elif "default" in location_type.lower() or "town" in location_type.lower():
                self.town = True
                self.movechance = SimulationSettings.move_rules["DefaultMoveChance"]
            else:
                print(
                    "Error in creating Location() object: cannot parse location_type value of"
                    " {} for location object with name {}".format(location_type, name),
                    file=sys.stderr

                )

        # Automatically tags a location as a Camp if refugees are less than 2%
        # likely to move out on a given day.
        if self.movechance < 0.005 and not self.camp:
            print(
                "Warning: automatically setting location {} to camp, "
                "as movechance = {}".format(self.name, self.movechance),
                file=sys.stderr,
            )
            self.camp = True
            self.town = False

        self.scores = np.array([1.0, 1.0, 1.0, 1.0])

        scoring.updateLocationScore(0,self)
        #scoring.updateNeighbourhoodScore(self)
        #scoring.updateRegionScore(self)

        if SimulationSettings.log_levels["camp"] > 0:
            # reinitializes every time step. Contains individual journey
            # lengths from incoming agents.
            self.incoming_journey_lengths = []

        self.print()

    @check_args_type
    def SetCamp(self) -> None:
        """
        Summary
        """
        self.movechance = SimulationSettings.CampMoveChance
        self.camp = True
        self.foreign = True
        self.flood = False
        self.town = False

    @check_args_type
    def calculateDistance(self, other_location) -> float:
        """
        Summary: Calculate distance between this location and another one.
        This concerns distance as the bird flies.
        """
        # Approximate radius of earth in km
        R = 6373.0

        lat1 = math.radians(self.y)
        lon1 = math.radians(self.x)
        lat2 = math.radians(other_location.y)
        lon2 = math.radians(other_location.x)

        dlon = lon2 - lon1
        dlat = lat2 - lat1

        a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    @check_args_type
    def open_camp(self, IDP=False) -> None:
        """
        Summary: change location type to camp or IDP camp.
        """
        super().__init__(IDP=IDP)
        self.flood = -1.0

    @check_args_type
    def close_camp(self, IDP=False) -> None:
        """
        Summary: change location type to town.
        """
        super().__init__(IDP=IDP)
        self.flood = -1.0
 
    @check_args_type
    def print(self) -> None:
        """
        Summary
        """
        print(
            "Location name: {}, X: {}, Y: {}, movechance: {}, cap: {}, "
            "pop: {}, country: {}, flood? {}, camp? {}, foreign? {}, attributes: {}".format(
                self.name,
                self.x,
                self.y,
                self.movechance,
                self.capacity,
                self.pop,
                self.country,
                self.flood,
                self.camp,
                self.foreign,
                self.attributes,
            ),
            file=sys.stderr,
        )
        for link in self.links:
            print(
                "Link from {} to {}, dist: {}, pop. {}".format(
                    self.name, link.endpoint.name, link.get_distance(), link.numAgents
                ),
                file=sys.stderr,
            )

    @check_args_type
    def SetFloodMoveChance(self) -> None:
        """
        Modify move chance to the default value set for flood regions.
        """
        self.movechance = SimulationSettings.move_rules["FloodMoveChance"]

class Link(flee.Link):
    """
    the Link class
    """

    @check_args_type
    def __init__(self, startpoint, endpoint, link_type, distance: float, forced_redirection: bool = False, attributes: dict = {}):
        super().__init__(startpoint, endpoint, distance, forced_redirection, attributes)
        self.link_type = link_type


    def get_linktype(self) -> str:
        """
        It returns the link type.

        Args:

        Returns:
            str: walk, drive, or crossing
        """
        return self.link_type


class Ecosystem(flee.Ecosystem):
    """
    the Ecosystem class
    """

    def __init__(self):

        super().__init__()

    @check_args_type
    def add_flood_zone(self, name: str, flood_level: float = 1.0, change_movechance: bool = True) -> None:
        """
        Adds a flood zone and its level. Default weight is equal to
        population of the location.

        Args:
            name (str): Description
            flood_level (int): Description
            change_movechance (bool, optional): Description

        Returns:
            None: Description
        """
        for i in range(0, len(self.locationNames)):
            #print('the flood level of {} is {}'.format(self.locationNames[i],flood_level))
            if self.locationNames[i] == name:
                if change_movechance:
                    self.locations[i].movechance = SimulationSettings.move_rules["FloodMoveChance"]
                    self.locations[i].flood = flood_level
                    self.locations[i].town = False

                self.locations[i].time_of_flood = self.time                  
                spawning.refresh_spawn_weights(self)

                if SimulationSettings.log_levels["init"] > 0:
                    print("Added flood zone: {}, pop: {}, flood level: {}".format(name, self.locations[i].pop, flood_level), file=sys.stderr)
                    print("New total spawn weight: ", sum(self.spawn_weights), file=sys.stderr)
                return


        print("Diagnostic: self.locationNames: ", self.locationNames, file=sys.stderr)
        print(
            "ERROR in flee.add_flood_zone: location with name [{}] "
            "appears not to exist in the FLEE ecosystem "
            "(see diagnostic above).".format(name),
            file=sys.stderr,
        )

    @check_args_type
    def remove_flood_zone(self, name: str, change_movechance: bool = True) -> None:
        """
        Shorthand function to remove a flood zone from the list.
        (not used yet)

        Args:
            name (str): Description
            change_movechance (bool, optional): Description
        """
        for i in range(0, len(self.locationNames)):
            if self.locationNames[i] == name:
                if change_movechance:
                    self.locations[i].movechance = SimulationSettings.move_rules["DefaultMoveChance"]
                self.locations[i].flood = -1.0
                self.locations[i].town = True

        spawning.refresh_spawn_weights(self)


    @check_args_type
    def evolve(self) -> None:
        """
        Summary
        """

        spawning.refresh_spawn_weights(self) # Required to correctly incorporate TakeFromPopulation and FloodSpawnDecay.

        # update level 1, 2 and 3 location scores
        for loc in self.locations:
            scoring.updateLocationScore(self.time, loc)

        # update agent locations
        for a in self.agents:
            if SimulationSettings.log_levels["agent"] > 1:
                a.locations_visited = []
            if a.location is not None:
                a.evolve(self, time=self.time)

        for a in self.agents:
            if a.location is not None:
                a.finish_travel(self, time=self.time)
                a.timesteps_since_departure += 1


        if SimulationSettings.log_levels["agent"] > 0:
            write_agents(agents=self.agents, time=self.time)

        if SimulationSettings.log_levels["link"] > 0:
            write_links(locations=self.locations, time=self.time)

        for a in self.agents:
            a.recent_travel_distance = (
                a.recent_travel_distance
                + (a.distance_moved_this_timestep / SimulationSettings.move_rules["MaxMoveSpeed"])
            ) / 2.0
            a.distance_moved_this_timestep = 0

        # update link properties
        if SimulationSettings.log_levels["camp"] > 0:
            self._aggregate_arrivals()

        # Deactivate agents in camps with a certain probability.
        if SimulationSettings.spawn_rules["camps_are_sinks"] == True:
            for a in self.agents:
                if a.travelling == False:
                    if a.location is not None:
                        if a.location.camp == True:
                            outcome = random.random()
                            if outcome < a.location.attributes.get("deactivation_probability", 0.0):
                                a.location = None

        self.time += 1


    @check_args_type
    def addAgent(self, location, attributes) -> None:
        """
        Summary

        Args:
            location (Location): Description
        """
        if SimulationSettings.spawn_rules["TakeFromPopulation"]:
            if location.flood > 0.0:
                if location.pop > 0:
                    location.pop -= 1
                    location.numAgentsSpawned += 1
                else:
                    print(
                        "ERROR: Number of agents in the simulation is larger than the combined "
                        "population of the flood zones. Please amend locations.csv."
                    )
                    location.print()
                    assert location.pop > 1

        self.agents.append(Person(location=location, attributes=attributes))



    @check_args_type
    def linkUp(
        self,
        endpoint1: str,
        endpoint2: str,
        link_type: str,
        distance: float = 1.0,
        forced_redirection: bool = False,
        attributes: dict = {},
    ) -> None:
        """
        Creates a link between two endpoint locations


        Args:
            endpoint1 (str): Description
            endpoint2 (str): Description
            distance (float, optional): Description
            forced_redirection (bool, optional): Description
        """
        endpoint1_index = -1
        endpoint2_index = -1
        for i in range(0, len(self.locationNames)):
            if self.locationNames[i] == endpoint1:
                endpoint1_index = i
            if self.locationNames[i] == endpoint2:
                endpoint2_index = i

        if endpoint1_index < 0:
            print("Diagnostic: Ecosystem.locationNames: ", self.locationNames, file=sys.stderr)
            print(
                "Error: link created to non-existent source: {}  with dest {}".format(
                    endpoint1, endpoint2, file=sys.stderr
                )
            )
            sys.exit()
        if endpoint2_index < 0:
            print("Diagnostic: Ecosystem.locationNames: ", self.locationNames, file=sys.stderr)
            print(
                "Error: link created to non-existent destination: {} with source {}".format(
                    endpoint2, endpoint1, file=sys.stderr
                )
            )
            sys.exit()

        self.locations[endpoint1_index].links.append(
            Link(
                startpoint=self.locations[endpoint1_index],
                endpoint=self.locations[endpoint2_index],
                distance=distance,
                forced_redirection=forced_redirection,
                link_type=link_type,
                attributes=attributes,
            )
        )
        self.locations[endpoint2_index].links.append(
            Link(
                startpoint=self.locations[endpoint2_index],
                endpoint=self.locations[endpoint1_index],
                distance=distance,
                link_type=link_type,
                attributes=attributes,
            )
        )

    @check_args_type
    def printInfo(self) -> None:
        """
        Summary
        """
        print(
            "Time: {}, # of agents: {}, # of flood zones {}.".format(
                self.time, len(self.agents), len(self.flood_zones)
            ),
            file=sys.stderr,
        )
        if len(self.flood_zones) > 0:
            print(
                "First flood zone is called {}".format(self.flood_zones[0].name),
                file=sys.stderr,
            )
        for loc in self.locations:
            print(loc.name, loc.numAgents, file=sys.stderr)


