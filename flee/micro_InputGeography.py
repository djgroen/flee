import csv
import sys
from flee import flee
from flee import SimulationSettings
from flee import InputGeography


class InputGeography(InputGeography.InputGeography):
    """
    Class which reads in Geographic information.
    """

    def __init__(self):
        super().__init__()

    def ReadLinksFromCSV(self, csv_name, name1_col=0, name2_col=1, dist_col=2, forced_redirection=3, link_type_col=4):
        """
        Converts a CSV file to a locations information table
        """
        self.links = []

        with open(csv_name, newline='') as csvfile:
            values = csv.reader(csvfile)

            for row in values:
                if row[0][0] == "#":
                    pass
                else:
                    # print(row)
                    self.links.append([row[name1_col], row[name2_col], row[dist_col], row[
                                      forced_redirection], row[link_type_col]])

        if isinstance(row[link_type_col], str):
            if "drive" in row[link_type_col].lower():
                flee.SimulationSettings.MaxMoveSpeed = flee.SimulationSettings.MaxMoveSpeed
            elif "walk" in row[link_type_col].lower():
                flee.SimulationSettings.MaxMoveSpeed = flee.SimulationSettings.MaxWalkSpeed
            elif "crossing" in row[link_type_col].lower():
                flee.SimulationSettings.MaxMoveSpeed = flee.SimulationSettings.MaxCrossingSpeed
            else:
                print("Error in identifying link_type() object: cannot parse the type of link ",
                      link_type_col, " for location object with name ", name1_col, ".")

    def StoreInputGeographyInEcosystem(self, e):
        """
        Store the geographic information in this class in a FLEE simulation,
        overwriting existing entries.
        """
        lm = {}
        num_conflict_zones = 0

        for l in self.locations:
            # if population field is empty, just set it to 0.
            if len(l[1]) < 1:
                l[1] = "0"
            # if population field is empty, just set it to 0.
            if len(l[7]) < 1:
                l[7] = "unknown"

            #print(l, file=sys.stderr)
            movechance = l[4]
            if "conflict" in l[4].lower():
                num_conflict_zones += 1
                if int(l[5]) > 0:
                    movechance = "town"

            if "camp" in l[4].lower():
                lm[l[0]] = e.addLocation(l[0], movechance=movechance, capacity=int(
                    l[1]), x=l[2], y=l[3], country=l[7])
            else:
                lm[l[0]] = e.addLocation(l[0], movechance=movechance, pop=int(
                    l[1]), x=l[2], y=l[3], country=l[7])

        for l in self.links:
            if (len(l) > 4):
                if int(l[3]) == 1:
                    e.linkUp(l[0], l[1], int(l[2]), True, str(l[4]))
                if int(l[3]) == 2:
                    e.linkUp(l[1], l[0], int(l[2]), True, str(l[4]))
                else:
                    e.linkUp(l[0], l[1], int(l[2]), False, str(l[4]))
            else:
                e.linkUp(l[0], l[1], int(l[2]), False, str(l[4]))

        e.closures = []
        for l in self.closures:
            e.closures.append([l[0], l[1], l[2], int(l[3]), int(l[4])])

        if num_conflict_zones < 1:
            print("Warning: location graph has 0 conflict zones (ignore if conflicts.csv is used).", file=sys.stderr)

        return e, lm
