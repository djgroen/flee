class Disease():
  def __init__(self, infection_rate, incubation_period, mild_recovery_period, recovery_period, mortality_period, period_to_hospitalisation):
    self.infection_rate = infection_rate
    self.incubation_period = incubation_period
    self.mild_recovery_period = mild_recovery_period
    self.recovery_period = recovery_period
    self.mortality_period = mortality_period
    self.period_to_hospitalisation = period_to_hospitalisation

  def print(self):
    print(self.infection_rate, self.incubation_period, self.mild_recovery_period, self.recovery_period, self.mortality_period)

