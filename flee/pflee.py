from __future__ import annotations

import os
import sys
from functools import wraps
from typing import List, Optional

import numpy as np
from flee import flee,scoring,spawning
from flee.Diagnostics import write_agents_par
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
        "age",
        "gender",
        "attributes",
    ]

    @check_args_type
    def __init__(self, e, location, age, gender, attributes):
        super().__init__(location, age, gender, attributes)
        self.e = e

    @check_args_type
    def evolve(self, time: int, ForceTownMove: bool = False) -> None:
        """
        Summary

        Args:
            time (int): Description
            ForceTownMove (bool, optional): Description
        """
        super().evolve(time=time, ForceTownMove=ForceTownMove)

    @check_args_type
    def finish_travel(self, time: int) -> None:
        """
        Summary

        Args:
            time (int): Description
        """
        super().finish_travel(time=time)

    @check_args_type
    def getLinkWeightV1(self, link, awareness_level: int) -> float:
        """
        Calculate the weight of an adjacent link. Weight = probability that
        it will be chosen.

        Args:
            link (Link): Description
            awareness_level (int): Description

        Returns:
            float: Description
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
        Overwrite serial function because we have a different data structure
        for endpoint scores.

        Args:
            link (Link) : Description

        Returns:
            float: Description
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
        x: float = 0.0,
        y: float = 0.0,
        location_type: Optional[str] = None,
        movechance: float = 0.001,
        capacity: int = -1,
        pop: int = 0,
        foreign: bool = False,
        country: str = "unknown",
    ) -> None:
        self.e = e

        self.id = cur_id
        self.numAgentsSpawnedOnRank = 0

        # If it is referred to in Flee in any way, the code should crash.
        super().__init__(
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

        # Emptying this array, as it is not used in the parallel version.
        self.scores = []

    @check_args_type
    def DecrementNumAgents(self) -> None:
        """
        Summary
        """
        self.numAgentsOnRank -= 1

    @check_args_type
    def IncrementNumAgents(self) -> None:
        """
        Summary
        """
        self.numAgentsOnRank += 1

    @check_args_type
    def print(self) -> None:
        """
        Summary
        """
        if self.e.mpi.rank == 0:
            super().print()

    @check_args_type
    def getScore(self, index: int) -> float:
        """
        Summary

        Args:
            index (int): Description

        Returns:
            float: Description
        """
        return self.e.scores[self.id * self.e.scores_per_location + index]

    @check_args_type
    def setScore(self, index: int, value: float) -> None:
        """
        Summary

        Args:
            index (int): Description
            value (float): Description
        """
        self.e.scores[self.id * self.e.scores_per_location + index] = value

    @check_args_type
    def updateAllScores(self, time: int) -> None:
        """
        Updates all scores of a particular location. Different to
        Serial Flee, due to the reversed order there.

        Args:
            time (int): Description
        """
        self.time = time
        scoring.updateRegionScore(self)
        scoring.updateNeighbourhoodScore(self)
        scoring.updateLocationScore(time, self)


class Link(flee.Link):
    """
    The Link class
    """

    @check_args_type
    def __init__(self, startpoint, endpoint, distance: float, forced_redirection: bool = False):
        super().__init__(startpoint, endpoint, distance, forced_redirection)

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


class Ecosystem(flee.Ecosystem):
    """
    The Ecosystem class
    """

    @check_args_type
    def __init__(self):
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
        Returns the <rank N> value, which is the rank meant to perform
        diagnostics at a given time step.
        Argument t contains the current number of time steps taken by
        the simulation.

        NOTE: This is overwritten to just give rank 0, to prevent garbage
        output ordering...

        Args:
            t (int): Description

        Returns:
            bool: Description
        """
        # N = t % self.mpi.size
        # if self.mpi.rank == N:
        if self.mpi.rank == 0:
            return True
        return False

    @check_args_type
    def updateNumAgents(self, CountClosed: bool = False, log: bool = True) -> None:
        """
        Summary

        Args:
            CountClosed (bool, optional): Description
            log (bool, optional): Description
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
            new_buffer = np.empty(buf_len, dtype="i")

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
    def addAgent(self, location, age, gender, attributes) -> None:
        """
        Summary

        Args:
            location (Location): Description
        """
        if SimulationSettings.spawn_rules["TakeFromPopulation"]:
            if location.conflict:
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
            self.agents.append(Person(self, location=location, age=age, gender=gender, attributes=attributes))


    @check_args_type
    def insertAgent(self, location) -> None:
        """
        Note: insert Agent does NOT take from Population.

        Args:
            location (Location): Description
        """
        self.total_agents += 1
        if self.total_agents % self.mpi.size == self.mpi.rank:
            self.agents.append(Person(self, location=location))

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

        TODO : REWRITE!!

        Args:
            location_names (List[str]): Description
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
        Summary

        Returns:
            int: Description
        """
        return int(self.total_agents)

    @check_args_type
    def numAgentsOnRank(self) -> int:
        """
        Summary

        Returns:
            int: Description
        """
        return len(self.agents)

    @check_args_type
    def synchronize_locations(
        self, start_loc_local: int, end_loc_local: int, Debug: bool = False
    ) -> None:
        """
        Gathers the scores from all the updated locations, and propagates them
        across the processes.

        Args:
            start_loc_local (int): Description
            end_loc_local (int): Description
            Debug (bool, optional): Description
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
        Summary
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
            # update level 1, 2 and 3 location scores.
            # Scores remain perfectly updated in classic mode.
            for loc in self.locations:
                loc.time = self.time
                scoring.updateLocationScore(loc)

            for loc in self.locations:
                scoring.updateNeighbourhoodScore(loc)

            for loc in self.locations:
                scoring.updateRegionScore(loc)

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
            a.evolve(time=self.time)

        # print("NumAgents after evolve:", file=sys.stderr)
        self.updateNumAgents(CountClosed=True, log=False)

        for a in self.agents:
            a.finish_travel(time=self.time)
            a.timesteps_since_departure += 1

        if SimulationSettings.log_levels["agent"] > 0:
            write_agents_par(rank=self.mpi.rank, agents=self.agents, time=self.time)

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

        self.time += 1

    @check_args_type
    def addLocation(
        self,
        name: str,
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
            x=x,
            y=y,
            location_type=location_type,
            movechance=movechance,
            capacity=capacity,
            pop=pop,
            foreign=foreign,
            country=country,
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
        Summary
        """
        if self.mpi.rank == 0:
            super().printComplete()

    @check_args_type
    def printInfo(self) -> None:
        """
        Summary
        """
        if self.mpi.rank == 0:
            super().printInfo()


if __name__ == "__main__":
    print("No testing functionality here yet.")
