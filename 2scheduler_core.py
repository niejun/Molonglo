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
import threading
import eventlet
from eventlet.green import socket
import lxml.etree as et
import lxml as xml
import MySQLdb as mysql

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
DEFAULT_STATUS_TXT_FILE = '.'+os.sep+'mol_status.txt'

# SQLite
DEFAULT_PULSAR_DB_FILE = '.'+os.sep+'mol_pulsars.db'

# MySQL
MYSQL_HOST = 'localhost'
MYSQL_USER = 'scheduler'
MYSQL_PASS = 'molonglo'
#MYSQL_PASS = 'MMypssqrl'
MYSQL_DB = 'scheduler'

# Slew rate, degrees per second
EW_SLEW_RATE = 4.0 / 60.0
NS_SLEW_RATE = 5.0 / 60.0

# Antenna slew limitation, degree
E_LIMIT = 15.0
W_LIMIT = -15.0
N_LIMIT = 53.37
S_LIMIT = -90.0

# Antenna view area
EW_VIEW = 5.0
NS_VIEW = 2.0

# MOPSR IP and Port
MOPSR_IP = '127.0.0.1'
MOPSR_PORT = 6000

# TCC IP and Port
TCC_IP = 'localhost'
TCC_PORT = 6001

# Saved PNG file resolution
PNG_DPI = 150

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
pulsarstatus = {}
joblist = []
running = True
gui_in_buffer = ''
gui_out_status_buffer = ''
gui_out_pulsar_buffer = ''
gui_out_obslist_buffer = ''
# manual, automatic
scheduler_mode = 'manual'
# parked, slewing, tracking
antenna_status = 'None'
# not_connect, ready, recording
mopsr_status = 'not_connect'
# not_connect, ready, tracking, slewing
tcc_status = 'not_connect'
# degree
antenna_position_ewd = 0.0
antenna_position_nsd = 0.0
message_to_mopsr = ''
message_from_mopsr = ''
message_to_tcc = ''
message_from_tcc = ''

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
def out(string, newline=True):
  if OUT == True and newline:
    print '[OUT-%s]  '% nowtime() + string
  if OUT == True and newline == False:
    print string,

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




def query(sql):
  con = mysql.connect(MYSQL_HOST, MYSQL_USER, MYSQL_PASS, MYSQL_DB)
  with con:
    cur = con.cursor()
    cur.execute(sql)
    result = cur.fetchall()
  return result

def preparedb():
  result = query("show tables like 'PulsarList'")
  if len(result)==0:
    initdb()
  readpulsarlist()



def initdb():
  createtable = 'create table PulsarList(jname varchar(250), raj varchar(250),decj varchar(250), s843 float, p0 float, w50 float, dm float, points_gain float, points_fail float, gap_min float, gap_max float, snr_min float, snr_min_tobs_max float, snr_max float , primary key(jname))'
  query(createtable)
  # Observing Log
  createtable = 'create table PulsarLog(jname varchar(250), tstart datetime, tobs float, succeed bool, points float, snr float, comment varchar(250))'
  query(createtable)
  # Observing List
  createtable = 'create table PulsarJobList(jname varchar(250), tstart datetime, tobs float, observing bool)'
  query(createtable)
  # Statuses and Commands
  createtable = 'create table Status(name varchar(250), taken bool, scheduler_mode varchar(250), antenna_status varchar(250), antenna_position_ewd float, antenna_position_nsd float, mopsr_status varchar(250), tcc_status varchar(250), running bool)'
  query(createtable)

  # System information
  createtable = 'create table System(mopsr_ip varchar(250), mopsr_port int, tcc_ip varchar(250), tcc_port int)'
  query(createtable)

  # Pulsars overhead status
  createtable = 'create table PulsarStatus(jname varchar(250), ewd float, nsd float)'
  query(createtable)

  out('Database does not exist, created')
  #self.testdata()
  initpulsarlist()
  initstatus()



def initpulsarlist():
  f = file(DEFAULT_PULSAR_TXT_FILE)
  sql = "delete from PulsarList"
  query(sql)
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
      query(sql)
      dbg('Loaded pulsar: '+templist[0])
    else:
      break



def initstatus():
  f = file(DEFAULT_STATUS_TXT_FILE)
  sql = "delete from Status"
  query(sql)
  while True:
    line = f.readline()
    if len(line)!=0:
      if line[0]=='#':
        continue
      templist = line.replace('*','NULL')
      templist = templist.split(' ')
      templist[-1] = templist[-1].replace('\n','')
      sql = "insert into Status values('"+templist[0]+"',"+str(templist[1])+",'"+templist[2]+"','"+templist[3]+"',"+str(templist[4])+","+str(templist[5])+",'"+templist[6]+"','"+templist[7]+"','"+templist[8]+"');"
      dbg(sql)
      query(sql)
      dbg('Loaded status: '+templist[0])
    else:
      break

def readpulsarlist():
  rows = query('select * from PulsarList;')
  for row in rows:
    pulsarlist[str(row[0])] = [str(row[1]), str(row[2]), row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11], row[12], row[13] ]

def update(table, column, value,wherecolumn, wherevalue):
  sql = "update "+ table + " set " + column + "='" + value + "' where " + wherecolumn + "='" + wherevalue + "';"
  query(sql)
  dbg(sql)




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
      #print attr
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
    #dbg('slewEW:\t'+str(slewEW))
    #dbg('slewNS:\t'+str(slewNS))
    return np.maximum(slewEWTime, slewNSTime)

  def fineSlewTime(self):
    p1 = self.source
    p2 = Point(self.target._ra, self.target._dec, self.target.observer)
    i = 4
    while True:
      tt = self.subSlewTime(p1, p2)
      #dbg('Slewtime: %f'% tt)
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
    
def positions(observatory=Molonglo()):
  positionlist = {}
  for line in pulsarlist.keys():
    name = line
    attr = pulsarlist[line]
    pulsar = Pulsar(name, observatory)
    positionlist[name] = [pulsar.ewd, pulsar.nsd, pulsar.visible_eye, pulsar.visible_tel]
  return positionlist

def gotime(initp, observatory):
  gotimelist = {}
  for line in pulsarlist.keys():
    name = line
    attr = pulsarlist[line]
    pulsar = Pulsar(name, observatory)
    
    if pulsar.visible_eye == True:
      gotimelist[name] = [-1.0, -1.0, -1.0, -1.0]
      st = SlewTime(initp, pulsar)
      gotimelist[name][0] = st.fineseconds
      gotimelist[name][1] = st.dest

      #snr(Tobs,EW,S843,P0,W50,G0=0.00001,Tsys=75,Nm=2,Bw=30,Np=1)
      tsnr = (snr(300, pulsar.ewr, pulsar.s843, pulsar.p0, pulsar.w50)+snr(300, st.dest.ewr, pulsar.s843, pulsar.p0, pulsar.w50))/2.0
      gotimelist[name][2] = tsnr

      #tobs(SNR,EW,S843,P0,W50,G0=0.00001,Tsys=75,Nm=2,Bw=30,Np=1)
      ttobs = tobs(pulsar.snr_min, (pulsar.ewr+st.dest.ewr)/2.0, pulsar.s843, pulsar.p0, pulsar.w50)
      gotimelist[name][3] = ttobs

  return gotimelist


def getCurrentPosition():
  # TODO: connect to TCC
  return SimplePoint(0.0,0.0)

def sendMessageToMOPSR(msg):
  out('Send to MOPSR: %s'%msg)
  return msg
  

def getMessageFromMOPSR(msg):
  out('Get from MOPSR: %s'%msg)
  return msg
  
def sendMessageToTCC(msg):
  out('Send to TCC: %s'%msg)
  return msg

def getMessageFromTCC(msg):
  out('Get from TCC: %s'%msg)
  return msg

class Scheduler():
  def __init__(self):

    global pulsarlist, joblist, running, scheduler_mode, antenna_status, mopsr_status, tcc_status, antenna_position_ewd, antenna_position_nsd
    global message_to_mopsr,message_from_mopsr,message_to_tcc,message_from_tcc
    preparedb()
    
    self.systemstatus = False
    self.systemtest()
    self.observatory = Molonglo()
    self.client = Client()
    self.client.start()
    self.drawmap = DrawMap(self.observatory)
    self.drawmap.start()
    self.status = StatusDealer()
    self.status.start()
    while True:
      self.systemtest()
      if self.systemstatus:
        joblist = []
        sql = "select * from PulsarJobList"
        results = query(sql)
        for row in results:
          joblist.append(row[0])
        #out('Joblist', False)
        #dbg(joblist)
        if len(joblist)>0:
                                      
          source = joblist[0]
          sql = "update PulsarJobList set observing=1 where jname='"+source+"'"
          query(sql)
          curp = SimplePoint(antenna_position_ewd, antenna_position_nsd)
          t_timetable = gotime(curp, self.observatory)
          t_sourcet = t_timetable[source][0] / 60.0
          t_dest = t_timetable[source][1]
          out('Begin observing schedule on %s'%source)
          sendMessageToTCC('Move to %s'%(str(t_dest.ewd)+str(t_dest.nsd) ))
          out('Antenna is slewing')
          #while tcc_status!='tracking':
          #  out('.', False)
          #  time.sleep(1)
          antenna_position_ewd = t_dest.ewd
          antenna_position_nsd = t_dest.nsd
          sql = "update Status set antenna_position_ewd="+str(antenna_position_ewd)+",antenna_position_nsd="+str(antenna_position_nsd)+" where name='status'"
          dbg(sql)
          query(sql)
          sendMessageToMOPSR('recording')
          mopsr_status = 'recording'
          out('MOPSR is preparing')
          while mopsr_status!='recording' and self.systemstatus:
            self.systemtest()
            out('.', False)
            time.sleep(1)

          temptobs = int(t_timetable[source][3])+20
          while self.systemstatus and temptobs > 0:
            out('.')
            self.systemtest()
            temptobs = temptobs - 1
            time.sleep(1)
          mopsr_status = 'finish'
          sql = "delete from PulsarJobList where jname='"+source+"'"
          query(sql)
          joblist.remove(source)
        else:
          out('Job list is empty')
          time.sleep(1)      

      else:
        out('Something wrong')
        out('Scheduler mode:%s, scheduler running:%s, MOPSR status:%s, TCC status:%s, job list length:%d, antenna position(%f,%f)'%(scheduler_mode, running, mopsr_status, tcc_status, len(joblist),antenna_position_ewd, antenna_position_nsd))
        time.sleep(1)


  def systemtest(self):
    if tcc_status!='not_connect':
      if mopsr_status!='not_connect':
        if running:
          self.systemstatus = True
        else:
          self.systemstatus = False
          out('The scheduler is not running')
      else:
        self.systemstatus = False
        out('MOPSR status wrong:%s'%mopsr_status)
    else:
      self.systemstatus = False
      out('TCC status wrong: %s'%antenna_status)


class Client(threading.Thread):
  def __init__(self):
    global mopsr_status, tcc_status
    threading.Thread.__init__(self)
    #self.pile = eventlet.GreenPile()
    self.mopsr_con = socket.socket()
    ip = socket.gethostbyname(MOPSR_IP)
    self.mopsr_con.connect((ip, MOPSR_PORT))
    #self.fd = self.mopsr_con.makefile('rw')
    mopsr_status = 'ready'
    tcc_status = 'ready'
    self.mopsr_status = mopsr_status

  def run(self):
    global message_to_mopsr,message_from_mopsr,message_to_tcc,message_from_tcc
    global mopsr_status
    while True:
      if self.mopsr_status != mopsr_status:
        out('MOPSR status changed from %s to %s'%(self.mopsr_status, mopsr_status))
        message_to_mopsr = XMLWriter('mopsr','set',{'status':mopsr_status})

        self.mopsr_con.sendall(message_to_mopsr+'\n')

        message_to_mopsr = XMLWriter('mopsr','query',{'status':''})

        self.mopsr_con.sendall(message_to_mopsr+'\n')

        message_from_mopsr = self.mopsr_con.recv(8192).strip()
        result = XMLReader('mopsr')
        dbg('Get message from MOPSR%s'%result['status'])        
        if result['status'] != mopsr_status:
          mopsr_status = self.mopsr_status
        else:
          self.mopsr_status = mopsr_status
      else:
        time.sleep(0.1)




def XMLReader(who):
  result = {}
  if who == 'mopsr':
    tmpdom = et.fromstring(message_from_mopsr)
    if tmpdom.tag == 'Molonglo':
      for i in tmpdom:
        if i.tag == who:
          for j in i:
            result[j.tag] = j.text
  return result

  if who == 'tcc':
    pass


def XMLWriter(who, action, attr):
  if who =='mopsr':
    tmpdom = et.Element('Molonglo')
    a00 = et.SubElement(tmpdom, who)
    a01 = et.SubElement(a00, action)
    for i in attr.keys():
      a02 = et.SubElement(a01, i)
      a02.text = attr[i]
    return et.tostring(tmpdom)

class StatusDealer(threading.Thread):
  def __init__(self):
    threading.Thread.__init__(self)
    #time.sleep(3.3)

  def run(self):
    global mopsr_status, tcc_status, antenna_status, running, antenna_position_ewd, antenna_position_nsd
    while True:
      sql = "select * from Status where name='command' and taken=1"
      results = query(sql)
      #dbg('Results:%d'%results)
      if results!=None:
        for row in results:
          mopsr_status = row['mopsr_status']
          tcc_status = row['tcc_status']
          antenna_status = row['antenna_status']
          running = row['running']
          antenna_position_ewd = row['antenna_position_ewd']
          antenna_position_nsd = row['antenna_position_nsd']
        sql = "update Status set taken=0 where name='command'"
        query(sql)
      sql = "update Status set scheduler_mode='"+scheduler_mode+"', mopsr_status='"+mopsr_status+"', tcc_status='"+tcc_status+"', antenna_status='"+antenna_status+"', running='"+str(int(running))+"', antenna_position_ewd="+str(antenna_position_ewd)+", antenna_position_nsd="+str(antenna_position_nsd)+" where name='status'"
      query(sql)
      time.sleep(2)
      


        
      

def keycommand(event):
  print 'Key pressed:', event.key, event.xdata, event.ydata 
  global running
  if event.key == '1':
    running = True
    Scheduler()
  if event.key == '2':
    running = False

def makejoblist(event):
  point = event.artist
  xdata = point.get_xdata()
  ydata = point.get_ydata()
  ind = event.ind
  #print type(ind)
  positionlist = positions()
  for key in positionlist.keys():
    if (positionlist[key][0]-xdata[ind])**2 + (positionlist[key][1]-ydata[ind])**2 < 1:
      print 'Different is: %f'% ((positionlist[key][0]-xdata[ind])**2 + (positionlist[key][1]-ydata[ind])**2)
      print 'Pulsar is:%s'%key
      joblist.append(key)
  print 'Point: ', zip(xdata[ind], ydata[ind])


class DrawMap(threading.Thread):
  def __init__(self, obs):
    threading.Thread.__init__(self)
    self.obs = obs
    self.fig = plt.figure(figsize=(12,10))
    self.ax = plt.axes([0.05,0.05,0.9,0.9])
    self.ax.set_aspect(1)



  def run(self):
    global running, pulsarstatus, antenna_position_ewd, antenna_position_nsd
    while True:
      if running:
        
        self.ax.cla()
        self.ax.axis('equal')
        self.ax.axis([-90,90 ,-90,60])
        self.ax.grid(True)
        self.ax.set_title('Pulsars over Molonglo @ '+nowtime(DATE))
        self.ax.set_xlabel('East west degrees')
        self.ax.set_ylabel('North south degrees')
        self.ax.plot([W_LIMIT, W_LIMIT, E_LIMIT, E_LIMIT], [S_LIMIT, N_LIMIT, N_LIMIT, S_LIMIT], 'b-', lw='2')
        sql = 'delete from PulsarStatus'
        query(sql)
        #dbg('Delete all in PulsarStatus')
        sql = "select antenna_position_ewd,antenna_position_nsd from Status where name='status'"
        results = query(sql)
        antenna_position_ewd = results[0][0]
        antenna_position_nsd = results[0][1]
        self.ax.plot([antenna_position_ewd-EW_VIEW/2, antenna_position_ewd-EW_VIEW/2, antenna_position_ewd+EW_VIEW/2, antenna_position_ewd+EW_VIEW/2, antenna_position_ewd-EW_VIEW/2], [antenna_position_nsd-NS_VIEW/2, antenna_position_nsd+NS_VIEW/2, antenna_position_nsd+NS_VIEW/2, antenna_position_nsd-NS_VIEW/2, antenna_position_nsd-NS_VIEW/2], 'r-', lw='1')
        for line in pulsarlist.keys():
          name = line
          attr = pulsarlist[line]
          pulsar = Pulsar(name, self.obs)
          if pulsar.visible_eye == True:
            if pulsar.visible_tel == True:
              self.ax.plot(pulsar.ewd, pulsar.nsd, 'bo')
            else:
              self.ax.plot(pulsar.ewd, pulsar.nsd, 'ro')
            pulsarstatus[name] = [pulsar.ewd, pulsar.nsd]
            self.ax.text(pulsar.ewd+1, pulsar.nsd-2.4, name, fontsize='9')
            sql = "insert into PulsarStatus values('"+name+"',"+str(pulsar.ewd)+","+str(pulsar.nsd)+")"
            #dbg('Append pulsar %s: %s'%(name, sql))
            query(sql)

          else:
            self.ax.plot(pulsar.ewd, pulsar.nsd, 'gx')
            self.ax.text(pulsar.ewd+1, pulsar.nsd-2.4, name, fontsize='9')
        self.fig.savefig('webgui/currentpulsars.png', dpi=PNG_DPI)
        dbg("Drawing currentpulsars.png")
        time.sleep(3)




def plotPulsarsZenith(observer, antenna=None, timetable=None,epoch='2000'):

  fig = plt.figure()
  #plt.ion()
  ax = fig.add_subplot(111)
  #plt.title('Pulsars over Molonglo @ '+nowtime(DATE))
  #plt.xlabel('W<------------------  Degree  ---------------->E')
  #plt.ylabel('S<------------------  Degree  ---------------->N')
  #ax.set_axes([0.05,0.05,0.7,0.9])
  #fig.axis('equal')
  #fig.axis([-80,80,-100,60])
  plt.grid(True)
  ax.plot([W_LIMIT, W_LIMIT, E_LIMIT, E_LIMIT], [S_LIMIT, N_LIMIT, N_LIMIT, S_LIMIT], 'b-', lw='2')

  #initp = Point(antenna[0], antenna[1], observer, epoch)
  initp = getCurrentPosition()
  ax.plot([initp.ewd], [initp.nsd], 'r*')

  for line in pulsarlist.keys():
    name = line
    attr = pulsarlist[line]
    pulsar = Pulsar(name, observer)
    slewtable[name] = [-1.0, -1.0, -1.0, -1.0]
    if pulsar.visible_eye == True:
      if pulsar.visible_tel == True:
        ax.plot(pulsar.ewd, pulsar.nsd, 'bo', picker=10)
      else:
        ax.plot(pulsar.ewd, pulsar.nsd, 'ro', picker=10)
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

      ax.text(pulsar.ewd+1, pulsar.nsd-2.4, name+'\nTsl:'+str(tt)+',S/N:'+str(ts), fontsize='9')
    else:
      ax.plot(pulsar.ewd, pulsar.nsd, 'gx')
      ax.text(pulsar.ewd+1, pulsar.nsd-2.4, name, fontsize='9')
  fig.canvas.mpl_connect('pick_event', makejoblist)
  fig.canvas.mpl_connect('key_press_event', keycommand)

def plotPulsars(observer, antenna=None, timetable=None, epoch='2000'):
  #plotPulsarsRADec(pulsarlist)
  plotPulsarsZenith(observer, antenna, timetable)
  plt.show()
  

class fig():
  def __init__(self, p):
    self.p = p
    self.p.ion()
    self.p.figure(figsize=(16,9))
    self.p.axes([0.05,0.05,0.7,0.9])
    self.p.axis('equal')
    self.p.axis([-80,80,-100,60])
    self.p.grid(True)
    self.p.plot([W_LIMIT, W_LIMIT, E_LIMIT, E_LIMIT], [S_LIMIT, N_LIMIT, N_LIMIT, S_LIMIT], 'b-', lw='2')
      
  def plot(self, *c):
    self.p.plot(*c)
    self.p.draw()




if __name__ == '__main__':
  #s = LiteSQL()
  #print 'All pulsars in database'
  #print pulsarlist.keys()

  #date = '2013-7-30 02:00:00'
  #date = nowtime()
  #DATE = strtime2sec(date)

  

  #ob = Molonglo(date)

  #p = Pulsar('J0437-4715', ob)
  #p.printPulsar()

  #plotPulsars(ob)

  #print slewtable

  #joblist = ['J0437-4715', 'J0738-4042', 'J0835-4510', 'J0953+0755', 'J1136+1551', 'J1456-6843', 'J1559-4438', 'J1644-4559', 'J1932+1059', 'J1935+1616']
  #joblist = ['J1456-6843', 'J1559-4438']
  joblist = ['J0835-4510']

  Scheduler()

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

