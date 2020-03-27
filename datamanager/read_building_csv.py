import csv
import sys
import pprint
import yaml

# File to read in CSV files of building definitions.
# The format is as follows:
# No,building,Longitude,Latitude,Occupancy
#lids = {"park":0,"hospital":1,"supermarket":2,"office":3,"school":4,"leisure":5,"shopping":6}

pp = pprint.PrettyPrinter()

def apply_building_mapping(mapdict, label):
  """
  Applies a building map YAML to a given label, binning it
  into the appropriate category.
  """
  for category in mapdict:
    #print(mapdict, category)
    if label in mapdict[category]['labels']:
      return category
  return "house"

def read_building_csv(e, csvfile, building_type_map="covid_data/building_types_map.yml", dumptypesandquit=False):
 
  building_mapping = {}
  with open(building_type_map) as f:
    building_mapping = yaml.load(f, Loader=yaml.FullLoader)

  if csvfile == "":
    print("Error: could not find csv file.")
    sys.exit()
  with open(csvfile) as csvfile:
    needs_reader = csv.reader(csvfile)
    row_number = 0
    num_locs = 0
    num_houses = 0
    building_types = {}
    for row in needs_reader:
      if row_number == 0:
        row_number += 1
        continue
      x = float(row[2])
      y = float(row[3])
      location_type = apply_building_mapping(building_mapping, row[1])

      #count all the building types in a dict.
      if row[1] not in building_types:
        building_types[row[1]] = 1
      else:
        building_types[row[1]] += 1

      if location_type == "house":
        e.addHouse(num_houses, x , y, 1)
        num_houses += 1
      else:
        e.addLocation(num_locs, location_type, x, y, 100)
        num_locs += 1
      row_number += 1

  print("Read in {} houses and {} other locations.".format(num_houses, num_locs))
  print("raw types are:")
  pp.pprint(building_types)
  if dumptypesandquit:
    sys.exit()

