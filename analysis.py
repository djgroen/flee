import numpy as np

def rel_error(val, correct_val):
  if correct_val < 0.00001:
    return 0.0
  return np.abs(float(val)/float(correct_val) - 1)

def abs_error(val, correct_val):
  return np.abs(float(val) - float(correct_val))
