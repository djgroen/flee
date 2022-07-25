import csv
import os
import sys
from functools import wraps

# from flee import flee
from flee.InputGeography import InputGeography as based_InputGeography_class
from flee.SimulationSettings import SimulationSettings

if os.getenv("FLEE_TYPE_CHECK") is not None and os.environ["FLEE_TYPE_CHECK"].lower() == "true":
    from beartype import beartype as check_args_type
else:

    def check_args_type(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper


class InputGeography(based_InputGeography_class):
    """
    Class which reads in Geographic information.
    """

    def __init__(self):
        super().__init__()

    @check_args_type
    def ReadLinksFromCSV(
        self,
        csv_name: str,
        name1_col: int = 0,
        name2_col: int = 1,
        dist_col: int = 2,
        forced_redirection: int = 3,
        link_type_col: int = 4,
    ) -> None:
        """
        Converts a CSV file to a locations information table

        Args:
            csv_name (str): Description
            name1_col (int, optional): Description
            name2_col (int, optional): Description
            dist_col (int, optional): Description
            forced_redirection (int, optional): Description
            link_type_col (int, optional): Description
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
                        [
                            row[name1_col],
                            row[name2_col],
                            row[dist_col],
                            row[forced_redirection],
                            row[link_type_col],
                        ]
                    )

        """
        if isinstance(row[link_type_col], str):
            if "drive" in row[link_type_col].lower():
                flee.SimulationSettings.move_rules["MaxMoveSpeed"] = flee.SimulationSettings.move_rules["MaxMoveSpeed"]
            elif "walk" in row[link_type_col].lower():
                flee.SimulationSettings.move_rules["MaxMoveSpeed"] = flee.SimulationSettings.MaxWalkSpeed
            elif "crossing" in row[link_type_col].lower():
                flee.SimulationSettings.move_rules["MaxMoveSpeed"] = flee.SimulationSettings.move_rules["MaxCrossingSpeed"]
            else:
                print(
                    "Error in identifying link_type() object: cannot parse the type of link {}"
                    " {} for location object with name.".format(link_type_col, name1_col)
                )
                sys.exit()
        """

    @check_args_type
    def StoreInputGeographyInEcosystem(self, e):
        """
        Store the geographic information in this class in a FLEE simulation,
        overwriting existing entries.

        Args:
            e (Ecosystem): Description

        Returns:
            Tuple[Ecosystem, Dict]: Description
        """
        lm = {}
        num_conflict_zones = 0

        for loc in self.locations:
            name = loc[0]

            # if population field is empty, just set it to 0.
            if len(loc[1]) < 1:
                population = 0
            else:
                population = int(loc[1]) // SimulationSettings.optimisations["PopulationScaleDownFactor"]

            x = float(loc[2]) if len(loc[2]) > 0 else 0.0
            y = float(loc[3]) if len(loc[3]) > 0 else 0.0

            # if population field is empty, just set it to 0.
            if len(loc[7]) < 1:
                country = "unknown"
            else:
                country = loc[7]

            # print(loc, file=sys.stderr)
            location_type = loc[4]
            if "conflict" in location_type.lower():
                num_conflict_zones += 1
                if int(loc[5]) > 0:
                    location_type = "town"

            if "camp" in loc[4].lower():
                lm[name] = e.addLocation(
                    name=name,
                    location_type=location_type,
                    capacity=population,
                    x=x,
                    y=y,
                    country=country,
                )
            else:
                lm[name] = e.addLocation(
                    name=name,
                    location_type=location_type,
                    pop=population,
                    x=x,
                    y=y,
                    country=country,
                )

        for link in self.links:
            if len(link) > 4:
                if int(link[3]) == 1:
                    e.linkUp(
                        endpoint1=link[0],
                        endpoint2=link[1],
                        distance=float(link[2]),
                        forced_redirection=True,
                        link_type=str(link[4]),
                    )
                if int(link[3]) == 2:
                    e.linkUp(
                        endpoint1=link[1],
                        endpoint2=link[0],
                        distance=float(link[2]),
                        forced_redirection=True,
                        link_type=str(link[4]),
                    )
                else:
                    e.linkUp(
                        endpoint1=link[0],
                        endpoint2=link[1],
                        distance=float(link[2]),
                        forced_redirection=False,
                        link_type=str(link[4]),
                    )
            else:
                e.linkUp(
                    endpoint1=link[0],
                    endpoint2=link[1],
                    distance=float(link[2]),
                    forced_redirection=False,
                    link_type=str(link[4]),
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
