#Name:      setSubTypeDefaultValues.py
#Purpose:   set default values for a domain associated
#           with a subtype

import arcpy

fc =(r"\\ad.utah.edu\sys\FM\gis\ags_10_3\ags_content\sde_connection_files\sdeadmin@FM-GISSQLHA_DEFAULT_VERSION.sde\uusd.DBO.Grounds\UUSD.DBO.Tree") 
subtypes = arcpy.da.ListSubtypes(fc)  
subtypeCodes = []

for stcode, stdict in subtypes.iteritems():  
    subtypeCodes.append(stcode)

##for fields in arcpy.ListFields(fc):
##    print fields.name

print subtypeCodes

for code in subtypeCodes:
    arcpy.AssignDefaultToField_management(fc,"tree_lifecycle","Active",code)
    print str(code) + "tree_lifecycle complete"
    arcpy.AssignDefaultToField_management(fc,"plaque",0,code)
    print str(code) + "plaque complete\n"
    
print "script done"    
  
