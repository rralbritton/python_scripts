#generateBuildingList

import arcpy

#Set Workspace
workspace = arcpy.env.workspace = r"\\ad.utah.edu\sys\FM\gis\ags_10_3\ags_content\sde_connection_files\sdeadmin@fm-sqlsrcvrtest.fm.utah.edu.sde"
arcpy.env.overwriteOutput = True

buildings = r"\\ad.utah.edu\sys\FM\gis\ags_10_3\ags_content\sde_connection_files\sdeadmin@FM-GISSQLHA_DEFAULT_VERSION.sde\uusd.DBO.structure"
buildingView = arcpy.MakeFeatureLayer_management(buildings, "building_view","building_number NOT IN(0,-1) AND lifecycle IN( 'Active' , 'Construction' ) AND informal_name IS NOT NULL")                                                      

sc= arcpy.SearchCursor(buildingView)

for row in sc:
    print "elif (row[0] == "+ str(row.building_number)+"):"
    print "\trow[1] = "+"'"+row.informal_name+"'"

del row
del sc

print "done"
