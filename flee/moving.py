import os
import sys
import numpy as np
import random
from beartype.typing import List, Optional, Tuple
from flee.SimulationSettings import SimulationSettings
import flee.spawning as spawning
import flee.demographics as demographics

# Import new 5-parameter S1/S2 model
try:
    from flee.s1s2_model import calculate_move_probability_s1s2, compute_deliberation_probability
except ImportError as e:
    print(f"DEBUG: ImportError in moving.py: {e}", file=sys.stderr)
    calculate_move_probability_s1s2 = None
    compute_deliberation_probability = None

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

    if SimulationSettings.move_rules["ChildrenAvoidHazards"]:
        if agent.attributes["age"]<19:
            base = base*base
        if SimulationSettings.move_rules["BoysTakeRisk"]:
            if agent.attributes["gender"]=="male" and agent.attributes["age"]>14:
                base = 1 

    if SimulationSettings.move_rules["StayCloseToHome"]:
        power_factor = SimulationSettings.move_rules["HomeDistancePower"]
        base *= 1.0/(max(1.0,endpoint.calculateDistance(agent.location))**power_factor)

    if SimulationSettings.move_rules["FloodRulesEnabled"] is True:
        flood_level = endpoint.attributes.get("flood_level",0)
        if flood_level > 0:
            base *= float(SimulationSettings.move_rules["FloodLocWeights"][flood_level])

        if SimulationSettings.move_rules["FloodForecaster"] is True:
            forecast_timescale = SimulationSettings.move_rules["FloodForecasterTimescale"]
            forecast_end_time = SimulationSettings.move_rules["FloodForecasterEndTime"] 
            if forecast_timescale is not None and forecast_end_time is not None:
                if (forecast_timescale > 1.0) and (time <= forecast_end_time): 
                  flood_forecast_base = 0.0
                  agent_awareness_weight = float(SimulationSettings.move_rules["FloodAwarenessWeights"][int(agent.attributes["floodawareness"])])
                  for x in range(1, forecast_timescale + 1):
                      forecast_day = time + x 
                      if forecast_day >= forecast_end_time:
                          forecast_day = forecast_end_time
                      forecast_flood_level = endpoint.attributes.get("forecast_flood_levels",0)[forecast_day]
                      if forecast_flood_level > 0.0: 
                        forecast_flood_level_weight = float(SimulationSettings.move_rules["FloodLocWeights"][forecast_flood_level]) 
                        flood_forecaster_weight = float(SimulationSettings.move_rules["FloodForecasterWeights"][forecast_day])
                        flood_forecast_base += forecast_flood_level_weight * flood_forecaster_weight
                      if forecast_day == forecast_end_time:
                        break
                  flood_forecast_base *= float(flood_forecast_base/forecast_timescale)
                  flood_forecast_base *= float(agent_awareness_weight) 
                  base *= flood_forecast_base  

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
    nearly_full_occ = SimulationSettings.move_rules["CapacityBuffer"]
    cap_scale = SimulationSettings.move_rules["CapacityScaling"]
    cap = location.capacity * float(cap_scale)    
    if cap < 1:
        return 1.0
    if location.numAgents <= nearly_full_occ * cap:
        return 1.0
    if location.numAgents >= 1.0 * cap:
        return 0.0
    residual = location.numAgents - (nearly_full_occ * cap)
    weight = 1.0 - (residual / (cap * (1.0 - nearly_full_occ)))
    return max(0.0, min(1.0, weight))


@check_args_type
def calculateLinkWeight(agent, link, prior_distance: float, origin_names: List[str], step: int, time: int, debug: bool = False) -> Tuple[List[float],List[List[str]]]:
  weights = []
  routes = []
  if link.endpoint.marker is False:
    weight = (float(SimulationSettings.move_rules["WeightSoftening"] + (float(getEndPointScore(agent=agent, endpoint=link.endpoint, time=time)))) / float(SimulationSettings.move_rules["DistanceSoftening"] + link.get_distance() + prior_distance)**SimulationSettings.move_rules["DistancePower"]) * getCapMultiplier(link.endpoint, numOnLink=int(link.numAgents))
    weight = weight**SimulationSettings.move_rules["WeightPower"]
    weights = [weight]
    routes = [origin_names + [link.endpoint.name]]
  else:
    step -= 1

  if SimulationSettings.move_rules["AwarenessLevel"] > step:
    for lel in link.endpoint.links:
      if lel.endpoint.name in origin_names:
        pass
      else:
        wgt, rts = calculateLinkWeight(agent=agent, link=lel, prior_distance=prior_distance + link.get_distance(), origin_names=origin_names + [link.endpoint.name], step=step + 1, time=time, debug=debug)
        weights = weights + wgt
        routes = routes + rts
  return weights, routes


@check_args_type
def normalizeWeights(weights: List[float]) -> List[float]:
  if np.sum(weights) > 0.0:
    weights = [x/float(sum(weights)) for x in weights]
  else:
    weights = [(x+1)/float(len(weights)) for x in weights]
  return weights


@check_args_type
def chooseFromWeights(weights, routes):
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
    """
    system2_active = False
    movechance = a.location.movechance
    
    # Standard FLEE: Population/Capacity scaling
    movechance *= (float(max(a.location.pop, a.location.capacity)) / SimulationSettings.move_rules["MovechancePopBase"])**SimulationSettings.move_rules["MovechancePopScaleFactor"]

    # Standard FLEE: Flood Rules
    if SimulationSettings.move_rules.get("FloodRulesEnabled", False):
        flood_level = a.location.attributes.get("flood_level", 0)
        if flood_level > 0.0:
            movechance = float(SimulationSettings.move_rules["FloodMovechances"][flood_level])

    if SimulationSettings.move_rules.get("TwoSystemDecisionMaking", False):
        conflict = max(0.0, getattr(a.location, 'conflict', 0.0))
        
        # Get S1/S2 parameters from config
        s1s2_params = SimulationSettings.move_rules.get('s1s2_model_params', {})
        if not s1s2_params: # Support flat structure as well
            s1s2_params = {
                'alpha': SimulationSettings.move_rules.get('alpha', 2.0),
                'beta': SimulationSettings.move_rules.get('beta', 2.0),
                'p_s2': SimulationSettings.move_rules.get('p_s2', 0.8)
            }
        
        alpha = float(s1s2_params.get('alpha', 2.0))
        beta = float(s1s2_params.get('beta', 2.0))
        p_s2_val = float(s1s2_params.get('p_s2', 0.8))

        # 1. Deliberation Probability: P_S2 = Ψ(experience; α) × Ω(conflict; β)
        if compute_deliberation_probability:
            p_s2_active = compute_deliberation_probability(a.experience_index, conflict, alpha, beta)
            a.s2_activation_prob = p_s2_active
            
            # 2. S2 Activation Threshold
            system2_active = p_s2_active > 0.5
            
            # 3. Combined Move Probability
            move_prob = (1.0 - p_s2_active) * movechance + p_s2_active * p_s2_val

            if system2_active:
                a.log_decision("S2", {
                    "experience_index": a.experience_index,
                    "conflict": conflict,
                    "p_s2_active": p_s2_active,
                    "location": getattr(a.location, 'name', 'Unknown')
                }, time)
                
                provisional_route = selectRoute(a, time, system2_active=True)
                if len(provisional_route) > 0:
                    a.attributes["_temp_route"] = provisional_route
            
            if conflict > 0.9:
                return 1.0, system2_active
                
            return move_prob, system2_active

    if a.location.town and ForceTownMove:
        return 1.0, system2_active
    elif len(a.route) > 0:
        return 1.0, system2_active

    return movechance, system2_active


@check_args_type
def selectRoute(a, time: int, debug: bool = False, return_all_routes: bool = False, system2_active: bool = False):
  weights = []
  routes = []
  
  if SimulationSettings.move_rules["AwarenessLevel"] == 0:
      linklen = len(a.location.links)
      return [np.random.randint(0, linklen)]

  original_params = {}
  if SimulationSettings.move_rules.get("TwoSystemDecisionMaking", False) and system2_active:
      original_params['awareness_level'] = SimulationSettings.move_rules["AwarenessLevel"]
      original_params['weight_softening'] = SimulationSettings.move_rules["WeightSoftening"]
      original_params['distance_power'] = SimulationSettings.move_rules["DistancePower"]
      original_params['pruning_threshold'] = SimulationSettings.move_rules["PruningThreshold"]
      
      SimulationSettings.move_rules["AwarenessLevel"] = min(3, original_params['awareness_level'] + 1)
      SimulationSettings.move_rules["WeightSoftening"] = 0.0
      SimulationSettings.move_rules["DistancePower"] = 1.2
      SimulationSettings.move_rules["PruningThreshold"] = 1.0

  if SimulationSettings.move_rules["FixedRoutes"] is True:
      for l in a.location.routes.keys():
          weights = weights + [a.location.routes[l][0] * getEndPointScore(a, a.location.routes[l][2], time)]
          routes = routes + [a.location.routes[l][1]]
  else:
      for k, e in enumerate(a.location.links):
          wgt, rts = calculateLinkWeight(a, link=e, prior_distance=0.0, origin_names=[a.location.name], step=1, time=time, debug=debug)
          weights = weights + wgt
          routes = routes + rts
      if return_all_routes is True:
          return weights, routes
      for i in range(0, len(routes)):
          routes[i] = routes[i][1:]
      weights, routes = pruneRoutes(weights, routes)
          
  if SimulationSettings.move_rules.get("TwoSystemDecisionMaking", False) and system2_active:
      SimulationSettings.move_rules["AwarenessLevel"] = original_params['awareness_level']
      SimulationSettings.move_rules["WeightSoftening"] = original_params['weight_softening']
      SimulationSettings.move_rules["DistancePower"] = original_params['distance_power']
      SimulationSettings.move_rules["PruningThreshold"] = original_params['pruning_threshold']

  route = chooseFromWeights(weights=weights, routes=routes)
  if route == None:
      return []
  return route


def pruneRoutes(weights, routes):
    threshold = SimulationSettings.move_rules["PruningThreshold"]
    if threshold < 1.001:
        return weights, routes
    min_weight_threshold = max(weights) / threshold
    i = 0
    while i < len(weights):
        if weights[i] < min_weight_threshold:
            weights.remove(weights[i])
            routes.remove(routes[i])
            i -= 1
        i += 1
    return weights, routes
