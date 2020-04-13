import csv
import sys
import pprint
import yaml
from flee import disease

pp = pprint.PrettyPrinter()

def read_disease_yml(ymlfile="covid_data/disease-covid19.yml"):

  disease_parameters = {}
  with open(ymlfile) as f:
    dp = yaml.load(f, Loader=yaml.FullLoader)
  d = disease.Disease(dp["infection_rate"], dp["incubation_period"], dp["mild_recovery_period"], dp["recovery_period"], dp["mortality_period"], dp["period_to_hospitalisation"])
  d.addHospitalisationChances(dp["hospitalised"])
  d.print()
  return d


