import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import matplotlib
import sys
import handle_refugee_data
import warnings
import analysis as a
warnings.filterwarnings("ignore")


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


def plotme(out_dir, data, name, retrofitted=True, offset=0):
  """
  Explain function: what does it do, what do the arguments mean, and possibly an example.
  """
  plt.clf()

  # data.loc[:,["%s sim" % name,"%s data" % name]]).as_matrix()
  y1 = data["%s sim" % name].as_matrix()
  y2 = data["%s data" % name].as_matrix()
  days = np.arange(len(y1))

  plt.xlabel("Days elapsed")

  matplotlib.rcParams.update({'font.size': 20})

  #Plotting lines representing simulation results and UNHCR data
  if retrofitted==False:
    if offset == 0:
      labelsim, = plt.plot(days,y1, linewidth=8, label="%s simulation" % (name.title()))
    if offset > 0:
      labelsim, = plt.plot(days[:-offset],y1[offset:], linewidth=8, label="%s simulation" % (name.title()))
  else:
    retrofitted_times = refugee_data.loc[:,["retrofitted time"]].as_matrix()
    labelsim, = plt.plot(retrofitted_times, y1, linewidth=8, label="%s simulation" % (name.title()))
  labeldata, = plt.plot(days,y2, linewidth=8, label="%s UNHCR data" % (name.title()))

  if retrofitted==True:
    plt.xlim(0,retrofitted_times[-1])

  plt.legend(handles=[labelsim, labeldata],loc=4,prop={'size':18})

  fig = matplotlib.pyplot.gcf()
  fig.set_size_inches(12, 8)
  #adjust margins
  set_margins()

  if retrofitted==False:
    if offset == 0:
      fig.savefig("%s/%s.png" % (out_dir, name))
    else:
      fig.savefig("%s/%s-offset.png" % (out_dir, name))
  else:
    fig.savefig("%s/%s-retrofitted.png" % (out_dir, name))



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

  RetroFitting = False
  if len(sys.argv)>2:
    if "-r" in sys.argv[2]:
      RetroFitting = True


  matplotlib.style.use('ggplot')
  #figsize=(15, 10)

  refugee_data = pd.read_csv("%s/out.csv" % (out_dir), sep=',', encoding='latin1',index_col='Day')
  if RetroFitting == True:
    refugee_data = pd.read_csv("%s/out-retrofitted.csv" % (out_dir), sep=',', encoding='latin1',index_col='Day')

  #Identifying location names for graphs
  rd_cols = list(refugee_data.columns.values)
  location_names = []
  for i in rd_cols:
    if " sim" in i:
      if "numAgents" not in i:
        location_names.append(' '.join(i.split()[:-1]))


  #Plotting and saving numagents (total refugee numbers) graph
  #TODO: These labels need to be more flexible/modifiable.

  plt.xlabel("Days elapsed")

  matplotlib.rcParams.update({'font.size': 20})


  if "refugee_debt" in refugee_data.columns:
    refugee_data.loc[:,["total refugees (simulation)","refugees in camps (UNHCR)","raw UNHCR refugee count","refugee_debt"]].plot(linewidth=5)
  else:
    refugee_data.loc[:,["total refugees (simulation)","refugees in camps (UNHCR)","raw UNHCR refugee count"]].plot(linewidth=5)
  
  #Size of plots/figures
  fig = matplotlib.pyplot.gcf()
  fig.set_size_inches(12, 8)

  set_margins()
  plt.savefig("%s/numagents.png" % out_dir)



  # Calculate the best offset.

  sim_refs = refugee_data.loc[:,["refugees in camps (simulation)"]].as_matrix()
  un_refs = refugee_data.loc[:,["refugees in camps (UNHCR)"]].as_matrix()
  raw_refs = refugee_data.loc[:,["raw UNHCR refugee count"]].as_matrix()

  offset = 0

  if RetroFitting == False:
    min_error = 1000000
    error_at_zero_offset = 0

    for i in range(0,200):
      compare_len = len(sim_refs[i:])
      error = np.mean(np.abs(sim_refs[i:] - un_refs[:compare_len]))

      if i == 0:
        error_at_zero_offset = error

      #print("error with offset ", i, " is: ", error)
      if error < min_error:
        min_error = error
        offset = i

    print(out_dir, ": The best offset = ", offset, ", error = ", min_error, ", error at offset 0 = ",error_at_zero_offset)


  # Recalculate and print the error when offset is set.

  total_errors = []
  total_errors_0 = []

  for d in range(0, len(sim_refs[offset:])):
    # calculate error terms.
    camp_pops = []
    errors = []
    errors_0 = []
    abs_errors = []
    abs_errors_0 = []
    #camp_pops_retrofitted = []
    #errors_retrofitted = []
    #abs_errors_retrofitted = []
    for name in location_names:
      y2 = refugee_data["%s data" % name].as_matrix()
      y1 = (refugee_data["%s sim" % name].as_matrix())[offset:]
      days = np.arange(len(y1))

      # normal 1 step = 1 day errors.
      camp_pops += [y2[d]]
      errors += [a.rel_error(y1[d], camp_pops[-1])]
      abs_errors += [a.abs_error(y1[d], camp_pops[-1])]

      # errors when using retrofitted time stepping.
      #camp_pops_retrofitted += [d.get_field(camp_names[i], t_retrofitted, FullInterpolation=True)]
      #errors_retrofitted += [a.rel_error(camps[i].numAgents, camp_pops_retrofitted[-1])]
      #abs_errors_retrofitted += [a.abs_error(camps[i].numAgents, camp_pops_retrofitted[-1])]

      y1_0 = refugee_data["%s sim" % name].as_matrix()
      days_0 = np.arange(len(y1_0))
      errors_0 += [a.rel_error(y1_0[d], camp_pops[-1])]
      abs_errors_0 += [a.abs_error(y1_0[d], camp_pops[-1])]

    if un_refs[d] > 0.0:
      total_errors += [float(np.sum(abs_errors))/float(raw_refs[d])]
      total_errors_0 += [float(np.sum(abs_errors_0))/float(raw_refs[d])]
      #total_errors_retrofitted += [float(np.sum(abs_errors_retrofitted))/float(un_refs[d])]
    # Total error is calculated using float(np.sum(abs_errors))/float(refugees_raw))

  #print(out_dir,": Averaged error with", offset, "offset: ", np.trapz(np.array(total_errors) ** 2.0) / (1.0*len(total_errors)))
  #print(out_dir,": Averaged error with no offset: ", np.trapz(np.array(total_errors_0) ** 2.0) / (1.0*len(total_errors_0)))


  #Plots for all locations, one .png file for every time plotme is called.
  for i in location_names:

    plotme(out_dir, refugee_data, i, retrofitted=RetroFitting)

    if not RetroFitting and offset>0:
      plotme(out_dir, refugee_data, i, retrofitted=RetroFitting, offset=offset)

    #plotme_minimal(out_dir, refugee_data,i)

  matplotlib.rcParams.update({'font.size': 20})

  plt.clf()

  # ERROR PLOTS

  #Size of plots/figures
  fig = matplotlib.pyplot.gcf()
  fig.set_size_inches(12, 8)

  #Plotting and saving error (differences) graph
  plt.ylabel("Averaged relative difference")
  plt.xlabel("Days elapsed")

  if RetroFitting==False:
    diffdata = (refugee_data.loc[:,["Total error"]].as_matrix()).flatten()
    print(out_dir,": Averaged error with 0 offset: ",  np.trapz(diffdata ** 2.0) / (1.0*len(diffdata)))
    plt.plot(np.arange(len(diffdata)), diffdata, linewidth=5, label="error")
    #plt.legend(handles=[labeldiff],loc=2,prop={'size':14})
  
    set_margins()
    plt.savefig("%s/error.png" % out_dir)

  # Plot error using retrofitting if applicable.
  if RetroFitting==True and "Total error (retrofitted)" in refugee_data.columns:
    offset = 0
    retrofitted_times = (refugee_data.loc[:,["retrofitted time"]].as_matrix()).flatten()
    for i in range(0,len(retrofitted_times)):
      if retrofitted_times[i] > 0.1:
        continue
      offset += 1

    diffdata_retro = (refugee_data.loc[:,["Total error (retrofitted)"]].as_matrix()).flatten()
    print(out_dir,": Averaged error (retrofitted): ", np.trapz((diffdata_retro[offset:]**2.0), retrofitted_times[offset:]) / retrofitted_times[-1])
    plt.plot(retrofitted_times[offset:], diffdata_retro[offset:], linewidth=5, label="error (retrofitted)")

    set_margins()
    plt.savefig("%s/error-retrofitted.png" % out_dir)

    plt.clf()

    refugee_data_normal_time = pd.read_csv("%s/out.csv" % (out_dir), sep=',', encoding='latin1',index_col='Day')
    diffdata = (refugee_data_normal_time.loc[:,["Total error"]].as_matrix()).flatten()
    plt.plot(np.arange(len(diffdata)), diffdata, linewidth=5, label="error")
    plt.plot(retrofitted_times[offset:], diffdata_retro[offset:], linewidth=5, label="error (retrofitted)")
    #plt.legend(handles=[labeldiff],loc=2,prop={'size':14})
  
    set_margins()
    plt.legend()
    plt.savefig("%s/error-both.png" % out_dir)

  plt.clf()



  if RetroFitting==True and "retrofitted time" in refugee_data.columns:
    plt.clf()
    fit_time_data = refugee_data.loc[:,["retrofitted time"]].as_matrix()
    plt.plot(np.arange(len(fit_time_data)), fit_time_data, linewidth=5)
    plt.plot(np.arange(len(fit_time_data)), np.arange(len(fit_time_data)), linewidth=3)
    #Size of plots/figures
  
    fig = matplotlib.pyplot.gcf()
    fig.set_size_inches(12, 8)
  
    plt.xlabel("Steps taken in simulation")
    plt.ylabel("Days passed when mapped to UNHCR data")

    set_margins()
    plt.savefig("%s/time_evolution.png" % out_dir)
  

    # Sim and data comparison.
    plt.clf()

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
    
    plt.legend(loc=4)


    set_margins()
    plt.savefig("%s/numagents_retrofitted.png" % out_dir)

