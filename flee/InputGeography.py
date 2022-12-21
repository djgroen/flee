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

    @check_args_type
    def ReadFlareConflictInputCSV(self, csv_name: str) -> None:
        """
        Reads a Flare input file, to set conflict information.

        Args:
            csv_name (str): Description
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
                        self.conflicts[headers[i]].append(int(row[i].strip()))
                row_count += 1

        # print(self.conflicts)
        # TODO: make test verifying this in test_csv.py

    @check_args_type
    def getConflictLocationNames(self) -> List[str]:
        """
        Summary

        Returns:
            List[str]: Description
        """
        if len(SimulationSettings.FlareConflictInputFile) == 0:
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

    def StoreInputGeographyInEcosystem(self, e):
        """
        Store the geographic information in this class in a FLEE simulation,
        overwriting existing entries.

        Args:
            e (Ecosystem): Description

        Returns:
            Tuple[Ecosystem, Dict]: Description
        """

        #0"name",1"region",2"country",3"gps_x",4"gps_y",5"location_type",6"conflict_date",7"pop/cap"


        lm = {}
        num_conflict_zones = 0
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

            # print(loc, file=sys.stderr)
            location_type = loc[5]
            if "conflict" in location_type.lower():
                num_conflict_zones += 1
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
    def AddNewConflictZones(self, e, time: int, Debug: bool = False) -> None:
        """
        Adds new conflict zones according to information about the current time step.
        If there is no Flare input file, then the values from locations.csv are used.
        If there is one, then the data from Flare is used instead.
        Note: there is no support for *removing* conflict zones at this stage.

        Args:
            e (Ecosystem): Description
            time (int): Description
            Debug (bool, optional): Description
        """
        if len(SimulationSettings.FlareConflictInputFile) == 0:
            for loc in self.locations:
                if "conflict" in loc[4].lower() and int(loc[5]) == time:
                    if e.print_location_output:
                        print(
                            "Time = {}. Adding a new conflict zone [{}] with pop. {}".format(
                                time, loc[0], int(loc[1])
                            ),
                            file=sys.stderr,
                        )
                    e.add_conflict_zone(name=loc[0])
        else:
            conflic_names = self.getConflictLocationNames()
            # print(confl_names)
            for conflic_name in conflic_names:
                if Debug:
                    print("L:", conflic_name, self.conflicts[conflic_name], time, file=sys.stderr)
                if self.conflicts[conflic_name][time] == 1:
                    if time > 0:
                        if self.conflicts[conflic_name][time - 1] == 0:
                            print(
                                "Time = {}. Adding a new conflict zone [{}]".format(
                                    time, conflic_name
                                ),
                                file=sys.stderr,
                            )
                            e.add_conflict_zone(name=conflic_name)
                    else:
                        print(
                            "Time = {}. Adding a new conflict zone [{}]".format(time, conflic_name),
                            file=sys.stderr,
                        )
                        e.add_conflict_zone(name=conflic_name)
                if self.conflicts[conflic_name][time] == 0 and time > 0:
                    if self.conflicts[conflic_name][time - 1] == 1:
                        print(
                            "Time = {}. Removing conflict zone [{}]".format(time, conflic_name),
                            file=sys.stderr,
                        )
                        e.remove_conflict_zone(name=conflic_name)
