from __future__ import annotations, print_function

import os
from functools import wraps

if os.getenv("FLEE_TYPE_CHECK") is not None and os.environ["FLEE_TYPE_CHECK"].lower() == "true":
    from beartype import beartype as check_args_type
else:
    def check_args_type(func):
        return func



@check_args_type
def write_agents_par(
    rank: int, agents, time: int, max_written: int = -1, timestep_interval: int = 1
) -> None:
    """
    Write agent data to file. Write only up to <max_written> agents each time step,
    and only write a file every <timestep_interval> time steps.

    Args:
        rank (int): Description
        agents (List[Person]): Description
        time (int): Description
        max_written (int, optional): Description
        timestep_interval (int, optional): Description
    """

    my_file = None
    if time == 0:
        my_file = open("agents.out.%s" % rank, "w", encoding="utf-8")
        print(
            "#time,rank-agentid,agent location,gps_x,gps_y,is_travelling,distance_travelled,"
            "places_travelled,distance_moved_this_timestep",
            file=my_file,
        )
    else:
        my_file = open("agents.out.%s" % rank, "a", encoding="utf-8")

    if max_written < 0:
        max_written = len(agents)

    if time % timestep_interval == 0:
        for k in range(0, max_written):
            a = agents[k]
            gps_x = 0.0
            gps_y = 0.0
            print(
                    "{},{}-{},{},{},{},{},{},{},{}".format(
                    time,
                    rank,
                    k,
                    a.location.name,
                    gps_x,
                    gps_y,
                    a.travelling,
                    a.distance_travelled,
                    a.places_travelled,
                    a.distance_moved_this_timestep,
                    ),
                file=my_file,
            )


@check_args_type
def write_agents(agents, time: int, max_written: int = -1, timestep_interval: int = 1) -> None:
    """
    Summary

    Args:
        agents (List[Person]): Description
        time (int): Description
        max_written (int, optional): Description
        timestep_interval (int, optional): Description
    """
    write_agents_par(rank=0, agents=agents, time=time, max_written=-1, timestep_interval=1)
