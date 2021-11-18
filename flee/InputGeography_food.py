import csv
import sys
# from flee import flee
# from flee import SimulationSettings


class InputGeography:
    """
    Class which reads in Geographic information.
    """

    def __init__(self):
        self.locations = []
        self.links = []

    def ReadLocationsFromCSV(self, csv_name,
                             columns=["name", "region", "country", "gps_x", "gps_y",
                                      "location_type", "conflict_date", "pop/cap"]
                             ):
        """
        Converts a CSV file to a locations information table
        """
        self.locations = []

        c = {}  # column map

        c["location_type"] = 0
        c["conflict_date"] = 0
        c["country"] = 0
        c["region"] = 0

        for i, name in enumerate(columns):
            c[name] = i

        with open(csv_name, newline="", encoding="utf-8") as csvfile:
            values = csv.reader(csvfile)

            for row in values:
                if row[0][0] == "#":
                    pass
                else:
                    # print(row)
                    self.locations.append(
                        [
                            row[c["name"]],
                            row[c["pop/cap"]],
                            row[c["gps_x"]],
                            row[c["gps_y"]],
                            row[c["location_type"]],
                            row[c["conflict_date"]],
                            row[c["region"]],
                            row[c["country"]],
                        ]
                    )

    def ReadLinksFromCSV(self, csv_name, name1_col=0, name2_col=1, dist_col=2):
        """
        Converts a CSV file to a locations information table
        """
        self.links = []

        with open(csv_name, newline="", encoding="utf-8") as csvfile:
            values = csv.reader(csvfile)

            for row in values:
                if row[0][0] == "#":
                    pass
                else:
                    # print(row)
                    self.links.append(
                        [row[name1_col], row[name2_col], row[dist_col]])

    def ReadClosuresFromCSV(self, csv_name):
        """
        Read the closures.csv file. Format is:
        closure_type,name1,name2,closure_start,closure_end
        """
        self.closures = []

        with open(csv_name, newline="", encoding="utf-8") as csvfile:
            values = csv.reader(csvfile)

            for row in values:
                if row[0][0] == "#":
                    pass
                else:
                    # print(row)
                    self.closures.append(row)

    def StoreInputGeographyInEcosystem(self, e):
        """
        Store the geographic information in this class in a FLEE simulation,
        overwriting existing entries.
        """
        lm = {}

        for loc in self.locations:
            # if population field is empty, just set it to 0.
            if len(loc[1]) < 1:
                loc[1] = "0"
            # if population field is empty, just set it to 0.
            if len(loc[7]) < 1:
                loc[7] = "unknown"

            # print(loc, file=sys.stderr)
            location_type = loc[4]
            if "conflict" in location_type.lower() and int(loc[5]) > 0:
                location_type = "town"

            if "camp" in loc[4].lower():
                lm[loc[0]] = e.addLocation(loc[0], location_type=location_type, capacity=int(
                    loc[1]), x=loc[2], y=loc[3], country=loc[7], region=loc[6])
            else:
                lm[loc[0]] = e.addLocation(loc[0], location_type=location_type, pop=int(
                    loc[1]), x=loc[2], y=loc[3], country=loc[7], region=loc[6])

        for link in self.links:
            if len(link) > 3:
                if int(link[3]) == 1:
                    e.linkUp(link[0], link[1], int(link[2]), True)
                if int(link[3]) == 2:
                    e.linkUp(link[1], link[0], int(link[2]), True)
                else:
                    e.linkUp(link[0], link[1], int(link[2]), False)
            else:
                e.linkUp(link[0], link[1], int(link[2]), False)

        e.closures = []
        for link in self.closures:
            e.closures.append([link[0], link[1], link[2], int(link[3]), int(link[4])])

        return e, lm

    def AddNewConflictZones(self, e, time):
        """
        Summary
        """
        for loc in self.locations:
            if "conflict" in loc[4].lower() and int(loc[5]) == time:
                print("Time = %s. Adding a new conflict zone [%s]" % (
                    time, loc[0]), file=sys.stderr)
                e.add_conflict_zone(name=loc[0])
