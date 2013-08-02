#!/usr/bin/python

import sqlite3 as lite
import sys

con = None

try:
  con = lite.connect('test.db')
  cur = con.cursor()
  cur.execute('select sqlite_version()')
  x = cur.fetchone()
  print 'SQLITE Version %s'%x

except lite.Error,e:
  print 'Error: %s'%e.args[0]
  sys.exit(1)

finally:
  if con:
    con.close()
