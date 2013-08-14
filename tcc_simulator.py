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
# not_connect, ready, slewing, tracking
tcc_status = 'ready'
antenna_now_position_ewd = 0.0
antenna_now_position_nsd = 0.0

antenna_destination_position_ewd = 0.0
antenna_destination_position_nsd = 0.0

# idle, point, tracking, scan
tcc_action = 'idle'


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
    self.server = eventlet.listen(('0.0.0.0', 6001))
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
    global in_buffer, out_buffer, tcc_status, antenna_now_position_ewd, antenna_now_position_nsd, antenna_destination_position_ewd, antenna_destination_position_nsd, tcc_action
    while True:
        # pass through every non-eof line
        in_buffer = fd.readline()
        if not in_buffer: break
        dbg(in_buffer)
        try:
          out_buffer = ''
          tempdom = et.Element('Molonglo')
          dtree = et.fromstring(in_buffer)
          if dtree.tag != 'Molonglo':
            continue
          for i in dtree:
            if i.tag == 'query':
              for j in i:
                if j.tag == 'tcc_status':
                  a00 = et.SubElement(tempdom, j.tag)
                  a00.text = tcc_status
                if j.tag == 'antenna_position':
                  a00 = et.SubElement(tempdom, j.tag)
                  a00.text = str(antenna_now_position_ewd)+','+str(antenna_now_position_nsd)

            if i.tag == 'set':
              for j in i:
                if j.tag == 'tcc':
                  for k in j:
                    if k.tag == 'point' or k.tag == 'track' or k.tag == 'scan':
                      tcc_action = k.tag
                      tempposi = k.text
                      tempposia = tempposi.split(',')
                      antenna_destination_position_ewd = float(tempposia[0])
                      antenna_destination_position_nsd = float(tempposia[1])
                      dbg(tempposi)
                      a00 = et.SubElement(tempdom, 'Done')
                      a00.text = k.tag
          out_buffer = et.tostring(tempdom)
          dbg(et.tostring(tempdom))
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
    global tcc_status, antenna_now_position_ewd, antenna_now_position_nsd, antenna_destination_position_ewd, antenna_destination_position_nsd, tcc_action
    while True:
      if tcc_action == 'idle':
        tcc_status = 'ready'
        time.sleep(1)
        continue
      if tcc_action == 'point' and tcc_status == 'ready':
        dbg('Point slewing')
        tcc_status = 'slewing'
        ewdiff = antenna_destination_position_ewd - antenna_now_position_ewd
        nsdiff = antenna_destination_position_nsd - antenna_now_position_nsd
        if ewdiff < 0:
          ewdiff = - EW_SLEW_RATE
        else:
          ewdiff = EW_SLEW_RATE
        if nsdiff < 0:
          nsdiff = - NS_SLEW_RATE
        else:
          nsdiff = NS_SLEW_RATE
        onslewew = True
        onslewns = True
        while onslewew or onslewns:
          if np.abs(antenna_destination_position_ewd - antenna_now_position_ewd) > 0.1:
            antenna_now_position_ewd = antenna_now_position_ewd + ewdiff
          else:
            antenna_now_position_ewd = antenna_destination_position_ewd
            onslewew = False

          if np.abs(antenna_destination_position_nsd - antenna_now_position_nsd) > 0.1:
            antenna_now_position_nsd = antenna_now_position_nsd + nsdiff
          else:
            antenna_now_position_nsd = antenna_destination_position_nsd
            onslewns = False
          time.sleep(1)
        tcc_status = 'ready'
        tcc_action = 'idle'
        continue
      if tcc_action == 'track' and tcc_status == 'ready':
        dbg('Track slewing')
        tcc_status = 'slewing'
        ewdiff = antenna_destination_position_ewd - antenna_now_position_ewd
        nsdiff = antenna_destination_position_nsd - antenna_now_position_nsd
        if ewdiff < 0:
          ewdiff = - EW_SLEW_RATE
        else:
          ewdiff = EW_SLEW_RATE
        if nsdiff < 0:
          nsdiff = - NS_SLEW_RATE
        else:
          nsdiff = NS_SLEW_RATE
        onslewew = True
        onslewns = True
        while onslewew or onslewns:
          if np.abs(antenna_destination_position_ewd - antenna_now_position_ewd) > 0.1:
            antenna_now_position_ewd = antenna_now_position_ewd + ewdiff
          else:
            antenna_now_position_ewd = antenna_destination_position_ewd
            onslewew = False

          if np.abs(antenna_destination_position_nsd - antenna_now_position_nsd) > 0.1:
            antenna_now_position_nsd = antenna_now_position_nsd + nsdiff
          else:
            antenna_now_position_nsd = antenna_destination_position_nsd
            onslewns = False
          time.sleep(1)
        tcc_status = 'tracking'
        dbg('Tracking')
        time.sleep(30)
        tcc_status = 'ready'
        tcc_action = 'idle'


if __name__ == '__main__':
  out('TCC Simulator')
  s = Server()
  s.start()
  i = Interactive()
  i.start()
