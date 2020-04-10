import csv
import sys
from datetime import datetime
from datetime import timedelta

#format: x,y,age,date,time (ignored)
#-0.338880986,51.5628624,27,3/16/2020

def subtract_dates(date1, date2, date_format="%m/%d/%Y"):
  """
  Takes two dates %m/%d/%Y format. Returns date1 - date2, measured in days.
  """
  a = datetime.strptime(date1, date_format)
  b = datetime.strptime(date2, date_format)
  delta = a - b
  return delta.days

def read_cases_csv(e, csvfile, date_format="%m/%d/%Y", start_date="3/18/2020"):
  period_to_hosp = 11
  period_to_rec = 25

  num_infections = 0
  if csvfile == "":
    print("Error: could not find csv file.")
    sys.exit()
  with open(csvfile) as csvfile:
    cases_reader = csv.reader(csvfile)
    next(cases_reader)
    for row in cases_reader:
      if len(row[3]) > 0:
        day = subtract_dates(row[3], start_date, date_format)
        if day<0 and day > - (period_to_rec - period_to_hosp):
          e.add_infection(float(row[0]), float(row[1]), int(row[2]), day-period_to_hosp) 
          e.add_infections(16, day-period_to_hosp) # 1 hospitalisation per 16.67 infections (0.06 prob).
          num_infections += 17
        e.add_validation_point(day)
  print("Using start date {} with {} infections initially.".format(start_date, num_infections))

