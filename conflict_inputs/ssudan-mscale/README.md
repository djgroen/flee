This directory contains example input files for use with ssudan_mscale.py

This document provides formats of csv files for loading initial graph. Each scale has five main csv files plus conflict-period:

 ## 1. locations-#.csv (Replace # with 0 for Macro simulation and 1 for Micro Simulation)
 
    |name| region| country| lat| lon| location_type| conflict_date| pop/cap              |
    |----|-------|--------|----|----|--------------|--------------|----------------------|
    |    |       |        |    |    | -conflict    |              |-population for cities|
    |    |       |        |    |    | -town        |              |                      |
    |    |       |        |    |    | -camp        |              |-capacities for camps |
 
 conflict_data is given as an integer, counting the number of days after the simulation start. The value of -1 indicates the end of the simulation, while 0 indicates the start.

 ## 2. routes-#.csv (Replace # with 0 for Macro simulation and 1 for Micro Simulation)

    |name1| name2| distance|forced_redirection|link_type|
    |-----|------|---------|------------------|---------|
    |     |      |         |                  |         |


 ## 3. closures-#.csv (Replace # with 0 for Macro simulation and 1 for Micro Simulation)

 (Border closure events at country or location levels)
   
    |closure_type| name1| name2| closure_start| closure_end|
    |------------|------|------|--------------|------------|
    | -country   |      |      |              |            |
    | -location  |      |      |              |            |
    
    closure_start and closure_end are given as integers, counting the number of days after the simulation start. The value of -1 indicates the end of the simulation.

 ## 4. conflicts-#.csv (Replace # with 0 for Macro simulation and 1 for Micro Simulation)

    |Day| name1| name2| name3| ... |name#|
    |---|------|------|------| ... |-----|
    |   |      |      |      | ... |     |

    This table contains the name of conflict locations and the start date of corresponding conflicts

 ## 5. conflict-period.csv (Indicates the lenght and start date of simulation)

    |StartDate|------| 
    | Length  |------|

 ## 6. registration_corrections-#.csv (Replace # with 0 for Macro simulation and 1 for Micro Simulation)

    |camp_location|date|normalize|
    |-------------|----|---------|
    |             |    |         |
