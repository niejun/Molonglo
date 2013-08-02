#!/usr/bin/python

import ephem as ep
import numpy as np
import time

#Vela: J0835-4510 5000 08:35:20.61149 -45:10:34.8751
#EW tilt (deg) = arc sin ( sin(az) * sin(zen));
#NS tilt (deg) = arc sin  ( cos(az) * sin(zen));



testtime = '2013/7/25 03:37:00'
testtime = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())

def deg_to_rad(val):
    return np.pi*val/180.

MOL_LAT  = deg_to_rad(-35.37075)
MOL_LON  = deg_to_rad(149.424702)

vela = ep.FixedBody()
vela._ra = '08:35:20.61149'
vela._dec = '-45:10:34.8751'
#vela._dec = deg_to_rad(-35.37075)

mol = ep.Observer()
mol.date = testtime
mol.lon = MOL_LON
mol.lat = MOL_LAT

vela.compute(mol)

EW = np.arcsin(np.sin(vela.az)*np.sin(deg_to_rad(90) - vela.alt))
NS = np.arcsin(np.cos(vela.az)*np.sin(deg_to_rad(90) - vela.alt))

EWd = EW * 180 / np.pi
NSd = NS * 180 / np.pi

print 'Observer: ',mol
print 'Az: ', vela.az, '\t\tAlt: ', vela.alt
print 'RA: ', vela.ra, '\t\tDec: ', vela.dec
print 'EWd: ', EWd, '\t\tNSd: ', NSd

