import os
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Pdf')
import matplotlib.pyplot as plt
import argparse
from flee.postprocessing import plot_flee_output as pfo

#In order to compare two simulation results, simply run:
#python3 compare_2_sim.py --first_sim name1 --second_sim name2 --mscale_model name3 --uncoupled_model name4 (optional)

work_dir = os.path.dirname(os.path.abspath(__file__))

def compare(input_dir_1,input_dir_2, first_sim, second_sim, mscale_model, **kwargs):

    matplotlib.style.use('ggplot')
    input_dir_3 = kwargs.get('input_dir_3', None)
    uncoupled_model = kwargs.get('uncoupled_model', None)


    refugee_data1=pd.read_csv("%s/out.csv" %(input_dir_1), sep=',', encoding='latin1', index_col='Day')
    refugee_data2=pd.read_csv("%s/out.csv" %(input_dir_2), sep=',', encoding='latin1', index_col='Day')
    if input_dir_3[-5:] == 'whole':
        refugee_data3=pd.read_csv("%s/out.csv" %(input_dir_3), sep=',', encoding='latin1', index_col='Day')

    cols1 = list(refugee_data1.columns.values)
    cols2 = list(refugee_data2.columns.values)
    if uncoupled_model == 'whole':
        cols3 = list(refugee_data3.columns.values)

    # Identifying location names for graphs
    location_names = []
    location_names2 = []

    for i in cols1:
            if " sim" in i:
                if "numAgents" not in i:
                    location_names.append(' '.join(i.split()[:-1]))
    if uncoupled_model == 'whole':
        for i in cols3:
                if " sim" in i:
                    if "numAgents" not in i:
                        location_names2.append(' '.join(i.split()[:-1]))
        

    # Plotting and saving NUMAGENTS (total refugee numbers) graph

    plt.xlabel("Days elapsed")
    plt.ylabel("Number of refugees")


    matplotlib.rcParams.update({'font.size': 20})

    refugees_with_debt = [refugee_data1.loc[:,["total refugees (simulation)", "refugees in camps (simulation)"]]+
    refugee_data2.loc[:, ["total refugees (simulation)", "refugees in camps (simulation)",
                             "raw UNHCR refugee count", "refugee_debt"]]]
    refugees_without_debt = [refugee_data1.loc[:,["total refugees (simulation)", "refugees in camps (simulation)"]]+
    refugee_data2.loc[:, ["total refugees (simulation)", "refugees in camps (simulation)",
                             "raw UNHCR refugee count"]]]

    if "refugee_debt" in refugee_data1.columns:
        total_refugees1, = plt.plot(np.arange(len(refugee_data1.loc[:,
            ["total refugees (simulation)"]])), refugee_data1.loc[:,["total refugees (simulation)"]], 
        linewidth=5, label="Total refugees (simulation) {} Coupling".format(first_sim))
        refugees_in_camps1, = plt.plot(np.arange(len(refugee_data1.loc[:,
            ["refugees in camps (simulation)"]])), refugee_data1.loc[:,["refugees in camps (simulation)"]], 
        linewidth=5, label="Refugees in camps (simulation) {} Coupling".format(first_sim))
        total_refugees2, = plt.plot(np.arange(len(refugee_data2.loc[:,
            ["total refugees (simulation)"]])), refugee_data2.loc[:,["total refugees (simulation)"]], 
        linewidth=5, label="Total refugees (simulation) {} Coupling".format(second_sim))
        refugees_in_camps2, = plt.plot(np.arange(len(refugee_data2.loc[:,
            ["refugees in camps (simulation)"]])), refugee_data2.loc[:,["refugees in camps (simulation)"]], 
        linewidth=5, label="Refugees in camps (simulation) {} Coupling".format(second_sim))
        raw_refugee_count, = plt.plot(np.arange(len(refugee_data1.loc[:,
            ["raw UNHCR refugee count"]])), refugee_data1.loc[:,["raw UNHCR refugee count"]], 
        linewidth=5, label="Raw UNHCR refugee count")
        refugee_debt_simulation, = plt.plot(np.arange(len(refugee_data1.loc[:,
            ["refugee_debt"]])), refugee_data1.loc[:,["refugee_debt"]], 
        linewidth=5, label="Refugee_debt")
        
        if uncoupled_model == 'whole': 
            total_refugees3, = plt.plot(np.arange(len(refugee_data3.loc[:,
                ["total refugees (simulation)"]])), refugee_data3.loc[:,["total refugees (simulation)"]], 
            linewidth=5, label="Total refugees (simulation) {} Coupling".format(uncoupled_model))
            refugees_in_camps3, = plt.plot(np.arange(len(refugee_data3.loc[:,
                ["refugees in camps (simulation)"]])), refugee_data3.loc[:,["refugees in camps (simulation)"]], 
            linewidth=5, label="Refugees in camps (simulation)- {}".format(uncoupled_model))

        if uncoupled_model == 'whole':
            plt.legend(handles=[total_refugees1, total_refugees2, total_refugees3, refugees_in_camps1, refugees_in_camps2, refugees_in_camps3, raw_refugee_count, refugee_debt_simulation], 
                loc=0, prop={'size': 14})
        else: 
            plt.legend(handles=[total_refugees1, total_refugees2, refugees_in_camps1, refugees_in_camps2, raw_refugee_count, refugee_debt_simulation], 
                loc=0, prop={'size': 14})
    
    else:
        total_refugees1, = plt.plot(np.arange(len(refugee_data1.loc[:,
            ["total refugees (simulation)"]])), refugee_data1.loc[:,["total refugees (simulation)"]], 
        linewidth=5, label="Total refugees (simulation) {} Coupling".format(first_sim))
        refugees_in_camps1, = plt.plot(np.arange(len(refugee_data1.loc[:,
            ["refugees in camps (simulation)"]])), refugee_data1.loc[:,["refugees in camps (simulation)"]], 
        linewidth=5, label="Refugees in camps (simulation) {} Coupling".format(first_sim))
        total_refugees2, = plt.plot(np.arange(len(refugee_data2.loc[:,
            ["total refugees (simulation)"]])), refugee_data2.loc[:,["total refugees (simulation)"]], 
        linewidth=5, label="Total refugees (simulation) {} Coupling".format(second_sim))
        refugees_in_camps2, = plt.plot(np.arange(len(refugee_data2.loc[:,
            ["refugees in camps (simulation)"]])), refugee_data2.loc[:,["refugees in camps (simulation)"]], 
        linewidth=5, label="Refugees in camps (simulation) {} Coupling".format(second_sim))
        raw_refugee_count, = plt.plot(np.arange(len(refugee_data1.loc[:,
                ["raw UNHCR refugee count"]])), refugee_data1.loc[:,["raw UNHCR refugee count"]], 
        linewidth=5, label="Raw UNHCR refugee count")
        if uncoupled_model == 'whole': 
            total_refugees3, = plt.plot(np.arange(len(refugee_data3.loc[:,
                ["total refugees (simulation)"]])), refugee_data3.loc[:,["total refugees (simulation)"]], 
            linewidth=5, label="Total refugees (simulation) {} Coupling".format(uncoupled_model))
            refugees_in_camps3, = plt.plot(np.arange(len(refugee_data3.loc[:,
                ["refugees in camps (simulation)"]])), refugee_data3.loc[:,["refugees in camps (simulation)"]], 
            linewidth=5, label="Refugees in camps (simulation)- {}".format(uncoupled_model))


        if uncoupled_model == 'whole':
            plt.legend(handles=[total_refugees1, total_refugees2, total_refugees3, refugees_in_camps1, refugees_in_camps2, refugees_in_camps3, raw_refugee_count], 
                loc=0, prop={'size': 14})
        else: 
            plt.legend(handles=[total_refugees1, total_refugees2, refugees_in_camps1, refugees_in_camps2, raw_refugee_count], 
                loc=0, prop={'size': 14})

    
    # Size of plots/figures
    fig = matplotlib.pyplot.gcf()
    fig.set_size_inches(14, 10)

    pfo.set_margins()

    plt.savefig("{}/numagents.png".format(output_dir))

    #ERROR PLOTS
    
    un_refs1 = refugee_data1.loc[
        :, ["refugees in camps (UNHCR)"]].to_numpy().flatten()
    un_refs2 = refugee_data1.loc[
        :, ["refugees in camps (UNHCR)"]].to_numpy().flatten()
    un_refs3 = refugee_data1.loc[
        :, ["refugees in camps (UNHCR)"]].to_numpy().flatten()
    
    loc_errors1 = []
    loc_errors2 = []
    loc_errors3 = []

    nmodel = False

    for i in location_names:
        loc_errors1.append(pfo.plotme(input_dir_1, refugee_data1, i,
                                 legend_loc=4, naieve_model=nmodel))
        loc_errors2.append(pfo.plotme(input_dir_2, refugee_data2, i,
                                 legend_loc=4, naieve_model=nmodel))
        if uncoupled_model == 'whole':
            loc_errors3.append(pfo.plotme(input_dir_3, refugee_data3, i,
                                    legend_loc=4, naieve_model=nmodel))

    sim_errors1 = pfo.SimulationErrors(loc_errors1)
    sim_errors2 = pfo.SimulationErrors(loc_errors2)
    sim_errors3 = pfo.SimulationErrors(loc_errors3)

    matplotlib.rcParams.update({'font.size': 20})
    plt.clf()


    # Size of plots/figures
    fig = matplotlib.pyplot.gcf()
    fig.set_size_inches(14, 10)

    pfo.set_margins()

    # Plotting and saving error (differences) graph
    plt.ylabel("Averaged relative difference")
    plt.xlabel("Days elapsed")

    diffdata1 = sim_errors1.abs_diff(rescaled=False) / np.maximum(un_refs1, np.ones(len(un_refs1)))
    diffdata2 = sim_errors2.abs_diff(rescaled=False) / np.maximum(un_refs2, np.ones(len(un_refs2)))
    if uncoupled_model == "whole":
        diffdata3 = sim_errors3.abs_diff(rescaled=False) / np.maximum(un_refs3, np.ones(len(un_refs3)))


    diffdata1_rescaled = sim_errors1.abs_diff() / np.maximum(un_refs1, np.ones(len(un_refs1)))
    diffdata2_rescaled = sim_errors2.abs_diff() / np.maximum(un_refs2, np.ones(len(un_refs2)))
    if uncoupled_model == "whole":
        diffdata3_rescaled = sim_errors3.abs_diff() / np.maximum(un_refs3, np.ones(len(un_refs3)))

    print(first_sim, ": Averaged error normal: ", np.mean(diffdata1),
          ", rescaled: ", np.mean(diffdata1_rescaled), ", len: ", len(diffdata1))
    print(second_sim, ": Averaged error normal: ", np.mean(diffdata2),
          ", rescaled: ", np.mean(diffdata2_rescaled), ", len: ", len(diffdata2))
    if uncoupled_model == "whole":
        print(uncoupled_model, ": Averaged error normal: ", np.mean(diffdata3),
              ", rescaled: ", np.mean(diffdata3_rescaled), ", len: ", len(diffdata3))

    labeldiff_rescaled1, = plt.plot(np.arange(len(diffdata1_rescaled)), diffdata1_rescaled, 
        linewidth=5, label="Error {} Coupling".format(first_sim))
    labeldiff_rescaled2, = plt.plot(np.arange(len(diffdata2_rescaled)), diffdata2_rescaled, 
        linewidth=5, label="Error {} Coupling".format(second_sim))
    if uncoupled_model == "whole":
        labeldiff_rescaled3, = plt.plot(np.arange(len(diffdata3_rescaled)), diffdata3_rescaled, 
            linewidth=5, label="Error {} Simulation".format(uncoupled_model))
        
    if uncoupled_model == "whole":

        plt.legend(handles=[labeldiff_rescaled1, labeldiff_rescaled2, labeldiff_rescaled3], loc=7, prop={'size': 14})

    else:
        plt.legend(handles=[labeldiff_rescaled1, labeldiff_rescaled2], loc=7, prop={'size': 14})

    pfo.set_margins()

    plt.savefig("{}/error.png".format(output_dir))

    
    #ERROR COMPARISON


    labeldiff1, = plt.plot(np.arange(len(diffdata1)), diffdata1, 
        linewidth=5, label="error- {} Coupling (not rescaled)".format(first_sim))
    labeldiff2, = plt.plot(np.arange(len(diffdata2)), diffdata2, 
        linewidth=5, label="error- {} Coupling (not rescaled)".format(second_sim))
    if uncoupled_model == "whole":
        labeldiff3, = plt.plot(np.arange(len(diffdata3)), diffdata3, 
            linewidth=5, label="error- {} Simulation (not rescaled)".format(uncoupled_model))
        
    if uncoupled_model == "whole":

        plt.legend(handles=[labeldiff_rescaled1, labeldiff_rescaled2, labeldiff_rescaled3 ,labeldiff1, labeldiff2, labeldiff3], loc=7, prop={'size': 14})

    else:
        plt.legend(handles=[labeldiff_rescaled1, labeldiff_rescaled2, labeldiff1, labeldiff2], loc=7, prop={'size': 14})

    pfo.set_margins()

    plt.savefig("{}/error_comparison.png".format(output_dir))

    plt.clf()


    #CAMPS PLOTS

    cols1 = cols1[1:-6]
    cols2 = cols2[1:-6]
    if uncoupled_model == 'whole':
        cols3 = cols3[1:-6]
        cols4 = diff(cols3,cols1)
        cols5 = diff(cols3,cols4)
      
    cols1.sort()
    cols2.sort()
    if uncoupled_model == 'whole':
        cols5.sort()

    cols_ref = list(refugee_data1.columns.values)
    col_error = [cols_ref[0], cols_ref[-6]]
    cols_ref = cols_ref[-5:]

    for i in range(len(cols2)):

        name1 = cols1[i].split()
        name2 = cols2[i].split()
        if uncoupled_model == 'whole':
            name3 = cols5[i].split()


        y1 = refugee_data1["%s sim" % name1[0]]
        y2 = refugee_data1["%s data" % name1[0]]
        y3 = refugee_data2["%s sim" % name2[0]]
        if uncoupled_model == 'whole':
            y4 = refugee_data3["%s sim" % name3[0]]

        fig = matplotlib.pyplot.gcf()
        fig.set_size_inches(14, 10)

        plt.xlabel("Days elapsed")
        plt.ylabel("Number of refugees")
        plt.title("{} Simulation".format(name1[0]))

        label1, = plt.plot(refugee_data1.index,y1, 'g', 
            linewidth=5, label="{} Coupling".format(first_sim))
        label2, = plt.plot(refugee_data1.index,y2, 'b', 
            linewidth=5, label="UNHCR data")
        label3, = plt.plot(refugee_data2.index,y3, 'r', 
            linewidth=5, label="{} Coupling".format(second_sim))
        if uncoupled_model == 'whole':
            label4, = plt.plot(refugee_data3.index,y4, 'y', 
                linewidth=5, label="{} Simulation".format(uncoupled_model))


        if uncoupled_model != 'whole':
            plt.legend(handles=[label1, label2, label3], loc=0, prop={'size': 14})
        else:
            plt.legend(handles=[label1, label2, label3, label4], loc=0, prop={'size': 14})

        mkdir_p(output_dir)

        plt.savefig("{}/{}.png".format(output_dir,name1[0]))

        plt.clf()


def mkdir_p(mypath):
    '''Creates a directory. equivalent to using mkdir -p on the command line'''

    from errno import EEXIST
    from os import makedirs,path

    try:
        makedirs(mypath)
    except OSError as exc: # Python >2.5
        if exc.errno == EEXIST and path.isdir(mypath):
            pass
        else: raise

def diff(li1, li2): 
    li_dif = [i for i in li1 + li2 if i not in li1 or i not in li2] 
    return li_dif 

if __name__ == "__main__":

    data_dir = os.path.join(work_dir, "out")

    uncoupled_model='uncoupled_model'

    parser = argparse.ArgumentParser()

    # Required parameters (Simulation output directories)
    parser.add_argument('--first_sim', 
        required=True, action="store", type=str, choices=['file', 'muscle3'])
    parser.add_argument('--second_sim', 
        required=True, action="store", type=str, choices=['file', 'muscle3'])
    parser.add_argument('--mscale_model', 
        required=True, action="store", type=str, choices=['micro', 'macro'])
                   
    # Optional parameters
    parser.add_argument('--uncoupled_model', 
        action="store", type=str, default=uncoupled_model)

    args, unknown = parser.parse_known_args()
    print(args)
    
    input_dir_1 = os.path.join(work_dir, 'out', args.first_sim, args.mscale_model)
    input_dir_2 = os.path.join(work_dir, 'out', args.second_sim, args.mscale_model)
    input_dir_3 = os.path.join(work_dir, 'out', args.uncoupled_model)
    output_dir = os.path.join(work_dir, 'out', args.mscale_model+'--comparison')

    mkdir_p(output_dir)

    #compare(input_dir_1, input_dir_2)
    compare(input_dir_1, input_dir_2, args.first_sim, args.second_sim, args.mscale_model, input_dir_3=input_dir_3, uncoupled_model= args.uncoupled_model)

    #print("To find about the results of comparison between {} and {} ({} model), please see the {} directory.".format(sys.argv[1],sys.argv[2],sys.argv[3],output_dir))