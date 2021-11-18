from __future__ import annotations, print_function

import csv
import logging
import os.path
import sys
import time
from functools import wraps
from typing import List, Tuple

import matplotlib

# pylint: disable=wrong-import-position
matplotlib.use("Agg")
# pylint: enable=wrong-import-position
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from libmuscle import Instance, Message
from ymmsl import Operator

if os.getenv("FLEE_TYPE_CHECK") is not None and os.environ["FLEE_TYPE_CHECK"].lower() == "true":
    from beartype import beartype as check_args_type
else:

    def check_args_type(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper


class CouplingInterface:
    """
    The Coupling Interface class
    """

    @check_args_type
    def __init__(
        self,
        e,
        submodel: str,
        instance_index: int = None,
        num_instances: int = None,
        coupling_type: str = "file",
        weather_coupling: bool = False,
        outputdir: str = "out",
        log_exchange_data: bool = True,
    ) -> None:
        """
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
        self.instance_index = instance_index
        self.num_instances = num_instances

        # for logging
        self.log_exchange_data = log_exchange_data

        if self.coupling_type == "muscle3":
            self.logger = logging.getLogger()
            self.logger.propagate = False

            if self.submodel in ["macro", "micro"]:
                self.instance = Instance({Operator.O_I: ["out"], Operator.S: ["in"]})
            elif self.submodel in ["macro_manager", "micro_manager"]:
                self.instance = Instance({Operator.O_I: ["out[]"], Operator.S: ["in[]"]})

    # pylint: disable=missing-function-docstring
    def reuse_coupling(self):
        if self.coupling_type == "file":
            return True

        if self.coupling_type == "muscle3":
            return self.instance.reuse_instance()

    @check_args_type
    def addCoupledLocation(
        self, location, name: str, direction: str = "inout", interval: int = 1
    ) -> None:
        """

        Adds a locations to the so-called *Coupled Region*.

        Args:
            location (Location): is the (p)Flee location object.
            name (str): Name is a location identifier that is identical to the one
                in the other code.
            direction (str, optional): Direction can be (once the code is done):
                - `out` -> agents are removed and stored in the coupling link.
                - `in` -> agents written to the coupling link by the other process
                        are added to this location.
                - `inout` -> both out and in.
                - `inout indirect` -> changes in agent numbers are stored in the
                    coupling link. No agents are added or removed.
            interval (int, optional): is the timestep interval of the coupling, ensuring that the
                coupling activity is performed every <interval> time steps.
        """
        if location.name not in self.location_names:

            self.location_ids += [self.e._convert_location_name_to_index(name=location.name)]
            self.location_names += [location.name]
            """
            disabled by HAMID
            print("Adding coupled location {} {} {}".format(
                location.name, direction, interval), file=sys.stderr)
            """
            self.names += [name]
            self.directions += [direction]
            self.intervals += [interval]
            self.coupling_rank = True
            if hasattr(self.e, "mpi") and self.e.mpi is not None:
                if self.e.mpi.rank > 0:
                    self.coupling_rank = False

        else:
            print(
                "{} --> warning: coupled location [{}] is selected twice "
                "(ignore this if a location is both a coupled location and "
                "a conflict location). Only one coupled location will be "
                "created.".format(self.submodel, location.name),
                file=sys.stderr,
            )

    def addGhostLocations(self, ig) -> None:
        """
        Summary

        Args:
            ig (Type[InputGeography]): Description
        """
        conflict_name_list = ig.getConflictLocationNames()
        print("Adding Ghosts", file=sys.stderr)

        for conflict_name in conflict_name_list:
            for i, location_name in enumerate(self.e.locationNames):
                if location_name == conflict_name:
                    loc = self.e.locations[i]
                    # print("L", loc.name, len(loc.links), file=sys.stderr)
                    if len(loc.links) == 0:
                        if loc.name not in self.location_names:
                            print("Adding ghost location {}".format(loc.name), file=sys.stderr)
                            self.addCoupledLocation(
                                location=loc, name=loc.name, direction="out", interval=1
                            )

    def addMicroConflictLocations(self, ig) -> None:
        """
        Summary

        Args:
            ig (Type[InputGeography]): Description
        """
        conflict_name_list = ig.getConflictLocationNames()
        print("Adding micro conflict coupling", file=sys.stderr)

        for conflict_name in conflict_name_list:
            for i, location_name in enumerate(self.e.locationNames):
                if location_name == conflict_name:
                    loc = self.e.locations[i]
                    # print("L", loc.name, len(loc.links), file=sys.stderr)
                    print(
                        "Adding micro coupled conflict location {}".format(loc.name),
                        file=sys.stderr,
                    )

                    self.addCoupledLocation(location=loc, name=loc.name, direction="in", interval=1)

    @check_args_type
    def Couple(self, time: int) -> None:
        """
        Summary

        Args:
            time (int): Description
        """

        newAgents = None

        # for the time being all intervals will have to be the same...

        # for current interval=1 we can ignore this check, but it should be
        # added later if we need higher interval values here
        if time % self.intervals[0] == 0:
            # if True:
            if self.coupling_type == "muscle3":
                if self.coupling_rank:
                    # If MPI is used, this will be the process with rank 0
                    if self.submodel == "macro_manager":

                        # collect output from each macro instance
                        newAgents = {}
                        for slot in range(self.num_instances):
                            msg = self.instance.receive("in", slot)
                            curr_newAgent = self.extractNewAgentsFromCSVString(
                                csv_string=msg.data["newAgents"].split("\n")
                            )

                            if len(newAgents) == 0:
                                newAgents = curr_newAgent
                            else:
                                for name, newAgents_num in curr_newAgent.items():
                                    if not isinstance(newAgents[name], list):
                                        newAgents[name] = [newAgents[name]]
                                    newAgents[name].append(newAgents_num)

                        # combined founded newAgents per location by each
                        # instance into one
                        # for now, we use arithmetic mean,
                        # we may need to change it to another approach later
                        for name in newAgents:
                            newAgents[name] = int(round(np.mean(newAgents[name])))

                        data_to_micro = "\n".join(
                            "{},{}".format(key, value) for key, value in newAgents.items()
                        )

                        for slot in range(self.num_instances):
                            self.instance.send("out", Message(time, None, data_to_micro), slot)

                    elif self.submodel == "micro_manager":

                        # receive from micro
                        newAgents = {}
                        for slot in range(self.num_instances):
                            msg = self.instance.receive("in", slot)
                            curr_newAgent = self.extractNewAgentsFromCSVString(
                                csv_string=msg.data["newAgents"].split("\n")
                            )

                            if len(newAgents) == 0:
                                newAgents = curr_newAgent
                            else:
                                for name, newAgents_num in curr_newAgent.items():
                                    if not isinstance(newAgents[name], list):
                                        newAgents[name] = [newAgents[name]]
                                    newAgents[name].append(newAgents_num)

                        # combined founded newAgents per location by
                        # each instance into one
                        # for now, we use arithmetic mean,
                        # we may need to change it to another approach later
                        for name in newAgents:
                            newAgents[name] = int(round(np.mean(newAgents[name])))

                        data_to_macro = "\n".join(
                            "{},{}".format(key, value) for key, value in newAgents.items()
                        )
                        # send to macro
                        for slot in range(self.num_instances):
                            self.instance.send("out", Message(time, None, data_to_macro), slot)

                    elif self.submodel in ["macro", "micro"]:

                        newAgents_str = self.generateOutputCSVString()
                        # here, in addition to newAgents, we can also pass
                        # other variables if are required
                        msg = {"newAgents": newAgents_str}
                        self.instance.send("out", Message(time, None, msg))

                        if self.log_exchange_data is True:
                            self.logExchangeData(t=time)

                        msg = self.instance.receive("in")
                        newAgents = self.extractNewAgentsFromCSVString(
                            csv_string=msg.data.split("\n")
                        )

                # If MPI is used, broadcast newAgents to all other processes
                if hasattr(self.e, "mpi") and self.e.mpi is not None:
                    newAgents = self.e.mpi.comm.bcast(newAgents, root=0)

            elif self.coupling_type == "file":
                # default is coupling through file IO.
                if self.coupling_rank:
                    # If MPI is used, this will be the process with rank 0
                    self.writeOutputToFile(day=time)
                    if self.log_exchange_data is True:
                        self.logExchangeData(t=time)

                newAgents = self.readInputFromFile(t=time)

            if self.submodel in ["micro", "macro"]:
                self.e.clearLocationsFromAgents(location_names=self.location_names)
                for i in range(0, len(self.location_names)):
                    # write departing agents to file
                    # read incoming agents from file
                    # print(self.names, i, newAgents)
                    if "in" in self.directions[i]:

                        print(
                            "Couple IN: {} {}".format(self.names[i], newAgents[self.names[i]]),
                            file=sys.stderr,
                        )

                        if self.names[i] in newAgents:
                            self.e.insertAgents(
                                location=self.e.locations[self.location_ids[i]],
                                number=newAgents[self.names[i]],
                            )
                    if hasattr(self.e, "mpi"):
                        self.e.updateNumAgents(log=False)

    @check_args_type
    def setCouplingChannel(self, outputchannel: str, inputchannel: str) -> None:
        """
        Sets the coupling output file name (for file coupling).
        Name should be WITHOUT .csv extension.

        Args:
            outputchannel (str): Description
            inputchannel (str): Description
        """
        if self.coupling_type == "file":

            self.outputfilename = outputchannel
            self.inputfilename = inputchannel

    @check_args_type
    def generateOutputCSVString(self) -> str:
        """
        Summary

        Returns:
            str: Description
        """
        out_csv_string = ""
        for i, location_id in enumerate(self.location_ids):
            if "out" in self.directions[i]:
                out_csv_string += "{},{}\n".format(
                    self.names[i], self.e.locations[location_id].numAgents
                )
                print(
                    "Couple OUT: {} {}".format(
                        self.names[i], self.e.locations[location_id].numAgents
                    ),
                    file=sys.stderr,
                )

        return out_csv_string

    @check_args_type
    def extractNewAgentsFromCSVString(self, csv_string: List[str]) -> dict:
        """
        Reads in a CSV string with coupling information, and extracts a list
        of New Agents.

        Args:
            csv_string (List[str]): Description

        Returns:
            dict: Description
        """
        newAgents = {}

        for line in csv_string:
            row = line.split(",")
            if len(row[0]) == 0:
                continue
            if row[0][0] == "#":
                pass
            else:
                for i in range(0, len(self.location_ids)):
                    if row[0] == self.names[i]:
                        newAgents[self.names[i]] = int(row[1])

        return newAgents

    @check_args_type
    def writeOutputToFile(self, day: int) -> None:
        """
        Summary

        Args:
            day (int): Description

        """
        out_csv_string = self.generateOutputCSVString()
        csv_outputfile_name = "{}[{}].{}.csv".format(self.outputfilename, self.instance_index, day)
        csv_outputfile_path = os.path.join(self.outputdir, "file", "coupled", csv_outputfile_name)

        with open(csv_outputfile_path, "a", encoding="utf-8") as file:
            file.write(out_csv_string)

        print(
            "{}[{}] t={} Couple: output written to {}".format(
                self.submodel, self.instance_index, day, csv_outputfile_name
            ),
            file=sys.stderr,
        )

    @check_args_type
    def waitForInputFiles(self, check_dir: str, in_fnames: dict) -> None:
        """
        Summary

        Args:
            check_dir (str): Description
            in_fnames (str): Description
        """
        # input format for in_fnames : [dic{"fileName",False}]
        founded_files = 0
        # wait until input files from all instances are available
        while founded_files != len(in_fnames):
            time.sleep(0.1)
            for fname in in_fnames:
                if in_fnames[fname] is False:
                    if os.path.exists(os.path.join(check_dir, fname)):
                        in_fnames[fname] = True
                        founded_files += 1

    @check_args_type
    def readInputFromFile(self, t: int) -> dict:
        """
        Returns a dictionary with key <coupling name> and
        value <number of agents>.

        Args:
            t (int): Description

        Returns:
            dict: Description
        """
        in_fnames = {}
        for i in range(self.num_instances):
            fname = "{}[{}].{}.csv".format(self.inputfilename, i, t)
            in_fnames[fname] = False

        dirInputFiles = os.path.join(self.outputdir, self.coupling_type, "coupled")
        # wait until input files from all instances are available
        self.waitForInputFiles(check_dir=dirInputFiles, in_fnames=in_fnames)

        # aggrgate newAgents from each input files
        aggNewAgents = {}
        for fname in in_fnames:
            with open(os.path.join(dirInputFiles, fname), encoding="utf-8") as csvfile:
                csv_string = csvfile.read().split("\n")

            curr_newAgent = self.extractNewAgentsFromCSVString(csv_string=csv_string)
            if len(aggNewAgents) == 0:
                aggNewAgents = curr_newAgent
            else:
                for name, newAgents_num in curr_newAgent.items():
                    if not isinstance(aggNewAgents[name], list):
                        aggNewAgents[name] = [aggNewAgents[name]]
                    aggNewAgents[name].append(newAgents_num)

        # combined founded newAgents per location by each instance into one
        # for now, we use arithmetic mean,
        # we may need to change it to another approach later
        for name in aggNewAgents:
            aggNewAgents[name] = int(round(np.mean(aggNewAgents[name])))

        return aggNewAgents

    # ------------------------------------------------------------------------
    #                           log Exchanged Data
    # ------------------------------------------------------------------------

    def saveExchangeDataToFile(self) -> None:
        """
        Summary
        """
        # save logTotalAgents to file
        if hasattr(self, "logTotalAgents"):
            filename = "logTotalAgents_{}[{}].csv".format(self.submodel, self.instance_index)
            outputfile = os.path.join(
                self.outputdir, self.coupling_type, "log_exchange_data", filename
            )
            # output csv header
            header_csv = "day,total_agents"
            with open(outputfile, "a", encoding="utf-8") as file:
                file.write("{}\n".format(header_csv))
                csvWriter = csv.writer(file, delimiter=",")
                csvWriter.writerows(self.logTotalAgents)

        # save logLocationsNumAgents to file
        if hasattr(self, "logLocationsNumAgents"):
            filename = "logLocationsNumAgents_{}[{}].csv".format(self.submodel, self.instance_index)
            outputfile = os.path.join(
                self.outputdir, self.coupling_type, "log_exchange_data", filename
            )

            # output csv header
            header_csv = "day"
            for i in range(0, len(self.location_ids)):
                if "out" in self.directions[i]:
                    header_csv += ",{}".format(self.names[i])

            with open(outputfile, "a", encoding="utf-8") as file:
                file.write("{}\n".format(header_csv))
                csvWriter = csv.writer(file, delimiter=",")
                csvWriter.writerows(self.logLocationsNumAgents)

        # save logNewRefugees to file
        if hasattr(self, "logNewRefugees"):
            filename = "logNewRefugees_{}[{}].csv".format(self.submodel, self.instance_index)
            outputfile = os.path.join(
                self.outputdir, self.coupling_type, "log_exchange_data", filename
            )
            # output csv header
            header_csv = "day,new_refs"
            with open(outputfile, "a", encoding="utf-8") as file:
                file.write("{}\n".format(header_csv))
                csvWriter = csv.writer(file, delimiter=",")
                csvWriter.writerows(self.logNewRefugees)

    @check_args_type
    def logNewAgents(self, t: int, new_refs: int) -> None:
        """
        create log all variables only if they are not exist

        Args:
            t (int): Description
            new_refs (int): Description
        """
        if not hasattr(self, "logNewRefugees"):
            self.logNewRefugees = []
            # logNewRefugees.append([day,new_refs])

        self.logNewRefugees.append([t, new_refs])

    @check_args_type
    def logExchangeData(self, t: int) -> None:
        """
        Summary

        Args:
            t (int): Description
        """
        # save log of total agents
        if not hasattr(self, "logTotalAgents"):
            self.logTotalAgents = []
            # logTotalAgents.append([day,total_agents])

        self.logTotalAgents.append([t, self.e.total_agents])

        # save log of numAgents in locations
        if not hasattr(self, "logLocationsNumAgents"):
            self.logLocationsNumAgents = []
            # logLocationsNumAgents.append([day,location_ids[i]].numAgents])

        data = [t]
        for i, location_id in enumerate(self.location_ids):
            if "out" in self.directions[i]:
                data.append(self.e.locations[location_id].numAgents)

        self.logLocationsNumAgents.append(data)

    def sumOutputCSVFiles(self) -> None:
        """
        Summary
        """
        in_fnames = {}
        for i in range(self.num_instances):
            fname = "out[{}].csv".format(i)
            in_fnames[fname] = False

        dirInputFiles = os.path.join(self.outputdir, self.coupling_type, self.submodel)

        # wait until input files from all instances are available
        self.waitForInputFiles(check_dir=dirInputFiles, in_fnames=in_fnames)

        dfs = []
        for fname in in_fnames:
            df = pd.read_csv(os.path.join(dirInputFiles, fname), index_col=None, header=0)
            dfs.append(df)

        frame = pd.concat(dfs, axis=0, ignore_index=True).groupby(["Day"]).mean()

        for column_name in list(frame):
            if "error" not in column_name.lower():
                frame[column_name].round(0).astype(int)

        df.to_csv(os.path.join(dirInputFiles, "out.csv"), encoding="utf-8", index=False)

    # ------------------------------------------------------------------------
    #                           Plotting functions
    # ------------------------------------------------------------------------

    def plotExchangedData(self) -> None:
        """
        Summary
        """
        if hasattr(self, "logTotalAgents"):
            self.plotTotalAgentsHistory()

        if hasattr(self, "logLocationsNumAgents"):
            self.plotLocationsNumAgentsHistory()

        if hasattr(self, "logNewRefugees"):
            self.plotNewRefugeesHistory()

    def plotLocationsNumAgentsHistory(self) -> None:
        """
        Summary
        """
        in_fnames = {}
        for i in range(self.num_instances):
            fname = "logLocationsNumAgents_{}[{}].csv".format(self.submodel, i)
            in_fnames[fname] = False
        dirInputFiles = os.path.join(self.outputdir, self.coupling_type, "log_exchange_data")

        # wait until input files from all instances are available
        self.waitForInputFiles(check_dir=dirInputFiles, in_fnames=in_fnames)

        csv_header = []
        for i in range(0, len(self.location_ids)):
            if "out" in self.directions[i]:
                csv_header.append(self.names[i])
        days, LocationsNumAgents = self.readCSVLogFiles(
            dirInputFiles=dirInputFiles,
            inputFileNames=list(in_fnames.keys()),
            columnHeader=csv_header
        )

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

        LINE_STYLES = ["solid", "dashed", "dotted"]
        NUM_STYLES = len(LINE_STYLES)
        for i, (loc_name, loc_res) in enumerate(LocationsNumAgents.items()):
            fig.add_subplot(ROWS, COLUMNS, POSITION[i], frameon=False)
            # xlabel=xlabel, ylabel=ylabel)
            set_legend = True
            for res in loc_res:
                if set_legend:
                    plt.plot(
                        days,
                        res,
                        color=cmp[i],
                        linestyle=LINE_STYLES[i % NUM_STYLES],
                        label=loc_name,
                    )
                    set_legend = False
                else:
                    plt.plot(days, res, color=cmp[i], linestyle=LINE_STYLES[i % NUM_STYLES])

            plt.legend()
            _, ymax = plt.ylim()  # returns bottom and top of the current ylim
            plt.ylim(0, ymax if ymax > 1 else 1)

        plt.tight_layout()
        outputPlotFile = os.path.join(
            self.outputdir,
            self.coupling_type,
            "plot_exchange_data",
            "plotLocationsNumAgents[{}].pdf".format(self.submodel),
        )
        plt.savefig(outputPlotFile)

    def plotTotalAgentsHistory(self) -> None:
        """
        Summary
        """
        in_fnames = {}
        for i in range(self.num_instances):
            fname = "logTotalAgents_{}[{}].csv".format(self.submodel, i)
            in_fnames[fname] = False

        dirInputFiles = os.path.join(self.outputdir, self.coupling_type, "log_exchange_data")

        # wait until input files from all instances are available
        self.waitForInputFiles(check_dir=dirInputFiles, in_fnames=in_fnames)

        csv_header = ["total_agents"]
        days, TotalAgents = self.readCSVLogFiles(
            dirInputFiles=dirInputFiles,
            inputFileNames=list(in_fnames.keys()),
            columnHeader=csv_header
        )

        # plotting preparation
        cmp = sns.color_palette("colorblind", self.num_instances)
        fig = plt.figure()
        _ = fig.add_subplot(111, xlabel="day", ylabel="total_agents")

        # plot newAgents from each input files
        for _, data in TotalAgents.items():
            for i, total_agents in enumerate(data):
                label = "{}[{}]".format(self.submodel, i)
                plt.plot(days, total_agents, color=cmp[i], label=label)

        plt.legend()
        plt.tight_layout()
        outputPlotFile = os.path.join(
            self.outputdir,
            self.coupling_type,
            "plot_exchange_data",
            "plotTotalAgents[{}].pdf".format(self.submodel),
        )
        plt.savefig(outputPlotFile)

    def plotNewRefugeesHistory(self) -> None:
        """
        Summary
        """
        in_fnames = {}

        for i in range(self.num_instances):
            fname = "logNewRefugees_{}[{}].csv".format(self.submodel, i)
            in_fnames[fname] = False

        dirInputFiles = os.path.join(self.outputdir, self.coupling_type, "log_exchange_data")

        # wait until input files from all instances are available
        self.waitForInputFiles(check_dir=dirInputFiles, in_fnames=in_fnames)

        csv_header = ["new_refs"]
        days, NewRefugees = self.readCSVLogFiles(
            dirInputFiles=dirInputFiles,
            inputFileNames=list(in_fnames.keys()),
            columnHeader=csv_header
        )

        # plotting preparation
        cmp = sns.color_palette("colorblind", self.num_instances)
        fig = plt.figure()
        _ = fig.add_subplot(111, xlabel="day", ylabel="NewRefugees")
        # plot NewRefugees from each input files
        for _, data in NewRefugees.items():
            for i, total_agents in enumerate(data):
                label = "{}[{}]".format(self.submodel, i)
                # for fist day, we have high number of NewRefugees
                plt.plot(days[1:], total_agents[1:], color=cmp[i], label=label)

        plt.legend()
        plt.tight_layout()
        outputPlotFile = os.path.join(
            self.outputdir,
            self.coupling_type,
            "plot_exchange_data",
            "plotNewRefugees[{}].pdf".format(self.submodel),
        )
        plt.savefig(outputPlotFile)

    @check_args_type
    def readCSVLogFiles(
        self, dirInputFiles: str, inputFileNames: List[str], columnHeader: List[str]
    ) -> Tuple[np.ndarray, dict]:
        """
        Summary

        Args:
            dirInputFiles (str): Description
            inputFileNames (List[str]): Description
            columnHeader (List[str]): Description

        No Longer Returned:
            Tuple[np.ndarray, dict]: Description
        """
        dict_res = {}
        days = np.array([])
        for name in columnHeader:
            dict_res[name] = []

        for fname in inputFileNames:
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
