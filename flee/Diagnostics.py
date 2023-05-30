from __future__ import annotations, print_function

import os
import sys
from functools import wraps
from flee.SimulationSettings import SimulationSettings

if os.getenv("FLEE_TYPE_CHECK") is not None and os.environ["FLEE_TYPE_CHECK"].lower() == "true":
    from beartype import beartype as check_args_type
else:
    def check_args_type(func):
        return func


def print_attribute_keys(a):
    out = ""
    for k in a.attributes.keys():
        out += str(k)
        out += ","
    return out


def print_attribute_values(a):
    out = ""
    for k in a.attributes.values():
        out += str(k)
        out += ","
    return out


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
            "#time,rank-agentid,original_location,current_location,gps_x,gps_y,is_travelling,distance_travelled,"
            "places_travelled,distance_moved_this_timestep,{}".format(print_attribute_keys(agents[0])),
            file=my_file,
        )
    else:
        my_file = open("agents.out.%s" % rank, "a", encoding="utf-8")

    if max_written < 0:
        max_written = len(agents)

    if time % timestep_interval == 0:
        for k in range(0, max_written):
            a = agents[k]
            print(
                    "{},{}-{},{},{},{},{},{},{},{},{},{}".format(
                    time,
                    rank,
                    k,
                    a.home_location.name,
                    a.location.name,
                    a.location.x,
                    a.location.y,
                    a.travelling,
                    a.distance_travelled,
                    a.places_travelled,
                    a.distance_moved_this_timestep,
                    print_attribute_values(a),
                    ),
                file=my_file,
            )

            if SimulationSettings.log_levels["agent"] > 1:
                if SimulationSettings.log_levels["agent"] > 2:
                    hop_number = 1 # hop counter starts at 1 to indicate second hop in time step.
                    for l in a.locations_visited:
                        print(
                            "{}-{},{}-{},{},{},{},{},{},{},{},{},{}".format(
                                time,
                                hop_number,
                                rank,
                                k,
                                a.home_location.name,
                                l.name,
                                l.x,
                                l.y,
                                a.travelling,
                                a.distance_travelled,
                                a.places_travelled,
                                a.distance_moved_this_timestep,
                                print_attribute_values(a),
                            ),
                            file=my_file,
                        )
                        hop_number += 1
                else:
                    for l in a.locations_visited:
                        print(
                            "{},{}-{},{},{},{},{},{},{},{},{},{}".format(
                                time,
                                rank,
                                k,
                                a.home_location.name,
                                l.name,
                                l.x,
                                l.y,
                                a.travelling,
                                a.distance_travelled,
                                a.places_travelled,
                                a.distance_moved_this_timestep,
                                print_attribute_values(a),
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


@check_args_type
def write_links_par(
    rank: int, locations, time: int, timestep_interval: int = 1
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
        my_file = open("links.out.%s" % rank, "w", encoding="utf-8")
        print(
            "#time,start_location,end_location,cum_num_agents,attribute",
            file=my_file,
        )
    else:
        my_file = open("links.out.%s" % rank, "a", encoding="utf-8")

    if time % timestep_interval == 0:
        for i in range(0, len(locations)):
            for l in locations[i].links:
                print(
                    "{},{},{},{},total".format(
                    time,
                    l.startpoint.name,
                    l.endpoint.name,
                    l.cumNumAgents,
                    ),
                file=my_file,
                )

                if SimulationSettings.log_levels["link"] > 1:
                    for a in l.cumNumAgentsByAttribute:
                        for v in l.cumNumAgentsByAttribute[a]:
                            print(
                                "{},{},{},{},{}:{}".format(
                                time,
                                l.startpoint.name,
                                l.endpoint.name,
                                l.cumNumAgentsByAttribute[a][v],
                                a,
                                v,
                                ),
                            file=my_file,
                            )




@check_args_type
def write_links(locations, time: int, timestep_interval: int = 1) -> None:
    """
    Summary

    Args:
        agents (List[Person]): Description
        time (int): Description
        max_written (int, optional): Description
        timestep_interval (int, optional): Description
    """
    write_links_par(rank=0, locations=locations, time=time, timestep_interval=1)

