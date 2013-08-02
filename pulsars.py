#!/usr/bin/python

# Use following script to generate the mol_pulsars.db file for reading

#psrcat -c "jname s400 s1400 spindx rajd decjd p0 w50 dm" | awk '{if($1>0 && $4>=100 && $7>=30 && $14<=18) print  $2, $13, $14,\
#                                                                                                                name ra   dec
#           $4*(400.0/843.0)**(log($7/$4)/log(400.0/1400.0)), $15, $18, $21}'|awk '{print NR, $0}' > mol_pulsars.db
#                                      s843                    p0  w50  dm                             

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

import os
import funcs

class pulsarReader():
  def __init__(self, dbfilepathname='.'+os.sep+'mol_pulsars.db'):
    funcs.D1('pulsars.pulsarReader.__init__('+dbfilepathname+')')
    self.dbfilepathname = dbfilepathname
    f = file(self.dbfilepathname)
    self.__pulsars = []
    self.__index = ['no','jname',  'rajd',  'decjd',  's843',    'p0',   'w50',    'dm']
    """self.pulsars[][1   2(J)    3(dgree)   4(as 3)   5(MHz)     6(s)    7(ms)      8]
                      no name  ra  dec  s843  p0  w50  dm
    """

    while True:
      line = f.readline()
      if len(line)!=0:
        templist = line.split(' ')
        templist[-1] = templist[-1].replace('\n','')
        self.__pulsars.append(templist)
        funcs.D1('Loaded pulsar: '+templist[1])
      else:
        break
    

  def printpulsars(self):
    for item in self.__index:
      print item+'    \t',
    print
    for line in self.__pulsars:
      for item in line:
        print item+' \t',
      print

  def pulsars(self):
    return self.__pulsars


if __name__ == '__main__':
  p = pulsarReader()
  p.printpulsars()
