from __future__ import annotations, print_function

import copy
import os
import random
import sys
from typing import List, Optional, Tuple

import numpy as np
from flee.Diagnostics import write_agents
from flee.SimulationSettings import SimulationSettings
import flee.moving as moving

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
    ]

    @check_args_type
    def __init__(self, location, age, gender, attributes):
        self.location = location
        self.home_location = location
        self.location.IncrementNumAgents()
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

        if SimulationSettings.log_levels["agent"] > 0:
            self.distance_travelled = 0

    @check_args_type
    def evolve(self, time: int, ForceTownMove: bool = False) -> None:
        """
        Summary

        Args:
            time (int): Description
            ForceTownMove (bool, optional): Description
        """
        if self.travelling is False:
            if self.location.town and ForceTownMove:
                movechance = 1.0
            else:
                movechance = self.location.movechance

            outcome = random.random()
            # print(movechance)

            if outcome < movechance:
                # determine here which route to take?
                chosenRoute = moving.selectRoute(self, time=time)

                # if there is a viable route to a different location.
                if chosenRoute:
                    # update location to link endpoint
                    self.location.DecrementNumAgents()
                    self.location = chosenRoute
                    self.location.IncrementNumAgents()
                    self.travelling = True
                    self.distance_travelled_on_link = 0


    @check_args_type
    def finish_travel(self, time: int) -> None:
        """
        Summary

        Args:
            time (int): Description
        """
        if self.travelling:

            if self.places_travelled == 1 and SimulationSettings.move_rules["StartOnFoot"]:
                # First journey
                self.distance_travelled_on_link += SimulationSettings.move_rules["MaxWalkSpeed"]
                self.distance_moved_this_timestep += SimulationSettings.move_rules["MaxWalkSpeed"]
            else:
                self.distance_travelled_on_link += SimulationSettings.move_rules["MaxMoveSpeed"]
                self.distance_moved_this_timestep += SimulationSettings.move_rules["MaxMoveSpeed"]

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
                    self.location.DecrementNumAgents()
                    self.location = self.location.startpoint
                    self.location.IncrementNumAgents()
                    self.travelling = False
                    self.distance_travelled_on_link = 0

                else:
                    # if the person has moved less than the MaxMoveSpeed, it
                    # should go through another evolve() step in the new
                    # location.
                    evolveMore = False
                    if self.distance_moved_this_timestep < SimulationSettings.move_rules["MaxMoveSpeed"]:
                        evolveMore = True

                    # update location (which is on a link) to link endpoint
                    self.location.DecrementNumAgents()
                    self.location = self.location.endpoint
                    self.location.IncrementNumAgents()

                    self.travelling = False
                    self.distance_travelled_on_link = 0

                    if SimulationSettings.log_levels["camp"] > 0:
                        if self.location.Camp is True:
                            self.location.incoming_journey_lengths += [
                                self.timesteps_since_departure
                            ]

                    # Perform another evolve step if needed. And if it results
                    # in travel, then the current traveled distance needs
                    # to be taken into account.
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
                        self.evolve(time=time, ForceTownMove=ForceTownMove)
                        self.finish_travel(time=time)


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
        self.conflict = False
        self.conflict_date = -1 # date that last conflict erupted.
        self.camp = False
        self.town = False
        self.forward = False
        self.marker = False
        self.time_of_conflict = -1 # Time that a major conflict event last took place.
        self.numAgentsSpawned = 0

        if location_type is not None:
            if "camp" in location_type.lower():
                self.movechance = SimulationSettings.move_rules["CampMoveChance"]
                self.camp = True
                self.foreign = True
            elif "conflict" in location_type.lower():
                self.movechance = SimulationSettings.move_rules["ConflictMoveChance"]
                self.conflict = True
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
                    " {} for location object with name {}".format(location_type, name)
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

        # Value of Location. Should be between 0.5 and
        # SimulationSettings.move_rules["CampWeight"].
        self.LocationScore = 1.0
        # Value of Neighbourhood. Should be between 0.5 and
        # SimulationSettings.move_rules["CampWeight"].
        self.NeighbourhoodScore = 1.0
        # Value of surrounding region. Should be between 0.5 and
        # SimulationSettings.move_rules["CampWeight"].
        self.RegionScore = 1.0
        self.scores = np.array([1.0, 1.0, 1.0, 1.0])

        self.updateLocationScore()
        self.updateNeighbourhoodScore()
        self.updateRegionScore()

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
        self.conflict = False
        self.town = False

    @check_args_type
    def DecrementNumAgents(self) -> None:
        """
        Summary
        """
        self.numAgents -= 1

    @check_args_type
    def IncrementNumAgents(self) -> None:
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
            "pop: {}, country: {}, conflict? {}, camp? {}".format(
                self.name,
                self.x,
                self.y,
                self.movechance,
                self.capacity,
                self.pop,
                self.country,
                self.conflict,
                self.camp,
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
    def SetConflictMoveChance(self) -> None:
        """
        Modify move chance to the default value set for conflict regions.
        """
        self.movechance = SimulationSettings.move_rules["ConflictMoveChance"]

    @check_args_type
    def SetCampMoveChance(self) -> None:
        """
        Modify move chance to the default value set for camps.
        """
        self.movechance = SimulationSettings.CampMoveChance

    @check_args_type
    def CalculateResidualWeightingFactor(
        self, residual: float, cap_limit: float, nearly_full_occ: float
    ) -> float:
        """
        Calculate the residual weighting factor, when pop is between 0.9 and
        1.0 of capacity (with default settings).
        Weight should be 1.0 at 0.9, and 0.0 at 1.0 capacity level.
        Asserts are added to prevent corruption of simulation results in case
        this function misbehaves.

        Args:
            residual (float): Description
            cap_limit (float): Description
            nearly_full_occ (float): Description

        Returns:
            float: Description
        """

        weight = 1.0 - (residual / (cap_limit * (1.0 - nearly_full_occ)))

        assert weight >= 0.0
        assert weight <= 1.0

        return weight

    @check_args_type
    def getCapMultiplier(self, numOnLink: int) -> float:
        """
        Checks whether a given location has reached full capacity
        or is close to it.

        Args:
            numOnLink (int): Description

        Returns:
            float: return

            - 1.0 if occupancy < nearly_full_occ (0.9).
            - 0.0 if occupancy >= 1.0.
            - a value in between for intermediate values
        """
        nearly_full_occ = 0.9  # occupancy rate to be considered nearly full.
        # full occupancy limit (should be equal to self.capacity).
        cap_limit = self.capacity * SimulationSettings.CapacityBuffer

        if self.capacity < 0:
            return 1.0

        if self.numAgents <= nearly_full_occ * cap_limit:
            return 1.0

        if self.numAgents >= 1.0 * cap_limit:
            return 0.0

        # should be a number equal in range [0 to 0.1*self.numAgents].
        residual = self.numAgents - (nearly_full_occ * cap_limit)

        return self.CalculateResidualWeightingFactor(
            residual=residual, cap_limit=cap_limit, nearly_full_occ=nearly_full_occ
        )

    @check_args_type
    def getScores(self, index: int) -> float:
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

    @check_args_type
    def updateLocationScore(self) -> None:
        """
        Attractiveness of the local point, based on local point
        information only.
        """

        if self.foreign or self.camp:
            # * max(1.0,SimulationSettings.move_rules["AwarenessLevel"])
            self.LocationScore = SimulationSettings.move_rules["CampWeight"]
        elif self.conflict:
            # * max(1.0,SimulationSettings.move_rules["AwarenessLevel"])
            self.LocationScore = SimulationSettings.move_rules["ConflictWeight"]
        else:
            self.LocationScore = 1.0

        self.setScore(index=0, value=1.0)
        self.setScore(index=1, value=self.LocationScore)
        # print(self.name,self.camp,self.foreign,self.LocationScore)

    @check_args_type
    def updateNeighbourhoodScore(self) -> None:
        """
        Attractiveness of the local point, based on information from local and
        adjacent points, weighted by link length.
        """
        # No links connected or a Camp? Use LocationScore.
        if len(self.links) == 0 or self.camp:
            self.NeighbourhoodScore = self.LocationScore
        else:
            self.NeighbourhoodScore = 0.0
            total_link_weight = 0.0

            for link in self.links:
                self.NeighbourhoodScore += link.endpoint.LocationScore / float(
                    link.get_distance()
                )
                total_link_weight += 1.0 / float(link.get_distance())

            self.NeighbourhoodScore /= total_link_weight
            self.setScore(index=2, value=self.NeighbourhoodScore)

    @check_args_type
    def updateRegionScore(self) -> None:
        """
        Attractiveness of the local point, based on neighbourhood information
        from local and adjacent points, weighted by link length.
        """
        # No links connected or a Camp? Use LocationScore.
        if len(self.links) == 0 or self.camp:
            self.RegionScore = self.LocationScore
        else:
            self.RegionScore = 0.0
            total_link_weight = 0.0

            for link in self.links:
                self.RegionScore += link.endpoint.NeighbourhoodScore / float(
                    link.get_distance()
                )
                total_link_weight += 1.0 / float(link.get_distance())

            self.RegionScore /= total_link_weight
            self.setScore(index=3, value=self.RegionScore)


class Link:
    """
    the Link class
    """

    @check_args_type
    def __init__(self, startpoint, endpoint, distance: float, forced_redirection: bool = False):
        self.name = "__link__"
        self.closed = False

        # distance in km.
        self.__distance = distance

        # links for now always connect two endpoints
        self.startpoint = startpoint
        self.endpoint = endpoint

        # number of agents that are in transit.
        self.numAgents = 0
        # refugee population on current rank (for pflee).
        self.numAgentsOnRank = 0

        # if True, then all Persons will go down this link.
        self.forced_redirection = forced_redirection

    @check_args_type
    def DecrementNumAgents(self) -> None:
        """
        Summary
        """
        self.numAgents -= 1

    @check_args_type
    def IncrementNumAgents(self) -> None:
        """
        Summary
        """
        self.numAgents += 1

    def get_distance(self) -> float:
        """
        Summary

        Args:

        Returns:
            float: Description
        """
        return self.__distance


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

        # Bring conflict zone management into FLEE.
        self.conflict_zones = []
        self.conflict_zone_names = []
        self.conflict_weights = np.array([])
        self.conflict_pop = 0

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
                if loc.Camp is True:
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
                    if c[0] == "location":
                        self.close_location(location_name=c[1], twoway=twoway)
                    if c[0] == "link":
                        self.close_link(startpoint=c[1], endpoint=c[2], twoway=twoway)
                if time == c[4]:
                    if c[0] == "country":
                        if Debug:
                            print(
                                "Time = {}. Reopening Border between "
                                "[{}] and [{}]".format(time, c[1], c[2]),
                                file=sys.stderr,
                            )
                        self.reopen_border(source_country=c[1], dest_country=c[2], twoway=twoway)
                    if c[0] == "location":
                        self.reopen_location(location_name=c[1], twoway=twoway)
                    if c[0] == "link":
                        self.reopen_link(startpoint=c[1], endpoint=c[2], twoway=twoway)

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
            print("#Warning: location not found in remove_link")
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
    def add_conflict_zone(self, name: str, change_movechance: bool = True) -> None:
        """
        Adds a conflict zone. Default weight is equal to
        population of the location.

        Args:
            name (str): Description
            change_movechance (bool, optional): Description

        Returns:
            None: Description
        """
        for i in range(0, len(self.locationNames)):
            if self.locationNames[i] == name:
                if name not in self.conflict_zone_names:
                    if change_movechance:
                        self.locations[i].movechance = SimulationSettings.move_rules["ConflictMoveChance"]
                        self.locations[i].conflict = True
                        self.locations[i].town = False

                    self.conflict_zone_names += [name]
                    self.conflict_zones += [self.locations[i]]
                    self.conflict_weights = np.append(
                        self.conflict_weights, [self.locations[i].pop]
                    )
                    self.conflict_pop = sum(self.conflict_weights)

                    self.locations[i].time_of_conflict = self.time
                    
                    if SimulationSettings.log_levels["init"] > 0:
                        print("Added conflict zone:", name, ", pop. ", self.locations[i].pop)
                        print("New total pop. in conflict zones: ", self.conflict_pop)
                    return

        print("Diagnostic: self.locationNames: ", self.locationNames, file=sys.stderr)
        print("Diagnostic: self.conflict_zone_names: ", self.conflict_zone_names, file=sys.stderr)
        print(
            "ERROR in flee.add_conflict_zone: location with name [{}] "
            "appears not to exist in the FLEE ecosystem "
            "(see diagnostic above).".format(name),
            file=sys.stderr,
        )

    @check_args_type
    def remove_conflict_zone(self, name: str, change_movechance: bool = True) -> None:
        """
        Shorthand function to remove a conflict zone from the list.
        (not used yet)

        Args:
            name (str): Description
            change_movechance (bool, optional): Description
        """
        new_conflict_zones = []
        new_conflict_zone_names = []
        new_weights = np.array([])

        for i in range(0, len(self.conflict_zones)):
            if not self.conflict_zones[i].name == name:
                new_conflict_zones += [self.conflict_zones[i]]
                new_conflict_zone_names += [self.conflict_zone_names[i]]
                new_weights = np.append(new_weights, [self.conflict_weights[i]])
            else:
                if change_movechance:
                    self.conflict_zones[i].movechance = SimulationSettings.move_rules["DefaultMoveChance"]
                self.conflict_zones[i].conflict = False
                self.conflict_zones[i].town = True

        self.conflict_zone_names = new_conflict_zone_names
        self.conflict_zones = new_conflict_zones
        self.conflict_weights = new_weights
        self.conflict_pop = sum(self.conflict_weights)

    @check_args_type
    def pick_conflict_location(self):
        """
        Summary

        !!! warning
            this function is now deprecated as of ruleset 2.0.
            Please use `pick_conflict_locations()` instead in your scripts

        Returns:
            Location: Description
        """
        return self.pick_conflict_locations(1)[0]

    @check_args_type
    def pick_conflict_locations(self, number: int = 1) -> list:
        """
        Returns a weighted random element from the list of conflict locations.
        This function returns a number, which is an index in the array of
        conflict locations.

        Args:
            number (int, optional): Description

        Returns:
            list: Description
        """
        assert self.conflict_pop > 0
        assert len(self.conflict_zones) > 0

        return np.random.choice(
            self.conflict_zones, number, p=self.conflict_weights / self.conflict_pop
        ).tolist()


    @check_args_type
    def refresh_conflict_weights(self) -> None:
        """
        This function needs to be called when
        SimulationSettings.spawn_rules["TakeFromPopulation"] is set to True.
        Also needed to model the ConflictSpawnDecay.
        It will update the weights to reflect the new population numbers.
        """
        for i in range(0, len(self.conflict_zones)):
            time_since_conflict = self.time - self.conflict_zones[i].time_of_conflict
            self.conflict_weights[i] = self.conflict_zones[i].pop * SimulationSettings.get_conflict_decay(time_since_conflict)
        self.conflict_pop = sum(self.conflict_weights)

    @check_args_type
    def evolve(self) -> None:
        """
        Summary
        """
        self.refresh_conflict_weights() # Required to correctly incorporate TakeFromPopulation and ConflictSpawnDecay.

        # update level 1, 2 and 3 location scores
        for loc in self.locations:
            loc.updateLocationScore()

        for loc in self.locations:
            loc.updateNeighbourhoodScore()

        for loc in self.locations:
            loc.updateRegionScore()

        # update agent locations
        for a in self.agents:
            a.evolve(time=self.time)

        for a in self.agents:
            a.finish_travel(time=self.time)
            a.timesteps_since_departure += 1

        if SimulationSettings.log_levels["agent"] > 0:
            write_agents(agents=self.agents, time=self.time)

        for a in self.agents:
            a.recent_travel_distance = (
                a.recent_travel_distance
                + (a.distance_moved_this_timestep / SimulationSettings.move_rules["MaxMoveSpeed"])
            ) / 2.0
            a.distance_moved_this_timestep = 0

        # update link properties
        if SimulationSettings.log_levels["camp"] > 0:
            self._aggregate_arrivals()

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
        )
        if SimulationSettings.log_levels["init"] > 0 and self.print_location_output:
            print("Location:", name, x, y, loc.movechance, capacity, ", pop. ", pop, foreign)
        self.locations.append(loc)
        self.locationNames.append(loc.name)
        return loc

    @check_args_type
    def addAgent(self, location, age, gender, attributes) -> None:
        """
        Summary

        Args:
            location (Location): Description
        """
        if SimulationSettings.spawn_rules["TakeFromPopulation"]:
            if location.conflict:
                if location.pop > 0:
                    location.pop -= 1
                    location.numAgentsSpawned += 1
                else:
                    print(
                        "ERROR: Number of agents in the simulation is larger than the combined "
                        "population of the conflict zones. Please amend locations.csv."
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
    def numAgents(self) -> int:
        """
        Summary

        Returns:
            int: Description
        """
        return len(self.agents)

    @check_args_type
    def linkUp(
        self,
        endpoint1: str,
        endpoint2: str,
        distance: float = 1.0,
        forced_redirection: bool = False,
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
            print("Diagnostic: Ecosystem.locationNames: ", self.locationNames)
            print(
                "Error: link created to non-existent source: {}  with dest {}".format(
                    endpoint1, endpoint2
                )
            )
            sys.exit()
        if endpoint2_index < 0:
            print("Diagnostic: Ecosystem.locationNames: ", self.locationNames)
            print(
                "Error: link created to non-existent destination: {} with source {}".format(
                    endpoint2, endpoint1
                )
            )
            sys.exit()

        self.locations[endpoint1_index].links.append(
            Link(
                startpoint=self.locations[endpoint1_index],
                endpoint=self.locations[endpoint2_index],
                distance=distance,
                forced_redirection=forced_redirection,
            )
        )
        self.locations[endpoint2_index].links.append(
            Link(
                startpoint=self.locations[endpoint2_index],
                endpoint=self.locations[endpoint1_index],
                distance=distance,
            )
        )

    @check_args_type
    def printInfo(self) -> None:
        """
        Summary
        """
        print(
            "Time: {}, # of agents: {}, # of conflict zones {}.".format(
                self.time, len(self.agents), len(self.conflict_zones)
            ),
            file=sys.stderr,
        )
        if len(self.conflict_zones) > 0:
            print(
                "First conflict zone is called {}".format(self.conflict_zones[0].name),
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
