import os

for name in ["brent","ealing","harrow","hillingdon"]:
  for runtype in ["default","lockSDCI","post-lockdown"]:
    for script in ["LineChart.py","DailyChart.py"]:
      csvname = "{}-{}".format(name,runtype)
      print("python3 {} {}.csv".format(script,csvname))
      os.system("python3 {} {}.csv".format(script,csvname))
