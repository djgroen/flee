import numpy as np
import sys
import random
from flee.SimulationSettings import SimulationSettings
from flee import pflee
# from flee import micro_flee as flee
from mpi4py import MPI
from mpi4py.MPI import ANY_SOURCE
import math
import datetime


class MPIManager(pflee.MPIManager):

    def __init__(self):
        super().__init__()


class Person(pflee.Person):

    def __init__(self, e, location):
        super().__init__(e, location)


class Location(pflee.Location):

    def __init__(self, e, cur_id, name, x=0.0, y=0.0, movechance=0.001, capacity=-1, pop=0, foreign=False, country="unknown"):
        super().__init__(e, cur_id, name, x, y, movechance, capacity, pop, foreign, country)


class Ecosystem(pflee.Ecosystem):

    def __init__(self):
        super().__init__()

    def linkUp(self, endpoint1, endpoint2, distance="1.0", forced_redirection=False, link_type=None):
        """ Creates a link between two endpoint locations
        """
        endpoint1_index = -1
        endpoint2_index = -1
        for i in range(0, len(self.locationNames)):
            if(self.locationNames[i] == endpoint1):
                endpoint1_index = i
            if(self.locationNames[i] == endpoint2):
                endpoint2_index = i

        if endpoint1_index < 0:
            print("Diagnostic: Ecosystem.locationNames: ", self.locationNames)
            print("Error: link created to non-existent source: ",
                  endpoint1, " with dest ", endpoint2)
            sys.exit()
        if endpoint2_index < 0:
            print("Diagnostic: Ecosystem.locationNames: ", self.locationNames)
            print("Error: link created to non-existent destination: ",
                  endpoint2, " with source ", endpoint1)
            sys.exit()

        self.locations[endpoint1_index].links.append(
            Link(self.locations[endpoint1_index],
                 self.locations[endpoint2_index],
                 distance,
                 forced_redirection,
                 link_type
                 )
        )
        self.locations[endpoint2_index].links.append(
            Link(
                self.locations[endpoint2_index],
                self.locations[endpoint1_index],
                distance
            )
        )


#-------------------------------------------------------------------------
#           modified version of class Link for weather coupling
#-------------------------------------------------------------------------
class Link(pflee.Link):

    def __init__(self, startpoint, endpoint, distance, forced_redirection=False, link_type=None):
        super().__init__(startpoint, endpoint, distance, forced_redirection)
        self.link_type = link_type

weather_source_files = {}


class Link_weather_coupling(pflee.Link):

    def __init__(self, startpoint, endpoint, distance, forced_redirection=False, link_type=None):
        self.name = "__link__"
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

        if self.link_type == 'crossing':
            self.discharge = weather_source_files['river_discharge']
            self.discharge_dict = self.discharge[
                ['lat', 'lon']].to_dict('records')
            self.closest_location = self.closest(self.discharge_dict,
                                                 {'lat': self.latMid, 'lon': self.lonMid})

            self.dl = self.discharge[
                (self.discharge['lat'] == self.closest_location['lat']) &
                (self.discharge['lon'] == self.closest_location['lon'])
            ]

    def DecrementNumAgents(self):
        self.numAgents -= 1

    def IncrementNumAgents(self):
        self.numAgents += 1

    def get_start_date(self, time):

        start_date = weather_source_files['conflict_start_date']
        date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
        date += datetime.timedelta(time)
        date = date.strftime('%Y-%m-%d')
        return date

    def midpoint(self):
        # This function returns the geoghraphical midpoint of two given
        # locations
        lat1 = math.radians(self.get_latitude(self.startpoint.name))
        lon1 = math.radians(self.get_longitude(self.startpoint.name))
        lat2 = math.radians(self.get_latitude(self.endpoint.name))
        lon2 = math.radians(self.get_longitude(self.endpoint.name))

        bx = math.cos(lat2) * math.cos(lon2 - lon1)
        by = math.cos(lat2) * math.sin(lon2 - lon1)
        latMid = math.atan2(math.sin(lat1) +
                            math.sin(lat2),
                            math.sqrt((math.cos(lat1) + bx) *
                                      (math.cos(lat1) + bx) +
                                      by**2)
                            )
        lonMid = lon1 + math.atan2(by, math.cos(lat1) + bx)

        latMid = round(math.degrees(latMid), 2)
        lonMid = round(math.degrees(lonMid), 2)

        latMid = float(round(latMid))
        lonMid = float(round(lonMid))

        return latMid, lonMid

    def get_longitude(self, location):

        # This function returns the longitude of given location based on 40
        # years dataset of South Sudan total precipitation
        history = weather_source_files['40yrs_total_precipitation']
        coordination = history[history["names"] == location]
        longitude = coordination["longitude"].mean()
        return longitude

    def get_latitude(self, location):

        # This function returns the latitude of given location based on 40
        # years dataset of South Sudan total precipitation
        history = weather_source_files['40yrs_total_precipitation']
        coordination = history[history["names"] == location]
        latitude = coordination["latitude"].mean()

        return latitude

    def X1_X2(self):

        # This function returns the two treshholds of X1 and X2.
        # The way of calculating threshholds needs to be discussed!
        # print(link)
        X1 = []
        X2 = []
        history = weather_source_files['40yrs_total_precipitation']
        latitude = history[history["latitude"] == self.latMid]

        if latitude.empty:
            result_index = history.iloc[
                (history["latitude"] - self.latMid).abs().argsort()[:1]]
            latitude_index = result_index["latitude"].to_numpy()
            latitude = history[history["latitude"] == float(latitude_index)]

        treshhold_tp = latitude[latitude["longitude"] == self.lonMid]

        if treshhold_tp.empty:
            result_index = latitude.iloc[
                (latitude["longitude"] - self.lonMid).abs().argsort()[:1]]
            longitude_index = result_index["longitude"].to_numpy()
            treshhold_tp = latitude[
                latitude["longitude"] == float(longitude_index)]

        X1 = treshhold_tp["tp"].quantile(q=0.15)
        X2 = treshhold_tp["tp"].quantile(q=0.75)

        return X1, X2

    def haversine_distance(self, lat1, lon1, lat2, lon2):
        p = 0.017453292519943295
        a = 0.5 - math.cos((lat2 - lat1) * p) / 2 + math.cos(lat1 * p) * \
            math.cos(lat2 * p) * (1 - math.cos((lon2 - lon1) * p)) / 2
        return 12742 * math.asin(math.sqrt(a))

    def closest(self, data, v):
        return min(data, key=lambda p: self.haversine_distance(v['lat'], v['lon'], p['lat'], p['lon']))

    def get_distance(self, time):
        if len(weather_source_files) == 0:
            print("Error !!! there is NO input file names for weather coupling")
            exit()
        else:
            date = self.get_start_date(time)

            df = weather_source_files['precipitation']
            columns = df.columns.values

            link_direct = self.startpoint.name + ' - ' + self.endpoint.name
            link_reverse = self.endpoint.name + ' - ' + self.startpoint.name
            '''
            for i in range(1, len(columns)):
                if (link_direct == columns[i] or link_reverse == columns[i]):
                    tp = df.loc[df.index[time], columns[i]]
            '''
            tp = df.loc[df.index[time], df.columns.isin(
                [link_direct, link_reverse])].values[0]

        if self.link_type == 'crossing':

            dis_level = self.dl[self.dl['time'] == date].iloc[0]['dis24']
            dis_threshold = 8000

            log_flag = False
            if dis_level < dis_threshold:
                new_distance = self.__distance * 1
            else:
                new_distance = self.__distance * 10000
                log_flag = True
        else:
            log_flag = False
            if tp <= self.X1:
                new_distance = self.__distance * 1
            elif tp <= self.X2:
                new_distance = self.__distance * 2
                log_flag = True
            elif tp > self.X2 and tp > 15:
                new_distance = self.__distance * 10000
                log_flag = True
            else:
                new_distance = self.__distance * 2
                log_flag = True

        '''
        if log_flag == True:
            log_file = weather_source_files['output_log']
            with open(log_file, 'a+') as f:
                f.write("day %d distance between %s - %s change from %f --> %f\n" %
                        (time, self.startpoint.name, self.endpoint.name, self.__distance, new_distance))
                f.flush()
        '''

        return new_distance


if __name__ == "__main__":
    print("No testing functionality here yet.")
