from __future__ import annotations

import os
import sys
from functools import wraps
from typing import List, Optional

import numpy as np
from flee import flee,scoring,spawning
from flee.Diagnostics import write_agents_par,write_links_par
from flee.SimulationSettings import SimulationSettings
from mpi4py import MPI

if os.getenv("FLEE_TYPE_CHECK") is not None and os.environ["FLEE_TYPE_CHECK"].lower() == "true":
    from beartype import beartype as check_args_type
else:

    def check_args_type(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper


class MPIManager:
    """
    The MPIManager class
    """

    def __init__(self):
        if not MPI.Is_initialized():
            print("Manual MPI_Init performed.")
            MPI.Init()
        self.comm = MPI.COMM_WORLD
        self.rank = self.comm.Get_rank()
        self.size = self.comm.Get_size()

    # pylint: disable=missing-function-docstring
    @check_args_type
    def CalcCommWorldTotalSingle(self, i):
        total = np.array([-1])
        # If you want this number on rank 0, just use Reduce.
        self.comm.Allreduce(np.array([i]), total, op=MPI.SUM)
        return total[0]

    # pylint: disable=missing-function-docstring
    @check_args_type
    def CalcCommWorldTotal(self, np_array):
        assert np_array.size > 0

        total = np.zeros(np_array.size, dtype="i")

        # If you want this number on rank 0, just use Reduce.
        self.comm.Allreduce([np_array, MPI.INT], [total, MPI.INT], op=MPI.SUM)

        return total


class Person(flee.Person):
    """
    The Person class
    """

    __slots__ = [
        "location",
        "home_location",
        "timesteps_since_departure",
        "places_travelled",
        "recent_travel_distance",
        "distance_moved_this_timestep",
        "travelling",
        "distance_travelled_on_link",
        "e",
        "attributes",
    ]

    @check_args_type
    def __init__(self, e, location, attributes):
        """
        Summary: 
            Initializes a new Person object.

        Args:
            e (Ecosystem): The ecosystem in which the person lives.
            location (Location): The location where the person is initially placed.
            attributes (dict): A dictionary of attributes for the person.

        Returns:
            None.
        """
        super().__init__(location, attributes)
        self.e = e

    @check_args_type
    def evolve(self, e, time: int, ForceTownMove: bool = False) -> None:
        """
        Summary:
            Evolves the person's state for a given time step.

        Args:
            e (Ecosystem): The ecosystem in which the person lives.
            time (int): The current time step.
            ForceTownMove (bool, optional): Whether or not to force towns to move. Defaults to False. Towns have a move chance of 1.0.

        Returns:
            None.
        """
        super().evolve(e, time=time, ForceTownMove=ForceTownMove)

    @check_args_type
    def finish_travel(self, e, time: int) -> None:
        """
        Summary: 
            Completes the person's travel to their destination location.

        Args:
            e (Ecosystem): The ecosystem in which the person lives.
            time (int): The current time step.

        Returns:
            None.
        """
        super().finish_travel(e, time=time)

    @check_args_type
    def getLinkWeightV1(self, link, awareness_level: int) -> float:
        """
        Summary: 
            Calculate the weight of an adjacent link. 
            Weight = probability that link will be chosen.

        Args:
            link (Link): The link to calculate the weight of.
            awareness_level (int): The awareness level of the person.

        Returns:
            float: The weight of the link.
        """

        if awareness_level < 0:
            return 1.0

        return float(
            self.e.scores[(link.endpoint.id * 4) + awareness_level]
            / float(SimulationSettings.move_rules["Softening"] + link.get_distance())
        )

    @check_args_type
    def getBaseEndPointScore(self, link) -> float:
        """
        Summary: 
            Overwrite serial function because we have a different data structure
            for endpoint scores.

        Args:
            link (Link): The link to calculate the score of.

        Returns:
            float: The score of the link.
        """
        return float(self.e.scores[(link.endpoint.id * 4) + 1])


class Location(flee.Location):
    """
    The Location class
    """

    @check_args_type
    def __init__(
        self,
        e,
        cur_id: int,
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
            e (Ecosystem): The ecosystem in which the location exists.
            cur_id (int): The current ID of the location.
            name (str): The name of the location.
            x (float, optional): The x coordinate of the location. Defaults to 0.0.
            y (float, optional): The y coordinate of the location. Defaults to 0.0.
            location_type (str, optional): The type of the location. Defaults to None.
            movechance (float, optional): The chance that a person will move from the location. Defaults to 0.001.
            capacity (int, optional): The capacity of the location. Defaults to -1.
            pop (int, optional): The population of the location. Defaults to 0.
            foreign (bool, optional): Whether or not the location is foreign. Defaults to False.
            country (str, optional): The country of the location. Defaults to "unknown".

        Returns: 
            None.
        """
        self.e = e

        self.id = cur_id
        self.numAgentsSpawnedOnRank = 0

        # If it is referred to in Flee in any way, the code should crash.
        super().__init__(
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

        # Emptying this array, as it is not used in the parallel version.
        self.scores = []


    @check_args_type
    def DecrementNumAgents(self) -> None:
        """
        Summary: 
            Decrements the number of agents at the location by 1.

        Args:
            None.

        Returns:
            None.
        """
        self.numAgentsOnRank -= 1


    @check_args_type
    def IncrementNumAgents(self, agent) -> None:
        """
        Summary: 
            Increments the number of agents at the location by 1.

        Args: 
            None.

        Returns: 
            None.
        """
        self.numAgentsOnRank += 1


    @check_args_type
    def print(self) -> None:
        """
        Summary: 
            Prints information about the location to the standard output stream,
            if the current process is the root process.

        Args:
            None.

        Returns:
            None.
        """
        if self.e.mpi.rank == 0:
            super().print()


    @check_args_type
    def getScore(self, index: int) -> float:
        """
        Summary: 
            Gets the score for the given index at the location.

        Args:
            index (int): The index of the score to get.

        Returns:
            float: The score for the given index.
        """
        return self.e.scores[self.id * self.e.scores_per_location + index]


    @check_args_type
    def setScore(self, index: int, value: float) -> None:
        """
        Summary: 
            Sets the score for the given index at the location.

        Args:
            index (int): The index of the score to set.
            value (float): The value to set the score to.
        
        Returns:
            None.
        """
        self.e.scores[self.id * self.e.scores_per_location + index] = value

    @check_args_type
    def updateAllScores(self, time: int) -> None:
        """
        Summary:
            Updates all scores of a particular location. Different to
            Serial Flee, due to the reversed order there.

        Args:
            time (int): The current time step.
        
        Returns: 
            None.
        """
        self.time = time
        scoring.updateLocationScore(time, self)


class Link(flee.Link):
    """
    The Link class
    """

    @check_args_type
    def __init__(self, startpoint, endpoint, distance: float, forced_redirection: bool = False, attributes: dict = {}):
        """
        Summary: 
            Creates a new link object.

        Args:
            startpoint (Location): The startpoint of the link.
            endpoint (Location): The endpoint of the link.
            distance (float): The distance between the startpoint and endpoint.
            forced_redirection (bool, optional): Whether or not the link should be used as a forced redirection. Defaults to False.
            attributes (dict, optional): A dictionary of attributes for the link. Defaults to {}.
        Returns:
            None.
        """
        super().__init__(startpoint, endpoint, distance, forced_redirection, attributes)



    @check_args_type
    def DecrementNumAgents(self) -> None:
        """
        Summary: 
            Decrements the number of agents on the link by 1.

        Args:
            None.

        Returns:
            None.
        """
        self.numAgentsOnRank -= 1
        super().DecrementNumAgents()


    @check_args_type
    def IncrementNumAgents(self, agent) -> None:
        """
        Summary: 
            Increments the number of agents on the link by 1.

        Args: 
            None.

        Returns: 
            None.
        """
        self.numAgentsOnRank += 1
        super().IncrementNumAgents(agent)


class Ecosystem(flee.Ecosystem):
    """
    The Ecosystem class
    """

    @check_args_type
    def __init__(self):
        """
        Summary: 
            Initializes a new Ecosystem object.

        Args: 
            None.

        Returns: 
            None.
        """
        self.locations = []
        self.locationNames = []
        self.agents = []
        self.total_agents = 0
        self.closures = []  # format [type, source, dest, start, end]
        self.time = 0
        self.print_location_output = False
        self.mpi = MPIManager()

        if self.getRankN(0):
            print("Creating Flee Ecosystem.", file=sys.stderr)

        self.cur_loc_id = 0
        self.scores_per_location = 4
        # single array holding all the location-related scores.
        self.scores = np.array([1.0, 1.0, 1.0, 1.0])

        # Bring conflict zone management into FLEE.
        self.spawn_weights = np.array([])

        # classic for replicated locations or loc-par for distributed
        # locations.
        self.parallel_mode = "loc-par"
        # high_latency for fewer MPI calls with more prep, or low_latency for
        # more MPI calls with less prep.
        self.latency_mode = "high_latency"

        if SimulationSettings.log_levels["camp"] > 0:
            self.num_arrivals = []  # one element per time step.
            self.travel_durations = []  # one element per time step.


    @check_args_type
    def getRankN(self, t: int) -> bool:
        """
        Summary: 
            Returns the <rank N> value, which is the rank meant to perform
            diagnostics at a given time step.
            Argument t contains the current number of time steps taken by
            the simulation.

            NOTE: This is overwritten to just give rank 0, to prevent garbage
            output ordering...

        Args:
            t (int): The current number of time steps taken by the simulation.

        Returns:
            bool: Whether or not the current process is the rank meant to perform diagnostics.
        """
        # N = t % self.mpi.size
        # if self.mpi.rank == N:
        if self.mpi.rank == 0:
            return True
        return False


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

        for loc in self.locations:
            if loc.idpcamp:
                num_idps += loc.numAgents

        num_idps_all = self.mpi.CalcCommWorldTotalSingle(num_idps)
        return num_idps_all


    @check_args_type
    def updateNumAgents(self, CountClosed: bool = False, log: bool = True) -> None:
        """
        Summary: Updates the number of agents in the ecosystem.

        Args:
            CountClosed (bool, optional): Whether to count agents on closed links. Defaults to False.
            log (bool, optional): Whether to log the updated number of agents to the standard error stream. Defaults to True.

        Returns:
            None.
        """
        mode = self.latency_mode

        total = 0

        if mode == "low_latency":
            for loc in self.locations:
                loc.numAgents = self.mpi.CalcCommWorldTotalSingle(loc.numAgentsOnRank)
                total += loc.numAgents
                # print("location:", self.time, loc.name, loc.numAgents, file=sys.stderr)
                for link in loc.links:
                    link.numAgents = self.mpi.CalcCommWorldTotalSingle(link.numAgentsOnRank)
                    # print(self.time, "link:", loc.name, link.numAgents, file=sys.stderr)
                    total += link.numAgents
                if CountClosed:
                    for link in loc.closed_links:
                        link.numAgents = self.mpi.CalcCommWorldTotalSingle(link.numAgentsOnRank)
                        # print(self.time, "link [closed]:", loc.name, link.numAgents,
                        #       file=sys.stderr)
                        total += link.numAgents
            self.total_agents = total
        elif mode == "high_latency":
            buf_len = 0

            buf_len += len(self.locations)
            for loc in self.locations:
                buf_len += len(loc.links)
                if CountClosed:
                    buf_len += len(loc.closed_links)

            numAgent_buffer = np.empty(buf_len, dtype="i")

            index = 0
            for loc in self.locations:
                numAgent_buffer[index] = loc.numAgentsOnRank
                index += 1
                for link in loc.links:
                    numAgent_buffer[index] = link.numAgentsOnRank
                    index += 1
                if CountClosed:
                    for link in loc.closed_links:
                        numAgent_buffer[index] = link.numAgentsOnRank
                        index += 1

            new_buffer = self.mpi.CalcCommWorldTotal(numAgent_buffer)

            index = 0
            for loc in self.locations:
                loc.numAgents = new_buffer[index]
                index += 1
                for link in loc.links:
                    link.numAgents = new_buffer[index]
                    index += 1
                if CountClosed:
                    for link in loc.closed_links:
                        link.numAgents = new_buffer[index]
                        index += 1

            self.total_agents = np.sum(new_buffer)

        if self.mpi.rank == 0 and log is True:
            print(
                "NumAgents updated. Total agents in simulation:", self.total_agents, file=sys.stderr
            )

    """
    Add & insert agent functions.
    TODO: make addAgent function smarter, to prevent large load imbalances
    over time due to removals by clearLocationFromAgents?
    """

    @check_args_type
    def addAgent(self, location, attributes) -> None:
        """
        Summary: 
            Adds an agent to the ecosystem at the specified location.

        Args:
            location (Location): The location to add the agent to.
            attributes (dict): A dictionary of attributes for the agent.

        Returns:
            None.
        """
        if SimulationSettings.spawn_rules["TakeFromPopulation"]:
            if location.conflict > 0.0:  
                if location.pop > 1: 
                    location.pop -= 1
                    location.numAgentsSpawnedOnRank += 1
                    location.numAgentsSpawned += 1
                else:
                    print(
                        "ERROR: Number of agents in the simulation is larger than the combined "
                        "population of the conflict zones. Please amend locations.csv." 
                    )
                    location.print()
                    assert location.pop > 1
        self.total_agents += 1
        if self.total_agents % self.mpi.size == self.mpi.rank:
            self.agents.append(Person(self, location=location, attributes=attributes))


    @check_args_type
    def insertAgent(self, location) -> None:
        """
        Summary: 
            Inserts an agent into the ecosystem at the specified location.
            Note: insert Agent does NOT take from Population.

        Args:
            location (Location): The location to insert the agent into.

        Returns:
            None.
        """
        self.total_agents += 1
        if self.total_agents % self.mpi.size == self.mpi.rank:
            self.agents.append(Person(self, location=location))


    @check_args_type
    def insertAgents(self, location, number: int) -> None:
        """
        Summary: 
            Inserts a number of agents into the ecosystem at the specified
            location.
            Note: insert Agent does NOT take from Population.

        Args:
            location (Location): The location to insert the agents into.
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

            TODO : REWRITE!!

        Args:
            location_names (List[str]): A list of location names to remove agents from.

        Returns: 
            None. 
        """

        new_agents = []
        for agent in self.agents:
            if agent.location.name not in location_names:
                new_agents += [agent]
            else:
                # print("Agent removed: ", agent.location.name)
                # agent is removed from ecosystem and number of agents in
                # location drops by one.
                agent.location.numAgentsOnRank -= 1

        self.agents = new_agents
        print("clearLocationsFromAgents()", file=sys.stderr)
        # when numAgentsOnRank has changed, we need to updateNumAgents (1x
        # MPI_Allreduce)
        self.updateNumAgents(log=False)


    @check_args_type
    def numAgents(self) -> int:
        """
        Summary: 
            Returns the number of agents in the ecosystem.

        Args:
            None.

        Returns:
            int: The number of agents in the ecosystem.
        """
        return int(self.total_agents)


    @check_args_type
    def numAgentsOnRank(self) -> int:
        """
        Summary:
            Returns the number of agents on the current process.

        Args:
            None.

        Returns:
            int: The number of agents on the current process.
        """
        return len(self.agents)


    @check_args_type
    def synchronize_locations(self, start_loc_local: int, end_loc_local: int, Debug: bool = False) -> None:
        """
        Summary: 
            Gathers the scores from all the updated locations,
            and propagates them across the processes.

        Args:
            start_loc_local (int): The index of the first location to synchronize.
            end_loc_local (int): The index of the last location to synchronize.
            Debug (bool, optional): Turns on debugging output. Defaults to False.

        Returns:
            None.
        """

        base = int((len(self.scores) / self.scores_per_location) / self.mpi.size)
        leftover = int((len(self.scores) / self.scores_per_location) % self.mpi.size)

        if Debug:
            print("Sync Locs:", self.mpi.rank, base, leftover, len(self.scores), file=sys.stderr)

        sizes = np.ones(self.mpi.size, dtype="i") * base
        sizes[:leftover] += 1
        sizes *= self.scores_per_location
        offsets = np.zeros(self.mpi.size, dtype="i")
        offsets[1:] = np.cumsum(sizes)[:-1]

        assert np.sum(sizes) == len(self.scores)
        assert offsets[-1] + sizes[-1] == len(self.scores)

        # Populate scores array
        scores_start = int(offsets[self.mpi.rank])
        local_scores_size = int(sizes[self.mpi.rank])
        local_scores = self.scores[scores_start : scores_start + local_scores_size].copy()

        if Debug and self.mpi.rank == 0:
            print("start of synchronize_locations MPI call.", file=sys.stderr)
            # print(self.mpi.rank, local_scores, self.scores, sizes, offsets)
        self.mpi.comm.Allgatherv(local_scores, [self.scores, sizes, offsets, MPI.DOUBLE])

        if Debug and self.mpi.rank == 0:
            print("end of synchronize_locations", file=sys.stderr)


    @check_args_type
    def evolve(self) -> None:
        """
        Summary:
            Evolves the ecosystem for a single time step.
        
        Args: 
            None.

        Returns:
            None.

        """
        if self.time == 0:
            # print("rank, num_agents:", self.mpi.rank, len(self.agents))

            # Update all scores three times to ensure code starts with updated
            # scores.
            for _ in range(0, 3):
                for i, loc in enumerate(self.locations):
                    if i % self.mpi.size == self.mpi.rank:
                        loc.updateAllScores(time=self.time)

        if self.parallel_mode == "classic":
            # update level 1 location scores (2 and 3 are obsolete).
            # Scores remain perfectly updated in classic mode.
            for loc in self.locations:
                loc.time = self.time
                scoring.updateLocationScore(self.time, loc)

        elif self.parallel_mode == "loc-par":
            # update scores in reverse order for efficiency.
            # Neighbourhood and Region score will be outdated by 1 and 2 time
            # steps resp.

            loc_per_rank = int(len(self.locations) / self.mpi.size)
            lpr_remainder = int(len(self.locations) % self.mpi.size)

            offset = int(self.mpi.rank) * int(loc_per_rank) + int(min(self.mpi.rank, lpr_remainder))
            num_locs_on_this_rank = int(loc_per_rank)
            if self.mpi.rank < lpr_remainder:
                num_locs_on_this_rank += 1

            for i in range(offset, offset + num_locs_on_this_rank):
                self.locations[i].updateAllScores(time=self.time)

            self.synchronize_locations(
                start_loc_local=offset, end_loc_local=offset + num_locs_on_this_rank
            )

        # SYNCHRONIZE SPAWN COUNTS IN LOCATIONS (needed for all versions).
        spawn_counts = np.zeros(len(self.locations), dtype="i")
        for i, le in enumerate(self.locations):
            # print(i, spawn_counts.size)
            spawn_counts[i] = le.numAgentsSpawnedOnRank

        # allreduce (sum up) spawn counts.
        spawn_totals = self.mpi.CalcCommWorldTotal(spawn_counts)

        # update location spawn total.
        for i, le in enumerate(self.locations):
            le.numAgentsSpawned = spawn_totals[i]

        # update agent locations
        for a in self.agents:
            a.evolve(self, time=self.time)

        # print("NumAgents after evolve:", file=sys.stderr)
        self.updateNumAgents(CountClosed=True, log=False)

        for a in self.agents:
            a.finish_travel(self, time=self.time)
            a.timesteps_since_departure += 1

        if SimulationSettings.log_levels["agent"] > 0:
            write_agents_par(rank=self.mpi.rank, agents=self.agents, time=self.time)

        if SimulationSettings.log_levels["link"] > 0:
            write_links_par(rank=self.mpi.rank, locations=self.locations, time=self.time)

        for a in self.agents:
            a.recent_travel_distance = (
                a.recent_travel_distance
                + (a.distance_moved_this_timestep / SimulationSettings.move_rules["MaxMoveSpeed"])
            ) / 2.0
            a.distance_moved_this_timestep = 0

        # print("NumAgents after finish_travel:", file=sys.stderr)
        self.updateNumAgents(log=False)

        # update link properties
        if SimulationSettings.log_levels["camp"] > 0:
            self._aggregate_arrivals()

        # Deactivate agents in camps with a certain probability.
        if SimulationSettings.spawn_rules["camps_are_sinks"] == True:
            for a in self.agents:
                if a.travelling == False:
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
        movechance: float = -1.0,
        capacity: int = -1,
        pop: int = 0,
        foreign: bool = False,
        country: str = "unknown",
        attributes: dict = {},
    ):
        """
        Summary: 
            Add a location to the ABM network graph.

        Args:
            name (str): The name of the location.
            x (float, optional): The x coordinate of the location. Defaults to 0.0.
            y (float, optional): The y coordinate of the location. Defaults to 0.0.
            location_type (str, optional): The type of the location. Defaults to None.
            movechance (float, optional): The chance that a person will move from the location. Defaults to -1.0.
            capacity (int, optional): The capacity of the location. Defaults to -1.
            pop (int, optional): The population of the location. Defaults to 0.
            foreign (bool, optional): Whether or not the location is foreign. Defaults to False.
            country (str, optional): The country of the location. Defaults to "unknown".

        No Longer Returned:
            Location: The location that was added.

        Returns: 
            None.

        """

        if movechance < 0.0:
            movechance = SimulationSettings.move_rules["DefaultMoveChance"]

        # Enlarge the scores array in Ecosystem to reflect the new location.
        # Pflee only.
        if self.cur_loc_id > 0:
            self.scores = np.append(self.scores, np.array([1.0, 1.0, 1.0, 1.0]))
        # print(len(self.scores))

        loc = Location(
            self,
            cur_id=self.cur_loc_id,
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

        self.cur_loc_id += 1

        if SimulationSettings.log_levels["init"] > 0:
            print(
                "Location: {} {} {} {} {} , pop. {} {}".format(
                    name, x, y, loc.movechance, capacity, pop, foreign
                ),
                file=sys.stderr,
            )
        self.locations.append(loc)
        self.spawn_weights = np.append(self.spawn_weights, [0.0])
        self.locationNames.append(loc.name)

        spawning.refresh_spawn_weights(self)


        return loc


    @check_args_type
    def printComplete(self) -> None:
        """
        Summary:
            Prints information about the ecosystem to the standard output stream,
            if the current process is the root process.

        Args:
            None.

        Returns:
            None.
        """
        if self.mpi.rank == 0:
            super().printComplete()


    @check_args_type
    def printInfo(self) -> None:
        """
        Summary:
            Prints information about the ecosystem to the standard output stream,
            if the current process is the root process.

        Args: 
            None.

        Returns:
            None.
        """
        if self.mpi.rank == 0:
            super().printInfo()


if __name__ == "__main__":
    print("No testing functionality here yet.")
