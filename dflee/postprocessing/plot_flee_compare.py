import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Pdf')
import matplotlib.pyplot as plt
from flee.postprocessing import plot_flee_output as cp

# ----------------------------It is a comparison script for different simulation models of the same scenario through FabSim3.---------------------------------


def find_locations_names(merged_df):

    ########### Identifying location names #######################################################################################

    cols = list(merged_df.columns.values)

    location_names = []

    for i in cols:
            if " sim" in i:
                if "numAgents" not in i:
                    location_names.append(' '.join(i.split()[:-1])) 

    return location_names


def compare_errors(data_dir,output_dir,config_name,list_of_directories_names):


    matplotlib.rcParams.update({'font.size': 20})
    plt.clf()

    fig = matplotlib.pyplot.gcf()
    fig.set_size_inches(14, 10)

    plt.style.use('fast')

    cp.set_margins()

    # Plotting and saving error (differences) graph
    plt.title("Averaged Error Comparison - {}".format(config_name))
    plt.ylabel("Averaged relative difference")
    plt.xlabel("Days elapsed")

    out_csv_file = os.path.join(output_dir,'comparisons.csv')

    output_header_string = "Simulation Model,Error,Rescaled error,Duration (Days),Execution Time (Seconds)"

    with open(out_csv_file, "w", encoding="utf-8") as f:
        f.truncate()
        f.write(output_header_string)
        f.write("\n")
        f.flush()

    for name in list_of_directories_names:

        input_dir = os.path.join(data_dir, name)

        df=pd.read_csv(os.path.join(input_dir,'out.csv'),sep=',', encoding='latin1', index_col='Day')

        un_refs = df.loc[:, ["refugees in camps (UNHCR)"]].to_numpy().flatten()

        loc_errors = []

        nmodel = False

        for i in find_locations_names(df):

            loc_errors.append(cp.error_quantification(output_dir, df, i, naieve_model=nmodel))

        sim_errors = cp.SimulationErrors(loc_errors)
   
        diffdata = sim_errors.abs_diff(rescaled=False) / np.maximum(un_refs, np.ones(len(un_refs)))

        diffdata_rescaled = sim_errors.abs_diff(rescaled=False) / np.maximum(un_refs, np.ones(len(un_refs)))
        '''
        execution_time = os.path.join(output_dir,'execution_time.txt')
        
        with open(execution_time,"r") as f:
            text = f.readlines()
            time = text[0].split(" ")
        '''
        output = "{},{},{},{}".format(
                        name,
                        np.mean(diffdata),
                        np.mean(diffdata_rescaled),
                        len(diffdata)
                    )

        with open(out_csv_file, "a+", encoding="utf-8") as f:
            f.write(output)
            f.write("\n")
            f.flush()

        print('Simulation Model: {0},'.format(name), 'Error:',
            np.mean(diffdata),
            ', Rescaled error:',np.mean(diffdata_rescaled),
            ', Duration:', len(diffdata), 'days')
    
        labeldiff = plt.plot(np.arange(len(diffdata)), diffdata, 
            linewidth=5, label="error- {}".format(name))

    handles, labels = plt.gca().get_legend_handles_labels()

    plt.legend(labels, loc=0, prop={'size': 18})
   
    cp.set_margins()

    plt.savefig("{}/error_comparison.png".format(output_dir))

    plt.clf()

def compare_camps(data_dir,output_dir,list_of_directories_names):

    for name in list_of_directories_names:

        input_dir = os.path.join(data_dir, name)

        df=pd.read_csv(os.path.join(input_dir,'out.csv'),sep=',', encoding='latin1')

        columns_list = list(df.columns.values)

        columns_list = columns_list[1:-7]

        camps_list =[]

        for i in range(len(columns_list)):

            camp_name = columns_list[i].split()
            camps_list.append(camp_name[0])

        camps_list = list(dict.fromkeys(camps_list))

        for camp_name in camps_list:

            data_line = df["%s data" % camp_name]

            plt.plot(df["Day"],data_line, 'b', linewidth=4,label="UNHCR data")


            for model in list_of_directories_names:

                input_dir = os.path.join(data_dir, model)
                df=pd.read_csv(os.path.join(input_dir,'out.csv'),sep=',', encoding='latin1')
                sim_line = df["%s sim" % camp_name]
                plt.plot(df["Day"],sim_line, linewidth=4,label=model)


            matplotlib.rcParams.update({'font.size': 20})

            # Size of plots/figures
            fig = matplotlib.pyplot.gcf()
            fig.set_size_inches(14, 10)

            plt.style.use('fast')
            

            plt.locator_params(axis="x", nbins=5)
            plt.locator_params(axis="y", nbins=8)

            plt.title("{} Simulation".format(camp_name))

            plt.xlabel("Days elapsed")

            plt.ylabel("Number of refugees")

            handles, labels = plt.gca().get_legend_handles_labels()

            plt.legend(labels, loc=0, prop={'size': 18})


            plt.savefig("%s/%s.png"%(output_dir, camp_name))
            
            plt.clf()
    

def compare_numagents(data_dir,output_dir,config_name,list_of_directories_names):

    # Plotting and saving numagents (total refugee numbers) graph

    for name in list_of_directories_names:

        input_dir = os.path.join(data_dir, name)

        df=pd.read_csv(os.path.join(input_dir,'out.csv'),sep=',', encoding='latin1')

        raw_refugee_count, = plt.plot(np.arange(len((df).loc[:,
            ["raw UNHCR refugee count"]])), (df).loc[:, ["raw UNHCR refugee count"]],linewidth=5, label="Raw UNHCR refugee count")
        refugee_debt_simulation, = plt.plot(np.arange(len((df).loc[:,["refugee_debt"]])), (df).loc[:, ["refugee_debt"]],linewidth=5, label="Refugee_debt")

        for model in list_of_directories_names:

            input_dir = os.path.join(data_dir, model)
            
            df=pd.read_csv(os.path.join(input_dir,'out.csv'),sep=',', encoding='latin1')

            total_refugees, = plt.plot(np.arange(len((df).loc[:,["total refugees (simulation)"]])), (df).loc[:, ["total refugees (simulation)"]],
                                        linewidth=5, label="Total refugees (simulation) {}".format(model))
            refugees_in_camps, = plt.plot(np.arange(len((df).loc[:,["refugees in camps (simulation)"]])), (df).loc[:, ["refugees in camps (simulation)"]],
                                           linewidth=5, label="Refugees in camps (simulation) {}".format(model))


        fig = matplotlib.pyplot.gcf()
        fig.set_size_inches(14, 10)

        plt.style.use('fast')
        plt.locator_params(axis="x", nbins=5)
        plt.locator_params(axis="y", nbins=8)

        plt.title("Number of agents - {}".format(config_name))

        plt.xlabel("Days elapsed")

        plt.ylabel("Number of refugees")

        handles, labels = plt.gca().get_legend_handles_labels()

        plt.legend(labels, loc=0, prop={'size': 18})

        plt.savefig("{}/numagents.png".format(output_dir))

        plt.clf()
        

def plot_flee_compare(*models,data_dir,output_dir):

    config_name = models[0].partition("_")[0].capitalize()

    compare_errors(data_dir,output_dir,config_name,models)

    compare_camps(data_dir,output_dir,models)

    compare_numagents(data_dir,output_dir,config_name,models)


if __name__ == "__main__":

    '''

    '''     

