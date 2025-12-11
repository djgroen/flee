import os
import sys
import numpy as np
import random
from beartype.typing import List, Optional, Tuple
from flee.SimulationSettings import SimulationSettings
import flee.spawning as spawning
import flee.demographics as demographics

# Import refactored S1/S2 system
try:
    from flee.s1s2_refactored import S1S2Config, calculate_s1s2_move_probability
except ImportError:
    # Fallback if refactored system not available
    S1S2Config = None
    calculate_s1s2_move_probability = None

# Import new 5-parameter S1/S2 model
try:
    from flee.s1s2_model import calculate_move_probability_s1s2, load_s1s2_parameters, validate_parameters
except ImportError:
    # Fallback if 5-parameter model not available
    calculate_move_probability_s1s2 = None
    load_s1s2_parameters = None
    validate_parameters = None

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
        endpoint (Location): endpoint location to score
        time (int): current time step

    Returns:
        base (float): score for the endpoint
    """
    #print(endpoint.name, endpoint.scores)
    base = endpoint.getScore(0)
    
    # Consider shared safety information if available
    if "_safety_info" in agent.attributes:
        safety_info = agent.attributes["_safety_info"]
        if endpoint.name in safety_info:
            location_info = safety_info[endpoint.name]
            
            # Adjust score based on shared conflict information
            shared_conflict = location_info.get('conflict_level', 0)
            if shared_conflict > 0.5:
                base *= 0.5  # Reduce attractiveness of high-conflict areas
            
            # Adjust score based on shared capacity information
            capacity_ratio = location_info.get('capacity_ratio', 0)
            if capacity_ratio > 0.9:
                base *= 0.3  # Heavily penalize overcrowded locations
            elif capacity_ratio > 0.7:
                base *= 0.7  # Moderately penalize crowded locations
            
            # Boost score for camps if they're not overcrowded
            if location_info.get('camp_status', False) and capacity_ratio < 0.8:
                base *= 1.5  # Camps are generally safer destinations

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
            base *= (demographics.get_attribute_ratio(endpoint, agent.attributes["ethnicity"]) * 10.0)
        if SimulationSettings.move_rules["MatchCampReligion"]:
            base *= (demographics.get_attribute_ratio(endpoint, agent.attributes["religion"]) * SimulationSettings.move_rules["ReligionBaseRate"])
    elif endpoint.conflict > 0.0:
        if SimulationSettings.move_rules["MatchConflictEthnicity"]:
            base *= (demographics.get_attribute_ratio(endpoint, agent.attributes["ethnicity"]) * 10.0)
        if SimulationSettings.move_rules["UsePopForLocWeight"]:
            base *= max(1.0,endpoint.pop)**float(SimulationSettings.move_rules["PopPowerForLocWeight"])
    else:
        if SimulationSettings.move_rules["MatchTownEthnicity"]:
            base *= (demographics.get_attribute_ratio(endpoint, agent.attributes["ethnicity"]) * 10.0)
        if SimulationSettings.move_rules["UsePopForLocWeight"]:
            base *= max(1.0,endpoint.pop)**float(SimulationSettings.move_rules["PopPowerForLocWeight"])

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



def calculate_systematic_s2_activation(agent, pressure, base_threshold, time):
    """
    Calculate systematic S2 activation using bounded mathematical model.
    
    NOTE: This is the OLD system. The aligned model uses experience_index
    via calculate_experience_index() and P_S2 = Ψ × Ω.
    
    This function is kept for backward compatibility with the original
    S1/S2 system that doesn't use the parsimonious model.
    """
    import math
    import random
    
    # Base sigmoid activation curve with proper steepness
    k = 6.0  # Steepness parameter (more realistic than 8.0)
    base_prob = 1.0 / (1.0 + math.exp(-k * (pressure - base_threshold)))
    
    # Individual difference modifiers (bounded and realistic)
    # NOTE: Using experience-based factors instead of direct education
    # Education is only a small component (5%) of experience index
    try:
        from flee.s1s2_model import calculate_experience_index
        experience_index = calculate_experience_index(
            prior_displacement=agent.timesteps_since_departure / 30.0,
            local_knowledge=agent.attributes.get('local_knowledge', 0.0),
            conflict_exposure=agent.attributes.get('conflict_exposure', 0.0),
            connections=agent.attributes.get('connections', 0),
            age_factor=agent.attributes.get('age_factor', 0.5),
            education_level=agent.attributes.get('education_level', 0.5)
        )
        # Use experience index for boost (normalized to [0, 1] range)
        experience_boost = min(experience_index / 5.0, 0.05)  # Max 5% boost
    except ImportError:
        # Fallback if experience index not available
        experience_boost = 0.0
    
    stress_tolerance = agent.attributes.get('stress_tolerance', 0.5)
    stress_modifier = stress_tolerance * 0.03  # Max 3% boost
    
    # Social support modifier (bounded)
    connections = agent.attributes.get('connections', 0)  # Start from 0, not 5
    social_support = min(connections * 0.01, 0.05)  # Max 5% boost
    
    # Time-based modifiers (bounded)
    fatigue_penalty = min(time * 0.001, 0.03)  # Max 3% penalty, bounded
    learning_boost = min(time * 0.002, 0.05)   # Max 5% boost, bounded
    
    # Combine all modifiers
    final_prob = base_prob + experience_boost + social_support - fatigue_penalty + learning_boost + stress_modifier
    
    # Ensure probability stays in valid range
    final_prob = max(0.0, min(1.0, final_prob))
    
    # Random activation based on probability
    return random.random() < final_prob


def calculate_s1_move_chance(a, ForceTownMove: bool, time) -> float:
    """Calculate S1 move chance (original logic)."""
    if a.location.town and ForceTownMove:  # called through evolve
        return 1.0
    elif len(a.route) > 0: #If a route with destination is known, the agent will continue to follow it.
        return 1.0
    else:  # called first time in loop
        movechance = a.location.movechance
        movechance *= (float(max(a.location.pop, a.location.capacity)) / SimulationSettings.move_rules["MovechancePopBase"])**SimulationSettings.move_rules["MovechancePopScaleFactor"]
        return movechance


def calculate_move_chance_original(a, ForceTownMove: bool, time) -> Tuple[float, bool]:
    """Original S1/S2 move chance calculation (fallback)."""
    system2_active = False
    
    # Enhanced System 2 Activation Logic with cognitive pressure
    cognitive_pressure = a.calculate_cognitive_pressure(time)
    system2_capable = a.get_system2_capable()
    
    # Systematic S2 activation with continuous probability
    if system2_capable:
        # Get agent's cognitive profile
        profile = a.attributes.get('cognitive_profile', 'balanced')
        base_threshold = a.attributes.get('s2_threshold', 0.5)
        
        # Use systematic continuous activation
        system2_active = calculate_systematic_s2_activation(
            a, cognitive_pressure, base_threshold, time
        )
    
        # Log S2 activation decision
        if system2_active:
            a.log_decision("S2", {
                "cognitive_pressure": cognitive_pressure,
                "threshold": base_threshold,
                "connections": a.attributes.get('connections', 0),
                "location": getattr(a.location, 'name', 'UnknownLocation')
            }, time)
            
            # Safe access to location name for debugging
            location_name = getattr(a.location, 'name', 'UnknownLocation')
            print(f"System 2 activated: Agent at {location_name} (pressure: {cognitive_pressure:.2f}, connections: {a.attributes.get('connections', 0)}) at time {time}", file=sys.stderr)
            print(f"DEBUG: Decision history length: {len(a.decision_history)}", file=sys.stderr)

        # Only pre-calculate route if System 2 is actually activated
        if system2_active:
            # Pre-calculate route for System 2 decision-making
            provisional_route = selectRoute(a, time, system2_active=True)
            if len(provisional_route) == 0:
                return 0.0, True  # suppress move if no viable route
            else:
                a.attributes["_temp_route"] = provisional_route
                
                # Share route information with connected agents
                if a.attributes.get("connections", 0) > 0:
                    import flee
                    # We need to pass the ecosystem, but it's not available here
                    # This will be handled in the evolve method
                    a.attributes["_share_route_info"] = True
                    
            # For System 2, always return 1.0 (100% chance to initiate movement decision)
            return 1.0, system2_active

    # If System 2 is not active, calculate standard System 1 move chance
    if a.location.town and ForceTownMove:  # called through evolve
        return 1.0, system2_active
    elif len(a.route) > 0: #If a route with destination is known, the agent will continue to follow it.
        return 1.0, system2_active
    else:  # called first time in loop
        movechance = a.location.movechance
        movechance *= (float(max(a.location.pop, a.location.capacity)) / SimulationSettings.move_rules["MovechancePopBase"])**SimulationSettings.move_rules["MovechancePopScaleFactor"]
        return movechance, system2_active


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

    if SimulationSettings.move_rules.get("TwoSystemDecisionMaking", False):
        # CRITICAL: Camps have very low movechance (0.001) - respect it regardless of S1/S2
        # This prevents agents from leaving safe zones too frequently
        if a.location.camp or a.location.idpcamp:
            # Preserve current cognitive state, but use camp_movechance (agents don't move)
            # This maintains behavioral continuity: S2 agents stay S2, S1 agents stay S1
            current_s2 = getattr(a, 'cognitive_state', 'S1') == 'S2'
            return a.location.movechance, current_s2
        
        # CRITICAL: High-conflict zones have high movechance (1.0) - respect it regardless of S1/S2
        # This ensures agents always try to leave extreme danger zones (panic response)
        conflict = max(0.0, getattr(a.location, 'conflict', 0.0))
        if conflict > 0.5:  # High conflict threshold
            # Preserve current cognitive state, but use conflict_movechance (agents always try to leave)
            # This maintains behavioral continuity while respecting urgency
            current_s2 = getattr(a, 'cognitive_state', 'S1') == 'S2'
            return a.location.movechance, current_s2
        
        # NEW: Use parsimonious dual-process S1/S2 model if available and enabled
        if calculate_move_probability_s1s2 is not None:
            # Import experience index calculation
            from flee.s1s2_model import calculate_experience_index
            
            # Check if S1/S2 model is enabled in config
            s1s2_params = SimulationSettings.move_rules.get('s1s2_model_params', None)
            if s1s2_params and s1s2_params.get('enabled', False):
                # Calculate experience-based capacity index (as per presentation)
                experience_index = calculate_experience_index(
                    prior_displacement=a.timesteps_since_departure / 30.0,  # Normalize to ~[0, 1]
                    local_knowledge=a.attributes.get('local_knowledge', 0.0),
                    conflict_exposure=a.attributes.get('conflict_exposure', 0.0),
                    connections=a.attributes.get('connections', 0),
                    age_factor=a.attributes.get('age_factor', 0.5),
                    education_level=a.attributes.get('education_level', getattr(a, 'education', 0.5))
                )
                
                # Conflict already calculated above for high-conflict check
                # Reuse it here for consistency (conflict is in scope from line 530)
                movechance = a.location.movechance
                
                # Get parameters from config (only α and β are free; p_s2 is fixed)
                alpha = s1s2_params.get('alpha', 2.0)
                beta = s1s2_params.get('beta', 2.0)
                p_s2 = s1s2_params.get('p_s2', 0.8)
                
                # Calculate move probability using parsimonious model (P_S2 = Ψ × Ω)
                p_move, p_s2_active = calculate_move_probability_s1s2(
                    experience_index, conflict, movechance,
                    alpha, beta, p_s2
                )
                
                # Store S2 activation probability for route selection
                a.s2_activation_prob = p_s2_active
                
                # Determine if S2 is active (lower threshold to allow more S2 activation)
                system2_active = p_s2_active > 0.3  # Reduced from 0.5 to 0.3 for easier S2 activation
                
                # Log S2 activation decision
                if system2_active:
                    a.log_decision("S2", {
                        "experience_index": experience_index,
                        "conflict": conflict,
                        "s2_activation_prob": p_s2_active,
                        "location": getattr(a.location, 'name', 'UnknownLocation')
                    }, time)
                    
                    # Pre-calculate route if System 2 is active
                    provisional_route = selectRoute(a, time, system2_active=True)
                    if len(provisional_route) == 0:
                        return 0.0, True  # suppress move if no viable route
                    else:
                        a.attributes["_temp_route"] = provisional_route
                        
                        # Share route information with connected agents
                        if a.attributes.get("connections", 0) > 0:
                            a.attributes["_share_route_info"] = True
                
                return p_move, system2_active
        
        # Fallback: Use refactored S1/S2 system if available
        elif calculate_s1s2_move_probability is not None:
            # NOTE: This fallback system still uses education directly
            # For consistency with aligned model, we should calculate experience_index
            # but the refactored system signature requires education parameter
            # This is a legacy fallback - the aligned model (above) is preferred
            
            # Calculate experience index for consistency (even though refactored system uses education)
            try:
                from flee.s1s2_model import calculate_experience_index
                experience_index = calculate_experience_index(
                    prior_displacement=a.timesteps_since_departure / 30.0,
                    local_knowledge=a.attributes.get('local_knowledge', 0.0),
                    conflict_exposure=a.attributes.get('conflict_exposure', 0.0),
                    connections=a.attributes.get('connections', 0),
                    age_factor=a.attributes.get('age_factor', 0.5),
                    education_level=a.attributes.get('education_level', 0.5)
                )
                # Map experience_index back to education-equivalent for refactored system
                # (This is a workaround - ideally refactored system would use experience_index)
                education_equivalent = min(experience_index / 3.0, 1.0)  # Normalize experience to [0,1]
            except ImportError:
                education_equivalent = a.attributes.get('education_level', 0.5)
            
            # Get S1/S2 configuration
            s1s2_config = S1S2Config({
                "connectivity_mode": SimulationSettings.move_rules.get("connectivity_mode", "baseline"),
                "soft_capability": SimulationSettings.move_rules.get("soft_capability", False),
                "pmove_s2_mode": SimulationSettings.move_rules.get("pmove_s2_mode", "scaled"),
                "pmove_s2_constant": SimulationSettings.move_rules.get("pmove_s2_constant", 0.9),
                "eta": SimulationSettings.move_rules.get("eta", 0.5),
                "steepness": SimulationSettings.move_rules.get("steepness", 6.0),
                "soft_gate_steepness": SimulationSettings.move_rules.get("soft_gate_steepness", 8.0),
            })
            
            # Calculate S1/S2 move probability
            move_prob, s2_activation_prob, s2_active = calculate_s1s2_move_probability(
                time=time,
                conflict_intensity=max(0.0, getattr(a.location, 'conflict', 0.0)),
                connections=a.attributes.get("connections", 0),
                timesteps_since_departure=a.timesteps_since_departure,
                education=education_equivalent,  # Use experience-based value
                stress_tolerance=a.attributes.get('stress_tolerance', 0.5),
                threshold=a.attributes.get('s2_threshold', 0.5),
                location_movechance=a.location.movechance,
                s1_move_prob=0.0,  # Will be calculated below
                config=s1s2_config,
                conflict_start_time=getattr(a.location, 'time_of_conflict', 0)
            )
            
            # Calculate S1 move chance for the combined probability
            s1_move_chance = calculate_s1_move_chance(a, ForceTownMove, time)
            
            # Recalculate with proper S1 move chance
            move_prob, s2_activation_prob, s2_active = calculate_s1s2_move_probability(
                time=time,
                conflict_intensity=max(0.0, getattr(a.location, 'conflict', 0.0)),
                connections=a.attributes.get("connections", 0),
                timesteps_since_departure=a.timesteps_since_departure,
                education=education_equivalent,  # Use experience-based value
                stress_tolerance=a.attributes.get('stress_tolerance', 0.5),
                threshold=a.attributes.get('s2_threshold', 0.5),
                location_movechance=a.location.movechance,
                s1_move_prob=s1_move_chance,
                config=s1s2_config,
                conflict_start_time=getattr(a.location, 'time_of_conflict', 0)
            )
            
            # Log S2 activation decision
            if s2_active:
                a.log_decision("S2", {
                    "cognitive_pressure": a.calculate_cognitive_pressure(time),
                    "threshold": a.attributes.get('s2_threshold', 0.5),
                    "connections": a.attributes.get('connections', 0),
                    "location": getattr(a.location, 'name', 'UnknownLocation')
                }, time)
                
                # Safe access to location name for debugging
                location_name = getattr(a.location, 'name', 'UnknownLocation')
                print(f"System 2 activated: Agent at {location_name} (pressure: {a.calculate_cognitive_pressure(time):.2f}, connections: {a.attributes.get('connections', 0)}) at time {time}", file=sys.stderr)
                print(f"DEBUG: Decision history length: {len(a.decision_history)}", file=sys.stderr)
            
            # Pre-calculate route if System 2 is active
            if s2_active:
                provisional_route = selectRoute(a, time, system2_active=True)
                if len(provisional_route) == 0:
                    return 0.0, True  # suppress move if no viable route
                else:
                    a.attributes["_temp_route"] = provisional_route
                    
                    # Share route information with connected agents
                    if a.attributes.get("connections", 0) > 0:
                        a.attributes["_share_route_info"] = True
            
            return move_prob, s2_active
        else:
            # Fallback to original S1/S2 logic
            return calculate_move_chance_original(a, ForceTownMove, time)

    # If System 2 is not active, calculate standard System 1 move chance
    # CRITICAL: Camps have very low movechance - respect it even if agent has a route
    if a.location.camp or a.location.idpcamp:
        # Preserve current cognitive state, but use camp_movechance (agents don't move)
        current_s2 = getattr(a, 'cognitive_state', 'S1') == 'S2'
        return a.location.movechance, current_s2
    
    # CRITICAL: High-conflict zones have high movechance (1.0) - respect it even if agent has a route
    # This ensures agents always try to leave extreme danger zones (panic response)
    conflict = max(0.0, getattr(a.location, 'conflict', 0.0))
    if conflict > 0.5:  # High conflict threshold
        # Preserve current cognitive state, but use conflict_movechance (agents always try to leave)
        current_s2 = getattr(a, 'cognitive_state', 'S1') == 'S2'
        return a.location.movechance, current_s2
    
    if a.location.town and ForceTownMove:  # called through evolve
        return 1.0, system2_active
    elif len(a.route) > 0: #If a route with destination is known, the agent will continue to follow it.
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
      SimulationSettings.move_rules["PruningThreshold"] = 1.0  # Pruning is disable (just to be sure).

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

