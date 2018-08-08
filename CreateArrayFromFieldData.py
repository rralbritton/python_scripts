#CreateArrayFromFieldData.py

#NOTE: Need to figure out a friendly way to export arrary to
#Javascript. Can not write an array to a textfile.

import arcpy
import time, uuid
from time import strftime

#Daily Data
#Exported as an X,Y pair - day & total count respectively

#Reference table that the daily stats are in
table = r"\\ad.utah.edu\sys\FM\gis\python_automation\reports\routes_summaryStats_20160825_1440.dbf"

TotalCnt = []
for row in arcpy.SearchCursor(table):
    TotalCnt.append([str(row.Date.strftime('%Y-%m-%d')),row.TotalCnt])
    del row

print TotalCnt
#print "done"
