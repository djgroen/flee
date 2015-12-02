import numpy as np

def rel_error(val, correct_val):
  if correct_val == 0.0:
    return -1
  return np.abs(1.0 - float(val)/float(correct_val))

def abs_error(val, correct_val):
  return np.abs(float(correct_val) - float(val))
