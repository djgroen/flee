from __future__ import annotations, print_function

import copy
import os
import random
import math
import sys
from typing import List, Optional, Tuple

import numpy as np
from dflee.Diagnostics import write_agents, write_links
from dflee.SimulationSettings import SimulationSettings
import dflee.moving as moving
import dflee.spawning as spawning
import dflee.scoring as scoring

if os.getenv("FLEE_TYPE_CHECK") is not None and os.environ["FLEE_TYPE_CHECK"].lower() == "true":
    from beartype import beartype as check_args_type
else:
    def check_args_type(func):
        return func


class Person:
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
        "age",
        "gender",
        "attributes",
        "locations_visited",
        "route",
    ]

    @check_args_type
    def __init__(self, location, age, gender, attributes):
        self.location = location
        self.home_location = location
        self.timesteps_since_departure = 0
        self.places_travelled = 1

        # An index of how much the agent has recently traveled
        # (range : 0.0-1.0).
        self.recent_travel_distance = 0.0
        # Number of km moved this timestep.
        self.distance_moved_this_timestep = 0.0

        # Set to true when an agent resides on a link.
        self.travelling = False

        # Tracks how much distance a Person has been able to travel on the
        # current link.
        self.distance_travelled_on_link = 0

        self.age=age
        self.gender=gender
        self.attributes=attributes
        self.route = []

        if SimulationSettings.log_levels["agent"] > 0:
            self.distance_travelled = 0
            # track total distance travelled.
        if SimulationSettings.log_levels["agent"] > 1:
            self.locations_visited = [] 
            # track and write locations visited before final one in timestep.

        self.location.IncrementNumAgents(self)

    @check_args_type
    def getBaseEndPointScore(self, link) -> float:
        """
        Serial base endpoint score retrieval.

        Args:
            link (Link) : Description

        Returns:
            float: Description
        """
        return link.endpoint.scores[1]


    @check_args_type
    def handle_travel(self, location, travelling) -> None:
        """
        Summary

        Args:
            location: location to travel to (can be Location of Link type).
            travelling: set to True if location is a Link, False if it is a Location object.
        """
        self.location.DecrementNumAgents()
        self.location = location
        self.location.IncrementNumAgents(self)
        self.travelling = travelling
        self.distance_travelled_on_link = 0

    def check_dest_is_full_camp(self,e):
        for i in range(0, len(e.locationNames)):
            if e.locationNames[i] == self.route[-1]:
                if e.locations[i].camp and moving.getCapMultiplier(e.locations[i],1) < 0.5:
                    #print(e.time, e.locationNames[i], self.route[-1], file=sys.stderr)
                    return True
                else: 
                    return False


    def take_next_step(self,e):
        for l in self.location.links:
            if l.endpoint.name == self.route[0]:
                if self.check_dest_is_full_camp(e):
                    self.route = []
                    return None
                self.route = self.route[1:]
                return l

        # Link has vanished, remove route.
        self.route = []
        return None


    @check_args_type
    def evolve(self, e, time: int, ForceTownMove: bool = False) -> None:
        """
        Summary

        Args:
            time (int): Description
            ForceTownMove (bool, optional): Description
        """

        if self.travelling is False:
            if self.location.town and ForceTownMove: # called through evolveMore
                movechance = 1.0
            else: # called first time in loop
                movechance = self.location.movechance
                movechance *= (float(max(self.location.pop, self.location.capacity)) / SimulationSettings.move_rules["MovechancePopBase"])**SimulationSettings.move_rules["MovechancePopScaleFactor"]

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

    @check_args_type
    def finish_travel(self, e, time: int) -> None:
        """
        Summary

        Args:
            time (int): Description
        """
        if self.travelling:

            todays_travel_speed = float(self.location.attributes.get("max_move_speed", SimulationSettings.move_rules["MaxMoveSpeed"]))

            if self.places_travelled == 1 and SimulationSettings.move_rules["StartOnFoot"]:
                todays_travel_speed = SimulationSettings.move_rules["MaxWalkSpeed"]

            # Flee 3.0: support for walk_probability attribute on links.
            walk_probability = float(self.location.attributes.get("walk_probability","0.0"))
            if random.random() < walk_probability:
                todays_travel_speed = SimulationSettings.move_rules["MaxWalkSpeed"]

            self.distance_travelled_on_link += todays_travel_speed
            self.distance_moved_this_timestep += todays_travel_speed

            # If destination has been reached.
            if self.distance_travelled_on_link > self.location.get_distance():

                self.places_travelled += 1
                # remove the excess km tracked by the
                # distance_moved_this_timestep var.
                self.distance_moved_this_timestep += (
                    self.location.get_distance() - self.distance_travelled_on_link
                )

                # update agent logs
                if SimulationSettings.log_levels["agent"] > 0:
                    self.distance_travelled += self.location.get_distance()

                # if link is closed, bring agent to start point instead of the
                # destination and return.
                if self.location.closed is True:
                    self.handle_travel(self.location.startpoint, travelling=False)

                else:
                    # if the person has moved less than the MaxMoveSpeed, it
                    # should go through another evolve() step in the new
                    # location.
                    evolveMore = False
                    if self.distance_moved_this_timestep < todays_travel_speed:
                        if SimulationSettings.log_levels["agent"] > 1:
                            self.locations_visited.append(self.location)
                        evolveMore = True

                    # update location (which is on a link) to link endpoint
                    self.handle_travel(self.location.endpoint, travelling=False)

                    if SimulationSettings.log_levels["camp"] > 0:
                        if self.location.camp is True:
                            self.location.incoming_journey_lengths += [
                                self.timesteps_since_departure
                            ]

                    # Perform another evolve step if needed. And if it results
                    # in travel, then the current traveled distance needs
                    # to be taken into account.
                    # Note MaxMoveSpeed is used here, not todays_travel_speed.
                    if evolveMore is True:
                        ForceTownMove = False
                        if SimulationSettings.move_rules["AvoidShortStints"]:
                            # Flee 2.0 Changeset 1, factor 2.
                            if (
                                self.recent_travel_distance
                                + (
                                    self.distance_moved_this_timestep
                                    / SimulationSettings.move_rules["MaxMoveSpeed"]
                                )
                            ) / 2.0 < 0.5:
                                ForceTownMove = True
                        self.evolve(e, time=time, ForceTownMove=ForceTownMove)
                        self.finish_travel(e, time=time)


class Location:
    """
    The Location class
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
        self.name = name
        self.x = x
        self.y = y
        self.movechance = movechance
        self.links = []  # paths connecting to other towns
        # paths connecting to other towns that are closed.
        self.closed_links = []
        self.numAgents = 0  # refugee population
        # refugee population on current rank (for pflee).
        self.numAgentsOnRank = 0
        self.capacity = capacity  # refugee capacity
        self.pop = pop  # non-refugee population
        self.foreign = foreign
        self.country = country
        self.flood = -1.0
        self.flood_time = -1 # date that last flood erupted.
        self.camp = False
        self.idpcamp = False
        self.town = False
        self.forward = False
        self.marker = False
        self.time_of_flood = -1 # Time that a major flood event last took place.
        self.numAgentsSpawned = 0

        self.attributes = attributes # This will store a range of attributes that are read from file.

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
        self.movechance = SimulationSettings.move_rules["CampMoveChance"]
        self.camp = True
        self.flood = -1.0
        self.town = False
        self.forward = False
        self.marker = False
        if IDP:
            self.idpcamp = True
            self.movechance = SimulationSettings.move_rules["IDPCampMoveChance"]


    @check_args_type
    def setAttribute(self, name: str, value) -> None:
        self.attributes[name] = value


    @check_args_type
    def close_camp(self, IDP=False) -> None:
        """
        Summary: change location type to town.
        """
        self.movechance = SimulationSettings.move_rules["DefaultMoveChance"]
        self.camp = False
        self.idpcamp = False
        self.flood = -1.0
        self.town = True
        self.forward = False
        self.marker = False

    @check_args_type
    def DecrementNumAgents(self) -> None:
        """
        Summary
        """
        self.numAgents -= 1

    @check_args_type
    def IncrementNumAgents(self, agent) -> None:
        """
        Summary
        """
        self.numAgents += 1

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

    @check_args_type
    def SetCampMoveChance(self) -> None:
        """
        Modify move chance to the default value set for camps.
        """
        self.movechance = SimulationSettings.CampMoveChance


    @check_args_type
    def getScore(self, index: int) -> float:
        """
        Summary

        Args:
            index (int): Description

        Returns:
            float: Description
        """
        return self.scores[index]

    @check_args_type
    def setScore(self, index: int, value: float) -> None:
        """
        Summary

        Args:
            index (int): Description
            value (float): Description
        """
        self.scores[index] = value


class Link:
    """
    the Link class
    """

    @check_args_type
    def __init__(self, startpoint, endpoint, link_type, distance: float, forced_redirection: bool = False, attributes: dict = {}):
        self.name = "L:{}:{}".format(startpoint.name, endpoint.name)
        self.closed = False

        # distance in km.
        self.__distance = distance
        self.link_type = link_type

        # links for now always connect two endpoints
        self.startpoint = startpoint
        self.endpoint = endpoint
        self.x = (self.startpoint.x + self.endpoint.x) / 2.0
        self.y = (self.startpoint.y + self.endpoint.y) / 2.0

        # number of agents that are in transit.
        self.numAgents = 0
        self.cumNumAgents = 0 # cumulative # of agents
        if SimulationSettings.log_levels["link"] > 1:
            self.cumNumAgentsByAttribute = {}
        # refugee population on current rank (for pflee).
        self.numAgentsOnRank = 0

        # if True, then all Persons will go down this link.
        self.forced_redirection = forced_redirection
        self.attributes = attributes

    @check_args_type
    def DecrementNumAgents(self) -> None:
        """
        Summary
        """
        self.numAgents -= 1

    @check_args_type
    def IncrementNumAgents(self, agent) -> None:
        """
        Summary
        """
        self.numAgents += 1
        self.cumNumAgents += 1

        if SimulationSettings.log_levels["link"] > 1:
            for a in agent.attributes:
                category = self.cumNumAgentsByAttribute.get(a, {})
                category[agent.attributes[a]] = category.get(agent.attributes[a], 0) + 1
                self.cumNumAgentsByAttribute[a] = category
            #print(category, file=sys.stderr)

    @check_args_type
    def setAttribute(self, name: str, value) -> None:
        self.attributes[name] = value

    def get_distance(self) -> float:
        """
        Summary

        Args:

        Returns:
            float: Description
        """
        return self.__distance

    def get_linktype(self) -> str:
        """
        It returns the link type.

        Args:

        Returns:
            str: walk, drive, or crossing
        """
        return self.link_type


class Ecosystem:
    """
    the Ecosystem class
    """

    @check_args_type
    def __init__(self):
        self.locations = []
        self.locationNames = []
        self.agents = []
        self.closures = []  # format [type, source, dest, start, end]
        self.time = 0
        self.print_location_output = True  # print location output data

        # FLEE3 does not have a flood zone list, and spawn weights cover all locations.
        self.spawn_weights = np.array([])

        if SimulationSettings.log_levels["camp"] > 0:
            self.num_arrivals = []  # one element per time step.
            self.travel_durations = []  # one element per time step.

    @check_args_type
    def get_camp_names(self) -> List[str]:
        """
        Summary

        Returns:
            List[str]: Description
        """

        camp_names = []
        for loc in self.locations:

            if loc.camp:
                camp_names += [loc.name]
        return camp_names

    @check_args_type
    def export_graph(self, use_ids_instead_of_names: bool = False) -> Tuple[List[str], List[List]]:
        """
        Summary

        Args:
            use_ids_instead_of_names (bool, optional): Description

        Returns:
            Tuple[List[str], List[List]]: Description
        """
        vertices = []
        edges = []
        for loc in self.locations:
            vertices += [loc.name]
            for p in loc.links:
                edges += [[loc.name, p.endpoint.name, p.get_distance()]]

        return vertices, edges

    @check_args_type
    def _aggregate_arrivals(self) -> None:
        """
        Add up arrival statistics, to find out travel durations and
        total number of camp arrivals.
        """
        if SimulationSettings.log_levels["camp"] > 0:
            arrival_total = 0
            tmp_num_arrivals = 0

            for loc in self.locations:
                if loc.camp is True:
                    arrival_total += np.sum(loc.incoming_journey_lengths)
                    tmp_num_arrivals += len(loc.incoming_journey_lengths)
                    loc.incoming_journey_lengths = []

            self.num_arrivals += [tmp_num_arrivals]

            if tmp_num_arrivals > 0:
                self.travel_durations += [float(arrival_total) / float(tmp_num_arrivals)]
            else:
                self.travel_durations += [0.0]

            # print("New arrivals: ", self.travel_durations[-1],
            #       arrival_total, tmp_num_arrivals)

    @check_args_type
    def enact_border_closures(self, time: int, twoway: bool = True, Debug: bool = False) -> None:
        """
        Summary

        Args:
            time (int): Description
            twoway (bool, optional): Description
            Debug (bool, optional): Description
        """
        # print("Enact border closures: ", self.closures)
        if len(self.closures) > 0:
            for c in self.closures:
                if time == c[3]:
                    if c[0] == "country":
                        if Debug:
                            print(
                                "Time = {}. Closing Border between "
                                "[{}] and [{}]".format(time, c[1], c[2]),
                                file=sys.stderr,
                            )
                        self.close_border(source_country=c[1], dest_country=c[2], twoway=twoway)
                    elif c[0] == "location":
                        self.close_location(location_name=c[1], twoway=twoway)
                    elif c[0] == "link":
                        self.close_link(startpoint=c[1], endpoint=c[2], twoway=twoway)
                    elif c[0] == "camp":
                        self.close_camp(c[1], IDP=False)
                    elif c[0] == "idpcamp":
                        self.close_camp(c[1], IDP=True)
                    elif c[0] == "remove_forced_redirection":
                        self.set_forced_redirection(c[1], c[2], False)

                if time == c[4]:
                    if c[0] == "country":
                        if Debug:
                            print(
                                "Time = {}. Reopening Border between "
                                "[{}] and [{}]".format(time, c[1], c[2]),
                                file=sys.stderr,
                            )
                        self.reopen_border(source_country=c[1], dest_country=c[2], twoway=twoway)
                    elif c[0] == "location":
                        self.reopen_location(location_name=c[1], twoway=twoway)
                    elif c[0] == "link":
                        self.reopen_link(startpoint=c[1], endpoint=c[2], twoway=twoway)
                    elif c[0] == "camp":
                        self.open_camp(c[1], IDP=False)
                    elif c[0] == "idpcamp":
                        self.open_camp(c[1], IDP=True)
                    elif c[0] == "remove_forced_redirection":
                        self.set_forced_redirection(c[1], c[2], True)

    @check_args_type
    def _convert_location_name_to_index(self, name: str) -> int:
        """
        Convert a location name to an index number

        Args:
            name (str): Description

        Returns:
            int: Description
        """
        x = -1
        # Convert name "startpoint" to index "x".
        for i, loc in enumerate(self.locations):
            if loc.name == name:
                x = i

        # for i in range(0, len(self.locations)):
        #     if self.locations[i].name == name:
        #         x = i

        if x < 0:
            print("#Warning: location not found in remove_link", file=sys.stderr)
            return False

        return x

    @check_args_type
    def _remove_link_1way(self, startpoint: str, endpoint: str, close_only: bool = False) -> bool:
        """
        Remove link in one direction
        (private function, use remove_link instead).
        close_only: if True will instead move the link to the closed_links
        list of the location, rendering it inactive.

        Args:
            startpoint (str): Description
            endpoint (str): Description
            close_only (bool, optional): Description

        Returns:
            bool: Description
        """
        new_links = []
        x = self._convert_location_name_to_index(name=startpoint)
        removed = False

        for i in range(0, len(self.locations[x].links)):
            if self.locations[x].links[i].endpoint.name is not endpoint:
                new_links += [self.locations[x].links[i]]
                continue

            if close_only:
                # print("Closing [%s] to [%s]" % (startpoint, endpoint),
                #       file=sys.stderr
                #       )
                self.locations[x].links[i].closed = True
                # we copy the route link to have a backup.
                self.locations[x].closed_links += [copy.copy(self.locations[x].links[i])]
                # The original object might still be used by agents as part of
                # finish_travel, but will be orphaned eventually.

                # make sure agent counts are set to 0.
                self.locations[x].closed_links[-1].numAgents = 0
                # ditto.
                self.locations[x].closed_links[-1].numAgentsOnRank = 0
            removed = True

        self.locations[x].links = new_links
        if not removed:
            print(
                "Warning: cannot remove link from {}, "
                "as there is no link to {}".format(startpoint, endpoint),
                file=sys.stderr,
            )
        return removed

    @check_args_type
    def _reopen_link_1way(self, startpoint: str, endpoint: str) -> bool:
        """
        Reopen a closed link.

        Args:
            startpoint (str): Description
            endpoint (str): Description

        Returns:
            bool: Description
        """
        new_closed_links = []
        x = self._convert_location_name_to_index(name=startpoint)
        reopened = False
        # print("Reopening link from {} to {}, "
        #       "closed link list length = {}.".format(
        #           startpoint, endpoint,
        #           len(self.locations[x].closed_links)),
        #       file=sys.stderr
        #       )

        for i in range(0, len(self.locations[x].closed_links)):
            if self.locations[x].closed_links[i].endpoint.name is not endpoint:
                # print("[{}] to [{}] ({})".format(
                #     startpoint,
                #     self.locations[x].closed_links[i].endpoint.name,
                #     endpoint),
                #     file=sys.stderr)
                new_closed_links += [self.locations[x].closed_links[i]]
            else:
                # print("Match: [{}] to [{}] ({})".format(
                #     startpoint,
                #     self.locations[x].closed_links[i].endpoint.name,
                #     endpoint),
                #     file=sys.stderr)
                self.locations[x].links += [self.locations[x].closed_links[i]]
                self.locations[x].links[-1].closed = False
                reopened = True

        self.locations[x].closed_links = new_closed_links
        if not reopened:
            print(
                "Warning: cannot reopen link from {},"
                " as there is no link to {}".format(startpoint, endpoint),
                file=sys.stderr,
            )
        return reopened

    @check_args_type
    def remove_link(
        self, startpoint: str, endpoint: str, twoway: bool = True, close_only: bool = False
    ) -> bool:
        """
        Removes a link between two location names.
        twoway: if True, also removes link from endpoint to startpoint.
        close_only: if True will instead move the link to the closed_links
        list of the location, rendering it inactive.

        Args:
            startpoint (str): Description
            endpoint (str): Description
            twoway (bool, optional): Description
            close_only (bool, optional): Description

        Returns:
            bool: Description
        """
        if twoway:
            return self._remove_link_1way(
                startpoint=endpoint, endpoint=startpoint, close_only=close_only
            )

        return self._remove_link_1way(
            startpoint=startpoint, endpoint=endpoint, close_only=close_only
        )

    @check_args_type
    def reopen_link(self, startpoint: str, endpoint: str, twoway: bool = True) -> bool:
        """
        Reopens a previously closed link between two location names.
        twoway: if True, also removes link from endpoint to startpoint.

        Args:
            startpoint (str): Description
            endpoint (str): Description
            twoway (bool, optional): Description

        Returns:
            bool: Description
        """
        if twoway:
            return self._reopen_link_1way(startpoint=endpoint, endpoint=startpoint)

        return self._reopen_link_1way(startpoint=startpoint, endpoint=endpoint)

    @check_args_type
    def close_link(self, startpoint: str, endpoint: str, twoway: bool = True) -> bool:
        """
        Shorthand call for remove_link, only moving the link to
        the closed list.

        Args:
            startpoint (str): Description
            endpoint (str): Description
            twoway (bool, optional): Description

        Returns:
            bool: Description
        """
        return self.remove_link(
            startpoint=startpoint, endpoint=endpoint, twoway=twoway, close_only=True
        )

    @check_args_type
    def _change_location_1way(
        self, location_name: str, mode: str = "close", direction: str = "both", Debug: bool = False
    ) -> bool:
        """
        Close all links to or from one location.
        mode: close or reopen
        direction: in, out or both.

        Args:
            location_name (str): Description
            mode (str, optional): Description
            direction (str, optional): Description
            Debug (bool, optional): Description

        Returns:
            bool: Description
        """

        dir_mode = 0
        if direction == "out":
            dir_mode = 1
        elif direction == "both":
            dir_mode = 2

        print(
            "{} location 1 way [{}] in direction {} ({}).".format(
                mode, location_name, direction, dir_mode
            ),
            file=sys.stderr,
        )
        changed_anything = False

        for i in range(0, len(self.locationNames)):
            if self.locationNames[i] == location_name:
                changed_anything = True

                link_set = self.locations[i].links
                if mode == "reopen":
                    link_set = self.locations[i].closed_links

                j = 0
                while j < len(link_set):
                    if Debug:
                        print(
                            "starting to {} link "
                            "[{}] [{}] in direction {}".format(
                                mode, location_name, link_set[j].endpoint.name, direction
                            ),
                            file=sys.stderr,
                        )
                    if mode == "close":

                        if dir_mode % 2 == 0:
                            self.close_link(
                                startpoint=link_set[j].endpoint.name,
                                endpoint=self.locationNames[i],
                                twoway=False,
                            )

                        if dir_mode > 0:
                            if self.close_link(
                                startpoint=self.locationNames[i],
                                endpoint=link_set[j].endpoint.name,
                                twoway=False,
                            ):
                                # shrink the link list. # This operation
                                # affects the overall loop, so no major
                                # operations should take place after this.
                                link_set = self.locations[i].links
                        else:
                            j += 1

                    elif mode == "reopen":

                        if dir_mode % 2 == 0:
                            self.reopen_link(
                                startpoint=link_set[j].endpoint.name,
                                endpoint=self.locationNames[i],
                                twoway=False,
                            )

                        if dir_mode > 0:
                            if self.reopen_link(
                                startpoint=self.locationNames[i],
                                endpoint=link_set[j].endpoint.name,
                                twoway=False,
                            ):
                                # shrink the closed link list. # This operation
                                # affects the overall loop, so no major
                                # operations should take place after this.
                                link_set = self.locations[i].closed_links
                            else:
                                j += 1

        return changed_anything

    @check_args_type
    def _change_border_1way(
        self, source_country: str, dest_country: str, mode: str = "close", Debug: bool = False
    ) -> None:
        """
        Close all links between two countries in one direction.

        Args:
            source_country (str): Description
            dest_country (str): Description
            mode (str, optional): Description
            Debug (bool, optional): Description
        """
        # print("{} border 1 way [{}] [{}]".format(
        #     mode, source_country, dest_country),file=sys.stderr)
        changed_anything = False
        for i in range(0, len(self.locationNames)):
            if self.locations[i].country == source_country:

                link_set = self.locations[i].links
                if mode == "reopen":
                    link_set = self.locations[i].closed_links

                j = 0
                while j < len(link_set):
                    if link_set[j].endpoint.country == dest_country:
                        if Debug:
                            print(
                                "starting to {} border 1 way "
                                "[{}/{}] [{}/{}]".format(
                                    mode,
                                    source_country,
                                    self.locations[i].name,
                                    dest_country,
                                    link_set[j].endpoint.name,
                                ),
                                file=sys.stderr,
                            )
                        changed_anything = True
                        if mode == "close":
                            if self.close_link(
                                startpoint=self.locationNames[i],
                                endpoint=link_set[j].endpoint.name,
                                twoway=False,
                            ):
                                link_set = self.locations[i].links
                                continue
                        elif mode == "reopen":
                            if self.reopen_link(
                                self.locationNames[i], link_set[j].endpoint.name, twoway=False
                            ):
                                link_set = self.locations[i].closed_links
                                continue
                    j += 1

        if not changed_anything:
            print(
                "Warning: no link closed when closing borders between "
                "{} and {}.".format(source_country, dest_country),
                file=sys.stderr,
            )

    @check_args_type
    def close_border(
        self, source_country: str, dest_country: str, twoway: bool = True, Debug: bool = False
    ) -> None:
        """
        Close all links between two countries. If twoway is set to false,
        the only links from source to destination will be closed.

        Args:
            source_country (str): Description
            dest_country (str): Description
            twoway (bool, optional): Description
            Debug (bool, optional): Description
        """
        self._change_border_1way(
            source_country=source_country, dest_country=dest_country, mode="close", Debug=Debug
        )
        if twoway:
            self._change_border_1way(
                source_country=dest_country, dest_country=source_country, mode="close", Debug=Debug
            )

    @check_args_type
    def reopen_border(
        self, source_country: str, dest_country: str, twoway: bool = True, Debug: bool = False
    ) -> None:
        """
        Re-open all links between two countries. If twoway is set to false,
        the only links from source to destination will be closed.

        Args:
            source_country (str): Description
            dest_country (str): Description
            twoway (bool, optional): Description
            Debug (bool, optional): Description
        """
        self._change_border_1way(
            source_country=source_country, dest_country=dest_country, mode="reopen", Debug=Debug
        )
        if twoway:
            self._change_border_1way(
                source_country=dest_country, dest_country=source_country, mode="reopen", Debug=Debug
            )

    @check_args_type
    def close_camp(self, location_name: str, IDP: bool):
        self.locations[self._convert_location_name_to_index(location_name)].close_camp(IDP)
        print("Time = {}. Close camp {}, IDP: {}.".format(self.time, location_name, IDP), file=sys.stderr)


    @check_args_type
    def open_camp(self, location_name: str, IDP: bool):
        self.locations[self._convert_location_name_to_index(location_name)].open_camp(IDP)
        print("Time = {}. Open camp {}, IDP: {}.".format(self.time, location_name, IDP), file=sys.stderr)


    @check_args_type
    def set_forced_redirection(self, loc1_name: str, loc2_name: str, value: bool):
        id1 = self._convert_location_name_to_index(loc1_name)
        for i in range(0, len(self.locations[id1].links)):
            if self.locations[id1].links[i].endpoint.name == loc2_name:
                old_val = self.locations[id1].links[i].forced_redirection
                self.locations[id1].links[i].forced_redirection = value
                print("Time = {}. Redirection {}-{} changed from {} to {}.".format(self.time, loc1_name, loc2_name, old_val, value), file=sys.stderr)

    @check_args_type
    def close_location(self, location_name: str, twoway: bool = True, Debug: bool = False) -> bool:
        """
        Close in- and outgoing links for a location.

        Args:
            location_name (str): Description
            twoway (bool, optional): Description
            Debug (bool, optional): Description

        Returns:
            bool: Description
        """
        if twoway:
            return self._change_location_1way(
                location_name=location_name, mode="close", direction="both", Debug=Debug
            )

        return self._change_location_1way(
            location_name=location_name, mode="close", direction="in", Debug=Debug
        )

    @check_args_type
    def reopen_location(self, location_name: str, twoway: bool = True, Debug: bool = False) -> bool:
        """
        Reopen in- and outgoing links for a location.

        Args:
            location_name (str): Description
            twoway (bool, optional): Description
            Debug (bool, optional): Description
        """
        if twoway:
            return self._change_location_1way(
                location_name, mode="reopen", direction="both", Debug=Debug
            )

        return self._change_location_1way(location_name, mode="reopen", direction="in", Debug=Debug)

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
    def pick_spawn_location(self):
        """
        Summary

        !!! warning
            this function is now deprecated as of ruleset 2.0.
            Please use `pick_spawn_locations()` instead in your scripts

        Returns:
            Location: Description
        """
        return self.pick_spawn_locations(1)[0]

    @check_args_type
    def pick_spawn_locations(self, number: int = 1) -> list:
        """
        Returns a weighted random element from the list of flood locations.
        This function returns a number, which is an index in the array of
        flood locations.

        Args:
            number (int, optional): Description

        Returns:
            list: Description
        """
        swtotal = sum(self.spawn_weights)

        assert swtotal > 0

        return np.random.choice(
            self.locations, number, p=self.spawn_weights / swtotal
        ).tolist()


    @check_args_type
    def evolve(self) -> None:
        """
        Summary
        """

        spawning.refresh_spawn_weights(self) # Required to correctly incorporate TakeFromPopulation and FloodSpawnDecay.

        # update level 1, 2 and 3 location scores
        for loc in self.locations:
            scoring.updateLocationScore(self.time, loc)

        for loc in self.locations:
            scoring.updateNeighbourhoodScore(loc)

        for loc in self.locations:
            scoring.updateRegionScore(loc)

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
    def addLocation(
        self,
        name: str,
        x: float = 0.0,
        y: float = 0.0,
        location_type: Optional[str] = None,
        movechance: float = 1.0,
        capacity: int = -1,
        pop: int = 0,
        foreign: bool = False,
        country: str = "unknown",
        attributes: dict = {},
    ):
        """
        Add a location to the ABM network graph

        Args:
            name (str): Description
            x (float, optional): Description
            y (float, optional): Description
            location_type (str, optional): Description
            movechance (float, optional): Description
            capacity (int, optional): Description
            pop (int, optional): Description
            foreign (bool, optional): Description
            country (str, optional): Description

        No Longer Returned:
            Location: Description

        """

        loc = Location(
            name=name,
            x=x,
            y=y,
            location_type=location_type,
            movechance=movechance,
            capacity=capacity,
            pop=pop,
            foreign=foreign,
            country=country,
            attributes=attributes,
        )
        if SimulationSettings.log_levels["init"] > 0 and self.print_location_output:
            print("Location:", name, x, y, loc.movechance, capacity, ", pop. ", pop, foreign, ", attrib. ",attributes, file=sys.stderr)

        self.locations.append(loc)
        self.spawn_weights = np.append(self.spawn_weights, [0.0])
        self.locationNames.append(loc.name)

        spawning.refresh_spawn_weights(self)
        return loc

    @check_args_type
    def addAgent(self, location, age, gender, attributes) -> None:
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

        self.agents.append(Person(location=location, age=age, gender=gender, attributes=attributes))

    @check_args_type
    def insertAgent(self, location) -> None:
        """
        Note: insert Agent does NOT take from Population.

        Args:
            location (Location): Description
        """
        self.agents.append(Person(location=location))

    @check_args_type
    def insertAgents(self, location, number: int) -> None:
        """
        Summary

        Args:
            location (Location): Description
            number (int): Description
        """
        for _ in range(0, number):
            self.insertAgent(location=location)

    @check_args_type
    def clearLocationsFromAgents(self, location_names: List[str]) -> None:
        """
        Remove all agents from a list of locations by name.
        Useful for couplings to other simulation codes.

        Args:
            location_names (List[str]): Description
        """
        new_agents = []
        for i in range(0, len(self.agents)):
            if self.agents[i].location.name not in location_names:
                new_agents += self.agents[i]  # agent is preserved in ecosystem
            else:
                # agent is removed from the ecosystem and number of agents
                # drops by one.
                self.agents[i].location.DecrementNumAgents()
        self.agents = new_agents

    @check_args_type
    def setAttribute(self, name: str, value) -> None:
        self.attributes[name] = value

    @check_args_type
    def numAgents(self) -> int:
        """
        Summary

        Returns:
            int: Description
        """
        return len(self.agents)

    @check_args_type
    def numIDPs(self) -> int:
        """
        Aggregates number of IDPs across locations

        Returns:
            int: total # of IDPs.
        """
        num_idps = 0

        for l in self.locations:
            if l.idpcamp:
                num_idps += l.numAgents

        return num_idps

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

    @check_args_type
    def printComplete(self) -> None:
        """
        Summary
        """
        print("Time: ", self.time, ", # of agents: ", len(self.agents))
        if self.print_location_output:
            for loc in self.locations:
                print(
                    "Location name %s, number of agents %s" % (loc.name, loc.numAgents),
                    file=sys.stderr,
                )
                loc.print()

    @check_args_type
    def getRankN(self, t: int) -> bool:
        """
        Returns whether this process should do a task. Always returns true,
        as flee.py is sequential.

        Args:
            t (int): Description

        Returns:
            bool: Description

        """
        return True
