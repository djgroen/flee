from flee.SimulationSettings import SimulationSettings
import numpy as np
import sys
import os
import pandas as pd

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

    if loc.camp:
        if loc.foreign:
            score *= SimulationSettings.move_rules["CampWeight"] * SimulationSettings.move_rules["ForeignWeight"]
        else:
            score *= SimulationSettings.move_rules["CampWeight"]
    elif loc.foreign:
        score *= SimulationSettings.move_rules["ForeignWeight"]
    elif loc.conflict:
        score *= SimulationSettings.move_rules["ConflictWeight"]**SimulationSettings.get_location_conflict_decay(time, loc)

    loc.setScore(1, score)

    loc.setScore(0, 1.0)
    # print(loc.name,loc.camp,loc.foreign,loc.LocationScore)


@check_args_type
def updateNeighbourhoodScore(loc) -> None:
    """
    Attractiveness of the local point, based on information from local and
    adjacent points, weighted by link length.
    """
    # No links connected or a Camp? Use LocationScore.
    if len(loc.links) == 0 or loc.camp:
        loc.setScore(2, loc.getScore(index=1))
    else:
        NeighbourhoodScore = 0.0
        total_link_weight = 0.0

        for link in loc.links:
            NeighbourhoodScore += link.endpoint.getScore(1) / float(
                link.get_distance()
            )
            total_link_weight += 1.0 / float(link.get_distance())

        NeighbourhoodScore /= total_link_weight
        loc.setScore(2, NeighbourhoodScore)


@check_args_type
def updateRegionScore(loc) -> None:
    """
    Attractiveness of the local point, based on neighbourhood information
    from local and adjacent points, weighted by link length.
    """
    # No links connected or a Camp? Use LocationScore.
    if len(loc.links) == 0 or loc.camp:
        loc.setScore(3, loc.getScore(2))
    else:
        RegionScore = 0.0
        total_link_weight = 0.0

        for link in loc.links:
            RegionScore += link.endpoint.getScore(2) / float(
                link.get_distance()
            )
            total_link_weight += 1.0 / float(link.get_distance())

        RegionScore /= total_link_weight
        loc.setScore(3, RegionScore)

