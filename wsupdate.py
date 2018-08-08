import arcpy, os, traceback

rootdir = r"\\ad.utah.edu\sys\FM\gis\datasource_change_test"
oldreadonly = r"\\ad.utah.edu\sys\FM\gis\ags_10_3\ags_content\sde_connection_files\fm-agsDataReader@gisdb1.it.utah.edu.sde"
oldreadwrite = r"\\ad.utah.edu\sys\FM\gis\ags_10_3\ags_content\sde_connection_files\fm-agsDataWriter@gisdb1.it.utah.edu.sde"
newreadonly = r"\\ad.utah.edu\sys\FM\gis\ags_10_3\ags_content\sde_connection_files\fm-agsDataReader@FM-GISSQLHA_DEFAULT_VERSION.sde"
newreadwrite = r"\\ad.utah.edu\sys\FM\gis\ags_10_3\ags_content\sde_connection_files\fm-agsDataWriter@FM-GISSQLHA_DEFAULT_VERSION.sde"

try:

    mxd = arcpy.mapping.MapDocument(r"\\ad.utah.edu\sys\FM\gis\datasource_change_test\sustainability_projects.mxd")
    #mxd.author = "SHON"
    #print mxd
    mxd.findAndReplaceWorkspacePaths ("", r"\\ad.utah.edu\sys\FM\gis\ags_10_3\ags_content\sde_connection_files\fm-agsDataReader@FM-GISSQLHA_DEFAULT_VERSION.sde")
    mxd.save();
    del mxd
    print "Done"

except arcpy.ExecuteError: 
    msgs = arcpy.GetMessages(2) 
    arcpy.AddError(msgs)
except:
    # Get the traceback object
     tb = sys.exc_info()[2]
     tbinfo = traceback.format_tb(tb)[0]

     # Concatenate information together concerning the error into a message string
     pymsg = "PYTHON ERRORS:\nTraceback info:\n" + tbinfo + "\nError Info:\n" + str(sys.exc_info()[1])
     print pymsg
