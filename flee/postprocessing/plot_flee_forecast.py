import os
import sys
import pandas as pd
import matplotlib
# matplotlib.use('Pdf')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib import cm
import numpy as np
import glob
from pprint import pprint
from shutil import rmtree

def plot_camps(data, mean, std, output):
    
    # Plotting function for camps.

    data_filtered = data.drop(['Total error', 'refugees in camps (UNHCR)', 'total refugees (simulation)',
     'raw UNHCR refugee count', 'refugees in camps (simulation)', 'refugee_debt'], axis=1)

    mean_filtered = mean.drop(['Total error', 'refugees in camps (UNHCR)', 'total refugees (simulation)',
     'raw UNHCR refugee count', 'refugees in camps (simulation)', 'refugee_debt'], axis=1)

    std_filtered = std.drop(['Total error', 'refugees in camps (UNHCR)', 'total refugees (simulation)',
     'raw UNHCR refugee count', 'refugees in camps (simulation)', 'refugee_debt'], axis=1)


    cols = list(data_filtered.columns.values)

    output = os.path.join(output, 'camps')
        
    mkdir_p(output)

    for i in range(len(cols)):

        name = cols[i].split()

        y1 = data_filtered["%s data" % name[0]]
        y2 = data_filtered["%s sim" % name[0]]
        y3 = mean_filtered["%s sim" % name[0]]
        y4 = std_filtered["%s sim" % name[0]]
        y5 = y3 - y4
        y6 = y3 + y4

        X = range(len(y3))
        
        fig = plt.figure()
        #fig.set_size_inches(14, 10)

        ax = fig.add_subplot(111, xlabel="Days elapsed",
                             ylabel="Number of refugees",
                             title="{} Simulation with mean +/- standard deviation".format(name[0]))
        ax.plot(X, y1, 'k', label='data')
        #ax.plot(X, y2, 'b', label='sim')
        ax.plot(X, y3, 'g-', label='mean')
        ax.plot(X, y5, '--r', label='+1 std-dev')
        ax.plot(X, y6, '--r')
        ax.fill_between(X, y5, y6, color='Pink', alpha=0.2)
        plt.tight_layout()
        plt.legend(loc='best')
        plot_file_name = 'plot_statistical_moments[%s]' % (name[0])

        plt.savefig(os.path.join(output, plot_file_name), dpi=200)
               
        #plt.savefig("{}/{}.png".format(output,plot_file_name))
        
        plt.clf()

def mkdir_p(mypath):
    # Creates a directory. equivalent to using mkdir -p on the command line

    if os.path.exists(mypath):
        rmtree(mypath)
    os.makedirs(mypath)



def plot_flee_forecast(input_dir, output_dir):
    data_dir = os.path.join(input_dir, 'RUNS')
    
    print(data_dir)

    output_dir = os.path.join(data_dir, 'result_plots')
    mkdir_p(output_dir)
    print('INPUT DIRECTORY={}'.format(input_dir))
    print('OUTPUT DIRECTORY={}'.format(output_dir))

   
    all_files = glob.glob(input_dir + "/RUNS/**/out.csv")

    li = []

    for filename in all_files:
        df = pd.read_csv(filename, index_col=None, header=0)
        li.append(df)

    dfList = [pd.read_csv(file, index_col='Day', header=0)
              for file in all_files]
    output = os.path.join(output_dir, 'camps')
    mkdir_p(output)

    #******************************************#
    #************Mean and STD Plots************#
    #******************************************#

    frame = pd.concat(li, axis=0, ignore_index=True)

    frame.to_csv('{}/all_out.csv'.format(output_dir), index=False)

    mean_df = frame.groupby(['Day']).mean()

    mean_df = mean_df.reset_index()

    std_df = frame.groupby(['Day']).std()

    std_df = std_df.reset_index()

    mean_df.to_csv('{}/mean_df.csv'.format(output_dir), index=False)
    
    std_df.to_csv('{}/std_df.csv'.format(output_dir), index=False)

    mean_filtered = mean_df.drop(['Total error', 'refugees in camps (UNHCR)', 'total refugees (simulation)',
     'raw UNHCR refugee count', 'refugees in camps (simulation)', 'refugee_debt'], axis=1)

    std_filtered = std_df.drop(['Total error', 'refugees in camps (UNHCR)', 'total refugees (simulation)',
     'raw UNHCR refugee count', 'refugees in camps (simulation)', 'refugee_debt'], axis=1)

    # find the camps camp_names
    camp_names = []
    for col in list(dfList[0].columns.values):
        if col.find(" data") != -1:
            camp_names.append(col.split()[0])

    print(camp_names)

    #evenly_spaced_interval = np.linspace(0.1, 1, len(all_files))
    #colors = [cm.rainbow(x) for x in evenly_spaced_interval]

    for camp_index, camp_name in enumerate(camp_names):
        fig = plt.figure()

        ax = fig.add_subplot(
            111, xlabel="Days elapsed",
            ylabel="Number of refugees",
            title="All Simulation runs ({}) for {} with mean and percentiles".format(len(all_files), camp_name)
        )

        boxplot_data = []
        for i in range(len(all_files)):
            y1 = dfList[i]["%s data" % camp_name]
            y2 = dfList[i]["%s sim" % camp_name]
            ax.plot(y1, 'k')
            ax.plot(y2, color='Silver')

            boxplot_data.append(y2.values)

        y3 = mean_filtered["%s sim" % camp_name]
        X = range(len(y3))
        ax.plot(X, y3, 'b-', label='mean')

        boxplot_data = np.array(boxplot_data).T
        percentile_5 = np.percentile(boxplot_data, 5, axis=1)
        percentile_95 = np.percentile(boxplot_data, 90, axis=1)
        ax.plot(X, percentile_5, linestyle='--',
                color='r', label='5th percentile')
        ax.plot(X, percentile_95, linestyle='-.',
                color='red', label='90th percentile')
        ax.fill_between(X, percentile_5, percentile_95,
                        color='Pink', alpha=0.5)

        plt.tight_layout()

        custom_lines = [Line2D([0], [0], color='k', lw=2),
                        Line2D([0], [0], color='b', lw=2),
                        Line2D([0], [0], color='Silver', lw=2),
                        Line2D([0], [0], color='red', lw=2, ls='-.'),
                        Line2D([0], [0], color='red', lw=2, ls='--')]

        ax.legend(custom_lines, ['Data', 'Mean', 'Runs',
                                 '90th percentile', '5th percentile'])

        plot_file_name = 'All %s runs for [%s] with Mean and Percentiles' % (
            len(all_files), camp_name)
        plt.ylim([0, 1000])
        plt.savefig("{}/{}.png".format(output, plot_file_name), dpi=200)

if __name__ == "__main__":

    input_dir = os.path.dirname(os.path.abspath(__file__))
    plot_flee_forecast(input_dir)
    
