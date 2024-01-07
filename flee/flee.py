from __future__ import annotations, print_function

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
import flee.spawning as spawning
import flee.scoring as scoring

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
        "attributes",
        "locations_visited",
        "route",
    ]

    @check_args_type
    def __init__(self, location, attributes):
        """
        Summary: 
            Initializes a new Flee Agent
        
        Args:
            location: The initial location of the agent.
            attributes: A dictionary of attributes for the agent.

        Returns:
            None.
        """
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
        Summary:
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
        Summary:
            Updates the agent's travel state.

        Args:
            location: location to travel to (can be Location of Link type).
            travelling: set to True if location is a Link, False if it is a Location object.
        
        Returns:
            None.
        """
        self.location.DecrementNumAgents() 
        self.location = location
        self.location.IncrementNumAgents(self)
        self.travelling = travelling
        self.distance_travelled_on_link = 0


    def check_dest_is_full_camp(self,e):
        """
        Summary:
            Checks if the agent's destination camp is full.
            Prevents the agent from moving to a camp that is already full.

        Args:
            e: ecosystem object

        Returns:
            True if the destination camp is full, False otherwise.
        """
        for i in range(0, len(e.locationNames)):
            if e.locationNames[i] == self.route[-1]:
                if e.locations[i].camp and moving.getCapMultiplier(e.locations[i],1) < 0.5:
                    #print(e.time, e.locationNames[i], self.route[-1], file=sys.stderr)
                    return True
                else: 
                    return False
        print(f"Error: camp {self.route[-1]} not found in check_dest_is_full_camp", file=sys.stderr)
        sys.exit()
    
    def take_next_step(self,e):
        """
        Summary:
            Takes the next step on the agent's route.

        Args:
            e: The ecosystem object.

        Returns:
            The next link on the agent's route, 
            or `None` if the agent's route is empty 
            or the next link is invalid.
        """
        for l in self.location.links:
            # If the name of the destination on the current link is same as the agents current waypoint on the route:
            if l.endpoint.name == self.route[0]:
                # Check if the destination camp is full, flooded. If so, remove the route and return `None`.
                if self.check_dest_is_full_camp(e):
                    self.route = []
                    return None
                # Otherwise, remove the first link from the route and return the next link.
                self.route = self.route[1:]
                return l

        # Link has vanished, remove route.
        self.route = []
        return None


    @check_args_type
    def evolve(self, e, time: int, ForceTownMove: bool = False) -> None:
        """
        Summary:
            Updates the agent's location and state 
            based on the current simulation timestep.

        Args:
            time (int): The current simulation timestep.
            ForceTownMove (bool, optional): Whether or not the agent is forced to move to a town.

        Returns:
            None.
        """
        if self.travelling is False:
            # Calculate the agent's move chance.
            movechance = moving.calculateMoveChance(self, ForceTownMove, time)
            #if self.location.town and ForceTownMove: # called through evolveMore
            #    movechance = 1.0
            #else: # called first time in loop
            #    movechance = self.location.movechance
            #    movechance *= (float(max(self.location.pop, self.location.capacity)) / SimulationSettings.move_rules["MovechancePopBase"])**SimulationSettings.move_rules["MovechancePopScaleFactor"]

            # Generate a random number and compare it to the move chance.
            outcome = random.random()
            # print(movechance)

            # If the outcome is less than the move chance, then the agent moves.
            if outcome < movechance:
                # If the agent does not have an existing route, then plan a new route.
                if len(self.route) == 0:
                    # Determine which route to take
                    self.route = moving.selectRoute(self, time=time)

                # Attempt to follow route. Return None if fail.  
                chosenDest = self.take_next_step(e)

                # If there is a viable route to a different location, then move to the next location.
                if chosenDest:
                    # update location to link endpoint
                    self.handle_travel(chosenDest, travelling=True)


    @check_args_type
    def finish_travel(self, e, time: int) -> None:
        """
        Summary:
            Completes the agent's current journey
            and updates its location and state.

        Args:
            e: The ecosystem object.
            time (int): The current simulation timestep.

        Returns:
            None.
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
        region: str = "unknown",
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
        """
        Summary:
            Initializes a new Location object.

        Args:
            name: The name of the location.
            x: The X-coordinate of the location.
            y: The Y-coordinate of the location.
            location_type: The type of the location (e.g. camp, town, conflict zone, etc.).
            movechance: The probability that an agent will move to this location.
            capacity: The capacity of the location (i.e. the maximum number of agents that can be present at the location at any one time).
            pop: The population of the location (i.e. the number of non-refugee agents that are present at the location at any one time).
            foreign: Whether or not the location is in a foreign country.
            country: The country that the location is in.
            attributes: A dictionary of attributes for the location.

        Returns:
            None.
        """
        self.name = name
        self.region = region
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
        self.conflict = -1.0
        self.conflict_date = -1 # date that last conflict erupted.
        self.camp = False
        self.idpcamp = False
        self.town = False
        self.forward = False
        self.marker = False
        self.flood_zone = False 
        self.time_of_conflict = -1 # Time that a major conflict event last took place.
        self.numAgentsSpawned = 0

        self.attributes = attributes # This will store a range of attributes that are read from file.

        if location_type is not None:
            if "camp" in location_type.lower():
                self.movechance = SimulationSettings.move_rules["CampMoveChance"]
                self.camp = True
                if "idp" in location_type.lower():
                    self.idpcamp = True
                    self.movechance = SimulationSettings.move_rules["IDPCampMoveChance"]
            elif "conflict" in location_type.lower():
                self.movechance = SimulationSettings.move_rules["ConflictMoveChance"]
                self.conflict = float(self.attributes.get("conflict_intensity",1.0))
            elif "forward" in location_type.lower():
                self.movechance = 1.0
                self.forward = True
            elif "marker" in location_type.lower():
                self.movechance = 1.0
                self.marker = True
            elif "flood_zone" in location_type.lower(): 
                # move chance based on default because flood_level not linked to flood_zone yet
                self.movechance = SimulationSettings.move_rules["DefaultMoveChance"]
                self.flood_zone = True 
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
        # Don't want flood zone to become a camp if movechance is low. 
        if self.movechance < 0.005 and not self.camp and not self.flood_zone:
            print(
                "Warning: automatically setting location {} to camp, "
                "as movechance = {}".format(self.name, self.movechance),
                file=sys.stderr,
            )
            self.camp = True
            self.town = False

        self.scores = np.array([1.0, 1.0, 1.0, 1.0])

        scoring.updateLocationScore(0,self)

        if SimulationSettings.log_levels["camp"] > 0:
            # reinitializes every time step. Contains individual journey
            # lengths from incoming agents.
            self.incoming_journey_lengths = []

        self.print()


    @check_args_type
    def calculateDistance(self, other_location) -> float:
        """
        Summary: 
            Calculates the distance between this location and another one.
            This assumes distance as the crow flies.

        Args:
            other_location: The other location to calculate the distance to.

        Returns:
            The distance between this location and the other location in kilometers.

        """
        # Approximate radius of earth in km
        R = 6371.0

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
        Summary:
            Changes the location type to camp or IDP camp.

        Args:
            IDP(boolean): Whether or not to open an IDP camp.

        Returns:
            None.
        """
        self.movechance = SimulationSettings.move_rules["CampMoveChance"]
        self.camp = True
        self.conflict = -1.0
        self.town = False
        self.forward = False
        self.marker = False
        self.flood_zone = False
        if IDP:
            self.idpcamp = True
            self.movechance = SimulationSettings.move_rules["IDPCampMoveChance"]


    @check_args_type
    def setAttribute(self, name: str, value) -> None:
        """
        Summary:
            Sets the value of an attribute for the location.

        Args:
            name: The name of the attribute to set.
            value: The value to set the attribute to.

        Returns:
            None.
        """
        self.attributes[name] = value


    @check_args_type
    def close_camp(self, IDP=False) -> None:
        """
        Summary:
            Changes the location type to town.

        Args:
            IDP: Whether or not to close an IDP camp.

        Returns:
            None.
        """
        self.movechance = SimulationSettings.move_rules["DefaultMoveChance"]
        self.camp = False
        self.idpcamp = False
        self.conflict = -1.0
        self.town = True
        self.forward = False
        self.marker = False
        self.flood_zone = False


    @check_args_type
    def DecrementNumAgents(self) -> None:
        """
        Summary:
            Decrements the number of agents in the location.

        Args:
            None.

        Returns:
            None.
        """
        self.numAgents -= 1


    @check_args_type
    def IncrementNumAgents(self, agent) -> None:
        """
        Summary: 
            Increments the number of agents in the location.

        Args:
            agent: The agent to add to the location. 
            Needed to specify which agent is being added to the location, 
            because there may be multiple agents in a location.

        Returns:
            None.
        """
        self.numAgents += 1


    @check_args_type
    def print(self) -> None:
        """
        Summary: 
            Prints information about the location.

        Args:
            None.

        Returns:
            None.
        """
        print(
            "Location name: {}, X: {}, Y: {}, movechance: {}, cap: {}, "
            "pop: {}, country: {}, conflict? {}, camp? {}, flood_zone? {}, foreign? {}, attributes: {}".format(
                self.name,
                self.x,
                self.y,
                self.movechance,
                self.capacity,
                self.pop,
                self.country,
                self.conflict,
                self.camp,
                self.flood_zone,
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
    def SetConflictMoveChance(self) -> None: 

        """
        Summary:
            Sets the move chance to the default value set for conflict regions.

        Args:
            None.

        Returns:
            None.
        """
        self.movechance = SimulationSettings.move_rules["ConflictMoveChance"]


    @check_args_type
    def SetCampMoveChance(self) -> None:
        """
        Summary: 
            Modify move chance to the default value set for camps.

        Args:
            None.

        Returns:
            None.

        """
        self.movechance = SimulationSettings.CampMoveChance


    @check_args_type
    def getScore(self, index: int) -> float:
        """
        Summary: 
            Gets the score at the specified index.

        Args:
            index (int): The index of the score to get.

        Returns:
            float: The score at the specified index.
        """
        return self.scores[index]


    @check_args_type
    def setScore(self, index: int, value: float) -> None:
        """
        Summary:
            Sets the score at the specified index.

        Args:
            index (int): The index of the score to set.
            value (float): The value to set the score to.

        Returns:
            None.
        """
        self.scores[index] = value


class Link:
    """
    The Link class
    """

    @check_args_type
    def __init__(self, startpoint, endpoint, distance: float, forced_redirection: bool = False, attributes: dict = {}):
        """
        Summary: 
            Initializes a new Link object.

        Args:
            startpoint (Location): The startpoint of the link.
            endpoint (Location): The endpoint of the link.
            distance (float): The distance between the startpoint and endpoint of the link, in kilometers.
            forced_redirection (bool): Whether or not the link is a forced redirection. If True, all agents will be routed through this link.
            attributes (dict): A dictionary of attributes for the link.

        Returns:
            None.
        """
        self.name = "L:{}:{}".format(startpoint.name, endpoint.name)
        self.closed = False

        # distance in km.
        self.__distance = distance

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
        Summary:
            Decrements the number of agents on the link.

        Args:
            None.

        Returns:
            None.
        """
        self.numAgents -= 1


    @check_args_type
    def IncrementNumAgents(self, agent) -> None:
        """
        Summary: 
            Increments the number of agents on the link 
            and the cumulative number of agents on the link.

        Args:
            agent: The agent to add to the link.

        Returns:
            None.
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
        """
        Summary: 
            Sets the value of an attribute for the link.

        Args:
            name (str): The name of the attribute to set.
            value: The value to set the attribute to.

        Returns:
            None.
        """

        self.attributes[name] = value
        


    def get_distance(self) -> float:
        """
        Summary: 
            Gets the distance of the link, in kilometers.

        Args:
            None.

        Returns:
            float: The distance of the link, in kilometers.
        """
        return self.__distance


class Ecosystem:
    """
    The Ecosystem class
    """

    @check_args_type
    def __init__(self):
        """
        Summary: 
            Initializes a new Simulation object.

        Args:
            None.

        Returns:
            None.
        """
        self.locations = []
        self.locationNames = []
        self.agents = []
        self.closures = []  # format [type, source, dest, start, end]
        self.time = 0
        self.print_location_output = True  # print location output data

        # FLEE3 does not have a conflict zone list, and spawn weights cover all locations.
        self.spawn_weights = np.array([])

        if SimulationSettings.log_levels["camp"] > 0:
            self.num_arrivals = []  # one element per time step.
            self.travel_durations = []  # one element per time step.


    @check_args_type
    def get_camp_names(self) -> List[str]:
        """
        Summary: 
            Gets a list of the names of all camps in the simulation.

        Args:
            None.

        Returns:
            List[str]: A list of the names of all camps in the simulation.
        """
        camp_names = []
        for loc in self.locations:
            if loc.camp:
                camp_names += [loc.name]
        return camp_names


    @check_args_type
    def export_graph(self, use_ids_instead_of_names: bool = False) -> Tuple[List[str], List[List]]:
        """
        Summary: 
            Exports the simulation graph as a list of vertices and a list of edges.

        Args:
            use_ids_instead_of_names (bool, optional): Whether to use location IDs instead of location names for the vertices. Defaults to False.

        Returns:
            Tuple[List[str], List[List]]: A tuple containing a list of vertices and a list of edges.
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
        Summary: 
            Adds up arrival statistics, to find out travel durations 
            and total number of camp arrivals.

        Args:
            None.

        Returns:
            None.
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
        Summary: 
            Enacts border closures, location closures, link closures,
            camp closures, and forced redirection removals according 
            to the list of closures provided.

        Args:
            time (int): The current time.
            twoway (bool, optional): Whether or not border closures should be two-way. Defaults to True.
            Debug (bool, optional): Whether or not to print debug messages. Defaults to False.

        Returns:
            None.
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
        Summary: 
            Converts a location name to an index number.

        Args:
            name (str): The name of the location.

        Returns:
            int: The index of the location in the `locations` list, or -1 if the location is not found.
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
        Summary: 
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
        Summary:
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
        Summary:
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
        Summary: 
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
        Summary:
            Shorthand call for remove_link, only moving the link to
            the closed list.

        Args:
            startpoint (str): name of the startpoint of the link.
            endpoint (str): name of the endpoint of the link.
            twoway (bool, optional): Whether or not the link is two-way. Defaults to True.

        Returns:
            bool: True if the link was closed, False otherwise.
        """
        return self.remove_link(
            startpoint=startpoint, endpoint=endpoint, twoway=twoway, close_only=True
        )


    @check_args_type
    def _change_location_1way(
        self, location_name: str, mode: str = "close", direction: str = "both", Debug: bool = False
    ) -> bool:
        """
        Summary: 
            Close all links to or from one location.
            mode: close or reopen
            direction: in, out or both.

        Args:
            location_name (str): The name of the location.
            mode (str, optional): The mode of the change: "close" or "reopen". Defaults to "close".
            direction (str, optional): The direction of the change: "in", "out", or "both". Defaults to "both".
            Debug (bool, optional): Whether or not to print debug messages. Defaults to False.

        Returns:
            bool: True if any links were changed, False otherwise.
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
        Summary:
            Close all links between two countries in one direction.

        Args:
            source_country (str): The name of the source country.
            dest_country (str): The name of the destination country.
            mode (str, optional): The mode of the change: "close" or "reopen". Defaults to "close".
            Debug (bool, optional): Whether or not to print debug messages. Defaults to False.

        Returns:
            None.

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
        Summary: 
            Close all links between two countries. If twoway is set to false,
            the only links from source to destination will be closed.

        Args:
            source_country (str): The name of the source country.
            dest_country (str): The name of the destination country.
            twoway (bool, optional): Whether to close the links in both directions. Defaults to True.
            Debug (bool, optional): Whether or not to print debug messages. Defaults to False.
        
        Returns:
            None.
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
        Summary:
            Re-open all links between two countries. If twoway is set to false,
            the only links from source to destination will be closed.

        Args:
            source_country (str): The name of the source country.
            dest_country (str): The name of the destination country.
            twoway (bool, optional): Whether to reopen the links in both directions. Defaults to True.
            Debug (bool, optional): Whether or not to print debug messages. Defaults to False.

        Returns:
            None.
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
        """
        Summary: 
            Closes a camp in a given location.

        Args:
            location_name (str): The name of the location where the camp is located.
            IDP (bool): Whether the camp is for IDPs or not.

        Returns:
            None.
        """     
        self.locations[self._convert_location_name_to_index(location_name)].close_camp(IDP)
        print("Time = {}. Close camp {}, IDP: {}.".format(self.time, location_name, IDP), file=sys.stderr)


    @check_args_type
    def open_camp(self, location_name: str, IDP: bool):
        """
        Summary: 
            Opens a camp in a given location.

        Args:
            location_name (str): The name of the location where the camp is located.
            IDP (bool): Whether the camp is for IDPs or not.

        Returns:
            None.
        """
        self.locations[self._convert_location_name_to_index(location_name)].open_camp(IDP)
        print("Time = {}. Open camp {}, IDP: {}.".format(self.time, location_name, IDP), file=sys.stderr)


    @check_args_type
    def set_forced_redirection(self, loc1_name: str, loc2_name: str, value: bool):
        """
        Summary: 
            Sets the forced redirection flag on the link between two locations.

        Args:
            loc1_name (str): The name of the first location.
            loc2_name (str): The name of the second location.
            value (bool): The new value of the forced redirection flag.

        Returns:
            None.
        """
        id1 = self._convert_location_name_to_index(loc1_name)
        for i in range(0, len(self.locations[id1].links)):
            if self.locations[id1].links[i].endpoint.name == loc2_name:
                old_val = self.locations[id1].links[i].forced_redirection
                self.locations[id1].links[i].forced_redirection = value
                print("Time = {}. Redirection {}-{} changed from {} to {}.".format(self.time, loc1_name, loc2_name, old_val, value), file=sys.stderr)


    @check_args_type
    def close_location(self, location_name: str, twoway: bool = True, Debug: bool = False) -> bool:
        """
        Summary:
            Close in- and outgoing links for a location.

        Args:
            location_name (str): The name of the location.
            twoway (bool, optional): Whether or not to close the links in both directions. Defaults to True.
            Debug (bool, optional): Whether or not to print debug messages. Defaults to False.

        Returns:
            bool: True if the location was successfully closed, False otherwise.
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
        Summary: 
            Reopens the links for a location.

        Args:
            location_name (str): The name of the location.
            twoway (bool, optional): Whether or not to reopen the links in both directions. Defaults to True.
            Debug (bool, optional): Whether or not to print debug messages. Defaults to False.

        Returns:
            bool: True if the location was successfully reopened, False otherwise.
        """
        if twoway:
            return self._change_location_1way(
                location_name, mode="reopen", direction="both", Debug=Debug
            )

        return self._change_location_1way(location_name, mode="reopen", direction="in", Debug=Debug)


    @check_args_type
    def add_conflict_zone(self, name: str, conflict_intensity: float = 1.0, change_movechance: bool = True) -> None:
        """
        Summary: 
            Adds a conflict zone. Default weight is equal to
            population of the location.

        Args:
            name (str): The name of the location to add as a conflict zone.
            conflict_intensity (float, optional): The intensity of the conflict in the specified location. Defaults to 1.0.
            change_movechance (bool, optional): Whether or not to change the movement chance for the specified location. Defaults to True.

        Returns:
            None.
        """
        for i in range(0, len(self.locationNames)):
            if self.locationNames[i] == name:
                if change_movechance:
                    self.locations[i].movechance = SimulationSettings.move_rules["ConflictMoveChance"]
                    self.locations[i].conflict = conflict_intensity
                    self.locations[i].town = False

                self.locations[i].time_of_conflict = self.time                  
                spawning.refresh_spawn_weights(self)

                if SimulationSettings.log_levels["init"] > 0:
                    print("Added conflict zone: {}, pop. {}, intensity: {}".format(name, self.locations[i].pop, conflict_intensity), file=sys.stderr)
                    print("New total spawn weight: ", sum(self.spawn_weights), file=sys.stderr)
                return

        print("Diagnostic: self.locationNames: ", self.locationNames, file=sys.stderr)
        print(
            "ERROR in flee.add_conflict_zone: location with name [{}] "
            "appears not to exist in the FLEE ecosystem "
            "(see diagnostic above).".format(name),
            file=sys.stderr,
        )


    @check_args_type
    def remove_conflict_zone(self, name: str, change_movechance: bool = True) -> None:
        """
        Summary:
            Shorthand function to remove a conflict zone from the list.
            (not used yet)

        Args:
            name (str): The name of the location to remove as a conflict zone.
            change_movechance (bool, optional): Whether or not to change the movement chance for the specified location. Defaults to True.

        Returns:
            None.
        """
        
        for i in range(0, len(self.locationNames)):
            if self.locationNames[i] == name:
                if change_movechance:
                    self.locations[i].movechance = SimulationSettings.move_rules["DefaultMoveChance"]
                self.locations[i].conflict = -1.0
                self.locations[i].town = True

        spawning.refresh_spawn_weights(self)


    @check_args_type
    def set_conflict_intensity(self, name: str, conflict_intensity: float, change_movechance: bool = True) -> None:
        """
        Summary: 
            Sets the conflict intensity for a given location.

        Args:
            name (str): The name of the location to set the conflict intensity for.
            conflict_intensity (float): The new conflict intensity for the specified location.
            change_movechance (bool, optional): Whether or not to change the movement chance for the specified location. Defaults to True.

        Returns:
            None.
        """
        if conflict_intensity < 0.000001:
            self.remove_conflict_zone(name, change_movechance)
        else:
            self.add_conflict_zone(name, conflict_intensity, change_movechance)


    @check_args_type
    def pick_spawn_locations(self, number: int = 1) -> list:
        """
        Summary:
            Returns a weighted random element from the list of conflict locations.
            This function returns a number, which is an index in the array of
            conflict locations. The probability of selecting a location 
            is proportional to its spawn weight.

        Args:
            number (int, optional): The number of locations to sample. Defaults to 1.

        Returns:
            list[Location]: A list of unique locations.
        """
        spawn_weight_total = sum(self.spawn_weights)

        assert spawn_weight_total > 0

        wgt = self.spawn_weights / spawn_weight_total

        return np.random.choice(
            self.locations, number, p=wgt
        ).tolist()


    @check_args_type
    def evolve(self) -> None:
        """
        Summary: 
            Updates the simulation state for the next timestep.

        Args:
            None.

        Returns:
            None.
        """
        spawning.refresh_spawn_weights(self) # Required to correctly incorporate TakeFromPopulation and ConflictSpawnDecay.
        
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
    def addLocation(
        self,
        name: str,
        region: str = "unknown",
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
        Summary: 
            Adds a location to the simulation network graph.

        Args:
            name (str): The name of the location.
            region (str): Description
            x (float, optional): The x-coordinate of the location. Defaults to 0.0.
            y (float, optional): The y-coordinate of the location. Defaults to 0.0.
            location_type (str, optional): The type of location. Defaults to None.
            movechance (float, optional): The probability that an agent will move from this location. Defaults to 1.0.
            capacity (int, optional): The maximum number of agents that can be present at this location. Defaults to -1 (unlimited).
            pop (int, optional): The initial population of the location. Defaults to 0.
            foreign (bool, optional): Whether or not this location is in a foreign country. Defaults to False.
            country (str, optional): The country that this location is in. Defaults to "unknown".
            attributes (dict, optional): A dictionary of additional attributes for the location. Defaults to an empty dictionary.

        Returns:
            None.
        """

        loc = Location(
            name=name,
            region=region,
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
            print("Location:", name, x, y, loc.movechance, capacity, ", pop. ", pop, foreign, ", attrib. ", attributes, file=sys.stderr)

        self.locations.append(loc)
        self.spawn_weights = np.append(self.spawn_weights, [0.0])
        self.locationNames.append(loc.name)

        spawning.refresh_spawn_weights(self)
        return loc


    @check_args_type
    def addAgent(self, location, attributes) -> None:
        """
        Summary: 
            Adds an agent to the simulation at the specified location.

        Args:
            location (Location): The location to add the agent to.
            attributes (dict): A dictionary of attributes for the agent.

        Returns:
            None.
        """
        if SimulationSettings.spawn_rules["TakeFromPopulation"]:
            if location.conflict > 0.0:
                if location.pop > 0:
                    location.pop -= 1
                else:
                    print(
                        "WARNING: Number of agents in the simulation is larger than the"
                        "population of the conflict zone."
                    )
                    location.print()
                location.numAgentsSpawned += 1

        self.agents.append(Person(location=location, attributes=attributes))


    @check_args_type
    def insertAgent(self, location) -> None:
        """
        Summary: 
        Inserts an agent into the simulation at the specified location.
        Note: insert Agent does NOT take from Population.

        Args:
            location (Location): The location to insert the agent at.

        Returns:
            None.
        """
        self.agents.append(Person(location=location, attributes={}))


    @check_args_type
    def insertAgents(self, location, number: int) -> None:
        """
        Summary: 
            Inserts a specified number of agents into the simulation
            at the specified location without taking from the population.

        Args:
            location (Location): The location to insert the agents at.
            number (int): The number of agents to insert.

        Returns:
            None.
        """
        for _ in range(0, number):
            self.insertAgent(location=location)


    @check_args_type
    def clearLocationsFromAgents(self, location_names: List[str]) -> None:
        """
        Summary: 
            Remove all agents from a list of locations by name.
            Useful for couplings to other simulation codes.

        Args:
            location_names (List[str]): A list of location names.

        Returns:
            None.
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
        """
        Summary: 
            Sets the value of an attribute for the simulation.

        Args:
            name (str): The name of the attribute.
            value: The value of the attribute.

        Returns:
            None.
        """
        self.attributes[name] = value
        


    @check_args_type
    def numAgents(self) -> int:
        """
        Summary:
            Returns the number of agents in the simulation.

        Args:
            None.

        Returns:
            int: The number of agents in the simulation.
        """
        return len(self.agents)


    @check_args_type
    def numIDPs(self) -> int:
        """
        Summary: 
            Aggregates number of IDPs across locations
        
        Args:
            None.

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
        distance: float = 1.0,
        forced_redirection: bool = False,
        attributes: dict = {},
    ) -> None:
        """
        Summary:
            Creates a link between two endpoint locations

        Args:
            endpoint1 (str): The name of the first endpoint location.
            endpoint2 (str): The name of the second endpoint location.
            distance (float, optional): The distance between the two endpoint locations. Defaults to 1.0.
            forced_redirection (bool, optional): Whether or not the link should be used as a forced redirection. Defaults to False.
            attributes (dict, optional): A dictionary of attributes for the link. Defaults to an empty dictionary.

        Returns:
            None.
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
                    endpoint1, endpoint2), file=sys.stderr)
            sys.exit()
        if endpoint2_index < 0:
            print("Diagnostic: Ecosystem.locationNames: ", self.locationNames, file=sys.stderr)
            print(
                "Error: link created to non-existent destination: {} with source {}".format(
                    endpoint2, endpoint1), file=sys.stderr)
            sys.exit()

        self.locations[endpoint1_index].links.append(
            Link(
                startpoint=self.locations[endpoint1_index],
                endpoint=self.locations[endpoint2_index],
                distance=distance,
                forced_redirection=forced_redirection,
                attributes=attributes,
            )
        )
        self.locations[endpoint2_index].links.append(
            Link(
                startpoint=self.locations[endpoint2_index],
                endpoint=self.locations[endpoint1_index],
                distance=distance,
                attributes=attributes,
            )
        )


    @check_args_type
    def printInfo(self) -> None:
        """
        Summary: 
            Prints information about the simulation to the standard error stream.

        Args:
            None. 

        Returns:
            None.
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
        Summary: 
            Prints complete information about the simulation to the standard error stream.

        Args: 
            None.

        Returns:
            None.
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
    def getRankN(self, time) -> bool:
        """
        Summary:
            Returns whether this process should do a task. Always returns true,
            as flee.py is sequential.

        Args:
            None.

        Returns:
            bool: True if this process should do a task, False otherwise.

        """
        return True
