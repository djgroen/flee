# coupling.py
# File which contains the multiscale coupling interface for FLEE.
# Idea is to support a wide range of coupling mechanisms within this
# Python file.
import os.path
import time
import csv
import sys
from libmuscle import Instance, Message
from ymmsl import Operator


class CouplingInterface:

    def __init__(self, e, coupling_type="file", outputdir=""):
        """ Constructor.
        e = FLEE ecosystem
        Coupling types to support eventually:
            - file
            - MPWide
            - one-sided store
            - repository coupling.
            - muscle
        """
        self.coupling_type = coupling_type

        # coupling definitions.
        self.e = e
        self.location_ids = []
        self.location_names = []
        self.ghost_location_ids = []
        self.ghost_location_names = []
        self.names = []
        self.directions = []
        self.intervals = []
        self.outputdir = outputdir

    def reuse_couling(self):
        if self.coupling_type == 'file':
            return True
        elif self.coupling_type == 'muscle3':
            from libmuscle import Instance
            return self.instance.reuse_instance()

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
        if location.name not in self.location_names:

            self.location_ids += [
                self.e._convert_location_name_to_index(location.name)]
            self.location_names += [location.name]
            print("Adding coupled location {} {} {}".format(
                location.name, direction, interval), file=sys.stderr)
            self.names += [name]
            self.directions += [direction]
            self.intervals += [interval]
            self.coupling_rank = True
            if hasattr(self.e, 'mpi') and self.e.mpi != None:
                if self.e.mpi.rank > 0:
                    self.coupling_rank = False

        else:
            print("warning: coupled location is selected twice (ignore this if a location is both a coupled location and a conflict location). Only one coupled location will be created.", file=sys.stderr)

    def addGhostLocations(self, ig):
        conflict_name_list = ig.getConflictLocationNames()
        print("Adding Ghosts", file=sys.stderr)
        for ln in conflict_name_list:
            for i in range(0, len(self.e.locationNames)):
                if self.e.locationNames[i] == ln:
                    l = self.e.locations[i]
                    print("L", l.name, len(l.links), file=sys.stderr)
                    if len(l.links) == 0:
                        if not l.name in self.location_names:
                            print("Adding ghost location {}".format(
                                l.name), file=sys.stderr)
                            self.addCoupledLocation(
                                l, l.name, "out", interval=1)

    def addMicroConflictLocations(self, ig):
        conflict_name_list = ig.getConflictLocationNames()
        print("Adding micro conflict coupling", file=sys.stderr)
        for ln in conflict_name_list:
            for i in range(0, len(self.e.locationNames)):
                if self.e.locationNames[i] == ln:
                    l = self.e.locations[i]
                    print("L", l.name, len(l.links), file=sys.stderr)
                    print("Adding micro coupled conflict location {}".format(
                        l.name), file=sys.stderr)
                    self.addCoupledLocation(l, l.name, "in", interval=1)

    def Couple(self, t):  # TODO: make this code more dynamic/flexible
        newAgents = None
        # for the time being all intervals will have to be the same...
        if t % self.intervals[0] == 0:
            if self.coupling_type == "muscle3":
                if self.coupling_rank:  # If MPI is used, this will be the process with rank 0
                    self.instance.send('out',
                                       Message(t, None,
                                               self.generateOutputCSVString(t))
                                       )
                    msg = self.instance.receive('in')
                    newAgents = self.extractNewAgentsFromCSVString(
                        msg.data.split('\n'))
                # If MPI is used, broadcast newAgents to all other processes
                if hasattr(self.e, 'mpi') and self.e.mpi != None:
                    newAgents = self.e.mpi.comm.bcast(newAgents, root=0)

            else:  # default is coupling through file IO.
                if self.coupling_rank:  # If MPI is used, this will be the process with rank 0
                    self.writeOutputToFile(t)

                newAgents = self.readInputFromFile(t)

            # TODO: make this conditional on coupling type.
            self.e.clearLocationsFromAgents(self.location_names)
            for i in range(0, len(self.location_names)):
                # write departing agents to file
                # read incoming agents from file
                #print(self.names, i, newAgents)

                if "in" in self.directions[i]:

                    print("Couple IN: %s %s" % (
                        self.names[i], newAgents[self.names[i]]), file=sys.stderr)
                    if self.names[i] in newAgents:
                        self.e.insertAgents(self.e.locations[self.location_ids[
                                            i]], newAgents[self.names[i]])
                if hasattr(self.e, 'mpi'):
                    self.e.updateNumAgents()

    # File coupling code

    def setCouplingChannel(self, outputchannel, inputchannel):
        """
        Sets the coupling output file name (for file coupling). 
        Name should be WITHOUT .csv extension.
        """
        if self.coupling_type == 'file':
            self.outputfilename = outputchannel
            self.inputfilename = inputchannel
        elif self.coupling_type == 'muscle3':
            from libmuscle import Instance
            from ymmsl import Operator
            self.instance = Instance({
                Operator.O_I: ['out'],
                Operator.S: ['in']
            })

    def generateOutputCSVString(self, t):
        out_csv_string = ""
        for i in range(0, len(self.location_ids)):
            if "out" in self.directions[i]:
                out_csv_string += "%s,%s\n" % (self.names[i], self.e.locations[
                                               self.location_ids[i]].numAgents)
                print("Couple OUT: %s %s" % (self.names[i], self.e.locations[
                      self.location_ids[i]].numAgents), file=sys.stderr)
        return out_csv_string

    def writeOutputToFile(self, t):
        out_csv_string = self.generateOutputCSVString(t)
        outputfile = '%s/file/coupled/%s.%s.csv' % (
            self.outputdir, self.outputfilename, t)

        with open(outputfile, 'a') as file:
            file.write(out_csv_string)

        print("Couple: output written to %s.%s.csv" %
              (self.outputfilename, t), file=sys.stderr)

    def extractNewAgentsFromCSVString(self, csv_string):
        """
        Reads in a CSV string with coupling information, and extracts a list of New Agents.
        """
        newAgents = {}

        for line in csv_string:
            row = line.split(',')
            if len(row[0]) == 0:
                continue
            if row[0][0] == "#":
                pass
            else:
                for i in range(0, len(self.location_ids)):
                    if row[0] == self.names[i]:
                        newAgents[self.names[i]] = int(row[1])
        return newAgents

    def readInputFromFile(self, t):
        """
        Returns a dictionary with key <coupling name> and value <number of agents>.
        """
        in_fname = "%s/file/coupled/%s.%s.csv" % (self.outputdir,
                                             self.inputfilename, t)

        print("Couple: searching for", in_fname, file=sys.stderr)
        while not os.path.exists(in_fname):
            time.sleep(0.1)
        time.sleep(0.001)

        csv_string = ""
        with open(in_fname) as csvfile:
            csv_string = csvfile.read().split('\n')

        return self.extractNewAgentsFromCSVString(csv_string)
