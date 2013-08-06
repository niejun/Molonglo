#!/usr/bin/python

# Use following script to generate the mol_pulsars.db file for reading
#psrcat -c "jname s400 s1400 spindx rajd decjd p0 w50 dm raj decj" | awk '{if($1>0 && $4>=100 && $7>=30 && $14<=18) print  $2, $24, $27,\
#                                                                                                                          name ra   dec
#           $4*(400.0/843.0)**(log($7/$4)/log(400.0/1400.0)), $15, $18, $21}'|awk '{print NR, $0}' > mol_pulsars.txt
#                                      s843                    p0  w50  dm                             
#
# psrcat -c "jname s400 s1400 spindx rajd decjd p0 w50 dm raj decj" | awk '{if($1>0 && $4>=100 && $7>=30 && $14<=18) print  $2, $24, $27, $4*(400.0/843.0)**(log($7/$4)/log(400.0/1400.0)), $15, $18, $21, 100, -200, 1,3,30, 300, 120}' > mol_pulsars.txt
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
import copy

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

########################
##  Public Functions  ##
########################

def nowtime(s = DATE):
  return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(s))

def latertime(seconds):
  return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(DATE+seconds))

def strtime2sec(s):
  return time.mktime(time.strptime(s, "%Y-%m-%d %H:%M:%S"))

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

def tobs(SNR,EW,S843,P0,W50,G0=0.00001,Tsys=75,Nm=352,Bw=30000000,Np=1):
  """                                   _________________        _________________
         S843 * Nm * G0 * cos(EW)       |                        | 1000 * P0 - W50
  SNR = --------------------------- *   | Bw * Np * Tobs   *     |----------------
                Tsys + Tsky           \/                       \/        W50
                                      
  EW: radian
  S843: Hz
  P0: second
  W50: minisecond
  G0 = [0.01 K/Jy or 0.00001 K/mJy]
  Tsys = 75K
  Bw = 30MHz
  Nm = 2 [352 for final]
  Np = 1 [only 1 polarization]
  """
  return W50 / ((1000*P0-W50)*Np*Bw) * ((Tsys*SNR)/(S843*G0*Nm*np.cos(EW)))**2

def snr(Tobs,EW,S843,P0,W50,G0=0.00001,Tsys=75,Nm=352,Bw=30000000,Np=1):
  """                                   _________________        _________________
         S843 * Nm * G0 * cos(EW)       |                        | 1000 * P0 - W50
  SNR = --------------------------- *   | Bw * Np * Tobs   *     |----------------
              Tsys + Tsky             \/                       \/        W50
                                      
  EW: radian
  S843: Hz
  P0: second
  W50: minisecond
  G0 = [0.01 K/Jy or 0.00001 K/mJy]
  Tsys = 75K
  Bw = 30MHz
  Nm = 2 [352 for final]
  Np = 1 [only 1 polarization]
  """
  return (S843 * Nm * G0 * np.cos(EW) / Tsys) * np.sqrt(Bw * Np * Tobs) * np.sqrt((1000 * P0 - W50) / W50)

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


class LiteSQL():
  def __init__(self, txt=DEFAULT_PULSAR_TXT_FILE, db=DEFAULT_PULSAR_DB_FILE):
    self.txt = txt
    self.db = db
    self.con = None
    self.cur = None
    self.litecheckdb(self.db)
    self.litereadpulsarlist(self.db)

  def litecheckdb(self, db):
    exist = False
    if os.path.isfile(db):
      exist = True
      out('Database file %s exists'% db)
    self.con = lite.connect(db)
    self.cur = self.con.cursor()
    if exist == False:
      createtable = 'create table PulsarList(jname text primary key, raj text,decj text, s843 real, p0 real, w50 real, dm real, points_gain real, points_fail real, gap_min real, gap_max real, snr_min real, snr_min_tobs_max real, snr_max real )'
      self.litequery(createtable,db)
      createtable = 'create table PulsarLog(jname text, tstart int, tobs int, succeed int, points int, snr real)'
      self.litequery(createtable,db)
      createtable = 'create table PulsarJobs(jname text, tstart int, tobs int)'
      self.litequery(createtable,db)
      out('Database file %s not exists, created'% db)
      self.litetestdata(db)
      self.liteinitpulsarlist(self.txt, db)

  def litequery(self, sql, db):
    if self.con != None:
      self.cur.execute(sql)
      res = self.cur.fetchall()
      #dbg('Query %s'% sql)
      return res
    else:
      out('Database not exists, please check')


  def litetestdata(self, db):
    self.litequery("insert into PulsarList values('JTEST','12:00:00','45:00:00',34.56,12.3,4.32,126.7,100,-200,1,3,20,60,100)", db)
    res = self.litequery("select * from PulsarList where jname='JTEST'", db)
    for row in res:
      print 'Test data:'
      print row
    self.litequery("delete from PulsarList where jname='JTEST'", db)

  def liteinitpulsarlist( self, txt, db):
    f = file(txt)
    while True:
      line = f.readline()
      if len(line)!=0:
        if line[0]=='#':
          continue
        templist = line.replace('*','NULL')
        templist = templist.split(' ')
        templist[-1] = templist[-1].replace('\n','')
        sql = "insert into PulsarList values('"+templist[0]+"','"+templist[1]+"','"+templist[2]+"',"+str(templist[3])+","+str(templist[4])+","+str(templist[5])+","+str(templist[6])+","+str(templist[7])+","+str(templist[8])+","+str(templist[9])+","+str(templist[10])+","+str(templist[11])+","+str(templist[12])+","+str(templist[13])+");"
        #dbg(sql)
        self.litequery(sql, db)
        dbg('Loaded pulsar: '+templist[0])
      else:
        break

  def litereadpulsarlist(self, db):
    rows = self.litequery('select * from PulsarList', db)
    for row in rows:
      pulsarlist[str(row[0])] = [str(row[1]), str(row[2]), row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11], row[12], row[13] ]

  def __del__(self):
    self.con.commit()
    self.con.close()


#########################################################################################

##############
##  Point   ##
##############

class SimplePoint():
  def __init__(self, ewd, nsd):
    self.ewd = ewd
    self.nsd = nsd

class Point(ep.FixedBody):
  def __init__(self, ra, dec, observer, epoch='2000'):
    ep.FixedBody.__init__(self)
    self._ra = ra
    self._dec = dec
    self._epoch = epoch
    self.observer = observer
    self.calc(observer)
    """
    self.az
    self.alt
    self.ze
    self.ns
    self.ew
    self.nsd
    self.ewd
    have values
    """

  def reposition(self, observer):
    self.calc(observer)

  def calc(self, observer):
    self.compute(observer)
    self.ze = np.pi/2 - self.alt
    self.nsr = nsr(self.az, self.ze)
    self.ewr = ewr(self.az, self.ze)
    self.nsd = np.rad2deg(self.nsr)
    self.ewd = np.rad2deg(self.ewr)



#########################################################################################

##############
##  pulsar  ##
##############

class Pulsar(Point):
  def __init__(self, name, observer, epoch='2000'):
    self.found = False
    self.target_name = name
    if pulsarlist.has_key(name):
      attr = pulsarlist[name]
      print attr
      Point.__init__(self, attr[0], attr[1], observer, epoch)
      # {jname : [raj, decj, s843, p0, w50, dm, points_gain, points_fail, gap_min, gap_max, snr_min, snr_min_tbos_max, snr_max]}
      self.jname = name
      self.s843 = attr[2]
      self.p0 = attr[3]
      self.w50 = attr[4]
      self.dm = attr[5]
      self.points_gain = float(attr[6])
      self.points_fail = float(attr[7])
      self.gap_min = float(attr[8])
      self.gap_max = float(attr[9])
      self.snr_min = float(attr[10])
      self.snr_min_tobs_max = float(attr[11])
      self.snr_max = float(attr[12])
      self.found = True
      self.visible_eye = False
      self.visible_tel = False
      if self.alt > 0:
        self.visible_eye = True
        if self.nsd < N_LIMIT and W_LIMIT <= self.ewd <= E_LIMIT :
          self.visible_tel = True
      """
      self.az
      self.alt
      self.ze
      self.ns
      self.ew
      self.nsd
      self.ewd
      have values
      """

    else:
      D3('Cann\'t find the pulsar: '+name+'in the pulsar database file: '+DEFAULT_PULSAR_DB_FILE)

  def printPulsar(self):
    print 'Pulsar %s, RA: %s, Dec: %s is now in NSd: %f and EWd: %f, Az: %s and Alt: %s, visible by eyes: %s, visible by tel: %s, points_gain: %f, points_fail: %f'% (self.jname, self.ra, self.dec, self.nsd, self.ewd, self.az, self.alt, self.visible_eye, self.visible_tel, self.points_gain, self.points_fail)



#########################################################################################

################
##  Molonglo  ##
################


class Molonglo(ep.Observer):
  def __init__(self, date=nowtime()):
    ep.Observer.__init__(self)

    self.date = date
    self.lon = MOL_LON_R
    self.lat = MOL_LAT_R
    self.elevation = MOL_ELE_M
    self.compute_pressure()


#########################################################################################

################
##  Slewtime  ##
################

class SlewTime():
  def __init__(self,p1,p2):
    self.fineseconds = -1
    self.fineminutes = -1
    self.coarseseconds = -1
    self.coarseminutes = -1
    self.dest = None
    self.source = p1
    self.target = p2
    if self.target.visible_eye == True:
      self.fineSlewTime()
      self.coarseSlewTime()

  def subSlewTime(self, p1, p2):
    slewEW = p2.ewd - p1.ewd
    slewEWTime = np.abs(slewEW) / EW_SLEW_RATE
    slewNS = p2.nsd - p1.nsd
    slewNSTime = np.abs(slewNS) / NS_SLEW_RATE
    dbg('slewEW:\t'+str(slewEW))
    dbg('slewNS:\t'+str(slewNS))
    return np.maximum(slewEWTime, slewNSTime)

  def fineSlewTime(self):
    p1 = self.source
    p2 = Point(self.target._ra, self.target._dec, self.target.observer)
    i = 4
    while True:
      tt = self.subSlewTime(p1, p2)
      dbg('Slewtime: %f'% tt)
      if i<=1:
        self.fineseconds = tt
        self.fineminutes = tt / 60.0
        self.dest = p2
        break
      #dbg('fineSlewTime in while 1, %d'% i)
      p2.reposition(Molonglo(latertime(tt)))
      #dbg('fineSlewTime in while 2, %d'% i)
      i -= 1
      #dbg('fineSlewTime in while 3, %d'% i)

  def coarseSlewTime(self):
    self.coarseseconds = self.subSlewTime(self.source, self.target)
    self.coarseminutes = self.coarseseconds / 60.0
    
def positions(date):
  positionlist = {}
  for line in pulsarlist.keys():
    name = line
    attr = pulsarlist[line]
    pulsar = Pulsar(name, Molonglo(date))
    positionlist[name] = [pulsar.ewd, pulsar.nsd, pulsar.visible_eye, pulsar.visible_tel]
  return positionlist

def gotime(initp, date):
  gotimelist = {}
  for line in pulsarlist.keys():
    name = line
    attr = pulsarlist[line]
    pulsar = Pulsar(name, Molonglo(date))
    
    if pulsar.visible_eye == True:
      gotimelist[name] = [-1.0, -1.0, -1.0, -1.0]
      st = SlewTime(initp, pulsar)
      gotimelist[name][0] = st.fineseconds

      #snr(Tobs,EW,S843,P0,W50,G0=0.00001,Tsys=75,Nm=2,Bw=30,Np=1)
      tsnr = (snr(300, pulsar.ewr, pulsar.s843, pulsar.p0, pulsar.w50)+snr(300, st.dest.ewr, pulsar.s843, pulsar.p0, pulsar.w50))/2.0
      gotimelist[name][1] = tsnr

      #tobs(SNR,EW,S843,P0,W50,G0=0.00001,Tsys=75,Nm=2,Bw=30,Np=1)
      ttobs = tobs(pulsar.snr_min, (pulsar.ewr+st.dest.ewr)/2.0, pulsar.s843, pulsar.p0, pulsar.w50)
      gotimelist[name][2] = ttobs

  return gotimelist


def getCurrentPosition():
  # TODO: connect to TCC
  return SimplePoint(0.0,0.0)


def Scheduler(mode='manual'):
  if mode == 'manual':
  # TODO Manually controlling
    while True:
      if len(joblist) >= 6:
        time.sleep(10)
        continue
      curp = getCurrentPosition()
      
  else:
  # TODO Automatically controlling
    pass

def plotPulsarsZenith(observer, antenna=None, timetable=None,epoch='2000'):

  #plt.title('Pulsars over Molonglo @ '+nowtime(DATE))
  #plt.xlabel('W<------------------  Degree  ---------------->E')
  #plt.ylabel('S<------------------  Degree  ---------------->N')
  plt.axes([0.05,0.05,0.7,0.9])
  plt.axis('equal')
  plt.axis([-80,80,-100,60])
  plt.grid(True)
  plt.plot([W_LIMIT, W_LIMIT, E_LIMIT, E_LIMIT], [S_LIMIT, N_LIMIT, N_LIMIT, S_LIMIT], 'b-', lw='2')
  
  #initp = Point(antenna[0], antenna[1], observer, epoch)
  initp = SimplePoint(0.0,0.0)
  plt.plot([initp.ewd], [initp.nsd], 'r*')

  for line in pulsarlist.keys():
    name = line
    attr = pulsarlist[line]
    pulsar = Pulsar(name, observer)
    slewtable[name] = [-1.0, -1.0, -1.0, -1.0]
    if pulsar.visible_eye == True:
      if pulsar.visible_tel == True:
        plt.plot(pulsar.ewd, pulsar.nsd, 'bo')
      else:
        plt.plot(pulsar.ewd, pulsar.nsd, 'ro')
      st = SlewTime(initp, pulsar)
      slewtable[name][0] = st.fineseconds
      slewtable[name][1] = st.fineminutes

      #snr(Tobs,EW,S843,P0,W50,G0=0.00001,Tsys=75,Nm=2,Bw=30,Np=1)
      tsnr = (snr(300, pulsar.ewr, pulsar.s843, pulsar.p0, pulsar.w50)+snr(300, st.dest.ewr, pulsar.s843, pulsar.p0, pulsar.w50))/2.0
      slewtable[name][2] = tsnr
      #tobs(SNR,EW,S843,P0,W50,G0=0.00001,Tsys=75,Nm=2,Bw=30,Np=1)
      ttobs = tobs(pulsar.snr_min, (pulsar.ewr+st.dest.ewr)/2.0, pulsar.s843, pulsar.p0, pulsar.w50)
      slewtable[name][3] = ttobs

      tt = round(slewtable[name][1], 2)
      ts = round(slewtable[name][2], 2)
      to = round(slewtable[name][3], 2)

      plt.text(pulsar.ewd+1, pulsar.nsd-2.4, name+'\nTsl:'+str(tt)+',S/R:'+str(ts)+',Tobs:'+str(to), fontsize='9')
    else:
      plt.plot(pulsar.ewd, pulsar.nsd, 'gx')
      plt.text(pulsar.ewd+1, pulsar.nsd-2.4, name, fontsize='9')

def plotPulsars(observer, antenna=None, timetable=None, epoch='2000'):
  #plotPulsarsRADec(pulsarlist)
  plotPulsarsZenith(observer, antenna, timetable)
  plt.show()
  






if __name__ == '__main__':
  s = LiteSQL()
  print pulsarlist.keys()

  date = '2013-7-30 02:00:00'
  date = nowtime()
  DATE = strtime2sec(date)

  

  ob = Molonglo(date)

  p = Pulsar('J0437-4715', ob)
  p.printPulsar()

  plotPulsars(ob)

  print slewtable

