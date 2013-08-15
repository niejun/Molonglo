#!/usr/bin/python

import matplotlib.pyplot as plt

fig = plt.figure(figsize=(12,10))
ax = plt.axes([0.05,0.05,0.9,0.9])
ax.cla()
ax.set_aspect(1)

ax.axis('equal')
ax.axis([-90,90 ,-90,60])
ax.grid()

ax.set_title('Test')
ax.set_xlabel('X')
ax.set_ylabel('Y')


ax.plot([1,2,3])



plt.show()

fig.savefig('test.png',dpi=150)

plt.show()
