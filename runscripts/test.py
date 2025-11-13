def updateAgentsFromLocations(self, agents, location_update_dict: dict) -> None:
    """
    update a specific number of agents from each location, using a nested dictionary.
    Args:
        location_update_dict (dict): {location_name: {"update": num_to_update}}
    """
    new_agents = []
    update_counters = {loc: 0 for loc in location_update_dict}
    # In the original agents list, remove agents as needed
    print("agents before update:", len(agents))
    for agent, loc_name in agents.items():
        #  = agent[.location.name]
        num_to_update = location_update_dict[loc_name]
        print('num_to_update for location', loc_name, ':', num_to_update)
        if num_to_update < 0 and update_counters[loc_name] > num_to_update:
            print(f"Removing {agent} from location {loc_name}")
            # agent.location.DecrementNumAgents()
            update_counters[loc_name] -= 1
        else:
            new_agents.append(agent)  # agent is preserved
            print(f"Keeping {agent} at location {loc_name}")

    # Now add agents where needed        
    for loc_name in location_update_dict:
        num_to_update = location_update_dict[loc_name]
        if num_to_update > 0:
            print(f"Adding {num_to_update} agents to location {loc_name}")
            for num in range(num_to_update):
                new_agent_id = max(agents.keys()) + 1 + num
                new_agents.append(new_agent_id)
                print(f"Added new agent {new_agent_id} to location {loc_name}")
                update_counters[loc_name] += 1
                # loc = lm[loc_name]
                # attributes = spawning.draw_samples(e, loc)
                # e.addAgent(location=loc, attributes=attributes) 

        print(f"Final count for location {loc_name}: {update_counters[loc_name]}")
    agents = new_agents
    print("agents after update:", len(agents))

diff_dict = {'Bajone': -1, 'Campo': 5, 'Cidade_De_Quelimane': 0,}
agents = {1:'Bajone', 2:'Campo', 3:'Cidade_De_Quelimane'}  # Example list of agents
updateAgentsFromLocations(agents, diff_dict)