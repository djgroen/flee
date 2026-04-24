Here we describe the automation process for Flee input file generation. Please be aware that the script used in this section are numbered according to their excecution order. 

## Create ACLED.csv

To use the Flee input generation scripts effectively, you'll need to create an `acled.csv` file containing the conflict data for your simulation scenario. The `acled.csv` file should follow a specific format to ensure compatibility with the scripts. Here are the steps to create the `acled.csv` file:

1. **Prepare ACLED Data**: Obtain ACLED conflict data for your desired simulation scenario. ACLED provides detailed information on various conflicts, including dates, locations, and other relevant data. You can access ACLED data at [ACLED](https://acleddata.com/).

2. **Data Format**: Ensure that your ACLED data is in a CSV format and contains columns for essential information, such as "event_date," "country," and the relevant location type (e.g., "admin1" or "admin2").

3. **Data Cleaning**: Clean the ACLED data to remove any unnecessary columns or rows that are not relevant to your simulation. Ensure that the data is properly formatted and follows the required data structure.

4. **Save as acled.csv**: Save the cleaned ACLED data as a CSV file with the filename `acled.csv`.

5. **Create Simulation Directory**: In the directory where you have the Flee input generation scripts (e.g., "FabSim3/plugins/FabFlee/scripts"), create a new directory using the name of the simulation country. This directory will be used to store the `acled.csv` file and other relevant data for the simulation. For example, if you are simulating conflict dynamics in Nigeria in the year 2016, create a directory named "nigeria2016."

6. **Place acled.csv**: Move the `acled.csv` file that you created in step 4 into the newly created simulation directory (e.g., "nigeria2016").

For more information on how to create ACLED conflict data, please visit: https://flee.readthedocs.io/en/master/Simulation_instance_construction/


## Extract Location Names from ACLED Data

To extract location names from the ACLED data, you can run the following command:

        python 00_extract_location_names.py nigeria2016 admin2

**Input:** ACLED data (acled.csv)
**Output:** Location Names

**Command arguments:**

"python 00_extract_location_names.py \<country\> \<location_type\>"

- \<country\>: Name of the country or dataset (e.g., nigeria2016).
- \<location_type\>: The type of location for which you want to extract names (e.g., "admin1", "admin2", "location").


## Extract Population Data from External Sources

1. Once you have identified the locations from the ACLED data using the provided script, the next step is to find population data for these locations.

2. To obtain population data, you can search websites such as [CityPopulation] (https://www.citypopulation.de/) or other reliable sources.

3. When you find a webpage containing the desired population data, save the webpage as an HTML file.

4. Place the saved HTML file, named population.html, in the directory created earlier, which is named after your simulation country (e.g., nigeria2016).

This step ensures that you have the necessary population data for your Flee simulation. Continue with the following instructions to process and filter the population data.


## Extract Population Data from HTML

After saving the population data as an HTML file and placing it in the country directory (e.g., nigeria2016), you can proceed to extract the population data using the provided script.

Run the following command in your terminal:

        python 01_extract_population_csv.py nigeria2016 0 7 10000

**Input:** population.html
**Output:** Population data (population.csv)

**Description:**

This script creates a directory named after the specified country (e.g., nigeria2016).
It extracts city/town names and population data from an HTML file (population.html) and saves them in a CSV file (population.csv).

**Command arguments:**

"python 01_extract_population_csv.py \<country\> \<table_num\> \<column_num\> \<threshold\>"

- \<country\>: Name of the country (e.g., nigeria2016).
- \<table_num\>: Table index (0, 1, etc.) specifying which table to extract data from in the HTML file.
- \<column_num\>: Column index (0, 1, etc.) indicating the population column to extract from the table.
- \<threshold\>: Population threshold for filtering rows in the selected table.


## Extract Location Data:

After creating the `population.csv` file, use this script to process ACLED conflict data for a specified country and extracts location-based information such as town or administrative region names, their populations, and other relevant data. It then classifies locations into "towns" and "conflict zones" based on predefined conflict thresholds and combines this information with population data obtained separately.

Run the following command in your terminal:

        python 02_extract_locations_csv.py nigeria2016 01-01-2016 admin1 0 100

**Input:** ACLED data (acled.csv) & Population data (population.csv)
**Output:** Location data (locations.csv)

**Command arguments:**

"python 02_extract_locations_csv.py \<country\> \<start_date\> \<location_type\> \<fatalities_threshold\> \<conflict_threshold\>"

- \<country\>: Name of the country or dataset (e.g., nigeria2016).
- \<start_date\>: The starting date to consider when calculating conflict periods (e.g., "01-01-2016").
- \<location_type\>: The type of location to focus on (e.g., "admin2" for administrative region level 2).
- \<fatalities_threshold\>: Minimum fatalities count for including a location.
- \<conflict_threshold\>: Conflict period threshold for classifying locations.


## Extract Conflict Information:

This script processes ACLED conflict data for a specified country and extracts information about conflict periods and their estimated durations for different locations. It calculates the conflict period for each location based on the provided start date, and it adds an estimated conflict duration based on the number of added conflict days.

Run the following command in your terminal:

        python 03_extract_conflict_info.py nigeria2016 01-01-2016 31-12-2016 admin2 7

**Input:** ACLED data (acled.csv)
**Output:** Conflict information data (conflict_info.csv)

**Command arguments:**

"python 03_extract_conflict_info.py \<country\> \<start_date\> \<end_date\> \<location_type\> \<added_conflict_days\>"

- \<country\>: Name of the country or dataset (e.g., nigeria2016).
- \<start_date\>: The starting date to consider when calculating conflict periods (e.g., "01-01-2016").
- \<end_date\>: The end date to consider when calculating conflict periods (e.g., "31-12-2016").
- \<location_type\>: The type of location to focus on (e.g., "admin2" for administrative region level 2).
- \<added_conflict_days\>: The number of days to add to the calculated conflict periods for estimating event periods.


## Extract Conflicts Data:

This script processes conflict information for a specified country and generates a `conflicts.csv` file. It reads conflict data from the `conflict_info.csv` file, which includes location names, their corresponding start dates, and conflict periods. The script takes the earliest conflict date for a region and extends the period to the end date, however, it can be modified to calculate the number of days between the start_date and end_date, then create a DataFrame with a range of days as columns.

It populates the DataFrame with 1s for days that fall within the conflict periods of each location and 0s for the rest.

Run the following command in your terminal:

        python 04_extract_conflicts_csv.py nigeria2016 1-1-2016 31-12-2016

**Input:** Conflict information data (conflict_info.csv)
**Output:** Conflict data (conflicts.csv) 

Command:
Run the script using the following command:
"python 04_extract_conflicts_csv.py \<country\> \<start_date\> \<end_date\>"

- \<country\>: Name of the country or dataset (e.g., "nigeria2016").
- \<start_date\>: The starting date to consider when calculating conflict periods (e.g., "1-1-2016").
- \<end_date\>: The ending date to limit the number of days in the conflicts.csv file (e.g., "31-12-2016").


## Add Camps to Locations Data

Before generating the `routes.csv` file, it's essential to add camps to your existing `locations.csv` data. This step is necessary because you'll need to connect routes from all locations to these camps in your Flee simulation.

To add camps, follow these instructions carefully while retaining the file's format:

Open your existing locations.csv file using a text editor or a spreadsheet application (e.g., Microsoft Excel, Google Sheets).

Add a new row for each camp in the file, following the same format as existing location entries. Ensure that you include the required columns, such as name, lat, lon, and other relevant information, except conflict_period which is set to zero (no conflict).

Assign unique names to each camp to differentiate them from other locations.

Save the modified locations.csv file.

You can now proceed with generating the `routes.csv` file based on your updated locations.csv data, including the newly added camps.


## Extract Routes

This script processes geographical location data to generate a set of routes between locations within a specified country or dataset. It uses a nearest neighbor approach, enhanced with the consideration of intermediate stops, to determine the most efficient routes based on Euclidean distance. 

Run the following command in your terminal:

        python 05_extract_routes_csv.py nigeria2016

**Input:** CSV file containing geographical locations (locations.csv)
**Output:** CSV file containing the distances between locations (routes.csv)

Each entry in the file includes the starting location ('name1'), the destination location ('name2'), the distance between these locations, and a placeholder for 'force_redirection'.

Command:
Run the script using the following command:
"python 05_extract_routes_csv.py \<country\>"

- \<country\>: Name of the country or dataset (e.g., "nigeria2016").


## Visualize Routes

This script visualizes geographical routes and locations for a specified country. It primarily functions through the `extract_routes_info(country)` method, which processes location and route data for the given country. The script reads two CSV files: 'locations.csv' and 'routes.csv'. The 'locations.csv' file contains location data with fields such as 'name', 'latitude', and 'longitude'. The 'routes.csv' file contains routes data with fields including the starting location (name1), destination location (name2), and the distance between them.

The script uses the `folium` library to create an interactive map. It first plots markers for each location from the 'locations.csv' file. Then, it draws lines representing the routes from the 'routes.csv' file, showing the connections between different locations.

The resulting map offers a visual representation of how various locations are interconnected through different routes. This visualization can be particularly useful for understanding geographic proximity and route planning in the specified country.

Run the following command in your terminal:

        python 06_extract_routes_info.py nigeria2016

**Input:** locations.csv & routes.csv
**Output:** An interactive map file (HTML format)

Command:
Run the script using the following command:
"python 06_extract_routes_info.py \<country\>"

- \<country\>: Name of the country or dataset (e.g., "nigeria2016").
