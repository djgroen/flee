import os
import sys
import numpy as np
import random
from beartype.typing import List, Optional, Tuple
from dflee.SimulationSettings import SimulationSettings

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
    # E.g. Flood zones have lower scores, camps have higher scores.
    # Location effects like high/low GDP, food security or weather effects could later also alter this score.

    #["ChildrenAvoidHazards", "BoysTakeRisk", "MatchCampEthnicity", "MatchTownEthnicity", "MatchFloodEthnicity"]
    if SimulationSettings.move_rules["ChildrenAvoidHazards"] and agent.age <19:

        if agent.attributes["age"]<19:
            # For children the safety of the destination is more important than for adults.
            base = base*base
        if SimulationSettings.move_rules["BoysTakeRisk"]:
            if agent.attributes["gender"]=="male" and agent.attributes["age"]>14:
                # Hypothesis that perceived safety does not affect routing decisions for teenage boys.
                base = 1 

    if SimulationSettings.move_rules["StayCloseToHome"]:
        power_factor = SimulationSettings.move_rules["HomeDistancePower"]
        base *= 1.0/(max(1.0,link.endpoint.getDistance(agent.location))**power_factor)

    if link.endpoint.camp is True:
        if SimulationSettings.move_rules["MatchCampEthnicity"]:
            base *= (spawning.getAttributeRatio(link.endpoint, "ethnicity") * 10.0)
    elif link.endpoint.flood > 0.0:
        if SimulationSettings.move_rules["MatchFloodEthnicity"]:
            base *= (spawning.getAttributeRatio(link.endpoint, "ethnicity") * 10.0)
        if SimulationSettings.move_rules["UsePopForLocWeight"]:
            base *= min(1.0,link.endpoint.pop)**float(SimulationSettings.move_rules["PopPowerForLocWeight"])
    else:
        if SimulationSettings.move_rules["MatchTownEthnicity"]:
            base *= (spawning.getAttributeRatio(link.endpoint, "ethnicity") * 10.0)
        if SimulationSettings.move_rules["UsePopForLocWeight"]:
            base *= min(1.0,link.endpoint.pop)**float(SimulationSettings.move_rules["PopPowerForLocWeight"])

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

    nearly_full_occ = SimulationSettings.move_rules["CapacityBuffer"]  # occupancy rate to be considered nearly full.
    # full occupancy limit (should be equal to self.capacity).

    if location.capacity < 1:
        return 1.0

    if location.numAgents <= nearly_full_occ * location.capacity:
        return 1.0

    if location.numAgents >= 1.0 * location.capacity:
        return 0.0

    # should be a number equal in range [0 to 0.1*self.numAgents].
    residual = location.numAgents - (nearly_full_occ * location.capacity)

    # Calculate the residual weighting factor, when pop is between 0.9 and
    # 1.0 of capacity (with default settings).
    weight = 1.0 - (residual / (location.capacity * (1.0 - nearly_full_occ)))

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
) -> Tuple[List[float],List[List[str]]]:
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


  weights = []
  routes = []
  if link.endpoint.marker is False:

    # Core formula for calculating link weight  
    weight = (float(getEndPointScore(agent=agent, link=link)) / float(SimulationSettings.move_rules["Softening"] + link.get_distance() + prior_distance)**SimulationSettings.move_rules["DistancePower"]) * getCapMultiplier(link.endpoint, numOnLink=int(link.numAgents))

    #print(weight, float(getEndPointScore(agent=agent, link=link)))

    weights = [weight]
    routes = [origin_names + [link.endpoint.name]]
  else:
    step -= 1


  if SimulationSettings.move_rules["AwarenessLevel"] > step:
    # Traverse the tree one step further.
    for lel in link.endpoint.links:

      proposed_route = origin_names + [link.endpoint.name, lel.endpoint.name]
      #print("Proposed route:", proposed_route, routes)

      if lel.endpoint.name in origin_names:
        #print("Looped endpoint:", link.endpoint.name, lel.endpoint.name, origin_names)
        # Link points back to an origin, so ignore.
        pass
        
      # Markers are ignored in the pathfinding, 
      # so the step variable doesn't increment.
      # Branch above will prevent (infinite) loops from occurring.
      else:
        wgt, rts = calculateLinkWeight(agent=agent,
              link=lel,
              prior_distance=prior_distance + link.get_distance(),
              origin_names=origin_names + [link.endpoint.name],
              step=step + 1,
              time=time,
              debug=debug,
              )
        weights = weights + wgt
        routes = routes + rts
        #print("Endpoint:", link.endpoint.name, lel.endpoint.name, lel.endpoint.marker, weights, routes)

  if debug:
    print("step {}, total weight returned {}, routes {}".format(step, weights, routes), file=sys.stderr)
  return weights, routes

# Add origin steps, next to origin names to check like for like correctly?
# Or make origin_names data structure encapsulated in recursion.


@check_args_type
def normalizeWeights(weights: List[float]) -> List[float]:
  """
  Summary

  Args:
    weights (List[float]): Description

  Returns:
    list: Description
  """

  if np.sum(weights) > 0.0:
    weights = [x/float(sum(weights)) for x in weights]
    #weights = weights.tolist()
  else:  # if all have zero weight, then we do equal weighting
    weights = [(x+1)/float(len(weights)) for x in weights]
    

  return weights



@check_args_type
def chooseFromWeights(weights, routes):
  """
  Summary

  Args:
    weights (List[float]): Weights for each route
    routes (List[List[str]]]): List of possible routes

  Returns:
    float: Description
  """
  if len(weights) == 0:
    return None

  weights = normalizeWeights(weights=weights)
  result = random.choices(routes, weights=weights)
  return result[0]


@check_args_type
def selectRoute(a, time: int, debug: bool = False, return_all_routes: bool = False):
  """
  Summary

  Args:
  a: Agent
  time (int): Description
  debug (bool, optional): Description

  Returns:
  int: Description
  """
  weights = []
  routes = []

  if SimulationSettings.move_rules["AwarenessLevel"] == 0:
    linklen = len(a.location.links)
    return [np.random.randint(0, linklen)]

  for k, e in enumerate(a.location.links):
    wgt, rts = calculateLinkWeight(
         a,
         link=e,
         prior_distance=0.0,
         origin_names=[a.location.name],
         step=1,
         time=time,
         debug=debug,
    )

    weights = weights + wgt
    routes = routes + rts

  if return_all_routes is True:
    return weights, routes
  if debug is True:
    print("selectRoute: ",routes, weights, file=sys.stderr)

  #Last step: delete origin from suggested routes.
  for i in range(0, len(routes)):
    routes[i] = routes[i][1:]

  #print(weights, routes)
  route = chooseFromWeights(weights=weights, routes=routes)
  #print("route chosen:", route)

  return route

