import csv
import os
import sys
from typing import List

from flee.SimulationSettings import SimulationSettings

if os.getenv("FLEE_TYPE_CHECK") is not None and os.environ["FLEE_TYPE_CHECK"].lower() == "true":
    from beartype import beartype as check_args_type
else:
    def check_args_type(func):
        #Commented out because it introduces 10% slowdown.
        #@wraps(func)
        #def wrapper(*args, **kwargs):
        #    return func(*args, **kwargs)
        #return wrapper
        return func


class InputGeography:
    """
    Class which reads in Geographic information.
    """

    def __init__(self):
        self.locations = []
        self.links = []
        self.conflicts = {}
        self.attributes = {}


    @check_args_type
    def ReadConflictInputCSV(self, csv_name: str) -> None:
        """
        Reads a Conflict input file, to set conflict information.

        Args:
            csv_name (str): csv file name
        
        Returns:
            None.
        """
        self.conflicts = {}

        row_count = 0
        headers = []

        with open(csv_name, newline="", encoding="utf-8") as csvfile:
            values = csv.reader(csvfile)

            for row in values:
                # print(row)
                if row_count == 0:
                    headers = row
                    for i in range(1, len(headers)):  # field 0 is day.
                        headers[i] = headers[i].strip()
                        if len(headers[i]) > 0:
                            self.conflicts[headers[i]] = []
                else:
                    for i in range(1, len(row)):  # field 0 is day.
                        # print(row[0])
                        self.conflicts[headers[i]].append(float(row[i].strip()))
                row_count += 1

        # print(self.conflicts)
        # TODO: make test verifying this in test_csv.py


    @check_args_type
    def ReadAttributeInputCSV(self, attribute_name: str, attribute_type: str, csv_name: str) -> None:
        """
        Summary:
            Reads an attribute input file, to set attribute-specific information.

        Args:
            attribute_name (str): name of the attribute
            attribute_type (str): type of the attribute (int or float)
            csv_name (str): csv file name
        
        Returns:
            None.
        """
        self.attributes[attribute_name] = {}

        row_count = 0
        headers = []

        with open(csv_name, newline="", encoding="utf-8") as csvfile:
            values = csv.reader(csvfile)

            for row in values:
                # print(row)
                if row_count == 0:
                    headers = row
                    for i in range(1, len(headers)):  # field 0 is day.
                        headers[i] = headers[i].strip()
                        if len(headers[i]) > 0:
                            self.attributes[attribute_name][headers[i]] = []
                else:
                    for i in range(1, len(row)):  # field 0 is day.
                        # print("RAICSV", row[0], row[i], file=sys.stderr)
                        if attribute_type == "int":
                            self.attributes[attribute_name][headers[i]].append(int(row[i].strip()))
                        elif attribute_type == "float":
                            self.attributes[attribute_name][headers[i]].append(float(row[i].strip()))
                row_count += 1

        #print(self.attributes, file=sys.stderr)


    @check_args_type
    def getConflictLocationNames(self) -> List[str]:
        """
        Summary:
            Returns a list of conflict location names.
        
        Args:
            None.

        Returns:
            List[str]: list of conflict location names
        """
        if len(SimulationSettings.ConflictInputFile) == 0:
            conflict_names = []
            for loc in self.locations:
                if "conflict" in loc[4].lower():
                    conflict_names += [loc[0]]
            print(conflict_names, file=sys.stderr)
            return conflict_names

        return list(self.conflicts.keys())


    @check_args_type
    def ReadLocationsFromCSV(self, csv_name: str) -> None:
        """
        Summary:
            Converts a CSV file to a locations information table

        Args:
            csv_name (str): csv file name

        Returns:
            None.
        """

        if "flood_driven_spawning" in SimulationSettings.spawn_rules.keys():
            # Read flood location attributes.
            if SimulationSettings.spawn_rules["flood_driven_spawning"] is True:
                self.ReadAttributeInputCSV("flood_level","int",SimulationSettings.FloodLevelInputFile)
                self.ReadAttributeInputCSV("forecast_flood_levels","int",SimulationSettings.FloodLevelInputFile)

            elif SimulationSettings.move_rules["FloodRulesEnabled"] is False:
                if SimulationSettings.spawn_rules["conflict_driven_spawning"] is True:
                    self.ReadConflictInputCSV(SimulationSettings.ConflictInputFile)

        self.locations = []

        c = {}  # column map

        columns = [
            "name",
            "region",
            "country",
            "gps_x",
            "gps_y",
            "location_type",
            "conflict_date",
            "pop/cap",
        ]


        with open(csv_name, newline="", encoding="utf-8") as csvfile:
            values = csv.reader(csvfile)

            for row in values:
                if len(row) == 0 or row[0][0] == "#":
                    if len(row) > 8:
                        # First 8 columns have hard-coded names, other columns can be added to include custom (static) attributes
                        for i in range(8, len(row)):
                            print("appending", file=sys.stderr)
                            columns.append(row[i])
                        self.columns = columns
                    print("header", columns, row, len(row), file=sys.stderr)
                else:
                    # print(row)
                    self.locations.append(row)


    @check_args_type
    def MakeLocationList(self) -> dict:
        """
        Summary:
            Returns a dictionary of location names and their coordinates.

        Args:
            None.

        Returns:
            dict: dictionary of location names and their coordinates.
        """
        loc_list = {}
        for l in self.locations:
            loc_list[l[0]] = [float(l[3]),float(l[4])]
        return loc_list


    @check_args_type
    def MakeLocationColorsList(self) -> dict:
        """
        Summary:
            Returns a list of location colors.

        Args:
            None.

        Returns:
            list: list of location colors, ordered in the same way as in MakeLocationList.
        """
        loc_list = []
        for l in self.locations:
            if l[5].lower() == "camp":
                loc_list.append("green")
            elif "conflict" in l[5].lower():
                loc_list.append("red")
            elif l[5].lower() == "town":
                loc_list.append("yellow")
            elif l[5].lower() == "idpcamp":
                loc_list.append("teal")
            elif l[5].lower() == "marker":
                loc_list.append("white")
            elif l[5].lower() == "flood_zone":
                loc_list.append("blue")
            elif l[5].lower() == "forward":
                loc_list.append("blue")
            else:
                loc_list.append("black")

        return loc_list



    @check_args_type
    def ReadLinksFromCSV(self, csv_name: str) -> None:
        """
        Summary:
            Converts a CSV file to a locations information table

        Args:
            csv_name (str): csv file name

        Returns:
            None.
        """
        self.links = []

        with open(csv_name, newline="", encoding="utf-8") as csvfile:
            values = csv.reader(csvfile)

            link_columns = ["name1","name2","distance","forced_redirection"]
            for row in values:
                if len(row) == 0 or row[0][0] == "#":
                    if len(row) > 4:
                        # First 8 columns have hard-coded names, other columns can be added to include custom (static) attributes
                        for i in range(4, len(row)):
                            print("appending", file=sys.stderr)
                            link_columns.append(row[i])
                    self.link_columns = link_columns
                    print("link header", link_columns, row, len(row), file=sys.stderr)
                else:
                    # print(row)
                    self.links.append(row)


    @check_args_type
    def ReadClosuresFromCSV(self, csv_name: str) -> None:
        """
        Summary:
            Read the closures.csv file. Format is:
            closure_type,name1,name2,closure_start,closure_end

        Args:
            csv_name (str): csv file name

        Returns:
            None.
        """
        self.closures = []

        with open(csv_name, newline="", encoding="utf-8") as csvfile:
            values = csv.reader(csvfile)

            for row in values:
                if len(row) == 0 or row[0][0] == "#":
                    pass
                else:
                    # print(row)
                    self.closures.append(row)


    def ReadAgentsFromCSV(self, e, csv_name: str) -> None:
        """
        Summary:
            Read the agents.csv file. Format is:
            location, attributes

        Args:
            e (Ecosystem): ecosystem object
            csv_name (str): csv file name

        Returns:
            None.
        """

        self.agents = []

        with open(csv_name, newline="", encoding="utf-8") as csvfile:
            values = csv.reader(csvfile)

            i = 0
            for row in values:
                if len(row) == 0 or row[0][0] == "#":
                    pass
                elif i == 0:
                    headers = row[1:]
                    print(headers)
                else:
                    print(row)
                    attr = {}
                    for i in range (1, len(row)):
                        attr[headers[i-1]] = row[i]

                    loc_found = False
                    for i in range(0, len(e.locationNames)):
                        if e.locationNames[i] == row[0]:
                            e.addAgent(e.locations[i], attributes=attr)
                            loc_found= True

                    if not loc_found:
                        print("could not map location to CSV-loaded agent on line. (not count commented lines or empty lines)", sys.stderr)
                i += 1


    def StoreInputGeographyInEcosystem(self, e):
        """
        Summary:
            Store the geographic information in this class in a Flee simulation,
            overwriting existing entries.

        Args:
            e (Ecosystem): ecosystem object

        Returns:
            Tuple[Ecosystem, Dict]: tuple of ecosystem object and location dictionary
        """

        #0"name",1"region",2"country",3"gps_x",4"gps_y",5"location_type",6"conflict_date",7"pop/cap"


        lm = {}
        num_conflict_zones = 0

        # Home country is assumed to be the country of the first location.
        home_country = self.locations[0][2]
        print("Home country set to: ", home_country, file=sys.stderr)
        if len(home_country) < 1:
            home_country = "unknown"

        for loc in self.locations:

            name = loc[0]
            # if population field is empty, just set it to 0.
            if len(loc[7]) < 1:
                population = 0
            else:
                try:
                    population = int(int(loc[7]) // SimulationSettings.optimisations["PopulationScaleDownFactor"])
                except ValueError:
                    print(f"ERROR: location {loc[0]} has population value of {loc[7]}, which is not an int.", file=sys.stderr)
                    sys.exit()

            x = float(loc[3]) if len(loc[3]) > 0 else 0.0
            y = float(loc[4]) if len(loc[4]) > 0 else 0.0

            # if region field is empty, just set it to unknown.
            if len(loc[1]) < 1:
                region = "unknown"
            else:
                region = loc[1]

            foreign = True
            # if country field is empty, just set it to unknown.
            if len(loc[2]) < 1:
                country = "unknown"
            else:
                country = loc[2]

            foreign = True
            if country == home_country:
                foreign = False

            # print(loc, file=sys.stderr)
            location_type = loc[5]
            if "conflict" in location_type.lower():
                num_conflict_zones += 1
                if int(loc[6]) > 0:
                    location_type = "town"

            attributes = {}

            # Loading of static attributes.
            if len(loc) > 8:
                for i in range(8, len(loc)):
                    attributes[self.columns[i]] = loc[i]

            if "camp" in location_type.lower():
                lm[name] = e.addLocation(
                    name=name,
                    region=region,
                    location_type=location_type,
                    capacity=population,
                    x=x,
                    y=y,
                    foreign=foreign,
                    country=country,
                    attributes=attributes
                )
            else:
                lm[name] = e.addLocation(
                    name=name,
                    region=region,
                    location_type=location_type,
                    pop=population,
                    x=x,
                    y=y,
                    foreign=foreign,
                    country=country,
                    attributes=attributes
                )

        for link in self.links:
            attributes = {}
            if len(link) > 4:
                for i in range(4, len(link)):
                    attributes[self.link_columns[i]] = link[i]

            if len(link) > 3:
                l3 = link[3]
                if len(l3) == 0:
                    l3 = 0

                if int(l3) == 1:
                    e.linkUp(
                        endpoint1=link[0],
                        endpoint2=link[1],
                        distance=float(link[2]),
                        forced_redirection=True,
                        attributes=attributes,
                    )
                if int(l3) == 2:
                    e.linkUp(
                        endpoint1=link[1],
                        endpoint2=link[0],
                        distance=float(link[2]),
                        forced_redirection=True,
                        attributes=attributes,
                    )
                else:
                    e.linkUp(
                        endpoint1=link[0],
                        endpoint2=link[1],
                        distance=float(link[2]),
                        forced_redirection=False,
                        attributes=attributes,
                    )
            else:
                e.linkUp(
                    endpoint1=link[0],
                    endpoint2=link[1],
                    distance=float(link[2]),
                    forced_redirection=False,
                    attributes = {},
                )

        e.closures = []
        for link in self.closures:
            e.closures.append([link[0], link[1], link[2], int(link[3]), int(link[4])])

        if num_conflict_zones < 1:
            print(
                "Warning: location graph has 0 conflict zones (ignore if conflicts.csv is used).",
                file=sys.stderr,
            )

        return e, lm


    @check_args_type
    def UpdateLocationAttributes(self, e, attribute_name: str, time: int) -> None:
        """
        Summary: 
            Updates the attributes of a location.

        Args:
            e (Ecosystem): ecosystem object
            attribute_name (str): name of the attribute
            time (int): time step

        Returns:
            None.
        """
        # In DFlee attrlist is a dictionary of flood location names and their attributes
        #e.g {'F1': [0, 0, 1, 1, 2, 1, 1, 1, 1, 1, 1], 'F2': [1, 1, 1, 3, 1, 1, 0, 0, 0, 0, 1], 'F3': [0, 0, 0, 1, 1, 2, 3, 2, 1, 1, 0]}
        attrlist = self.attributes[attribute_name]

        # Get the length of the first array in attrlist 
        for key, value in attrlist.items():
            attrlength = int(len(value))
            break

        #Iterate through the locations and update their attributes
        for i in range(0, len(e.locations)):
            loc_name = e.locations[i].name
            
            #If the attibute has been specified by the input file: 
            if loc_name in attrlist:
                if attribute_name == "forecast_flood_levels":
                    #Set forecast_flood_levels attribute for flood_zones
                    e.locations[i].attributes[attribute_name] = attrlist[loc_name]
                else:
                    #Set flood_levels attribute for flood zones
                    e.locations[i].attributes[attribute_name] =int(attrlist[loc_name][time])
            else: 
                #If the location name is not in the attribute list, then set the attribute to default value of zero
                if attribute_name == "forecast_flood_levels":
                    #Set default forecast_flood_levels attribute to array of zeros for towns/camps
                    e.locations[i].attributes[attribute_name] = [0] * attrlength #array of zeros with length equal to the length of the first array in attrlist
                else:
                    #Set default flood_levels attribute to zero for towns/camps
                    e.locations[i].attributes[attribute_name] = 0
                
            # print(e.time, loc_name, e.locations[i].attributes, file=sys.stderr)


    @check_args_type
    def AddNewConflictZones(self, e, time: int, Debug: bool = False) -> None:
        """
        Summary:
            Adds new conflict zones according to information about the current time step.
            If there is no conflict input file, then the values from locations.csv are used.
            If there is one, then the data from it is used instead.
            Note: there is no support for *removing* conflict zones at this stage.

        Args:
            e (Ecosystem): ecosystem object
            time (int): time step
            Debug (bool, optional): debug flag. Defaults to False.

        Returns:
            None.
        """
        #Add New Flood Zones
        if SimulationSettings.move_rules["FloodRulesEnabled"] is True:
            #Current flood_level attribute is set to the flood level at the current time step specified in flood_level.csv. Default value is zero.
            self.UpdateLocationAttributes(e, "flood_level", time)
            if SimulationSettings.move_rules["FloodForecaster"] is True:
                #Store future flood levels in the forecast_flood_levels attribute. Default value is array of zeros.
                self.UpdateLocationAttributes(e, "forecast_flood_levels", time) 

        elif len(SimulationSettings.ConflictInputFile) == 0:
            for loc in self.locations:
                if "conflict" in loc[4].lower() and int(loc[5]) == time:
                    conflict_intensity = 1.0
                    if e.print_location_output:
                        print(
                            "Time = {}. Adding a new conflict zone [{}] with pop. {} and intensity {}".format(
                                time, loc[0], int(loc[1]), conflict_intensity
                            ),
                            file=sys.stderr,
                        )
                    e.add_conflict_zone(name=loc[0], conflict_intensity=conflict_intensity)
        else:
            conflict_names = self.getConflictLocationNames()
            # print(confl_names)


            for conflict_name in conflict_names:
                if len(self.conflicts[conflict_name]) < (time - 1):
                    print(f"Error: conflict value at time {time} requested, but the conflicts table for {conflict_name} only has values up to t = {len(conflicts[conflict_name])}.", file=sys.stderr)

                if Debug and e.getRankN(e.time) is True:
                    print("L:", conflict_name, self.conflicts[conflict_name], time, file=sys.stderr)
                if self.conflicts[conflict_name][time] > 0.000001:
                    if time > 0:
                        if self.conflicts[conflict_name][time - 1] < 0.000001:
                            if e.getRankN(e.time) is True:
                                print(
                                    "Time = {}. Adding a new conflict zone [{}] with intensity {}".format(
                                        time, conflict_name, self.conflicts[conflict_name][time]
                                    ),
                                    file=sys.stderr,
                                )
                            e.set_conflict_intensity(name=conflict_name, conflict_intensity=self.conflicts[conflict_name][time])
                    else:
                        if e.getRankN(e.time) is True:
                            print(
                                "Time = {}. Adding a new conflict zone [{}] with intensity {}".format(
                                    time, conflict_name, self.conflicts[conflict_name][time]
                                ),
                                file=sys.stderr,
                            )
                        e.add_conflict_zone(name=conflict_name, conflict_intensity=self.conflicts[conflict_name][time])
                if self.conflicts[conflict_name][time] < 0.000001 and time > 0:
                    if self.conflicts[conflict_name][time - 1] >= 0.000001:
                        if e.getRankN(e.time) is True:
                            print(
                                "Time = {}. Removing conflict zone [{}]".format(time, conflict_name),
                                file=sys.stderr,
                            )
                        e.set_conflict_intensity(name=conflict_name, conflict_intensity=self.conflicts[conflict_name][time])

