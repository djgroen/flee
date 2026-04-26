import os
import sys
import numpy as np
import random
import flee.lib_math as lm
from typing import List, Optional, Tuple
from flee.SimulationSettings import SimulationSettings
import flee.spawning as spawning
import flee.demographics as demographics

# Import dual-process (System 1 / System 2) V3 model: continuous blend with
# P_S2 = Psi*Omega as blending weight. Module renamed in Day 7b so that
# bare "S1" no longer collides with sobol first-order index notation.
# The subscript S2 in P_S2 refers to System 2 cognition, NOT a sobol index.
try:
    from flee.dual_process_model import (
        compute_deliberation_weight,
        compute_s2_move_probability,
        compute_opportunity,
    )
except ImportError as e:
    print(f"DEBUG: ImportError in moving.py: {e}", file=sys.stderr)
    compute_deliberation_weight = None
    compute_s2_move_probability = None
    compute_opportunity = None


def _get_location_coords(loc):
    """Return (lat, lon) if location has coordinates, else None."""
    lat = getattr(loc, "lat", getattr(loc, "gps_y", getattr(loc, "y", None)))
    lon = getattr(loc, "lon", getattr(loc, "gps_x", getattr(loc, "x", None)))
    if lat is not None and lon is not None:
        return (float(lat), float(lon))
    return None


def _get_radiation_at_location(loc, time: int, fallback: float) -> float:
    """
    Get actual radiation [0,1] at location for System 2 move evaluation.
    Uses: radiation_field (if loc has coords), else location.radiation/dose_rate, else fallback (conflict).
    """
    rf = SimulationSettings.move_rules.get("radiation_field")
    if rf is not None:
        coords = _get_location_coords(loc)
        if coords is not None:
            time_hours = SimulationSettings.move_rules.get("time_hours", float(time))
            return rf.get_dose_rate(coords[0], coords[1], time_hours)
    return getattr(loc, "radiation", getattr(loc, "dose_rate", fallback))


def _lookup_potential(location, time: int, c_here: float, s2: bool = False):
    """Return ``(c_best, d_best)`` for ``location`` at simulation day ``time``.

    Queries the precomputed ``ConflictPotentialField`` registered on
    ``SimulationSettings.move_rules['potential_field']`` if available.
    Falls back to a 1-hop minimum-conflict scan over ``location.links`` when
    no field is registered (e.g. unit tests, legacy callers).
    """
    field = SimulationSettings.move_rules.get("potential_field")
    if field is not None:
        try:
            return field.get(int(time), getattr(location, "name", ""), s2=s2)
        except Exception:
            pass

    # Legacy 1-hop fallback: minimum-conflict neighbour.
    c_best = c_here
    d_best = 1.0
    links = getattr(location, "links", None) or []
    if links:
        best_link = min(
            links,
            key=lambda lnk: max(0.0, getattr(lnk.endpoint, "conflict", 0.0)),
        )
        c_best = max(0.0, getattr(best_link.endpoint, "conflict", 0.0))
        d_best = max(1.0, best_link.get_distance())
    return c_best, d_best

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
        #Get the current flood level of the endpoint, if flood level not set in flood_level.csv then default to zero
        flood_level = endpoint.attributes.get("flood_level", 0.0)
        #print("Link:", endpoint.name, endpoint.attributes, file=sys.stderr)
        if flood_level > 0.0:
            #set the base equal to the flood location weight
            base *= lm.interp(SimulationSettings.move_rules["FloodLocWeights"], flood_level)
            #otherwise base score is unaffected by flooding

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
                        #get the endpoint locations current flood level weight based on that flood level.
                        forecast_flood_level_weight = lm.interp(SimulationSettings.move_rules["FloodLocWeights"], forecast_flood_level)
                        #get the current flood forecaster weight e.g. how important the current day is in the forecast
                        flood_forecaster_weight = float(SimulationSettings.move_rules["FloodForecasterWeights"][forecast_day])
                        flood_forecast_base += forecast_flood_level_weight * flood_forecaster_weight
                      if forecast_day == forecast_end_time:
                        break
                  flood_forecast_base *= float(flood_forecast_base/forecast_timescale)
                  flood_forecast_base *= float(agent_awareness_weight) 
                  base *= flood_forecast_base  

    # Waypoints: strongly down-weight as final destinations (route through, not to)
    if getattr(endpoint, "is_waypoint", False):
        base *= 0.05
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


S2_OVERRIDE_KEYS = ["AwarenessLevel", "WeightSoftening", "DistancePower", "PruningThreshold"]
S2_OVERRIDES = {
    "AwarenessLevel": lambda orig: min(3, orig + 1),
    "WeightSoftening": 0.0,
    "DistancePower": 1.2,
    "PruningThreshold": 1.0,
}


def _s2_route_context():
    """Context manager: temporarily apply System-2 routing params, restore on exit."""
    from contextlib import contextmanager

    @contextmanager
    def _ctx():
        old = {k: SimulationSettings.move_rules[k] for k in S2_OVERRIDE_KEYS}
        try:
            for k in S2_OVERRIDE_KEYS:
                v = S2_OVERRIDES.get(k)
                SimulationSettings.move_rules[k] = v(old[k]) if callable(v) else v
            yield
        finally:
            SimulationSettings.move_rules.update(old)

    return _ctx()


@check_args_type
def calculateMoveChance(a, ForceTownMove: bool, time) -> Tuple[float, float]:
    """
    Calculates the probability that an agent will move this step.
    Returns (blended_movechance, sys2_weight) where sys2_weight is in [0, 1].
    """
    sys2_weight = 0.0
    movechance = a.location.movechance

    # Standard FLEE: Population/Capacity scaling
    movechance *= (float(max(a.location.pop, a.location.capacity)) / SimulationSettings.move_rules["MovechancePopBase"])**SimulationSettings.move_rules["MovechancePopScaleFactor"]

    if SimulationSettings.move_rules.get("FleeWhenStarving", False) is True:
        if "region_IPC_level" not in a.location.attributes.keys():
            print("ERROR: move_rules.FleeWhenStarving is set in simulationsetting.yml, but no IPC input data (region_attributes_IPC.csv) has been loaded.", file=sys.stderr)
            print(f"INFO: Error occurred for Location {a.location.name}, region {a.location.region}.", file=sys.stderr)
            sys.exit()
        loc_ipc_modifier = a.location.attributes["region_IPC_level"] / 100.0
        movechance = loc_ipc_modifier + ((1.0 - loc_ipc_modifier) * movechance)

    # DFlee Flood Location Movechance implementation
    if SimulationSettings.move_rules.get("FloodRulesEnabled", False) is True:
        flood_level = a.location.attributes.get("flood_level", 0.0)
        if flood_level > 0.0:
            movechance = lm.interp(SimulationSettings.move_rules["FloodMovechances"], flood_level)
        if SimulationSettings.move_rules.get("FloodForecaster", False) is True:
            forecast_timescale = SimulationSettings.move_rules["FloodForecasterTimescale"]
            forecast_end_time = SimulationSettings.move_rules["FloodForecasterEndTime"]
            flood_forecast_base = 0.0
            flood_forecast_movechance = 0.0
            agent_awareness_weight = float(SimulationSettings.move_rules["FloodAwarenessWeights"][int(a.attributes["floodawareness"])])
            for x in range(1, forecast_timescale + 1):
                forecast_day = time + x
                if forecast_day >= forecast_end_time:
                    forecast_day = forecast_end_time
                forecast_flood_level = int(a.location.attributes.get("forecast_flood_levels", 0)[forecast_day])
                if forecast_flood_level > 0.0:
                    forecast_flood_level_weight = lm.interp(SimulationSettings.move_rules["FloodLocWeights"], forecast_flood_level)
                    flood_forecaster_weight = float(SimulationSettings.move_rules["FloodForecasterWeights"][forecast_day])
                    flood_forecast_base += forecast_flood_level_weight * flood_forecaster_weight
                if forecast_day == forecast_end_time:
                    break
            flood_forecast_movechance = float(flood_forecast_base / forecast_timescale)
            flood_forecast_movechance *= float(agent_awareness_weight)
            movechance *= flood_forecast_movechance

    if SimulationSettings.move_rules.get("TwoSystemDecisionMaking", False):
        # Camps/safe zones: respect camp_movechance, no dual-process override
        if getattr(a.location, 'camp', False) or getattr(a.location, 'idpcamp', False):
            a.sys2_activation_prob = 0.0  # ensure recorded correctly for analytics
            return a.location.movechance, 0.0

        # Native FLEE conflict at current location is the sole input.
        c_here = max(0.0, getattr(a.location, 'conflict', 0.0))

        # Optional override for comparison runs (sys1_only -> 0, sys2_only -> 1)
        override = SimulationSettings.move_rules.get("sys2_weight_override")
        if override is None:
            # Back-compat: legacy key name from pre-Day-7b YAML configs
            override = SimulationSettings.move_rules.get("s2_weight_override")
        if override is not None:
            sys2_weight = float(override)
            a.sys2_activation_prob = sys2_weight
            if sys2_weight <= 0.0:
                return movechance, 0.0
            if sys2_weight >= 1.0 and compute_s2_move_probability:
                c_best, d_best = _lookup_potential(
                    a.location, time, c_here, s2=True,
                )
                kappa = float(SimulationSettings.move_rules.get(
                    's1s2_model_params', {}).get('kappa', 5.0))
                sigma = compute_s2_move_probability(c_here, c_best, d_best, kappa)
                blended = sigma
                if c_here > 0.9:
                    blended = max(blended, 0.95)
                return blended, 1.0

        # Decision engine (blend/switch) — delegate to engine
        engine = SimulationSettings.move_rules.get("decision_engine")
        if engine is None:
            # Lazy engine creation when decision_mode set but no YML loaded
            # (e.g. run_synthetic)
            decision_mode = SimulationSettings.move_rules.get("decision_mode", "blend")
            if decision_mode and compute_deliberation_weight:
                from flee.decision_engine import DecisionEngine
                config = {"s1s2_model_params":
                          SimulationSettings.move_rules.get("s1s2_model_params", {})}
                engine = DecisionEngine.create(decision_mode, config)
                SimulationSettings.move_rules["decision_engine"] = engine
            else:
                return movechance, 0.0

        # Look up (c_best, d_best) from the potential field if available;
        # otherwise fall back to the legacy 1-hop minimum-conflict lookup so
        # tests and callers without a precomputed field still work.
        # We don't yet know sys2_weight — use the deeper System-2 lookup whenever the
        # agent could plausibly receive non-trivial deliberation weight; the
        # engine then re-weights via P_S2.
        c_best, d_best = _lookup_potential(
            a.location, time, c_here, s2=True,
        )

        blended_movechance, sys2_weight = engine.compute_move_probability(
            movechance_s1=movechance,
            experience_index=a.experience_index,
            conflict_intensity=c_here,
            rad_here=c_here,
            rad_best=c_best,
            distance_best=d_best,
        )
        a.sys2_activation_prob = sys2_weight
        return blended_movechance, sys2_weight

    if a.location.town and ForceTownMove:
        return 1.0, 0.0
    elif len(a.route) > 0:
        return 1.0, 0.0

    return movechance, 0.0


@check_args_type
def selectRoute(a, time: int, debug: bool = False, return_all_routes: bool = False, sys2_weight: float = 0.0):
    """Select route using blended System 1 / System 2 scoring when sys2_weight > 0."""
    if SimulationSettings.move_rules["AwarenessLevel"] == 0:
        linklen = len(a.location.links)
        return [np.random.randint(0, linklen)]

    use_s2 = SimulationSettings.move_rules.get("TwoSystemDecisionMaking", False) and sys2_weight > 0.01

    def _compute_routes_s1():
        """Standard FLEE route scoring (System 1, no deliberation)."""
        weights_s1, routes_s1 = [], []
        if SimulationSettings.move_rules["FixedRoutes"] is True:
            for l in a.location.routes.keys():
                weights_s1.append(a.location.routes[l][0] * getEndPointScore(a, a.location.routes[l][2], time))
                routes_s1.append(a.location.routes[l][1])
        else:
            for k, e in enumerate(a.location.links):
                wgt, rts = calculateLinkWeight(a, link=e, prior_distance=0.0,
                    origin_names=[a.location.name], step=1, time=time, debug=debug)
                weights_s1 += wgt
                routes_s1 += rts
            if return_all_routes:
                return (weights_s1, routes_s1)
            for i in range(len(routes_s1)):
                routes_s1[i] = routes_s1[i][1:]
            weights_s1, routes_s1 = pruneRoutes(weights_s1, routes_s1)
        return (weights_s1, routes_s1)

    if not use_s2:
        result = _compute_routes_s1()
        if return_all_routes and isinstance(result, tuple) and len(result) == 2:
            return result
        weights, routes = result
        route = chooseFromWeights(weights=weights, routes=routes)
        return route if route is not None else []

    # Blended System-1 / System-2 path: compute both, then blend weights
    s1_result = _compute_routes_s1()
    weights_s1, routes_s1 = s1_result

    weights_s2, routes_s2 = [], []
    with _s2_route_context():
        if SimulationSettings.move_rules["FixedRoutes"] is True:
            for l in a.location.routes.keys():
                weights_s2.append(a.location.routes[l][0] * getEndPointScore(a, a.location.routes[l][2], time))
                routes_s2.append(a.location.routes[l][1])
        else:
            for k, e in enumerate(a.location.links):
                wgt, rts = calculateLinkWeight(a, link=e, prior_distance=0.0,
                    origin_names=[a.location.name], step=1, time=time, debug=debug)
                weights_s2 += wgt
                routes_s2 += rts
            for i in range(len(routes_s2)):
                routes_s2[i] = routes_s2[i][1:]
            weights_s2, routes_s2 = pruneRoutes(weights_s2, routes_s2)

    route_to_sys2_weight = {}
    for w, r in zip(weights_s2, routes_s2):
        key = tuple(r)
        route_to_sys2_weight[key] = w

    conflict_at_location = max(0.0, getattr(a.location, 'conflict', 0.0))
    engine = SimulationSettings.move_rules.get("decision_engine")

    blended_weights = []
    for w_s1, r in zip(weights_s1, routes_s1):
        w_s2 = route_to_sys2_weight.get(tuple(r), 0.0)
        if engine is not None:
            w = engine.compute_destination_weight(
                w_s1, w_s2,
                experience_index=a.experience_index,
                conflict_intensity=conflict_at_location,
            )
        else:
            w = (1.0 - sys2_weight) * w_s1 + sys2_weight * w_s2
        blended_weights.append(w)

    s1_route_set = {tuple(r) for r in routes_s1}
    for w, r in zip(weights_s2, routes_s2):
        if tuple(r) not in s1_route_set:
            if engine is not None:
                blended_weights.append(
                    engine.compute_destination_weight(
                        0.0, w,
                        experience_index=a.experience_index,
                        conflict_intensity=conflict_at_location,
                    )
                )
            else:
                blended_weights.append(sys2_weight * w)
            routes_s1.append(r)

    route = chooseFromWeights(weights=blended_weights, routes=routes_s1)
    return route if route is not None else []


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
