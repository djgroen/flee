import os
import sys
import numpy as np
import random
from typing import List, Optional, Tuple
from flee.SimulationSettings import SimulationSettings

if os.getenv("FLEE_TYPE_CHECK") is not None and os.environ["FLEE_TYPE_CHECK"].lower() == "true":
    from beartype import beartype as check_args_type
else:
    def check_args_type(func):
        return func



@check_args_type
def getEndPointScore(agent, link) -> float:
    """
    Summary

    Args:
        agent (Person): agent making the decision
        link (Link): Description

    Returns:
        float: Description
    """
    # print(link.endpoint.name, link.endpoint.scores)
    base = agent.getBaseEndPointScore(link) # called externally because serial and parallel implementations differ.

    # The base score is derived from the perceived level of safety and security.
    # E.g. Conflict zones have lower scores, camps have higher scores.
    # Location effects like high/low GDP, food security or weather effects could later also alter this score.

    #["ChildrenAvoidHazards", "BoysTakeRisk", "MatchCampEthnicity", "MatchTownEthnicity", "MatchConflictEthnicity"]
    if SimulationSettings.move_rules["ChildrenAvoidHazards"] and agent.age <19:
        # For children the safety of the destination is more important than for adults.
        base = base*base
        if SimulationSettings.move_rules["BoysTakeRisk"] and agent.gender=="male" and agent.age>14:
            # Hypothesis that perceived safety does not affect routing decisions for teenage boys.
            base = 1 

    if link.endpoint.camp == True:
        if SimulationSettings.move_rules["MatchCampEthnicity"]:
            base *= (spawning.getAttributeRatio(link.endpoint, "ethnicity") * 10.0)
    elif link.endpoint.conflict == True:
        if SimulationSettings.move_rules["MatchConflictEthnicity"]:
            base *= (spawning.getAttributeRatio(link.endpoint, "ethnicity") * 10.0)
    else:
        if SimulationSettings.move_rules["MatchTownEthnicity"]:
            base *= (spawning.getAttributeRatio(link.endpoint, "ethnicity") * 10.0)

    return base


@check_args_type
def getCapMultiplier(location, numOnLink: int) -> float:
    """
    Checks whether a given location has reached full capacity
    or is close to it.

    Args:
        numOnLink (int): Description

    Returns:
        float: return

        - 1.0 if occupancy < nearly_full_occ (0.9).
        - 0.0 if occupancy >= 1.0.
        - a value in between for intermediate values
    """

    nearly_full_occ = 0.9  # occupancy rate to be considered nearly full.
    # full occupancy limit (should be equal to self.capacity).
    cap_limit = location.capacity * SimulationSettings.move_rules["CapacityBuffer"]

    if location.capacity < 0:
        return 1.0

    if location.numAgents <= nearly_full_occ * cap_limit:
        return 1.0

    if location.numAgents >= 1.0 * cap_limit:
        return 0.0

    # should be a number equal in range [0 to 0.1*self.numAgents].
    residual = location.numAgents - (nearly_full_occ * cap_limit)

    # Calculate the residual weighting factor, when pop is between 0.9 and
    # 1.0 of capacity (with default settings).
    weight = 1.0 - (residual / (cap_limit * (1.0 - nearly_full_occ)))

    assert weight >= 0.0
    assert weight <= 1.0

    return weight



@check_args_type
def calculateLinkWeight(
  agent,
  link,
  prior_distance: float,
  origin_names: List[str],
  step: int,
  time: int,
  debug: bool = False,
) -> float:
  """
  Calculates Link Weights recursively based on awareness level.
  Loops are avoided.

  Args:
  a: agent
  link (Link): Description
  prior_distance (float): Description
  origin_names (List[str]): Description
  step (int): Description
  time (int): Description
  debug (bool, optional): Description
  """



  weight = float(getEndPointScore(agent=agent, link=link)
          / float(SimulationSettings.move_rules["Softening"] + link.get_distance() + prior_distance)) * getCapMultiplier(link.endpoint, numOnLink=int(link.numAgents))


  if SimulationSettings.move_rules["AwarenessLevel"] > step:
    # Traverse the tree one step further.
    for lel in link.endpoint.links:
      if lel.endpoint.name in origin_names:
        # Link points back to an origin, so ignore.
        pass
      else:
        weight = max(
          weight,
          calculateLinkWeight(agent=agent,
              link=lel,
              prior_distance=prior_distance + link.get_distance(),
              origin_names=origin_names + [link.endpoint.name],
              step=step + 1,
              time=time,
              debug=debug,
              ),
          )

  if debug:
    print("step {}, total weight returned {}".format(step, weight))
  return weight


@check_args_type
def normalizeWeights(weights) -> list:
  """
  Summary

  Args:
    weights (List[float]): Description

  Returns:
    list: Description
  """
  if np.sum(weights) > 0.0:
    weights /= np.sum(weights)
  else:  # if all have zero weight, then we do equal weighting.
    weights += 1.0 / float(len(weights))
  return weights.tolist()



@check_args_type
def chooseFromWeights(weights, linklist):
  """
  Summary

  Args:
    weights (List[float]): Description
    linklist (List[Link]): Description

  Returns:
    float: Description
  """
  if len(weights) == 0:
    return None

  weights = normalizeWeights(weights=weights)
  result = random.choices(linklist, weights=weights)
  return result[0]


@check_args_type
def selectRoute(a, time: int, debug: bool = False):
  """
  Summary

  Args:
  a: Agent
  time (int): Description
  debug (bool, optional): Description

  Returns:
  int: Description
  """
  linklen = len(a.location.links)
  weights = np.zeros(linklen)

  if SimulationSettings.move_rules["AwarenessLevel"] == 0:
    return np.random.randint(0, linklen)

  for k, e in enumerate(a.location.links):
    weights[k] = calculateLinkWeight(
         a,
         link=e,
         prior_distance=0.0,
         origin_names=[a.location.name],
         step=1,
         time=time,
         debug=debug,
    )

  return chooseFromWeights(weights=weights, linklist=a.location.links)

