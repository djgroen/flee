import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import matplotlib
import sys
import handle_refugee_data

"""
This is a generic plotting program.
See an example of the output format used in test-output/out.csv
Example use:
  python3 plot-flee-output.py test-output
"""

def set_margins(l=0.13,b=0.13,r=0.96,t=0.96):
  #adjust margins - Setting margins for graphs
  fig = plt.gcf()
  fig.subplots_adjust(bottom=b,top=t,left=l,right=r)


def plotme(out_dir, data, name):
  """
  Explain function: what does it do, what do the arguments mean, and possibly an example.
  """
  plt.clf()

  data_x = []
  data_y = []

  d = handle_refugee_data.DataTable("mali2012/refugees.csv", csvformat="mali-portal")

  #Loop - taking the lenght of dataset for x and y rays & populating data to use for graphs
  for day in range(0, len(data["%s data" % name])):
    if d.is_interpolated(name, day) == False:
      #draw a point
      data_x.append(day)
      data_y.append(data.at[day,"%s data" % name])


  # data.loc[:,["%s sim" % name,"%s data" % name]]).as_matrix()
  y1 = data["%s sim" % name].as_matrix()
  y2 = data["%s data" % name].as_matrix()
  days = np.arange(len(y1))

  plt.xlabel("Days elapsed")

  matplotlib.rcParams.update({'font.size': 20})

  #Plotting lines representing simulation results and UNHCR data
  labelsim, = plt.plot(days,y1, linewidth=8, label="%s simulation" % (name.title()))
  labeldata, = plt.plot(days,y2, linewidth=8, label="%s UNHCR data" % (name.title()))
  plt.plot(data_x,data_y,'ob')

  plt.legend(handles=[labelsim, labeldata],loc=4,prop={'size':18})

  fig = matplotlib.pyplot.gcf()
  fig.set_size_inches(12, 8)
  #adjust margins
  set_margins()

  fig.savefig("%s/%s.png" % (out_dir, name))



def plotme_minimal(out_dir, data, name):
  """
  Explaining minimal graphs: populating data points to generate graphs and an example
  """

  plt.clf()

  data_x = []
  data_y = []

  d = handle_refugee_data.DataTable("mali2012/refugees.csv", csvformat="mali-portal")

  #Loop - taking the length of dataset for x and y rays 
  for day in range(0, len(data["%s data" % name])):
    if d.is_interpolated(name, day) == False:
      #draw a point
      data_x.append(day)
      data_y.append(data.at[day,"%s data" % name])

  # data.loc[:,["%s sim" % name,"%s data" % name]]).as_matrix()
  y1 = data["%s sim" % name].as_matrix()
  y2 = data["%s data" % name].as_matrix()
  days = np.arange(len(y1))

  matplotlib.rcParams.update({'font.size': 18})

  max_val = max([max(y1),max(y2)])

  #Graph labels
  plt.xticks([])
  plt.yticks([2000,5000])
  plt.ylim([0, 1.1*max_val])

  #Plotting lines representing simulation results and UNHCR data
  labelsim, = plt.plot(days,y1, linewidth=10, label="%s simulation" % (name.title()))
  labeldata, = plt.plot(days,y2, linewidth=10, label="%s UNHCR data" % (name.title()))
  plt.plot(data_x,data_y,'ob')


  #Text labels
  #plt.legend(handles=[labelsim, labeldata],loc=4,prop={'size':20})
  plt.gca().legend_ = None

  plt.text(295, 0.02*plt.ylim()[1], "%s" % (name.title()), size=24, ha='right')
  #plt.text(200, 0.02*plt.ylim()[1], "Max: %s" % (max(y1)), size=24)

  #Size of plots/graphs
  fig = matplotlib.pyplot.gcf()
  fig.set_size_inches(8, 6)
  #adjust margins.
  set_margins(l=0.14,b=0.13,r=0.96,t=0.96)

  fig.savefig("%s/min-%s.png" % (out_dir, name))


#Start of the code, assuring arguments of out-folder & csv file are kept
if __name__ == "__main__":

  if len(sys.argv)>1:
    out_dir = sys.argv[1]
  else:
    out_dir = "out"

  matplotlib.style.use('ggplot')
  #figsize=(15, 10)

  refugee_data = pd.read_csv("%s/out.csv" % (out_dir), sep=',', encoding='latin1',index_col='Day')

  #Identifying location names for graphs
  rd_cols = list(refugee_data.columns.values)
  location_names = []
  for i in rd_cols:
    if " sim" in i:
      if "numAgents" not in i:
        location_names.append(' '.join(i.split()[:-1]))

  #Plots for all locations
  for i in location_names:
    plotme(out_dir, refugee_data,i)
    plotme_minimal(out_dir, refugee_data,i)

  matplotlib.rcParams.update({'font.size': 20})

  plt.clf()
  diffdata = refugee_data.loc[:,["Total error"]].as_matrix()
  plt.plot(np.arange(len(diffdata)), diffdata, linewidth=5)
  #plt.legend(handles=[labeldiff],loc=2,prop={'size':14})

  #Size of plots/figures
  fig = matplotlib.pyplot.gcf()
  fig.set_size_inches(12, 8)

  #Plotting and saving error (differences) graph
  plt.ylabel("Averaged relative difference")
  plt.xlabel("Days elapsed")

  set_margins()
  plt.savefig("%s/error.png" % out_dir)

  #TODO: These labels need to be more flexible/modifiable.
  #Plotting and saving numagents (total refugee numbers) graph
  refugee_data.loc[:,["total refugees (simulation)","refugees in camps (UNHCR)"]].plot(linewidth=5)
  
  #Size of plots/figures
  fig = matplotlib.pyplot.gcf()
  fig.set_size_inches(12, 8)

  set_margins()
  plt.savefig("%s/numagents.png" % out_dir)

  if "retrofitted time" in refugee_data.columns:
    plt.clf()
    fit_time_data = refugee_data.loc[:,["retrofitted time"]].as_matrix()
    plt.plot(np.arange(len(fit_time_data)), fit_time_data, linewidth=5)
    #Size of plots/figures
  
    fig = matplotlib.pyplot.gcf()
    fig.set_size_inches(12, 8)
  
    plt.ylabel("Days passed in simulation")
    plt.xlabel("Days passed when mapped to UNHCR data")

    set_margins()
    plt.savefig("%s/time_evolution.png" % out_dir)
  
    sim_refs = refugee_data.loc[:,["refugees in camps (simulation)"]].as_matrix()
    un_refs = refugee_data.loc[:,["refugees in camps (UNHCR)"]].as_matrix()

    plt.clf()
    fit_time_data = refugee_data.loc[:,["retrofitted time"]].as_matrix()
    plt.plot(fit_time_data, sim_refs, linewidth=8, label="# in camps (sim, retrofitted)")
    plt.plot(range(0,len(sim_refs)), sim_refs, linewidth=5, label="# in camps (sim)")
    plt.plot(range(0,len(un_refs)), un_refs, linewidth=3, label="# in camps (data)")
    #Size of plots/figures
  
    fig = matplotlib.pyplot.gcf()
    fig.set_size_inches(12, 8)
  
    plt.ylabel("Number of refugees in camps")
    plt.xlabel("Simulated (or measured) days")

    set_margins()
    plt.savefig("%s/numagents_retrofitted.png" % out_dir)
