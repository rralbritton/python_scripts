#subtypes

import arcpy, traceback, sys

#Set workspace environment to geodatabase
workspace = arcpy.env.workspace = r"\\ad.utah.edu\sys\FM\gis\ags_10_3\ags_content\sde_connection_files\sdeadmin@fm-sqlsrcvrtest.fm.utah.edu.sde"

try:

    subtypes = arcpy.da.ListSubtypes(r"\\ad.utah.edu\sys\FM\gis\ags_10_3\ags_content\sde_connection_files\sdeadmin@fm-sqlsrcvrtest.fm.utah.edu.sde\uusd.DBO.Grounds\UUSD.DBO.tree")

    for stcode, stdict in list(subtypes.items()):
        #print('Code: {0}'.format(stcode))
        for stkey in list(stdict.keys()):
            if stkey == 'FieldValues':
                fields = stdict[stkey]
                for field, fieldvals in list(fields.items()):
                    if not fieldvals[1] is None:
                        print fieldvals[1].name
            
        
        
##    try: 
##        for fc in arcpy.ListFeatureClasses('*meters*'):
##            for field in arcpy.ListFields(fc):
##                if field.domain !="":
##                    print field.domain
####                        intcur = arcpy.da.InsertCursor(activeDomainTable,("name"))
####                        intcur.insertRow([field.domain])
####                        del intcur
##            subtypes = arcpy.da.ListSubtypes(fc)
##            for stcode, stdict in list(subtypes.items()):
##                for stkey in list(stdict.keys()):
##                    if stkey == 'FieldValues':
##                        fields = stdict[stkey]
##                        for field, fieldvals in list(fields.items()):
##                            if not fieldvals[1] is None:
##                                print fieldvals[1].name
##
##    except:
##        print "ERROR: " + fc
##        continue
##            
##     
##    print "\nDONE"

except arcpy.ExecuteError:
    print(arcpy.GetMessages(2))
    
except:
     # Get the traceback object
    tb = sys.exc_info()[2]
    tbinfo = traceback.format_tb(tb)[0]

    # Concatenate information together concerning the error into a message string
    pymsg = "PYTHON ERRORS:\nTraceback info:\n" + tbinfo + "\nError Info:\n" + str(sys.exc_info()[1])
    arcpy.AddError(pymsg)
    print(pymsg)

    
