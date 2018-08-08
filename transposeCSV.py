#transpose.py

import os, csv
from itertools import izip

csvFileIn = r"C:\Temp\CSVReports\coffee_shop_wm_fm-ags0.fm.utah.edu.csv"
csvFileOut = r"C:\Temp\CSVReports\Test.csv"

a = izip(*csv.reader(open(csvFileIn, "rb")))
csv.writer(open(csvFileOut, "wb")).writerows(a)
print "done"

