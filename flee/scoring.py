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
    Attractiveness of the local point, based on local point
    information only.
    """

    score = 1.0

    if loc.foreign is True:
        score *= SimulationSettings.move_rules["ForeignWeight"]
    if loc.camp or loc.idpcamp is True:
        score *= SimulationSettings.move_rules["CampWeight"]
    if loc.conflict > 0.0:
        score *= SimulationSettings.move_rules["ConflictWeight"]**(SimulationSettings.get_location_conflict_decay(time, loc) * loc.conflict)

    loc.setScore(1, score)

    loc.setScore(0, 1.0)
    #print(loc.name,loc.camp,loc.foreign,loc.scores)

