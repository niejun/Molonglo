#!/usr/bin/python

import ephem as ep
import numpy as np
import time
import defines


# D1 for tracking program
def D1(string):
  if defines.dbg1 == True:
    print '[L1-%s]  %s'%(time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()), string)

# D2 for important information
def D2(string):
  if defines.dbg2 == True:
    print '[L2-%s]  %s'%(time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()), string)

# D3 for critical information
def D3(string):
  if defines.dbg3 == True:
    print '[L3-%s]  %s'%(time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()), string)
