import os
import sys
import numpy as np
import random
from beartype.typing import List, Optional, Tuple
from flee.SimulationSettings import SimulationSettings

if os.getenv("FLEE_TYPE_CHECK") is not None and os.environ["FLEE_TYPE_CHECK"].lower() == "true":
    from beartype import beartype as check_args_type
else:
    def check_args_type(func):
        return func



@check_args_type
def getLocationCrawlEndPointScore(agent, link, time) -> float:
    """
    Summary:
        Calculates the score for a given endpoint.
        This score is used to determine the probability of an agent moving to a given location.

    Args:
        agent (Person): agent making the decision
        link (Link): link to the endpoint
        time (int): current time step

    Returns:
        base (float): score for the endpoint
    """
    #print(link.endpoint.name, link.endpoint.scores)
    base = agent.getBaseEndPointScore(link) # called externally because serial and parallel implementations differ.

    # The base score is derived from the perceived level of safety and security.
    # E.g. Conflict zones have lower scores, camps have higher scores.
    # Location effects like high/low GDP, food security or weather effects could later also alter this score.

    # DFlee Flood Location Weight implementation
    if SimulationSettings.move_rules["FloodRulesEnabled"] is True:
        #Get the current flood level of the endpoint, if flood level not set in flood_level.csv then default to zero
        flood_level = link.endpoint.attributes.get("flood_level",0)
        #print("Link:", link.endpoint.name, link.endpoint.attributes, file=sys.stderr)
        if flood_level > 0:
            #set the base equal to the flood location weight
            base *= float(SimulationSettings.move_rules["FloodLocWeights"][flood_level])
            #otherwise base score is unaffected by flooding

    return base


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
  Summary:
      Calculates Link Weights recursively based on awareness level.
      Loops are avoided.

  Args:
      a: agent  
      link (Link): The link to calculate the weight for.
      prior_distance (float): The distance travelled so far.
      origin_names (List[str]): The names of the locations that have been visited so far.
      step (int): The number of steps taken so far.
      time (int): The current time. 
      debug (bool, optional): Whether to print debug information. Defaults to False. 

  Returns:
      Tuple[List[float],List[List[str]]]: A tuple containing the weights and routes.
  """

  #if location_is_marker is True: #marker locations should not create a branch.
  weights = []
  routes = []
  if link.endpoint.marker is False:

    # Core formula for calculating link weight  
    weight = (float(SimulationSettings.move_rules["WeightSoftening"] + (float(getEndPointScore(agent=agent, link=link, time=time)))) / float(SimulationSettings.move_rules["DistanceSoftening"] + link.get_distance() + prior_distance)**SimulationSettings.move_rules["DistancePower"]) * getCapMultiplier(link.endpoint, numOnLink=int(link.numAgents))

    #print(weight, float(getEndPointScore(agent=agent, link=link)))
    weight = weight**SimulationSettings.move_rules["WeightPower"]

    weights = [weight]
    routes = [origin_names + [link.endpoint.name]]
  else:
    step -= 1


  #print("Endpoint:", link.endpoint.name, weights, routes, origin_names, step)

  if SimulationSettings.move_rules["AwarenessLevel"] > step:
    # Traverse the tree one step further.
    for lel in link.endpoint.links:

      #proposed route is defined as: origin_names + [link.endpoint.name, lel.endpoint.name]

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


def check_routes(weights, routes, label):
    if len(weights) == 0 or len(routes) == 0:
        print(f"ERROR: Pruning to empty tree at {label}, W:{len(weights)} R:{len(routes)}", file=sys.stderr)
    if sum(weights) == 0:
        print(f"ERROR: Pruning to empty weight sum at {label}", file=sys.stderr)
    if len(weights) != len(routes):
        print(f"ERROR: Pruning to broken tree at {label}, W:{len(weights)} R:{len(routes)}", file=sys.stderr)


def pruneRoutes(weights, routes):

    #check_routes(weights, routes, "START")

    threshold = SimulationSettings.move_rules["PruningThreshold"]
    if threshold < 1.001:
        #check_routes(weights, routes, "LOTHRESHOLD")
        return weights, routes

    min_weight_threshold = max(weights) / threshold
    i = 0
    while i < len(weights):
        if weights[i] < min_weight_threshold:
            weights.remove(weights[i])
            routes.remove(routes[i])
            i -= 1
        i += 1

    #check_routes(weights, routes, "END")
    return weights, routes


@check_args_type
def generateLocationRoutes(l: Location, time: int, debug: bool = False, return_all_routes: bool = False):
  """
  Summary:
      Selects a route for an agent to move to.

  Args:
    l: Location
    time (int): Current time
    debug (bool, optional): Whether to print debug information. Defaults to False.

  Returns:
      int: Index of the chosen route
  """
  l.routes = {}

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

  weights, routes = pruneRoutes(weights, routes)

  #print(weights, routes)
  route = chooseFromWeights(weights=weights, routes=routes)
  #print("route chosen:", route)

  return route

