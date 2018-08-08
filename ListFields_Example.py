import arcpy, os

FC = r"\\ad.utah.edu\sys\fm\gis\ags_10_3\ags_content\sde_connection_files\sdeadmin@fm-sqlsrcvrtest.fm.utah.edu.sde\uusd.DBO.DRU\uusd.DBO.SPATIAL_1000YR"
FieldList = arcpy.ListFields(FC)
for field in FieldList:
    print field.name

