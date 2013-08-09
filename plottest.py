#!/usr/bin/env python

import time,struct,sys
import matplotlib.pyplot as plt
from numpy import *

a = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16]

i = 0

subfig_1 = plt
subfig_1.ion()
subfig_1.figure(figsize=(6,4))

while(1):
    i = i + 1

    subfig_1.subplot(211)
    subfig_1.title('First Fig %d'%i)
    subfig_1.plot(a)


    subfig_1.subplot(212)
    subfig_1.title('Second Fig')
    subfig_1.plot(a)

    subfig_1.draw()
    print i
    time.sleep(1)

