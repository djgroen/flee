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
def getEndPointScore(agent, endpoint, time) -> float:
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
    #print(endpoint.name, endpoint.scores)
    base = endpoint.getScore(1)

    # The base score is derived from the perceived level of safety and security.
    # E.g. Conflict zones have lower scores, camps have higher scores.
    # Location effects like high/low GDP, food security or weather effects could later also alter this score.

    #["ChildrenAvoidHazards", "BoysTakeRisk", "MatchCampEthnicity", "MatchTownEthnicity", "MatchConflictEthnicity"]
    if SimulationSettings.move_rules["ChildrenAvoidHazards"]:
        if agent.attributes["age"]<19:
            # For children the safety of the destination is more important than for adults.
            base = base*base
        if SimulationSettings.move_rules["BoysTakeRisk"]:
            if agent.attributes["gender"]=="male" and agent.attributes["age"]>14:
                # Hypothesis that perceived safety does not affect routing decisions for teenage boys.
                base = 1 


    if SimulationSettings.move_rules["StayCloseToHome"]:
        power_factor = SimulationSettings.move_rules["HomeDistancePower"]
        base *= 1.0/(max(1.0,endpoint.calculateDistance(agent.location))**power_factor)

    # DFlee Flood Location Weight implementation
    if SimulationSettings.move_rules["FloodRulesEnabled"] is True:
        #Get the current flood level of the endpoint, if flood level not set in flood_level.csv then default to zero
        flood_level = endpoint.attributes.get("flood_level",0)
        #print("Link:", endpoint.name, endpoint.attributes, file=sys.stderr)
        if flood_level > 0:
            #set the base equal to the flood location weight
            base *= float(SimulationSettings.move_rules["FloodLocWeights"][flood_level])
            #otherwise base score is unaffected by flooding


        #Flooding Forecaster Location Weight Implementation:
        if SimulationSettings.move_rules["FloodForecaster"] is True:

            #Get the forecast timescale e.g. 5 day weather forecast
            forecast_timescale = SimulationSettings.move_rules["FloodForecasterTimescale"]

            #Get the forecast length e.g. only know the forecast until day 7
            forecast_end_time = SimulationSettings.move_rules["FloodForecasterEndTime"] 

            # If there is a forecast timescale and endtime are set
            # If forecast_timescale is greater than 1 and the current time step is less than the forecast end time
            if forecast_timescale is not None:
              if forecast_end_time is not None:
                if (forecast_timescale > 1.0) and (time <= forecast_end_time): 
              
                  #Set the base forecast value
                  flood_forecast_base = 0.0 #no forecast, no flooding 

                  #Get the agents awareness level of the flood forecast
                  #Weighting of each awareness level defined in simsetting.yml
                  #Fraction of population with each level of flood awareness defined in demographics_floodawareness.csv 
                  #Awareness can be used as a proxy for ability to adapt to forecasted flooding.
                  #For example, low awareness will down weight the importance of the forecast or reduce the impact the forecast has on the 
                  # agents decision making process. 
                  agent_awareness_weight = float(SimulationSettings.move_rules["FloodAwarenessWeights"][int(agent.attributes["floodawareness"])])

                  #Forecast loop: iterate over the location flood level weights for the forecast timescale
                  for x in range(1, forecast_timescale + 1): #iterates over the 5 day forecast, ignoring the current day

                      #the day of the forcast we're considering 
                      forecast_day = time + x 

                      #If the simulation length is less than the end of the forecast, then the forecast will be shorter
                      if forecast_day >= forecast_end_time:
                          #set the forecast day to the end of the simulation
                          forecast_day = forecast_end_time #same as time + x
                    
                      #get the forecast flood level for location on the day we're considering in the for loop
                      forecast_flood_level = endpoint.attributes.get("forecast_flood_levels",0)[forecast_day]

                      # if it's not zero, then we need to modify the base forecast value, otherwise leave the base as it will zero.
                      if forecast_flood_level > 0.0: 
                        #get the endpoint locations current flood level weight based on that flood level.
                        forecast_flood_level_weight = float(SimulationSettings.move_rules["FloodLocWeights"][forecast_flood_level]) 
                        
                        #get the current flood forecaster weight e.g. how important the current day is in the forecast
                        flood_forecaster_weight = float(SimulationSettings.move_rules["FloodForecasterWeights"][forecast_day])
                      
                        #modify the flood_forecast_base using the flood level on the current day and the imporatance of the current day in the forecast loop
                        flood_forecast_base += forecast_flood_level_weight * flood_forecaster_weight

                      #break the loop if we've reached the end of the forecast data 
                      if forecast_day == forecast_end_time:
                        break
                    
                  #the flood_forecast_base now represents the total weight of the flooding during the forecast for the endpoint location,
                  # this needed to be divided by the total number of days in the forecast to get the average weight based on the severity and relative imporatance of the forecasted days
                  flood_forecast_base *= float(flood_forecast_base/forecast_timescale)

                  #down weight the overall importance of the flood forecast on the base depending on the agents awareness weighting
                  #currently using a simple down weighting, but may want lower awareness agents to only respond to high flood levels 
                  # or shorter forecast timescales.
                  flood_forecast_base *= float(agent_awareness_weight) 

                  # Make the flood_forecast_base effect the actual base score
                  base *= flood_forecast_base  
                    
              else:
                  print("WARNING: flood_forecaster_endtime is not set in simsetting.yml", file=sys.stderr)
            else:
                print("WARNING: flood_forecaster_timescale is not set in simsetting.yml", file=sys.stderr)


    if endpoint.camp is True:
        if SimulationSettings.move_rules["MatchCampEthnicity"]:
            base *= (spawning.getAttributeRatio(endpoint, agent.attributes["ethnicity"]) * 10.0)
    elif endpoint.conflict > 0.0:
        if SimulationSettings.move_rules["MatchConflictEthnicity"]:
            base *= (spawning.getAttributeRatio(endpoint, agent.attributes["ethnicity"]) * 10.0)
        if SimulationSettings.move_rules["UsePopForLocWeight"]:
            base *= min(1.0,endpoint.pop)**float(SimulationSettings.move_rules["PopPowerForLocWeight"])
    else:
        if SimulationSettings.move_rules["MatchTownEthnicity"]:
            base *= (spawning.getAttributeRatio(endpoint, agent.attributes["ethnicity"]) * 10.0)
        if SimulationSettings.move_rules["UsePopForLocWeight"]:
            base *= min(1.0,endpoint.pop)**float(SimulationSettings.move_rules["PopPowerForLocWeight"])

    return base


@check_args_type
def getCapMultiplier(location, numOnLink: int) -> float:
    """
    Summary:
        Checks whether a given location has reached full capacity
        or is close to it.

    Args:
        location (Location): location to check
        numOnLink (int): number of agents on the link

    Returns:
        float: returns a value between 0.0 and 1.0, where:
        - 1.0 if occupancy < nearly_full_occ (0.9).
        - 0.0 if occupancy >= 1.0.
        - a value in between for intermediate values
    """

    nearly_full_occ = SimulationSettings.move_rules["CapacityBuffer"]  # occupancy rate to be considered nearly full.
    cap_scale = SimulationSettings.move_rules["CapacityScaling"]  # Multiplier rate on capacity to loosen the assumption.
    
    # full occupancy limit (should be equal to self.capacity).
    cap = location.capacity * float(cap_scale)    

    if cap < 1:
        return 1.0

    if location.numAgents <= nearly_full_occ * cap:
        return 1.0

    if location.numAgents >= 1.0 * cap:
        return 0.0

    # should be a number equal in range [0 to 0.1*self.numAgents].
    residual = location.numAgents - (nearly_full_occ * cap)

    # Calculate the residual weighting factor, when pop is between 0.9 and
    # 1.0 of capacity (with default settings).
    weight = 1.0 - (residual / (cap * (1.0 - nearly_full_occ)))

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
    weight = (float(SimulationSettings.move_rules["WeightSoftening"] + (float(getEndPointScore(agent=agent, endpoint=link.endpoint, time=time)))) / float(SimulationSettings.move_rules["DistanceSoftening"] + link.get_distance() + prior_distance)**SimulationSettings.move_rules["DistancePower"]) * getCapMultiplier(link.endpoint, numOnLink=int(link.numAgents))

    #print(weight, float(getEndPointScore(agent=agent, endpoint=link.endpoint)))
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

# Add origin steps, next to origin names to check like for like correctly?
# Or make origin_names data structure encapsulated in recursion.

@check_args_type
def normalizeWeights(weights: List[float]) -> List[float]:
  """
  Summary:
    Normalizes a list of weights.

  Args:
    weights (List[float]): List of weights

  Returns:
    list: Normalized list of weights
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
  Summary:
      Chooses a route from a list of routes based on a list of weights.

  Args:
      weights (List[float]): Weights for each route
      routes (List[List[str]]]): List of possible routes

  Returns:
      float: The chosen route index   
  """
  if len(weights) == 0:
    return None

  weights = normalizeWeights(weights=weights)
  result = random.choices(routes, weights=weights)
  return result[0]


@check_args_type
def calculateMoveChance(a, ForceTownMove: bool, time) -> Tuple[float, bool]:
    """
    Summary:
        Calculates the probability that an agent will move this step.

    Args:
        a: Agent to calculate move chance for.
        ForceTownMove: Whether to force agents to move through regular town. If True, agents will always move.
        time (int): Current time step.

    Returns:
        movechance (float): Probability that agent will move this step. 
        system2_active: Whether System 2 thinking is active.
    """
    system2_active = False

    if SimulationSettings.move_rules["TwoSystemDecisionMaking"] is True:
        # System 2 Activation Logic
        conflict_triggered = a.location.conflict > 0.6
        in_recovery = a.location.time_of_conflict >= 0 and \
                  time >= a.location.time_of_conflict + 10
        connected = a.attributes.get("connections", 0) >= 3
   
        if conflict_triggered and in_recovery and connected:
            system2_active = True
        
            # Safe access to location name for debugging
            location_name = getattr(a.location, 'name', 'UnknownLocation')
            print(f"System 2 activated: Agent at {location_name} (connections: {a.attributes.get('connections', 0)}) at time {time}", file=sys.stderr)

            provisional_route = selectRoute(a, time)
            if len(provisional_route) == 0:
                return 0.0, True  # suppress move if no viable route
            else:
                a.attributes["_temp_route"] = provisional_route
            # For System 2, always return 1.0 (100% chance to initiate movement decision)
            return 1.0, system2_active

    # If System 2 is not active, calculate standard System 1 move chance
    if a.location.town and ForceTownMove:  # called through evolve
        return 1.0, system2_active
    else:  # called first time in loop
        movechance = a.location.movechance

        movechance *= (float(max(a.location.pop, a.location.capacity)) / SimulationSettings.move_rules["MovechancePopBase"])**SimulationSettings.move_rules["MovechancePopScaleFactor"]

    # flood
    # DFlee Flood Location Movechance implementation:
    if SimulationSettings.move_rules["FloodRulesEnabled"] is True:
        #Get the current flood level of the agents location, if flood level not set in flood_level.csv then default to zero
        flood_level = a.location.attributes.get("flood_level",0)
        
        if flood_level > 0.0:
            #set the base equal to the flood location weight
            movechance = float(SimulationSettings.move_rules["FloodMovechances"][flood_level])
            #otherwise base movechance is unaffected by flooding
            #print(f"flood_level: {flood_level}, movechance: {movechance}")

        #Flooding Forecaster Location Weight Implementation:
        if SimulationSettings.move_rules["FloodForecaster"] is True:

            #Get the forecast timescale e.g. 5 day weather forecast
            forecast_timescale = SimulationSettings.move_rules["FloodForecasterTimescale"]

            #Get the forecast length e.g. only know the forecast until day 7
            forecast_end_time = SimulationSettings.move_rules["FloodForecasterEndTime"] 

            # If there is a forecast timescale and endtime are set
            # If forecast_timescale is greater than 1 and the current time step is less than the forecast end time
            if forecast_timescale is None:
                print("ERROR: flood_forecaster_timescale is not set in simsetting.yml", file=sys.stderr)
                sys.exit()
            if forecast_end_time is None:
                print("ERROR: flood_forecaster_endtime is not set in simsetting.yml", file=sys.stderr)
                sys.exit()


            if (forecast_timescale > 1.0) and (time <= forecast_end_time): 
                
                #Set the base forecast value
                flood_forecast_base = 0.0 #no forecast, no flooding 

                #Set the default movechance value
                flood_forecast_movechance = 0.0 #no forecast, no flooding

                #Get the agents awareness level of the flood forecast
                #Weighting of each awareness level defined in simsetting.yml
                #Fraction of population with each level of flood awareness defined in demographics_floodawareness.csv 
                #Awareness can be used as a proxy for ability to adapt to forecasted flooding.
                #For example, low awareness will down weight the importance of the forecast or reduce the impact the forecast has on the 
                # agents decision making process. 
                agent_awareness_weight = float(SimulationSettings.move_rules["FloodAwarenessWeights"][int(a.attributes["floodawareness"])])
         

                #Forecast loop: iterate over the location flood level weights for the forecast timescale
                for x in range(1, forecast_timescale + 1): #iterates over the 5 day forecast, ignoring the current day

                    #the day of the forcast we're considering 
                    forecast_day = time + x 

                    #If the simulation length is less than the end of the forecast, then the forecast will be shorter
                    if forecast_day >= forecast_end_time:
                        #set the forecast day to the end of the simulation
                        forecast_day = forecast_end_time #same as time + x
                  
                    #get the forecast flood level for location on the day we're considering in the for loop
                    forecast_flood_level = int(a.location.attributes.get("forecast_flood_levels",0)[forecast_day])

                    # if it's not zero, then we need to modify the base forecast value, otherwise leave the base as it will zero.
                    if forecast_flood_level > 0.0: 
                        #get the endpoint locations current flood level weight based on that flood level.
                        forecast_flood_level_weight = float(SimulationSettings.move_rules["FloodLocWeights"][forecast_flood_level]) 
                      
                        #get the current flood forecaster weight e.g. how important the current day is in the forecast
                        flood_forecaster_weight = float(SimulationSettings.move_rules["FloodForecasterWeights"][forecast_day])
                    
                        #modify the flood_forecast_base using the flood level on the current day and the imporatance of the current day in the forecast loop
                        flood_forecast_base += forecast_flood_level_weight * flood_forecaster_weight

                    #break the loop if we've reached the end of the forecast data 
                    if forecast_day == forecast_end_time:
                        break

                #the flood_forecast_base now represents the total weight of the flooding during the forecast for the endpoint location,
                # this needed to be divided by the total number of days in the forecast to get the average weight based on the severity and relative imporatance of the forecasted days
                flood_forecast_movechance = float(flood_forecast_base/forecast_timescale)

                #down weight the overall importance of the flood forecast on the base depending on the agents awareness weighting
                #currently using a simple down weighting, but may want lower awareness agents to only respond to high flood levels 
                # or shorter forecast timescales.
                flood_forecast_movechance *= float(agent_awareness_weight) 

                # Make the flood_forecast_base effect the actual base score
                movechance *= flood_forecast_movechance  
                  
    return movechance, system2_active 


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
def selectRoute(a, time: int, debug: bool = False, return_all_routes: bool = False, system2_active: bool = False):
  """
  Summary:
      Selects a route for an agent to move to.
  Args:
    a: Agent
    time (int): Current time
    debug (bool, optional): Whether to print debug information. Defaults to False.
    return_all_routes (bool, optional): Whether to return all routes. Defaults to False.
    system2_active (bool, optional): Whether the agent's System 2 thinking is active. Defaults to False.
  Returns:
      int: Index of the chosen route
  """
  weights = []
  routes = []
  
  if SimulationSettings.move_rules["AwarenessLevel"] == 0:
      linklen = len(a.location.links)
      return [np.random.randint(0, linklen)]

  # Store original parameters for System 2 modification
  original_params = {}
  if SimulationSettings.move_rules["TwoSystemDecisionMaking"] and system2_active:
      # Store original values
      original_params['awareness_level'] = SimulationSettings.move_rules["AwarenessLevel"]
      original_params['weight_softening'] = SimulationSettings.move_rules["WeightSoftening"]
      original_params['distance_power'] = SimulationSettings.move_rules["DistancePower"]
      original_params['pruning_threshold'] = SimulationSettings.move_rules["PruningThreshold"]
      
      # Set System 2 parameters (more deliberative thinking)
      SimulationSettings.move_rules["AwarenessLevel"] = min(3, original_params['awareness_level'] + 1)  # Higher awareness
      SimulationSettings.move_rules["WeightSoftening"] = 0.0  # Less randomness, more deliberate
      SimulationSettings.move_rules["DistancePower"] = 1.2  # Slightly more distance-sensitive
      SimulationSettings.move_rules["PruningThreshold"] = 1.5  # Less aggressive pruning (consider more options)

  if SimulationSettings.move_rules["FixedRoutes"] is True:
      for l in a.location.routes.keys():
          weights = weights + [a.location.routes[l][0] * getEndPointScore(a, a.location.routes[l][2], time)]
          routes = routes + [a.location.routes[l][1]]
      #print("FixedRoute Weights", a.location.name, weights, routes, file=sys.stderr)
  else:
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

      # Apply pruning (now influenced by System 2 parameters if active)
      weights, routes = pruneRoutes(weights, routes)
          
  if SimulationSettings.move_rules["TwoSystemDecisionMaking"] and system2_active:
      # Always restore original parameters if they were modified
      SimulationSettings.move_rules["AwarenessLevel"] = original_params['awareness_level']
      SimulationSettings.move_rules["WeightSoftening"] = original_params['weight_softening']
      SimulationSettings.move_rules["DistancePower"] = original_params['distance_power']
      SimulationSettings.move_rules["PruningThreshold"] = original_params['pruning_threshold']

  route = chooseFromWeights(weights=weights, routes=routes)
  
  if route == None:
      print("WARNING: Empty route (None type) generated in selectRoute.", file=sys.stderr)
      print(f"Location: {a.location.name}, {weights}, {routes}", file=sys.stderr)
      return []
  elif len(route) == 0:
      print(f"ERROR: Empty route {route} generated in selectRoute.", file=sys.stderr)
      sys.exit()
  
  return route

