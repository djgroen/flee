class Disease():
  def __init__(self, infection_rate, incubation_period, recovery_period, mortality_period):
    self.infection_rate = infection_rate
    self.incubation_period = incubation_period
    self.recovery_period = recovery_period
    self.mortality_period = mortality_period

  def print(self):
    print(self.infection_rate, self.incubation_period, self.recovery_period, self.mortality_period)

