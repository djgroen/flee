from flee.SimulationSettings import SimulationSettings
import numpy as np
import os

from typing import List, Optional, Tuple

if os.getenv("FLEE_TYPE_CHECK") is not None and os.environ["FLEE_TYPE_CHECK"].lower() == "true":
    from beartype import beartype as check_args_type
else:
    def check_args_type(func):
        return func

import sys

@check_args_type
def updateLocationScore(time: int, loc) -> None:
    """
    Summary: 
        Attractiveness of the local point, based on local point
        information only.

    Args: 
        time (int): The current timestep
        loc (Location): The location to update the score for

    Returns:
        None. The score is updated in place.
    """

    score = 1.0 #default score

    #score multiplier for foreign
    if loc.foreign is True:
        score *= SimulationSettings.move_rules["ForeignWeight"] 
   
    #score multiplier for camps
    if loc.camp or loc.idpcamp is True:
        score *= SimulationSettings.move_rules["CampWeight"] 

    #score multiplier for conflict
    if loc.conflict > 0.0: 
        #score takes the conflict weight to the power of the conflict decay multiplier
        #conflict decay multiplier is larger for locations with conflict for longer periods of time
        score *= SimulationSettings.move_rules["ConflictWeight"]**(SimulationSettings.get_location_conflict_decay(time, loc) * loc.conflict)

    # #score multiplier for flooding
    # if loc.flood_zone: 
    #     flood_level = loc.attributes.get("flood_level",0)
    #     score *= float(SimulationSettings.move_rules["FloodLocWeights"][flood_level])
       
    #     #Flooding Forecaster Location Score Implementation:
    #     if SimulationSettings.move_rules["FloodForecaster"] is True:

    #         #Get the forecast timescale e.g. 5 day weather forecast
    #         forecast_timescale = SimulationSettings.move_rules["FloodForecasterTimescale"]

    #         #Get the forecast length e.g. only know the forecast until day 7
    #         forecast_end_time = SimulationSettings.move_rules["FloodForecasterEndTime"] 

    #         # If there is a forecast timescale and endtime are set
    #         # If forecast_timescale is greater than 1 and the current time step is less than the forecast end time
    #         if forecast_timescale is not None:
    #             if forecast_end_time is not None:
    #                 if (forecast_timescale > 1.0) and (time <= forecast_end_time): 
                
    #                     #Set the default score value
    #                     flood_forecast_score = 0.0 #no forecast, no flooding

    #                     #Get the agents awareness level of the flood forecast
    #                     #Weighting of each awareness level defined in simsetting.yml
    #                     #Fraction of population with each level of flood awareness defined in demographics_floodawareness.csv 
    #                     #Awareness can be used as a proxy for ability to adapt to forecasted flooding.
    #                     #For example, low awareness will down weight the importance of the forecast or reduce the impact the forecast has on the 
    #                     # agents decision making process. 
    #                     # agent_awareness_weight = float(SimulationSettings.move_rules["FloodAwarenessWeights"][int(agent.attributes["floodawareness"])])

    #                     #Forecast loop: iterate over the location flood level weights for the forecast timescale
    #                     for x in range(1, forecast_timescale + 1): #iterates over the 5 day forecast, ignoring the current day

    #                         #the day of the forcast we're considering 
    #                         forecast_day = time + x 

    #                         # If the simulation length is less than the end of the forecast, then the forecast will be shorter
    #                         if forecast_day >= forecast_end_time:
    #                             # Set the forecast day to the end of the simulation
    #                             forecast_day = forecast_end_time  # same as time + x

    #                         #Get the forecast flood level for the location on the day we're considering in the for loop
    #                         forecast_flood_level = loc.attributes.get("forecast_flood_level",0)

    #                         # print("forecast_flood_level",forecast_flood_level, file=sys.stderr)

    #                         # print("loc.flood_level", loc.flood_level, file=sys.stderr)
                    
    #                         # # if it's not zero, then we need to modify the base forecast value, otherwise leave the base as it will zero.
    #                         # if forecast_flood_level > 0.0: 
    #                         #     #get the endpoint locations current flood level weight based on that flood level.
    #                         #     forecast_flood_level_weight = float(SimulationSettings.move_rules["FloodLocWeights"][forecast_flood_level]) 
                                
    #     #                         #get the current flood forecaster weight e.g. how important the current day is in the forecast
    #     #                         flood_forecaster_weight = float(SimulationSettings.move_rules["FloodForecasterWeights"][forecast_day])
                            
    #     #                         #modify the flood_forecast_base using the flood level on the current day and the imporatance of the current day in the forecast loop
    #     #                         flood_forecast_base += forecast_flood_level_weight * flood_forecaster_weight

    #     #                     #break the loop if we've reached the end of the forecast data 
    #     #                     if forecast_day == forecast_end_time:
    #     #                         break

    #     #                 #the flood_forecast_base now represents the total weight of the flooding during the forecast for the endpoint location,
    #     #                 # this needed to be divided by the total number of days in the forecast to get the average weight based on the severity and relative imporatance of the forecasted days
    #     #                 flood_forecast_score *= float(flood_forecast_score/forecast_timescale)

    #     #                 #down weight the overall importance of the flood forecast on the base depending on the agents awareness weighting
    #     #                 #currently using a simple down weighting, but may want lower awareness agents to only respond to high flood levels 
    #     #                 # or shorter forecast timescales.
    #     #                 # flood_forecast_score *= float(agent_awareness_weight) 

    #     #                 # Make the flood_forecast_base effect the actual base score
    #     #                 score *= flood_forecast_score

                    
    #         #     else:
    #         #         print("WARNING: flood_forecaster_endtime is not set in simsetting.yml", file=sys.stderr)
    #         # else:
    #         #     print("WARNING: flood_forecaster_timescale is not set in simsetting.yml", file=sys.stderr)
        

    loc.setScore(0, 1.0)
    #print(loc.name,loc.camp,loc.foreign,loc.scores)

