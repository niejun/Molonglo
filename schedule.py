#!/usr/bin/python

# Use following script to generate the mol_pulsars.db file for reading
#psrcat -c "jname s400 s1400 spindx rajd decjd p0 w50 dm raj decj" | awk '{if($1>0 && $4>=100 && $7>=30 && $14<=18) print  $2, $24, $27,\
#                                                                                                                          name ra   dec
#           $4*(400.0/843.0)**(log($7/$4)/log(400.0/1400.0)), $15, $18, $21}'|awk '{print NR, $0}' > mol_pulsars.db
#                                      s843                    p0  w50  dm                             


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

###################
##  Definitions  ##
###################
dbg1 = True
dbg2 = True
dbg3 = True

mol_lat_d = -35.37075
mod_lon_d = 149.424702

mol_lat_r  = np.deg2rad(mol_lat_d)
mol_lon_r  = np.deg2rad(mod_lon_d)

mol_ele_m  = 735.031

defaultPulsarFile = '.'+os.sep+'mol_pulsars.db'

defaultExtensionFile = '.'+os.sep+'mol_pulsars_extensions.db'

defaultLogFile = '.'+os.sep+'mol_observation.log'

# Degrees per second
EWSlewRate = 4.0 / 60
NSSlewRate = 5.0 / 60

ELimit = 15.0
WLimit = -15.0
NLimit = 53.37
SLimit = -90.0

########################
##  Public Functions  ##
########################

def nowtime():
  return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())

def latertime(seconds):
  return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(time.time()+seconds))

# D1 for tracking program
def D1(string):
  if dbg1 == True:
    print '[L1-%s]  '% nowtime() + string

# D2 for important information
def D2(string):
  if dbg2 == True:
    print '[L2-%s]  '% nowtime() + string

# D3 for critical information
def D3(string):
  if dbg3 == True:
    print '[L3-%s]  '% nowtime() + string

def EW(az, ze):
  return np.arcsin(np.sin(az)*np.sin(ze))

def NS(az, ze):
  return np.arcsin(np.cos(az)*np.sin(ze))

def EWd(az, ze):
  return EW(az,ze) * 180 / np.pi

def NSd(az, ze):
  return NS(az,ze) * 180 / np.pi

def Tobs(SNR,EW,S843,P0,W50,G0=0.00001,Tsys=75,Nm=2,Bw=30,Np=1):
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

###############
##  Classes  ##
###############

#########################################################################################

####################
##  pulsarReader  ##
####################

class Pulsars():
  def __init__(self, dbfilepathname=defaultPulsarFile):
    D1('pulsars.pulsarReader.__init__('+dbfilepathname+')')
    self.dbfilepathname = dbfilepathname
    f = file(self.dbfilepathname)
    self.pulsars = []
    self.index = ['no',  'jname','raj',     'decj',    's843',    'p0',   'w50',    'dm']
    """self.pulsars[][1   2(J)    3(dgree)   4(as 3)   5(MHz)     6(s)    7(ms)      8]]
                      no name  ra  dec  s843  p0  w50  dm
    """

    while True:
      line = f.readline()
      if len(line)!=0:
        if line[0]=='#':
          continue
        templist = line.split(' ')
        templist[-1] = templist[-1].replace('\n','')
        self.pulsars.append(templist)
        D1('Loaded pulsar: '+templist[1])
      else:
        break
    

  def printPulsars(self):
    for item in self.index:
      print item+'    \t',
    print
    for line in self.pulsars:
      for item in line:
        print item+' \t',
      print


#########################################################################################

####################
##  specReader  ##
####################

class Extensions():
  def __init__(self, dbfilepathname=defaultExtensionFile):
    D1('pulsars.pulsarReader.__init__('+dbfilepathname+')')
    self.dbfilepathname = dbfilepathname
    f = file(self.dbfilepathname)
    self.extensions = []
    self.index = ['no','jname','points_gain','points_fail','gap_min','gap_max','SNR_min','SNR_min_tobs_max','SNR_max']
    """self.specs[][ 0    1         2             3             4        5          6          7                  8]
    """

    while True:
      line = f.readline()
      if len(line)!=0:
        if line[0]=='#':
          continue
        templist = line.split(' ')
        templist[-1] = templist[-1].replace('\n','')
        self.extensions.append(templist)
        D1('Loaded pulsar specs: '+templist[1])
      else:
        break
    

  def printExtensions(self):
    for item in self.index:
      print item+'    \t',
    print
    for line in self.extensions:
      for item in line:
        print item+' \t',
      print


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
    self.ns = NS(self.az, self.ze)
    self.ew = EW(self.az, self.ze)
    self.nsd = np.rad2deg(self.ns)
    self.ewd = np.rad2deg(self.ew)


#########################################################################################

##############
##  pulsar  ##
##############

class PulsarBase(Point):
  def __init__(self, pulsars, name, observer, epoch='2000'):
    self.found1 = False
    self.target_name = name
    for line in pulsars:
      if line[1] == name:
        Point.__init__(self, line[2], line[3], observer, epoch)
        self.jname_base = line[1]
        self.s843 = line[4]
        self.p0 = line[5]
        self.w50 = line[6]
        self.dm = line[7]
        self.found1 = True
        self.visible_eye = False
        self.visible_tel = False
        if self.alt > 0:
          self.visible_eye = True
          if self.nsd < NLimit and WLimit <= self.ewd <= ELimit :
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
        break
    if self.found1!= True:
      D3('Cann\'t find the pulsar: '+name+'in the pulsar file: '+defaultPulsarFile)

  def printPulsarBase(self):
    print 'Pulsar %s, RA: %s, Dec: %s is now in NSd: %f and EWd: %f, Az: %s and Alt: %s, visible by eyes: %s, visible by tel: %s'% (self.jname_base, self.ra, self.dec, self.nsd, self.ewd, self.az, self.alt, self.visible_eye, self.visible_tel)


class PulsarExtension():
  def __init__(self, extensions, name):
    self.found2 = False
    for line in extensions:
      if line[1] == name:
        self.jname_ext = line[1]
        self.points_gain = float(line[2])
        self.points_fail = float(line[3])
        self.gap_min = float(line[4])
        self.gap_max = float(line[5])
        self.SNR_min = float(line[6])
        self.SNR_min_tobs_max = float(line[7])
        self.SNR_max = float(line[8])
        self.found2 = True
        break
    if self.found2!= True:
      D3('Cann\'t find the pulsar: '+name+'in the extension file: '+defaultExtensionFile)

  def printPulsarExtension(self):
    print 'Pulsar extension %s'%self.jname_ext, ' points_gain:%f' %self.points_gain, ' points_fail:%f'% self.points_fail


class Pulsar(PulsarBase, PulsarExtension):
  def __init__(self, pulsars, extensions, name, observer, epoch='2000'):
    self.exist = False
    PulsarBase.__init__(self, pulsars, name, observer, epoch)
    PulsarExtension.__init__(self, extensions,name)
    if self.found1 and self.found2:
      self.exist = True
    
    else:
      D3('Cann\'t find the same pulsar: '+name+'in the base and extension file: '+defaultPulsarFile+'  '+defaultExtensionFile)
    
  def printPulsar(self):
    if self.exist:
      self.printPulsarBase()
      self.printPulsarExtension()
    else:
      print 'Pulsar %s is not found'% self.target_name


class ObservationLogger():
  def __init__(self, dbfilepathname=defaultLogFile):
    self.f = file(dbfilepathname, 'a')
  
  def write(self,r):
    tmpstr = '\t'.join(r)
    self.f.write(tmpstr+'\n')
    self.f.flush()

  def __del__(self):
    self.f.close()

class ObservationRecord():
  def __init__(self, jname, time, snr, tobs, status, nmod, mopsrver, note):
    self.index = ['jname', 'time', 'snr', 'tobs', 'status', 'nmod', 'mopsrver', 'note']
    self.record = []
    self.record[0] = jname
    self.record[1] = time
    self.record[2] = snr
    self.record[3] = tobs
    self.record[4] = status
    self.record[5] = nmodule
    self.record[6] = mopsrver
    self.record[7] = note
    

#########################################################################################

################
##  Molonglo  ##
################


class Molonglo(ep.Observer):
  def __init__(self, date=nowtime()):
    ep.Observer.__init__(self)
    self.date = date
    self.lon = mol_lon_r
    self.lat = mol_lat_r
    self.elevation = mol_ele_m
    self.compute_pressure()


#########################################################################################

################
##  Slewtime  ##
################

class SlewTime():
  def __init__(self,p1,p2):
    self.fineseconds = -1
    self.fineminiseconds = -1
    self.coarseseconds = -1
    self.coarseminiseconds = -1
    self.source = p1
    self.target = p2
    if self.target.visible_eye == True:
      self.fineSlewTime()
      self.coarseSlewTime()

  def subSlewTime(self, p1, p2):
    slewEW = p2.ewd - p1.ewd
    slewEWTime = np.abs(slewEW) / EWSlewRate
    slewNS = p2.nsd - p1.nsd
    slewNSTime = np.abs(slewNS) / NSSlewRate
    D1('slewEW:\t'+str(slewEW))
    D1('slewNS:\t'+str(slewNS))
    return np.maximum(slewEWTime, slewNSTime)

  def fineSlewTime(self):
    p1 = self.source
    p2 = self.target
    i = 4
    while True:
      tt = self.subSlewTime(p1, p2)
      D1('Slewtime: %f'% tt)
      if i<=1:
        self.fineseconds = tt
        self.fineminiSeconds = tt * 1000.0
        p2.reposition(Molonglo())
        break

      p2.reposition(Molonglo(latertime(tt)))
      i -= 1

  def coarseSlewTime(self):
    self.coarseseconds = self.subSlewTime(self.source, self.target)
    self.coarseminiseconds = self.coarseseconds * 1000
    

class Scheduler():
  def __init__(self):
    """
    pulsarlist[][0         1   2    ]
                 jname    ra  dec  
    """
    self.pulsarlist = []
    pass


def position(ra, dec, date=nowtime(), epoch='2000'):
  target = Point(ra, dec, Molonglo(date))
  return target.ewd, target.nsd


def plotPulsarsRADec(pulsarlist, antenna = None):
  plt.subplot(121, projection='hammer')
  plt.grid(True)
  plt.title('Pulsars with RA and Dec')
  plt.xlabel('RA in degree')
  plt.ylabel('Dec in degree')
  for line in pulsarlist:
    name = line[1]
    ra = ratime2rad(line[2])
    if ra>np.pi:
      ra = ra - 2*np.pi
    dec = decdeg2rad(line[3])
    plt.plot(ra, dec, 'bo')
    plt.text(ra+0.02, dec-0.015, name, fontsize='9')
    #D1('Drawing %s, RA %f, Dec %f'% (name, ra, dec))


def plotPulsarsZenith(pulsarlist, observer, antenna=None, timetable=None,epoch='2000'):
  plt.subplot(111)
  plt.grid(True)
  plt.title('Pulsars over Molonglo')
  plt.xlabel('W<------------------  Degree  ---------------->E')
  plt.ylabel('S<------------------  Degree  ---------------->N')
  plt.axis('equal')
  plt.plot([WLimit, WLimit, ELimit, ELimit], [SLimit, NLimit, NLimit, SLimit], 'b-', lw='2')
  
  #initp = Point(antenna[0], antenna[1], observer, epoch)
  initp = SimplePoint(0.0,0.0)
  plt.plot([initp.ewd], [initp.nsd], 'r*')

  for line in pulsarlist:
    name = line[1]
    pulsar = PulsarBase(pulsarlist, name, observer)
    if pulsar.visible_eye == True:
      if pulsar.visible_tel == True:
        plt.plot(pulsar.ewd, pulsar.nsd, 'bo')
      else:
        plt.plot(pulsar.ewd, pulsar.nsd, 'ro')
      t = round(SlewTime(initp,pulsar).fineseconds / 60.0, 2)
      plt.text(pulsar.ewd+1, pulsar.nsd-2.4, name+'\n'+str(t), fontsize='9')
    else:
      plt.plot(pulsar.ewd, pulsar.nsd, 'gx')
      plt.text(pulsar.ewd+1, pulsar.nsd-2.4, name, fontsize='9')

def plotPulsars(pulsarlist, observer, antenna=None, timetable=None, epoch='2000'):
  #plotPulsarsRADec(pulsarlist)
  plotPulsarsZenith(pulsarlist, observer, antenna, timetable)
  plt.show()
  
def slewTimes(pulsarlist, antenna, observer, epoch='2000' ):
  timetable = []
  initp = Point(antenna[0], antenna[1], observer, epoch)
  for line in pulsarlist:
    subline = []
    subline.append(line[1])
    tmpp = PulsarBase([line], line[1], observer)
    subline.append(SlewTime(initp,tmpp).fineseconds)
    timetable.append(subline)
  return timetable


#########################################################################################

#################
##  Main test  ##
#################


if __name__ == '__main__':
  

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

  ps = Pulsars()
  #ps = Pulsars('kk.out')
  #ps.printPulsars()
  x = ps.pulsars

  es = Extensions()
  #es.printExtensions()
  e = es.extensions

  ob = Molonglo()
  #ob = Molonglo('2013/7/31 14:37:00')
  print ob

  p1 = Pulsar(x,e, 'J0437-4715', ob)
  print 'p1'
  p1.printPulsar()

  
  p2 = Pulsar(x,e, 'J1456-6843', ob)
  p2.printPulsar()

  p3 = Pulsar(x,e, 'J1935+1616', ob)
  p3.printPulsar()

  p4 = Pulsar(x,e, 'J0953+0755', ob)
  p4.printPulsar()

  t = SlewTime(p1,p2)
  print t.fineseconds
  print t.coarseseconds

  print position('04:37:15.883250', '-47:15:09.031863')
  print position('04:37:15.883250', '-47:15:09.031863', latertime(t.fineseconds))

  an = ['4:37:38.49', '-68:47:09.8']
  sp = SimplePoint(0.0, 0.0)

  plotPulsars(ps.pulsars, ob, an)


