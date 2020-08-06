import os
import sys
import csv
import math
import numpy as np
import pandas as pd
import datetime
import argparse
from flee.datamanager import read_period

# This Script filters the discharge dataset based on simulation period and the Micro model locations!

parser = argparse.ArgumentParser()

parser.add_argument('--input_dir', required=True,
                    action="store", type=str,
                    help="the input data directory")

args, unknown = parser.parse_known_args()

print("args: {}".format(args), file=sys.stderr)

work_dir = os.path.dirname(os.path.abspath(__file__))

input_dir = os.path.join(work_dir, args.input_dir)

data_dir = os.path.join(input_dir, 'weather_data')

locations = pd.read_csv("%s/locations-1.csv" %(input_dir))

start_date, end_time = read_period.read_conflict_period(
    os.path.join(input_dir, "conflict_period.csv"))


def return_date(day):

#This function returns the date of given day!

    start_date, end_time = read_period.read_conflict_period(
    os.path.join(input_dir, "conflict_period.csv"))

    date_1 = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()

    if isinstance(day, np.generic):
        day = np.asscalar(day)    

    date = date_1 + datetime.timedelta(day)

    date = date.strftime('%Y-%m-%d')

    return date


if __name__ == "__main__":

    discharge = pd.read_csv("%s/ssudan_dis_filtered.csv" %(data_dir), sep=',', encoding='latin1')

    start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()

    end_date = return_date(end_time)    

    discharge['time'] = pd.to_datetime(discharge['time'])

    mask_time = (discharge['time'] >= pd.Timestamp(start_date)) & (discharge['time'] < pd.Timestamp(end_date))

    discharge = discharge.loc[mask_time]

    mask_lat = (discharge['lat'] >= locations['lat'].min()) & (discharge['lat'] <= locations['lat'].max())

    discharge = discharge.loc[mask_lat]

    mask_lon = (discharge['lon'] >= locations['lon'].min()) & (discharge['lon'] <= locations['lon'].max())

    discharge = discharge.loc[mask_lon]

    discharge.reset_index(drop=True, inplace=True)

    discharge.to_csv('%s/river_discharge.csv' %(data_dir), na_rep='',float_format = '%.3f', index=False)

    print("The ({}) river_discharge.csv is stored in {}".format(args.input_dir, data_dir))








