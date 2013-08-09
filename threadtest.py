#!/usr/bin/python
import os
import ephem as ep
import numpy as np
import time
import defines
import matplotlib.pyplot as plt
import sqlite3 as lite
import sys
import copy
import threading

arr = []
running = True


class DrawThread(threading.Thread):
  def run(self):
    global running
    while running:
      plt.cla()
      global arr
      plt.plot(arr, 'bo')
      plt.draw()
      #print 'DrawThread'
      #time.sleep(1)



class GenThread(threading.Thread):
  def run(self):
    global running
    while running:
      global arr
      arr = np.random.rand(10)
      #print 'GenThread'
      #time.sleep(1)


def hehe(event):
  global running
  print '--------------------------Hehe', event.key
  if event.key == '1':
    running = True
  if event.key == '2':
    running = False


if __name__ == '__main__':

  plt.ion()
  fig = plt.figure(figsize=(8,5))
  fig.add_subplot(111)
  d = DrawThread()
  d.start()
  time.sleep(0.5)
  g = GenThread()
  g.start()
  
  fig.canvas.mpl_connect('key_press_event', hehe)


