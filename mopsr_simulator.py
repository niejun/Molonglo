#!/usr/bin/python


###############
##  Imports  ##
###############
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
import eventlet
import lxml.etree as et
import lxml as xml

############################
##  Constant definitions  ##
############################
# Debug and output
DBG = True
OUT = True

# Molonglo observatory geographic information
# Degree
MOL_LAT_D = -35.37075
MOL_LON_D = 149.424702
# Radian
MOL_LAT_R = np.deg2rad(MOL_LAT_D)
MOL_LON_R = np.deg2rad(MOL_LON_D)
# Elevation
MOL_ELE_M = 735.031

# Pulsar list files
DEFAULT_PULSAR_TXT_FILE = '.'+os.sep+'mol_pulsars.txt'
DEFAULT_PULSAR_DB_FILE = '.'+os.sep+'mol_pulsars.db'
DEFAULT_OBS_DB_FILE = '.'+os.sep+'mod_obs.db'

# Slew rate, degrees per second
EW_SLEW_RATE = 4.0 / 60.0
NS_SLEW_RATE = 5.0 / 60.0

# Antenna slew limitation, degree
E_LIMIT = 15.0
W_LIMIT = -15.0
N_LIMIT = 53.37
S_LIMIT = -90.0

# Default date(seconds from 1970) for overall observatory
DATE = time.time()

#########################
##  Gloabel variables  ##
#########################

# List for storing pulsars
# {jname : [raj, decj, s843, p0, w50, dm, points_gain, points_fail, gap_min, gap_max, snr_min, snr_min_tbos_max, snr_max]}
pulsarlist = {}
pulsarposition = []
slewtable = {}
joblist = []
running = False
in_buffer = ''
out_buffer = ''
mopsr_status = 'ready'



########################
##  Public Functions  ##
########################

# D1 for tracking program
def dbg(string):
  if DBG == True:
    print '[DBG-%s]  '% nowtime() + string

# D2 for output information
def out(string):
  if OUT == True:
    print '[OUT-%s]  '% nowtime() + string

def nowtime(s = DATE):
  return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(s))

def latertime(seconds):
  return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(DATE+seconds))

def strtime2sec(s):
  return time.mktime(time.strptime(s, "%Y-%m-%d %H:%M:%S"))



class Server(threading.Thread):
  def __init__(self):
    threading.Thread.__init__(self)
    self.server = eventlet.listen(('0.0.0.0', 6000))
    self.pool = eventlet.GreenPool()

  def run(self):
    while True:
      try:
          new_sock, address = self.server.accept()
          print "accepted", address
          self.pool.spawn_n(self.handle, new_sock.makefile('rw'))
      except (SystemExit, KeyboardInterrupt):
          break
  
  def handle(self,fd):
    print "client connected"
    global in_buffer, out_buffer, mopsr_status
    while True:
        # pass through every non-eof line
        out('Waiting for incoming data')
        in_buffer = fd.readline()
        out('In buffer: %s'%in_buffer)
        if not in_buffer: break
        dbg(in_buffer)
        try:
          out_buffer = ''
          tempdom = et.Element('Molonglo')
          dtree = et.fromstring(in_buffer)
          if dtree.tag != 'Molonglo':
            continue
          for i in dtree:
            if i.tag == 'mopsr':
              a00 = et.SubElement(tempdom, 'mopsr')
              for j in i:
                if j.tag == 'query':
                  for k in j:
                    if k.tag == 'status':
                      a01 = et.SubElement(a00, k.tag)
                      a01.text = mopsr_status
                  out_buffer = et.tostring(tempdom)
                  dbg(et.tostring(tempdom))
                if j.tag == 'set':
                  for k in j:
                    if k.tag == 'status':
                      mopsr_status = k.text

        except(et.LxmlError):
          out('Error with XML parsing%s'%et.LxmlError.message)
        if out_buffer != '':
          dbg(out_buffer)
          fd.write(out_buffer)
          fd.flush()

    print "client disconnected"

class Interactive(threading.Thread):
  def __init__(self):
    threading.Thread.__init__(self)
  
  def run(self):
    global mopsr_status
    while True:
      if mopsr_status == 'ready':
        time.sleep(1)
        continue
      if mopsr_status == 'recording':
        time.sleep(20)
        mopsr_status = 'ready'
        continue

if __name__ == '__main__':
  out('MOPSR Simulator')
  s = Server()
  s.start()
  i = Interactive()
  i.start()
