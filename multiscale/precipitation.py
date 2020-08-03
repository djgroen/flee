import os
import sys
import csv
import math
import numpy as np
import pandas as pd
import datetime
import argparse
from flee.datamanager import read_period

'''
This script creates the precipitation.csv file which will be used as a reference 
to search for precipitation level of the given link at the specific day of simulation!
In order to run, just enter python3 precipitation.py --input_dir (config_files directory)
'''

parser = argparse.ArgumentParser()

parser.add_argument('--input_dir', required=True,
                    action="store", type=str,
                    help="the input data directory")

args, unknown = parser.parse_known_args()

print("args: {}".format(args), file=sys.stderr)

work_dir = os.path.dirname(os.path.abspath(__file__))

input_dir = os.path.join(work_dir, args.input_dir)

data_dir = os.path.join(input_dir, 'weather_data')

history = pd.read_csv("%s/weather_data/40yrs_tp.csv" %(input_dir), sep=',', encoding='latin1')

daily=pd.read_csv("%s/weather_data/daily_tp.csv" %(input_dir), sep=',', encoding='latin1')



def X1_X2(link,date):

#This function returns the two treshholds of X1 and X2.
#The way of calculating threshholds needs to be discussed!
    #print(link)
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

    midpoint_tp = float(midpoint_tp)

    return midpoint_tp


def return_date(day):

#This function returns the date of given link based on routes_tp.csv which has created manually and needs to be created automatically!

    start_date, end_time = read_period.read_conflict_period(
    os.path.join(input_dir, "conflict_period.csv"))

    date_1 = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()

    date = date_1 + datetime.timedelta(day)

    date = date.strftime('%Y-%m-%d')

    return date


def multiplier(startpoint, endpoint, day):

#This function returns the multiplier in order to change the distance of links while the weather_coupling flag set to True!

    data_dir = os.path.join(input_dir, 'weather_data')

    date = return_date(day)

    link = [startpoint, endpoint]

    link_cat = startpoint+" - "+endpoint

    link_cat_reverse = endpoint+" - "+startpoint

    X1, X2=X1_X2(link,date)

    df = pd.read_csv("{}/precipitation.csv".format(data_dir)) 

    columns = df.columns.values

    for i in range(1, len(columns)):
        if link_cat == columns[i] or link_cat_reverse == columns[i]:
            tp= df.loc[df.index[day], columns[i]]
            print ("Link exist")
         
    #Log: print inputs and output
    #print("startpoint = %s   endpoint = %s " %(startpoint, endpoint))
    #print("tp={}".format(tp))
    #print("X1={}".format(X1))
    #print("X2={}".format(X2))
    
    if tp <= X1:
        return 1

    elif tp <=X2: 
        return 2

    else:
        return 1000


if __name__ == "__main__":

    df = pd.read_csv("{}/routes-1.csv".format(input_dir)) 

    df = df[['#name1', 'name2']]
    
    links = df.values.tolist()

    df['link'] = df['#name1'].str.cat(df['name2'],sep=" - ")

    routes = df['link'].tolist()

    output_header_string = "Day"

    start_date, end_time = read_period.read_conflict_period(
    os.path.join(input_dir, "conflict_period.csv"))

    out_csv_file = os.path.join(data_dir, "precipitation.csv")

    for i in range(0, len(routes)):
        output_header_string += ",%s" % (routes[i])

    #print(output_header_string)

    with open(out_csv_file, 'w') as f:
        f.write(output_header_string)
        f.write('\n')
        f.flush()        

    for t in range(0, end_time):
        output = "%s" % t

        for i in range(0, len(links)):
                    date = return_date(t)
                    output += ",%s" % (midpoint_tp(links[i], date))
                  
        with open(out_csv_file, '+a') as f:
            f.write(output)
            f.write('\n')
            f.flush()  
    

    print("The precipitation.csv is stored in {}".format(data_dir))
    


    
