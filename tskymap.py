#!/usr/bin/python


import matplotlib.pyplot as plt
import numpy as np

f = file('tsky.dat')
a = []

while True:
  b = f.readline()
  if len(b) == 0:
    break
  for i in np.arange(16):
    sl = b[i*5:i*5+5]
    sl = sl.replace('\n','')
    #print sl
    if sl != '':
      a.append(float(sl))
      #print float(b[i*5:i*5+5])

plt.plot(a,'bo')
plt.show()
