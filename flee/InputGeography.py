import csv
from flee import flee
from flee import SimulationSettings

class InputGeography:
  """
  Class which reads in Geographic information.
  """
  def __init__(self):
    self.locations = []
    self.links = []


  def ReadLocationsFromCSV(self,csv_name, columns=["name","region","country","gps_x","gps_y","location_type","conflict_date","pop/cap"]):
    """
    Converts a CSV file to a locations information table
    """
    self.locations = []

    c = {} #column map

    c["location_type"] = 0
    c["conflict_date"] = 0
    c["country"] = 0
    c["region"] = 0

    for i in range(0, len(columns)):
      c[columns[i]] = i

    with open(csv_name, newline='') as csvfile:
      values = csv.reader(csvfile)

      for row in values:
        if row[0][0] == "#":
          pass
        else:
          #print(row)
          self.locations.append([row[c["name"]], row[c["pop/cap"]], row[c["gps_x"]], row[c["gps_y"]], row[c["location_type"]], row[c["conflict_date"]], row[c["region"]], row[c["country"]]])


  def ReadLinksFromCSV(self,csv_name, name1_col=0, name2_col=1, dist_col=2):
    """
    Converts a CSV file to a locations information table
    """
    self.links = []

    with open(csv_name, newline='') as csvfile:
      values = csv.reader(csvfile)

      for row in values:
        if row[0][0] == "#":
          pass
        else:
          #print(row)
          self.links.append([row[name1_col], row[name2_col], row[dist_col]])

  def ReadClosuresFromCSV(self, csv_name):
    """
    Read the closures.csv file. Format is:
    closure_type,name1,name2,closure_start,closure_end
    """
    self.closures = []

    with open(csv_name, newline='') as csvfile:
      values = csv.reader(csvfile)

      for row in values:
        if row[0][0] == "#":
          pass
        else:
          #print(row)
          self.closures.append(row)

    print(self.closures)

  def StoreInputGeographyInEcosystem(self, e):
    """
    Store the geographic information in this class in a FLEE simulation,
    overwriting existing entries.
    """
    lm = {}

    for l in self.locations:
      if len(l[1]) < 1: #if population field is empty, just set it to 0.
        l[1] = "0"
      if len(l[7]) < 1: #if population field is empty, just set it to 0.
        l[7] = "unknown"
      #print(l)
      lm[l[0]] = e.addLocation(l[0], movechance=l[4], pop=int(l[1]), x=l[2], y=l[3], country=l[7])

    for l in self.links:
      e.linkUp(l[0], l[1], int(l[2]))

    return e, lm

