This document provides formats of csv files for loading initial graph. Each conflict has three main csv files:

 ## 1. locations.csv
 
    |name| region| country| lat| lon| location_type| conflict_date| pop/cap              |
    |----|-------|--------|----|----|--------------|--------------|----------------------|
    |    |       |        |    |    | -conflict    |              |-population for cities|
    |    |       |        |    |    | -town        |              |-population for cities|
    |    |       |        |    |    | -camp        |              |-capacities for camps |
 

 ## 2. routes.csv

    |name1| name2| distance|
    |-----|------|---------|
    |     |      |         |


 ## 3. closures.csv  (Border closure events at country or location levels)
   
    |closure_type| name1| name2| closure_start| closure_end|
    |------------|------|------|--------------|------------|
    | -country   |      |      |              |            |
    | -location  |      |      |              |            |
