import random
import folium
from folium.plugins import HeatMap
from folium.plugins import HeatMapWithTime
import geopandas as gpd
import pandas as pd
from pandas import read_csv
from datetime import datetime
from datetime import timedelta
from datetime import date
from shapely.geometry import Point, Polygon, MultiPolygon
import sys

geo_json_data = gpd.read_file('./Brent.geojson')
geo_json_data['value'] = 0

#format of infected dataset. (first is day)
#time         x          y location_type        date  count  day

infected = read_csv(sys.argv[1]) #read time,x,y,location_type columns of all infections.
# infected = infected[infected['#time']<=20]
startdate = date(2020, 3, 17)
#infected['date'] = ""
infected['count'] = 0
infected['#time'] = pd.to_numeric(infected['#time'])
infected.columns = ["day","x","y","location_type","count"]

#print(infected)
#sys.exit()

#for index, row in infected.iterrows():
#    day = int(row['#time'])
    #infected['date'][index] = startdate + timedelta(days=day)

#infected['day'] = infected.date.apply(lambda x: x.day)

# infected_time = infected.groupby(infected['#time']).size().reset_index(name='Count')

df = []
for day in infected.day.sort_values().unique():
    df.append(infected.loc[infected.day == day, ['y', 'x', 'count']].groupby(['y', 'x']).mean().reset_index().values.tolist())
    #print("DAY:", day, infected.loc[infected.day == day, ['y', 'x', 'count']].groupby(['y', 'x']).mean().reset_index().values.tolist())
#sys.exit()

#geo_json_data.info()

m = folium.Map(location = [51.55, -0.26], zoom_start = 12, control_scale=True,)
m.choropleth(geo_data=geo_json_data, data = geo_json_data,
             columns = ['NAME', 'value'],
             fill_color = 'BuGn',
             fill_opacity=0.2,
             key_on = 'feature.properties.NAME',
             legend_name='Infected',
             highlight=True,
             popup = 'Test')
# folium.LayerControl().add_to(m)
# HeatMap(data=infected[['y', 'x', 'count']].groupby(['y', 'x']).mean().reset_index().values.tolist(), radius=10, max_zoom=12).add_to(m)
HeatMapWithTime(df, radius=12, gradient={0.1: 'green', 0.2: 'lime', 0.4: 'yellow', 0.6: 'orange', 0.8: 'red', 1.0: 'black'}, min_opacity=0.1, max_opacity=1, use_local_extrema=False).add_to(m)
m.save('./{}_map.html'.format(sys.argv[1]))

m2 = folium.Map(location = [51.55, -0.26], zoom_start = 12, control_scale=True,)
m2.choropleth(geo_data=geo_json_data, data = geo_json_data,
             columns = ['NAME', 'value'],
             fill_color = 'BuGn',
             fill_opacity=0.2,
             key_on = 'feature.properties.NAME',
             legend_name='Infected',
             highlight=True,
             popup = 'Test')
# folium.LayerControl().add_to(m)
# HeatMap(data=infected[['y', 'x', 'count']].groupby(['y', 'x']).mean().reset_index().values.tolist(), radius=10, max_zoom=12).add_to(m)
HeatMapWithTime(df, radius=12, gradient={0.1: 'green', 0.2: 'lime', 0.4: 'yellow', 0.6: 'orange', 0.8: 'red', 1.0: 'black'}, min_opacity=0.1, max_opacity=1, use_local_extrema=False).add_to(m)
#m2.save('./{}_map2.html'.format(sys.argv[1]))

