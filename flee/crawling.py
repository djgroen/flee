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
def _addLocationRoute(
  source_loc,
  loc,
  link,
  prior_distance: float,
  origin_names: List[str],
  time: int,
) -> None:
    # Core formula for calculating link weight  
    weight = (float(SimulationSettings.move_rules["WeightSoftening"] + (float(getLocationCrawlEndPointScore(link=link, time=time)))) / float(SimulationSettings.move_rules["DistanceSoftening"] + link.get_distance() + prior_distance)**SimulationSettings.move_rules["DistancePower"])

    #print(weight, float(getEndPointScore(agent=agent, link=link)))
    weight = weight**SimulationSettings.move_rules["WeightPower"]

    #print("Adding loc route:", origin_names[1:], link.endpoint.name, file=sys.stderr)
    if weight > loc.routes.get(link.endpoint.name, [0,None])[0]:
        source_loc.routes[link.endpoint.name] = [weight, origin_names[1:] + [link.endpoint.name], link.endpoint]


@check_args_type
def _addMajorRouteToLocation(
  source_loc, 
  route,
  time,
) -> None:
    prior_distance = 0.0
    routing_step = 0
    current_loc = source_loc
    selected_endpoint = None
    while routing_step < len(route):
        #print(f"{current_loc.name}: {len(current_loc.links)}", file=sys.stderr)
        for link in current_loc.links:
            #print(f"{current_loc.name}: {link.endpoint.name}={route[routing_step]}? Full route = {route}, routing_step {routing_step}.", file=sys.stderr)
            if link.endpoint.name == route[routing_step]:
                if routing_step == len(route)-1:
                    _addLocationRoute(source_loc, current_loc, link, prior_distance, route[:-1], time)
                    return
                prior_distance += link.get_distance()
                selected_endpoint = link.endpoint
                break
        if selected_endpoint is None:
            print(f"ERROR: major route {route} cannot be resolved at step {routing_step}. No connection between {current_loc.name} and {route[routing_step]}.", file=sys.stderr)
            for link in current_loc.links:
                print(f"Current location {current_loc.name} has a link to {link.endpoint.name}.", file=sys.stderr)
            sys.exit()
        else:
            routing_step += 1
            current_loc = selected_endpoint
            selected_endpoint = None

    print(f"ERROR: major route {route} cannot be resolved at step {routing_step}. No connection between {current_loc.name} and {link.endpoint.name}.", file=sys.stderr)
    sys.exit()



@check_args_type
def calculateLocCrawlLinkWeight(
  source_loc,
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

      _addLocationRoute(source_loc, loc, link, prior_distance, origin_names, time)

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
              calculateLocCrawlLinkWeight(
                    source_loc=source_loc,
                    loc=loc,
                    link=lel,
                    prior_distance=prior_distance + link.get_distance(),
                    origin_names=origin_names + [link.endpoint.name],
                    step=step + 1,
                    time=time,
                    )


@check_args_type
def insertMajorRoutesForLocation(
  source_loc, 
  l, 
  route_to_l, 
  dest_list, 
  time: int
) -> None:
    """
    Inserts major_routes into the route list for a given location.
    """
    dest_names = [source_loc.name]
    for d in dest_list:
        dest_names.append(d.name)

    #print(f"major route loop: {l.name}, {l.major_routes}, {dest_names}", file=sys.stderr)
    for mr in l.major_routes:
        #print(f"MR contains: {mr}", file=sys.stderr)
        if mr[-1] not in dest_names:
            route = route_to_l + mr
            #print(f"Adding route for {source_loc.name}: {route}, {route_to_l}, {mr}", file=sys.stderr)

            _addMajorRouteToLocation(source_loc, route, time)
    #print(f"major route loop done.", file=sys.stderr)


@check_args_type
def compileDestList(l):
    """
    Makes a list of destinations that are reachable through regular routes
    from the location, given the AwarenessLevel.
    """
    dest_list = []
    for route_name in l.routes:
        #print(l.routes, file=sys.stderr)
        if l.routes[route_name][1][-1] not in dest_list:
            dest_list.append(l.routes[route_name][2]) # dest_list contains Location objects.

    return dest_list


@check_args_type
def insertAllMajorRoutesAtLocation(l, time: int):
    # get list of destination locations (l.routes[name][2]) 
    # get list of destination location names keys of (l.routes)
    # get list of destination location routes (l.routes[name][1]) 
    dest_list = compileDestList(l)

    # Storing current route names before major loop additions, because l.routes
    # itself will be expanded with major routes during the iterations. 
    route_names = list(l.routes.keys()).copy()

    # Check for major routes from current location.
    if len(l.major_routes) > 0:
        #print(f"Adding major route in curloc: {l.name}, {l.routes}, {l.major_routes}.", file=sys.stderr)
        print(f"Adding major route in curloc {l.name}.", file=sys.stderr)
        print(f"{l.major_routes}", file=sys.stderr)
        insertMajorRoutesForLocation(l, l, [], dest_list, time)

    # Check for major routes from all other locations reachable
    # with regular routes.

    # Main loop over regular routes.
    for route_name in route_names:
        loc = l.routes[route_name][2]
        if len(loc.major_routes) > 0:
            #print(l.routes, file=sys.stderr)
            #print(f"Location {l.name}, Major route hub: {loc.name}, Route to hub: {l.routes[route_name][1]}, Major route #1 {loc.major_routes[0]}", file=sys.stderr)
            insertMajorRoutesForLocation(l, loc, l.routes[route_name][1], dest_list, time)



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
         l,
         link=e,
         prior_distance=0.0,
         origin_names=[l.name],
         step=1,
         time=time,
    )

  insertAllMajorRoutesAtLocation(l, time)

  #print(f"Generated {len(l.routes)} routes for {l.name} at time {time}.", file=sys.stderr)
  return l.routes

