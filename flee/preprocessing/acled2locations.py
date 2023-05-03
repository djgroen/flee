import pandas as pd
import warnings
import sys
import os
import calendar as cal
from datetime import datetime
import json
import requests
import time
import wikipedia
import wbdata

def get_state_population(state_name,population_input_file):
    
    df = pd.read_csv(population_input_file)
    print(state_name)
    population = df.loc[df['States'] == state_name, 'Population'].values[0]
    return population

def get_city_population(city_name,population_input_file):
    country_code = 'NG'
    url = "https://wft-geo-db.p.rapidapi.com/v1/geo/cities/{0}".format(get_wikidata_id(city_name))

    headers = {
        "X-RapidAPI-Key": "API_KEY",
        "X-RapidAPI-Host": "wft-geo-db.p.rapidapi.com"
    }
    response = requests.request("GET", url, headers=headers)

    if response.status_code == 404:
        get_state_population(city_name,population_input_file)

    else:
        data = response.json()
        population = data["data"]['population']
        return population

def get_wikidata_id(city_name):

    url = "https://www.wikidata.org/w/api.php"

    params = {
        'action': 'wbsearchentities',
        'format': 'json',
        'language': 'en',
        'search': city_name
    }

    r = requests.get(url, params = params)

    return (r.json()['search'][0]['id'])


def month_convert(month_name):

    months = {
    "jan": "01", "january": "01",
    "feb": "02", "february": "02",
    "mar": "03", "march": "03",
    "apr": "04", "april": "04",
    "may": "05",
    "jun": "06", "june": "06",
    "jul": "07", "july": "07",
    "aug": "08", "august": "08",
    "sep": "09", "september": "09",
    "oct": "10", "october": "10",
    "nov": "11", "november": "11",
    "dec": "12", "december": "12"
    }

    # Convert the month name to lowercase and strip leading/trailing whitespace
    month_name = month_name.strip().lower()

    # Look up the month number in the dictionary
    if month_name in months:
        month_num = months[month_name]
        #print(f"The month number for {month_name} is {month_num}.")
    else:
        print("Invalid month name entered.")

    return month_num


def date_format(in_date):
    # converting date from textbased to dd-mm-yyyy format
    if "-" in in_date:
        split_date = in_date.split("-")
    else:
        split_date = in_date.split(" ")

    month_num = month_convert(split_date[1])
    if int(split_date[2]) < 50:
        year = int(split_date[2]) + 2000
    else:
        year = int(split_date[2])
    out_date = split_date[0] + "-" + str(month_num) + "-" + str(year)
    return out_date


def between_date(d1, d2):

    # Gets difference between two dates in string format "dd-mm-yyyy"
    d1list = d1.split("-")
    d2list = d2.split("-")
    date1 = datetime(int(d1list[2]), int(d1list[1]), int(d1list[0]))
    date2 = datetime(int(d2list[2]), int(d2list[1]), int(d2list[0]))

    return abs((date1 - date2).days)  # Maybe add +1


def date_verify(date):
    date_format = "%d-%m-%Y"
    try:
        date_obj = datetime.strptime(date, date_format)
        return True

    except ValueError:
        print("Incorrect data format please input dd-mm-yyyy")
        return False


def drop_rows(inputdata, columnname, dropparameter):
    removedrows = inputdata.index[
        inputdata[columnname] <= dropparameter].tolist()
    outputdata = inputdata.drop(removedrows)
    return outputdata


def filter_table(df, colname, adminlevel):
    if adminlevel == "admin1":
        adminlist = df.admin1.unique()
    elif adminlevel == "location":
        adminlist = df.location.unique()
    else:
        adminlist = df.admin2.unique()
    newdf = pd.DataFrame(columns=df.columns)

    for admin in adminlist:
        tempdf = df.loc[df[adminlevel] == admin]
        tempdf.sort_values(colname, ascending=True)
        newdf = newdf.append(tempdf.tail(1))
    print(newdf)
    return newdf


def find_csv(country):
    path_to_dir = os.getcwd()
    print(path_to_dir)
    filename = country + "-acled.csv"
    locations = os.path.join(
        "config_files", country, "source_data", filename
    )
    print(locations)

    return locations

# Takes path to acled csv file, a start date in dd-mm-yyyy format, and a
# filter (First occurence or highest fatalities)


def acled2locations(fab_flee_loc, country, start_date,
                    filter_opt, admin_level):
    warnings.filterwarnings('ignore')
    input_file = os.path.join(fab_flee_loc, "config_files",
                              country,
                              "acled.csv")
    print("Current Path: ", input_file)
    try:
        tempdf = pd.read_csv(input_file)
    except:
        print("Runtime Error: File Cannot be found")

    df = tempdf[["event_date", "country", "admin1", "latitude", "longitude", "fatalities"]]
    # event_date is given in incorrect format, so formatting to dd-mm-yyyy
    # required
    event_dates = df["event_date"].tolist()

    formatted_event_dates = [date_format(date) for date in event_dates]

    conflict_dates = [between_date(d, start_date)
                      for d in formatted_event_dates]
    # replacing event_date
    df.loc[:, "event_date"] = conflict_dates
    
    df.rename(columns={'event_date': 'conflict_date'}, inplace=True)

    fatalities_threshold = 0

    df = drop_rows(df, 'fatalities', fatalities_threshold)

    df = df.sort_values("conflict_date").drop_duplicates("admin1")


    if filter_opt == 'earliest':
        filter_opt = 'conflict_date'

    try:
        df = filter_table(df, filter_opt, admin_level)
    except:
        print("Runtime error: filter_opt value must be earliest or fatalities")

    # Exporting CSV to locations.csv
    output_df = df[['admin1', 'admin1', 'country',
                    'latitude', 'longitude', 'conflict_date']]
    output_df.rename(columns={'admin1': '#name'}, inplace=True)
    output_df["location_type"] = "conflict_zone"

    population = []

    #print(df['admin1'])
    for name in df['admin1']:
        #output_df[name]["population"] = get_city_population(name)
        population.append(get_state_population(name,population_input_file))
        #print('{0},{1}'.format(name,population))
        #time.sleep(1)
        #print('Due to the request limit of GeoDB API, which is one request per second, please wait:')
        #print('{0} seconds'.format(len(df['admin1'])*2))

    output_df['population']=population
    output_df = output_df[
        ['#name', 'country', 'latitude',
         'longitude', 'location_type', 'conflict_date',
         'population']
    ]
    output_file = os.path.join(fab_flee_loc, "config_files",
                               country, "input_csv",
                               "locations.csv")

    try:
        output_df.to_csv(output_file, index=False, mode='x')
    except FileExistsError:
        print("File Already exists, saving as new_locations.csv")
        output_file = os.path.join(fab_flee_loc, "config_files",
                                   country, "input_csv",
                                   "new_locations.csv")
        output_df.to_csv(output_file, index=False, mode='x')


if __name__ == '__main__':

    fabflee = sys.argv[1]
    country = sys.argv[2]
    start_date = sys.argv[3]
    filter_opt = sys.argv[4]
    adminlevel = sys.argv[5]
    population_input_file = sys.argv[6]
    acled2locations(fabflee, country, start_date, filter_opt, adminlevel)
