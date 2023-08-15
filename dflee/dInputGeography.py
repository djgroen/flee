import csv
import os
import sys
from typing import List

from dflee.SimulationSettings import SimulationSettings

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
        self.floods = {}

    @check_args_type
    def ReadFloodInputCSV(self, csv_name: str) -> None:
        """
        Reads a Flood input file, to set flood information.

        Args:
            csv_name (str): Description
        """
        self.floods = {}

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
                            self.floods[headers[i]] = []
                else:
                    for i in range(1, len(row)):  # field 0 is day.
                        # print(row[0])
                        self.floods[headers[i]].append(int(row[i].strip()))
                row_count += 1

        # print(self.floods)
        # TODO: make test verifying this in test_csv.py

    @check_args_type
    def getFloodLocationNames(self) -> List[str]:
        """
        Summary

        Returns:
            List[str]: Description
        """
        if len(SimulationSettings.FloodInputFile) == 0:
            flood_names = []
            for loc in self.locations:
                if "flood" in loc[4].lower():
                    flood_names += [loc[0]]
            print(flood_names, file=sys.stderr)
            return flood_names

        return list(self.floods.keys())

    @check_args_type
    def ReadLocationsFromCSV(self, csv_name: str) -> None:
        """
        Converts a CSV file to a locations information table

        Args:
            csv_name (str): Description
        """
        self.locations = []

        c = {}  # column map

        columns = [
            "name",
            "region",
            "country",
            "gps_x",
            "gps_y",
            "location_type",
            "flood_date",
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
        loc_list = {}
        for l in self.locations:
            loc_list[l[0]] = [float(l[3]),float(l[4])]
        return loc_list

    @check_args_type
    def ReadLinksFromCSV(self, csv_name: str) -> None:
        """
        Converts a CSV file to a locations information table

        Args:
            csv_name (str): Description
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
                    pass
                else:
                    # print(row)
                    self.links.append(row)

    @check_args_type
    def ReadClosuresFromCSV(self, csv_name: str) -> None:
        """
        Read the closures.csv file. Format is:
        closure_type,name1,name2,closure_start,closure_end

        Args:
            csv_name (str): Description
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
        Read the agents.csv file. Format is:
        location,attributes

        Args:
            csv_name (str): Description
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
        Store the geographic information in this class in a FLEE simulation,
        overwriting existing entries.

        Args:
            e (Ecosystem): Description

        Returns:
            Tuple[Ecosystem, Dict]: Description
        """

        #0"name",1"region",2"country",3"gps_x",4"gps_y",5"location_type",6"flood_date",7"pop/cap"


        lm = {}
        num_flood_zones = 0

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
                population = int(int(loc[7]) // SimulationSettings.optimisations["PopulationScaleDownFactor"])

            x = float(loc[3]) if len(loc[3]) > 0 else 0.0
            y = float(loc[4]) if len(loc[4]) > 0 else 0.0

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
            if "flood" in location_type.lower():
                num_flood_zones += 1
                if int(loc[6]) > 0:
                    location_type = "town"

            attributes = {}
            if len(loc) > 8:
                for i in range(8, len(loc)):
                    attributes[self.columns[i]] = loc[i]

            if "camp" in location_type.lower():
                lm[name] = e.addLocation(
                    name=name,
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
                        link_type=link[4],
                        attributes=attributes,
                    )
                if int(l3) == 2:
                    #print("CHECK2")
                    e.linkUp(
                        endpoint1=link[1],
                        endpoint2=link[0],
                        distance=float(link[2]),
                        forced_redirection=True,
                        link_type=link[4],
                        attributes=attributes,
                    )
                else:
                    #print('CHECK2')
                    if link[4] == 'walk':
                        SimulationSettings.move_rules["StartOnFoot"] = True
                    else:
                        SimulationSettings.move_rules["StartOnFoot"] = False
                    e.linkUp(
                        endpoint1=link[0],
                        endpoint2=link[1],
                        distance=float(link[2]),
                        forced_redirection=False,
                        link_type=link[4],
                        attributes=attributes,
                    )
            else:
                e.linkUp(
                    endpoint1=link[0],
                    endpoint2=link[1],
                    distance=float(link[2]),
                    forced_redirection=False,
                    link_type=link[4],
                    attributes = {},
                )

        e.closures = []
        for link in self.closures:
            e.closures.append([link[0], link[1], link[2], int(link[3]), int(link[4])])

        if num_flood_zones < 1:
            print(
                "Warning: location graph has 0 flood zones (ignore if floods.csv is used).",
                file=sys.stderr,
            )

        return e, lm

    @check_args_type
    def AddNewFloodZones(self, e, time: int, Debug: bool = False) -> None:
        """
        Adds new flood zones according to information about the current time step.
        If there is no Flood input file, then the values from locations.csv are used.
        If there is one, then the data from Floos is used instead.
        Note: there is no support for *removing* flood zones at this stage.

        Args:
            e (Ecosystem): Description
            time (int): Description
            Debug (bool, optional): Description
        """
        if len(SimulationSettings.FloodInputFile) == 0:
            for loc in self.locations:
                if "flood" in loc[4].lower() and int(loc[5]) == time:
                    flood_level = 1.0
                    if e.print_location_output:
                        print(
                            "Time = {}. Adding a new flood zone [{}] with pop: {} and flood level: {}".format(
                                time, loc[0], int(loc[1], flood_level)
                            ),
                            file=sys.stderr,
                        )
                    e.add_flood_zone(name=loc[0], flood_level=flood_level)
        else:
            flood_names = self.getFloodLocationNames()
            for flood_name in flood_names:
                flood_level = self.floods[flood_name][time]

                if Debug:
                    print("L:", flood_name, self.floods[flood_name], time, file=sys.stderr)
                if self.floods[flood_name][time] >= 1:
                    if time > 0:
                        if self.floods[flood_name][time - 1] == 0:
                            print(
                                "Time = {}. Adding a new flood zone (level {}) [{}]".format(
                                    time, flood_level, flood_name
                                ),
                                file=sys.stderr,
                            )
                            e.add_flood_zone(name=flood_name, flood_level=flood_level)
                    else:
                        print(
                            "Time = {}. Adding a new flood zone (level {}) [{}]".format(time, flood_level, flood_name),
                            file=sys.stderr,
                        )
                        e.add_flood_zone(name=flood_name, flood_level=flood_level)
                if self.floods[flood_name][time] == 0 and time > 0:
                    if self.floods[flood_name][time - 1] == 1:
                        print(
                            "Time = {}. Removing flood zone (level {}) [{}]".format(time, flood_level, flood_name),
                            file=sys.stderr,
                        )
                        e.remove_flood_zone(name=flood_name)
