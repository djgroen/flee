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


def mkdir_p(mypath):
    # Creates a directory. equivalent to using mkdir -p on the command line

    if os.path.exists(mypath):
        rmtree(mypath)
    os.makedirs(mypath)


def plot_flee_forecast(input_dir, region_names=[]):
    data_dir = os.path.join(input_dir, 'RUNS')

    print('INPUT DIRECTORY={}'.format(input_dir))
    # print("data_dir = {}".format(data_dir))

    # we add empty string here to calculate results contains from all
    # available config folder names in RUNS directory
    region_names.append('')
    # print("region_names = {}".format(region_names))

    # clear the result_plots directory
    mkdir_p(os.path.join(input_dir, 'plots'))

    for region_name in region_names:
        output_dir = os.path.join(input_dir, 'plots')

        if len(region_name) > 0:
            output_dir = os.path.join(output_dir, region_name)
        else:
            output_dir = os.path.join(output_dir, "entire_runs")
        print('OUTPUT DIRECTORY={}'.format(output_dir))
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        if len(region_name) == 0:
            all_files = glob.glob(input_dir + "/RUNS/**/out.csv")
        else:
            all_files = [f for f in glob.glob(
                input_dir + "/RUNS/**/out.csv")
                if region_name in os.path.abspath(f) and
                os.path.basename(os.path.dirname(f)).index(region_name) == 0
            ]

        #print("Collected out.csv files for analysis:")
        #pprint(all_files)

        li = []

        for filename in all_files:
            df = pd.read_csv(filename, index_col=None, header=0)
            li.append(df)

        dfList = [pd.read_csv(file, index_col='Day', header=0)
                  for file in all_files]
        output = os.path.join(output_dir, 'camps')
        mkdir_p(output)

        # ******************************************#
        # ************Mean and STD Plots************#
        # ******************************************#

        frame = pd.concat(li, axis=0, ignore_index=True)

        frame.to_csv('{}/all_out.csv'.format(output_dir), index=False)

        mean_df = frame.groupby(['Day']).mean()

        mean_df = mean_df.reset_index()

        std_df = frame.groupby(['Day']).std()

        std_df = std_df.reset_index()

        mean_df.to_csv('{}/mean_df.csv'.format(output_dir), index=False)

        std_df.to_csv('{}/std_df.csv'.format(output_dir), index=False)

        mean_filtered = mean_df.drop(
            ['Total error', 'refugees in camps (UNHCR)',
             'total refugees (simulation)', 'raw UNHCR refugee count',
             'refugees in camps (simulation)', 'refugee_debt'],
            axis=1
        )

        std_filtered = std_df.drop(
            ['Total error', 'refugees in camps (UNHCR)',
             'total refugees (simulation)', 'raw UNHCR refugee count',
             'refugees in camps (simulation)', 'refugee_debt'],
            axis=1
        )

        # find the camps camp_names
        camp_names = []
        for col in list(dfList[0].columns.values):
            if col.find(" data") != -1:
                camp_names.append(col.split()[0])

        # print(camp_names)

        # evenly_spaced_interval = np.linspace(0.1, 1, len(all_files))
        # colors = [cm.rainbow(x) for x in evenly_spaced_interval]

        for camp_index, camp_name in enumerate(camp_names):
            fig = plt.figure()

            ax = fig.add_subplot(
                111, xlabel="Days elapsed",
                ylabel="Number of refugees",
                title="All Simulation runs ({}) for {} "
                "with mean and percentiles".format(
                    len(all_files), camp_name
                )
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
            plt.gca().set_ylim(bottom=0)
            plt.savefig("{}/{}.png".format(output, plot_file_name), dpi=200)

            # to avoid all figure to avoid warning about too many open figures
            plt.close('all')

if __name__ == "__main__":

    input_dir = os.path.dirname(os.path.abspath(__file__))
    region_names = ["all", "tigray", "benshangul", "oromia"]
    plot_flee_forecast(input_dir, region_names=region_names)
