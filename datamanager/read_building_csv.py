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
      x = float(row[1])
      y = float(row[2])
      location_type = apply_building_mapping(building_mapping, row[0])

      #count all the building types in a dict.
      if row[0] not in building_types:
        building_types[row[0]] = 1
      else:
        building_types[row[0]] += 1

      if location_type == "house":
        e.addHouse(num_houses, x , y, 1)
        num_houses += 1
      else:
        e.addLocation(num_locs, location_type, x, y, building_mapping[location_type]['default_sqm'])
        num_locs += 1
      row_number += 1
      if row_number % 10000 == 0:
        print(row_number, "read", file=sys.stderr)
    print(row_number, "read", file=sys.stderr)

    e.update_nearest_locations()

  print("Read in {} houses and {} other locations.".format(num_houses, num_locs))
  print("Type distribution:")
  print("house",len(e.houses))
  for lt in e.locations:
    print(lt, len(e.locations[lt]))
  print("raw types are:")
  pp.pprint(building_types)
  if dumptypesandquit:
    sys.exit()

