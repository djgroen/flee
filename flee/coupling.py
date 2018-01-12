# coupling.py
# File which contains the multiscale coupling interface for FLEE.
# Idea is to support a wide range of coupling mechanisms within this Python file.
import os.path
import time

class CouplingInterface:

  def __init__(self, coupling_type="file"):
    """ Constructor. Coupling types to support eventually:
        - file
        - MPWide
        - one-sided store
        - repository coupling.
    """
    self.coupling_type = coupling_type

    # coupling definitions.
    self.locations = []
    self.location_names = []
    self.names = []
    self.directions = []
    self.intervals = []

  def addCoupledLocation(self, location, name, direction="inout", interval=1):
    """
    Adds a locations to the so-called *Coupled Region*.
    * Location is the (p)Flee location object.
    * Name is a location identifier that is identical to the one in the other code.
    * Direction can be (once the code is done):
      - "out" -> agents are removed and stored in the coupling link.
      - "in" -> agents written to the coupling link by the other process are added to this location.
      - "inout" -> both out and in.
      - "inout indirect" -> changes in agent numbers are stored in the coupling link. No agents are added or removed.
    * Interval is the timestep interval of the coupling, ensuring that the coupling activity is performed every <interval> time steps.
    """
    self.locations += [location]
    self.location_names += [location.name]
    self.names += [name]
    self.directions += [direction]
    self.intervals += [interval]

  def Couple(self, e, t): #TODO: make this code more dynamic/flexible
    if t % self.intervals[0] == 0: #for the time being all intervals will have to be the same...
      self.writeOutputToFile(t)
      e.clearLocationsFromAgents(self.location_names) #TODO: make this conditional on coupling type.
      for i in range(0, locations):
        #write departing agents to file
        #read incoming agents from file
        newAgents = self.readInputFromFile(t)
        e.insertAgents(locations[i], newAgents[names[i]])

  # File coupling code

  def setCouplingFilenames(self, outputfilename, inputfilename):
    """
    Sets the coupling output file name (for file coupling). Name should be WITHOUT .csv extension.
    """
    self.outputfilename = outputfilename
    self.inputfilename = inputfilename

  def writeOutputToFile(self, t):
    for i in range(0, len(self.locations)):
      with open('%s.%s.csv' % (self.outputfilename, t),'wb') as file:
        file.write("%s,%s" % (self.names[i], self.locations[i].numAgents))

  def readInputFromFile(self, t):
    """
    Returns a dictionary with key <coupling name> and value <number of agents>.
    """
    in_fname = "%s.%s.csv" % (self.inputfilename, t)

    while not os.path.exists(in_fname):
      time.sleep(0.1)
    time.sleep(0.001)

    newAgents = {}
    with open("%s.%s.csv" % (self.inputfilename, t), newline='') as csvfile:
      values = csv.reader(csvfile)
      for row in values:
        if row[0][0] == "#":
          pass
        else:
          for i in range(0, len(self.locations)):
            if row[0] == self.names[i]:
              newAgents[self.names[i]] = int(row[1])
    return newAgents
