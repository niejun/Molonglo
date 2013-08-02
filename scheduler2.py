#!/usr/bin/python

# Use following script to generate the mol_pulsars.db file for reading
#psrcat -c "jname s400 s1400 spindx rajd decjd p0 w50 dm raj decj" | awk '{if($1>0 && $4>=100 && $7>=30 && $14<=18) print  $2, $24, $27,\
#                                                                                                                          name ra   dec
#           $4*(400.0/843.0)**(log($7/$4)/log(400.0/1400.0)), $15, $18, $21}'|awk '{print NR, $0}' > mol_pulsars.txt
#                                      s843                    p0  w50  dm                             
#
# psrcat -c "jname s400 s1400 spindx rajd decjd p0 w50 dm raj decj" | awk '{if($1>0 && $4>=100 && $7>=30 && $14<=18) print  $2, $24, $27, $4*(400.0/843.0)**(log($7/$4)/log(400.0/1400.0)), $15, $18, $21}'|awk '{print NR, $0}' > mol_pulsars.txt
#

# Examples:

#    jname       ra        dec     s843         p0              w50    dm
#1 J0437-4715 69.31618 -47.25251 252.839 0.005757451924362137 0.1410 2.64476
#2 J0738-4042 114.63470 -40.71137 113.554 0.374919985032 29 160.8
#3 J0835-4510 128.83588 -45.17635 2030.74 0.089328385024 2.1 67.99
#4 J0953+0755 148.28879 7.92660 158.024 0.2530651649482 9.5 2.958
#5 J1136+1551 174.01353 15.85124 74.389 1.187913065936 31.7 4.864
#6 J1456-6843 224.00066 -68.72757 145.422 0.2633768148933 12.5 8.6
#7 J1559-4438 239.92303 -44.64608 60.2493 0.2570560976508 6 56.1
#8 J1644-4559 251.20534 -45.98597 334.839 0.455059775403 8.2 478.8
#9 J1932+1059 293.05812 10.99234 85.2912 0.226517635038 7.4 3.180
#10 J1935+1616 293.94927 16.27777 85.3518 0.3587384107696 9.0 158.521

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


#########################
##  Gloabel variables  ##
#########################

# List for storing pulsars
# jname, raj, decj, s843, p0, w50, dm, points_gain, points_fail, gap_min, gap_max, snr_min, snr_min_tbos_max, snr_max
pulsarlist = []
pulsarposition = []

########################
##  Public Functions  ##
########################

def nowtime():
  return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())

def latertime(seconds):
  return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(time.time()+seconds))

# D1 for tracking program
def dbg(string):
  if DBG == True:
    print '[DBG-%s]  '% nowtime() + string

# D2 for output information
def out(string):
  if OUT == True:
    print '[OUT-%s]  '% nowtime() + string

def ewr(az, ze):
  return np.arcsin(np.sin(az)*np.sin(ze))

def nsr(az, ze):
  return np.arcsin(np.cos(az)*np.sin(ze))

def ewd(az, ze):
  return ewr(az,ze) * 180 / np.pi

def nsd(az, ze):
  return nsr(az,ze) * 180 / np.pi

def tobs(SNR,EW,S843,P0,W50,G0=0.00001,Tsys=75,Nm=2,Bw=30,Np=1):
  """                                   _________________        _________________
         S843 * Nm * G0 * cos(EW)       |                        | 1000 * P0 - W50
  SNR = --------------------------- *   | Bw * Np * Tobs   *     |----------------
                   Tsys               \/                       \/        W50
                                      
  EW: radian
  S843: MHz
  P0: second
  W50: minisecond
  G0 = [0.01 K/Jy or 0.00001 K/mJy]
  Tsys = 75K
  Bw = 30MHz
  Nm = 2 [352 for final]
  Np = 1 [only 1 polarization]
  """
  return ((Tsys*SNR)/(S843*G0*np.cos(EWd)))**2 * W50 / ((P0-W50)*Np*Bw)

def snr(Tobs,EW,S843,P0,W50,G0=0.00001,Tsys=75,Nm=2,Bw=30,Np=1):
  """                                   _________________        _________________
         S843 * Nm * G0 * cos(EW)       |                        | 1000 * P0 - W50
  SNR = --------------------------- *   | Bw * Np * Tobs   *     |----------------
                   Tsys               \/                       \/        W50
                                      
  EW: radian
  S843: MHz
  P0: second
  W50: minisecond
  G0 = [0.01 K/Jy or 0.00001 K/mJy]
  Tsys = 75K
  Bw = 30MHz
  Nm = 2 [352 for final]
  Np = 1 [only 1 polarization]
  """
  return (S843 * Nm * G0 * cos(EW) / Tsys) * np.sqrt(Bw * Np * Tobs) * np.sqrt((1000*P0) - W50) / W50)


def ratime2rad(time):
  hms = time.split(':')
  h = float(hms[0])
  m = 0.0
  s = 0.0
  if len(hms) >=2:
    m = float(hms[1])
    if len(hms) == 3:
      s = float(hms[2])
  return 2*np.pi*( h /24.0+ m /(24.0*60.0)+ s /(24.0*60.0*60.0))

def decdeg2rad(deg):
  dms = deg.split(':')
  mark = 1.0
  if dms[0][0]=='-':
    mark = -1.0
  d = float(dms[0])
  absd = np.abs(d)
  m = 0.0
  s = 0.0
  if len(dms) >=2:
    m = float(dms[1])
    if len(dms) == 3:
      s = float(dms[2])
  return mark * np.deg2rad(absd+ m /60.0+ s /(60.0*60.0))

def query(sql, db=''):
  con = lite.connect()



