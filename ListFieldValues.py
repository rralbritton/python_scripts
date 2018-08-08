#Name:      ListFieldValues.py
#Purpose:   Lists all of the values in a given field

import arcpy

featureClass = r"\\ad.utah.edu\sys\fm\gis\ags_10_3\ags_content\sde_connection_files\sdeadmin@fm-sqlsrcvrtest.fm.utah.edu.sde\uusd.DBO.cs_parking\uusd.DBO.lotpermittypes"
field = "LOTNAME"
sc = arcpy.SearchCursor(featureClass)

for row  in sc:
    print (row.getValue(field))

del row
del sc
    
