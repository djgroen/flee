import csv
import os
import sys
from typing import List

from flee.SimulationSettings import SimulationSettings

if os.getenv("FLEE_TYPE_CHECK") is not None and os.environ["FLEE_TYPE_CHECK"].lower() == "true":
    from beartype import beartype as check_args_type
else:
    def check_args_type(func):
        #Commented out because it introduces 10% slowdown.
        #@wraps(func)
        #def wrapper(*args, **kwargs):
        #    return func(*args, **kwargs)
        #return wrapper
        return func


class ParticleFilter:
    """
    Class which creates the Particle Filter.
    """

    def __init__(self):
        pass

    # TODO: Implement data assimilation step here.
    # GOAL: Compare current number of agents in each location to observed data and adjust agent locations accordingly
    # Add in simulation setttings a flag to turn data assimilation on or off
    # Read in observed data from file or other source
    # For every location compare observed to simulated using particle filter
    # Use AddAgents, InsertAgents or Location.IncrementNumAgents to add agents to locations
    # Use clearLocationsFromAgents, Location.DecrementNumAgens, or something similar as code piece in flee at line 1683
    # to remove agents from locations
    # I am not sure what the difference between methods are, need to test and see response
    if SimulationSettings.spawn_rules["data_assimilation_enabled"] == True:
        # Read the days in the observation file
        # Run particles until that the next observation day
        # Save Ecosystem state per particle in dict {particle_id: Ecosystem_state}
        # Compare each particles locations with observed data
        # Update weights of particles based on comparison
        # Resample particles based on weights
        # Run next iteration until end of simulation

        # If time is in day column of SimulationSettings.ObservationsFile (might want to do the reading of csv in input geography)
        # For location in locations:
            # Update location agent numbers based on observed data using
            # ParticleFilter()
        
        pass  # Placeholder for future implementation
        