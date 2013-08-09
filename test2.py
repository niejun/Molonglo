#!/usr/bin/python


import matplotlib.pyplot as plt

def enter_figure(event):
  print 'Enter figure', event.canvas.figure
  event.canvas.figure.patch.set_facecolor('red')
  event.canvas.draw()

def leave_figure(event):
  print 'Leave figure', event.canvas.figure
  event.canvas.figure.patch.set_facecolor('grey')
  event.canvas.draw()

def enter_axes(event):
  print 'Enter Axes', event.inaxes
  event.inaxes.patch.set_facecolor('green')
  event.canvas.draw()

def leave_axes(event):
  print 'Leave Axes', event.inaxes
  event.inaxes.patch.set_facecolor('blue')
  event.canvas.draw()

fig = plt.figure()
fig.add_subplot(121)
fig.add_subplot(122)

fig.canvas.mpl_connect('figure_enter_event', enter_figure)
fig.canvas.mpl_connect('figure_leave_event', leave_figure)
fig.canvas.mpl_connect('axes_enter_event', enter_axes)
fig.canvas.mpl_connect('axes_leave_event', leave_axes)



plt.show()
