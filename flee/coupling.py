# coupling.py
# File which contains the multiscale coupling interface for FLEE.
# Idea is to support a wide range of coupling mechanisms within this
# Python file.
import matplotlib
matplotlib.use('Agg')
import os.path
import time
import csv
import sys
from libmuscle import Instance, Message
from ymmsl import Operator
import logging
import numpy as np
from pprint import pprint
import pandas as pd


# import matplotlib
# matplotlib.use('Pdf')
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.colors import ListedColormap
import matplotlib.patches as mpatches


class CouplingInterface:

    def __init__(self, e, submodel, worker_index=None, num_workers=None,
                 coupling_type="file", outputdir="out", log_exchange_data=True):
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
        self.submodel = submodel  # micro / macro / manager

        self.worker_index = worker_index
        self.num_workers = num_workers

        # for logging
        self.log_exchange_data = log_exchange_data

        if self.coupling_type == 'muscle3':
            self.logger = logging.getLogger()
            self.logger.propagate = False

            if self.submodel in ['macro', 'micro']:
                self.instance = Instance({
                    Operator.O_I: ['out'],
                    Operator.S: ['in']})
            elif self.submodel in ['macro_manager', 'micro_manager']:
                self.instance = Instance({
                    Operator.O_I: ['out[]'],
                    Operator.S: ['in[]']})

    def reuse_coupling(self):
        if self.coupling_type == 'file':
            return True
        elif self.coupling_type == 'muscle3':
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
            '''
            disabled by HAMID
            print("Adding coupled location {} {} {}".format(
                location.name, direction, interval), file=sys.stderr)
            '''
            self.names += [name]
            self.directions += [direction]
            self.intervals += [interval]
            self.coupling_rank = True
            if hasattr(self.e, 'mpi') and self.e.mpi != None:
                if self.e.mpi.rank > 0:
                    self.coupling_rank = False

        else:
            print("%s --> warning: coupled location [%s] is selected twice (ignore this if a location is both a coupled location and a conflict location). Only one coupled location will be created." % (
                self.submodel, location.name), file=sys.stderr)

    def addGhostLocations(self, ig):
        conflict_name_list = ig.getConflictLocationNames()
        print("Adding Ghosts", file=sys.stderr)

        for ln in conflict_name_list:
            for i in range(0, len(self.e.locationNames)):
                if self.e.locationNames[i] == ln:
                    l = self.e.locations[i]
                    #print("L", l.name, len(l.links), file=sys.stderr)
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
                    #print("L", l.name, len(l.links), file=sys.stderr)
                    print("Adding micro coupled conflict location {}".format(
                        l.name), file=sys.stderr)

                    self.addCoupledLocation(l, l.name, "in", interval=1)

    def Couple(self, t):  # TODO: make this code more dynamic/flexible
        newAgents = None

        # for the time being all intervals will have to be the same...

        # for current interval=1 we can ignore this check, but it should be
        # added later if we need higher interval values here
        if t % self.intervals[0] == 0:
            # if True:
            if self.coupling_type == "muscle3":
                if self.coupling_rank:  # If MPI is used, this will be the process with rank 0
                    if self.submodel == 'macro_manager':

                        # collect output from each macro worker
                        newAgents = {}
                        for slot in range(self.num_workers):
                            msg = self.instance.receive('in', slot)
                            curr_newAgent = self.extractNewAgentsFromCSVString(
                                msg.data['newAgents'].split('\n'))

                            if len(newAgents) == 0:
                                newAgents = curr_newAgent
                            else:
                                for name in curr_newAgent:
                                    if type(newAgents[name]) is not list:
                                        newAgents[name] = [newAgents[name]]
                                    newAgents[name].append(curr_newAgent[name])

                        # combined founded newAgents per location by each worker into one
                        # for now, we use arithmetic mean,
                        # we may need to change it to another approach later
                        for name in newAgents:
                            newAgents[name] = int(
                                round(np.mean(newAgents[name])))

                        data_to_micro = "\n".join("%s,%s" % (
                            key, value) for key, value in newAgents.items())

                        for slot in range(self.num_workers):
                            self.instance.send('out',
                                               Message(t, None, data_to_micro),
                                               slot)

                    elif self.submodel == 'micro_manager':

                        # receive from micro
                        newAgents = {}
                        for slot in range(self.num_workers):
                            msg = self.instance.receive('in', slot)
                            curr_newAgent = self.extractNewAgentsFromCSVString(
                                msg.data['newAgents'].split('\n'))

                            if len(newAgents) == 0:
                                newAgents = curr_newAgent
                            else:
                                for name in curr_newAgent:
                                    if type(newAgents[name]) is not list:
                                        newAgents[name] = [newAgents[name]]
                                    newAgents[name].append(curr_newAgent[name])

                        # combined founded newAgents per location by each worker into one
                        # for now, we use arithmetic mean,
                        # we may need to change it to another approach later
                        for name in newAgents:
                            newAgents[name] = int(
                                round(np.mean(newAgents[name])))

                        data_to_macro = "\n".join("%s,%s" % (
                            key, value) for key, value in newAgents.items())
                        # send to macro
                        for slot in range(self.num_workers):
                            self.instance.send('out',
                                               Message(t, None, data_to_macro),
                                               slot)

                    elif self.submodel in ['macro', 'micro']:

                        newAgents_str = self.generateOutputCSVString(t)
                        # here, in addition to newAgents, we can also pass
                        # other variables if are required
                        msg = {
                            'newAgents': newAgents_str
                        }
                        self.instance.send('out', Message(t, None, msg))

                        if self.log_exchange_data == True:
                            self.logExchangeData(t)

                        msg = self.instance.receive('in')
                        newAgents = self.extractNewAgentsFromCSVString(
                            msg.data.split('\n'))

                # If MPI is used, broadcast newAgents to all other processes
                if hasattr(self.e, 'mpi') and self.e.mpi != None:
                    newAgents = self.e.mpi.comm.bcast(newAgents, root=0)

            elif self.coupling_type == "file":  # default is coupling through file IO.
                if self.coupling_rank:  # If MPI is used, this will be the process with rank 0
                    self.writeOutputToFile(t)
                    if self.log_exchange_data == True:
                        self.logExchangeData(t)

                newAgents = self.readInputFromFile(t)

            # TODO: make this conditional on coupling type.
            if self.submodel in ['micro', 'macro']:
                self.e.clearLocationsFromAgents(self.location_names)
                for i in range(0, len(self.location_names)):
                    # write departing agents to file
                    # read incoming agents from file
                    # print(self.names, i, newAgents)
                    if "in" in self.directions[i]:

                        print("Couple IN: %s %s" % (
                            self.names[i], newAgents[self.names[i]]), file=sys.stderr)

                        if self.names[i] in newAgents:
                            self.e.insertAgents(self.e.locations[self.location_ids[
                                                i]], newAgents[self.names[i]])
                    if hasattr(self.e, 'mpi'):
                        self.e.updateNumAgents(log=False)

    def setCouplingChannel(self, outputchannel, inputchannel):
        """
        Sets the coupling output file name (for file coupling).
        Name should be WITHOUT .csv extension.
        """
        if self.coupling_type == 'file':

            self.outputfilename = outputchannel
            self.inputfilename = inputchannel

    def generateOutputCSVString(self, t):
        out_csv_string = ""
        for i in range(0, len(self.location_ids)):
            if "out" in self.directions[i]:
                out_csv_string += "%s,%s\n" % (self.names[i], self.e.locations[
                                               self.location_ids[i]].numAgents)
                print("Couple OUT: %s %s" % (self.names[i], self.e.locations[
                      self.location_ids[i]].numAgents), file=sys.stderr)

        return out_csv_string

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

    def writeOutputToFile(self, t):
        out_csv_string = self.generateOutputCSVString(t)
        outputfile = '%s/file/coupled/%s[%d].%s.csv' % (
            self.outputdir, self.outputfilename, self.worker_index, t)

        with open(outputfile, 'a') as file:
            file.write(out_csv_string)

        print("%s[%d] t=%d Couple: output written to %s[%d].%s.csv" %
              (self.submodel, self.worker_index, t, self.outputfilename,
               self.worker_index, t), file=sys.stderr)

    def waitForInputFiles(self, check_dir, in_fnames):
        # input format for in_fnames : [dic{"fileName",False}]
        founded_files = 0
        # wait until input files from all workers are available
        while founded_files != len(in_fnames):
            time.sleep(0.1)
            for fname in in_fnames:
                if in_fnames[fname] == False:
                    if os.path.exists(os.path.join(check_dir, fname)):
                        in_fnames[fname] = True
                        founded_files += 1

    def readInputFromFile(self, t):
        """
        Returns a dictionary with key <coupling name> and value <number of agents>.
        """
        in_fnames = {}
        for i in range(self.num_workers):
            fname = "%s[%d].%s.csv" % (self.inputfilename,
                                       i, t)
            in_fnames[fname] = False

        dirInputFiles = os.path.join(self.outputdir,
                                     self.coupling_type, "coupled")
        # wait until input files from all workers are available
        self.waitForInputFiles(dirInputFiles, in_fnames)

        # aggrgate newAgents from each input files
        aggNewAgents = {}
        for i, fname in enumerate(in_fnames):
            with open(os.path.join(dirInputFiles, fname)) as csvfile:
                csv_string = csvfile.read().split('\n')

            curr_newAgent = self.extractNewAgentsFromCSVString(csv_string)
            if len(aggNewAgents) == 0:
                aggNewAgents = curr_newAgent
            else:
                for name in curr_newAgent:
                    if type(aggNewAgents[name]) is not list:
                        aggNewAgents[name] = [aggNewAgents[name]]
                    aggNewAgents[name].append(curr_newAgent[name])

        # combined founded newAgents per location by each worker into one
        # for now, we use arithmetic mean,
        # we may need to change it to another approach later
        for name in aggNewAgents:
            aggNewAgents[name] = int(round(np.mean(aggNewAgents[name])))

        return aggNewAgents

    #------------------------------------------------------------------------
    #                           log Exchanged Data
    #------------------------------------------------------------------------

    def saveExchangeDataToFile(self):
        # save logTotalAgents to file
        if hasattr(self, 'logTotalAgents'):
            filename = 'logTotalAgents_%s[%d].csv' % (self.submodel,
                                                      self.worker_index)
            outputfile = os.path.join(self.outputdir, self.coupling_type,
                                      'log_exchange_data', filename)
            # output csv header
            header_csv = "day,total_agents"
            with open(outputfile, 'a') as file:
                file.write("%s\n" % (header_csv))
                csvWriter = csv.writer(file, delimiter=',')
                csvWriter.writerows(self.logTotalAgents)

        # save logLocationsNumAgents to file
        if hasattr(self, 'logLocationsNumAgents'):
            filename = 'logLocationsNumAgents_%s[%d].csv' % (self.submodel,
                                                             self.worker_index)
            outputfile = os.path.join(self.outputdir, self.coupling_type,
                                      'log_exchange_data', filename)

            # output csv header
            header_csv = "day"
            for i in range(0, len(self.location_ids)):
                if "out" in self.directions[i]:
                    header_csv += ",%s" % (self.names[i])

            with open(outputfile, 'a') as file:
                file.write("%s\n" % (header_csv))
                csvWriter = csv.writer(file, delimiter=',')
                csvWriter.writerows(self.logLocationsNumAgents)

        # save logNewRefugees to file
        if hasattr(self, 'logNewRefugees'):
            filename = 'logNewRefugees_%s[%d].csv' % (self.submodel,
                                                      self.worker_index)
            outputfile = os.path.join(self.outputdir, self.coupling_type,
                                      'log_exchange_data', filename)
            # output csv header
            header_csv = "day,new_refs"
            with open(outputfile, 'a') as file:
                file.write("%s\n" % (header_csv))
                csvWriter = csv.writer(file, delimiter=',')
                csvWriter.writerows(self.logNewRefugees)

    def logNewAgents(self, t, new_refs):
        # create log all variables only if they are not exist
        if not hasattr(self, 'logNewRefugees'):
            self.logNewRefugees = []
            # logNewRefugees.append([day,new_refs])

        self.logNewRefugees.append([t, new_refs])

    def logExchangeData(self, t):

        # save log of total agents
        if not hasattr(self, 'logTotalAgents'):
            self.logTotalAgents = []
            # logTotalAgents.append([day,total_agents])

        self.logTotalAgents.append([t, self.e.total_agents])

        # save log of numAgents in locations
        if not hasattr(self, 'logLocationsNumAgents'):
            self.logLocationsNumAgents = []
            # logLocationsNumAgents.append([day,location_ids[i]].numAgents])

        data = [t]
        for i in range(0, len(self.location_ids)):
            if "out" in self.directions[i]:
                data.append(self.e.locations[self.location_ids[i]].numAgents)

        self.logLocationsNumAgents.append(data)

    #------------------------------------------------------------------------
    #                           Plotting functions
    #------------------------------------------------------------------------
    def plotExchangedData(self):

        if hasattr(self, 'logTotalAgents'):
            self.plotTotalAgentsHistory()

        if hasattr(self, 'logLocationsNumAgents'):
            self.plotLocationsNumAgentsHistory()

        if hasattr(self, 'logNewRefugees'):
            self.plotNewRefugeesHistory()

    def plotLocationsNumAgentsHistory(self):

        in_fnames = {}
        for i in range(self.num_workers):
            fname = "logLocationsNumAgents_%s[%d].csv" % (self.submodel,
                                                          i)
            in_fnames[fname] = False
        dirInputFiles = os.path.join(self.outputdir, self.coupling_type,
                                     "log_exchange_data")

        # wait until input files from all workers are available
        self.waitForInputFiles(dirInputFiles, in_fnames)

        csv_header = []
        for i in range(0, len(self.location_ids)):
            if "out" in self.directions[i]:
                csv_header.append(self.names[i])
        days, LocationsNumAgents = self.readCSVLogFiles(dirInputFiles, in_fnames,
                                                        csv_header)

        # plot data
        TOTAL = float(len(LocationsNumAgents))
        COLUMNS = 4
        # Compute Rows required
        ROWS = int(TOTAL / COLUMNS)
        ROWS += TOTAL % COLUMNS > 0
        # Create a Position index
        POSITION = range(1, int(TOTAL) + 1)

        cmp = sns.color_palette("colorblind", len(LocationsNumAgents))
        fig = plt.figure(figsize=(16, 7))
        # fig.suptitle(title)

        LINE_STYLES = ['solid', 'dashed', 'dotted']
        NUM_STYLES = len(LINE_STYLES)
        legends = []
        for i, (loc_name, loc_res) in enumerate(LocationsNumAgents.items()):
            fig.add_subplot(ROWS, COLUMNS, POSITION[
                i], frameon=False)
            # xlabel=xlabel, ylabel=ylabel)
            set_legend = True
            for res in loc_res:
                if set_legend:
                    plt.plot(days, res, color=cmp[i],
                             linestyle=LINE_STYLES[i % NUM_STYLES], label=loc_name)
                    set_legend = False
                else:
                    plt.plot(days, res, color=cmp[i],
                             linestyle=LINE_STYLES[i % NUM_STYLES])

            plt.legend()
            ymin, ymax = plt.ylim()
            plt.ylim(0, ymax if ymax > 1 else 1)

        plt.tight_layout()
        outputPlotFile = os.path.join(self.outputdir, self.coupling_type,
                                      "plot_exchange_data",
                                      "plotLocationsNumAgents[%s].pdf" % (self.submodel))
        plt.savefig(outputPlotFile)

    def plotTotalAgentsHistory(self):

        in_fnames = {}
        for i in range(self.num_workers):
            fname = "logTotalAgents_%s[%d].csv" % (self.submodel,
                                                   i)
            in_fnames[fname] = False
        dirInputFiles = os.path.join(self.outputdir, self.coupling_type,
                                     "log_exchange_data")

        # wait until input files from all workers are available
        self.waitForInputFiles(dirInputFiles, in_fnames)

        csv_header = ["total_agents"]
        days, TotalAgents = self.readCSVLogFiles(dirInputFiles, in_fnames,
                                                 csv_header)

        # plotting preparation
        cmp = sns.color_palette("colorblind", self.num_workers)
        fig = plt.figure()
        ax = fig.add_subplot(111, xlabel='day', ylabel='total_agents')

        # plot newAgents from each input files
        for column_header in TotalAgents.keys():
            for i, data in enumerate(TotalAgents[column_header]):
                total_agents = data
                label = "%s[%d]" % (self.submodel, i)
                plt.plot(days, total_agents, color=cmp[i], label=label)

        plt.legend()
        plt.tight_layout()
        outputPlotFile = os.path.join(self.outputdir, self.coupling_type,
                                      "plot_exchange_data",
                                      "plotTotalAgents[%s].pdf" % (self.submodel))
        plt.savefig(outputPlotFile)

    def plotNewRefugeesHistory(self):
        in_fnames = {}

        for i in range(self.num_workers):
            fname = "logNewRefugees_%s[%d].csv" % (self.submodel,
                                                   i)
            in_fnames[fname] = False
        dirInputFiles = os.path.join(self.outputdir, self.coupling_type,
                                     "log_exchange_data")

        # wait until input files from all workers are available
        self.waitForInputFiles(dirInputFiles, in_fnames)

        csv_header = ["new_refs"]
        days, NewRefugees = self.readCSVLogFiles(dirInputFiles, in_fnames,
                                                 csv_header)

        # plotting preparation
        cmp = sns.color_palette("colorblind", self.num_workers)
        fig = plt.figure()
        ax = fig.add_subplot(111, xlabel='day', ylabel='NewRefugees')
        # plot NewRefugees from each input files
        for column_header in NewRefugees.keys():
            for i, data in enumerate(NewRefugees[column_header]):
                total_agents = data
                label = "%s[%d]" % (self.submodel, i)
                # for fist day, we have high number of NewRefugees
                plt.plot(days[1:], total_agents[1:], color=cmp[i], label=label)

        plt.legend()
        plt.tight_layout()
        outputPlotFile = os.path.join(self.outputdir, self.coupling_type,
                                      "plot_exchange_data",
                                      "plotNewRefugees[%s].pdf" % (self.submodel))
        plt.savefig(outputPlotFile)

    def readCSVLogFiles(self, dirInputFiles, inputFileNames, columnHeader):
        dict_res = {}
        days = []
        for name in columnHeader:
            dict_res[name] = []

        for i, fname in enumerate(inputFileNames):
            with open(os.path.join(dirInputFiles, fname), "rb") as csvfile:
                data = np.loadtxt(csvfile, delimiter=",", skiprows=1)

                # keep day column for plotting purpose
                if len(days) == 0:
                    days = data[:, 0]

                # remove day column
                data = np.delete(data, 0, 1)

                for j, name in enumerate(dict_res):
                    dict_res[name].append(data[:, j])

        return days, dict_res
