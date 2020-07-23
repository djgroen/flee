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
#python3 compare_2_sim.py --first_directory name1 --second_directory name2 --mscale_model name3 --uncoupled_model name4 (optional)


work_dir = os.path.dirname(os.path.abspath(__file__))


def compare(out_dir_1,out_dir_2, first_directory, second_directory, mscale_model, **kwargs):

    matplotlib.style.use('ggplot')
    out_dir_3 = kwargs.get('out_dir_3', None)


    refugee_data1=pd.read_csv("%s/out.csv" %(out_dir_1), sep=',', encoding='latin1')
    refugee_data2=pd.read_csv("%s/out.csv" %(out_dir_2), sep=',', encoding='latin1')
    if out_dir_3[-5:] == 'whole':
        refugee_data3=pd.read_csv("%s/out.csv" %(out_dir_3), sep=',', encoding='latin1')

    
    
    cols1 = list(refugee_data1.columns.values)



    cols2 = list(refugee_data2.columns.values)
    if out_dir_3[-5:] == 'whole':
        cols3 = list(refugee_data3.columns.values)

    # Identifying location names for graphs
    location_names = []
    if out_dir_3[-5:] == 'whole':
        for i in cols3:
                if " sim" in i:
                    if "numAgents" not in i:
                        location_names.append(' '.join(i.split()[:-1]))
    else:
        for i in cols1:
            if " sim" in i:
                if "numAgents" not in i:
                    location_names.append(' '.join(i.split()[:-1]))

    # Plotting and saving numagents (total refugee numbers) graph
    # TODO: These labels need to be more flexible/modifiable.

    plt.xlabel("Days elapsed")

    matplotlib.rcParams.update({'font.size': 20})

    if "refugee_debt" in refugee_data1.columns:
        refugee_data1.loc[:, ["total refugees (simulation)", "refugees in camps (simulation)",
                             "raw UNHCR refugee count", "refugee_debt"]].plot(linewidth=5)
    else:
        refugee_data1.loc[:, [
            "total refugees (simulation)", "refugees in camps (UNHCR)", "raw UNHCR refugee count"]].plot(linewidth=5)

    # Size of plots/figures
    fig = matplotlib.pyplot.gcf()
    fig.set_size_inches(12, 8)

    pfo.set_margins()

    plt.savefig("{}/numagents-{}.png".format(output_dir, first_directory))

    if "refugee_debt" in refugee_data2.columns:
        refugee_data2.loc[:, ["total refugees (simulation)", "refugees in camps (simulation)",
                             "raw UNHCR refugee count", "refugee_debt"]].plot(linewidth=5)
    else:
        refugee_data2.loc[:, [
            "total refugees (simulation)", "refugees in camps (UNHCR)", "raw UNHCR refugee count"]].plot(linewidth=5)

    # Size of plots/figures
    fig = matplotlib.pyplot.gcf()
    fig.set_size_inches(12, 8)

    pfo.set_margins()
    plt.savefig("{}/numagents-{}.png".format(output_dir, second_directory))

  

    # Calculate the best offset.

    sim_refs = refugee_data1.loc[
        :, ["refugees in camps (simulation)"]].to_numpy().flatten()
    un_refs = refugee_data1.loc[
        :, ["refugees in camps (UNHCR)"]].to_numpy().flatten()
    raw_refs = refugee_data1.loc[
        :, ["raw UNHCR refugee count"]].to_numpy().flatten()
    

    PlotOffsets = True
    loc_errors1 = []
    loc_errors2 = []
    nmodel = False

    for i in location_names:
        loc_errors1.append(pfo.plotme(out_dir_1, refugee_data1, i,
                                 legend_loc=4, naieve_model=nmodel))
        loc_errors2.append(pfo.plotme(out_dir_2, refugee_data2, i,
                                 legend_loc=4, naieve_model=nmodel))

    sim_errors1 = pfo.SimulationErrors(loc_errors1)
    sim_errors2 = pfo.SimulationErrors(loc_errors2)

    matplotlib.rcParams.update({'font.size': 20})

    plt.clf()

    #ERROR PLOTS

    # Size of plots/figures
    fig = matplotlib.pyplot.gcf()
    fig.set_size_inches(12, 8)

    pfo.set_margins()


    # Plotting and saving error (differences) graph
    plt.ylabel("Averaged relative difference")
    plt.xlabel("Days elapsed")

    diffdata1 = sim_errors1.abs_diff(rescaled=False) / np.maximum(un_refs, np.ones(len(un_refs)))
    diffdata2 = sim_errors2.abs_diff(rescaled=False) / np.maximum(un_refs, np.ones(len(un_refs)))

    diffdata1_rescaled = sim_errors1.abs_diff() / np.maximum(un_refs, np.ones(len(un_refs)))
    diffdata2_rescaled = sim_errors2.abs_diff() / np.maximum(un_refs, np.ones(len(un_refs)))

    print(out_dir_1, ": Averaged error normal: ", np.mean(diffdata1),
          ", rescaled: ", np.mean(diffdata1_rescaled), ", len: ", len(diffdata1))
    print(out_dir_2, ": Averaged error normal: ", np.mean(diffdata2),
          ", rescaled: ", np.mean(diffdata2_rescaled), ", len: ", len(diffdata2))

    labeldiff_rescaled1, = plt.plot(np.arange(len(diffdata1_rescaled)), diffdata1_rescaled, linewidth=5, label="Error {}".format(first_directory))
    labeldiff_rescaled2, = plt.plot(np.arange(len(diffdata1_rescaled)), diffdata2_rescaled, linewidth=5, label="Error {}".format(second_directory))

    plt.legend(handles=[labeldiff_rescaled1, labeldiff_rescaled2], loc=1, prop={'size': 14})

    plt.savefig("{}/error.png".format(output_dir))

    labeldiff1, = plt.plot(np.arange(len(diffdata1)), diffdata1, linewidth=5, label="error- {}- (not rescaled)".format(first_directory))
    labeldiff2, = plt.plot(np.arange(len(diffdata2)), diffdata2, linewidth=5, label="error- {}- (not rescaled)".format(second_directory))


    plt.legend(handles=[labeldiff_rescaled1, labeldiff_rescaled2, labeldiff1, labeldiff2], loc=1, prop={'size': 14})

    plt.savefig("{}/error_comparison.png".format(output_dir))

    plt.clf()

    #CAMPS PLOTS

    cols1 = cols1[1:-6]
    cols2 = cols2[1:-6]
    if out_dir_3[-5:] == 'whole':
        cols3 = cols3[1:-6]
        cols4 = diff(cols3,cols1)
        cols5 = diff(cols3,cols4)
      
      
    cols1.sort()
    cols2.sort()
    if out_dir_3[-5:] == 'whole':
        cols5.sort()

    cols_ref = list(refugee_data1.columns.values)
    col_error = [cols_ref[0], cols_ref[-6]]
    cols_ref = cols_ref[-5:]

   
    for i in range(len(cols2)):

        name1 = cols1[i].split()
        name2 = cols2[i].split()
        if out_dir_3[-5:] == 'whole':
            name3 = cols5[i].split()


        y1 = refugee_data1["%s sim" % name1[0]]
        y2 = refugee_data1["%s data" % name1[0]]
        y3 = refugee_data2["%s sim" % name2[0]]
        if out_dir_3[-5:] == 'whole':
            y4 = refugee_data3["%s sim" % name3[0]]

      

        fig = matplotlib.pyplot.gcf()
        fig.set_size_inches(12, 8)

        plt.xlabel("Days elapsed")
        plt.ylabel("Number of refugees")

        label1, = plt.plot(refugee_data1["Day"],y1, 'g', linewidth=5, label="error- {}- (not rescaled)".format(first_directory))
        label2, = plt.plot(refugee_data1["Day"],y2, 'b', linewidth=5, label="error- {}- (not rescaled)".format("UNHCR data"))
        label3, = plt.plot(refugee_data2["Day"],y3, 'r', linewidth=5, label="error- {}- (not rescaled)".format(second_directory))
        if out_dir_3[-5:] == 'whole':
            label4, = plt.plot(refugee_data3["Day"],y4, 'r', linewidth=5, label="error- {}- (not rescaled)".format(out_dir_3[-5:]))



        plt.legend(handles=[label1, label2, label3], loc=1, prop={'size': 14})

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
    parser.add_argument('--first_directory', required=True, action="store", type=str, choices=['file', 'muscle3'])
    parser.add_argument('--second_directory', required=True, action="store", type=str, choices=['file', 'muscle3'])
    parser.add_argument('--mscale_model', required=True, action="store", type=str, choices=['micro', 'macro'])
                   
    # Optional parameters
    parser.add_argument('--uncoupled_model', action="store", type=str, default=uncoupled_model)

    args, unknown = parser.parse_known_args()
    print(args)
    
    out_dir_1 = os.path.join(work_dir, 'out', args.first_directory, args.mscale_model)
    out_dir_2 = os.path.join(work_dir, 'out', args.second_directory, args.mscale_model)
    out_dir_3 = os.path.join(work_dir, 'out', args.uncoupled_model)
    output_dir = os.path.join(work_dir, 'out', args.mscale_model+'--comparison')


    #compare(out_dir_1, out_dir_2)
    compare(out_dir_1, out_dir_2, args.first_directory, args.second_directory, args.mscale_model, out_dir_3=out_dir_3)

    #print("To find about the results of comparison between {} and {} ({} model), please see the {} directory.".format(sys.argv[1],sys.argv[2],sys.argv[3],output_dir))