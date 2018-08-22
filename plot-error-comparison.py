#This script should be run using the main flee directory as working directory.

import pandas as pd
import matplotlib
matplotlib.use('Pdf')
import matplotlib.pyplot as plt
import numpy as np
import sys
from datamanager import handle_refugee_data
import warnings
import outputanalysis.analysis as a

warnings.filterwarnings("ignore")

class LocationErrors:
  """
  Class containing a dictionary of errors and diagnostics pertaining a single location.
  """
  def __init__(self):
    self.errors = {}


class SimulationErrors:
  """
  Class containing all error measures within a single simulation.
  It should be initialized with a Python list of the LocationErrors structure
  for all of the relevant locations.
  """
  def __init__(self, location_errors):
    self.location_errors = location_errors


  def abs_diff(self, rescaled=True):
    #true_total_refs is the number of total refugees according to the data.

    errtype = "absolute difference"
    if rescaled:
      errtype = "absolute difference rescaled"

    self.tmp = self.location_errors[0].errors[errtype]

    for lerr in self.location_errors[1:]:
      self.tmp = np.add(self.tmp, lerr.errors[errtype])

    return self.tmp

  def get_error(self, err_type):
    """
    Here err_type is the string name of the error that needs to be aggregated.
    """
    self.tmp = self.location_errors[0].errors[err_type] * self.location_errors[0].errors["N"]
    N = self.location_errors[0].errors["N"]

    for lerr in self.location_errors[1:]:
      self.tmp = np.add(self.tmp, lerr.errors[err_type] * lerr.errors["N"])
      N += lerr.errors["N"]

    #print(self.tmp, N, self.tmp/ N)
    return self.tmp / N

def set_margins(l=0.13,b=0.13,r=0.96,t=0.96):
  #adjust margins - Setting margins for graphs
  fig = plt.gcf()
  fig.subplots_adjust(bottom=b,top=t,left=l,right=r)


def calc_errors(out_dir, data, name, naieve_model=True):
  """
  Advanced plotting function for validation of refugee registration numbers in camps.
  """
  plt.clf()

  # data.loc[:,["%s sim" % name,"%s data" % name]]).as_matrix()
  y1 = data["%s sim" % name].as_matrix()

  y2 = data["%s data" % name].as_matrix()
  days = np.arange(len(y1))

  naieve_early_day = 7
  naieve_training_day = 30

  # Rescaled values
  plt.clf()

  plt.xlabel("Days elapsed")
  plt.ylabel("Number of refugees")

  simtot = data["refugees in camps (simulation)"].as_matrix().flatten()
  untot = data["refugees in camps (UNHCR)"].as_matrix().flatten()

  y1_rescaled = np.zeros(len(y1))
  for i in range(0, len(y1_rescaled)):
    # Only rescale if simtot > 0
    if simtot[i] > 0:
      y1_rescaled[i] = y1[i] * untot[i] / simtot[i]

  """
  Error quantification phase:
  - Quantify the errors and mismatches for this camp.
  """

  lerr = LocationErrors()

  # absolute difference
  lerr.errors["absolute difference"] = a.abs_diffs(y1, y2)

  # absolute difference (rescaled)
  lerr.errors["absolute difference rescaled"] = a.abs_diffs(y1_rescaled, y2)

  # ratio difference
  lerr.errors["ratio difference"] = a.abs_diffs(y1, y2) / (np.maximum(untot, np.ones(len(untot))))

  """ Errors of which I'm usure whether to report:
   - accuracy ratio (forecast / true value), because it crashes if denominator is 0.
   - ln(accuracy ratio).
  """

  # We can only calculate the Mean Absolute Scaled Error if we have a naieve model in our plot.
  if naieve_model:

    # Number of observations (aggrgate refugee days in UNHCR data set for this location)
    lerr.errors["N"] = np.sum(y2)

    # flat naieve model (7 day)
    lerr.errors["MASE7"] = a.calculate_MASE(y1_rescaled, y2, n1, naieve_early_day)
    lerr.errors["MASE7-sloped"] = a.calculate_MASE(y1_rescaled, y2, n3, naieve_early_day)
    lerr.errors["MASE7-ratio"] = a.calculate_MASE(y1_rescaled, y2, n5, naieve_early_day)

    # flat naieve model (30 day)
    lerr.errors["MASE30"] = a.calculate_MASE(y1_rescaled, y2, n2, naieve_training_day)
    lerr.errors["MASE30-sloped"] = a.calculate_MASE(y1_rescaled, y2, n4, naieve_training_day)
    lerr.errors["MASE30-ratio"] = a.calculate_MASE(y1_rescaled, y2, n6, naieve_training_day)


    # Accuracy ratio doesn't work because of 0 values in the data.
    print("%s,%s,%s,%s,%s,%s,%s,%s,%s" % (out_dir, name, lerr.errors["MASE7"],lerr.errors["MASE7-sloped"], lerr.errors["MASE7-ratio"],lerr.errors["MASE30"],lerr.errors["MASE30-sloped"],lerr.errors["MASE30-ratio"],lerr.errors["N"]))

  return lerr

def prepare_figure(xlabel):
  plt.clf()
  plt.xlabel(xlabel)

  matplotlib.rcParams.update({'font.size': 20})
  fig = matplotlib.pyplot.gcf()
  fig.set_size_inches(12, 8)
  set_margins()
  return fig


def numagents_camp_compare(out_dir, datas, name, legend_loc=4):
  """
  Advanced plotting function for validation of refugee registration numbers in camps.
  """
  fig = prepare_figure(xlabel="Days elapsed")

  labelssim = []

  for data in datas:
    y1 = data["%s sim" % name].as_matrix()

    y2 = data["%s data" % name].as_matrix()
    days = np.arange(len(y1))

    #Plotting lines representing simulation results.
    labelsim, = plt.plot(days,y1, linewidth=8, label="%s simulation" % (name.title()))
    labelssim.append(labelsim)

    # Plotting line representing UNHCR data.
    #labeldata, = plt.plot(days,y2, 'o-', linewidth=8, label="%s UNHCR data" % (name.title()))


  # Add label for the naieve model if it is enabled.
  plt.legend(handles=labelssim,loc=legend_loc,prop={'size':18})

  fig.savefig("%s/%s-%s.png" % (out_dir, name, legend_loc))

  # Rescaled values
  plt.clf()

  plt.xlabel("Days elapsed")
  plt.ylabel("Number of refugees")

  labelssim = []

  for data in datas:

    simtot = data["refugees in camps (simulation)"].as_matrix().flatten()
    untot = data["refugees in camps (UNHCR)"].as_matrix().flatten()

    y1_rescaled = np.zeros(len(y1))
    for i in range(0, len(y1_rescaled)):
      # Only rescale if simtot > 0
      if simtot[i] > 0:
        y1_rescaled[i] = y1[i] * untot[i] / simtot[i]


    labelsim, = plt.plot(days,y1_rescaled, linewidth=8, label="%s simulation" % (name.title()))
    labelssim.append(labelsim)

    #labeldata, = plt.plot(days,y2, linewidth=8, label="%s UNHCR data" % (name.title()))


  plt.legend(handles=[labelsim],loc=legend_loc,prop={'size':18})

  fig = matplotlib.pyplot.gcf()
  fig.set_size_inches(12, 8)
  set_margins()

  fig.savefig("%s/%s-%s-rescaled.png" % (out_dir, name, legend_loc))




#Start of the code, assuring arguments of out-folder & csv file are kept
if __name__ == "__main__":


  in_dirs = []
  names = []

  for i in range(1, len(sys.argv)-1):
    in_dirs.append(sys.argv[i])
    names.append(sys.argv[i])

  out_dir = sys.argv[-1]

  matplotlib.style.use('ggplot')
  #figsize=(15, 10)

  refugee_data = []

  print(in_dirs)

  for d in in_dirs:
    refugee_data.append(pd.read_csv("%s/out.csv" % (d), sep=',', encoding='latin1',index_col='Day'))

  #Identifying location names for graphs
  rd_cols = list(refugee_data[0].columns.values)
  location_names = []
  for i in rd_cols:
    if " sim" in i:
      if "numAgents" not in i:
        location_names.append(' '.join(i.split()[:-1]))


  plt.xlabel("Days elapsed")

  # Calculate the best offset.

  sim_refs = []
  un_refs = []
  raw_refs = []


  for i in range(0, len(refugee_data)):
    sim_refs.append(refugee_data[i].loc[:,["refugees in camps (simulation)"]].as_matrix().flatten())
    un_refs.append(refugee_data[i].loc[:,["refugees in camps (UNHCR)"]].as_matrix().flatten())
    raw_refs.append(refugee_data[i].loc[:,["raw UNHCR refugee count"]].as_matrix().flatten())

  loc_errors = []
  sim_errors = []
  nmodel = False

  #plot numagents compare by camp.
  for i in location_names:
    numagents_camp_compare(out_dir, refugee_data, i, legend_loc=4)

  for i in range(0, len(refugee_data)):
    loc_errors.append([])
    for j in location_names:
      loc_errors[i].append(calc_errors(out_dir, refugee_data[i], j, naieve_model=nmodel))

    sim_errors.append(SimulationErrors(loc_errors[i]))

  matplotlib.rcParams.update({'font.size': 20})

  plt.clf()

  # ERROR PLOTS

  #Size of plots/figures
  fig = matplotlib.pyplot.gcf()
  fig.set_size_inches(12, 8)

  #Plotting and saving error (differences) graph
  plt.ylabel("Averaged relative difference")
  plt.xlabel("Days elapsed")

  handle_list = []

  for i in range(0, len(in_dirs)):
    diffdata = (sim_errors[i].abs_diff(rescaled=False) / np.maximum(un_refs[i], np.ones(len(un_refs[i]))))
    diffdata_rescaled = (sim_errors[i].abs_diff() / np.maximum(un_refs[i], np.ones(len(un_refs[i]))))
    print(out_dir,": Averaged error normal: ", np.mean(diffdata), ", rescaled: ", np.mean(diffdata_rescaled),", len: ", len(diffdata))
    plt.plot(np.arange(len(diffdata_rescaled)), diffdata_rescaled, linewidth=5, label="error %s" % names[i])

  plt.legend(loc=1,prop={'size':14})

  set_margins()
  plt.savefig("%s/error-compare-runs.png" % out_dir)

  plt.clf()

  #Size of plots/figures
  fig = matplotlib.pyplot.gcf()
  fig.set_size_inches(12, 8)

  #Plotting and saving error (differences) graph
  plt.ylabel("Number of agents")
  plt.xlabel("Days elapsed")

  handle_list = []

  for i in range(0, len(in_dirs)):
      #refugee_data[i].loc[:,["total refugees (simulation)","refugees in camps (simulation)","raw UNHCR refugee count","refugee_debt"]].plot(linewidth=5, label="refugees in camps (sim) %s" % names[i])
      refugee_data[i].loc[:,["refugees in camps (simulation)"]].plot(linewidth=5, label="refugees in camps (sim) - %s" % names[i])

  plt.legend(loc=1,prop={'size':14})

  set_margins()
  plt.savefig("%s/numsim-compare-runs.png" % out_dir)

