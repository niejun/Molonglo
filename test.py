#!/usr/bin/python

import matplotlib.pyplot as plt
import numpy as np


fig = plt.figure()
ax = fig.add_subplot(111)
ax.plot(np.random.rand(10))

p = [0,0]


def onclick(event):
  print 'Button=',event.button,' x=',event.x, 'y=', event.y, 'xdata=',event.xdata, 'ydata=', event.ydata
  if p != [0,0]:
    ax.plot([p[0], event.xdata], [p[1], event.ydata], 'b-')
    plt.draw()
    print 'Line'
    p[0] = event.xdata
    p[1] = event.ydata
  else:
    p[0] = event.xdata
    p[1] = event.ydata

cid = fig.canvas.mpl_connect('button_press_event', onclick)

plt.show()
