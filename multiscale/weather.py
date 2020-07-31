import os
import sys
import csv
import math
import numpy as np
import pandas as pd
import datetime
import argparse
from flee.datamanager import read_period

#in order to run weather.py individually, just run python3 weather.py --input_dir ssudan-mscale-test
#otherwise, it can be executed by enabling the --weather_coupling flag to True in run_file_coupling.sh

parser = argparse.ArgumentParser()

parser.add_argument('--input_dir', required=True,
                    action="store", type=str,
                    help="the input data directory")

args, unknown = parser.parse_known_args()

print("args: {}".format(args), file=sys.stderr)

work_dir = os.path.dirname(os.path.abspath(__file__))

input_dir = os.path.join(work_dir, args.input_dir)

data_dir = os.path.join(input_dir, 'weather_data')

history = pd.read_csv("%s/40yrs_tp.csv" %(data_dir), sep=',', encoding='latin1')

daily=pd.read_csv("%s/daily_tp.csv" %(data_dir), sep=',', encoding='latin1')

def X1_X2(link,date):

#This function returns the two treshholds of X1 and X2.
#The way of calculating threshholds needs to be discussed!

    X1 = []
    X2 = []
    latMid, lonMid = midpoint(link, date)

    latitude = history[history["latitude"]==latMid]

    if latitude.empty:
        result_index = history.iloc[(history["latitude"]-latMid).abs().argsort()[:1]]
        latitude_index = result_index["latitude"].to_numpy()
        latitude = history[history["latitude"]==float(latitude_index)]

    treshhold_tp = latitude[latitude["longitude"]==lonMid]

    if treshhold_tp.empty:
        result_index = latitude.iloc[(latitude["longitude"]-lonMid).abs().argsort()[:1]]
        longitude_index = result_index["longitude"].to_numpy()
        treshhold_tp = latitude[latitude["longitude"]==float(longitude_index)]

    X1 = treshhold_tp["tp"].quantile(q=0.15)
    X2 = treshhold_tp["tp"].quantile(q=0.75)

    return X1, X2


def latitude(location):
    
#This function returns the latitude of given location based on 40 years dataset of South Sudan total precipitation

    coordination = history[history["names"]==location]
    latitude = coordination["latitude"].mean()

    return latitude

def longitude(location):

#This function returns the longitude of given location based on 40 years dataset of South Sudan total precipitation

    coordination = history[history["names"]==location]
    longitude = coordination["longitude"].mean()
    return longitude

def midpoint(link, date):

#This function returns the geoghraphical midpoint of two given locations

    lat1 = math.radians(latitude(link[0]))
    lon1 = math.radians(longitude(link[0]))
    lat2 = math.radians(latitude(link[1]))
    lon2 = math.radians(longitude(link[1]))

    bx = math.cos(lat2) * math.cos(lon2 - lon1)
    by = math.cos(lat2) * math.sin(lon2 - lon1)
    latMid = math.atan2(math.sin(lat1) + math.sin(lat2), math.sqrt((math.cos(lat1) + bx) * (math.cos(lat1) + bx) + by**2))
    lonMid = lon1 + math.atan2(by, math.cos(lat1) + bx)

    latMid = round(math.degrees(latMid), 2)
    lonMid = round(math.degrees(lonMid), 2)

    latMid = float(round(latMid))
    lonMid = float(round(lonMid))

    return latMid, lonMid

def midpoint_tp(link, date):

#This function returns the total precipitation level of the midpoint

    latMid, lonMid = midpoint(link, date)

    sim_date = daily[daily["time"]==date]
    midpoint_latitude = sim_date[sim_date["latitude"]==latMid]
    midpoint_longitude = midpoint_latitude[midpoint_latitude["longitude"]==lonMid]
    midpoint_tp = midpoint_longitude["tp"].to_numpy()

    return midpoint_tp


def return_date(link):

#This function returns the date of given link based on routes_tp.csv which has created manually and needs to be created automatically!

    start_date, end_time = read_period.read_conflict_period(
        os.path.join(input_dir, "conflict_period.csv"))    

    date_1 = datetime.datetime.strptime(start_date, '%Y-%m-%d')

    links=pd.read_csv("{}/links-tp.csv".format(data_dir),sep=',', encoding='latin1')

    links['date'] = date_1 + links['date'].map(datetime.timedelta)

    source = links[links['source']==link[0]]
    destination = source[source['destination']==link[1]]
    date = destination['date']

    return date.to_string(index=False)


def generate_routes_m_file(name1_col=0, name2_col=1, dist_col=2, forced_redirection=3, link_type_col=4):

#This function creates the routes_m.csv file which will be used as a new routes file for micro model while the weather_coupling flag set to True!
    routes = []
    with open("{}/routes-1.csv".format(data_dir), newline='') as csvfile:
            values = csv.reader(csvfile)

            for row in values:
                if row[0][0] == "#":
                    routes.append([row[name1_col], row[name2_col], row[dist_col], row[
                                              forced_redirection], row[link_type_col]])
                else:
                    if row[link_type_col] != "crossing":

                        routes_revised=list([row[name1_col], row[name2_col]])


                        date = return_date(routes_revised)

                        multiplier = distance_change(routes_revised,date)   
                        
                        if multiplier != 0:

                            row[dist_col] = multiplier*(int(row[dist_col]))

                            routes.append([row[name1_col], row[name2_col], row[dist_col], row[
                                              forced_redirection], row[link_type_col]])
                    else:
                        routes_revised=list([row[name1_col], row[name2_col]])
                        date = return_date(routes_revised)
                        multiplier = distance_change(routes_revised,date)   

                        if multiplier == 1:
                            routes.append([row[name1_col], row[name2_col], row[dist_col], row[
                                              forced_redirection], row[link_type_col]])

    routes_df = pd.DataFrame(routes)

    routes_df.to_csv("{}/routes-m.csv".format(data_dir), index=False, header=False)

    print("The new routes file is stored in {}/routes-m.csv".format(data_dir))


def distance_change(link, date, **kwargs):

#This function returns the multiplier in order to change the distance of locations in generate_routes_m_file() function!

    X1, X2=X1_X2(link,date)
    '''
    print("******************line1**************************")
    print("link={}".format(link))
    print("date={}".format(date))
    print("midpoint_tp={}".format(midpoint_tp(link, date)))
    print("X1={}".format(X1))
    print("X2={}".format(X2))
    print("******************line2**************************")
    '''

    if midpoint_tp(link, date) <= X1:
        #print("Normal")
        return 1
    elif midpoint_tp(link, date) <= X2:
        #print("Doubled")
        return 2
    else:
        #print("closed")
        return 0



if __name__ == "__main__":

    date = "2016-06-01"

    link = ['Renk', 'Doro']

    generate_routes_m_file(name1_col=0, name2_col=1, dist_col=2, forced_redirection=3, link_type_col=4)

    distance_change(link, date, data_dir=data_dir, history=history, daily=daily)

    
