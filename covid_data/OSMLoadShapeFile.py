from OSMPythonTools.overpass import overpassQueryBuilder, Overpass
import pandas as pd
import geopandas as gpd
import numpy as np
import json
import folium
from geojson import Point, Feature, FeatureCollection, dump
import matplotlib.pyplot as plt
import plotly.express as px
import  plotly as py
import plotly.graph_objects as go
import csv
import shapely.geometry.point as Point
import pyproj
from functools import partial
from shapely.geometry import shape
from shapely.ops import transform
import random

pd.set_option('mode.chained_assignment', None)
df = gpd.read_file("./Brent.geojson")
df.info()
# grps = df.groupby('building')

df['Latitude'] = df['geometry'].centroid.y
df['Longitude'] = df['geometry'].centroid.x

points = []
df['type'] = 0
for index, row in df.iterrows():
    if df['building'][index] == 'park':  df['type'][index] = 1  # park
    if df['building'][index] == 'hospital':  df['type'][index] = 2  # hospital

    if df['building'][index] == 'supermarket':  df['type'][index] = 3  # supermarket
    if df['building'][index] == 'shops':  df['type'][index] = 3  # shops
    if df['building'][index] == 'shop':  df['type'][index] = 3  # shop
    if df['building'][index] == 'retail':  df['type'][index] = 3  # retail
    if df['building'][index] == 'warehouse':  df['type'][index] = 3  # warehouse
    if df['building'][index] == 'store':  df['type'][index] = 3  # store

    if df['building'][index] == 'office':  df['type'][index] = 4  # office
    if df['building'][index] == 'government':  df['type'][index] = 4  # government
    if df['building'][index] == 'fire_station':  df['type'][index] = 4  # fire_station
    if df['building'][index] == 'industrial':  df['type'][index] = 4  # industrial
    if df['building'][index] == 'construction':  df['type'][index] = 4  # construction
    if df['building'][index] == 'bank':  df['type'][index] = 4  # bank
    if df['building'][index] == 'service':  df['type'][index] = 4  # service
    if df['building'][index] == 'commercial':  df['type'][index] = 4  # commercial
    if df['building'][index] == 'industrial':  df['type'][index] = 4  # industrial
    if df['building'][index] == 'data_center':  df['type'][index] = 4  # data_center

    if df['building'][index] == 'school':  df['type'][index] = 5  # school
    if df['building'][index] == 'university':  df['type'][index] = 5  # university
    if df['building'][index] == 'college':  df['type'][index] = 5  # college
    if df['building'][index] == 'school_hostel':  df['type'][index] = 5  # school_hostel

    if df['building'][index] == 'leisure':  df['type'][index] = 6  # leisure
    if df['building'][index] == 'sports_centre':  df['type'][index] = 6  # sports_centre
    if df['building'][index] == 'soft_play':  df['type'][index] = 6  # soft_play
    if df['building'][index] == 'mosque':  df['type'][index] = 6  # mosque
    if df['building'][index] == 'church':  df['type'][index] = 6  # church
    if df['building'][index] == 'chapel':  df['type'][index] = 6  # chapel
    if df['building'][index] == 'temple':  df['type'][index] = 6  # temple
    if df['building'][index] == 'synagogue':  df['type'][index] = 6  # synagogue
    if df['building'][index] == 'religious':  df['type'][index] = 6  # religious
    if df['building'][index] == 'clubhouse':  df['type'][index] = 6  # clubhouse
    if df['building'][index] == 'pavilion':  df['type'][index] = 6  # pavilion
    if df['building'][index] == 'stadium':  df['type'][index] = 6  # stadium
    if df['building'][index] == 'library':  df['type'][index] = 6  # library
    if df['building'][index] == 'community_centre':  df['type'][index] = 6  # community_centre

    if df['building'][index] == 'shopping':  df['type'][index] = 7  # shopping
    if df['building'][index] == 'store':  df['type'][index] = 7  # store
    if df['building'][index] == 'commercial':  df['type'][index] = 7  # commercial
    if df['building'][index] == 'bank':  df['type'][index] = 7  # bank
    if df['building'][index] == 'mall':  df['type'][index] = 7  # mall
    if df['building'][index] == 'pub':  df['type'][index] = 7  # pub
    if df['building'][index] == 'restaurant':  df['type'][index] = 7  # restaurant
    if df['building'][index] == 'shop':  df['type'][index] = 7  # shop
    if df['building'][index] == 'shops':  df['type'][index] = 7  # shops
    if df['building'][index] == 'retail':  df['type'][index] = 7  # retail
    if df['building'][index] == 'hotel':  df['type'][index] = 7  # hotel

    if df['building'][index] == 'apartments':  df['type'][index] = 8  # apartments
    if df['building'][index] == 'appartments':  df['type'][index] = 8  # appartments
    if df['building'][index] == 'detached':  df['type'][index] = 8  # detached
    if df['building'][index] == 'house':  df['type'][index] = 8  # house
    if df['building'][index] == 'hut':  df['type'][index] = 8 # hut
    if df['building'][index] == 'residential':  df['type'][index] = 8  # residential
    if df['building'][index] == 'terrace':  df['type'][index] = 8  # terrace
    if df['building'][index] == 'semidetached_house':  df['type'][index] = 8  # semidetached_house

    if df['building'][index] == 'no':  df['type'][index] = 9  # no
    if df['building'][index] == 'None':  df['type'][index] = 9  # None
    if df['building'][index] == 'yes':  df['type'][index] = 9  # yes
    tuple = (df['osm_id'][index], df['building'][index], df['type'][index], df['other_tags'], df['Latitude'][index], df['Longitude'][index])
    points.append(tuple)

print(points)
# df.info()

with open('buildings.csv', 'w', newline='\n') as file:
    writer = csv.writer(file, delimiter=',')
    writer.writerow(['osm_id','building','type', 'taginfo', 'Latitude','Longitude'])
    writer.writerows(points)


fig = px.scatter_mapbox(df, lat="Latitude", lon="Longitude",
                        # color_discrete_sequence=px.colors.cyclical.IceFire,
                        color="type",
                        # size="count",
                        hover_name="building",
                        zoom=10,  height=800)
fig.update_layout(mapbox_style="open-street-map")
fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
py.offline.plot(fig, filename='name.html')
fig.show()

# df.to_csv("buildings_test.csv", columns=['building', 'Longitude', 'Latitude'], index=False)
