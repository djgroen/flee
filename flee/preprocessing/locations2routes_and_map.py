import pandas as pd
import numpy as np
import os
import csv
import sys
import requests
import json
import folium
from haversine import haversine, Unit
from folium.plugins import MarkerCluster
from folium.plugins import PolyLineTextPath
from polyline import decode
from geopy.distance import distance
from geopy.geocoders import Nominatim

def routes_creator(df):
    # Create a new dataframe to store the distances
    distances = pd.DataFrame(columns=["start_point", "end_point", "distance"])

    # Loop through each row in the input dataframe and calculate the distance to the next location
    for i in range(len(df)-1):
        loc1 = (df.loc[i,"latitude"], df.loc[i,"longitude"])
        for j in range(len(df)-1):
            loc2 = (df.loc[j,"latitude"], df.loc[j,"longitude"])
            #print('loc1_lat={0} and loc1_lon={1}'.format(loc1[0],loc1[1]))
            #print('loc2_lat={0} and loc2_lon={1}'.format(loc2[0],loc2[1]))
            dist = distance(loc1, loc2).km
            #dist = distance_calculator(loc1[0],loc1[1],loc2[0],loc2[1])
            if int(dist) != 0:
                distances.loc[len(distances)] = [df.loc[i,"#name"], df.loc[j,"#name"], int(dist)]

    # sort the values in the first two columns
    #distances[["start_point", "end_point"]] = np.sort(distances[["start_point", "end_point"]])

    # drop duplicates based on col1 and col2, keep the first occurrence
    distances.drop_duplicates(subset=["start_point", "end_point"], keep='first', inplace=True)

    result_df = distances.groupby('start_point').apply(lambda x: x.nsmallest(5, 'distance')).reset_index(drop=True)

    result_df = result_df[result_df['distance'] <= 1200]

    # Output the distances to a new CSV file
    output_file = fabflee_configs+country+'/'+'input_csv'+'/'+"new_routes2.csv"
    result_df.to_csv(output_file, index=False)
    print('The results are stored in {0}'.format(output_file))

    map_generator(df,result_df)



def map_generator(df, distances):
    # Create a map with all the locations and the routes to the nearest locations
    m = folium.Map(location=[df['latitude'].mean(), df['longitude'].mean()], zoom_start=7)
    '''
    # Add all the locations to the map
    marker_cluster = MarkerCluster().add_to(m)

    for index, row in df.iterrows():
        #print(row)
        if row["location_type"] == 'conflict_zone':
            folium.Marker([row['latitude'], row['longitude']], popup=row['#name'],icon = folium.Icon(color='red',icon='info-sign')).add_to(marker_cluster)
        elif row["location_type"] == 'camp':
            folium.Marker([row['latitude'], row['longitude']], popup=row['#name'],icon = folium.Icon(color='green',icon='plus')).add_to(marker_cluster)
    '''
    for index, row in df.iterrows():
        #print(row)
        if row["location_type"] == 'conflict_zone':
            folium.Circle(
                location=[row['latitude'], row['longitude']],
                radius=10000,
                color='red',
                fill=True,
                fill_color='red',
                tooltip='',
                popup=row['#name']
            ).add_to(m)
        elif row["location_type"] == 'camp':
            folium.Circle(
                location=[row['latitude'], row['longitude']],
                radius=10000,
                color='green',
                fill=True,
                fill_color='green',
                tooltip='',
                popup=row['#name']
            ).add_to(m)

    # Add the routes to the nearest locations to the map
    for index, row in distances.iterrows():
        source = df[df['#name']==row['start_point']].iloc[0]
        dest = df[df['#name']==row['end_point']].iloc[0]
        coords1 = f"{source['latitude']},{source['longitude']}"
        coords2 = f"{dest['latitude']},{dest['longitude']}"
        params = {'origin': coords1, 'destination': coords2, 'key': api_key}
        response = requests.get(endpoint, params=params).json()
        if (response['routes']) == []:
            print("Couldn't find the geospacial information of route between {} and {}.".format(row['start_point'],row['end_point']))
            continue
        route = decode(response['routes'][0]['overview_polyline']['points'])
        popup_text = f"Source: {row['start_point']}<br>Destination: {row['end_point']}<br>Distance: {row['distance']} km"
        folium.PolyLine(locations=route, color='orange', weight=2, opacity=0.8, popup=popup_text).add_to(m)

    # Save the map to an HTML file
    output_file = fabflee_configs+'/'+country+'/'+'input_csv'+'/'+"{0}_map.html".format(country)
    m.save(output_file)
    print('The map is stored in {0}'.format(output_file))


    # Print the problematic rows
    for index, row in distances.iterrows():
        try:
            float(row['distance'])
        except ValueError:
            print(f"Error: could not convert '{row['distance']}' to float. Row {index+1}: {row}")


if __name__ == '__main__':

    fabflee_configs = sys.argv[1]
    country = sys.argv[2]
    locations = (fabflee_configs+'/'+country+'/'+'input_csv'+'/'+sys.argv[3])
    # Read in the CSV file containing coordinates
    df = pd.read_csv(locations)

    # Define the API endpoint for the routing service
    endpoint = 'https://maps.googleapis.com/maps/api/directions/json'

    # Specify your Google Maps API key here
    api_key = 'API_KEY'

    routes_creator(df)

    

    
