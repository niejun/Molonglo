#!/usr/bin/python

import sqlite3 as lite
import sys

con = lite.connect('test.db')

with con:
  cur = con.cursor()
  cur.execute('select sqlite_version()')
  date = cur.fetchone()
  print '%s'% date

