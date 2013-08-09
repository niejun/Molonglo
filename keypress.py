#!/usr/bin/env python

import time,struct,sys
import matplotlib.pyplot as plt
from numpy import *

def key(event):
  print 'Key is pressed:', event.key, event.xdata, event.ydata
  
fig = plt.figure()
ax = fig.add_subplot(111)
ax.plot([1,2,3],'bo')
fig.canvas.mpl_connect('key_press_event', key)

plt.show()
