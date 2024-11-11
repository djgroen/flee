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

# File for generating routes to interconnect different locations using pregenerated routes.
# To be used for alternative algorithms for agent movement selection.

@check_args_type
def getLocationCrawlEndPointScore(link, time) -> float:
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
    base = link.getBaseEndPointScore() # called externally because serial and parallel implementations differ.

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
def calculateLocCrawlLinkWeight(
  loc,
  link,
  prior_distance: float,
  origin_names: List[str],
  step: int,
  time: int,
) -> None:
  """
  Summary:
      Calculates Link Weights recursively based on awareness level.
      Loops are avoided.

  Args:
      loc: start location  
      link (Link): The link to calculate the weight for.
      prior_distance (float): The distance travelled so far.
      origin_names (List[str]): The names of the locations that have been visited so far.
      step (int): The number of steps taken so far.
      time (int): The current time. 
      debug (bool, optional): Whether to print debug information. Defaults to False. 

  Returns:
      None (routes are stored in loc.routes)
  """

  if link.endpoint.marker is False:

    # Core formula for calculating link weight  
    weight = (float(SimulationSettings.move_rules["WeightSoftening"] + (float(getLocationCrawlEndPointScore(link=link, time=time)))) / float(SimulationSettings.move_rules["DistanceSoftening"] + link.get_distance() + prior_distance)**SimulationSettings.move_rules["DistancePower"])

    #print(weight, float(getEndPointScore(agent=agent, link=link)))
    weight = weight**SimulationSettings.move_rules["WeightPower"]

    if weight > loc.routes.get(link.endpoint.name, [0,None])[0]:
        loc.routes[link.endpoint.name] = [weight, origin_names + [link.endpoint.name], link.endpoint]


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
        calculateLocCrawlLinkWeight(loc=loc,
              link=lel,
              prior_distance=prior_distance + link.get_distance(),
              origin_names=origin_names + [link.endpoint.name],
              step=step + 1,
              time=time,
              )


@check_args_type
def insertMajorRoutesForLocation(source_loc, l, route_to_l, dest_list):
    """
    Inserts major_routes into the route list for a given location.
    """
    for ml in l.major_routes:
        if ml[-1] not in dest_list:
            source_loc.routes.append([route_to_l] + [ml])


@check_args_type
def compileDestList(l):
    """
    Makes a list of destinations that are reachable through regular routes
    from the location, given the AwarenessLevel.
    """
    dest_list = []
    for lr in l.routes:
        if lr[-1] not in dest_list:
            dest_list.append(lr[-1])

    return dest_list


@check_args_type
def insertMajorRoutes(l):
    # get list of destination locations (l.routes[name][2]) 
    # get list of destination location names keys of (l.routes)
    # get list of destination location routes (l.routes[name][1]) 
    dest_list = compileDestList(l)

    # Check for major routes from current location.
    if len(l.major_routes) > 0:
        insertMajorRoutesForLocation(l, l, [], dest_list)

    # Check for major routes from all other locations reachable
    # with regular routes.
    for route_name in l.routes:
        loc = l.routes[route_name][2]
        if len(loc.major_routes) > 0:
            insertMajorRoutesForLocation(l, loc, l.routes[route_name][1], dest_list)



@check_args_type
def generateLocationRoutes(l, time: int, debug: bool = False):
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
  if l.marker:
      return {}

  l.routes = {}

  if SimulationSettings.move_rules["AwarenessLevel"] == 0:
    linklen = len(l.links)
    return [np.random.randint(0, linklen)]

  for k, e in enumerate(l.links):
    calculateLocCrawlLinkWeight(
         l,
         link=e,
         prior_distance=0.0,
         origin_names=[l.name],
         step=1,
         time=time,
    )

  insertMajorRoutes(l)

  print(f"Generated {len(l.routes)} routes for {l.name} at time {time}.", file=sys.stderr)
  return l.routes

