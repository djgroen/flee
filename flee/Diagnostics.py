def write_agents_par(rank, agents, time, max_written=-1, timestep_interval=1):
    """
    Write agent data to file. Write only up to <max_written> agents each time step, and only write a file every <timestep_interval> time steps.
    """

    my_file = None
    if time == 0:
        my_file = open('agents.out.%s' % rank, 'w', encoding='utf-8')
        print("#time, rank-agentid, agent location, gps_x, gps_y, is_travelling, distance_travelled, places_travelled, distance_moved_this_timestep", file=my_file)
    else:
        my_file = open('agents.out.%s' % rank, 'a', encoding='utf-8')

    if max_written < 0:
        max_written = len(agents)

    if time % timestep_interval == 0:
        for k,a in enumerate(agents[0:max_written]):
            gps_x = 0.0
            gps_y = 0.0
            print("{},{}-{},{},{},{},{},{},{},{}".format(time, rank, k, a.location.name, gps_x, gps_y, a.travelling, a.distance_travelled, a.places_travelled, a.distance_moved_this_timestep), file=my_file)


def write_agents(agents, time, max_written=-1, timestep_interval=1):
    write_agents_par(0, agents, time, max_written=-1, timestep_interval=1)
