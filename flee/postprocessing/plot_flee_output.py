import os
from os.path import normpath, basename, isfile
import sys
import numpy as np
import pandas as pd
import argparse
import matplotlib.pyplot as plt
from flee.postprocessing import analysis as a
import matplotlib
matplotlib.use('Pdf')


class LocationErrors:
    """
    Class containing a dictionary of errors and diagnostics pertaining
    a single location.
    """

    def __init__(self):
        self.errors = {}


class SimulationErrors:
    """
    Class containing all error measures within a single simulation.
    It should be initialized with a Python list of the LocationErrors
    structure for all of the relevant locations.
    """

    def __init__(self, location_errors):
        self.location_errors = location_errors

    def abs_diff(self, rescaled=True):

        # true_total_refs is the number of total refugees according to the data.

        errtype = "absolute difference"
        if rescaled:
            errtype = "absolute difference rescaled"

        self.tmp = self.location_errors[0].errors[errtype]

        for lerr in self.location_errors[1:]:
            self.tmp = np.add(self.tmp, lerr.errors[errtype])

        return self.tmp

    def get_error(self, err_type):
        
        # Here err_type is the string name of the error that needs to be aggregated.
        
        self.tmp = self.location_errors[0].errors[
            err_type] * self.location_errors[0].errors["N"]
        N = self.location_errors[0].errors["N"]

        for lerr in self.location_errors[1:]:
            self.tmp = np.add(self.tmp, lerr.errors[
                              err_type] * lerr.errors["N"])
            N += lerr.errors["N"]

        # print(self.tmp, N, self.tmp/ N)
        return self.tmp / N


def plot_camps(data, config, output):

    # Plotting function for camps. #

    data_filtered = data.drop(['Total error', 'refugees in camps (UNHCR)',
                               'total refugees (simulation)',
                               'raw UNHCR refugee count',
                               'refugees in camps (simulation)',
                               'refugee_debt'], axis=1)

    cols = list(data_filtered.columns.values)

    output = os.path.join(output, 'camps')

    mkdir_p(output)

    for i in range(len(cols)):

        name = cols[i].split()

        y1 = data_filtered["%s sim" % name[0]]
        y2 = data_filtered["%s data" % name[0]]

        fig = matplotlib.pyplot.gcf()
        fig.set_size_inches(14, 10)

        plt.xlabel("Days elapsed")
        plt.ylabel("Number of refugees")
        plt.title("{} Simulation".format(name[0]))

        label1, = plt.plot(data_filtered.index, y1, 'g',
                           linewidth=5, label="{} Simulation".format(name[0]))
        label2, = plt.plot(data_filtered.index, y2, 'b',
                           linewidth=5, label="UNHCR data")

        plt.legend(handles=[label1, label2], loc=0, prop={'size': 14})

        plt.savefig("{}/{}.png".format(output, name[0]))

        plt.clf()


def plot_numagents(data, config, output):

    # Plotting and saving NUMAGENTS (total refugee numbers) graph #

    output = os.path.join(output, 'numagents')

    mkdir_p(output)

    if "refugee_debt" in data.columns:
        data.loc[:, ["total refugees (simulation)",
                     "refugees in camps (simulation)",
                     "raw UNHCR refugee count",
                     "refugee_debt"]].plot(linewidth=5)
        '''
        plt.legend(handles=[total_refugees1, total_refugees2,
                            refugees_in_camps1, refugees_in_camps2,
                            raw_refugee_count, refugee_debt_simulation],
                   loc=0, prop={'size': 14})
        '''

    else:
        data.loc[:, ["total refugees (simulation)",
                     "refugees in camps (UNHCR)",
                     "raw UNHCR refugee count"]].plot(linewidth=5)

        '''
        plt.legend(handles=[total_refugees1, total_refugees2,
                            refugees_in_camps1, refugees_in_camps2,
                            raw_refugee_count],
                   loc=0, prop={'size': 14})
        '''

    plt.xlabel("Days elapsed")
    plt.ylabel("Number of refugees")
    plt.title("{} number of agents".format(config))

    matplotlib.rcParams.update({'font.size': 20})

    # Size of plots/figures
    fig = matplotlib.pyplot.gcf()
    fig.set_size_inches(14, 10)

    set_margins()

    plt.savefig("{}/numagents.png".format(output))

    plt.clf()


def plot_errors(data, config, output, model='macro'):

    output = os.path.join(output, 'errors')

    mkdir_p(output)

    un_refs = data.loc[:, ["refugees in camps (UNHCR)"]].to_numpy().flatten()

    loc_errors = []

    nmodel = False

    cols = list(data.columns.values)

    location_names = []

    for i in cols:
        if " sim" in i:
            if "numAgents" not in i:
                location_names.append(' '.join(i.split()[:-1]))

    for i in location_names:
        loc_errors.append(error_quantification(
            output, data, i, naieve_model=nmodel))

    sim_errors = SimulationErrors(loc_errors)

    matplotlib.rcParams.update({'font.size': 20})

    plt.clf()

    # Size of plots/figures
    fig = matplotlib.pyplot.gcf()

    fig.set_size_inches(14, 10)

    set_margins()

    #################################################
    # Plotting and saving error (differences) graph #
    #################################################

    plt.ylabel("Averaged relative difference")
    plt.xlabel("Days elapsed")
    plt.title("{} errors".format(config))

    diffdata = sim_errors.abs_diff(
        rescaled=False) / np.maximum(un_refs, np.ones(len(un_refs)))
    diffdata_rescaled = sim_errors.abs_diff() / \
        np.maximum(un_refs, np.ones(len(un_refs)))

    print("%s - %s model: Averaged error normal: " % (config, model),
          np.mean(diffdata), ", rescaled: ", np.mean(diffdata_rescaled),
          ", len: ", len(diffdata))

    labeldiff_rescaled, = plt.plot(np.arange(len(diffdata_rescaled)),
                                   diffdata_rescaled,
                                   linewidth=5, label="Error")

    plt.legend(handles=[labeldiff_rescaled], loc=7, prop={'size': 14})

    set_margins()

    plt.savefig("{}/error.png".format(output))

    ###############################################
    #               ERROR COMPARISON              #
    ###############################################

    labeldiff, = plt.plot(np.arange(len(diffdata)), diffdata,
                          linewidth=5, label="error (not rescaled)")

    plt.legend(handles=[labeldiff, labeldiff_rescaled],
               loc=1, prop={'size': 14})

    set_margins()

    plt.savefig("{}/error_comparison.png".format(output))

    plt.clf()


def error_quantification(config, data, name, naieve_model=True):
    """
    Error quantification function to quantify the errors and mismatches
    for camps.
    """
    y1 = data["%s sim" % name].to_numpy()

    y2 = data["%s data" % name].to_numpy()

    simtot = data["refugees in camps (simulation)"].to_numpy().flatten()

    untot = data["refugees in camps (UNHCR)"].to_numpy().flatten()

    y1_rescaled = np.zeros(len(y1))

    for i in range(0, len(y1_rescaled)):
        # Only rescale if simtot > 0
        if simtot[i] > 0:
            y1_rescaled[i] = y1[i] * untot[i] / simtot[i]

    naieve_early_day = 7

    naieve_training_day = 30

    days = np.arange(len(y1))

    lerr = LocationErrors()

    # absolute difference
    lerr.errors["absolute difference"] = a.abs_diffs(y1, y2)

    # absolute difference (rescaled)
    lerr.errors["absolute difference rescaled"] = a.abs_diffs(y1_rescaled, y2)

    # ratio difference
    lerr.errors["ratio difference"] = a.abs_diffs(
        y1, y2) / (np.maximum(untot, np.ones(len(untot))))

    # We can only calculate the Mean Absolute Scaled Error if we have a naieve
    # model in our plot.
    if naieve_model:

        # Number of observations (aggrgate refugee days in UNHCR data set for
        # this location)
        lerr.errors["N"] = np.sum(y2)

        # flat naieve model (7 day)
        lerr.errors["MASE7"] = a.calculate_MASE(
            y1_rescaled, y2, n1, naieve_early_day)
        lerr.errors["MASE7-sloped"] = a.calculate_MASE(y1_rescaled,
                                                       y2, n3,
                                                       naieve_early_day)
        lerr.errors["MASE7-ratio"] = a.calculate_MASE(y1_rescaled,
                                                      y2, n5,
                                                      naieve_early_day)

        # flat naieve model (30 day)
        lerr.errors["MASE30"] = a.calculate_MASE(
            y1_rescaled, y2, n2, naieve_training_day)
        lerr.errors["MASE30-sloped"] = a.calculate_MASE(y1_rescaled,
                                                        y2, n4,
                                                        naieve_training_day)
        lerr.errors[
            "MASE30-ratio"] = a.calculate_MASE(y1_rescaled,
                                               y2, n6,
                                               naieve_training_day)

        print("%s,%s,%s,%s,%s,%s,%s,%s,%s" % (
            config, name, lerr.errors["MASE7"],
            lerr.errors["MASE7-sloped"],
            lerr.errors["MASE7-ratio"],
            lerr.errors["MASE30"],
            lerr.errors["MASE30-sloped"],
            lerr.errors["MASE30-ratio"],
            lerr.errors["N"])
        )

    return lerr

def plot_aggregated_errors(macro_df, micro_df, config, macro_output_dir, micro_output_dir):

    
    # Macro and Micro Concatination
    #######################################################################################

    macro_filtered = macro_df.drop(['Total error', 'refugees in camps (UNHCR)', 'total refugees (simulation)',
     'raw UNHCR refugee count', 'refugees in camps (simulation)', 'refugee_debt'], axis=1)

    micro_filtered = micro_df.drop(['Total error', 'refugees in camps (UNHCR)', 'total refugees (simulation)',
     'raw UNHCR refugee count', 'refugees in camps (simulation)', 'refugee_debt'], axis=1)
    
    merged_file_out = pd.concat([macro_filtered, micro_filtered], axis=1, sort=False)

    # Identifying location names for graphs

    cols = list(merged_file_out.columns.values)

    location_names = []

    for i in cols:
            if " sim" in i:
                if "numAgents" not in i:
                    location_names.append(' '.join(i.split()[:-1])) 

    # abs Error calculations
    abs_error = 0
    for i in location_names:
        abs_error += merged_file_out["{} sim".format(i)] - merged_file_out["{} data".format(i)]  

    merged_file_out["abs error"] = round(abs(abs_error), a.ROUND_NDIGITS)

    merged_file_out["raw UNHCR refugee count"] = macro_df["raw UNHCR refugee count"]

    total_error = round((merged_file_out["abs error"] / merged_file_out["raw UNHCR refugee count"]).fillna(0), a.ROUND_NDIGITS)
        
    merged_file_out["total_error"] = total_error

    merged_file_out["refugees in camps (UNHCR)"] = macro_df["refugees in camps (UNHCR)"] + micro_df["refugees in camps (UNHCR)"]

    merged_file_out["total refugees (simulation)"] = macro_df["total refugees (simulation)"] + micro_df["total refugees (simulation)"]

    merged_file_out["refugees in camps (simulation)"] = macro_df["refugees in camps (simulation)"] + micro_df["refugees in camps (simulation)"]

    merged_file_out["refugee_debt"] = macro_df["refugee_debt"] + micro_df["refugee_debt"]

    merged_file_out.to_csv('merged_file_out.csv', index=True, header=True)
    
   
    # ERROR PLOTS
    #######################################################################################

    un_refs1 = merged_file_out.loc[
        :, ["refugees in camps (UNHCR)"]].to_numpy().flatten()
        
    
    loc_errors1 = []
    

    nmodel = False

    
    for i in location_names:
        
        loc_errors1.append(error_quantification(output_dir, merged_file_out, i, naieve_model=nmodel))


    sim_errors1 = SimulationErrors(loc_errors1)

    print(loc_errors1)
   
    matplotlib.rcParams.update({'font.size': 20})
    plt.clf()

    # Size of plots/figures
    fig = matplotlib.pyplot.gcf()
    fig.set_size_inches(14, 10)
    plt.rc('xtick',labelsize=18)
    plt.rc('ytick',labelsize=18)
    set_margins()

    # Plotting and saving error (differences) graph
    plt.ylabel("Averaged relative difference", fontsize=24)
    plt.xlabel("Days elapsed", fontsize=24)
    plt.title("{} Simulation: Averaged relative difference".format(config), fontsize=24)


    diffdata1 = sim_errors1.abs_diff(rescaled=False) / np.maximum(un_refs1, np.ones(len(un_refs1)))
   
    diffdata1_rescaled = sim_errors1.abs_diff() / np.maximum(un_refs1, np.ones(len(un_refs1)))

    
    
    print("Aggregated averaged error normal: ", np.mean(diffdata1),
          ", rescaled: ", np.mean(diffdata1_rescaled), ", len: ", len(diffdata1))
    

    labeldiff_rescaled1, = plt.plot(np.arange(len(diffdata1_rescaled)), diffdata1_rescaled, 
        linewidth=5, label="Error of Multiscale Simulation")
    
        
    plt.legend(handles=[labeldiff_rescaled1], loc=7, prop={'size': 14})
   
    set_margins()

    mkdir_p("{}/Error_plots/".format(output_dir))

    plt.savefig("{}/Error_plots/error.png".format(output_dir))


    #ERROR COMPARISON
    #######################################################################################

    labeldiff1, = plt.plot(np.arange(len(diffdata1)), diffdata1, 
        linewidth=5, label="Error- Multiscale Simulation (not rescaled)")
    
        
    plt.legend(handles=[labeldiff_rescaled1, labeldiff1], loc=1, prop={'size': 14})

    set_margins()

    plt.savefig("{}/Error_plots/error_comparison.png".format(output_dir))

    plt.clf()

def mkdir_p(mypath):
    # Creates a directory. equivalent to using mkdir -p on the command line

    from errno import EEXIST
    from os import makedirs, path

    try:
        makedirs(mypath)
    except OSError as exc:  # Python >2.5
        if exc.errno == EEXIST and path.isdir(mypath):
            pass
        else:
            raise


def set_margins(l=0.13, b=0.13, r=0.96, t=0.96):
    # adjust margins - Setting margins for graphs
    fig = plt.gcf()
    fig.subplots_adjust(bottom=b, top=t, left=l, right=r)


def plot_flee_output(input_dir, output_dir, mscale=False):

    config = basename(normpath(input_dir)).split('_')[0]

    mscale_micro = False
    mscale_macro = False

    #############################################
    #   micro Multiscale results preparation    #
    #############################################
    micro_input_dir = os.path.join(input_dir, 'micro')
    micro_output_dir = os.path.join(output_dir, 'Micro_plots')
    micro_df_PATH=os.path.join(micro_input_dir,'out.csv')
    

    #############################################
    #   macro Multiscale results preparation    #
    #############################################
    macro_input_dir = os.path.join(input_dir, 'macro')
    macro_output_dir = os.path.join(output_dir, 'Macro_plots')
    macro_df_PATH=os.path.join(macro_input_dir,'out.csv')
    

    #############################################
    #   normal results preparation    #
    #############################################
    whole_df_PATH = os.path.join(input_dir,'out.csv')
    

    #################################################################
    #   Plotting serial mode simulation results (without Multiscale)     #
    #################################################################

    if isfile(whole_df_PATH):
        whole_df = pd.read_csv(whole_df_PATH, sep=',',
                           encoding='latin1', index_col='Day')
        plot_camps(whole_df, config, output_dir)
        plot_numagents(whole_df, config, output_dir)
        plot_errors(whole_df, config, output_dir, model='single-scale')
        print('The results of Serial mode simulation are stored '
              'in %s directory.' % (output_dir))

    #####################################################
    #   Plotting micro Multiscale simulation results    #
    #####################################################
    if isfile(micro_df_PATH):
        micro_df = pd.read_csv(micro_df_PATH, sep=',',
                           encoding='latin1', index_col='Day')
        plot_camps(micro_df, config, micro_output_dir)
        # RAW UNHCR Counts need to be addressed
        plot_numagents(micro_df, config, micro_output_dir)
        print('The results of micro simulation are stored '
              'in %s directory.' % (micro_output_dir))

    #####################################################
    #   Plotting macro Multiscale simulation results    #
    #####################################################
    if isfile(macro_df_PATH):
        macro_df = pd.read_csv(macro_df_PATH, sep=',',
                           encoding='latin1', index_col='Day')
        plot_camps(macro_df, config, macro_output_dir)
        # RAW UNHCR Counts need to be addressed
        plot_numagents(macro_df, config, macro_output_dir)
        print('The results of macro simulation are stored '
              'in %s directory.' % (macro_output_dir))

    if isfile(micro_df_PATH) and isfile(macro_df_PATH):

        plot_aggregated_errors(macro_df, micro_df, config, macro_output_dir, micro_output_dir)
        print('The error plots are stored '
              'in %s/Error_plots directory.' % (output_dir))


if __name__ == "__main__":

    if len(sys.argv) > 1:
        input_dir = sys.argv[1]
    else:
        input_dir = "out"

    if len(sys.argv) > 2:
        output_dir = sys.argv[2]
    else:
        output_dir = "out"

    plot_flee_output(input_dir, output_dir)
