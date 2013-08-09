#!/usr/bin/python


import matplotlib.pyplot as plt
import numpy as np

def p(*args):
  print args
  plt.plot(*args)


#plt.ion()
p([1,2,3],'bo')
p([1,2,3],[4,3,2],'ro')
plt.show()
