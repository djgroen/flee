from flee.SimulationSettings import SimulationSettings
import numpy as np
import os

from typing import List, Optional, Tuple

if os.getenv("FLEE_TYPE_CHECK") is not None and os.environ["FLEE_TYPE_CHECK"].lower() == "true":
    from beartype import beartype as check_args_type
else:
    def check_args_type(func):
        return func


@check_args_type
def updateLocationScore(time: int, loc) -> None:
    """
    Summary: 
        Attractiveness of the local point, based on local point
        information only.

    Args: 
        time (int): The current timestep
        loc (Location): The location to update the score for

    Returns:
        None. The score is updated in place.
    """

    score = 1.0 #default score

    #score multiplier for foreign
    if loc.foreign is True:
        score *= SimulationSettings.move_rules["ForeignWeight"] 

    #score multiplier for camps
    if loc.camp or loc.idpcamp is True:
        score *= SimulationSettings.move_rules["CampWeight"] 

    #score multiplier for conflict
    if loc.conflict > 0.0: 
        #score takes the conflict weight to the power of the conflict decay multiplier
        #conflict decay multiplier is larger for locations with conflict for longer periods of time
        score *= SimulationSettings.move_rules["ConflictWeight"]**(SimulationSettings.get_location_conflict_decay(time, loc) * loc.conflict)
    

    loc.setScore(0, 1.0)
    #print(loc.name,loc.camp,loc.foreign,loc.scores)

