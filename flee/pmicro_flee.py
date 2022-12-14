import datetime
import math
import os
import sys
from functools import wraps
from typing import Optional, Tuple

from flee import pflee
from flee.SimulationSettings import SimulationSettings  # noqa, pylint: disable=W0611

if os.getenv("FLEE_TYPE_CHECK") is not None and os.environ["FLEE_TYPE_CHECK"].lower() == "true":
    from beartype import beartype as check_args_type
else:

    def check_args_type(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper


class MPIManager(pflee.MPIManager):
    """
    The MPIManager class
    """

    def __init__(self):
        super().__init__()


class Person(pflee.Person):
    """
    The Person class
    """

    def __init__(self, e, location):
        super().__init__(e, location)


class Location(pflee.Location):
    """
    The Location class
    """

    @check_args_type
    def __init__(
        self,
        e,
        cur_id: int,
        name: str,
        x: float = 0.0,
        y: float = 0.0,
        location_type: Optional[str] = None,
        movechance: float = 0.001,
        capacity: int = -1,
        pop: int = 0,
        foreign: bool = False,
        country: str = "unknown",
    ) -> None:
        super().__init__(
            e=e,
            cur_id=cur_id,
            name=name,
            x=x,
            y=y,
            location_type=location_type,
            movechance=movechance,
            capacity=capacity,
            pop=pop,
            foreign=foreign,
            country=country,
        )


class Ecosystem(pflee.Ecosystem):
    """
    The Ecosystem class
    """

    def __init__(self):
        super().__init__()

    @check_args_type
    def linkUp(
        self,
        endpoint1: str,
        endpoint2: str,
        distance: float = 1.0,
        forced_redirection: bool = False,
        link_type: str = None,
    ) -> None:
        """
        Creates a link between two endpoint locations

        Args:
            endpoint1 (str): Description
            endpoint2 (str): Description
            distance (float, optional): Description
            forced_redirection (bool, optional): Description
            link_type (str, optional): Description
        """
        endpoint1_index = -1
        endpoint2_index = -1
        for i, location_name in enumerate(self.locationNames):
            if location_name == endpoint1:
                endpoint1_index = i
            if location_name == endpoint2:
                endpoint2_index = i

        if endpoint1_index < 0:
            print("Diagnostic: Ecosystem.locationNames: ", self.locationNames)
            print(
                "Error: link created to non-existent source: {} with dest {}".format(
                    endpoint1, endpoint2
                )
            )
            sys.exit()
        if endpoint2_index < 0:
            print("Diagnostic: Ecosystem.locationNames: ", self.locationNames)
            print(
                "Error: link created to non-existent destination: {} with source {}".format(
                    endpoint2, endpoint1
                )
            )
            sys.exit()

        self.locations[endpoint1_index].links.append(
            Link(
                startpoint=self.locations[endpoint1_index],
                endpoint=self.locations[endpoint2_index],
                distance=distance,
                forced_redirection=forced_redirection,
                link_type=link_type,
            )
        )
        self.locations[endpoint2_index].links.append(
            Link(
                startpoint=self.locations[endpoint2_index],
                endpoint=self.locations[endpoint1_index],
                distance=distance,
            )
        )


# -------------------------------------------------------------------------
#           modified version of class Link for weather coupling
# -------------------------------------------------------------------------
class Link(pflee.Link):
    """
    the Link class
    """

    @check_args_type
    def __init__(
        self,
        startpoint,
        endpoint,
        distance: float,
        forced_redirection: bool = False,
        link_type: str = None,
    ):
        super().__init__(startpoint, endpoint, distance, forced_redirection)
        self.link_type = link_type


weather_source_files = {}


class Link_weather_coupling(pflee.Link):
    """
    the Link_weather_coupling class
    """

    @check_args_type
    def __init__(
        self,
        startpoint,
        endpoint,
        distance: float,
        forced_redirection: bool = False,
        link_type: Optional[str] = None,
    ):
        self.name = "L:{}:{}".format(startpoint.name, endpoint.name)
        self.closed = False

        # distance in km.
        self.__distance = float(distance)

        # links for now always connect two endpoints
        self.startpoint = startpoint
        self.endpoint = endpoint

        # number of agents that are in transit.
        self.numAgents = 0
        # refugee population on current rank (for pflee).
        self.numAgentsOnRank = 0

        # if True, then all Persons will go down this link.
        self.forced_redirection = forced_redirection

        self.link_type = link_type

        self.latMid, self.lonMid = self.midpoint()
        self.X1, self.X2 = self.X1_X2()

        df = weather_source_files["precipitation"]
        link_direct = self.startpoint.name + " - " + self.endpoint.name
        link_reverse = self.endpoint.name + " - " + self.startpoint.name
        self.prec = df.loc[:, df.columns.isin([link_direct, link_reverse])]

        if self.link_type == "crossing":
            self.discharge = weather_source_files["river_discharge"]
            self.discharge_dict = self.discharge[["lat", "lon"]].to_dict("records")
            self.closest_location = self.closest(
                data=self.discharge_dict, v={"lat": self.latMid, "lon": self.lonMid}
            )

            self.dl = self.discharge[
                (self.discharge["lat"] == self.closest_location["lat"])
                & (self.discharge["lon"] == self.closest_location["lon"])
            ]

    def DecrementNumAgents(self):
        """
        Summary
        """
        self.numAgents -= 1

    def IncrementNumAgents(self):
        """
        Summary
        """
        self.numAgents += 1

    @check_args_type
    def get_start_date(self, time: int):
        """
        Summary

        Args:
            time (TYPE): Description

        Returns:
            TYPE: Description
        """
        start_date = weather_source_files["conflict_start_date"]
        date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
        date += datetime.timedelta(time)
        date = date.strftime("%Y-%m-%d")
        return date

    @check_args_type
    def midpoint(self) -> Tuple[float, float]:
        """
        This function returns the geoghraphical midpoint of two given locations

        Returns:
            Tuple[float, float]: Description
        """
        lat1 = math.radians(self.get_latitude(location_name=self.startpoint.name))
        lon1 = math.radians(self.get_longitude(location_name=self.startpoint.name))
        lat2 = math.radians(self.get_latitude(location_name=self.endpoint.name))
        lon2 = math.radians(self.get_longitude(location_name=self.endpoint.name))

        bx = math.cos(lat2) * math.cos(lon2 - lon1)
        by = math.cos(lat2) * math.sin(lon2 - lon1)
        latMid = math.atan2(
            math.sin(lat1) + math.sin(lat2),
            math.sqrt((math.cos(lat1) + bx) * (math.cos(lat1) + bx) + by ** 2),
        )
        lonMid = lon1 + math.atan2(by, math.cos(lat1) + bx)

        latMid = round(math.degrees(latMid), 2)
        lonMid = round(math.degrees(lonMid), 2)

        latMid = float(round(latMid))
        lonMid = float(round(lonMid))

        return latMid, lonMid

    @check_args_type
    def get_longitude(self, location_name: str) -> float:
        """
        This function returns the longitude of given location name based on 40 years dataset of
        South Sudan total precipitation

        Args:
            location_name (str): Description

        Returns:
            float: Description
        """
        history = weather_source_files["40yrs_total_precipitation"]
        coordination = history[history["names"] == location_name]
        longitude = coordination["longitude"].mean()
        return longitude

    @check_args_type
    def get_latitude(self, location_name: str) -> float:
        """
        This function returns the latitude of given location name based on 40 years dataset of
        South Sudan total precipitation

        Args:
            location_name (str): Description

        Returns:
            float: Description
        """
        history = weather_source_files["40yrs_total_precipitation"]
        coordination = history[history["names"] == location_name]
        latitude = coordination["latitude"].mean()

        return latitude

    @check_args_type
    def X1_X2(self) -> Tuple[float, float]:
        """
        This function returns the two treshholds of X1 and X2.
        The way of calculating threshholds needs to be discussed!

        Returns:
            Tuple[float, float]: Description
        """
        # print(link)
        X1 = []
        X2 = []
        history = weather_source_files["40yrs_total_precipitation"]
        latitude = history[history["latitude"] == self.latMid]

        if latitude.empty:
            result_index = history.iloc[(history["latitude"] - self.latMid).abs().argsort()[:1]]
            latitude_index = result_index["latitude"].to_numpy()
            latitude = history[history["latitude"] == float(latitude_index)]

        treshhold_tp = latitude[latitude["longitude"] == self.lonMid]

        if treshhold_tp.empty:
            result_index = latitude.iloc[(latitude["longitude"] - self.lonMid).abs().argsort()[:1]]
            longitude_index = result_index["longitude"].to_numpy()
            treshhold_tp = latitude[latitude["longitude"] == float(longitude_index)]

        X1 = treshhold_tp["tp"].quantile(q=0.15)
        X2 = treshhold_tp["tp"].quantile(q=0.75)

        return X1, X2

    @check_args_type
    def haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Summary

        Args:
            lat1 (float): Description
            lon1 (float): Description
            lat2 (float): Description
            lon2 (float): Description

        Returns:
            float: Description
        """
        p = 0.017453292519943295
        a = (
            0.5
            - math.cos((lat2 - lat1) * p) / 2
            + math.cos(lat1 * p) * math.cos(lat2 * p) * (1 - math.cos((lon2 - lon1) * p)) / 2
        )
        return 12742 * math.asin(math.sqrt(a))

    def closest(self, data, v):
        """
        Summary

        Args:
            data (TYPE): Description
            v (TYPE): Description

        Returns:
            TYPE: Description
        """
        return min(
            data,
            key=lambda p: self.haversine_distance(
                lat1=v["lat"], lon1=v["lon"], lat2=p["lat"], lon2=p["lon"]
            ),
        )

    @check_args_type
    def get_distance(self, time: int) -> float:
        """
        Summary

        Args:
            time (int): Description

        Returns:
            TYPE: Description
        """
        if len(weather_source_files) == 0:
            print("Error!!! there is NO input file names for weather coupling")
            sys.exit()

        elif self.link_type == "crossing":
            date = self.get_start_date(time=time)
            dis_level = self.dl[self.dl["time"] == date].iloc[0]["dis24"]
            dis_threshold = 8000

            # log_flag = False
            if dis_level < dis_threshold:
                new_distance = self.__distance * 1
            else:
                new_distance = self.__distance * 10000
                # log_flag = True
        else:
            # log_flag = False
            tp = self.prec.loc[self.prec.index[time]].values[0]
            if tp <= self.X1:
                new_distance = self.__distance * 1
            elif tp <= self.X2:
                new_distance = self.__distance * 2
                # log_flag = True
            elif tp > self.X2 and tp > 15:
                new_distance = self.__distance * 10000
                # log_flag = True
            else:
                new_distance = self.__distance * 2
                # log_flag = True

        """
        if log_flag is True:
            log_file = weather_source_files["output_log"]
            with open(log_file, "a+") as f:
                f.write(
                    "day {} distance between {} - {} "
                    "change from {} --> {}\n".format(
                        time, self.startpoint.name,
                        self.endpoint.name, self.__distance, new_distance
                    )
                )
                f.flush()
        """

        return new_distance


if __name__ == "__main__":
    print("No testing functionality here yet.")
