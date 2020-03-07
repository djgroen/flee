# developed by chris vassiliou. a file that uses Matplotlib and pandas to compare simulation results for the various
# food hypotheses.

import sys
import matplotlib.pyplot as pplot
import pandas as pnd
import numpy as np
import csv


# input in terminal: "python3 compare_food_simulations.py [food results folder path] [food inverse
# results folder path] [food speed results folder path] [flee results folder path]"

# create a big graph comparing all 4 of the result sets (3 food sims, 1 base flee sim)
def create_graph(food_dir, food_inverse_dir, food_speed_dir, flee_dir):
    # use pandas to access the out.csv results file for each sim
    food = pnd.read_csv("%s/out.csv" % food_dir)
    inverse = pnd.read_csv("%s/out.csv" % food_inverse_dir)
    speed = pnd.read_csv("%s/out.csv" % food_speed_dir)
    flee = pnd.read_csv("%s/out.csv" % flee_dir)
    # create an array that can be used to specify which column in the csv files should be plotted
    columns = ["Days", "Total error"]

    # plot the total error for each of the simulations being tested
    pplot.plot(flee["Day"], food["Total error"], label="Food (Original)")
    pplot.plot(flee["Day"], inverse["Total error"], label="Food (Inverse Movechance)")
    pplot.plot(flee["Day"], speed["Total error"], label="Food (Speed)")
    pplot.plot(flee["Day"], flee["Total error"], label="Flee")
    # add labels to the graph
    pplot.ylabel("Error")
    pplot.xlabel("Days")
    pplot.legend()
    pplot.title("Total Error Comparison")
    # save the image as a png in the correct folder
    pplot.savefig("/home/chris/codes/FabSim3/results/chris validation/total error comparison.png")
    pplot.clf()


def create_file(food_dir, food_inverse_dir, food_speed_dir, flee_dir):
    # use pandas to access the out.csv results file for each sim
    food = pnd.read_csv("%s/out.csv" % food_dir)
    inverse = pnd.read_csv("%s/out.csv" % food_inverse_dir)
    speed = pnd.read_csv("%s/out.csv" % food_speed_dir)
    flee = pnd.read_csv("%s/out.csv" % flee_dir)

    mean_food = food['Total error'].mean()
    mean_inverse = inverse['Total error'].mean()
    mean_speed = speed['Total error'].mean()
    mean_flee = flee['Total error'].mean()

    avg_array = {'Food (Original)': [mean_food],
                 'Food (Inverse)': [mean_inverse],
                 'Food (Speed)': [mean_speed],
                 'Flee': mean_flee}

    avg_data = pnd.DataFrame(avg_array, index=['Average Total Error'])

    avg_data.to_csv("/home/chris/codes/FabSim3/results/chris validation/Average errors.csv")


if __name__ == "__main__":
    food_dir = sys.argv[1]
    food_inverse_dir = sys.argv[2]
    food_speed_dir = sys.argv[3]
    flee_dir = sys.argv[4]
    create_graph(food_dir, food_inverse_dir, food_speed_dir, flee_dir)
    create_file(food_dir, food_inverse_dir, food_speed_dir, flee_dir)
